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

    # Shared node map.
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

    for name, (nx, ny, c) in nodes.items():
        color = c
        if mode == "create" and name in {"Quick Strike", "Bandage", "Ember"}:
            color = (203, 213, 228)
        r = 11 if name == "Core" else 10
        draw.ellipse((nx - r, ny - r, nx + r, ny + r), fill=color, outline=(120, 140, 168), width=1)
        draw.text((nx, ny + 18), name, anchor="mm", font=FONT_XS, fill=PALETTE["text_soft"])

    if mode == "create":
        draw.text((x0 + 24, y0 + 24), "Archetype Start: Core -> Resolve", font=FONT_XS, fill=PALETTE["success"])


def sidebar(draw: ImageDraw.ImageDraw, items: list[str], active: int, x=24, y=156, h=444):
    rr(draw, (x, y, x + 136, y + h), PALETTE["panel_alt"], r=8, outline=PALETTE["border"], w=1)
    by = y + 90
    for i, item in enumerate(items):
        button(draw, (x + 16, by + i * 44, x + 120, by + i * 44 + 34), item, primary=(i == active))


def atlas_login() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Update", "Quit"], 0)

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

    d.text((900, 198), "Atlas Workspace", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (900, 232), "Graph remains visible in character selection and creation.\n\nSelection supports offline build edits with explicit Save Build action before entering gameplay.", FONT_SM, PALETTE["text_soft"], 392, max_lines=12)
    button(d, (900, 632, 1292, 668), "Open Update Center")
    return img


def atlas_play(selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)

    rr(d, (210, 170, 412, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((230, 198), "Characters", font=FONT_H, fill=PALETTE["text"])
    button(d, (230, 232, 392, 266), "Create Character", primary=not selected)
    if selected:
        rr(d, (230, 286, 392, 336), PALETTE["primary"], r=5, outline=PALETTE["border_soft"], w=1)
        d.text((242, 300), "Sellsword", font=FONT_SM, fill=PALETTE["primary_text"])
        d.text((242, 320), "Lv 5 | Ironhold", font=FONT_XS, fill=PALETTE["primary_text"])
    else:
        tbox(d, (230, 286), "No characters yet.", FONT_SM, PALETTE["text_muted"], 150, max_lines=2)

    rr(d, (426, 170, 1118, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((446, 198), "Build Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (446, 226, 1098, 620), "selected" if selected else "empty")

    if selected:
        button(d, (446, 638, 736, 674), "Save Build (Offline)", primary=True)
        d.text((748, 648), "Stored now; gold cost can apply on in-game commit.", font=FONT_XS, fill=PALETTE["text_muted"])

    rr(d, (1132, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1148, 198), "Character Details", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (1148, 232), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold", FONT_SM, PALETTE["text_soft"], 152, max_lines=7)
        button(d, (1148, 640, 1230, 676), "Play", primary=True)
        button(d, (1234, 640, 1310, 676), "Delete")
    else:
        tbox(d, (1148, 232), "Select a character to enable build editing and launch actions.", FONT_SM, PALETTE["text_muted"], 152, max_lines=8)
        button(d, (1148, 640, 1230, 676), "Play")
        button(d, (1234, 640, 1310, 676), "Delete")
    return img


def atlas_create() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1)

    rr(d, (186, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (210, 170, 412, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((230, 198), "Archetypes", font=FONT_H, fill=PALETTE["text"])
    rr(d, (230, 232, 392, 286), PALETTE["primary"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((242, 246), "Sellsword", font=FONT_SM, fill=PALETTE["primary_text"])
    d.text((242, 266), "Melee baseline", font=FONT_XS, fill=PALETTE["primary_text"])

    rr(d, (426, 170, 1118, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((446, 198), "Archetype Graph Start", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (446, 226, 1098, 620), "create")

    rr(d, (1132, 170, 1316, 702), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1148, 198), "Identity", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (1148, 232, 1310, 266), "Character Name")
    input_box(d, (1148, 276, 1310, 310), "Character Type", "Sellsword")
    input_box(d, (1148, 320, 1310, 354), "Sex", "Male")
    tbox(d, (1148, 388), "Start node: Core\nFirst branches: Resolve, Dexterity, Vitality.", FONT_SM, PALETTE["text_soft"], 152, max_lines=7)
    button(d, (1148, 640, 1310, 676), "Create Character", primary=True)
    return img


def atlas_update() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Update", "Quit"], 2)

    rr(d, (286, 154, 1120, 628), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (312, 188, 1092, 228), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((330, 200), "Build: v1.0.157", font=FONT_SM, fill=PALETTE["text"])

    rr(d, (312, 240, 1092, 544), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((330, 262), "Release Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (330, 298), "- Atlas lobby keeps graph available for both selection and creation.\n- Save Build action persists pre-launch edits.\n- UI structure trims friction between roster, graph, and launch paths.", FONT_SM, PALETTE["text_soft"], 742, max_lines=10)
    button(d, (312, 556, 1092, 594), "Check for Update", primary=True)
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
    sidebar(d, ["Login", "Register", "Update", "Quit"], 0)

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

    d.text((806, 198), "Release Snapshot", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (806, 232), "Dual-pane layout separates account actions from update/notes context for cleaner scanning.", FONT_SM, PALETTE["text_soft"], 492, max_lines=10)
    button(d, (806, 646, 1292, 682), "Check for Update")
    return img


def dual_play(selected: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)

    rr(d, (196, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)

    # Left pane = roster + details stack
    rr(d, (220, 170, 580, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((242, 198), "Characters", font=FONT_H, fill=PALETTE["text"])
    button(d, (242, 232, 558, 266), "Create Character", primary=not selected)
    if selected:
        rr(d, (242, 286, 558, 336), PALETTE["primary"], r=5, outline=PALETTE["border_soft"], w=1)
        d.text((256, 300), "Sellsword", font=FONT_SM, fill=PALETTE["primary_text"])
        d.text((256, 320), "Lv 5 | Ironhold", font=FONT_XS, fill=PALETTE["primary_text"])
    else:
        tbox(d, (242, 286), "No characters yet.", FONT_SM, PALETTE["text_muted"], 310, max_lines=2)

    rr(d, (242, 356, 558, 678), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((256, 374), "Character Details", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (256, 406), "Class: Mercenary\nZone: Ironhold\nFacing: East", FONT_SM, PALETTE["text_soft"], 282, max_lines=6)
        button(d, (256, 630, 406, 666), "Play", primary=True)
        button(d, (414, 630, 544, 666), "Delete")

    # Right pane = graph + inspector
    rr(d, (594, 170, 1316, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((616, 198), "Build Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (616, 226, 1166, 664), "selected" if selected else "empty")

    rr(d, (1178, 226, 1298, 664), PALETTE["panel"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((1188, 244), "Node", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (1188, 276), "Core\n+2 to all base stats\n\nNext: Resolve, Dexterity, Vitality", FONT_XS, PALETTE["text_soft"], 100, max_lines=12)
        button(d, (1188, 620, 1288, 654), "Save Build", primary=True)
    return img


def dual_create() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1)

    rr(d, (196, 132, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (220, 170, 580, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    rr(d, (594, 170, 1316, 700), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)

    d.text((242, 198), "Identity", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (242, 236, 558, 270), "Character Name")
    input_box(d, (242, 280, 558, 314), "Character Type", "Sellsword")
    input_box(d, (242, 324, 558, 358), "Sex", "Male")
    tbox(d, (242, 396), "Sellsword starts at Core and can branch early into Resolve, Dexterity, or Vitality lines.", FONT_SM, PALETTE["text_soft"], 312, max_lines=8)
    button(d, (242, 630, 558, 666), "Create Character", primary=True)

    d.text((616, 198), "Starting Graph", font=FONT_H, fill=PALETTE["text"])
    draw_graph(d, (616, 226, 1294, 664), "create")
    return img


def dual_update() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Update", "Quit"], 2)

    rr(d, (286, 154, 1120, 628), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (312, 188, 1092, 228), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((330, 200), "Build: v1.0.157", font=FONT_SM, fill=PALETTE["text"])
    rr(d, (312, 240, 1092, 544), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((330, 262), "Release Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (330, 298), "- Dual-pane mode: roster/actions left, graph+inspector right.\n- Selection and creation both expose graph context.\n- Offline build save available before entering gameplay.", FONT_SM, PALETTE["text_soft"], 742, max_lines=10)
    button(d, (312, 556, 1092, 594), "Check for Update", primary=True)
    return img


def dual_settings() -> Image.Image:
    img = atlas_settings()
    return img


# Option 3: Command-Palette UI

def cmd_base(active: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Play", "Create", "Settings", "Update", "Log Out", "Quit"], active, x=24, y=178, h=400)

    # Central command strip.
    rr(d, (214, 122, 1170, 162), PALETTE["panel"], r=8, outline=PALETTE["border_soft"], w=1)
    d.text((236, 136), "Command: type action or press Ctrl+K", font=FONT_XS, fill=PALETTE["text_muted"])
    button(d, (952, 128, 1062, 156), "Open Palette")
    button(d, (1070, 128, 1158, 156), "Help")
    return img, d


def cmd_login() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Update", "Quit"], 0, x=24, y=178, h=400)

    rr(d, (254, 196, 824, 560), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (842, 196, 1256, 560), PALETTE["panel_alt"], r=10, outline=PALETTE["border_soft"], w=1)

    d.text((276, 224), "Account Access", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (276, 262, 802, 296), "Email", "admin@admin.com")
    input_box(d, (276, 306, 802, 340), "Password")
    input_box(d, (276, 350, 802, 384), "MFA Code (optional)")
    button(d, (276, 402, 802, 438), "Login", primary=True)
    d.text((276, 516), "Client version: v1.0.157", font=FONT_XS, fill=PALETTE["text_muted"])
    d.text((794, 516), "MFA available in Security settings", anchor="ra", font=FONT_XS, fill=PALETTE["text_muted"])

    d.text((862, 224), "Quick Commands", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (862, 260), "login\nregister\nopen update\ncheck notes", FONT_SM, PALETTE["text_soft"], 374, max_lines=9)
    return img


def cmd_play(selected: bool) -> Image.Image:
    img, d = cmd_base(0)

    rr(d, (184, 176, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    draw_graph(d, (264, 236, 1110, 686), "selected" if selected else "empty")

    # floating roster panel
    rr(d, (204, 216, 248, 520), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((216, 236), "Roster", font=FONT_H, fill=PALETTE["text"])
    button(d, (216, 266, 236, 300), "+", primary=True)
    if selected:
        rr(d, (216, 312, 236, 362), PALETTE["primary"], r=5, outline=PALETTE["border_soft"], w=1)
        d.text((220, 324), "S", font=FONT_SM, fill=PALETTE["primary_text"])
    # node inspector
    rr(d, (1124, 216, 1320, 560), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1140, 236), "Inspector", font=FONT_H, fill=PALETTE["text"])
    if selected:
        tbox(d, (1140, 268), "Core\n+2 base stats\n\nRoute to Resolve\nRoute to Dexterity", FONT_XS, PALETTE["text_soft"], 168, max_lines=10)
        button(d, (1140, 516, 1304, 550), "Save Build", primary=True)

    # action rail bottom
    rr(d, (264, 696, 1110, 726), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    button(d, (272, 698, 432, 724), "Save Build", primary=True)
    button(d, (440, 698, 574, 724), "Reset")
    button(d, (582, 698, 708, 724), "Play")
    d.text((722, 705), "Offline edits are saved before gameplay entry.", font=FONT_XS, fill=PALETTE["text_muted"])
    return img


def cmd_create() -> Image.Image:
    img, d = cmd_base(1)

    rr(d, (184, 176, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    draw_graph(d, (264, 236, 1110, 686), "create")

    rr(d, (204, 216, 248, 520), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((216, 236), "Create", font=FONT_H, fill=PALETTE["text"])
    input_box(d, (216, 266, 236, 300), "Name")
    input_box(d, (216, 310, 236, 344), "Class", "Sellsword")
    input_box(d, (216, 354, 236, 388), "Sex", "Male")

    rr(d, (1124, 216, 1320, 560), PALETTE["panel_alt"], r=7, outline=PALETTE["border_soft"], w=1)
    d.text((1140, 236), "Start Route", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (1140, 268), "Starts at Core.\nRecommended early path:\nCore -> Resolve -> Quick Strike", FONT_XS, PALETTE["text_soft"], 168, max_lines=10)

    rr(d, (264, 696, 1110, 726), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    button(d, (272, 698, 466, 724), "Create Character", primary=True)
    button(d, (474, 698, 640, 724), "Back to Play")
    return img


def cmd_update() -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_header(img)
    d = ImageDraw.Draw(img, "RGBA")
    sidebar(d, ["Login", "Register", "Update", "Quit"], 2, x=24, y=178, h=400)

    rr(d, (254, 180, 1260, 640), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
    rr(d, (278, 214, 1234, 252), PALETTE["panel_alt"], r=5, outline=PALETTE["border_soft"], w=1)
    d.text((296, 226), "Build: v1.0.157", font=FONT_SM, fill=PALETTE["text"])
    rr(d, (278, 264, 1234, 556), PALETTE["panel_alt"], r=6, outline=PALETTE["border_soft"], w=1)
    d.text((296, 286), "Release Notes", font=FONT_H, fill=PALETTE["text"])
    tbox(d, (296, 322), "- Command-palette UX supports power users while keeping core actions visible.\n- Graph editing remains available in both selection and creation.\n- Build save can happen before entering gameplay session.", FONT_SM, PALETTE["text_soft"], 916, max_lines=10)
    button(d, (278, 570, 1234, 608), "Check for Update", primary=True)
    return img


def cmd_settings() -> Image.Image:
    img, d = cmd_base(2)
    rr(d, (184, 176, 1340, 736), PALETTE["panel"], r=10, outline=PALETTE["border_soft"], w=1)
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


def generate_option(
    folder: Path,
    prefix: str,
    screens: list[tuple[str, Callable[[], Image.Image]]],
):
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
            ("play_empty", lambda: cmd_play(False)),
            ("play_selected", lambda: cmd_play(True)),
            ("create", cmd_create),
            ("update", cmd_update),
            ("settings", cmd_settings),
        ],
    )


if __name__ == "__main__":
    main()
