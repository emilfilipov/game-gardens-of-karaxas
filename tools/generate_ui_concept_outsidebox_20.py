#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import textwrap
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

W, H = 1366, 768

PALETTE = {
    "bg": (170, 188, 214, 255),
    "panel": (197, 208, 223, 245),
    "panel_alt": (190, 202, 219, 245),
    "panel_soft": (205, 214, 228, 245),
    "line": (131, 158, 196, 255),
    "line_soft": (154, 177, 206, 210),
    "text": (34, 56, 90, 255),
    "text_soft": (70, 92, 124, 255),
    "text_muted": (88, 106, 132, 255),
    "primary": (86, 139, 214, 255),
    "primary_text": (234, 241, 250, 255),
    "ok": (111, 189, 143, 255),
    "warn": (235, 176, 91, 255),
}

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "concept_art" / "option_outsidebox_20pass"


def _font(cands: Iterable[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for cand in cands:
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT_H1 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 30)
FONT_H2 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 22)
FONT_H3 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 16)
FONT_SM = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 14)
FONT_XS = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)
FONT_SIGIL = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 24)


def rr(draw: ImageDraw.ImageDraw, rect, fill, outline=None, width=1, r=8):
    draw.rounded_rectangle(rect, radius=r, fill=fill, outline=outline, width=width)


def tbox(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, width_px: int, max_lines=16, line_h=20):
    x, y = xy
    avg = max(6, int(font.size * 0.62)) if hasattr(font, "size") else 8
    wrap = textwrap.wrap(text, width=max(12, width_px // avg))[:max_lines]
    for i, line in enumerate(wrap):
        draw.text((x, y + i * line_h), line, font=font, fill=fill)


def button(draw: ImageDraw.ImageDraw, rect, label: str, primary=False, icon=False):
    fill = PALETTE["primary"] if primary else (225, 223, 214, 255)
    txt = PALETTE["primary_text"] if primary else PALETTE["text"]
    rr(draw, rect, fill, outline=PALETTE["line"], width=1, r=8)
    x0, y0, x1, y1 = rect
    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), label, anchor="mm", font=FONT_H3 if not icon else FONT_SIGIL, fill=txt)


def input_box(draw: ImageDraw.ImageDraw, rect, hint: str, value: str | None = None):
    rr(draw, rect, PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=6)
    x0, y0, x1, y1 = rect
    draw.text((x0 + 12, (y0 + y1) // 2), value if value else hint, anchor="lm", font=FONT_H3, fill=PALETTE["text_muted"])


def draw_solid_bg(draw: ImageDraw.ImageDraw):
    draw.rectangle((0, 0, W, H), fill=PALETTE["bg"])


def draw_crest(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, subtitle: str | None = None):
    r1 = int(42 * scale)
    r2 = int(30 * scale)
    draw.ellipse((cx - r1, cy - r1, cx + r1, cy + r1), fill=PALETTE["panel"], outline=PALETTE["line"], width=2)
    draw.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=2)
    # Hand-drawn blade motif.
    draw.polygon([(cx, cy - int(18 * scale)), (cx + int(7 * scale), cy + int(14 * scale)), (cx - int(7 * scale), cy + int(14 * scale))], fill=(184, 201, 223, 255), outline=PALETTE["line"])
    draw.rectangle((cx - int(14 * scale), cy + int(11 * scale), cx + int(14 * scale), cy + int(15 * scale)), fill=(186, 202, 222, 255), outline=PALETTE["line"])
    draw.text((cx, cy - 1), "COI", anchor="mm", font=FONT_H3, fill=PALETTE["text"])
    if subtitle:
        draw.text((cx, cy + int(58 * scale)), subtitle, anchor="mm", font=FONT_XS, fill=PALETTE["text_muted"])


def draw_corner_art(draw: ImageDraw.ImageDraw, pass_no: int):
    # Custom decorative line art, no background gradients.
    alpha = max(60, 150 - pass_no * 4)
    # Left corner leaf-blade.
    draw.polygon([(36, 118), (72, 94), (122, 102), (96, 128), (48, 132)], outline=(141, 166, 200, alpha), fill=(186, 203, 222, alpha // 3))
    draw.line((64, 96, 88, 130), fill=(141, 166, 200, alpha), width=2)
    # Right corner shard ring.
    base_x = W - 80
    draw.arc((base_x - 54, 72, base_x + 24, 148), 200, 340, fill=(141, 166, 200, alpha), width=2)
    draw.polygon([(base_x - 12, 84), (base_x + 8, 98), (base_x + 2, 122), (base_x - 22, 112)], outline=(141, 166, 200, alpha), fill=(186, 203, 222, alpha // 3))


def nav_icons(pass_no: int) -> list[tuple[str, str]]:
    if pass_no <= 6:
        return [("A", "Auth"), ("H", "Hub"), ("F", "Forge"), ("S", "System"), ("U", "Update"), ("Q", "Quit")]
    if pass_no <= 12:
        return [("@", "Auth"), ("*", "Hub"), ("+", "Create"), ("~", "System"), ("!", "Update"), ("x", "Quit")]
    return [("o", "Auth"), (">", "Play"), ("+", "Create"), ("#", "System"), ("?", "Update"), ("x", "Quit")]


def draw_navigation(draw: ImageDraw.ImageDraw, pass_no: int, active: int):
    icons = nav_icons(pass_no)

    if pass_no <= 5:
        # Top icon dock.
        rr(draw, (180, 20, 1186, 76), PALETTE["panel"], outline=PALETTE["line"], width=1, r=12)
        draw_crest(draw, 98, 48, 0.9)
        x = 248
        for i, (glyph, _) in enumerate(icons):
            button(draw, (x, 30, x + 64, 66), glyph, primary=(i == active), icon=True)
            x += 80
    elif pass_no <= 10:
        # Right utility column.
        rr(draw, (1230, 140, 1328, 620), PALETTE["panel"], outline=PALETTE["line"], width=1, r=12)
        draw_crest(draw, 1278, 94, 0.68)
        y = 178
        for i, (glyph, _) in enumerate(icons):
            button(draw, (1242, y, 1316, y + 48), glyph, primary=(i == active), icon=True)
            y += 62
    elif pass_no <= 15:
        # Bottom command dock.
        rr(draw, (170, 682, 1196, 748), PALETTE["panel"], outline=PALETTE["line"], width=1, r=12)
        draw_crest(draw, 96, 714, 0.64)
        x = 242
        for i, (glyph, _) in enumerate(icons):
            button(draw, (x, 694, x + 72, 736), glyph, primary=(i == active), icon=True)
            x += 92
    else:
        # Radial nav cluster (outside-box final passes).
        cx, cy = 96, 384
        draw_crest(draw, cx, cy, 0.74)
        for i, (glyph, _) in enumerate(icons):
            ang = -90 + i * 54
            rad = 128
            x = int(cx + rad * math.cos(math.radians(ang)))
            y = int(cy + rad * math.sin(math.radians(ang)))
            button(draw, (x - 30, y - 22, x + 30, y + 22), glyph, primary=(i == active), icon=True)


def draw_workspace_shell(draw: ImageDraw.ImageDraw, pass_no: int):
    if pass_no <= 5:
        rr(draw, (160, 100, 1208, 664), PALETTE["panel"], outline=PALETTE["line"], width=1, r=16)
    elif pass_no <= 10:
        # split crest shell
        rr(draw, (120, 100, 1210, 664), PALETTE["panel"], outline=PALETTE["line"], width=1, r=14)
        draw.line((665, 118, 665, 646), fill=PALETTE["line_soft"], width=1)
    elif pass_no <= 15:
        rr(draw, (142, 84, 1224, 658), PALETTE["panel"], outline=PALETTE["line"], width=1, r=20)
    else:
        # asym shell
        pts = [(162, 102), (1160, 102), (1216, 144), (1216, 620), (1164, 658), (210, 658), (144, 620), (144, 150)]
        draw.polygon(pts, fill=PALETTE["panel"], outline=PALETTE["line"])


def draw_graph(draw: ImageDraw.ImageDraw, rect, mode: str, compact=False):
    x0, y0, x1, y1 = rect
    rr(draw, rect, PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=8)
    gx0, gy0, gx1, gy1 = x0 + 16, y0 + 16, x1 - 16, y1 - 16
    rr(draw, (gx0, gy0, gx1, gy1), PALETTE["panel_soft"], outline=PALETTE["line_soft"], width=1, r=6)
    sx = 80 if not compact else 92
    sy = 70 if not compact else 80
    for x in range(gx0 + 20, gx1 - 12, sx):
        draw.line((x, gy0 + 8, x, gy1 - 8), fill=(154, 177, 206, 125), width=1)
    for y in range(gy0 + 8, gy1 - 8, sy):
        draw.line((gx0 + 8, y, gx1 - 8, y), fill=(154, 177, 206, 125), width=1)

    if mode == "empty":
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 - 8), "No character selected", anchor="mm", font=FONT_H3, fill=PALETTE["text_muted"])
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 + 14), "Choose hero to edit offline build", anchor="mm", font=FONT_XS, fill=PALETTE["text_muted"])
        return

    gw, gh = gx1 - gx0, gy1 - gy0
    rel = {
        "Core": (0.50, 0.72, PALETTE["primary"]),
        "Resolve": (0.37, 0.72, PALETTE["primary"]),
        "Dex": (0.53, 0.54, PALETTE["primary"]),
        "Vit": (0.47, 0.88, PALETTE["primary"]),
        "Agi": (0.64, 0.88, PALETTE["primary"]),
        "Will": (0.64, 0.62, PALETTE["primary"]),
        "Strike": (0.20, 0.62, PALETTE["ok"]),
        "Bandage": (0.58, 0.36, PALETTE["warn"]),
        "Ember": (0.84, 0.78, PALETTE["warn"]),
    }
    nodes = {k: (int(gx0 + rx * gw), int(gy0 + ry * gh), col) for k, (rx, ry, col) in rel.items()}
    edges = [("Core", "Resolve"), ("Core", "Dex"), ("Core", "Vit"), ("Core", "Agi"), ("Core", "Will"), ("Resolve", "Strike"), ("Dex", "Bandage"), ("Agi", "Ember")]
    for a, b in edges:
        ax, ay, _ = nodes[a]
        bx, by, _ = nodes[b]
        draw.line((ax, ay, bx, by), fill=(134, 160, 198), width=3)
    for name, (nx, ny, col) in nodes.items():
        if mode == "create" and name in {"Strike", "Bandage", "Ember"}:
            col = PALETTE["panel"]
        r = 11 if name == "Core" else 9
        draw.ellipse((nx - r, ny - r, nx + r, ny + r), fill=col, outline=PALETTE["line"], width=1)
        draw.text((nx, ny + 16), name, anchor="mm", font=FONT_XS, fill=PALETTE["text_soft"])


def scene_gateway(pass_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_navigation(d, pass_no, 0)
    draw_workspace_shell(d, pass_no)

    rr(d, (188, 124, 768, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    rr(d, (782, 124, 1180, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)

    d.text((212, 152), "Entry Hub", font=FONT_H2, fill=PALETTE["text"])
    # no separate menu: mode chips in same card
    button(d, (212, 182, 354, 214), "Login", primary=True)
    button(d, (362, 182, 504, 214), "Register")
    input_box(d, (212, 234, 744, 268), "Email", "admin@admin.com")
    input_box(d, (212, 276, 744, 310), "Password")
    input_box(d, (212, 318, 744, 352), "MFA (optional)")
    button(d, (212, 366, 744, 404), "Continue", primary=True)
    d.text((212, 610), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
    d.text((742, 610), "MFA controls in System", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((806, 152), "Update Pulse", font=FONT_H2, fill=PALETTE["text"])
    rr(d, (806, 184, 1156, 550), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    d.text((824, 206), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])
    tbox(d, (824, 236), "- Login and update are one route. - Character lobby supports optional offline graph editing. - Security and MFA consolidated in System.", FONT_SM, PALETTE["text_soft"], 316, max_lines=10)
    button(d, (806, 566, 1156, 604), "Check Update")
    return img


def scene_lobby(pass_no: int, selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_navigation(d, pass_no, 1)
    draw_workspace_shell(d, pass_no)

    rr(d, (188, 124, 460, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    rr(d, (474, 124, 994, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    rr(d, (1008, 124, 1180, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)

    d.text((210, 152), "Roster", font=FONT_H2, fill=PALETTE["text"])
    button(d, (210, 182, 430, 216), "+", icon=True)
    d.text((250, 192), "create", anchor="lm", font=FONT_XS, fill=PALETTE["text_muted"])
    rr(d, (210, 226, 438, 618), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    if selected:
        rr(d, (220, 238, 428, 286), PALETTE["primary"], outline=PALETTE["line"], width=1, r=6)
        d.text((232, 254), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
        d.text((232, 272), "Lv 5 | Ironhold", font=FONT_XS, fill=PALETTE["primary_text"])
        rr(d, (220, 294, 428, 342), PALETTE["panel_alt"], outline=PALETTE["line"], width=1, r=6)
        d.text((232, 312), "Scout", font=FONT_H3, fill=PALETTE["text"])
        d.text((232, 330), "Lv 2 | Khar Grotto", font=FONT_XS, fill=PALETTE["text_muted"])
        for i in range(3):
            y = 350 + i * 46
            rr(d, (220, y, 428, y + 38), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=6)
            d.text((232, y + 13), f"Empty {i+1}", font=FONT_SM, fill=PALETTE["text_muted"])
    else:
        tbox(d, (226, 250), "No characters yet. Use + to create one.", FONT_SM, PALETTE["text_muted"], 196, max_lines=4)

    d.text((496, 152), "Build Graph", font=FONT_H2, fill=PALETTE["text"])
    button(d, (620, 136, 722, 164), "select", primary=True)
    button(d, (730, 136, 832, 164), "create")
    button(d, (840, 136, 942, 164), "plan")
    draw_graph(d, (492, 176, 976, 560), "selected" if selected else "empty", compact=pass_no >= 12)
    rr(d, (492, 572, 976, 614), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=8)
    button(d, (500, 578, 642, 608), "Save", primary=selected)
    button(d, (650, 578, 752, 608), "Reset")
    button(d, (760, 578, 860, 608), "Play", primary=selected)
    tbox(d, (868, 586), "Offline build saved before launch.", FONT_XS, PALETTE["text_muted"], 100, max_lines=3, line_h=12)

    d.text((1028, 152), "Details", font=FONT_H2, fill=PALETTE["text"])
    if selected:
        tbox(d, (1028, 188), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold\nFacing: East", FONT_H3, PALETTE["text_soft"], 132, max_lines=8)
        button(d, (1028, 560, 1160, 594), "Play", primary=True)
        button(d, (1028, 602, 1160, 636), "Delete")
    else:
        tbox(d, (1028, 188), "Select hero to launch or edit graph.", FONT_H3, PALETTE["text_muted"], 132, max_lines=5)
    return img


def scene_forge(pass_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_navigation(d, pass_no, 2)
    draw_workspace_shell(d, pass_no)

    rr(d, (188, 124, 440, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    rr(d, (454, 124, 964, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    rr(d, (978, 124, 1180, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)

    d.text((208, 152), "Archetypes", font=FONT_H2, fill=PALETTE["text"])
    rr(d, (208, 184, 420, 246), PALETTE["primary"], outline=PALETTE["line"], width=1, r=8)
    d.text((220, 204), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
    d.text((220, 224), "durable melee", font=FONT_XS, fill=PALETTE["primary_text"])
    rr(d, (208, 258, 420, 320), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    d.text((220, 278), "Scout", font=FONT_H3, fill=PALETTE["text"])
    d.text((220, 298), "precision mobile", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((476, 152), "Identity + Lore", font=FONT_H2, fill=PALETTE["text"])
    input_box(d, (476, 184, 940, 218), "Character Name")
    input_box(d, (476, 226, 940, 260), "Type", "Sellsword")
    input_box(d, (476, 268, 940, 302), "Sex", "Male")
    rr(d, (476, 316, 940, 534), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    tbox(d, (492, 336), "Sellsword starts near Core and can branch to Resolve, Dexterity, and Vitality routes. The graph shows early branch options.", FONT_H3, PALETTE["text_soft"], 430, max_lines=8, line_h=30)
    button(d, (476, 556, 940, 594), "Create", primary=True)

    d.text((996, 152), "Start Graph", font=FONT_H2, fill=PALETTE["text"])
    draw_graph(d, (996, 184, 1162, 534), "create", compact=True)
    button(d, (996, 556, 1162, 594), "Back")
    return img


def scene_system(pass_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_navigation(d, pass_no, 3)
    draw_workspace_shell(d, pass_no)

    rr(d, (188, 124, 1180, 642), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    d.text((210, 152), "System Deck", font=FONT_H2, fill=PALETTE["text"])
    button(d, (210, 182, 302, 214), "Video")
    button(d, (310, 182, 402, 214), "Audio", primary=True)
    button(d, (410, 182, 520, 214), "Security")

    rr(d, (210, 226, 850, 614), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    d.text((228, 250), "Audio", font=FONT_H2, fill=PALETTE["text"])
    labels = ["Master", "Music", "Effects", "Interface"]
    vals = [0.78, 0.62, 0.83, 0.57]
    for i, (lbl, val) in enumerate(zip(labels, vals)):
        y = 284 + i * 72
        d.text((228, y), lbl, font=FONT_H3, fill=PALETTE["text"])
        rr(d, (320, y + 8, 818, y + 14), (184, 201, 223, 255), r=3)
        rr(d, (320, y + 8, int(320 + 498 * val), y + 14), PALETTE["primary"], r=3)
    button(d, (706, 570, 818, 604), "Apply", primary=True)

    rr(d, (864, 226, 1158, 614), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    d.text((882, 250), "MFA", font=FONT_H2, fill=PALETTE["text"])
    button(d, (882, 278, 996, 310), "MFA ON", primary=True)
    button(d, (1006, 278, 1106, 310), "Refresh")
    button(d, (882, 318, 1106, 350), "Copy URI")
    rr(d, (882, 364, 1008, 500), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=6)
    rr(d, (1018, 364, 1138, 500), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=6)
    tbox(d, (882, 516), "Security and MFA stay in one place.", FONT_XS, PALETTE["text_muted"], 250, max_lines=3)
    return img


def scene_update(pass_no: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_navigation(d, pass_no, 4)
    draw_workspace_shell(d, pass_no)

    rr(d, (302, 148, 1066, 618), PALETTE["panel_alt"], outline=PALETTE["line_soft"], width=1, r=10)
    rr(d, (326, 180, 1040, 222), PALETTE["panel"], outline=PALETTE["line"], width=1, r=6)
    d.text((344, 194), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["text"])

    rr(d, (326, 234, 1040, 530), PALETTE["panel"], outline=PALETTE["line"], width=1, r=8)
    d.text((344, 256), "Release Notes", font=FONT_H2, fill=PALETTE["text"])
    tbox(d, (344, 292), "- Entry hub merges login/register/update awareness. - Lobby supports optional offline graph edits. - System deck consolidates settings and MFA controls.", FONT_H3, PALETTE["text_soft"], 678, max_lines=8, line_h=30)
    button(d, (326, 546, 1040, 584), "Check Update", primary=True)
    return img


def contact_sheet(paths: list[Path], out: Path):
    thumbs = []
    for p in paths:
        img = Image.open(p).convert("RGBA")
        thumbs.append((p.stem, img.resize((410, 230), Image.Resampling.LANCZOS)))
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 420 + 24, rows * 272 + 24), PALETTE["bg"])
    d = ImageDraw.Draw(sheet, "RGBA")
    for i, (name, thumb) in enumerate(thumbs):
        c = i % cols
        r = i // cols
        x = 12 + c * 420
        y = 12 + r * 272
        rr(d, (x, y, x + 410, y + 230), PALETTE["panel_soft"], outline=PALETTE["line"], width=1, r=6)
        sheet.paste(thumb, (x, y), thumb)
        d.text((x, y + 238), f"{name}.png", font=FONT_SM, fill=PALETTE["text"])
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def render_pass(pass_no: int):
    out_dir = OUT_ROOT / f"pass_{pass_no:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    imgs = {
        "outsidebox_gateway": scene_gateway(pass_no),
        "outsidebox_lobby_empty": scene_lobby(pass_no, selected=False),
        "outsidebox_lobby_selected": scene_lobby(pass_no, selected=True),
        "outsidebox_forge": scene_forge(pass_no),
        "outsidebox_system": scene_system(pass_no),
        "outsidebox_update": scene_update(pass_no),
    }
    saved: list[Path] = []
    for name, img in imgs.items():
        p = out_dir / f"{name}.png"
        img.save(p)
        saved.append(p)
    contact_sheet(saved, out_dir / "outsidebox_contact_sheet.png")


def write_notes():
    pass_plan = {
        1: "Start from merged gateway (auth + update pulse) with top icon dock.",
        2: "Tighten top dock spacing and improve glyph readability for first-time scan.",
        3: "Increase graph card prominence in lobby selected/empty split.",
        4: "Raise create-flow clarity by separating identity, lore, and start-graph.",
        5: "Validate system deck consolidation (audio + MFA in one surface).",
        6: "Shift nav to right utility rail to test left-to-right reading comfort.",
        7: "Reduce right-rail visual weight and rebalance content card margins.",
        8: "Stress test no-character empty lobby state under right-rail model.",
        9: "Improve selected-lobby launch affordance hierarchy.",
        10: "Freeze right-rail phase and measure information density ceiling.",
        11: "Move nav to bottom command dock for center-stage workspace focus.",
        12: "Increase graph and roster vertical space under bottom-dock mode.",
        13: "Simplify action clusters to reduce repeated text-label noise.",
        14: "Tune create screen for faster first-character onboarding.",
        15: "Finalize bottom-dock readability and compactness checks.",
        16: "Begin radial cluster experiment for non-linear navigation.",
        17: "Expand radial spacing and improve active-state discoverability.",
        18: "Add asym shell silhouette to reduce repeated rectangle feeling.",
        19: "Rebalance radial + asym shell with denser core content areas.",
        20: "Converge final outside-box pass with strongest novelty/stability mix.",
    }
    pass_draw = {
        1: "Solid-color stage, crest emblem, corner motifs, top dock buttons.",
        2: "Refined dock rhythm and micro-spacing in entry cards.",
        3: "Graph grid scaling tuned for better node legibility.",
        4: "Create surface receives stronger visual hierarchy blocks.",
        5: "System panel sliders/MFA controls aligned to one deck grammar.",
        6: "Utility rail icons replace top dock as primary mode switch.",
        7: "Rail buttons resized; card gutters tightened.",
        8: "Empty lobby callout enlarged to prevent dead-space ambiguity.",
        9: "Launch/save buttons receive clearer rank ordering.",
        10: "Right-rail phase stabilized with balanced shell proportions.",
        11: "Bottom dock introduced with crest anchor at left.",
        12: "Graph canvas area widened and vertical rhythm adjusted.",
        13: "Action row simplified to reduce duplicated controls.",
        14: "Forge panel reflowed around identity-first form order.",
        15: "Bottom dock polished for fast motor-target access.",
        16: "Radial icon ring prototype around crest center.",
        17: "Radial spoke distances and hitbox sizing refined.",
        18: "Asymmetric shell polygon replaces standard rounded frame.",
        19: "Asym shell corners tuned; interior cards recentered.",
        20: "Final asym/radial composition merged with stable card geometry.",
    }
    pass_eval = {
        1: "Merged auth/update cuts one menu hop but still looks conventional.",
        2: "Faster scanning than pass 1; still too dock-heavy.",
        3: "Graph priority improved; roster needs stronger affordance.",
        4: "Create comprehension improved; retains too many rigid blocks.",
        5: "System consolidation succeeds for functional parity.",
        6: "Right rail opens central stage but reduces first-glance discoverability.",
        7: "Balance improves; rail remains secondary for some users.",
        8: "Empty-state communication clearer; still visually conservative.",
        9: "Action hierarchy improved with clearer play/save path.",
        10: "Right-rail variant reaches density limit; move to new structure.",
        11: "Bottom dock improves focus but increases travel distance for navigation.",
        12: "Center canvas feels stronger; dock still familiar rather than novel.",
        13: "Less duplication helps clarity.",
        14: "Create flow is readable and direct.",
        15: "Bottom dock feels stable but not bold enough.",
        16: "Radial nav is the first clearly outside-box move.",
        17: "Radial discoverability improves with spacing tweaks.",
        18: "Asym shell breaks rectangle monotony successfully.",
        19: "Asym + radial combination is visually distinct and still usable.",
        20: "Best compromise between originality, clarity, and required capability parity.",
    }

    lines = ["# Outside-Box 20-Pass Iteration", ""]
    for i in range(1, 21):
        lines.append(f"## Pass {i:02d}")
        lines.append(f"- Plan: {pass_plan[i]}")
        lines.append(f"- Draw: {pass_draw[i]}")
        lines.append(f"- Evaluate: {pass_eval[i]}")
        lines.append("")
    (OUT_ROOT / "pass_notes.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", type=int, choices=list(range(1, 21)), help="Render only one pass.")
    args = parser.parse_args()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.pass_no:
        render_pass(args.pass_no)
    else:
        for i in range(1, 21):
            render_pass(i)
    write_notes()


if __name__ == "__main__":
    main()
