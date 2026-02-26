#!/usr/bin/env python3
"""Generate three distinct UI concept options in separate folders.

Outputs:
- concept_art/option_atlas_workspace/
- concept_art/option_dual_pane_studio/
- concept_art/option_command_palette/
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "concept_art"
W, H = 1366, 768

PALETTE = {
    "bg": (194, 209, 229),
    "bg_alt": (186, 203, 225),
    "panel": (236, 242, 250),
    "panel_alt": (228, 236, 247),
    "border": (146, 169, 199),
    "border_soft": (165, 183, 210),
    "text": (27, 44, 72),
    "text_soft": (62, 82, 108),
    "text_muted": (88, 106, 132),
    "primary": (82, 138, 210),
    "primary_text": (244, 249, 255),
    "button": (246, 244, 235),
    "button_text": (57, 74, 100),
    "success": (86, 168, 110),
    "warning": (237, 173, 84),
    "graph_node": (99, 150, 217),
    "graph_active": (103, 194, 128),
    "graph_special": (242, 172, 77),
}


def _font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


FONT_TITLE = _font(ROOT / "game-client" / "assets" / "fonts" / "cinzel.ttf", 56)
FONT_H = _font(ROOT / "game-client" / "assets" / "fonts" / "cinzel.ttf", 18)
FONT_BODY = _font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 24)
FONT_SM = _font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 20)
FONT_XS = _font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 17)


def rr(draw: ImageDraw.ImageDraw, rect, fill, r=8, outline=None, w=1):
    draw.rounded_rectangle(rect, radius=r, fill=fill, outline=outline, width=w)


def _split_token(draw: ImageDraw.ImageDraw, token: str, font, max_w: int) -> list[str]:
    if draw.textlength(token, font=font) <= max_w:
        return [token]
    out: list[str] = []
    i = 0
    while i < len(token):
        j = i + 1
        while j <= len(token) and draw.textlength(token[i:j], font=font) <= max_w:
            j += 1
        end = max(i + 1, j - 1)
        out.append(token[i:end])
        i = end
    return out


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int, max_lines: int | None = None) -> list[str]:
    lines: list[str] = []
    for part in text.split("\n"):
        words = part.split()
        if not words:
            lines.append("")
            continue
        line = ""
        for raw in words:
            for word in _split_token(draw, raw, font, max_w):
                cand = f"{line} {word}".strip()
                if not line or draw.textlength(cand, font=font) <= max_w:
                    line = cand
                else:
                    lines.append(line)
                    line = word
        if line:
            lines.append(line)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "...", font=font) > max_w:
            last = last[:-1]
        lines[-1] = (last + "...") if last else "..."
    return lines


def tbox(draw: ImageDraw.ImageDraw, pos, text: str, font, color, max_w: int, line_h: int = 22, max_lines: int | None = None):
    x, y = pos
    for i, line in enumerate(wrap(draw, text, font, max_w, max_lines=max_lines)):
        draw.text((x, y + i * line_h), line, font=font, fill=color)


def button(draw: ImageDraw.ImageDraw, rect, label: str, primary: bool = False):
    fill = PALETTE["primary"] if primary else PALETTE["button"]
    text = PALETTE["primary_text"] if primary else PALETTE["button_text"]
    rr(draw, rect, fill, r=4, outline=PALETTE["border_soft"], w=1)
    draw.text(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), label, anchor="mm", font=FONT_SM, fill=text)


def input_box(draw: ImageDraw.ImageDraw, rect, placeholder: str, value: str = ""):
    rr(draw, rect, PALETTE["panel_alt"], r=4, outline=PALETTE["border_soft"], w=1)
    draw.text((rect[0] + 10, (rect[1] + rect[3]) // 2), value if value else placeholder, anchor="lm", font=FONT_XS, fill=PALETTE["text"] if value else PALETTE["text_muted"])


def draw_header(img: Image.Image):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, H), fill=PALETTE["bg"] + (255,))
    d.rectangle((0, 0, W, 100), fill=PALETTE["bg_alt"] + (128,))
    d.text((W // 2, 44), "Children of Ikphelion", anchor="mm", font=FONT_TITLE, fill=PALETTE["text"])
    d.line((24, 98, W - 24, 98), fill=PALETTE["border_soft"], width=1)


def sidebar(draw: ImageDraw.ImageDraw, items: list[str], active: int | None, x=24, y=156, h=444):
    rr(draw, (x, y, x + 136, y + h), PALETTE["panel_alt"], r=8, outline=PALETTE["border"], w=1)
    by = y + (h - (len(items) * 34 + (len(items) - 1) * 10)) // 2
    for i, item in enumerate(items):
        button(draw, (x + 16, by + i * 44, x + 120, by + i * 44 + 34), item, primary=(active == i))


def draw_graph(draw: ImageDraw.ImageDraw, rect, mode: str):
    x0, y0, x1, y1 = rect
    rr(draw, rect, PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)

    gx = x0 + 18
    while gx < x1 - 18:
        draw.line((gx, y0 + 18, gx, y1 - 18), fill=(188, 203, 223), width=1)
        gx += 72
    gy = y0 + 18
    while gy < y1 - 18:
        draw.line((x0 + 18, gy, x1 - 18, gy), fill=(188, 203, 223), width=1)
        gy += 72

    if mode == "empty":
        draw.text(((x0 + x1) // 2, (y0 + y1) // 2 - 8), "No character selected", anchor="mm", font=FONT_BODY, fill=PALETTE["text_muted"])
        draw.text(((x0 + x1) // 2, (y0 + y1) // 2 + 18), "Choose a hero to edit an offline build.", anchor="mm", font=FONT_XS, fill=PALETTE["text_muted"])
        return

    nodes = {
        "Core": (x0 + 255, y0 + 305, PALETTE["graph_node"]),
        "Resolve": (x0 + 165, y0 + 305, PALETTE["graph_node"]),
        "Vitality": (x0 + 220, y0 + 385, PALETTE["graph_node"]),
        "Dexterity": (x0 + 255, y0 + 220, PALETTE["graph_node"]),
        "Willpower": (x0 + 345, y0 + 250, PALETTE["graph_node"]),
        "Agility": (x0 + 345, y0 + 385, PALETTE["graph_node"]),
        "Quick Strike": (x0 + 65, y0 + 270, PALETTE["graph_active"]),
        "Bandage": (x0 + 305, y0 + 140, PALETTE["graph_special"]),
        "Ember": (x0 + 525, y0 + 335, PALETTE["graph_special"]),
    }
    edges = [
        ("Core", "Resolve"),
        ("Core", "Vitality"),
        ("Core", "Dexterity"),
        ("Core", "Willpower"),
        ("Core", "Agility"),
        ("Resolve", "Quick Strike"),
        ("Dexterity", "Bandage"),
        ("Agility", "Ember"),
    ]
    for a, b in edges:
        ax, ay, _ = nodes[a]
        bx, by, _ = nodes[b]
        draw.line((ax, ay, bx, by), fill=(140, 162, 191), width=3)

    for name, (nx, ny, col) in nodes.items():
        draw_col = col
        if mode == "create" and name in {"Quick Strike", "Bandage", "Ember"}:
            draw_col = (203, 213, 228)
        r = 11 if name == "Core" else 10
        draw.ellipse((nx - r, ny - r, nx + r, ny + r), fill=draw_col, outline=(120, 140, 168), width=1)
        draw.text((nx, ny + 18), name, anchor="mm", font=FONT_XS, fill=PALETTE["text_soft"])

    if mode == "create":
        draw.text((x0 + 22, y0 + 22), "Archetype Start: Core -> Resolve", font=FONT_XS, fill=PALETTE["success"])


def draw_char_list(draw: ImageDraw.ImageDraw, rect, include_selected: bool):
    x0, y0, x1, y1 = rect
    rr(draw, rect, PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    draw.text((x0 + 18, y0 + 18), "Characters", font=FONT_H, fill=PALETTE["text"])
    button(draw, (x0 + 18, y0 + 50, x1 - 18, y0 + 84), "Create Character")

    list_box = (x0 + 18, y0 + 96, x1 - 18, y1 - 18)
    rr(draw, list_box, PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)

    if include_selected:
        rr(draw, (list_box[0] + 10, list_box[1] + 10, list_box[2] - 10, list_box[1] + 58), PALETTE["primary"], r=4, outline=PALETTE["border_soft"], w=1)
        draw.text((list_box[0] + 22, list_box[1] + 24), "Sellsword", font=FONT_SM, fill=PALETTE["primary_text"])
        draw.text((list_box[0] + 22, list_box[1] + 42), "Lv 5 | Ironhold", font=FONT_XS, fill=PALETTE["primary_text"])
        rr(draw, (list_box[0] + 10, list_box[1] + 66, list_box[2] - 10, list_box[1] + 114), PALETTE["panel_alt"], r=4, outline=PALETTE["border_soft"], w=1)
        draw.text((list_box[0] + 22, list_box[1] + 80), "Scout", font=FONT_SM, fill=PALETTE["text"])
        draw.text((list_box[0] + 22, list_box[1] + 98), "Lv 2 | Khar Grotto", font=FONT_XS, fill=PALETTE["text_muted"])
        # More visible list capacity.
        for i in range(3):
            row_y = list_box[1] + 122 + i * 48
            rr(draw, (list_box[0] + 10, row_y, list_box[2] - 10, row_y + 40), PALETTE["panel"], r=4, outline=PALETTE["border_soft"], w=1)
            draw.text((list_box[0] + 22, row_y + 14), f"Empty Slot {i + 1}", font=FONT_XS, fill=PALETTE["text_muted"])
    else:
        tbox(draw, (list_box[0] + 18, list_box[1] + 20), "No characters yet. Create a hero to start building your path.", FONT_SM, PALETTE["text_muted"], (list_box[2] - list_box[0]) - 36, max_lines=5)


# Option 1: Atlas Workspace

def atlas_login() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], 0)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (210, 170, 860, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (878, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((232, 198), "Account Access", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (232, 236, 838, 270), "Email", "admin@admin.com")
    input_box(d, (232, 280, 838, 314), "Password")
    input_box(d, (232, 324, 838, 358), "MFA Code (optional)")
    button(d, (232, 376, 838, 412), "Login", primary=True)
    d.text((232, 666), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
    d.text((830, 666), "MFA available in Security settings", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((900, 198), "Update Center", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (900, 232), "Latest patch summary is shown here directly next to login.\n\nNo extra auth-sidebar update button needed.", FONT_SM, PALETTE["text_soft"], 392, max_lines=8)
    rr(d, (900, 312, 1292, 610), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((918, 332), "Build: v1.0.157", font=FONT_XS, fill=PALETTE["text"])
    tbox(d, (918, 360), "- Graph available in selection + creation.\n- Pre-launch Save Build enabled.\n- Cleaner roster capacity in Dual Pane v2.", FONT_XS, PALETTE["text_soft"], 356, max_lines=8)
    button(d, (900, 632, 1292, 668), "Check for Update")
    return img


def atlas_register() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], 1)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (210, 170, 860, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (878, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((232, 198), "Create Account", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (232, 236, 838, 270), "Display Name")
    input_box(d, (232, 280, 838, 314), "Email")
    input_box(d, (232, 324, 838, 358), "Password")
    button(d, (232, 376, 838, 412), "Register", primary=True)

    d.text((900, 198), "New Player Flow", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (900, 232), "1. Register\n2. Select/Create character\n3. Configure build offline\n4. Launch", FONT_SM, PALETTE["text_soft"], 392, max_lines=8)
    button(d, (900, 632, 1292, 668), "Back to Login")
    return img


def atlas_play(selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    draw_char_list(d, (210, 170, 470, 702), include_selected=selected)

    rr(d, (484, 170, 1132, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((502, 198), "Build Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (502, 226, 1112, 620), "selected" if selected else "empty")
    if selected:
        button(d, (502, 638, 792, 674), "Save Build (Offline)", primary=True)
        d.text((804, 648), "Stored now; gold cost can apply on in-game commit.", font=FONT_XS, fill=PALETTE["text_muted"])

    rr(d, (1146, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1160, 198), "Details", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (1160, 232), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold", FONT_SM, PALETTE["text_soft"], 144, max_lines=8)
        button(d, (1160, 640, 1232, 676), "Play", primary=True)
        button(d, (1236, 640, 1308, 676), "Delete")
    else:
        tbox(d, (1160, 232), "Select a character to enable graph editing and launch.", FONT_SM, PALETTE["text_muted"], 144, max_lines=7)
    return img


def atlas_create() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)

    rr(d, (210, 170, 480, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((230, 198), "Identity", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (230, 236, 460, 270), "Character Name")
    input_box(d, (230, 280, 460, 314), "Character Type", "Sellsword")
    input_box(d, (230, 324, 460, 358), "Sex", "Male")
    tbox(d, (230, 396), "Sellsword starts at Core and can branch into Resolve, Dexterity, or Vitality.", FONT_SM, PALETTE["text_soft"], 220, max_lines=8)
    button(d, (230, 640, 460, 676), "Create Character", primary=True)

    rr(d, (494, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((514, 198), "Archetype Starting Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (514, 226, 1296, 676), "create")
    return img


def atlas_update() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], None)

    rr(d, (286, 154, 1120, 628), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (312, 188, 1092, 228), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((330, 200), "Build: v1.0.157", font=FONT_SM, fill=PALETTE["text"])
    rr(d, (312, 240, 1092, 544), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((330, 262), "Release Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (330, 298), "- Atlas keeps graph visible in both selection and creation.\n- Save Build can happen pre-launch.\n- Update remains adjacent to login flow.", FONT_SM, PALETTE["text_soft"], 742, max_lines=10)
    button(d, (312, 556, 1092, 594), "Back to Login", primary=True)
    return img


def atlas_settings() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 2)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    d.text((210, 160), "Settings", font=FONT_H, fill=PALETTE["text"])
    button(d, (210, 192, 300, 226), "Video")
    button(d, (306, 192, 396, 226), "Audio", primary=True)
    button(d, (402, 192, 492, 226), "Security")

    rr(d, (210, 240, 1316, 710), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((232, 262), "Audio Mix", font=FONT_H, fill=PALETTE["text"])
    labels = ["Master", "Music", "Effects", "Interface"]
    vals = [78, 62, 84, 55]
    y = 312
    for k, v in zip(labels, vals):
        d.text((232, y - 20), k, font=FONT_SM, fill=PALETTE["text_soft"])
        rr(d, (232, y, 1008, y + 12), (205, 218, 236), r=4)
        fill_w = int((1008 - 232) * (v / 100))
        rr(d, (232, y, 232 + fill_w, y + 12), PALETTE["primary"], r=4)
        y += 74
    button(d, (1120, 660, 1288, 696), "Apply", primary=True)
    return img


# Option 2: Dual-Pane Studio

def dual_login() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], 0)

    rr(d, (196, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (220, 170, 770, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (784, 170, 1316, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((242, 198), "Login", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (242, 236, 748, 270), "Email", "admin@admin.com")
    input_box(d, (242, 280, 748, 314), "Password")
    input_box(d, (242, 324, 748, 358), "MFA Code (optional)")
    button(d, (242, 376, 748, 412), "Login", primary=True)
    d.text((242, 660), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
    d.text((740, 660), "MFA available in Security settings", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((806, 198), "Update Snapshot", font=FONT_H, fill=PALETTE["text"])
    rr(d, (806, 236, 1292, 610), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((824, 256), "Build: v1.0.157", font=FONT_XS, fill=PALETTE["text"])
    tbox(d, (824, 282), "- Selection + creation both include graph context.\n- Offline Save Build path remains available before launch.", FONT_XS, PALETTE["text_soft"], 450, max_lines=8)
    button(d, (806, 646, 1292, 682), "Check for Update")
    return img


def dual_register() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], 1)

    rr(d, (196, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (220, 170, 770, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (784, 170, 1316, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((242, 198), "Create Account", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (242, 236, 748, 270), "Display Name")
    input_box(d, (242, 280, 748, 314), "Email")
    input_box(d, (242, 324, 748, 358), "Password")
    button(d, (242, 376, 748, 412), "Register", primary=True)

    d.text((806, 198), "New Player Prep", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (806, 232), "Registration feeds directly into character creation where graph start routes are explained per archetype.", FONT_SM, PALETTE["text_soft"], 492, max_lines=8)
    button(d, (806, 646, 1292, 682), "Back to Login")
    return img


def dual_play(selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)

    rr(d, (196, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)

    # Widened roster column for real list capacity.
    draw_char_list(d, (220, 170, 550, 702), include_selected=selected)

    rr(d, (564, 170, 1088, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((584, 198), "Build Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (584, 226, 1068, 620), "selected" if selected else "empty")

    rr(d, (584, 638, 1068, 674), PALETTE["panel"], r=4, outline=PALETTE["border_soft"], w=1)
    if selected:
        button(d, (592, 640, 772, 672), "Save Build", primary=True)
        d.text((780, 648), "Saved offline before gameplay launch.", font=FONT_XS, fill=PALETTE["text_muted"])

    rr(d, (1102, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1118, 198), "Character Details", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (1118, 232), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold\nFacing: East", FONT_SM, PALETTE["text_soft"], 178, max_lines=9)
        button(d, (1118, 640, 1210, 676), "Play", primary=True)
        button(d, (1214, 640, 1308, 676), "Delete")
    else:
        tbox(d, (1118, 232), "Pick a character to inspect details and edit build paths.", FONT_SM, PALETTE["text_muted"], 178, max_lines=7)
    return img


def dual_create() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1)

    rr(d, (196, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (220, 170, 560, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (574, 170, 1316, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((242, 198), "Identity", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (242, 236, 538, 270), "Character Name")
    input_box(d, (242, 280, 538, 314), "Character Type", "Sellsword")
    input_box(d, (242, 324, 538, 358), "Sex", "Male")
    tbox(d, (242, 396), "Sellsword starts at Core and can branch early into Resolve, Dexterity, or Vitality lines.", FONT_SM, PALETTE["text_soft"], 292, max_lines=8)
    button(d, (242, 640, 538, 676), "Create Character", primary=True)

    d.text((596, 198), "Starting Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (596, 226, 1294, 676), "create")
    return img


def dual_update() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], None)

    rr(d, (286, 154, 1120, 628), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (312, 188, 1092, 228), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((330, 200), "Build: v1.0.157", font=FONT_SM, fill=PALETTE["text"])
    rr(d, (312, 240, 1092, 544), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((330, 262), "Release Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (330, 298), "- Dual pane now gives much more room to character roster.\n- Graph stays visible in both selection and creation.\n- Save Build remains a pre-launch action.", FONT_SM, PALETTE["text_soft"], 742, max_lines=10)
    button(d, (312, 556, 1092, 594), "Back to Login", primary=True)
    return img


def dual_settings() -> Image.Image:
    return atlas_settings()


# Option 3: Command Palette (fully restyled)

def cmd_login() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], 0, x=24, y=178, h=400)

    rr(d, (204, 128, 1162, 170), PALETTE["panel"], r=8, outline=PALETTE["border_soft"], w=1)
    d.text((224, 142), "Command Palette: Ctrl+K for quick actions", font=FONT_XS, fill=PALETTE["text_muted"])
    button(d, (980, 134, 1088, 162), "Palette")
    button(d, (1096, 134, 1146, 162), "?")

    rr(d, (204, 188, 1162, 700), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (228, 218, 748, 676), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (766, 218, 1138, 676), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((248, 246), "Account Access", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (248, 284, 726, 318), "Email", "admin@admin.com")
    input_box(d, (248, 328, 726, 362), "Password")
    input_box(d, (248, 372, 726, 406), "MFA Code (optional)")
    button(d, (248, 424, 726, 460), "Login", primary=True)
    d.text((248, 648), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
    d.text((718, 648), "MFA available in Security settings", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((786, 246), "Quick Actions", font=FONT_H, fill=PALETTE["text"])
    rr(d, (786, 284, 1118, 392), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    tbox(d, (800, 302), "login\nregister\nopen update\nopen settings", FONT_SM, PALETTE["text_soft"], 300, max_lines=8)
    rr(d, (786, 408, 1118, 620), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((800, 428), "Update", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (800, 456), "Build: v1.0.157\nPatch notes and check action live beside login.", FONT_XS, PALETTE["text_soft"], 300, max_lines=6)
    button(d, (786, 632, 1118, 668), "Check for Update")
    return img


def cmd_register() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], 1, x=24, y=178, h=400)

    rr(d, (204, 128, 1162, 170), PALETTE["panel"], r=8, outline=PALETTE["border_soft"], w=1)
    d.text((224, 142), "Command Palette: Ctrl+K for quick actions", font=FONT_XS, fill=PALETTE["text_muted"])

    rr(d, (204, 188, 1162, 700), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (228, 218, 748, 676), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (766, 218, 1138, 676), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((248, 246), "Create Account", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (248, 284, 726, 318), "Display Name")
    input_box(d, (248, 328, 726, 362), "Email")
    input_box(d, (248, 372, 726, 406), "Password")
    button(d, (248, 424, 726, 460), "Register", primary=True)

    d.text((786, 246), "Onboarding", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (800, 284), "After registration:\n1. Create character\n2. Review start graph\n3. Save starter build\n4. Launch", FONT_SM, PALETTE["text_soft"], 300, max_lines=9)
    button(d, (786, 632, 1118, 668), "Back to Login")
    return img


def cmd_play(selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0, x=24, y=178, h=400)

    rr(d, (204, 128, 1162, 170), PALETTE["panel"], r=8, outline=PALETTE["border_soft"], w=1)
    d.text((224, 142), "Command Palette: Ctrl+K for quick actions", font=FONT_XS, fill=PALETTE["text_muted"])
    button(d, (980, 134, 1088, 162), "Palette")
    button(d, (1096, 134, 1146, 162), "Help")

    rr(d, (184, 176, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)

    # Better structured than previous tiny floating widgets.
    draw_char_list(d, (204, 202, 470, 716), include_selected=selected)

    rr(d, (484, 202, 1118, 676), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((504, 224), "Graph Canvas", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (504, 252, 1098, 652), "selected" if selected else "empty")

    rr(d, (1132, 202, 1316, 676), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1148, 224), "Inspector", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (1148, 252), "Core\n+2 base stats\n\nRoutes:\nResolve\nDexterity\nVitality", FONT_SM, PALETTE["text_soft"], 154, max_lines=10)
        button(d, (1148, 624, 1300, 660), "Save Build", primary=True)

    rr(d, (484, 686, 1118, 718), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    button(d, (492, 688, 660, 716), "Save Build", primary=True)
    button(d, (668, 688, 790, 716), "Reset")
    button(d, (798, 688, 900, 716), "Play")
    d.text((912, 694), "Offline edits are saved before gameplay entry.", font=FONT_XS, fill=PALETTE["text_muted"])
    return img


def cmd_create() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1, x=24, y=178, h=400)

    rr(d, (204, 128, 1162, 170), PALETTE["panel"], r=8, outline=PALETTE["border_soft"], w=1)
    d.text((224, 142), "Command Palette: Ctrl+K for quick actions", font=FONT_XS, fill=PALETTE["text_muted"])

    rr(d, (184, 176, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)

    rr(d, (204, 202, 470, 716), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((222, 224), "Create", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (222, 254, 452, 288), "Character Name")
    input_box(d, (222, 298, 452, 332), "Character Type", "Sellsword")
    input_box(d, (222, 342, 452, 376), "Sex", "Male")
    tbox(d, (222, 408), "Use graph cues to understand starting node and early branch identity.", FONT_SM, PALETTE["text_soft"], 220, max_lines=7)
    button(d, (222, 672, 452, 708), "Create Character", primary=True)

    rr(d, (484, 202, 1118, 716), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((504, 224), "Starting Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (504, 252, 1098, 690), "create")

    rr(d, (1132, 202, 1316, 716), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1148, 224), "Route Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (1148, 252), "Core start.\nRecommended opener:\nCore -> Resolve -> Quick Strike", FONT_SM, PALETTE["text_soft"], 154, max_lines=8)
    button(d, (1148, 672, 1300, 708), "Back to Play")
    return img


def cmd_update() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Quit"], None, x=24, y=178, h=400)

    rr(d, (254, 180, 1260, 640), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (278, 214, 1234, 252), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((296, 226), "Build: v1.0.157", font=FONT_SM, fill=PALETTE["text"])
    rr(d, (278, 264, 1234, 556), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((296, 286), "Release Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (296, 322), "- Command palette option fully restyled with structured panels.\n- Graph present in selection and creation.\n- Save Build before launch remains core path.", FONT_SM, PALETTE["text_soft"], 916, max_lines=10)
    button(d, (278, 570, 1234, 608), "Back to Login", primary=True)
    return img


def cmd_settings() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 2, x=24, y=178, h=400)

    rr(d, (184, 176, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (204, 128, 1162, 170), PALETTE["panel"], r=8, outline=PALETTE["border_soft"], w=1)
    d.text((224, 142), "Command Palette: Ctrl+K for quick actions", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((206, 204), "Settings", font=FONT_H, fill=PALETTE["text"])
    button(d, (206, 236, 296, 270), "Video")
    button(d, (302, 236, 392, 270), "Audio")
    button(d, (398, 236, 488, 270), "Security", primary=True)

    rr(d, (206, 286, 1316, 704), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((228, 310), "Security", font=FONT_H, fill=PALETTE["text"])
    button(d, (1010, 304, 1118, 338), "MFA: ON", primary=True)
    button(d, (1128, 304, 1218, 338), "Refresh")
    button(d, (1226, 304, 1304, 338), "Copy URI")
    rr(d, (228, 346, 702, 670), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    rr(d, (720, 346, 1304, 670), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    tbox(d, (740, 370), "MFA active.\nSecret and URI are available for authenticator setup.", FONT_SM, PALETTE["text_soft"], 544, max_lines=8)
    return img


def make_contact_sheet(images: list[tuple[str, Image.Image]]) -> Image.Image:
    cols = 3
    rows = (len(images) + cols - 1) // cols
    tw, th = 420, 236
    pad = 18
    lh = 24
    out = Image.new("RGBA", (cols * tw + (cols + 1) * pad, rows * (th + lh) + (rows + 1) * pad), PALETTE["bg"] + (255,))
    d = ImageDraw.Draw(out, "RGBA")

    for i, (name, img) in enumerate(images):
        row, col = divmod(i, cols)
        x = pad + col * tw
        y = pad + row * (th + lh)
        rr(d, (x, y, x + tw, y + th), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
        thumb = img.convert("RGB").resize((tw - 12, th - 12), Image.Resampling.BICUBIC)
        out.paste(thumb, (x + 6, y + 6))
        d.text((x, y + th + 4), name, font=FONT_XS, fill=PALETTE["text"])
    return out


def generate_option(folder: Path, prefix: str, screens: list[tuple[str, Callable[[], Image.Image]]]):
    folder.mkdir(parents=True, exist_ok=True)
    rendered: list[tuple[str, Image.Image]] = []
    for short_name, fn in screens:
        img = fn()
        file_name = f"{prefix}_{short_name}.png"
        img.convert("RGB").save(folder / file_name, "PNG", optimize=True)
        rendered.append((file_name, img))
        print(folder / file_name)

    sheet = make_contact_sheet(rendered)
    sheet_name = f"{prefix}_contact_sheet.png"
    sheet.convert("RGB").save(folder / sheet_name, "PNG", optimize=True)
    print(folder / sheet_name)


def main() -> None:
    atlas_dir = OUT_ROOT / "option_atlas_workspace"
    dual_dir = OUT_ROOT / "option_dual_pane_studio"
    cmd_dir = OUT_ROOT / "option_command_palette"

    generate_option(
        atlas_dir,
        "atlas",
        [
            ("login", atlas_login),
            ("register", atlas_register),
            ("play_empty", lambda: atlas_play(False)),
            ("play_selected", lambda: atlas_play(True)),
            ("create", atlas_create),
            ("update", atlas_update),
            ("settings", atlas_settings),
        ],
    )

    generate_option(
        dual_dir,
        "dual",
        [
            ("login", dual_login),
            ("register", dual_register),
            ("play_empty", lambda: dual_play(False)),
            ("play_selected", lambda: dual_play(True)),
            ("create", dual_create),
            ("update", dual_update),
            ("settings", dual_settings),
        ],
    )

    generate_option(
        cmd_dir,
        "cmd",
        [
            ("login", cmd_login),
            ("register", cmd_register),
            ("play_empty", lambda: cmd_play(False)),
            ("play_selected", lambda: cmd_play(True)),
            ("create", cmd_create),
            ("update", cmd_update),
            ("settings", cmd_settings),
        ],
    )


if __name__ == "__main__":
    main()
