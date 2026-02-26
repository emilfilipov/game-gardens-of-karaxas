#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "concept_art"
OUT_DIR = BASE_DIR / "option_radial_5pass"
BASE_GLOB = "ui_concept_*.png"


def load_canvas_size() -> tuple[int, int]:
    bases = sorted(BASE_DIR.glob(BASE_GLOB))
    if not bases:
        raise SystemExit("No ui_concept_*.png files found under concept_art/")
    with Image.open(bases[0]) as im:
        return im.size


def font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_H1 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 30)
F_H2 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 20)
F_TX = font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 15)
F_SM = font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)


def pass_profile(n: int) -> dict:
    # Intentional progressive tightening across passes.
    return {
        "bg": (245 - n, 246 - n, 248 - n, 255),
        "grid": (226 - n, 228 - n, 233 - n, 255),
        "ink": (20, 22, 28, 255),
        "ink_soft": (68 - n, 72 - n, 84 - n, 255),
        "blob_outer": (14, 16, 22, 255),
        "blob_mid": (25, 28, 37, 255),
        "blob_hi": (44, 48, 60, 255),
        "edge": (24, 27, 36, 255),
        "chip": (237, 239, 243, 250),
        "chip_text": (59, 63, 75, 255),
        "panel": (248, 249, 251, 240),
        "panel_edge": (186 - n, 190 - n, 201 - n, 255),
        "field": (241, 243, 247, 255),
        "button": (23, 26, 34, 255),
        "button_text": (248, 248, 251, 255),
        "muted_btn": (220, 222, 228, 255),
        "muted_text": (154, 158, 168, 255),
        "show_edge_chips": n <= 3,
        "orb_r": 94 + (n * 3),
        "node_r": 46 + n,
        "ring_r": 282 - (n * 6),
        "panel_w": 580 - (n * 12),
        "panel_h": 372 - (n * 6),
        "line_w": 4,
        "compact_copy": n >= 3,
    }


def draw_background(d: ImageDraw.ImageDraw, w: int, h: int, pal: dict, seed: int) -> None:
    d.rectangle((0, 0, w, h), fill=pal["bg"])
    for y in range(0, h, 96):
        d.line((0, y, w, y), fill=pal["grid"], width=1)
    rng = Random(seed)
    for _ in range(620):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        c = rng.choice([236, 242, 248])
        a = rng.randint(12, 38)
        d.point((x, y), fill=(c, c, c, a))


def blob_pts(cx: int, cy: int, r: int, seed: int, count: int = 96) -> list[tuple[int, int]]:
    rng = Random(seed)
    pts: list[tuple[int, int]] = []
    for i in range(count):
        ang = (2 * math.pi * i) / count
        wave = 0.11 * math.sin(ang * 7.0) + 0.08 * math.cos(ang * 5.0)
        jitter = rng.uniform(-0.08, 0.08)
        rr = r * (1.0 + wave + jitter)
        pts.append((int(cx + math.cos(ang) * rr), int(cy + math.sin(ang) * rr)))
    return pts


def draw_blob(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, pal: dict, seed: int, selected: bool = False) -> None:
    pts = blob_pts(cx, cy, r, seed)
    outer = pal["blob_outer"] if not selected else (16, 20, 30, 255)
    mid = pal["blob_mid"] if not selected else (30, 36, 50, 255)
    hi = pal["blob_hi"] if not selected else (58, 66, 82, 255)
    d.polygon(pts, fill=outer, outline=(8, 9, 12, 255))
    for scale, col in [(0.90, mid), (0.82, hi)]:
        inner = [(int(cx + (x - cx) * scale), int(cy + (y - cy) * scale)) for x, y in pts]
        d.polygon(inner, fill=col)
    d.ellipse((cx - r + 36, cy - r + 22, cx - 8, cy - r + 108), fill=(255, 255, 255, 18))
    rng = Random(seed + 777)
    for _ in range(int(r * 5.5)):
        px = rng.randint(cx - r + 10, cx + r - 10)
        py = rng.randint(cy - r + 10, cy + r - 10)
        if (px - cx) ** 2 + (py - cy) ** 2 > (r - 12) ** 2:
            continue
        s = rng.choice([1, 2, 2, 3])
        col = rng.choice([(4, 5, 8, 92), (62, 67, 82, 46), (92, 98, 114, 36)])
        d.rectangle((px, py, px + s, py + s), fill=col)
    if selected:
        d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), outline=(236, 238, 243, 170), width=2)
        d.ellipse((cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14), outline=(224, 227, 235, 110), width=1)


def polar(cx: int, cy: int, r: int, deg: float) -> tuple[int, int]:
    a = math.radians(deg)
    return int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)


def draw_spoke(d: ImageDraw.ImageDraw, c: tuple[int, int], n: tuple[int, int], label: str, pal: dict, show_chip: bool = True):
    x0, y0 = c
    x1, y1 = n
    # Slight arc keeps the radial routes from looking mechanically straight.
    vx, vy = x1 - x0, y1 - y0
    ln = max(1.0, math.hypot(vx, vy))
    ux, uy = vx / ln, vy / ln
    px, py = -uy, ux
    mx, my = int((x0 + x1) * 0.5 + px * 18), int((y0 + y1) * 0.5 + py * 18)
    d.line((x0, y0, mx, my, x1, y1), fill=pal["edge"], width=4, joint="curve")
    vx, vy = x1 - x0, y1 - y0
    ln = max(1.0, math.hypot(vx, vy))
    ux, uy = vx / ln, vy / ln
    px, py = -uy, ux
    tip = (x1, y1)
    l = (int(x1 - ux * 13 + px * 7), int(y1 - uy * 13 + py * 7))
    r = (int(x1 - ux * 13 - px * 7), int(y1 - uy * 13 - py * 7))
    d.polygon([tip, l, r], fill=pal["edge"])
    if show_chip:
        mx, my = int(x0 + vx * 0.64), int(y0 + vy * 0.64)
        w = max(84, len(label) * 7 + 18)
        h = 24
        d.rounded_rectangle((mx - w // 2, my - h // 2, mx + w // 2, my + h // 2), radius=8, fill=pal["chip"], outline=pal["panel_edge"], width=1)
        d.text((mx, my), label, anchor="mm", font=F_SM, fill=pal["chip_text"])


def draw_panel(d: ImageDraw.ImageDraw, cx: int, cy: int, w: int, h: int, pal: dict) -> tuple[int, int, int, int]:
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = x0 + w, y0 + h
    cut = 22
    poly = [
        (x0 + cut, y0), (x1 - cut, y0), (x1, y0 + cut), (x1, y1 - cut),
        (x1 - cut, y1), (x0 + cut, y1), (x0, y1 - cut), (x0, y0 + cut)
    ]
    shadow = [(x + 6, y + 8) for x, y in poly]
    d.polygon(shadow, fill=(18, 21, 28, 28))
    d.polygon(poly, fill=pal["panel"], outline=pal["panel_edge"])
    d.line((x0 + 30, y0 + 44, x1 - 30, y0 + 44), fill=(206, 211, 222, 255), width=1)
    return (x0, y0, x1, y1)


def clamp_panel(cx: int, cy: int, w: int, h: int, canvas_w: int, canvas_h: int) -> tuple[int, int]:
    half_w = w // 2
    half_h = h // 2
    cx = max(half_w + 24, min(canvas_w - half_w - 24, cx))
    cy = max(half_h + 24, min(canvas_h - half_h - 24, cy))
    return cx, cy


def field(d: ImageDraw.ImageDraw, x: int, y: int, w: int, text: str, pal: dict) -> None:
    d.rounded_rectangle((x, y, x + w, y + 32), radius=8, fill=pal["field"], outline=pal["panel_edge"], width=1)
    d.text((x + 12, y + 16), text, anchor="lm", font=F_TX, fill=pal["ink_soft"])


def button(d: ImageDraw.ImageDraw, x: int, y: int, w: int, text: str, pal: dict, enabled: bool = True) -> None:
    if enabled:
        fill = pal["button"]
        text_col = pal["button_text"]
    else:
        fill = pal["muted_btn"]
        text_col = pal["muted_text"]
    d.rounded_rectangle((x, y, x + w, y + 34), radius=9, fill=fill, outline=pal["panel_edge"], width=1)
    d.text((x + w // 2, y + 17), text, anchor="mm", font=F_TX, fill=text_col)


def draw_graph_mini(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], pal: dict, muted: bool) -> None:
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=10, fill=(243, 245, 249, 255), outline=pal["panel_edge"], width=1)
    for x in range(x0 + 16, x1 - 8, 42):
        d.line((x, y0 + 12, x, y1 - 10), fill=(222, 225, 232, 255), width=1)
    for y in range(y0 + 12, y1 - 10, 38):
        d.line((x0 + 10, y, x1 - 10, y), fill=(222, 225, 232, 255), width=1)
    nodes = [(0.16, 0.63), (0.34, 0.70), (0.48, 0.57), (0.62, 0.67), (0.69, 0.49), (0.48, 0.80), (0.81, 0.61)]
    pts = [(int(x0 + (x1 - x0) * px), int(y0 + (y1 - y0) * py)) for px, py in nodes]
    edges = [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5), (3, 6)]
    line_col = (95, 101, 114, 255) if not muted else (168, 172, 182, 255)
    node_col = (28, 31, 41, 255) if not muted else (162, 166, 176, 255)
    for a, b in edges:
        d.line((pts[a][0], pts[a][1], pts[b][0], pts[b][1]), fill=line_col, width=3)
    for x, y in pts:
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=node_col, outline=(244, 245, 248, 255), width=1)


def draw_mode_content(d: ImageDraw.ImageDraw, mode: str, box: tuple[int, int, int, int], pal: dict, compact_copy: bool) -> None:
    x0, y0, x1, y1 = box
    d.text((x0 + 18, y0 + 18), {
        "boot": "COI",
        "gateway": "Gateway",
        "play_empty": "Play Hub",
        "play_selected": "Play Hub",
        "create": "Create Character",
        "system": "System",
    }[mode], font=F_H2, fill=pal["ink"])

    if mode == "boot":
        d.text(((x0 + x1) // 2, (y0 + y1) // 2 - 8), "Click center orb to open radial routes", anchor="mm", font=F_TX, fill=pal["ink_soft"])
        d.text(((x0 + x1) // 2, (y0 + y1) // 2 + 24), "No headline. Navigation is the graph.", anchor="mm", font=F_SM, fill=pal["ink_soft"])
        return

    if mode == "gateway":
        field(d, x0 + 18, y0 + 56, 332, "Email", pal)
        field(d, x0 + 18, y0 + 94, 332, "Password", pal)
        field(d, x0 + 18, y0 + 132, 332, "MFA (optional)", pal)
        button(d, x0 + 18, y0 + 172, 332, "Continue", pal, True)
        d.rounded_rectangle((x0 + 366, y0 + 56, x1 - 18, y0 + 238), radius=10, fill=(243, 245, 249, 255), outline=pal["panel_edge"], width=1)
        d.text((x0 + 380, y0 + 72), "Update Snapshot", font=F_TX, fill=pal["ink"])
        d.text((x0 + 380, y0 + 96), "Build: v1.0.157", font=F_SM, fill=pal["ink_soft"])
        d.text((x0 + 380, y0 + 120), "- Login + register + update merged.", font=F_SM, fill=pal["ink_soft"])
        d.text((x0 + 380, y0 + 138), "- Optional MFA kept in gateway.", font=F_SM, fill=pal["ink_soft"])
        button(d, x0 + 380, y0 + 188, (x1 - 18) - (x0 + 380), "Check Update", pal, True)
        return

    if mode == "play_empty":
        d.rounded_rectangle((x0 + 18, y0 + 56, x0 + 188, y1 - 52), radius=9, fill=(243, 245, 249, 255), outline=pal["panel_edge"], width=1)
        d.text((x0 + 28, y0 + 72), "Roster", font=F_TX, fill=pal["ink"])
        d.text((x0 + 28, y0 + 98), "No character selected", font=F_SM, fill=pal["ink_soft"])
        draw_graph_mini(d, (x0 + 202, y0 + 56, x1 - 18, y1 - 96), pal, muted=True)
        button(d, x0 + 18, y1 - 44, 118, "Save", pal, False)
        button(d, x0 + 146, y1 - 44, 118, "Play", pal, False)
        return

    if mode == "play_selected":
        d.rounded_rectangle((x0 + 18, y0 + 56, x0 + 188, y1 - 52), radius=9, fill=(243, 245, 249, 255), outline=pal["panel_edge"], width=1)
        d.text((x0 + 28, y0 + 72), "Roster", font=F_TX, fill=pal["ink"])
        d.rounded_rectangle((x0 + 28, y0 + 96, x0 + 176, y0 + 124), radius=8, fill=(30, 34, 44, 255), outline=pal["panel_edge"], width=1)
        d.text((x0 + 38, y0 + 110), "Sellsword", font=F_SM, fill=(246, 248, 250, 255))
        d.rounded_rectangle((x0 + 28, y0 + 132, x0 + 176, y0 + 160), radius=8, fill=(231, 234, 240, 255), outline=pal["panel_edge"], width=1)
        d.text((x0 + 38, y0 + 146), "Scout", font=F_SM, fill=pal["ink_soft"])
        draw_graph_mini(d, (x0 + 202, y0 + 56, x1 - 18, y1 - 96), pal, muted=False)
        d.text((x0 + 204, y1 - 82), "Node: Core  |  Routes: Resolve, Dexterity, Vitality", font=F_SM, fill=pal["ink_soft"])
        button(d, x0 + 18, y1 - 44, 118, "Save", pal, True)
        button(d, x0 + 146, y1 - 44, 118, "Play", pal, True)
        return

    if mode == "create":
        field(d, x0 + 18, y0 + 56, x1 - x0 - 36, "Character Name", pal)
        field(d, x0 + 18, y0 + 94, x1 - x0 - 36, "Sellsword", pal)
        field(d, x0 + 18, y0 + 132, x1 - x0 - 36, "Male", pal)
        lore = "Sellsword starts near Core and can branch to Resolve / Vitality paths."
        if compact_copy:
            lore = "Core start. Early routes: Resolve, Vitality."
        d.text((x0 + 18, y0 + 176), lore, font=F_TX, fill=pal["ink_soft"])
        draw_graph_mini(d, (x0 + 18, y0 + 206, x1 - 18, y1 - 88), pal, muted=False)
        button(d, x0 + 18, y1 - 44, x1 - x0 - 36, "Create Character", pal, True)
        return

    if mode == "system":
        d.text((x0 + 18, y0 + 62), "Audio", font=F_TX, fill=pal["ink"])
        for i, (name, amount) in enumerate([("Master", 0.72), ("Music", 0.58), ("Effects", 0.78), ("Interface", 0.52)]):
            yy = y0 + 96 + i * 38
            d.text((x0 + 18, yy - 10), name, font=F_SM, fill=pal["ink_soft"])
            d.rounded_rectangle((x0 + 98, yy - 4, x1 - 190, yy + 4), radius=3, fill=(211, 214, 223, 255), outline=pal["panel_edge"], width=1)
            bw = int((x1 - 190 - (x0 + 98)) * amount)
            d.rounded_rectangle((x0 + 98, yy - 4, x0 + 98 + bw, yy + 4), radius=3, fill=pal["button"], outline=pal["button"], width=1)
        d.rounded_rectangle((x1 - 174, y0 + 56, x1 - 18, y1 - 86), radius=10, fill=(243, 245, 249, 255), outline=pal["panel_edge"], width=1)
        d.text((x1 - 160, y0 + 74), "MFA", font=F_TX, fill=pal["ink"])
        button(d, x1 - 164, y0 + 96, 136, "MFA: ON", pal, True)
        button(d, x1 - 164, y0 + 136, 136, "Refresh", pal, False)
        button(d, x1 - 164, y0 + 176, 136, "Copy URI", pal, False)
        button(d, x1 - 164, y1 - 44, 136, "Apply", pal, True)


def radial_nodes(cx: int, cy: int, radius: int) -> list[tuple[str, float, str]]:
    return [
        ("gateway", -150, "enter"),
        ("play", -25, "launch"),
        ("create", 42, "forge"),
        ("system", 100, "system"),
        ("update", 158, "notes"),
        ("quit", 215, "quit"),
    ]


def render_screen(pass_no: int, mode: str, w: int, h: int) -> Image.Image:
    pal = pass_profile(pass_no)
    img = Image.new("RGBA", (w, h), pal["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_background(d, w, h, pal, seed=3011 + pass_no * 19 + len(mode) * 7)

    cx, cy = w // 2, h // 2
    orb_r = pal["orb_r"]
    node_r = pal["node_r"]

    # Draw radial skeleton first.
    selected_map = {
        "boot": "",
        "gateway": "gateway",
        "play_empty": "play",
        "play_selected": "play",
        "create": "create",
        "system": "system",
    }
    selected = selected_map[mode]

    center = (cx, cy)
    d.ellipse((cx - pal["ring_r"] - 28, cy - pal["ring_r"] - 28, cx + pal["ring_r"] + 28, cy + pal["ring_r"] + 28), outline=(170, 174, 185, 80), width=2)
    d.ellipse((cx - pal["ring_r"] + 6, cy - pal["ring_r"] + 6, cx + pal["ring_r"] - 6, cy + pal["ring_r"] - 6), outline=(180, 184, 194, 72), width=1)
    draw_blob(d, cx, cy, orb_r, pal, seed=9021 + pass_no, selected=(mode in {"boot", "gateway"}))
    d.text((cx, cy), "COI", anchor="mm", font=F_H2, fill=(242, 244, 249, 255))

    nodes = radial_nodes(cx, cy, pal["ring_r"])
    node_positions: dict[str, tuple[int, int]] = {}
    for i, (name, deg, route) in enumerate(nodes):
        nx, ny = polar(cx, cy, pal["ring_r"], deg)
        node_positions[name] = (nx, ny)
        draw_spoke(d, center, (nx, ny), route, pal, show_chip=pal["show_edge_chips"])
        draw_blob(d, nx, ny, node_r, pal, seed=10000 + i * 101 + pass_no, selected=(name == selected))
        label = {"gateway": "A", "play": "P", "create": "+", "system": "S", "update": "U", "quit": "Q"}[name]
        d.text((nx, ny), label, anchor="mm", font=F_H2, fill=(243, 245, 250, 255))
        if not pal["show_edge_chips"]:
            txt = {"gateway": "Auth", "play": "Play", "create": "Create", "system": "System", "update": "Update", "quit": "Quit"}[name]
            d.text((nx, ny + node_r + 16), txt, anchor="mm", font=F_SM, fill=pal["ink_soft"])

    # Focus panel follows selected node, preserving the radial as first-class UI.
    if mode == "boot":
        panel_cx, panel_cy = cx, cy
    else:
        target_name = "gateway" if mode == "gateway" else ("play" if mode.startswith("play_") else mode)
        tx, ty = node_positions[target_name]
        if pass_no >= 3:
            vx, vy = tx - cx, ty - cy
            panel_cx = cx + int(vx * 0.78) + int(-vy * 0.16)
            panel_cy = cy + int(vy * 0.78) + int(vx * 0.16)
        else:
            panel_cx = cx + int((tx - cx) * 0.42)
            panel_cy = cy + int((ty - cy) * 0.42)
        panel_cx, panel_cy = clamp_panel(panel_cx, panel_cy, pal["panel_w"], pal["panel_h"], w, h)
        if pass_no >= 3:
            # Ensure panel does not swallow the center orb.
            px0 = panel_cx - pal["panel_w"] // 2
            py0 = panel_cy - pal["panel_h"] // 2
            px1 = panel_cx + pal["panel_w"] // 2
            py1 = panel_cy + pal["panel_h"] // 2
            if px0 < cx + orb_r and px1 > cx - orb_r and py0 < cy + orb_r and py1 > cy - orb_r:
                panel_cx += int((tx - cx) * 0.18)
                panel_cy += int((ty - cy) * 0.18)
                panel_cx, panel_cy = clamp_panel(panel_cx, panel_cy, pal["panel_w"], pal["panel_h"], w, h)
        d.line((tx, ty, panel_cx, panel_cy), fill=(60, 64, 76, 160), width=2)
    panel = draw_panel(d, panel_cx, panel_cy, pal["panel_w"], pal["panel_h"], pal)
    draw_mode_content(d, mode, panel, pal, compact_copy=pal["compact_copy"])

    return img


def contact_sheet(paths: list[Path], out_path: Path) -> None:
    thumbs = []
    for p in paths:
        with Image.open(p) as im:
            thumbs.append((p.stem, im.convert("RGBA").resize((410, 230), Image.Resampling.LANCZOS)))

    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 420 + 24, rows * 272 + 24), (245, 246, 248, 255))
    d = ImageDraw.Draw(sheet, "RGBA")
    for i, (name, th) in enumerate(thumbs):
        c = i % cols
        r = i // cols
        x = 12 + c * 420
        y = 12 + r * 272
        d.rounded_rectangle((x, y, x + 410, y + 230), radius=10, fill=(241, 243, 247, 255), outline=(186, 190, 202, 255), width=1)
        sheet.paste(th, (x, y), th)
        d.text((x, y + 238), f"{name}.png", font=F_TX, fill=(30, 34, 44, 255))
    sheet.save(out_path)


def write_process(pass_no: int, pass_dir: Path) -> None:
    notes = {
        1: "Plan: establish radial IA with center COI orb and edge routes; Draw: baseline node shells + merged gateway; Review next: tighten spacing + reduce copy.",
        2: "Plan: tighten panel/menu density and spacing; Draw: reduced shell dimensions and less dead space; Review next: improve route readability.",
        3: "Plan: simplify copy and hierarchy; Draw: compact wording + stronger node focus; Review next: improve graph/menu visual balance.",
        4: "Plan: balance graph vs form content and reduce redundancy; Draw: clearer play/create payload weights; Review next: polish visual fidelity.",
        5: "Plan: final polish pass; Draw: refined black/white radial treatment, consistent in-node controls, and reduced redundancy; Review: ready for selection.",
    }
    (pass_dir / "process.md").write_text(
        f"# Radial Pass {pass_no:02d}\n\n- {notes[pass_no]}\n",
        encoding="utf-8",
    )


def render_pass(pass_no: int) -> None:
    if pass_no < 1 or pass_no > 5:
        raise SystemExit("pass must be 1..5")

    w, h = load_canvas_size()
    pass_dir = OUT_DIR / f"pass_{pass_no:02d}"
    pass_dir.mkdir(parents=True, exist_ok=True)

    modes = [
        "boot",
        "gateway",
        "play_empty",
        "play_selected",
        "create",
        "system",
    ]

    paths: list[Path] = []
    for mode in modes:
        img = render_screen(pass_no, mode, w, h)
        p = pass_dir / f"radial_{mode}.png"
        img.save(p)
        paths.append(p)

    contact_sheet(paths, pass_dir / "radial_contact_sheet.png")
    write_process(pass_no, pass_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", required=True, type=int)
    args = parser.parse_args()
    render_pass(args.pass_no)


if __name__ == "__main__":
    main()
