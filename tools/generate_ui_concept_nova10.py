#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import textwrap
import argparse

from PIL import Image, ImageDraw, ImageFont

W, H = 1366, 768

PALETTE = {
    "bg": (168, 186, 213, 255),
    "bg_soft": (181, 198, 221, 255),
    "panel": (198, 209, 223, 248),
    "panel_alt": (190, 202, 219, 248),
    "panel_soft": (206, 215, 228, 248),
    "line": (131, 158, 196, 255),
    "line_soft": (154, 177, 207, 220),
    "text": (35, 56, 90, 255),
    "text_soft": (70, 92, 124, 255),
    "text_muted": (89, 106, 132, 255),
    "primary": (86, 139, 214, 255),
    "primary_soft": (112, 156, 218, 255),
    "primary_text": (234, 241, 250, 255),
    "accent": (110, 187, 139, 255),
    "warn": (234, 176, 90, 255),
}

PASS_SPECS = {
    1: {
        "name": "Pass 1 - Wedge Dock",
        "analysis": "Start with an aggressive wedge-shell architecture and command-strip login fusion.",
        "plan": "Test whether angled shells improve identity without hurting scan flow.",
        "layout": "wedge",
        "nav": "nodes",
        "density": 0,
    },
    2: {
        "name": "Pass 2 - Floating Deck",
        "analysis": "Shift into floating deck cards with compact rail labels and less container bulk.",
        "plan": "Check if card layering is clearer than hard panel borders.",
        "layout": "float",
        "nav": "pills",
        "density": 0,
    },
    3: {
        "name": "Pass 3 - Stage + Drawer",
        "analysis": "Use a stage metaphor: primary canvas + collapsible utility drawer + action runway.",
        "plan": "Validate launch/read/edit actions in one horizontal flow.",
        "layout": "stage",
        "nav": "rail",
        "density": 0,
    },
    4: {
        "name": "Pass 4 - Hybrid Fusion",
        "analysis": "Merge strongest pieces from first 3 passes into a hybrid shell.",
        "plan": "Increase information hierarchy and remove redundant labels.",
        "layout": "hybrid",
        "nav": "rail",
        "density": 1,
    },
    5: {
        "name": "Pass 5 - Hub Compression",
        "analysis": "Compress auth and update into one workspace; keep register as mode, not a disconnected screen.",
        "plan": "Reduce clicks while keeping full function parity.",
        "layout": "hybrid",
        "nav": "rail",
        "density": 2,
    },
    6: {
        "name": "Pass 6 - Roster Expansion",
        "analysis": "Expand roster handling and make graph controls more explicit for offline saves.",
        "plan": "Improve capacity and legibility in character selection.",
        "layout": "stage",
        "nav": "nodes",
        "density": 3,
    },
    7: {
        "name": "Pass 7 - Control Discipline",
        "analysis": "Normalize control grouping: mode chips, action strip, and consistent side utilities.",
        "plan": "Lower cognitive overhead while preserving distinct style.",
        "layout": "float",
        "nav": "pills",
        "density": 4,
    },
    8: {
        "name": "Pass 8 - Typography Pass",
        "analysis": "Tune text scale and line breaks; remove cramped inspector/status copy.",
        "plan": "Increase readability and reduce clipping risks.",
        "layout": "hybrid",
        "nav": "rail",
        "density": 5,
    },
    9: {
        "name": "Pass 9 - Balance Pass",
        "analysis": "Rebalance whitespace and panel weight to avoid crowding at 1366x768.",
        "plan": "Land near-final arrangement for review.",
        "layout": "hybrid",
        "nav": "rail",
        "density": 6,
    },
    10: {
        "name": "Pass 10 - Presentation Candidate",
        "analysis": "Finalize the strongest variant with stable hierarchy and minimal redundancy.",
        "plan": "Prepare for implementation decision.",
        "layout": "hybrid",
        "nav": "rail",
        "density": 7,
    },
}

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "concept_art" / "option_nova_10pass"
CURRENT_DENSITY = 0


def _font(cands: Iterable[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in cands:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT_TITLE = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 52)
FONT_H1 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 34)
FONT_H2 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 24)
FONT_H3 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 18)
FONT_SM = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 14)
FONT_XS = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)


def rr(draw: ImageDraw.ImageDraw, rect, fill, outline=None, width=1, r=8):
    draw.rounded_rectangle(rect, radius=r, fill=fill, outline=outline, width=width)


def tbox(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, width_px: int, max_lines=20, line_h=20):
    x, y = xy
    avg = max(6, int(font.size * 0.62)) if hasattr(font, "size") else 8
    wrapped = textwrap.wrap(text, width=max(12, width_px // avg))[:max_lines]
    for i, ln in enumerate(wrapped):
        draw.text((x, y + i * line_h), ln, font=font, fill=fill)


def poly(draw: ImageDraw.ImageDraw, rect, fill, outline, style: str):
    x0, y0, x1, y1 = rect
    if style == "wedge":
        pts = [(x0 + 20, y0), (x1, y0), (x1 - 20, y1), (x0, y1)]
    elif style == "float":
        pts = [(x0 + 10, y0), (x1 - 10, y0), (x1, y0 + 10), (x1, y1 - 10), (x1 - 10, y1), (x0 + 10, y1), (x0, y1 - 10), (x0, y0 + 10)]
    elif style == "stage":
        pts = [(x0 + 24, y0), (x1 - 24, y0), (x1, y0 + 24), (x1, y1 - 12), (x1 - 12, y1), (x0 + 12, y1), (x0, y1 - 24), (x0, y0 + 12)]
    else:
        # Hybrid shape: combined notches + angled corners.
        mx = (x0 + x1) // 2
        pts = [
            (x0 + 20, y0),
            (mx - 40, y0),
            (mx - 24, y0 + 10),
            (mx + 24, y0 + 10),
            (mx + 40, y0),
            (x1 - 20, y0),
            (x1, y0 + 20),
            (x1, y1 - 20),
            (x1 - 20, y1),
            (mx + 40, y1),
            (mx + 24, y1 - 10),
            (mx - 24, y1 - 10),
            (mx - 40, y1),
            (x0 + 20, y1),
            (x0, y1 - 20),
            (x0, y0 + 20),
        ]
    draw.polygon(pts, fill=fill, outline=outline)


def button(draw: ImageDraw.ImageDraw, rect, label: str, primary=False, active=False):
    if primary or active:
        fill = PALETTE["primary"]
    else:
        fill = (229, 227, 216, 255) if CURRENT_DENSITY >= 5 else (224, 223, 214, 255)
    txt = PALETTE["primary_text"] if primary or active else PALETTE["text"]
    rr(draw, rect, fill, outline=PALETTE["line"], width=1, r=6)
    x0, y0, x1, y1 = rect
    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), label, anchor="mm", font=FONT_H3, fill=txt)


def input_box(draw: ImageDraw.ImageDraw, rect, placeholder: str, value: str | None = None):
    rr(draw, rect, PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=6)
    x0, y0, x1, y1 = rect
    draw.text((x0 + 12, (y0 + y1) // 2), value if value else placeholder, anchor="lm", font=FONT_H3, fill=PALETTE["text_muted"])


def draw_brand_mark(draw: ImageDraw.ImageDraw, density: int):
    cx, cy = W // 2, 52
    outer = 66
    inner = 48
    trim_alpha = max(120, 190 - density * 6)
    # Crest rings.
    draw.ellipse((cx - outer, cy - outer, cx + outer, cy + outer), fill=(184, 201, 223, 220), outline=PALETTE["line"], width=2)
    draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=(196, 208, 224, 255), outline=PALETTE["line_soft"], width=2)
    # Top half halo arc.
    draw.arc((cx - 78, cy - 78, cx + 78, cy + 78), start=198, end=342, fill=(143, 170, 206, trim_alpha), width=3)
    # Lower split plate.
    draw.polygon([(cx - 44, cy + 8), (cx + 44, cy + 8), (cx + 30, cy + 36), (cx - 30, cy + 36)], fill=(187, 201, 222, 240), outline=PALETTE["line"])
    # Corner shards for uniqueness.
    draw.polygon([(cx - 64, cy - 12), (cx - 48, cy - 32), (cx - 42, cy - 10)], fill=(171, 191, 218, 200), outline=PALETTE["line_soft"])
    draw.polygon([(cx + 64, cy - 12), (cx + 48, cy - 32), (cx + 42, cy - 10)], fill=(171, 191, 218, 200), outline=PALETTE["line_soft"])
    # Initials.
    draw.text((cx, cy + 2), "COI", anchor="mm", font=FONT_TITLE, fill=PALETTE["text"])


def draw_bg(draw: ImageDraw.ImageDraw, density: int):
    draw.rectangle((0, 0, W, H), fill=PALETTE["bg"])
    for i in range(7):
        alpha = max(12, 52 - density * 5)
        x0 = 40 + i * 180
        draw.polygon([(x0, 0), (x0 + 96, 0), (x0 + 220, H), (x0 + 124, H)], fill=(183, 198, 220, alpha))
    if density >= 5:
        draw.rectangle((0, 108, W, H), fill=(170, 187, 214, 22))
    draw.rectangle((0, 0, W, 102), fill=(182, 199, 221, 214))
    draw.line((24, 102, W - 24, 102), fill=PALETTE["line_soft"], width=1)
    draw_brand_mark(draw, density)
    # Original line-art sigils (custom drawn, not image assets).
    alpha = max(28, 64 - density * 4)
    # Left sigil: crossed blades.
    lx, ly = 118, 64
    draw.line((lx - 24, ly + 18, lx + 22, ly - 18), fill=(134, 160, 196, alpha), width=3)
    draw.line((lx - 22, ly - 18, lx + 24, ly + 18), fill=(134, 160, 196, alpha), width=3)
    draw.ellipse((lx - 6, ly - 6, lx + 6, ly + 6), outline=(134, 160, 196, alpha), width=2)
    # Right sigil: shield shard.
    rx, ry = W - 118, 62
    draw.polygon([(rx, ry - 24), (rx + 22, ry - 8), (rx + 16, ry + 18), (rx, ry + 28), (rx - 16, ry + 18), (rx - 22, ry - 8)], outline=(134, 160, 196, alpha), fill=(176, 195, 220, alpha // 2))


def draw_nav(draw: ImageDraw.ImageDraw, spec: dict, items: list[str], active: int | None, auth=False):
    x0, y0, x1, y1 = 24, 158, 160, 598
    poly(draw, (x0, y0, x1, y1), PALETTE["panel"], PALETTE["line"], spec["layout"])
    if spec["nav"] == "nodes":
        draw.line((56, 210, 56, 548), fill=PALETTE["line_soft"], width=3)
        by = 232
        for i, item in enumerate(items):
            cy = by + i * 52
            r = 12
            draw.ellipse((56 - r, cy - r, 56 + r, cy + r), fill=PALETTE["primary"] if i == active else PALETTE["panel_soft"], outline=PALETTE["line"], width=1)
            rr(draw, (78, cy - 15, 150, cy + 15), PALETTE["primary"] if i == active else (224, 223, 214, 255), outline=PALETTE["line"], width=1, r=8)
            draw.text((114, cy), item[:7], anchor="mm", font=FONT_XS, fill=PALETTE["primary_text"] if i == active else PALETTE["text"])
    elif spec["nav"] == "pills":
        by = 240
        for i, item in enumerate(items):
            button(draw, (40, by + i * 44, 144, by + i * 44 + 34), item, active=i == active)
    else:
        by = 232
        if CURRENT_DENSITY >= 6:
            glyphs = ["L", "R", "C", "S", "Q", "X"]
            for i, item in enumerate(items):
                cy = by + i * 52
                rr(draw, (40, cy - 13, 72, cy + 13), PALETTE["primary"] if i == active else PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=6)
                draw.text((56, cy), glyphs[i] if i < len(glyphs) else "•", anchor="mm", font=FONT_XS, fill=PALETTE["primary_text"] if i == active else PALETTE["text"])
            if active is not None and active < len(items):
                draw.text((82, 560), items[active], anchor="lm", font=FONT_XS, fill=PALETTE["text_muted"])
        else:
            for i, item in enumerate(items):
                draw.ellipse((44, by + i * 52 - 10, 64, by + i * 52 + 10), fill=PALETTE["primary"] if i == active else PALETTE["panel_soft"], outline=PALETTE["line"], width=1)
                draw.text((82, by + i * 52), item, anchor="lm", font=FONT_XS, fill=PALETTE["text"])


def draw_ribbon(draw: ImageDraw.ImageDraw, spec: dict, text="Nova Flow: one workspace, multiple modes"):
    x0, x1 = (236, 1132) if CURRENT_DENSITY >= 6 else (206, 1162)
    poly(draw, (x0, 128, x1, 168), PALETTE["panel_soft"], PALETTE["line"], spec["layout"])
    draw.text((x0 + 18, 148), text, anchor="lm", font=FONT_SM, fill=PALETTE["text_muted"])
    button(draw, (x1 - 176, 134, x1 - 92, 162), "Palette")
    button(draw, (x1 - 84, 134, x1 - 12, 162), "Help")


def draw_graph(draw: ImageDraw.ImageDraw, rect, mode: str, tight=False):
    x0, y0, x1, y1 = rect
    rr(draw, rect, PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    gx0, gy0, gx1, gy1 = x0 + 18, y0 + 18, x1 - 18, y1 - 18
    rr(draw, (gx0, gy0, gx1, gy1), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=6)
    step = 70 if not tight else 76
    for x in range(gx0 + 20, gx1 - 12, step):
        draw.line((x, gy0 + 10, x, gy1 - 10), fill=(156, 177, 206, 140), width=1)
    for y in range(gy0 + 10, gy1 - 10, step):
        draw.line((gx0 + 10, y, gx1 - 10, y), fill=(156, 177, 206, 140), width=1)
    if mode == "empty":
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 - 8), "No character selected", anchor="mm", font=FONT_H3, fill=PALETTE["text_muted"])
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 + 14), "Choose roster slot to edit offline build", anchor="mm", font=FONT_XS, fill=PALETTE["text_muted"])
        return

    gw, gh = gx1 - gx0, gy1 - gy0
    nodes_rel = {
        "Core": (0.52, 0.72, PALETTE["primary"]),
        "Resolve": (0.38, 0.72, PALETTE["primary_soft"]),
        "Dexterity": (0.54, 0.54, PALETTE["primary_soft"]),
        "Vitality": (0.48, 0.88, PALETTE["primary_soft"]),
        "Agility": (0.64, 0.88, PALETTE["primary_soft"]),
        "Willpower": (0.64, 0.62, PALETTE["primary_soft"]),
        "Quick Strike": (0.20, 0.64, PALETTE["accent"]),
        "Bandage": (0.58, 0.34, PALETTE["warn"]),
        "Ember": (0.84, 0.78, PALETTE["warn"]),
    }
    nodes = {k: (int(gx0 + rx * gw), int(gy0 + ry * gh), c) for k, (rx, ry, c) in nodes_rel.items()}
    edges = [("Core", "Resolve"), ("Core", "Dexterity"), ("Core", "Vitality"), ("Core", "Agility"), ("Core", "Willpower"), ("Resolve", "Quick Strike"), ("Dexterity", "Bandage"), ("Agility", "Ember")]
    for a, b in edges:
        ax, ay, _ = nodes[a]
        bx, by, _ = nodes[b]
        draw.line((ax, ay, bx, by), fill=(133, 160, 198), width=3)

    for name, (nx, ny, col) in nodes.items():
        if mode == "create" and name in {"Quick Strike", "Bandage", "Ember"}:
            col = (198, 208, 223)
        r = 11 if name == "Core" else 10
        draw.ellipse((nx - r, ny - r, nx + r, ny + r), fill=col, outline=PALETTE["line"], width=1)
        draw.text((nx, min(gy1 - 8, ny + 18)), name, anchor="mm", font=FONT_XS, fill=PALETTE["text_soft"])


def auth_scene(spec: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bg(d, spec["density"])
    draw_nav(d, spec, ["Login", "Register", "Quit"], 0, auth=True)
    draw_ribbon(d, spec, "Auth + update fused: account entry and patch awareness in one frame")

    if spec["layout"] == "float":
        # Floating card stack layout.
        rr(d, (214, 188, 886, 704), PALETTE["panel"], outline=PALETTE["line"], width=1, r=14)
        rr(d, (236, 210, 864, 526), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
        rr(d, (646, 362, 1276, 714), PALETTE["panel"], outline=PALETTE["line"], width=1, r=12)
        rr(d, (668, 384, 1254, 692), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)

        d.text((258, 238), "Account Access", font=FONT_H2, fill=PALETTE["text"])
        button(d, (258, 270, 414, 302), "Login", primary=True)
        button(d, (422, 270, 578, 302), "Register")
        input_box(d, (258, 320, 842, 354), "Email", "admin@admin.com")
        input_box(d, (258, 364, 842, 398), "Password")
        input_box(d, (258, 408, 842, 442), "MFA Code (optional)")
        button(d, (258, 454, 842, 490), "Continue", primary=True)
        d.text((258, 498), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
        d.text((842, 498), "MFA in Security", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

        d.text((690, 412), "Patch Snapshot", font=FONT_H2, fill=PALETTE["text"])
        d.text((690, 442), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])
        tbox(d, (690, 472), "- Login and update awareness are fused.\n- Build graph can be edited pre-launch.\n- MFA controls are in System > Security.", FONT_SM, PALETTE["text_soft"], 530, max_lines=8)
        button(d, (690, 648, 1232, 682), "Check for Update")
    elif spec["layout"] == "stage":
        # Stage layout: stacked login and update lanes.
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
        rr(d, (214, 196, 1314, 492), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (214, 508, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)

        d.text((236, 222), "Account Access", font=FONT_H2, fill=PALETTE["text"])
        button(d, (236, 252, 396, 284), "Login", primary=True)
        button(d, (404, 252, 564, 284), "Register")
        input_box(d, (236, 302, 830, 336), "Email", "admin@admin.com")
        input_box(d, (236, 344, 830, 378), "Password")
        input_box(d, (236, 386, 830, 420), "MFA Code (optional)")
        button(d, (236, 430, 830, 466), "Continue", primary=True)
        d.text((236, 470), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
        d.text((830, 470), "MFA in Security", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

        d.text((236, 534), "Patch Notes", font=FONT_H2, fill=PALETTE["text"])
        rr(d, (236, 566, 1292, 664), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
        d.text((254, 586), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])
        tbox(d, (254, 612), "- Auth and update path unified.\n- Pre-launch build planning retained.\n- Security + MFA in same system route.", FONT_SM, PALETTE["text_soft"], 900, max_lines=4)
        button(d, (1040, 674, 1292, 704), "Check for Update")
    else:
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
        left_x1 = 900 if spec["density"] >= 3 else 862
        rr(d, (214, 198, left_x1, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (left_x1 + 16, 198, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)

        d.text((236, 226), "Account Access", font=FONT_H2, fill=PALETTE["text"])
        button(d, (236, 258, 396, 290), "Login", primary=True)
        button(d, (404, 258, 564, 290), "Register")

        input_box(d, (236, 308, left_x1 - 22, 342), "Email", "admin@admin.com")
        input_box(d, (236, 352, left_x1 - 22, 386), "Password")
        input_box(d, (236, 396, left_x1 - 22, 430), "MFA Code (optional)")
        button(d, (236, 444, left_x1 - 22, 480), "Continue", primary=True)

        d.text((236, 680), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
        d.text((left_x1 - 26, 680), "MFA toggle lives in Security", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

        right_x0 = left_x1 + 32
        d.text((right_x0, 226), "Patch Snapshot", font=FONT_H2, fill=PALETTE["text"])
        rr(d, (right_x0, 256, 1290, 610), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
        d.text((right_x0 + 18, 276), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])
        tbox(d, (right_x0 + 18, 310), "- Unified account entry and update checks.\n- Graph editable before launch in hub.\n- MFA surface available in Settings > Security.", FONT_SM, PALETTE["text_soft"], 1290 - right_x0 - 36, max_lines=10)
        button(d, (right_x0, 632, 1290, 668), "Check for Update")
    return img


def register_scene(spec: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bg(d, spec["density"])
    draw_nav(d, spec, ["Login", "Register", "Quit"], 1, auth=True)
    draw_ribbon(d, spec, "Registration mode inside the same workspace shell")

    poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
    rr(d, (214, 198, 880, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
    rr(d, (896, 198, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)

    d.text((236, 226), "Create Account", font=FONT_H2, fill=PALETTE["text"])
    button(d, (236, 258, 396, 290), "Login")
    button(d, (404, 258, 564, 290), "Register", primary=True)
    input_box(d, (236, 308, 858, 342), "Display Name")
    input_box(d, (236, 352, 858, 386), "Email")
    input_box(d, (236, 396, 858, 430), "Password")
    button(d, (236, 444, 858, 480), "Register", primary=True)

    d.text((918, 226), "New Player Prep", font=FONT_H2, fill=PALETTE["text"])
    tbox(d, (918, 262), "1. Register\n2. Create/select hero\n3. Edit build graph offline\n4. Launch", FONT_H3, PALETTE["text_soft"], 370, max_lines=9, line_h=34)
    button(d, (918, 632, 1290, 668), "Back to Login")
    return img


def hub_scene(spec: dict, selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bg(d, spec["density"])
    draw_nav(d, spec, ["Play", "Create", "System", "Log Out", "Quit"], 0)
    draw_ribbon(d, spec, "Character hub: roster + graph editor + launch strip (single workspace)")

    if spec["layout"] == "float":
        # Top roster band + bottom graph/inspector.
        rr(d, (188, 172, 1340, 738), PALETTE["panel"], outline=PALETTE["line"], width=1, r=16)
        rr(d, (214, 198, 1314, 332), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
        rr(d, (214, 346, 1038, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
        rr(d, (1052, 346, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
        d.text((236, 224), "Roster Deck", font=FONT_H2, fill=PALETTE["text"])
        button(d, (236, 252, 430, 286), "Create Character")
        slot_x = 446
        if selected:
            for i, label in enumerate(["Sellsword", "Scout", "Empty 1", "Empty 2", "Empty 3"]):
                rr(d, (slot_x + i * 164, 244, slot_x + 154 + i * 164, 300), PALETTE["primary"] if i == 0 else PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
                d.text((slot_x + 10 + i * 164, 264), label, font=FONT_SM, fill=PALETTE["primary_text"] if i == 0 else PALETTE["text"])
        else:
            tbox(d, (446, 252), "No characters yet. Create one to unlock build editing.", FONT_SM, PALETTE["text_muted"], 840, max_lines=2)
        d.text((236, 374), "Build Graph", font=FONT_H2, fill=PALETTE["text"])
        draw_graph(d, (236, 398, 1016, 640), "selected" if selected else "empty", tight=True)
        rr(d, (236, 650, 1016, 688), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=6)
        button(d, (244, 654, 406, 684), "Save Build", primary=selected)
        button(d, (414, 654, 522, 684), "Reset")
        button(d, (530, 654, 640, 684), "Play", primary=selected)
        d.text((660, 670), "Offline build saved before launch.", font=FONT_XS, fill=PALETTE["text_muted"])
        d.text((1070, 374), "Inspector", font=FONT_H2, fill=PALETTE["text"])
        if selected:
            tbox(d, (1070, 408), "Name: Sellsword\nClass: Mercenary\nNode: Core", FONT_H3, PALETTE["text_soft"], 220, max_lines=8)
        else:
            tbox(d, (1070, 408), "No character selected.\nChoose a roster slot.", FONT_H3, PALETTE["text_muted"], 220, max_lines=4)
        button(d, (1070, 624, 1292, 658), "Play", primary=selected)
        button(d, (1070, 666, 1292, 698), "Delete")
    elif spec["layout"] == "stage":
        # Graph stage in center, roster as bottom strip, details on left tower.
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
        rr(d, (214, 198, 414, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (428, 198, 1314, 626), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (428, 640, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((236, 226), "Inspector", font=FONT_H2, fill=PALETTE["text"])
        tbox(d, (236, 262), "Character launch, spawn override, and node details live here.", FONT_SM, PALETTE["text_soft"], 160, max_lines=8)
        button(d, (236, 624, 392, 658), "Play", primary=selected)
        button(d, (236, 666, 392, 698), "Delete")
        d.text((450, 226), "Build Stage", font=FONT_H2, fill=PALETTE["text"])
        draw_graph(d, (450, 250, 1290, 610), "selected" if selected else "empty", tight=False)
        d.text((450, 658), "Roster Strip", font=FONT_H3, fill=PALETTE["text"])
        button(d, (554, 648, 744, 684), "Create Character")
        if selected:
            for i, label in enumerate(["Sellsword", "Scout", "Empty 1", "Empty 2"]):
                rr(d, (754 + i * 130, 648, 874 + i * 130, 684), PALETTE["primary"] if i == 0 else PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
                d.text((764 + i * 130, 666), label, font=FONT_XS, fill=PALETTE["primary_text"] if i == 0 else PALETTE["text"])
        else:
            d.text((754, 666), "No characters yet", font=FONT_SM, fill=PALETTE["text_muted"])
        button(d, (1150, 648, 1250, 684), "Save Build", primary=selected)
        button(d, (1258, 648, 1302, 684), ">", primary=False)
    else:
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])

        if spec["density"] >= 6:
            roster_w = 252
        elif spec["density"] >= 3:
            roster_w = 270
        else:
            roster_w = 280 + min(24, spec["density"] * 4)
        roster = (214, 198, 214 + roster_w, 714)
        graph = (roster[2] + 14, 198, 1130, 714)
        right = (1146, 198, 1314, 714)

        rr(d, roster, PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((236, 226), "Roster", font=FONT_H2, fill=PALETTE["text"])
        button(d, (236, 258, roster[2] - 18, 292), "Create Character")
        rr(d, (236, 304, roster[2] - 18, 696), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)

        if selected:
            rr(d, (246, 316, roster[2] - 28, 368), PALETTE["primary"], outline=PALETTE["line"], width=1, r=5)
            d.text((258, 334), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
            d.text((258, 352), "Lv 5 | Ironhold", font=FONT_SM, fill=PALETTE["primary_text"])
            rr(d, (246, 376, roster[2] - 28, 424), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=5)
            d.text((258, 392), "Scout", font=FONT_H3, fill=PALETTE["text"])
            d.text((258, 410), "Lv 2 | Khar Grotto", font=FONT_SM, fill=PALETTE["text_muted"])
            for i in range(3):
                py = 432 + i * 48
                rr(d, (246, py, roster[2] - 28, py + 40), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=5)
                d.text((258, py + 14), f"Empty Slot {i+1}", font=FONT_SM, fill=PALETTE["text_muted"])
        else:
            tbox(d, (252, 336), "No characters yet. Create one and begin with an offline build path.", FONT_SM, PALETTE["text_muted"], roster_w - 56, max_lines=6)

        rr(d, graph, PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((graph[0] + 18, 226), "Build Graph", font=FONT_H2, fill=PALETTE["text"])
        if spec["density"] >= 3:
            button(d, (graph[0] + 170, 206, graph[0] + 292, 236), "Select", active=True)
            button(d, (graph[0] + 300, 206, graph[0] + 422, 236), "Create")
            button(d, (graph[0] + 430, 206, graph[0] + 572, 236), "Planner")
        draw_graph(d, (graph[0] + 18, 250, graph[2] - 18, 640), "selected" if selected else "empty", tight=spec["density"] >= 5)

        rr(d, (graph[0] + 18, 650, graph[2] - 18, 688), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=12 if spec["density"] >= 4 else 6)
        button(d, (graph[0] + 24, 654, graph[0] + 186, 684), "Save Build", primary=selected)
        button(d, (graph[0] + 194, 654, graph[0] + 304, 684), "Reset")
        button(d, (graph[0] + 312, 654, graph[0] + 420, 684), "Play", primary=selected)
        tbox(d, (graph[0] + 432, 658), "Offline edits saved before gameplay entry.", FONT_XS, PALETTE["text_muted"], graph[2] - graph[0] - 460, max_lines=2, line_h=12)

        rr(d, right, PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((right[0] + 16, 226), "Inspector", font=FONT_H2, fill=PALETTE["text"])
        if selected:
            tbox(d, (right[0] + 16, 262), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold\n\nNode: Core\nRoutes: Resolve / Dex / Vit", FONT_H3, PALETTE["text_soft"], 136, max_lines=10)
            button(d, (right[0] + 16, 624, right[2] - 16, 658), "Play", primary=True)
            button(d, (right[0] + 16, 666, right[2] - 16, 698), "Delete")
        else:
            tbox(d, (right[0] + 16, 262), "Select character to launch or edit graph.", FONT_H3, PALETTE["text_muted"], 136, max_lines=5)
    return img


def create_scene(spec: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bg(d, spec["density"])
    draw_nav(d, spec, ["Play", "Create", "System", "Log Out", "Quit"], 1)
    draw_ribbon(d, spec, "Character creation merged with start-graph explanation")

    if spec["layout"] == "float":
        # Stepper style creation.
        rr(d, (188, 172, 1340, 738), PALETTE["panel"], outline=PALETTE["line"], width=1, r=14)
        rr(d, (214, 198, 1314, 248), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        button(d, (236, 206, 380, 240), "1 Archetype", primary=True)
        button(d, (392, 206, 544, 240), "2 Identity")
        button(d, (556, 206, 728, 240), "3 Start Graph")
        button(d, (740, 206, 920, 240), "4 Confirm")
        rr(d, (214, 262, 730, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (744, 262, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((236, 290), "Identity + Lore", font=FONT_H2, fill=PALETTE["text"])
        input_box(d, (236, 324, 708, 358), "Character Name")
        input_box(d, (236, 368, 708, 402), "Character Type", "Sellsword")
        input_box(d, (236, 412, 708, 446), "Sex", "Male")
        rr(d, (236, 462, 708, 622), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
        tbox(d, (252, 484), "Sellsword starts on Core. Early paths: Resolve, Dexterity, Vitality.", FONT_H3, PALETTE["text_soft"], 440, max_lines=6, line_h=30)
        button(d, (236, 648, 708, 684), "Create Character", primary=True)
        d.text((766, 290), "Start Graph", font=FONT_H2, fill=PALETTE["text"])
        draw_graph(d, (766, 324, 1292, 632), "create", tight=True)
        button(d, (766, 648, 1292, 684), "Back to Play")
    elif spec["layout"] == "stage":
        # Wizard lane on left + huge graph stage.
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
        rr(d, (214, 198, 520, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (534, 198, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((236, 226), "Creation Steps", font=FONT_H2, fill=PALETTE["text"])
        for i, label in enumerate(["Pick Archetype", "Set Identity", "Review Start Graph", "Create"]):
            y = 264 + i * 78
            rr(d, (236, y, 498, y + 58), PALETTE["primary"] if i == 0 else PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
            d.text((250, y + 20), label, font=FONT_SM, fill=PALETTE["primary_text"] if i == 0 else PALETTE["text"])
        input_box(d, (236, 584, 498, 618), "Character Name")
        input_box(d, (236, 626, 498, 660), "Sellsword")
        button(d, (236, 672, 498, 704), "Create Character", primary=True)
        d.text((556, 226), "Starting Graph + Route Preview", font=FONT_H2, fill=PALETTE["text"])
        draw_graph(d, (556, 254, 1292, 650), "create", tight=False)
        button(d, (1020, 672, 1292, 704), "Back to Play")
    else:
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])

        if spec["density"] >= 4:
            left = (214, 198, 440, 714)
            mid = (454, 198, 1020, 714)
            right = (1034, 198, 1314, 714)
        else:
            left = (214, 198, 474, 714)
            mid = (488, 198, 1046, 714)
            right = (1060, 198, 1314, 714)

        rr(d, left, PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((236, 226), "Archetypes", font=FONT_H2, fill=PALETTE["text"])
        rr(d, (236, 258, 452, 320), PALETTE["primary"], outline=PALETTE["line"], width=1, r=5)
        d.text((248, 276), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
        d.text((248, 296), "Durable melee opener", font=FONT_SM, fill=PALETTE["primary_text"])
        rr(d, (236, 330, 452, 392), PALETTE["panel"], outline=PALETTE["line"], width=1, r=5)
        d.text((248, 350), "Scout", font=FONT_H3, fill=PALETTE["text"])
        d.text((248, 370), "Mobile precision style", font=FONT_SM, fill=PALETTE["text_muted"])

        rr(d, mid, PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((510, 226), "Identity + Lore", font=FONT_H2, fill=PALETTE["text"])
        input_box(d, (510, 258, 1024, 292), "Character Name")
        input_box(d, (510, 302, 1024, 336), "Character Type", "Sellsword")
        input_box(d, (510, 346, 1024, 380), "Sex", "Male")
        rr(d, (510, 398, 1024, 622), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
        tbox(d, (528, 424), "Sellsword starts near Core and can branch early into Resolve, Dexterity, or Vitality routes. This panel stays lore-focused while graph gives route preview.", FONT_H3, PALETTE["text_soft"], 478, max_lines=8, line_h=32)
        button(d, (510, 648, 1024, 684), "Create Character", primary=True)

        rr(d, right, PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((1078, 226), "Start Graph", font=FONT_H2, fill=PALETTE["text"])
        draw_graph(d, (1078, 254, 1296, 616), "create", tight=True)
        button(d, (1078, 648, 1296, 684), "Back to Play")
    return img


def system_scene(spec: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bg(d, spec["density"])
    draw_nav(d, spec, ["Play", "Create", "System", "Log Out", "Quit"], 2)
    draw_ribbon(d, spec, "System deck: video, audio, and security in one route")

    if spec["layout"] == "stage":
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
        rr(d, (214, 198, 540, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (554, 198, 1314, 448), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        rr(d, (554, 462, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)
        d.text((236, 226), "System Tabs", font=FONT_H2, fill=PALETTE["text"])
        for i, lab in enumerate(["Video", "Audio", "Security"]):
            button(d, (236, 258 + i * 42, 518, 292 + i * 42), lab, primary=(lab == "Audio"))
        tbox(d, (236, 398), "Single system deck replaces fragmented settings menus.", FONT_SM, PALETTE["text_soft"], 260, max_lines=6)
        d.text((576, 226), "Audio Mix", font=FONT_H2, fill=PALETTE["text"])
        for i, (lbl, val) in enumerate(zip(["Master", "Music", "Effects", "Interface"], [0.78, 0.62, 0.83, 0.57])):
            y = 262 + i * 42
            d.text((576, y), lbl, font=FONT_H3, fill=PALETTE["text"])
            rr(d, (680, y + 4, 1260, y + 10), (184, 201, 223, 255), r=3)
            rr(d, (680, y + 4, int(680 + 580 * val), y + 10), PALETTE["primary"], r=3)
        button(d, (1162, 396, 1260, 430), "Apply", primary=True)
        d.text((576, 490), "MFA", font=FONT_H2, fill=PALETTE["text"])
        button(d, (576, 522, 700, 554), "MFA: ON", primary=True)
        button(d, (712, 522, 828, 554), "Refresh QR")
        button(d, (840, 522, 956, 554), "Copy URI")
        rr(d, (576, 566, 852, 692), PALETTE["panel"], outline=PALETTE["line"], width=1, r=4)
        rr(d, (866, 566, 1260, 692), PALETTE["panel"], outline=PALETTE["line"], width=1, r=4)
    else:
        poly(d, (188, 172, 1340, 738), PALETTE["panel"], PALETTE["line"], spec["layout"])
        rr(d, (214, 198, 1314, 714), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=8)

        d.text((236, 226), "System Settings", font=FONT_H2, fill=PALETTE["text"])
        button(d, (236, 258, 328, 290), "Video")
        button(d, (336, 258, 428, 290), "Audio", primary=True)
        button(d, (436, 258, 548, 290), "Security")

        rr(d, (236, 304, 958, 684), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
        d.text((256, 328), "Audio Mix", font=FONT_H2, fill=PALETTE["text"])
        labels = ["Master", "Music", "Effects", "Interface"]
        vals = [0.78, 0.62, 0.83, 0.57]
        for i, (lbl, val) in enumerate(zip(labels, vals)):
            y = 368 + i * 66
            d.text((256, y), lbl, font=FONT_H3, fill=PALETTE["text"])
            rr(d, (256, y + 24, 920, y + 30), (184, 201, 223, 255), r=3)
            rr(d, (256, y + 24, int(256 + 664 * val), y + 30), PALETTE["primary"], r=3)
        button(d, (830, 646, 940, 678), "Apply", primary=True)

        rr(d, (974, 304, 1292, 684), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
        d.text((994, 328), "MFA", font=FONT_H2, fill=PALETTE["text"])
        button(d, (994, 358, 1098, 390), "MFA: ON", primary=True)
        button(d, (1110, 358, 1210, 390), "Refresh QR")
        button(d, (994, 398, 1210, 430), "Copy URI")
        rr(d, (994, 444, 1132, 582), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=4)
        rr(d, (1142, 444, 1270, 582), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=4)
        tbox(d, (994, 596), "Security in same system view to avoid menu hopping.", FONT_XS, PALETTE["text_muted"], 280, max_lines=3)
    return img


def update_scene(spec: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bg(d, spec["density"])
    draw_nav(d, spec, ["Login", "Register", "Quit"], 0, auth=True)
    draw_ribbon(d, spec, "Dedicated update log (optional deep view)")

    if spec["layout"] == "float":
        rr(d, (286, 188, 1120, 626), PALETTE["panel"], outline=PALETTE["line"], width=1, r=14)
        rr(d, (314, 218, 1092, 258), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=6)
        d.text((332, 232), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])
        rr(d, (314, 270, 1092, 538), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=8)
        d.text((332, 294), "Release Notes", font=FONT_H2, fill=PALETTE["text"])
        tbox(d, (332, 330), "- Offline build save is available in character hub.\n- Start graph guidance remains in creation flow.\n- System deck consolidates audio/video/security + MFA.", FONT_H3, PALETTE["text_soft"], 742, max_lines=8, line_h=34)
        button(d, (314, 552, 706, 592), "Back to Login")
        button(d, (714, 552, 1092, 592), "Check for Update", primary=True)
    else:
        poly(d, (286, 196, 1120, 626), PALETTE["panel"], PALETTE["line"], spec["layout"])
        rr(d, (312, 222, 1094, 264), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=5)
        d.text((330, 236), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])

        rr(d, (312, 276, 1094, 544), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=6)
        d.text((330, 298), "Release Notes", font=FONT_H2, fill=PALETTE["text"])
        tbox(d, (330, 334), "- Offline build save is available in character hub.\n- Start graph guidance remains in creation flow.\n- System deck consolidates audio/video/security + MFA.", FONT_H3, PALETTE["text_soft"], 742, max_lines=8, line_h=34)
        button(d, (312, 556, 1094, 594), "Check for Update", primary=True)
    return img


def contact_sheet(images: list[Path], out_path: Path):
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
    global CURRENT_DENSITY
    spec = PASS_SPECS[pass_no]
    CURRENT_DENSITY = spec["density"]
    out = OUT_ROOT / f"pass_{pass_no:02d}"
    out.mkdir(parents=True, exist_ok=True)
    scenes = {
        "nova_auth": auth_scene(spec),
        "nova_register": register_scene(spec),
        "nova_hub_empty": hub_scene(spec, selected=False),
        "nova_hub_selected": hub_scene(spec, selected=True),
        "nova_create": create_scene(spec),
        "nova_system": system_scene(spec),
        "nova_update": update_scene(spec),
    }
    saved = []
    for name, img in scenes.items():
        p = out / f"{name}.png"
        img.save(p)
        saved.append(p)
    contact_sheet(saved, out / "nova_contact_sheet.png")


def write_notes():
    lines = ["# Nova 10-Pass Concept Iteration", ""]
    for i in range(1, 11):
        spec = PASS_SPECS[i]
        lines.append(f"## {spec['name']}")
        lines.append(f"- Analysis: {spec['analysis']}")
        lines.append(f"- Improvement Plan: {spec['plan']}")
        lines.append("")
    (OUT_ROOT / "pass_notes.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", type=int, choices=list(range(1, 11)), help="Render only one pass (1-10).")
    args = parser.parse_args()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.pass_no:
        render_pass(args.pass_no)
    else:
        for i in range(1, 11):
            render_pass(i)
    write_notes()


if __name__ == "__main__":
    main()
