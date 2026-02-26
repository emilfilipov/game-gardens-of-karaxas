#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import textwrap
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFont

W, H = 1366, 768

COL = {
    "bg": (170, 188, 214, 255),
    "panel": (197, 208, 223, 246),
    "panel_b": (189, 202, 219, 245),
    "panel_c": (205, 214, 228, 245),
    "line": (130, 158, 196, 255),
    "line_soft": (153, 176, 206, 220),
    "text": (35, 56, 90, 255),
    "text_soft": (70, 92, 124, 255),
    "muted": (92, 110, 138, 255),
    "primary": (88, 139, 214, 255),
    "primary_t": (237, 243, 250, 255),
    "ok": (111, 188, 143, 255),
    "warn": (235, 176, 92, 255),
}

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "concept_art" / "option_true_iterative_20pass"


def font(cands, size):
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_H1 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 32)
F_H2 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 21)
F_H3 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 16)
F_TX = font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 14)
F_SM = font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)


def rough(draw: ImageDraw.ImageDraw, rect, seed: int, fill, outline, width=1):
    x0, y0, x1, y1 = rect
    rng = Random(seed)
    j = 8
    pts = [
        (x0 + rng.randint(0, j), y0 + rng.randint(0, j)),
        (x1 - rng.randint(0, j), y0 + rng.randint(0, j)),
        (x1 - rng.randint(0, j), y1 - rng.randint(0, j)),
        (x0 + rng.randint(0, j), y1 - rng.randint(0, j)),
    ]
    draw.polygon(pts, fill=fill, outline=outline)
    if width > 1:
        draw.line(pts + [pts[0]], fill=outline, width=width)


def button(draw, rect, label, primary=False):
    fill = COL["primary"] if primary else (225, 223, 214, 255)
    txt = COL["primary_t"] if primary else COL["text"]
    rough(draw, rect, seed=sum(rect) + len(label), fill=fill, outline=COL["line"], width=1)
    draw.text(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), label, anchor="mm", font=F_H3, fill=txt)


def field(draw, rect, val):
    rough(draw, rect, seed=sum(rect), fill=COL["panel_c"], outline=COL["line_soft"], width=1)
    draw.text((rect[0] + 10, (rect[1] + rect[3]) // 2), val, anchor="lm", font=F_H3, fill=COL["muted"])


def wrap(draw, rect, txt, line_h=20):
    x0, y0, x1, y1 = rect
    avg = 8
    for i, ln in enumerate(textwrap.wrap(txt, width=max(12, (x1 - x0 - 20) // avg))):
        y = y0 + 10 + i * line_h
        if y + line_h > y1 - 6:
            break
        draw.text((x0 + 10, y), ln, font=F_TX, fill=COL["text_soft"])


def crest(draw, cx, cy):
    draw.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=COL["panel"], outline=COL["line"], width=2)
    draw.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=COL["panel_b"], outline=COL["line_soft"], width=2)
    draw.polygon([(cx, cy - 15), (cx + 7, cy + 13), (cx - 7, cy + 13)], fill=(183, 202, 223, 255), outline=COL["line"])
    draw.rectangle((cx - 12, cy + 9, cx + 12, cy + 13), fill=(186, 203, 224, 255), outline=COL["line"])
    draw.text((cx, cy - 1), "COI", anchor="mm", font=F_H3, fill=COL["text"])


def corner_art(draw, pass_no: int):
    rng = Random(700 + pass_no)
    for _ in range(14):
        x = rng.randint(30, W - 30)
        y = rng.choice([rng.randint(16, 130), rng.randint(H - 120, H - 20)])
        s = rng.randint(8, 18)
        draw.polygon([(x, y), (x + s, y + rng.randint(-3, 3)), (x + s // 2, y + s)], fill=(192, 207, 224, 90), outline=(143, 166, 199, 130))


def draw_graph(draw, rect, selected=True):
    rough(draw, rect, seed=sum(rect), fill=COL["panel_b"], outline=COL["line"])
    gx0, gy0, gx1, gy1 = rect[0] + 16, rect[1] + 16, rect[2] - 16, rect[3] - 16
    rough(draw, (gx0, gy0, gx1, gy1), seed=gx0 + gy0, fill=COL["panel_c"], outline=COL["line_soft"])
    for x in range(gx0 + 20, gx1 - 8, 74):
        draw.line((x, gy0 + 8, x, gy1 - 8), fill=(154, 176, 206, 120), width=1)
    for y in range(gy0 + 8, gy1 - 8, 74):
        draw.line((gx0 + 8, y, gx1 - 8, y), fill=(154, 176, 206, 120), width=1)
    if not selected:
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 - 6), "No character selected", anchor="mm", font=F_H3, fill=COL["muted"])
        draw.text(((gx0 + gx1) // 2, (gy0 + gy1) // 2 + 14), "Choose hero to edit offline build", anchor="mm", font=F_SM, fill=COL["muted"])
        return
    nodes = {
        "Core": (0.50, 0.72, COL["primary"]),
        "Resolve": (0.36, 0.72, COL["primary"]),
        "Dexterity": (0.54, 0.54, COL["primary"]),
        "Vitality": (0.47, 0.88, COL["primary"]),
        "Agility": (0.64, 0.88, COL["primary"]),
        "Willpower": (0.64, 0.62, COL["primary"]),
        "Quick Strike": (0.18, 0.62, COL["ok"]),
        "Bandage": (0.58, 0.36, COL["warn"]),
        "Ember": (0.84, 0.78, COL["warn"]),
    }
    gw, gh = gx1 - gx0, gy1 - gy0
    p = {k: (int(gx0 + rx * gw), int(gy0 + ry * gh), c) for k, (rx, ry, c) in nodes.items()}
    edges = [("Core", "Resolve"), ("Core", "Dexterity"), ("Core", "Vitality"), ("Core", "Agility"), ("Core", "Willpower"), ("Resolve", "Quick Strike"), ("Dexterity", "Bandage"), ("Agility", "Ember")]
    for a, b in edges:
        draw.line((p[a][0], p[a][1], p[b][0], p[b][1]), fill=(133, 160, 198), width=3)
    for k, (x, y, c) in p.items():
        r = 10 if k == "Core" else 8
        draw.ellipse((x - r, y - r, x + r, y + r), fill=c, outline=COL["line"], width=1)
        draw.text((x, y + 14), k, anchor="mm", font=F_SM, fill=COL["text_soft"])


def scene_auth(pass_no: int):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    rough(d, (24, 136, 154, 620), seed=101 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    crest(d, 89, 92)
    for i, lab in enumerate(["L", "R", "P", "C", "S", "U", "Q"]):
        button(d, (40, 204 + i * 50, 138, 238 + i * 50), lab, primary=(i == 0))
    rough(d, (184, 106, 1266, 700), seed=199 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    rough(d, (210, 132, 612, 674), seed=211 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (628, 132, 1238, 674), seed=229 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((230, 160), "Account Access", font=F_H2, fill=COL["text"])
    button(d, (230, 188, 334, 216), "Login", primary=True)
    button(d, (342, 188, 446, 216), "Register")
    field(d, (230, 232, 592, 264), "admin@admin.com")
    field(d, (230, 272, 592, 304), "Password")
    field(d, (230, 312, 592, 344), "MFA Code (optional)")
    button(d, (230, 356, 592, 390), "Continue", primary=True)
    d.text((230, 648), "Client version: v1.0.157", font=F_SM, fill=COL["muted"])

    d.text((648, 160), "Patch Snapshot", font=F_H2, fill=COL["text"])
    rough(d, (648, 190, 1210, 618), seed=257 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    wrap(d, (658, 200, 1200, 604), "Build: v1.0.157. Login, register and update are merged into one fast route. Optional MFA and graph save remain available from settings and lobby.")
    button(d, (648, 630, 1210, 664), "Check for Update")
    return img


def scene_register(pass_no: int):
    img = scene_auth(pass_no)
    d = ImageDraw.Draw(img, "RGBA")
    # overwrite active mode region to register variant
    rough(d, (210, 132, 612, 674), seed=311 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((230, 160), "Create Account", font=F_H2, fill=COL["text"])
    field(d, (230, 232, 592, 264), "Display Name")
    field(d, (230, 272, 592, 304), "Email")
    field(d, (230, 312, 592, 344), "Password")
    button(d, (230, 356, 592, 390), "Register", primary=True)
    return img


def scene_lobby(pass_no: int, selected: bool):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    rough(d, (24, 136, 154, 620), seed=401 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    crest(d, 89, 92)
    for i, lab in enumerate(["L", "R", "P", "C", "S", "U", "Q"]):
        button(d, (40, 204 + i * 50, 138, 238 + i * 50), lab, primary=(i == 2))
    rough(d, (184, 106, 1266, 700), seed=501 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    rough(d, (210, 132, 452, 674), seed=517 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (466, 132, 1048, 674), seed=533 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (1062, 132, 1238, 674), seed=547 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((230, 160), "Roster", font=F_H2, fill=COL["text"])
    button(d, (230, 188, 432, 220), "+")
    if selected:
        rough(d, (230, 232, 432, 290), seed=561 + pass_no, fill=COL["primary"], outline=COL["line"])
        d.text((244, 252), "Sellsword", font=F_H3, fill=COL["primary_t"])
        d.text((244, 270), "Lv 5 | Ironhold", font=F_SM, fill=COL["primary_t"])
        rough(d, (230, 298, 432, 356), seed=571 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
        d.text((244, 318), "Scout", font=F_H3, fill=COL["text"])
        d.text((244, 336), "Lv 2 | Khar Grotto", font=F_SM, fill=COL["muted"])
    else:
        wrap(d, (230, 236, 432, 342), "No characters yet. Create one and save an offline build.", line_h=19)
    d.text((486, 160), "Build Graph", font=F_H2, fill=COL["text"])
    draw_graph(d, (486, 190, 1028, 596), selected=selected)
    button(d, (486, 610, 606, 644), "Save", primary=selected)
    button(d, (614, 610, 704, 644), "Reset")
    button(d, (712, 610, 810, 644), "Play", primary=selected)
    wrap(d, (818, 610, 1028, 646), "Offline save before launch.", line_h=14)
    d.text((1082, 160), "Inspector", font=F_H2, fill=COL["text"])
    if selected:
        wrap(d, (1082, 188, 1218, 420), "Name: Sellsword. Class: Mercenary. Sex: Male. Zone: Ironhold. Node: Core.", line_h=22)
        button(d, (1082, 596, 1218, 628), "Play", primary=True)
        button(d, (1082, 636, 1218, 668), "Delete")
    else:
        wrap(d, (1082, 188, 1218, 330), "Select a character to launch and inspect build routes.", line_h=22)
    return img


def scene_create(pass_no: int):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    rough(d, (24, 136, 154, 620), seed=601 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    crest(d, 89, 92)
    for i, lab in enumerate(["L", "R", "P", "C", "S", "U", "Q"]):
        button(d, (40, 204 + i * 50, 138, 238 + i * 50), lab, primary=(i == 3))
    rough(d, (184, 106, 1266, 700), seed=701 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    rough(d, (210, 132, 452, 674), seed=717 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (466, 132, 962, 674), seed=733 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (976, 132, 1238, 674), seed=747 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((230, 160), "Archetypes", font=F_H2, fill=COL["text"])
    rough(d, (230, 188, 432, 252), seed=761 + pass_no, fill=COL["primary"], outline=COL["line"])
    d.text((244, 212), "Sellsword", font=F_H3, fill=COL["primary_t"])
    d.text((244, 232), "durable melee opener", font=F_TX, fill=COL["primary_t"])
    rough(d, (230, 262, 432, 326), seed=771 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    d.text((244, 286), "Scout", font=F_H3, fill=COL["text"])
    d.text((244, 306), "mobile precision style", font=F_TX, fill=COL["muted"])
    d.text((486, 160), "Identity + Core Choices", font=F_H2, fill=COL["text"])
    field(d, (486, 188, 942, 220), "Character Name")
    field(d, (486, 228, 942, 260), "Sellsword")
    field(d, (486, 268, 942, 300), "Male")
    rough(d, (486, 310, 942, 596), seed=783 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    wrap(d, (496, 322, 932, 584), "Sellsword starts near Core and can branch into Resolve, Dexterity, and Vitality routes. This preview communicates long-term path options.", line_h=24)
    button(d, (486, 610, 942, 644), "Create Character", primary=True)
    d.text((996, 160), "Start Graph", font=F_H2, fill=COL["text"])
    draw_graph(d, (996, 188, 1218, 596), selected=True)
    button(d, (996, 610, 1218, 644), "Back to Play")
    return img


def scene_system(pass_no: int):
    img = scene_create(pass_no)
    d = ImageDraw.Draw(img, "RGBA")
    rough(d, (210, 132, 962, 674), seed=883 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (976, 132, 1238, 674), seed=897 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((230, 160), "System Settings", font=F_H2, fill=COL["text"])
    button(d, (230, 188, 316, 216), "Video")
    button(d, (324, 188, 410, 216), "Audio", primary=True)
    button(d, (418, 188, 514, 216), "Security")
    for i, (lbl, v) in enumerate([("Master", 0.78), ("Music", 0.62), ("Effects", 0.83), ("Interface", 0.57)]):
        y = 240 + i * 80
        d.text((230, y), lbl, font=F_H3, fill=COL["text_soft"])
        rough(d, (320, y + 8, 942, y + 16), seed=913 + pass_no + i, fill=(186, 202, 223, 255), outline=COL["line_soft"])
        rough(d, (320, y + 8, int(320 + (622 * v)), y + 16), seed=937 + pass_no + i, fill=COL["primary"], outline=COL["primary"])
    button(d, (826, 620, 942, 652), "Apply", primary=True)

    d.text((996, 160), "MFA", font=F_H2, fill=COL["text"])
    button(d, (996, 188, 1218, 220), "MFA ON", primary=True)
    button(d, (996, 228, 1218, 260), "Refresh QR")
    button(d, (996, 268, 1218, 300), "Copy URI")
    rough(d, (996, 310, 1218, 652), seed=953 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    wrap(d, (1006, 320, 1208, 640), "Security and optional MFA are controlled in one place.", line_h=20)
    return img


def scene_update(pass_no: int):
    img = scene_auth(pass_no)
    d = ImageDraw.Draw(img, "RGBA")
    rough(d, (210, 132, 1238, 674), seed=1011 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (236, 168, 1212, 212), seed=1029 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    d.text((250, 182), "Build: v1.0.157", font=F_H3, fill=COL["text"])
    rough(d, (236, 224, 1212, 610), seed=1043 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    d.text((250, 244), "Release Notes", font=F_H2, fill=COL["text"])
    wrap(d, (250, 270, 1196, 590), "Auth, update, and optional MFA remain connected. Character lobby supports offline graph edits before launch. System deck keeps audio/video/security in one route.")
    button(d, (236, 622, 1212, 656), "Check for Update", primary=True)
    return img


def draw_arc_nav(draw: ImageDraw.ImageDraw, pass_no: int, active: int):
    crest(draw, 100, 98)
    if pass_no >= 3:
        icons = ["L", "P", "C", "S", "U", "Q"]
    else:
        icons = ["L", "R", "P", "C", "S", "U", "Q"]
    for i, ic in enumerate(icons):
        ang = 210 + i * (24 if pass_no >= 3 else 20)
        rad = 126 if pass_no >= 3 else 120
        x = int(100 + math.cos(math.radians(ang)) * rad)
        y = int(98 + math.sin(math.radians(ang)) * rad)
        button(draw, (x - (26 if pass_no >= 3 else 24), y - 15, x + (26 if pass_no >= 3 else 24), y + 15), ic, primary=(i == active))


def scene_auth_v2(pass_no: int):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    draw_arc_nav(d, pass_no, 0)

    if pass_no >= 3:
        rough(d, (200, 94, 1248, 690), seed=2011 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
        rough(d, (252, 154, 964, 602), seed=2021 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (980, 154, 1214, 602), seed=2033 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        d.text((274, 180), "Account Access", font=F_H2, fill=COL["text"])
        field(d, (274, 220, 936, 254), "admin@admin.com")
        field(d, (274, 264, 936, 298), "Password")
        field(d, (274, 308, 936, 342), "MFA Code (optional)")
        button(d, (274, 356, 936, 392), "Continue", primary=True)
        d.text((274, 568), "Client version: v1.0.157", font=F_SM, fill=COL["muted"])
        d.text((274, 548), "MFA available in System", font=F_SM, fill=COL["muted"])
        d.text((996, 180), "Update", font=F_H2, fill=COL["text"])
        wrap(d, (992, 212, 1204, 514), "Build v1.0.157. Check updates before login. Notes stay concise in the update panel.", line_h=20)
        button(d, (992, 528, 1202, 562), "Check Update")
    else:
        rough(d, (200, 94, 1248, 690), seed=2011 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
        rough(d, (236, 130, 836, 654), seed=2021 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (860, 190, 1212, 654), seed=2033 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        d.text((258, 158), "Access", font=F_H2, fill=COL["text"])
        field(d, (258, 194, 808, 228), "admin@admin.com")
        field(d, (258, 238, 808, 272), "Password")
        field(d, (258, 282, 808, 316), "MFA Code (optional)")
        button(d, (258, 332, 808, 368), "Continue", primary=True)
        button(d, (258, 380, 528, 414), "Login", primary=True)
        button(d, (538, 380, 808, 414), "Register")
        d.text((258, 626), "Client version: v1.0.157", font=F_SM, fill=COL["muted"])
        d.text((258, 602), "Security setup in System", font=F_SM, fill=COL["muted"])
        d.text((882, 220), "Live Notes", font=F_H2, fill=COL["text"])
        rough(d, (882, 250, 1188, 582), seed=2047 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
        wrap(d, (890, 258, 1180, 570), "Build: v1.0.157. Entry route merges login and update awareness. Optional MFA remains in system menu.")
        button(d, (882, 596, 1188, 630), "Check for Update")
    return img


def scene_register_v2(pass_no: int):
    img = scene_auth_v2(pass_no)
    d = ImageDraw.Draw(img, "RGBA")
    rough(d, (236, 130, 836, 654), seed=2069 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((258, 158), "Create Account", font=F_H2, fill=COL["text"])
    field(d, (258, 194, 808, 228), "Display Name")
    field(d, (258, 238, 808, 272), "Email")
    field(d, (258, 282, 808, 316), "Password")
    button(d, (258, 332, 808, 368), "Register", primary=True)
    button(d, (258, 380, 808, 414), "Back to Login")
    return img


def scene_lobby_v2(pass_no: int, selected: bool):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    draw_arc_nav(d, pass_no, 2)

    if pass_no >= 3:
        rough(d, (188, 94, 1248, 690), seed=2101 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
        rough(d, (224, 126, 486, 336), seed=2119 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (224, 352, 486, 654), seed=2123 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (504, 126, 1220, 594), seed=2129 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (504, 606, 1220, 654), seed=2141 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
        d.text((242, 152), "Roster", font=F_H2, fill=COL["text"])
        button(d, (242, 182, 468, 214), "+")
        if selected:
            rough(d, (242, 228, 468, 286), seed=2153 + pass_no, fill=COL["primary"], outline=COL["line"])
            d.text((256, 250), "Sellsword", font=F_H3, fill=COL["primary_t"])
            d.text((256, 268), "Lv 5 | Ironhold", font=F_SM, fill=COL["primary_t"])
        else:
            wrap(d, (242, 228, 468, 316), "No characters yet. Create one.", line_h=19)
        d.text((242, 378), "Inspector", font=F_H2, fill=COL["text"])
        if selected:
            wrap(d, (242, 408, 468, 590), "Name: Sellsword. Class: Mercenary. Node: Core.", line_h=22)
            button(d, (242, 602, 354, 634), "Play", primary=True)
            button(d, (360, 602, 468, 634), "Delete")
        else:
            wrap(d, (242, 408, 468, 560), "Select character to launch and inspect.", line_h=21)
        d.text((522, 152), "Graph Canvas", font=F_H2, fill=COL["text"])
        draw_graph(d, (522, 182, 1202, 584), selected=selected)
        button(d, (522, 614, 672, 646), "Save", primary=selected)
        button(d, (680, 614, 792, 646), "Reset")
        button(d, (800, 614, 912, 646), "Play", primary=selected)
        wrap(d, (920, 614, 1202, 646), "Offline build can be saved before launch.", line_h=14)
    else:
        rough(d, (188, 94, 1248, 690), seed=2101 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
        rough(d, (224, 126, 430, 654), seed=2119 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (448, 126, 1044, 654), seed=2129 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        rough(d, (1062, 126, 1220, 654), seed=2137 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
        d.text((242, 152), "Characters", font=F_H2, fill=COL["text"])
        button(d, (242, 182, 412, 214), "+")
        if selected:
            rough(d, (242, 228, 412, 286), seed=2153 + pass_no, fill=COL["primary"], outline=COL["line"])
            d.text((254, 250), "Sellsword", font=F_H3, fill=COL["primary_t"])
            d.text((254, 268), "Lv 5 | Ironhold", font=F_SM, fill=COL["primary_t"])
            rough(d, (242, 294, 412, 352), seed=2167 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
            d.text((254, 316), "Scout", font=F_H3, fill=COL["text"])
            d.text((254, 334), "Lv 2 | Khar Grotto", font=F_SM, fill=COL["muted"])
        else:
            wrap(d, (242, 230, 412, 346), "No characters yet. Create one and save an offline build.", line_h=19)
        d.text((468, 152), "Build Stage", font=F_H2, fill=COL["text"])
        draw_graph(d, (468, 182, 1024, 578), selected=selected)
        rough(d, (468, 590, 1024, 646), seed=2191 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
        button(d, (478, 600, 618, 634), "Save", primary=selected)
        button(d, (628, 600, 728, 634), "Reset")
        button(d, (738, 600, 838, 634), "Play", primary=selected)
        wrap(d, (848, 600, 1010, 634), "Offline build save.", line_h=14)
        d.text((1082, 152), "Node", font=F_H2, fill=COL["text"])
        if selected:
            wrap(d, (1080, 186, 1212, 446), "Name: Sellsword. Class: Mercenary. Node: Core. Routes: Resolve, Dexterity, Vitality.", line_h=24)
            button(d, (1080, 584, 1212, 616), "Play", primary=True)
            button(d, (1080, 624, 1212, 656), "Delete")
        else:
            wrap(d, (1080, 186, 1212, 360), "No character selected.", line_h=24)
    return img


def scene_create_v2(pass_no: int):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    draw_arc_nav(d, pass_no, 3)

    rough(d, (188, 94, 1248, 690), seed=2203 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    rough(d, (224, 126, 500, 654), seed=2219 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (514, 126, 930, 654), seed=2229 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (944, 126, 1220, 654), seed=2237 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((242, 152), "Archetypes", font=F_H2, fill=COL["text"])
    rough(d, (242, 184, 482, 252), seed=2251 + pass_no, fill=COL["primary"], outline=COL["line"])
    d.text((256, 210), "Sellsword", font=F_H3, fill=COL["primary_t"])
    d.text((256, 230), "durable melee opener", font=F_TX, fill=COL["primary_t"])
    rough(d, (242, 266, 482, 334), seed=2263 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    d.text((256, 292), "Scout", font=F_H3, fill=COL["text"])
    d.text((256, 312), "mobile precision style", font=F_TX, fill=COL["muted"])
    d.text((534, 152), "Identity", font=F_H2, fill=COL["text"])
    field(d, (534, 184, 910, 218), "Character Name")
    field(d, (534, 228, 910, 262), "Sellsword")
    field(d, (534, 272, 910, 306), "Male")
    rough(d, (534, 320, 910, 600), seed=2273 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    wrap(d, (544, 332, 900, 590), "Sellsword starts near Core and branches toward Resolve, Dexterity, and Vitality. Graph preview explains opening routes.", line_h=24)
    button(d, (534, 612, 910, 646), "Create Character", primary=True)
    d.text((964, 152), "Starting Graph", font=F_H2, fill=COL["text"])
    draw_graph(d, (964, 184, 1200, 600), selected=True)
    button(d, (964, 612, 1200, 646), "Back to Play")
    return img


def scene_system_v2(pass_no: int):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    draw_arc_nav(d, pass_no, 4)
    rough(d, (188, 94, 1248, 690), seed=2303 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    rough(d, (224, 126, 928, 654), seed=2317 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    rough(d, (944, 126, 1220, 654), seed=2329 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((242, 152), "System", font=F_H2, fill=COL["text"])
    button(d, (242, 182, 330, 212), "Video")
    button(d, (338, 182, 426, 212), "Audio", primary=True)
    button(d, (434, 182, 530, 212), "Security")
    for i, (lbl, v) in enumerate([("Master", 0.78), ("Music", 0.62), ("Effects", 0.83), ("Interface", 0.57)]):
        y = 240 + i * 80
        d.text((242, y), lbl, font=F_H3, fill=COL["text_soft"])
        rough(d, (326, y + 8, 910, y + 16), seed=2339 + i + pass_no, fill=(186, 202, 223, 255), outline=COL["line_soft"])
        rough(d, (326, y + 8, int(326 + 584 * v), y + 16), seed=2363 + i + pass_no, fill=COL["primary"], outline=COL["primary"])
    button(d, (794, 612, 910, 644), "Apply", primary=True)
    d.text((964, 152), "MFA", font=F_H2, fill=COL["text"])
    button(d, (964, 184, 1200, 216), "MFA ON", primary=True)
    button(d, (964, 226, 1200, 258), "Refresh QR")
    button(d, (964, 268, 1200, 300), "Copy URI")
    rough(d, (964, 312, 1200, 644), seed=2377 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    wrap(d, (974, 322, 1190, 634), "Security and optional MFA stay in one deck.", line_h=20)
    return img


def scene_update_v2(pass_no: int):
    img = Image.new("RGBA", (W, H), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=COL["bg"])
    corner_art(d, pass_no)
    draw_arc_nav(d, pass_no, 5)
    rough(d, (256, 130, 1210, 650), seed=2401 + pass_no, fill=COL["panel"], outline=COL["line"], width=2)
    rough(d, (286, 168, 1180, 212), seed=2419 + pass_no, fill=COL["panel_c"], outline=COL["line_soft"])
    d.text((302, 182), "Build: v1.0.157", font=F_H3, fill=COL["text"])
    rough(d, (286, 224, 1180, 578), seed=2429 + pass_no, fill=COL["panel_b"], outline=COL["line_soft"])
    d.text((302, 246), "Release Notes", font=F_H2, fill=COL["text"])
    wrap(d, (302, 274, 1164, 560), "Login and update share one launch route. Character selection and creation both include graph context. Security and MFA remain consolidated in settings.")
    button(d, (286, 592, 1180, 626), "Check for Update", primary=True)
    return img


def sheet(paths, out):
    thumbs = []
    for p in paths:
        thumbs.append((p.stem, Image.open(p).convert("RGBA").resize((410, 230), Image.Resampling.LANCZOS)))
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    img = Image.new("RGBA", (cols * 420 + 24, rows * 272 + 24), COL["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    for i, (name, th) in enumerate(thumbs):
        c = i % cols
        r = i // cols
        x = 12 + c * 420
        y = 12 + r * 272
        rough(d, (x, y, x + 410, y + 230), seed=1301 + i, fill=COL["panel_c"], outline=COL["line_soft"])
        img.paste(th, (x, y), th)
        d.text((x, y + 238), f"{name}.png", font=F_TX, fill=COL["text"])
    img.save(out)


def render(pass_no: int):
    pdir = OUT / f"pass_{pass_no:02d}"
    pdir.mkdir(parents=True, exist_ok=True)
    if pass_no == 1:
        scenes = {
            "true_auth": scene_auth(pass_no),
            "true_register": scene_register(pass_no),
            "true_lobby_empty": scene_lobby(pass_no, False),
            "true_lobby_selected": scene_lobby(pass_no, True),
            "true_create": scene_create(pass_no),
            "true_system": scene_system(pass_no),
            "true_update": scene_update(pass_no),
        }
    elif pass_no == 2:
        scenes = {
            "true_auth": scene_auth_v2(pass_no),
            "true_register": scene_register_v2(pass_no),
            "true_lobby_empty": scene_lobby_v2(pass_no, False),
            "true_lobby_selected": scene_lobby_v2(pass_no, True),
            "true_create": scene_create_v2(pass_no),
            "true_system": scene_system_v2(pass_no),
            "true_update": scene_update_v2(pass_no),
        }
    else:
        scenes = {
            "true_auth": scene_auth_v2(pass_no),
            "true_register": scene_register_v2(pass_no),
            "true_lobby_empty": scene_lobby_v2(pass_no, False),
            "true_lobby_selected": scene_lobby_v2(pass_no, True),
            "true_create": scene_create_v2(pass_no),
            "true_system": scene_system_v2(pass_no),
            "true_update": scene_update_v2(pass_no),
        }
    paths = []
    for n, im in scenes.items():
        path = pdir / f"{n}.png"
        im.save(path)
        paths.append(path)
    sheet(paths, pdir / "true_contact_sheet.png")


def write_process(pass_no: int):
    if pass_no == 1:
        txt = (
            f"# Pass {pass_no:02d}\n\n"
            "- Plan: Build a non-placeholder carved UI shell with integrated auth/update flow and graph-ready lobby.\n"
            "- Draw: Added custom crest art, custom corner motifs, rough-edged carved panels, and icon glyph rail.\n"
            "- Review: Layout still too close to fixed three-column slabs and left-rail dependence.\n"
            "- Next: Recompose with radial controls and floating modules for pass 2.\n"
        )
    elif pass_no == 2:
        txt = (
            f"# Pass {pass_no:02d}\n\n"
            "- Plan: Break the fixed-column feel with radial command navigation and floating module cards.\n"
            "- Draw: Rebuilt all screens around an arc-nav motif with larger center stage and asym module placement.\n"
            "- Review: Discoverability improved, but lobby remains cramped and too many micro-actions compete.\n"
            "- Next: Recompose lobby into roster+inspector stack + wide graph stage and simplify action rhythm.\n"
        )
    else:
        txt = (
            f"# Pass {pass_no:02d}\n\n"
            "- Plan: Improve hierarchy and reduce micro-button density while keeping graph optional edit flow.\n"
            "- Draw: Rebuilt lobby composition into a stacked side utility + wide graph canvas stage with clearer action row.\n"
            "- Review: Check whether this split improves scan speed and launch clarity.\n"
            "- Next: Continue reducing redundant controls and strengthen icon semantics in pass 4.\n"
        )
    (OUT / f"pass_{pass_no:02d}" / "process.md").write_text(txt, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", required=True, type=int, choices=list(range(1, 21)))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    render(args.pass_no)
    write_process(args.pass_no)


if __name__ == "__main__":
    main()
