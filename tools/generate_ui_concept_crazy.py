#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 1366, 768

PALETTE = {
    "bg": (170, 187, 214, 255),
    "bg_alt": (185, 199, 220, 255),
    "panel": (198, 208, 223, 245),
    "panel_alt": (190, 202, 219, 245),
    "panel_soft": (205, 214, 228, 245),
    "line": (131, 158, 196, 255),
    "line_soft": (156, 177, 206, 220),
    "text": (36, 56, 88, 255),
    "text_soft": (70, 92, 124, 255),
    "text_muted": (88, 106, 132, 255),
    "primary": (86, 139, 214, 255),
    "primary_soft": (112, 156, 218, 255),
    "primary_text": (233, 240, 249, 255),
    "accent": (110, 187, 139, 255),
    "warn": (235, 176, 91, 255),
}

PASS_CONFIG = {
    1: {
        "arc_alpha": 86,
        "rail_alpha": 72,
        "sidebar_x": 20,
        "sidebar_w": 144,
        "ribbon_y": 122,
        "shell_x0": 182,
        "shell_x1": 1340,
        "roster_w": 254,
        "inspector_w": 170,
        "chamfer": 12,
        "note": "Pass 1: maximal asymmetry, aggressive framing, high ornament density.",
        "next": "Trim noise, increase readability, add stronger spacing rhythm.",
        "experimental": False,
    },
    2: {
        "arc_alpha": 72,
        "rail_alpha": 58,
        "sidebar_x": 22,
        "sidebar_w": 140,
        "ribbon_y": 122,
        "shell_x0": 186,
        "shell_x1": 1340,
        "roster_w": 262,
        "inspector_w": 178,
        "chamfer": 10,
        "note": "Pass 2: reduced background competition and cleaner shell boundaries.",
        "next": "Expand core task space and improve roster scanning capacity.",
        "experimental": True,
    },
    3: {
        "arc_alpha": 58,
        "rail_alpha": 46,
        "sidebar_x": 24,
        "sidebar_w": 138,
        "ribbon_y": 124,
        "shell_x0": 188,
        "shell_x1": 1338,
        "roster_w": 274,
        "inspector_w": 188,
        "chamfer": 10,
        "note": "Pass 3: widened actionable areas (roster + graph), reduced dead zones.",
        "next": "Tighten typography, unify control groups, remove micro-clutter.",
        "experimental": True,
    },
    4: {
        "arc_alpha": 44,
        "rail_alpha": 34,
        "sidebar_x": 24,
        "sidebar_w": 138,
        "ribbon_y": 126,
        "shell_x0": 190,
        "shell_x1": 1336,
        "roster_w": 286,
        "inspector_w": 202,
        "chamfer": 9,
        "note": "Pass 4: hierarchy tuning with calmer background and stronger grouping.",
        "next": "Final polish pass for balance and launch-ready readability.",
        "experimental": True,
    },
    5: {
        "arc_alpha": 34,
        "rail_alpha": 24,
        "sidebar_x": 24,
        "sidebar_w": 136,
        "ribbon_y": 128,
        "shell_x0": 192,
        "shell_x1": 1334,
        "roster_w": 296,
        "inspector_w": 214,
        "chamfer": 8,
        "note": "Pass 5: final balance; preserved bold identity with stable clarity.",
        "next": "Present candidate set for review and implementation pick.",
        "experimental": True,
    },
}

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "concept_art" / "option_crazy_flux"


def _font(cands: Iterable[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in cands:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT_TITLE = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 68)
FONT_H1 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 40)
FONT_H2 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 24)
FONT_H3 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 18)
FONT_BODY = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 16)
FONT_SM = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 14)
FONT_XS = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)


def rr(draw: ImageDraw.ImageDraw, rect, fill, outline=None, width=1, r=8):
    draw.rounded_rectangle(rect, radius=r, fill=fill, outline=outline, width=width)


def chamfer(draw: ImageDraw.ImageDraw, rect, fill, outline, width=1, c=10):
    x0, y0, x1, y1 = rect
    pts = [
        (x0 + c, y0),
        (x1 - c, y0),
        (x1, y0 + c),
        (x1, y1 - c),
        (x1 - c, y1),
        (x0 + c, y1),
        (x0, y1 - c),
        (x0, y0 + c),
    ]
    draw.polygon(pts, fill=fill, outline=outline)
    if width > 1:
        for i in range(1, width):
            p2 = [
                (x0 + c + i, y0 + i),
                (x1 - c - i, y0 + i),
                (x1 - i, y0 + c + i),
                (x1 - i, y1 - c - i),
                (x1 - c - i, y1 - i),
                (x0 + c + i, y1 - i),
                (x0 + i, y1 - c - i),
                (x0 + i, y0 + c + i),
            ]
            draw.line(p2 + [p2[0]], fill=outline, width=1)


def slanted(draw: ImageDraw.ImageDraw, rect, fill, outline, tilt=22, flip=False):
    x0, y0, x1, y1 = rect
    if flip:
        pts = [(x0, y0), (x1 - tilt, y0), (x1, y1), (x0 + tilt, y1)]
    else:
        pts = [(x0 + tilt, y0), (x1, y0), (x1 - tilt, y1), (x0, y1)]
    draw.polygon(pts, fill=fill, outline=outline)


def tbox(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, width_px: int, max_lines=20, line_h=20):
    x, y = xy
    avg = max(6, int(font.size * 0.62)) if hasattr(font, "size") else 8
    wrapped = textwrap.wrap(text, width=max(14, width_px // avg))[:max_lines]
    for i, ln in enumerate(wrapped):
        draw.text((x, y + i * line_h), ln, font=font, fill=fill)


def input_box(draw: ImageDraw.ImageDraw, rect, placeholder: str, value: str | None = None):
    rr(draw, rect, PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=6)
    x0, y0, x1, y1 = rect
    draw.text((x0 + 14, y0 + (y1 - y0) // 2), value if value else placeholder, anchor="lm", font=FONT_H3, fill=PALETTE["text_muted"])


def button(draw: ImageDraw.ImageDraw, rect, label: str, primary=False, active=False):
    fill = PALETTE["primary"] if primary or active else (224, 223, 214, 255)
    txt = PALETTE["primary_text"] if primary or active else PALETTE["text"]
    rr(draw, rect, fill, outline=PALETTE["line"], width=1, r=6)
    x0, y0, x1, y1 = rect
    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), label, anchor="mm", font=FONT_H3, fill=txt)


def draw_bg(img: Image.Image, cfg: dict):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=PALETTE["bg"])

    for r in range(180, 1180, 100):
        d.arc((W // 2 - r, -290 - r // 6, W // 2 + r, 450 + r // 8), 22, 162, fill=(146, 169, 202, cfg["arc_alpha"]), width=2)

    for x in range(-220, W + 320, 240):
        d.polygon([(x, 0), (x + 130, 0), (x + 350, H), (x + 220, H)], fill=(181, 196, 217, cfg["rail_alpha"]))

    d.rectangle((0, 0, W, 100), fill=(180, 198, 221, 208))
    d.line((24, 100, W - 24, 100), fill=PALETTE["line_soft"], width=1)
    d.text((W // 2, 48), "Children of Ikphelion", anchor="mm", font=FONT_TITLE, fill=PALETTE["text"])


def draw_sidebar(draw: ImageDraw.ImageDraw, cfg: dict, items: list[str], active: int | None):
    x = cfg["sidebar_x"]
    w = cfg["sidebar_w"]
    if not cfg.get("experimental"):
        chamfer(draw, (x, 156, x + w, 600), PALETTE["panel"], PALETTE["line"], c=cfg["chamfer"])
        by = 250
        for i, item in enumerate(items):
            button(draw, (x + 16, by + i * 44, x + w - 16, by + i * 44 + 34), item, active=(i == active))
        return

    rr(draw, (x, 156, x + w, 600), PALETTE["panel"], outline=PALETTE["line"], width=1, r=18)
    rail_x = x + 34
    draw.line((rail_x, 210, rail_x, 550), fill=PALETTE["line_soft"], width=3)
    by = 232
    for i, item in enumerate(items):
        cy = by + i * 52
        r = 13
        is_active = i == active
        draw.ellipse((rail_x - r, cy - r, rail_x + r, cy + r), fill=PALETTE["primary"] if is_active else PALETTE["panel_soft"], outline=PALETTE["line"], width=1)
        rr(
            draw,
            (rail_x + 20, cy - 15, x + w - 10, cy + 15),
            PALETTE["primary"] if is_active else (224, 223, 214, 255),
            outline=PALETTE["line"],
            width=1,
            r=8,
        )
        draw.text((rail_x + 27, cy), item, anchor="lm", font=FONT_SM, fill=PALETTE["primary_text"] if is_active else PALETTE["text"])


def draw_command_ribbon(draw: ImageDraw.ImageDraw, cfg: dict, show_help=True):
    x0, x1 = 206, 1160
    y = cfg["ribbon_y"]
    if cfg.get("experimental"):
        slanted(draw, (x0, y, x1, y + 40), PALETTE["panel_soft"], PALETTE["line"], tilt=22)
    else:
        rr(draw, (x0, y, x1, y + 40), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=8)
    draw.text((x0 + 18, y + 20), "Flux Command Bar: type or press Ctrl+K", anchor="lm", font=FONT_SM, fill=PALETTE["text_muted"])
    if show_help:
        button(draw, (x1 - 176, y + 6, x1 - 94, y + 34), "Palette")
        button(draw, (x1 - 88, y + 6, x1 - 16, y + 34), "Help")


def panel(draw: ImageDraw.ImageDraw, cfg: dict, rect, alt=False, flip=False, soft=False):
    if soft:
        fill = PALETTE["panel_soft"]
    else:
        fill = PALETTE["panel_alt"] if alt else PALETTE["panel"]

    if cfg.get("experimental"):
        slanted(draw, rect, fill, PALETTE["line_soft"] if alt else PALETTE["line"], tilt=20 if not alt else 14, flip=flip)
    else:
        chamfer(draw, rect, fill, PALETTE["line_soft"] if alt else PALETTE["line"], c=cfg["chamfer"] if not alt else cfg["chamfer"] - 2)


def draw_graph(draw: ImageDraw.ImageDraw, rect, mode: str, experimental=False):
    x0, y0, x1, y1 = rect
    if experimental:
        chamfer(draw, rect, PALETTE["panel"], PALETTE["line"], c=24)
    else:
        rr(draw, rect, PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    gx0, gy0, gx1, gy1 = x0 + 18, y0 + 20, x1 - 18, y1 - 20
    if experimental:
        chamfer(draw, (gx0, gy0, gx1, gy1), PALETTE["panel_alt"], PALETTE["line_soft"], c=18)
    else:
        rr(draw, (gx0, gy0, gx1, gy1), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=6)

    for x in range(gx0 + 24, gx1 - 12, 72):
        draw.line((x, gy0 + 10, x, gy1 - 10), fill=(156, 177, 206, 130), width=1)
    for y in range(gy0 + 14, gy1 - 10, 72):
        draw.line((gx0 + 10, y, gx1 - 10, y), fill=(156, 177, 206, 130), width=1)
    if experimental:
        cx = (gx0 + gx1) // 2
        cy = (gy0 + gy1) // 2
        radius = min((gx1 - gx0), (gy1 - gy0)) // 3
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(150, 172, 203, 110), width=1)

    if mode == "empty":
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 - 8), "No character selected", anchor="mm", font=FONT_H3, fill=PALETTE["text_muted"])
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 + 14), "Choose a roster slot to load graph state.", anchor="mm", font=FONT_XS, fill=PALETTE["text_muted"])
        return

    gw = gx1 - gx0
    gh = gy1 - gy0
    nodes_rel = {
        "Core": (0.52, 0.74, PALETTE["primary"]),
        "Resolve": (0.38, 0.74, PALETTE["primary_soft"]),
        "Dexterity": (0.54, 0.54, PALETTE["primary_soft"]),
        "Vitality": (0.48, 0.90, PALETTE["primary_soft"]),
        "Agility": (0.64, 0.90, PALETTE["primary_soft"]),
        "Willpower": (0.64, 0.62, PALETTE["primary_soft"]),
        "Quick Strike": (0.20, 0.66, PALETTE["accent"]),
        "Bandage": (0.58, 0.36, PALETTE["warn"]),
        "Ember": (0.84, 0.78, PALETTE["warn"]),
    }
    nodes = {
        name: (int(gx0 + rx * gw), int(gy0 + ry * gh), col)
        for name, (rx, ry, col) in nodes_rel.items()
    }
    edges = [
        ("Core", "Resolve"),
        ("Core", "Dexterity"),
        ("Core", "Vitality"),
        ("Core", "Agility"),
        ("Core", "Willpower"),
        ("Resolve", "Quick Strike"),
        ("Dexterity", "Bandage"),
        ("Agility", "Ember"),
    ]
    for a, b in edges:
        ax, ay, _ = nodes[a]
        bx, by, _ = nodes[b]
        draw.line((ax, ay, bx, by), fill=(133, 160, 198), width=3)

    for name, (nx, ny, col) in nodes.items():
        if mode == "create" and name in {"Quick Strike", "Bandage", "Ember"}:
            col = (198, 208, 223)
        r = 12 if name == "Core" else 10
        draw.ellipse((nx - r, ny - r, nx + r, ny + r), fill=col, outline=PALETTE["line"], width=1)
        draw.text((nx, min(gy1 - 10, ny + 20)), name, anchor="mm", font=FONT_XS, fill=PALETTE["text_soft"])

    if mode == "create":
        draw.text((gx0 + 20, gy0 + 18), "Archetype Start: Core -> Resolve", font=FONT_XS, fill=PALETTE["accent"])


def draw_roster(draw: ImageDraw.ImageDraw, cfg: dict, rect, selected: bool):
    x0, y0, x1, y1 = rect
    panel(draw, cfg, rect, alt=False, flip=False)
    draw.text((x0 + 16, y0 + 18), "Characters", font=FONT_H2, fill=PALETTE["text"])
    button(draw, (x0 + 16, y0 + 50, x1 - 16, y0 + 84), "Create Character")

    rr(draw, (x0 + 16, y0 + 96, x1 - 16, y1 - 16), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=6)
    if not selected:
        tbox(draw, (x0 + 26, y0 + 122), "No characters yet. Create one and save an offline build path.", FONT_SM, PALETTE["text_muted"], x1 - x0 - 48, max_lines=5)
        return

    rr(draw, (x0 + 26, y0 + 110, x1 - 26, y0 + 160), PALETTE["primary"], outline=PALETTE["line"], width=1, r=5)
    draw.text((x0 + 38, y0 + 126), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
    draw.text((x0 + 38, y0 + 146), "Lv 5 | Ironhold", font=FONT_SM, fill=PALETTE["primary_text"])
    rr(draw, (x0 + 26, y0 + 170, x1 - 26, y0 + 220), PALETTE["panel"], outline=PALETTE["line"], width=1, r=5)
    draw.text((x0 + 38, y0 + 186), "Scout", font=FONT_H3, fill=PALETTE["text"])
    draw.text((x0 + 38, y0 + 206), "Lv 2 | Khar Grotto", font=FONT_SM, fill=PALETTE["text_muted"])

    for i in range(3):
        py = y0 + 228 + i * 48
        rr(draw, (x0 + 26, py, x1 - 26, py + 40), PALETTE["panel"], outline=PALETTE["line_soft"], width=1, r=5)
        draw.text((x0 + 38, py + 14), f"Empty Slot {i + 1}", font=FONT_SM, fill=PALETTE["text_muted"])


def base_canvas(cfg: dict) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    draw_bg(img, cfg)
    return img, ImageDraw.Draw(img, "RGBA")


def scene_login(cfg: dict) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Login", "Register", "Quit"], 0)
    draw_command_ribbon(d, cfg, show_help=True)

    shell = (cfg["shell_x0"], 170, cfg["shell_x1"], 738)
    panel(d, cfg, shell, alt=False)
    panel(d, cfg, (shell[0] + 24, 194, 782, 716), alt=True, flip=False)
    panel(d, cfg, (798, 194, 1316, 716), alt=True, flip=True)

    d.text((shell[0] + 48, 222), "Account Access", font=FONT_H2, fill=PALETTE["text"])
    input_box(d, (shell[0] + 48, 264, 762, 298), "Email", "admin@admin.com")
    input_box(d, (shell[0] + 48, 308, 762, 342), "Password")
    input_box(d, (shell[0] + 48, 352, 762, 386), "MFA Code (optional)")
    button(d, (shell[0] + 48, 404, 762, 442), "Login", primary=True)
    d.text((shell[0] + 48, 686), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
    d.text((748, 686), "MFA available in Security settings", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((818, 222), "Quick Actions", font=FONT_H2, fill=PALETTE["text"])
    tbox(d, (818, 258), "login\nregister\ncheck update\npatch notes", FONT_SM, PALETTE["text_soft"], 474, max_lines=10)
    d.text((818, 356), "Update", font=FONT_H3, fill=PALETTE["text"])
    rr(d, (818, 382, 1298, 624), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
    d.text((836, 402), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])
    tbox(d, (836, 434), "- Graph is available in selection and creation.\n- Save Build can happen offline before launch.", FONT_SM, PALETTE["text_soft"], 442, max_lines=9)
    button(d, (818, 638, 1298, 674), "Check for Update")
    return img


def scene_register(cfg: dict) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Login", "Register", "Quit"], 1)
    draw_command_ribbon(d, cfg, show_help=False)

    shell = (cfg["shell_x0"], 170, cfg["shell_x1"], 738)
    panel(d, cfg, shell, alt=False)
    panel(d, cfg, (shell[0] + 24, 194, 770, 716), alt=True, flip=False)
    panel(d, cfg, (786, 194, 1316, 716), alt=True, flip=True)

    d.text((shell[0] + 48, 222), "Create Account", font=FONT_H2, fill=PALETTE["text"])
    input_box(d, (shell[0] + 48, 264, 750, 298), "Display Name")
    input_box(d, (shell[0] + 48, 308, 750, 342), "Email")
    input_box(d, (shell[0] + 48, 352, 750, 386), "Password")
    button(d, (shell[0] + 48, 404, 750, 442), "Register", primary=True)

    d.text((808, 222), "Onboarding", font=FONT_H2, fill=PALETTE["text"])
    tbox(d, (808, 258), "After registration:\n1. Create character\n2. Review start graph\n3. Save starter build\n4. Launch", FONT_H3, PALETTE["text_soft"], 486, max_lines=9, line_h=34)
    button(d, (808, 636, 1292, 672), "Back to Login")
    return img


def scene_play(cfg: dict, selected: bool) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)
    draw_command_ribbon(d, cfg, show_help=True)

    shell = (cfg["shell_x0"], 170, cfg["shell_x1"], 738)
    panel(d, cfg, shell, alt=False)

    roster = (shell[0] + 24, 194, shell[0] + 24 + cfg["roster_w"], 716)
    draw_roster(d, cfg, roster, selected)

    inspector_x0 = shell[2] - cfg["inspector_w"] - 18
    inspector = (inspector_x0, 194, shell[2] - 18, 716)
    graph = (roster[2] + 14, 194, inspector_x0 - 14, 716)

    panel(d, cfg, graph, alt=True, flip=False)
    d.text((graph[0] + 20, 222), "Graph Canvas", font=FONT_H2, fill=PALETTE["text"])
    draw_graph(d, (graph[0] + 20, 246, graph[2] - 20, 648), "selected" if selected else "empty", experimental=cfg.get("experimental", False))

    rr(d, (graph[0] + 20, 656, graph[2] - 20, 688), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=4)
    button(d, (graph[0] + 26, 659, graph[0] + 192, 686), "Save Build", primary=selected)
    button(d, (graph[0] + 200, 659, graph[0] + 320, 686), "Reset")
    button(d, (graph[0] + 328, 659, graph[0] + 440, 686), "Play")
    footer_msg = "Offline edits are saved before gameplay entry."
    if cfg.get("pass_no", 1) >= 3:
        footer_msg = "Offline build is saved before launch."
    tbox(d, (graph[0] + 450, 660), footer_msg, FONT_XS, PALETTE["text_muted"], (graph[2] - 20) - (graph[0] + 450) - 8, max_lines=2, line_h=12)

    panel(d, cfg, inspector, alt=True, flip=True)
    d.text((inspector[0] + 16, 222), "Inspector", font=FONT_H2, fill=PALETTE["text"])
    if selected:
        inspect_text = "Core\n+2 base stats\n\nRoutes:\n- Resolve\n- Dexterity\n- Vitality"
        if cfg.get("pass_no", 1) >= 3:
            inspect_text = "Node: Core\nBonus: +2 base stats\n\nLinks:\nResolve\nDexterity\nVitality"
        tbox(d, (inspector[0] + 16, 258), inspect_text, FONT_H3, PALETTE["text_soft"], cfg["inspector_w"] - 34, max_lines=11)
        button(d, (inspector[0] + 16, 622, inspector[2] - 16, 658), "Save Build", primary=True)
    else:
        tbox(d, (inspector[0] + 16, 258), "No character selected", FONT_H3, PALETTE["text_muted"], cfg["inspector_w"] - 34, max_lines=2)
    return img


def scene_create(cfg: dict) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1)
    draw_command_ribbon(d, cfg, show_help=True)

    shell = (cfg["shell_x0"], 170, cfg["shell_x1"], 738)
    panel(d, cfg, shell, alt=False)

    left = (shell[0] + 24, 194, shell[0] + 334, 716)
    mid = (left[2] + 14, 194, shell[0] + 844, 716)
    right = (mid[2] + 14, 194, shell[2] - 18, 716)

    panel(d, cfg, left, alt=True, flip=False)
    d.text((left[0] + 18, 222), "Archetypes", font=FONT_H2, fill=PALETTE["text"])
    rr(d, (left[0] + 18, 248, left[2] - 18, 312), PALETTE["primary"], outline=PALETTE["line"], width=1, r=5)
    d.text((left[0] + 30, 268), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
    d.text((left[0] + 30, 288), "Durable melee opener", font=FONT_SM, fill=PALETTE["primary_text"])
    rr(d, (left[0] + 18, 322, left[2] - 18, 386), PALETTE["panel"], outline=PALETTE["line"], width=1, r=5)
    d.text((left[0] + 30, 342), "Scout", font=FONT_H3, fill=PALETTE["text"])
    d.text((left[0] + 30, 362), "Mobile precision style", font=FONT_SM, fill=PALETTE["text_muted"])

    panel(d, cfg, mid, alt=True, flip=True)
    d.text((mid[0] + 18, 222), "Identity & Core Choices", font=FONT_H2, fill=PALETTE["text"])
    input_box(d, (mid[0] + 18, 258, mid[2] - 18, 292), "Character Name")
    input_box(d, (mid[0] + 18, 302, mid[2] - 18, 336), "Character Type", "Sellsword")
    input_box(d, (mid[0] + 18, 346, mid[2] - 18, 380), "Sex", "Male")
    rr(d, (mid[0] + 18, 400, mid[2] - 18, 622), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
    d.text((mid[0] + 36, 426), "Lore", font=FONT_H2, fill=PALETTE["text"])
    tbox(d, (mid[0] + 36, 462), "Sellswords are frontline contractors hardened by border conflicts. They are intended as a straightforward entry with strong survivability and stable momentum in early progression.", FONT_H3, PALETTE["text_soft"], (mid[2] - mid[0]) - 56, max_lines=8, line_h=32)
    button(d, (mid[0] + 18, 648, mid[2] - 18, 684), "Create Character", primary=True)

    panel(d, cfg, right, alt=True, flip=False)
    d.text((right[0] + 18, 222), "Starting Graph", font=FONT_H2, fill=PALETTE["text"])
    draw_graph(d, (right[0] + 18, 256, right[2] - 18, 616), "create", experimental=cfg.get("experimental", False))
    button(d, (right[0] + 18, 648, right[2] - 18, 684), "Back to Play")
    return img


def scene_update(cfg: dict) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Login", "Register", "Quit"], None)
    draw_command_ribbon(d, cfg, show_help=False)

    panel(d, cfg, (286, 194, 1120, 622), alt=False, flip=True)
    rr(d, (312, 220, 1094, 262), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=5)
    d.text((328, 232), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])

    rr(d, (312, 274, 1094, 536), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=5)
    d.text((328, 294), "Release Notes", font=FONT_H2, fill=PALETTE["text"])
    tbox(d, (328, 330), "- Graph available in both selection and creation paths.\n- Save Build persists pre-launch graph edits.\n- Visual hierarchy refined for faster scanning.", FONT_H3, PALETTE["text_soft"], 742, max_lines=10, line_h=36)
    button(d, (312, 548, 1094, 586), "Check for Update", primary=True)
    return img


def scene_settings_audio(cfg: dict) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 2)
    draw_command_ribbon(d, cfg, show_help=False)

    panel(d, cfg, (186, 170, 1306, 728), alt=False)
    d.text((210, 198), "Settings", font=FONT_H1, fill=PALETTE["text"])
    button(d, (214, 226, 302, 258), "Video")
    button(d, (308, 226, 396, 258), "Audio", primary=True)
    button(d, (402, 226, 496, 258), "Security")

    rr(d, (214, 272, 1282, 666), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=6)
    d.text((232, 296), "Audio Mix", font=FONT_H2, fill=PALETTE["text"])
    labels = ["Master", "Music", "Effects", "Interface"]
    vals = [0.78, 0.62, 0.83, 0.57]
    for i, (lbl, val) in enumerate(zip(labels, vals)):
        y = 336 + i * 70
        d.text((232, y), lbl, font=FONT_H3, fill=PALETTE["text"])
        rr(d, (232, y + 24, 1180, y + 30), (184, 201, 223, 255), r=3)
        rr(d, (232, y + 24, int(232 + 948 * val), y + 30), PALETTE["primary"], r=3)
    button(d, (1160, 624, 1270, 656), "Apply", primary=True)
    return img


def scene_settings_security(cfg: dict) -> Image.Image:
    img, d = base_canvas(cfg)
    draw_sidebar(d, cfg, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 2)
    draw_command_ribbon(d, cfg, show_help=False)

    panel(d, cfg, (186, 170, 1306, 728), alt=False)
    d.text((210, 198), "Settings", font=FONT_H1, fill=PALETTE["text"])
    button(d, (214, 226, 302, 258), "Video")
    button(d, (308, 226, 396, 258), "Audio")
    button(d, (402, 226, 496, 258), "Security", primary=True)

    rr(d, (214, 272, 1282, 706), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=6)
    d.text((234, 296), "Multi-factor Authentication", font=FONT_H2, fill=PALETTE["text"])
    button(d, (956, 292, 1060, 324), "MFA: ON", primary=True)
    button(d, (1074, 292, 1168, 324), "Refresh QR")
    button(d, (1182, 292, 1258, 324), "Copy URI")

    rr(d, (234, 344, 702, 650), PALETTE["panel"], outline=PALETTE["line_soft"], width=1, r=5)
    rr(d, (720, 344, 1258, 650), PALETTE["panel"], outline=PALETTE["line_soft"], width=1, r=5)
    qx, qy = 310, 402
    for i in range(21):
        for j in range(21):
            if (i * 5 + j * 3) % 7 in {0, 1}:
                d.rectangle((qx + i * 12, qy + j * 12, qx + i * 12 + 7, qy + j * 12 + 7), fill=PALETTE["text"])
    tbox(d, (740, 370), "MFA is active for this account.\n\nSecret: D772WD3GP3ITL4JCP3YGNG5DGAJOSTIH\n\nProvisioning URI:\notpauth://totp/karaxas:account@email.com?issuer=karaxas", FONT_H3, PALETTE["text_soft"], 500, max_lines=8, line_h=42)
    d.text((234, 676), "Status: MFA QR ready.", font=FONT_H3, fill=PALETTE["accent"])
    return img


def make_contact_sheet(images: list[Path], out_path: Path):
    thumbs = []
    for p in images:
        img = Image.open(p).convert("RGBA")
        thumb = img.resize((420, 236), Image.Resampling.LANCZOS)
        thumbs.append((p.stem, thumb))

    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 430 + 20, rows * 276 + 20), PALETTE["bg"])
    d = ImageDraw.Draw(sheet, "RGBA")

    for i, (name, thumb) in enumerate(thumbs):
        c = i % cols
        r = i // cols
        x = 10 + c * 430
        y = 10 + r * 276
        rr(d, (x, y, x + 420, y + 236), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=4)
        sheet.paste(thumb, (x, y), thumb)
        d.text((x, y + 244), f"{name}.png", font=FONT_SM, fill=PALETTE["text"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def render_pass(pass_no: int):
    cfg = dict(PASS_CONFIG[pass_no])
    cfg["pass_no"] = pass_no
    out = OUT_ROOT / f"pass_{pass_no}"
    out.mkdir(parents=True, exist_ok=True)

    scenes = {
        "crazy_login": scene_login(cfg),
        "crazy_register": scene_register(cfg),
        "crazy_update": scene_update(cfg),
        "crazy_play_empty": scene_play(cfg, selected=False),
        "crazy_play_selected": scene_play(cfg, selected=True),
        "crazy_create": scene_create(cfg),
        "crazy_settings_audio": scene_settings_audio(cfg),
        "crazy_settings_security": scene_settings_security(cfg),
    }

    saved = []
    for name, img in scenes.items():
        path = out / f"{name}.png"
        img.save(path)
        saved.append(path)
    make_contact_sheet(saved, out / "crazy_contact_sheet.png")


def write_pass_notes(rendered_passes: list[int]):
    lines = ["# Crazy Concept Iteration Notes", ""]
    for i in rendered_passes:
        cfg = PASS_CONFIG[i]
        lines.append(f"## Pass {i}")
        lines.append(f"- Analysis: {cfg['note']}")
        lines.append(f"- Improvement plan: {cfg['next']}")
        lines.append("")
    (OUT_ROOT / "pass_notes.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", type=int, choices=[1, 2, 3, 4, 5], help="Render only one pass.")
    args = parser.parse_args()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.pass_no:
        render_pass(args.pass_no)
        rendered = [i for i in range(1, 6) if (OUT_ROOT / f"pass_{i}").exists()]
        write_pass_notes(rendered)
        return

    for i in range(1, 6):
        render_pass(i)
    write_pass_notes([1, 2, 3, 4, 5])


if __name__ == "__main__":
    main()
