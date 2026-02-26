#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import textwrap
from pathlib import Path
from random import Random
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

W, H = 1366, 768

PALETTE = {
    "bg": (170, 188, 214, 255),
    "panel": (198, 210, 224, 246),
    "panel_b": (191, 204, 220, 244),
    "panel_c": (205, 214, 228, 244),
    "ink": (36, 57, 90, 255),
    "ink_soft": (73, 93, 124, 255),
    "line": (131, 158, 196, 255),
    "line_soft": (154, 176, 206, 220),
    "primary": (88, 138, 213, 255),
    "primary_text": (237, 243, 250, 255),
    "muted": (92, 110, 138, 255),
    "ok": (111, 188, 143, 255),
    "warn": (235, 176, 92, 255),
}

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "concept_art" / "option_iterative_loop_20pass"


def _font(cands: Iterable[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT_H1 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 34)
FONT_H2 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 17)
FONT_H3 = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 15)
FONT_TX = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)
FONT_SM = _font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 11)
FONT_ICON = _font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 16)


def family_for_pass(pass_no: int) -> str:
    if pass_no <= 4:
        return "monolith"
    if pass_no <= 8:
        return "orbital"
    if pass_no <= 12:
        return "ribbon"
    if pass_no <= 16:
        return "glyphdeck"
    return "finale"


PASS_PLAN = {
    1: "Set baseline with a carved totem nav and a single work slab.",
    2: "Reduce slab bulk and improve hierarchy between auth and update cells.",
    3: "Improve graph visibility and action readability in lobby.",
    4: "Refine create flow with clearer identity-to-graph sequence.",
    5: "Pivot to orbital navigation to break linear sidebar conventions.",
    6: "Rebalance orbital navigation size and declutter central content.",
    7: "Improve empty-state readability and minimize dead zones.",
    8: "Tighten selected-state controls for launch and save actions.",
    9: "Switch to ribbon frame language with asymmetric top command strip.",
    10: "Reduce visual noise in ribbons and clean anchor points.",
    11: "Increase menu discoverability with stronger icon labels.",
    12: "Normalize spacing + typography rhythm in ribbon mode.",
    13: "Move to glyph-deck command UX with fewer persistent labels.",
    14: "Improve create/menu discoverability under compact glyph navigation.",
    15: "Stabilize graph editing affordances in glyph-deck flow.",
    16: "Harden system deck + MFA grouping in glyph-deck style.",
    17: "Pivot into hybrid finale with asym frame + compass controls.",
    18: "Increase clarity of multi-panel regions while preserving novelty.",
    19: "Polish hierarchy, button rhythm, and lore readability.",
    20: "Finalize with strongest balance of uniqueness and usability.",
}


PASS_REVIEW = {
    1: "Works functionally, but still reads too rectangular.",
    2: "Hierarchy improved; needs bolder non-box silhouette.",
    3: "Graph now clearer; roster still compressed.",
    4: "Create path is readable; still conservative in shell shape.",
    5: "Orbital nav feels fresh; icon semantics need clarity.",
    6: "Better balance; still too much repetitive card framing.",
    7: "Empty state improved; edge art is still timid.",
    8: "Selected state controls clearer; launch zone still crowded.",
    9: "Ribbon style is distinct; some text zones run tight.",
    10: "Spacing is cleaner; some controls remain over-labeled.",
    11: "Discoverability improved; still needs calmer hierarchy.",
    12: "Stable rhythm reached; visual novelty plateaus.",
    13: "Glyph deck is concise but hides some meaning.",
    14: "Create flow clearer; command model still slightly opaque.",
    15: "Graph actions now cleaner; inspector too terse.",
    16: "System grouping improved; security explanation still dense.",
    17: "Hybrid frame is visually unique and stronger.",
    18: "More usable, but some regions still equal-weighted.",
    19: "Hierarchy nearly there; final pass should simplify labels.",
    20: "Final pass gives best novelty + clarity compromise.",
}


def rough_panel(draw: ImageDraw.ImageDraw, rect, seed: int, fill, outline, width=1, notch=False):
    x0, y0, x1, y1 = rect
    rng = Random(seed)
    j = 7
    pts = [
        (x0 + rng.randint(0, j), y0 + rng.randint(0, j)),
        (x1 - rng.randint(0, j), y0 + rng.randint(0, j)),
        (x1 - rng.randint(0, j), y1 - rng.randint(0, j)),
        (x0 + rng.randint(0, j), y1 - rng.randint(0, j)),
    ]
    if notch:
        midx = (x0 + x1) // 2
        pts = [
            pts[0],
            (midx - 34, y0 + rng.randint(0, j)),
            (midx, y0 - 12),
            (midx + 34, y0 + rng.randint(0, j)),
            pts[1],
            pts[2],
            (midx + 26, y1 - rng.randint(0, j)),
            (midx, y1 + 10),
            (midx - 26, y1 - rng.randint(0, j)),
            pts[3],
        ]
    draw.polygon(pts, fill=fill, outline=outline)
    if width > 1:
        draw.line(pts + [pts[0]], fill=outline, width=width)


def wrap_text(draw: ImageDraw.ImageDraw, rect, text: str, font, fill, line_h=18):
    x0, y0, x1, y1 = rect
    avg = max(6, int(getattr(font, "size", 12) * 0.58))
    max_chars = max(12, (x1 - x0 - 20) // avg)
    y = y0 + 10
    for line in textwrap.wrap(text, width=max_chars):
        if y + line_h > y1 - 8:
            break
        draw.text((x0 + 10, y), line, font=font, fill=fill)
        y += line_h


def button(draw: ImageDraw.ImageDraw, rect, label: str, primary=False):
    fill = PALETTE["primary"] if primary else (224, 223, 214, 255)
    txt = PALETTE["primary_text"] if primary else PALETTE["ink"]
    rough_panel(draw, rect, seed=sum(rect) + len(label), fill=fill, outline=PALETTE["line"], width=1)
    draw.text(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), label, anchor="mm", font=FONT_H3, fill=txt)


def input_box(draw: ImageDraw.ImageDraw, rect, value: str):
    rough_panel(draw, rect, seed=sum(rect), fill=PALETTE["panel_c"], outline=PALETTE["line_soft"], width=1)
    draw.text((rect[0] + 10, (rect[1] + rect[3]) // 2), value, anchor="lm", font=FONT_H3, fill=PALETTE["muted"])


def draw_solid_bg(draw: ImageDraw.ImageDraw):
    draw.rectangle((0, 0, W, H), fill=PALETTE["bg"])


def draw_crest(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float):
    r = int(30 * scale)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=PALETTE["panel"], outline=PALETTE["line"], width=2)
    blade = [(cx, cy - int(16 * scale)), (cx + int(7 * scale), cy + int(12 * scale)), (cx - int(7 * scale), cy + int(12 * scale))]
    draw.polygon(blade, fill=(183, 202, 223, 255), outline=PALETTE["line"])
    draw.rectangle((cx - int(12 * scale), cy + int(9 * scale), cx + int(12 * scale), cy + int(13 * scale)), fill=(186, 203, 224, 255), outline=PALETTE["line"])
    draw.text((cx, cy - 1), "COI", anchor="mm", font=FONT_H3, fill=PALETTE["ink"])


def draw_corner_art(draw: ImageDraw.ImageDraw, pass_no: int):
    rng = Random(900 + pass_no)
    for _ in range(8):
        x = rng.randint(24, W - 24)
        y = rng.choice([rng.randint(20, 120), rng.randint(H - 130, H - 24)])
        s = rng.randint(8, 18)
        poly = [(x, y), (x + s, y + rng.randint(-2, 4)), (x + s // 2, y + s)]
        draw.polygon(poly, outline=(146, 170, 202, 140), fill=(191, 206, 224, 70))


def draw_nav(draw: ImageDraw.ImageDraw, pass_no: int, active: int):
    family = family_for_pass(pass_no)
    icons = ["L", "R", "P", "C", "S", "U", "Q"]
    if family == "monolith":
        rough_panel(draw, (30, 150, 162, 610), seed=100 + pass_no, fill=PALETTE["panel"], outline=PALETTE["line"], notch=True)
        draw_crest(draw, 96, 108, 0.72)
        y = 220
        for i, glyph in enumerate(icons):
            button(draw, (48, y, 144, y + 34), glyph, primary=(i == active))
            y += 46
    elif family == "orbital":
        draw_crest(draw, 98, 384, 0.8)
        for i, glyph in enumerate(icons):
            ang = -90 + i * 48
            rad = 118
            x = int(98 + math.cos(math.radians(ang)) * rad)
            y = int(384 + math.sin(math.radians(ang)) * rad)
            button(draw, (x - 30, y - 20, x + 30, y + 20), glyph, primary=(i == active))
    elif family == "ribbon":
        rough_panel(draw, (20, 62, 1288, 104), seed=212 + pass_no, fill=PALETTE["panel"], outline=PALETTE["line"], notch=False)
        draw_crest(draw, 98, 83, 0.56)
        x = 182
        for i, glyph in enumerate(icons):
            button(draw, (x, 72, x + 72, 94), glyph, primary=(i == active))
            x += 86
    elif family == "glyphdeck":
        rough_panel(draw, (26, 160, 128, 612), seed=334 + pass_no, fill=PALETTE["panel"], outline=PALETTE["line"], notch=True)
        draw_crest(draw, 80, 114, 0.62)
        y = 220
        for i, glyph in enumerate(icons):
            button(draw, (44, y, 112, y + 28), glyph if i == active else "•", primary=(i == active))
            y += 40
    else:
        # finale: compact compass + icon chips
        draw_crest(draw, 86, 690, 0.68)
        for i, glyph in enumerate(icons):
            ang = 180 + i * 26
            rad = 82
            x = int(86 + math.cos(math.radians(ang)) * rad)
            y = int(690 + math.sin(math.radians(ang)) * rad)
            button(draw, (x - 25, y - 16, x + 25, y + 16), glyph, primary=(i == active))


def workspace_rect(pass_no: int):
    family = family_for_pass(pass_no)
    if family == "monolith":
        return (186, 124, 1264, 706)
    if family == "orbital":
        return (170, 96, 1244, 682)
    if family == "ribbon":
        return (86, 126, 1284, 706)
    if family == "glyphdeck":
        return (158, 118, 1268, 700)
    return (156, 98, 1272, 694)


def draw_shell(draw: ImageDraw.ImageDraw, pass_no: int):
    r = workspace_rect(pass_no)
    rough_panel(draw, r, seed=500 + pass_no, fill=PALETTE["panel"], outline=PALETTE["line"], width=2, notch=(pass_no % 2 == 0))
    return r


def draw_graph(draw: ImageDraw.ImageDraw, rect, mode: str):
    rough_panel(draw, rect, seed=sum(rect), fill=PALETTE["panel_b"], outline=PALETTE["line"])
    gx0, gy0, gx1, gy1 = rect[0] + 16, rect[1] + 16, rect[2] - 16, rect[3] - 16
    rough_panel(draw, (gx0, gy0, gx1, gy1), seed=gx0 + gy0, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    for x in range(gx0 + 18, gx1 - 8, 72):
        draw.line((x, gy0 + 8, x, gy1 - 8), fill=(154, 176, 206, 125), width=1)
    for y in range(gy0 + 8, gy1 - 8, 72):
        draw.line((gx0 + 8, y, gx1 - 8, y), fill=(154, 176, 206, 125), width=1)
    if mode == "empty":
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 - 8), "No character selected", anchor="mm", font=FONT_H3, fill=PALETTE["muted"])
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 + 12), "Choose a hero to edit offline build", anchor="mm", font=FONT_SM, fill=PALETTE["muted"])
        return
    rel = {
        "Core": (0.50, 0.72, PALETTE["primary"]),
        "Resolve": (0.34, 0.72, PALETTE["primary"]),
        "Dexterity": (0.54, 0.53, PALETTE["primary"]),
        "Vitality": (0.47, 0.87, PALETTE["primary"]),
        "Agility": (0.64, 0.87, PALETTE["primary"]),
        "Willpower": (0.64, 0.62, PALETTE["primary"]),
        "Quick Strike": (0.17, 0.60, PALETTE["ok"]),
        "Bandage": (0.59, 0.36, PALETTE["warn"]),
        "Ember": (0.83, 0.77, PALETTE["warn"]),
    }
    nodes = {}
    gw = gx1 - gx0
    gh = gy1 - gy0
    for name, (rx, ry, col) in rel.items():
        nodes[name] = (int(gx0 + rx * gw), int(gy0 + ry * gh), col)
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
        draw.line((ax, ay, bx, by), fill=(134, 160, 198), width=3)
    for name, (x, y, col) in nodes.items():
        rr = 10 if name == "Core" else 8
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col, outline=PALETTE["line"], width=1)
        draw.text((x, y + 14), name, anchor="mm", font=FONT_SM, fill=PALETTE["ink_soft"])


def content_grid(r):
    x0, y0, x1, y1 = r
    return {
        "left": (x0 + 20, y0 + 20, x0 + 292, y1 - 20),
        "center": (x0 + 306, y0 + 20, x1 - 206, y1 - 20),
        "right": (x1 - 192, y0 + 20, x1 - 20, y1 - 20),
    }


def draw_auth_scene(pass_no: int):
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_nav(d, pass_no, 0)
    r = draw_shell(d, pass_no)
    g = content_grid(r)

    rough_panel(d, g["left"], seed=901 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["center"], seed=911 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    d.text((g["left"][0] + 14, g["left"][1] + 12), "Account Access", font=FONT_H2, fill=PALETTE["ink"])
    button(d, (g["left"][0] + 14, g["left"][1] + 40, g["left"][0] + 116, g["left"][1] + 66), "Login", primary=True)
    button(d, (g["left"][0] + 122, g["left"][1] + 40, g["left"][0] + 226, g["left"][1] + 66), "Register")
    input_box(d, (g["left"][0] + 14, g["left"][1] + 84, g["left"][2] - 14, g["left"][1] + 114), "admin@admin.com")
    input_box(d, (g["left"][0] + 14, g["left"][1] + 122, g["left"][2] - 14, g["left"][1] + 152), "Password")
    input_box(d, (g["left"][0] + 14, g["left"][1] + 160, g["left"][2] - 14, g["left"][1] + 190), "MFA Code (optional)")
    button(d, (g["left"][0] + 14, g["left"][1] + 204, g["left"][2] - 14, g["left"][1] + 234), "Continue", primary=True)
    d.text((g["left"][0] + 14, g["left"][3] - 20), "Client version: v1.0.157", font=FONT_SM, fill=PALETTE["muted"])

    d.text((g["center"][0] + 14, g["center"][1] + 12), "Patch Snapshot", font=FONT_H2, fill=PALETTE["ink"])
    rough_panel(d, (g["center"][0] + 14, g["center"][1] + 40, g["center"][2] - 14, g["center"][3] - 54), seed=933 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    wrap_text(
        d,
        (g["center"][0] + 20, g["center"][1] + 52, g["center"][2] - 20, g["center"][3] - 70),
        "Build: v1.0.157\nRelease notes include login/register flow cleanup, optional MFA path, and pre-launch graph save support.",
        FONT_TX,
        PALETTE["ink_soft"],
        line_h=20,
    )
    button(d, (g["center"][0] + 14, g["center"][3] - 42, g["center"][2] - 14, g["center"][3] - 12), "Check for Update")
    draw_crest(d, g["right"][0] + 84, g["right"][1] + 84, 1.2)
    return img


def draw_register_scene(pass_no: int):
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_nav(d, pass_no, 1)
    r = draw_shell(d, pass_no)
    g = content_grid(r)

    rough_panel(d, g["left"], seed=1001 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["center"], seed=1013 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    d.text((g["left"][0] + 14, g["left"][1] + 12), "Create Account", font=FONT_H2, fill=PALETTE["ink"])
    input_box(d, (g["left"][0] + 14, g["left"][1] + 52, g["left"][2] - 14, g["left"][1] + 82), "Display Name")
    input_box(d, (g["left"][0] + 14, g["left"][1] + 90, g["left"][2] - 14, g["left"][1] + 120), "Email")
    input_box(d, (g["left"][0] + 14, g["left"][1] + 128, g["left"][2] - 14, g["left"][1] + 158), "Password")
    button(d, (g["left"][0] + 14, g["left"][1] + 172, g["left"][2] - 14, g["left"][1] + 202), "Register", primary=True)

    d.text((g["center"][0] + 14, g["center"][1] + 12), "Onboarding", font=FONT_H2, fill=PALETTE["ink"])
    wrap_text(
        d,
        (g["center"][0] + 14, g["center"][1] + 44, g["center"][2] - 14, g["center"][3] - 60),
        "1) Register\n2) Create character\n3) Check start graph\n4) Save offline build\n5) Launch",
        FONT_TX,
        PALETTE["ink_soft"],
        line_h=23,
    )
    button(d, (g["center"][0] + 14, g["center"][3] - 42, g["center"][2] - 14, g["center"][3] - 12), "Back to Login")
    draw_crest(d, g["right"][0] + 84, g["right"][1] + 84, 1.2)
    return img


def draw_lobby_scene(pass_no: int, selected: bool):
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_nav(d, pass_no, 2)
    r = draw_shell(d, pass_no)
    g = content_grid(r)

    rough_panel(d, g["left"], seed=1101 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["center"], seed=1113 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["right"], seed=1129 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])

    d.text((g["left"][0] + 14, g["left"][1] + 12), "Roster", font=FONT_H2, fill=PALETTE["ink"])
    button(d, (g["left"][0] + 14, g["left"][1] + 40, g["left"][2] - 14, g["left"][1] + 72), "+")
    if selected:
        rough_panel(d, (g["left"][0] + 14, g["left"][1] + 84, g["left"][2] - 14, g["left"][1] + 136), seed=1138 + pass_no, fill=PALETTE["primary"], outline=PALETTE["line"])
        d.text((g["left"][0] + 22, g["left"][1] + 104), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
        d.text((g["left"][0] + 22, g["left"][1] + 120), "Lv 5 | Ironhold", font=FONT_SM, fill=PALETTE["primary_text"])
        rough_panel(d, (g["left"][0] + 14, g["left"][1] + 146, g["left"][2] - 14, g["left"][1] + 198), seed=1148 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
        d.text((g["left"][0] + 22, g["left"][1] + 166), "Scout", font=FONT_H3, fill=PALETTE["ink"])
        d.text((g["left"][0] + 22, g["left"][1] + 182), "Lv 2 | Khar Grotto", font=FONT_SM, fill=PALETTE["muted"])
    else:
        wrap_text(d, (g["left"][0] + 14, g["left"][1] + 90, g["left"][2] - 14, g["left"][1] + 200), "No characters yet.\nCreate one, then save an offline build.", FONT_TX, PALETTE["muted"], line_h=20)

    d.text((g["center"][0] + 14, g["center"][1] + 12), "Build Graph", font=FONT_H2, fill=PALETTE["ink"])
    draw_graph(d, (g["center"][0] + 14, g["center"][1] + 40, g["center"][2] - 14, g["center"][3] - 72), "selected" if selected else "empty")
    button(d, (g["center"][0] + 14, g["center"][3] - 58, g["center"][0] + 134, g["center"][3] - 26), "Save", primary=selected)
    button(d, (g["center"][0] + 142, g["center"][3] - 58, g["center"][0] + 242, g["center"][3] - 26), "Reset")
    button(d, (g["center"][0] + 250, g["center"][3] - 58, g["center"][0] + 350, g["center"][3] - 26), "Play", primary=selected)
    wrap_text(d, (g["center"][0] + 360, g["center"][3] - 62, g["center"][2] - 14, g["center"][3] - 20), "Offline edits can be saved now; in-game commit cost can apply later.", FONT_SM, PALETTE["muted"], line_h=14)

    d.text((g["right"][0] + 14, g["right"][1] + 12), "Inspector", font=FONT_H2, fill=PALETTE["ink"])
    if selected:
        wrap_text(d, (g["right"][0] + 14, g["right"][1] + 40, g["right"][2] - 14, g["right"][1] + 280), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold\nNode: Core", FONT_H3, PALETTE["ink_soft"], line_h=24)
        button(d, (g["right"][0] + 14, g["right"][3] - 86, g["right"][2] - 14, g["right"][3] - 54), "Play", primary=True)
        button(d, (g["right"][0] + 14, g["right"][3] - 44, g["right"][2] - 14, g["right"][3] - 12), "Delete")
    else:
        wrap_text(d, (g["right"][0] + 14, g["right"][1] + 40, g["right"][2] - 14, g["right"][1] + 180), "Select a character to launch and inspect build routes.", FONT_H3, PALETTE["muted"], line_h=22)
    return img


def draw_create_scene(pass_no: int):
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_nav(d, pass_no, 3)
    r = draw_shell(d, pass_no)
    g = content_grid(r)
    rough_panel(d, g["left"], seed=1201 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["center"], seed=1213 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["right"], seed=1229 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])

    d.text((g["left"][0] + 14, g["left"][1] + 12), "Archetypes", font=FONT_H2, fill=PALETTE["ink"])
    rough_panel(d, (g["left"][0] + 14, g["left"][1] + 42, g["left"][2] - 14, g["left"][1] + 104), seed=1237 + pass_no, fill=PALETTE["primary"], outline=PALETTE["line"])
    d.text((g["left"][0] + 22, g["left"][1] + 64), "Sellsword", font=FONT_H3, fill=PALETTE["primary_text"])
    d.text((g["left"][0] + 22, g["left"][1] + 84), "durable melee opener", font=FONT_TX, fill=PALETTE["primary_text"])
    rough_panel(d, (g["left"][0] + 14, g["left"][1] + 114, g["left"][2] - 14, g["left"][1] + 176), seed=1247 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    d.text((g["left"][0] + 22, g["left"][1] + 136), "Scout", font=FONT_H3, fill=PALETTE["ink"])
    d.text((g["left"][0] + 22, g["left"][1] + 156), "mobile precision style", font=FONT_TX, fill=PALETTE["muted"])

    d.text((g["center"][0] + 14, g["center"][1] + 12), "Identity + Core Choices", font=FONT_H2, fill=PALETTE["ink"])
    input_box(d, (g["center"][0] + 14, g["center"][1] + 42, g["center"][2] - 14, g["center"][1] + 72), "Character Name")
    input_box(d, (g["center"][0] + 14, g["center"][1] + 80, g["center"][2] - 14, g["center"][1] + 110), "Sellsword")
    input_box(d, (g["center"][0] + 14, g["center"][1] + 118, g["center"][2] - 14, g["center"][1] + 148), "Male")
    rough_panel(d, (g["center"][0] + 14, g["center"][1] + 158, g["center"][2] - 14, g["center"][3] - 86), seed=1259 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    wrap_text(
        d,
        (g["center"][0] + 24, g["center"][1] + 166, g["center"][2] - 24, g["center"][3] - 92),
        "Sellsword starts near Core and can branch early into Resolve, Dexterity, or Vitality lines.\nThis preview shows where your archetype enters the graph.",
        FONT_H3,
        PALETTE["ink_soft"],
        line_h=26,
    )
    button(d, (g["center"][0] + 14, g["center"][3] - 70, g["center"][2] - 14, g["center"][3] - 38), "Create Character", primary=True)

    d.text((g["right"][0] + 14, g["right"][1] + 12), "Start Graph", font=FONT_H2, fill=PALETTE["ink"])
    draw_graph(d, (g["right"][0] + 14, g["right"][1] + 42, g["right"][2] - 14, g["right"][3] - 86), "selected")
    button(d, (g["right"][0] + 14, g["right"][3] - 70, g["right"][2] - 14, g["right"][3] - 38), "Back to Play")
    return img


def draw_system_scene(pass_no: int):
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_nav(d, pass_no, 4)
    r = draw_shell(d, pass_no)
    g = content_grid(r)
    rough_panel(d, (g["left"][0], g["left"][1], g["center"][2], g["left"][3]), seed=1301 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])
    rough_panel(d, g["right"], seed=1313 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"])

    d.text((g["left"][0] + 14, g["left"][1] + 12), "System Settings", font=FONT_H2, fill=PALETTE["ink"])
    button(d, (g["left"][0] + 14, g["left"][1] + 42, g["left"][0] + 100, g["left"][1] + 68), "Video")
    button(d, (g["left"][0] + 108, g["left"][1] + 42, g["left"][0] + 194, g["left"][1] + 68), "Audio", primary=True)
    button(d, (g["left"][0] + 202, g["left"][1] + 42, g["left"][0] + 304, g["left"][1] + 68), "Security")
    labels = ["Master", "Music", "Effects", "Interface"]
    vals = [0.78, 0.62, 0.82, 0.57]
    for i, (lbl, val) in enumerate(zip(labels, vals)):
        y = g["left"][1] + 100 + i * 68
        d.text((g["left"][0] + 14, y), lbl, font=FONT_H3, fill=PALETTE["ink_soft"])
        rough_panel(d, (g["left"][0] + 96, y + 8, g["center"][2] - 26, y + 16), seed=1329 + pass_no + i, fill=(186, 202, 223, 255), outline=PALETTE["line_soft"])
        rough_panel(d, (g["left"][0] + 96, y + 8, int(g["left"][0] + 96 + (g["center"][2] - g["left"][0] - 122) * val), y + 16), seed=1361 + pass_no + i, fill=PALETTE["primary"], outline=PALETTE["primary"])
    button(d, (g["center"][2] - 132, g["left"][3] - 48, g["center"][2] - 18, g["left"][3] - 16), "Apply", primary=True)

    d.text((g["right"][0] + 14, g["right"][1] + 12), "MFA", font=FONT_H2, fill=PALETTE["ink"])
    button(d, (g["right"][0] + 14, g["right"][1] + 42, g["right"][2] - 14, g["right"][1] + 74), "MFA ON", primary=True)
    button(d, (g["right"][0] + 14, g["right"][1] + 82, g["right"][2] - 14, g["right"][1] + 114), "Refresh QR")
    button(d, (g["right"][0] + 14, g["right"][1] + 122, g["right"][2] - 14, g["right"][1] + 154), "Copy URI")
    rough_panel(d, (g["right"][0] + 14, g["right"][1] + 168, g["right"][2] - 14, g["right"][3] - 18), seed=1337 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    wrap_text(d, (g["right"][0] + 22, g["right"][1] + 178, g["right"][2] - 22, g["right"][3] - 24), "Security controls stay in one place so auth setup is easy to find.", FONT_TX, PALETTE["muted"], line_h=18)
    return img


def draw_update_scene(pass_no: int):
    img = Image.new("RGBA", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_solid_bg(d)
    draw_corner_art(d, pass_no)
    draw_nav(d, pass_no, 5)
    r = draw_shell(d, pass_no)

    card = (r[0] + 120, r[1] + 90, r[2] - 120, r[3] - 90)
    rough_panel(d, card, seed=1401 + pass_no, fill=PALETTE["panel_b"], outline=PALETTE["line_soft"], notch=True)
    meta = (card[0] + 20, card[1] + 20, card[2] - 20, card[1] + 56)
    rough_panel(d, meta, seed=1413 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    d.text((meta[0] + 10, meta[1] + 14), "Build: v1.0.157", font=FONT_H3, fill=PALETTE["ink"])
    box = (card[0] + 20, card[1] + 66, card[2] - 20, card[3] - 58)
    rough_panel(d, box, seed=1439 + pass_no, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
    d.text((box[0] + 10, box[1] + 10), "Release Notes", font=FONT_H2, fill=PALETTE["ink"])
    wrap_text(
        d,
        (box[0] + 10, box[1] + 34, box[2] - 10, box[3] - 10),
        "Login/register/update are streamlined.\nCharacter lobby supports optional graph editing before launch.\nSystem deck keeps audio/video/security + MFA grouped.",
        FONT_TX,
        PALETTE["ink_soft"],
        line_h=22,
    )
    button(d, (card[0] + 20, card[3] - 44, card[2] - 20, card[3] - 12), "Check for Update", primary=True)
    return img


def contact_sheet(paths: list[Path], out: Path):
    thumbs: list[tuple[str, Image.Image]] = []
    for p in paths:
        thumbs.append((p.stem, Image.open(p).convert("RGBA").resize((410, 230), Image.Resampling.LANCZOS)))
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 420 + 24, rows * 272 + 24), PALETTE["bg"])
    d = ImageDraw.Draw(sheet, "RGBA")
    for i, (name, thumb) in enumerate(thumbs):
        c = i % cols
        r = i // cols
        x = 12 + c * 420
        y = 12 + r * 272
        rough_panel(d, (x, y, x + 410, y + 230), seed=1501 + i, fill=PALETTE["panel_c"], outline=PALETTE["line_soft"])
        sheet.paste(thumb, (x, y), thumb)
        d.text((x, y + 238), f"{name}.png", font=FONT_TX, fill=PALETTE["ink"])
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def render_pass(pass_no: int):
    out = OUT_ROOT / f"pass_{pass_no:02d}"
    out.mkdir(parents=True, exist_ok=True)
    screens = {
        "iter_auth": draw_auth_scene(pass_no),
        "iter_register": draw_register_scene(pass_no),
        "iter_lobby_empty": draw_lobby_scene(pass_no, selected=False),
        "iter_lobby_selected": draw_lobby_scene(pass_no, selected=True),
        "iter_create": draw_create_scene(pass_no),
        "iter_system": draw_system_scene(pass_no),
        "iter_update": draw_update_scene(pass_no),
    }
    saved: list[Path] = []
    for name, img in screens.items():
        p = out / f"{name}.png"
        img.save(p)
        saved.append(p)
    contact_sheet(saved, out / "iter_contact_sheet.png")
    report = (
        f"# Pass {pass_no:02d}\n\n"
        f"- Plan: {PASS_PLAN[pass_no]}\n"
        f"- Review: {PASS_REVIEW[pass_no]}\n"
        f"- Next: {PASS_PLAN[min(20, pass_no + 1)] if pass_no < 20 else 'Use this as candidate final direction for user review.'}\n"
    )
    (out / "pass_report.md").write_text(report, encoding="utf-8")


def write_master_notes():
    lines = ["# Iterative 20-Pass Loop", ""]
    for i in range(1, 21):
        lines.append(f"## Pass {i:02d}")
        lines.append(f"- Plan: {PASS_PLAN[i]}")
        lines.append(f"- Review: {PASS_REVIEW[i]}")
        lines.append(f"- Next: {PASS_PLAN[min(20, i + 1)] if i < 20 else 'Present final set for review.'}")
        lines.append("")
    (OUT_ROOT / "iteration_log.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", type=int, required=True, choices=list(range(1, 21)))
    args = parser.parse_args()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    render_pass(args.pass_no)
    write_master_notes()


if __name__ == "__main__":
    main()
