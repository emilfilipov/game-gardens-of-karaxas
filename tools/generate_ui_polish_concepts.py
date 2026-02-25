#!/usr/bin/env python3
"""Generate UI polish concept mockups for Children of Ikphelion menus."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "concept_art"
W, H = 1366, 768

COLORS = {
    "bg_top": (210, 223, 241),
    "bg_bottom": (188, 206, 231),
    "band": (173, 194, 223, 45),
    "shell": (226, 236, 248, 220),
    "panel": (236, 242, 250, 245),
    "panel_alt": (228, 237, 248, 245),
    "border": (151, 174, 202, 220),
    "border_soft": (170, 188, 212, 180),
    "text": (28, 44, 72),
    "text_soft": (68, 88, 116),
    "text_muted": (95, 112, 138),
    "primary": (82, 138, 210),
    "primary_hover": (101, 155, 224),
    "primary_text": (244, 249, 255),
    "button": (246, 244, 235),
    "button_text": (57, 74, 100),
    "success": (91, 176, 113),
    "warning": (237, 173, 84),
    "danger": (218, 104, 107),
    "graph_node": (99, 150, 217),
    "graph_active": (103, 194, 128),
    "graph_special": (242, 172, 77),
}


def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


FONT_TITLE = _load_font(ROOT / "game-client" / "assets" / "fonts" / "cinzel.ttf", 57)
FONT_SUBTITLE = _load_font(ROOT / "game-client" / "assets" / "fonts" / "cinzel.ttf", 21)
FONT_BODY = _load_font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 27)
FONT_BODY_SM = _load_font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 22)
FONT_BODY_XS = _load_font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 19)
FONT_CAPTION = _load_font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 17)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def rounded(draw: ImageDraw.ImageDraw, rect, fill, radius=10, outline=None, width=1):
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    lines: list[str] = []
    for part in text.split("\n"):
        words = part.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if draw.textlength(candidate, font=font) <= max_w:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_text_box(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, max_w: int, line_h: int | None = None):
    x, y = xy
    lines = wrap_text(draw, text, font, max_w)
    if line_h is None:
        line_h = int(font.size * 1.15) if hasattr(font, "size") else 20
    for idx, line in enumerate(lines):
        draw.text((x, y + idx * line_h), line, font=font, fill=fill)


def draw_background(img: Image.Image):
    draw = ImageDraw.Draw(img, "RGBA")
    for y in range(H):
        t = y / (H - 1)
        c = tuple(lerp(COLORS["bg_top"][i], COLORS["bg_bottom"][i], t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c + (255,))

    # Atmospheric bands for depth.
    rounded(draw, (0, 0, 234, H), COLORS["band"], radius=0)
    rounded(draw, (1135, 0, W, H), COLORS["band"], radius=0)

    # Header area.
    draw.text((W // 2, 44), "Children of Ikphelion", anchor="mm", font=FONT_TITLE, fill=COLORS["text"])
    draw.line([(24, 98), (W - 24, 98)], fill=COLORS["border_soft"], width=1)


def draw_sidebar(img: Image.Image, items: list[str], active: int):
    draw = ImageDraw.Draw(img, "RGBA")
    px, py, pw, ph = 24, 170, 148, 430
    rounded(draw, (px, py, px + pw, py + ph), COLORS["shell"], radius=8, outline=COLORS["border"], width=1)

    # Centered stack.
    btn_w, btn_h, gap = 114, 34, 10
    total_h = len(items) * btn_h + (len(items) - 1) * gap
    start_y = py + (ph - total_h) // 2
    bx = px + (pw - btn_w) // 2

    for idx, item in enumerate(items):
        by = start_y + idx * (btn_h + gap)
        is_active = idx == active
        fill = COLORS["primary"] if is_active else COLORS["button"]
        tfill = COLORS["primary_text"] if is_active else COLORS["button_text"]
        rounded(draw, (bx, by, bx + btn_w, by + btn_h), fill, radius=4, outline=COLORS["border_soft"], width=1)
        draw.text((bx + btn_w // 2, by + btn_h // 2), item, anchor="mm", font=FONT_BODY_XS, fill=tfill)


def draw_shell(img: Image.Image, rect, title: str | None = None):
    draw = ImageDraw.Draw(img, "RGBA")
    rounded(draw, rect, COLORS["shell"], radius=8, outline=COLORS["border_soft"], width=1)
    if title:
        draw.text((rect[0] + 20, rect[1] + 20), title, font=FONT_SUBTITLE, fill=COLORS["text"])


def draw_input(draw: ImageDraw.ImageDraw, rect, placeholder: str, value: str = ""):
    rounded(draw, rect, COLORS["panel_alt"], radius=4, outline=COLORS["border_soft"], width=1)
    text = value if value else placeholder
    fill = COLORS["text"] if value else COLORS["text_muted"]
    draw.text((rect[0] + 10, (rect[1] + rect[3]) // 2), text, anchor="lm", font=FONT_BODY_XS, fill=fill)


def draw_button(draw: ImageDraw.ImageDraw, rect, label: str, primary: bool = False, disabled: bool = False):
    if disabled:
        fill = (190, 199, 212)
        tfill = (225, 232, 243)
    elif primary:
        fill = COLORS["primary"]
        tfill = COLORS["primary_text"]
    else:
        fill = COLORS["button"]
        tfill = COLORS["button_text"]
    rounded(draw, rect, fill, radius=4, outline=COLORS["border_soft"], width=1)
    draw.text(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), label, anchor="mm", font=FONT_BODY_XS, fill=tfill)


def draw_skill_graph(draw: ImageDraw.ImageDraw, rect, populated: bool = True):
    x0, y0, x1, y1 = rect
    rounded(draw, rect, COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)

    # grid
    grid_col = (188, 203, 223)
    gx = x0 + 18
    while gx < x1 - 18:
        draw.line([(gx, y0 + 18), (gx, y1 - 18)], fill=grid_col, width=1)
        gx += 72
    gy = y0 + 18
    while gy < y1 - 18:
        draw.line([(x0 + 18, gy), (x1 - 18, gy)], fill=grid_col, width=1)
        gy += 72

    if not populated:
        draw.text(((x0 + x1) // 2, (y0 + y1) // 2 - 6), "No character selected", anchor="mm", font=FONT_BODY, fill=COLORS["text_muted"])
        draw.text(((x0 + x1) // 2, (y0 + y1) // 2 + 20), "Choose a hero to inspect skill layout.", anchor="mm", font=FONT_CAPTION, fill=COLORS["text_muted"])
        return

    nodes = {
        "Core": (x0 + 255, y0 + 305, COLORS["graph_node"]),
        "Resolve": (x0 + 165, y0 + 305, COLORS["graph_node"]),
        "Vitality": (x0 + 220, y0 + 385, COLORS["graph_node"]),
        "Dexterity": (x0 + 255, y0 + 220, COLORS["graph_node"]),
        "Willpower": (x0 + 345, y0 + 250, COLORS["graph_node"]),
        "Agility": (x0 + 345, y0 + 385, COLORS["graph_node"]),
        "Quick Strike": (x0 + 65, y0 + 270, COLORS["graph_active"]),
        "Bandage": (x0 + 305, y0 + 140, COLORS["graph_special"]),
        "Ember": (x0 + 525, y0 + 335, COLORS["graph_special"]),
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
        draw.line([(ax, ay), (bx, by)], fill=(140, 162, 191), width=3)

    for name, (nx, ny, col) in nodes.items():
        r = 11 if name == "Core" else 10
        draw.ellipse((nx - r, ny - r, nx + r, ny + r), fill=col, outline=(120, 140, 168), width=1)
        draw.text((nx, ny + 18), name, anchor="mm", font=FONT_CAPTION, fill=COLORS["text_soft"])


def base_screen(sidebar_items: list[str], sidebar_active: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw_background(img)
    draw_sidebar(img, sidebar_items, sidebar_active)
    return img


def screen_login() -> Image.Image:
    img = base_screen(["Login", "Register", "Update", "Quit"], 0)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (356, 205, 1010, 560)
    draw_shell(img, shell, "Account Access")

    draw_text_box(draw, (378, 256), "Sign in to continue your journey through Ikphelion.", FONT_BODY_XS, COLORS["text_soft"], 520)

    fields = [
        (378, 292, 818, 326, "Email", "admin@admin.com"),
        (378, 334, 818, 368, "Password", ""),
        (378, 376, 818, 410, "MFA Code (optional)", ""),
    ]
    for x0, y0, x1, y1, ph, val in fields:
        draw_input(draw, (x0, y0, x1, y1), ph, val)

    draw_button(draw, (378, 424, 818, 460), "Login", primary=True)
    draw.text((378, 492), "Client version: v1.0.156", font=FONT_CAPTION, fill=COLORS["text_muted"])
    draw.text((806, 492), "MFA available in Security settings", anchor="ra", font=FONT_CAPTION, fill=COLORS["text_muted"])
    return img


def screen_register() -> Image.Image:
    img = base_screen(["Login", "Register", "Update", "Quit"], 1)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (356, 185, 1010, 575)
    draw_shell(img, shell, "Create Account")

    draw_text_box(draw, (378, 236), "Set up a new account. You can enable MFA after first login.", FONT_BODY_XS, COLORS["text_soft"], 560)
    fields = [
        (378, 274, 818, 308, "Display Name", ""),
        (378, 316, 818, 350, "Email", ""),
        (378, 358, 818, 392, "Password", ""),
    ]
    for x0, y0, x1, y1, ph, val in fields:
        draw_input(draw, (x0, y0, x1, y1), ph, val)
    draw_button(draw, (378, 408, 818, 444), "Register", primary=True)
    draw.text((378, 472), "By creating an account you agree to the service terms.", font=FONT_CAPTION, fill=COLORS["text_muted"])
    return img


def screen_update() -> Image.Image:
    img = base_screen(["Login", "Register", "Update", "Quit"], 2)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (308, 142, 1090, 626)
    draw_shell(img, shell, "Update Center")

    rounded(draw, (332, 188, 700, 230), COLORS["panel_alt"], radius=5, outline=COLORS["border_soft"], width=1)
    draw.text((348, 200), "Installed Build", font=FONT_CAPTION, fill=COLORS["text_muted"])
    draw.text((348, 214), "v1.0.156", font=FONT_BODY_XS, fill=COLORS["text"])

    rounded(draw, (714, 188, 1066, 230), COLORS["panel_alt"], radius=5, outline=COLORS["border_soft"], width=1)
    draw.text((730, 200), "Update Channel", font=FONT_CAPTION, fill=COLORS["text_muted"])
    draw.text((730, 214), "Stable / Live", font=FONT_BODY_XS, fill=COLORS["text"])

    rounded(draw, (332, 246, 1066, 520), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((352, 264), "Release Notes", font=FONT_SUBTITLE, fill=COLORS["text"])

    notes = [
        "Auth/login shell tightened to remove dead panel space.",
        "Fields and controls scaled for denser, cleaner interactions.",
        "Status messaging is contextual; no permanent empty status row.",
        "Sidebar-focused navigation remains the primary control model.",
    ]
    y = 300
    for note in notes:
        draw.text((360, y), f"- {note}", font=FONT_BODY_XS, fill=COLORS["text_soft"])
        y += 34

    draw_button(draw, (332, 532, 720, 570), "Check for Update", primary=True)
    draw_button(draw, (730, 532, 1066, 570), "View Logs")
    return img


def draw_play_layout(img: Image.Image, selected: bool):
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (160, 116, 1340, 746)
    draw_shell(img, shell, "Character Hub")

    # Roster
    rounded(draw, (176, 154, 370, 726), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((192, 172), "Characters", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw_button(draw, (190, 202, 356, 236), "Create Character", primary=not selected)

    if selected:
        rounded(draw, (190, 250, 356, 296), COLORS["primary"], radius=4, outline=COLORS["border_soft"], width=1)
        draw.text((204, 262), "Sellsword", font=FONT_BODY_XS, fill=COLORS["primary_text"])
        draw.text((204, 280), "Level 5  |  Ironhold", font=FONT_CAPTION, fill=COLORS["primary_text"])
        rounded(draw, (190, 304, 356, 350), COLORS["panel_alt"], radius=4, outline=COLORS["border_soft"], width=1)
        draw.text((204, 316), "Scout", font=FONT_BODY_XS, fill=COLORS["text"])
        draw.text((204, 334), "Level 2  |  Khar Grotto", font=FONT_CAPTION, fill=COLORS["text_muted"])
    else:
        draw_text_box(draw, (192, 258), "No characters yet. Create your first hero to begin.", FONT_BODY_XS, COLORS["text_muted"], 156)

    # Graph area
    rounded(draw, (384, 154, 1120, 726), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((402, 172), "Skill Tree", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw_skill_graph(draw, (402, 198, 1102, 706), populated=selected)

    # Details
    rounded(draw, (1134, 154, 1324, 726), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((1148, 172), "Character Details", font=FONT_SUBTITLE, fill=COLORS["text"])
    if selected:
        info = "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold\nFacing: East"
        draw_text_box(draw, (1148, 206), info, FONT_BODY_XS, COLORS["text_soft"], 156)
        draw.text((1148, 380), "Spawn Override (Admin)", font=FONT_CAPTION, fill=COLORS["text_muted"])
        draw_input(draw, (1148, 398, 1310, 430), "Current location", "Current location")
        draw_button(draw, (1148, 680, 1230, 714), "Play", primary=True)
        draw_button(draw, (1234, 680, 1310, 714), "Delete")
    else:
        draw_text_box(draw, (1148, 206), "Select a character to inspect details and launch gameplay.", FONT_BODY_XS, COLORS["text_muted"], 154)
        draw_button(draw, (1148, 680, 1230, 714), "Play", disabled=True)
        draw_button(draw, (1234, 680, 1310, 714), "Delete", disabled=True)


def screen_play_empty() -> Image.Image:
    img = base_screen(["Play", "Create", "Settings", "Update", "Logout", "Quit"], 0)
    draw_play_layout(img, selected=False)
    return img


def screen_play_selected() -> Image.Image:
    img = base_screen(["Play", "Create", "Settings", "Update", "Logout", "Quit"], 0)
    draw_play_layout(img, selected=True)
    return img


def screen_create_character() -> Image.Image:
    img = base_screen(["Play", "Create", "Settings", "Update", "Logout", "Quit"], 1)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (160, 116, 1340, 746)
    draw_shell(img, shell, "Create Character")

    rounded(draw, (176, 154, 960, 726), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((194, 172), "Skill Tree Preview", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw_skill_graph(draw, (194, 198, 942, 706), populated=True)

    rounded(draw, (974, 154, 1324, 726), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((992, 172), "Identity", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw_input(draw, (992, 204, 1306, 238), "Character Name")
    draw_input(draw, (992, 246, 1306, 280), "Character Type", "Sellsword")
    draw_input(draw, (992, 288, 1306, 322), "Sex", "Male")

    rounded(draw, (992, 338, 1306, 620), COLORS["panel_alt"], radius=5, outline=COLORS["border_soft"], width=1)
    draw.text((1006, 354), "Character Type Lore", font=FONT_BODY_XS, fill=COLORS["text"])
    lore = (
        "A disciplined sword-for-hire shaped by border wars. "
        "Reliable in melee, durable under pressure, and ideal for players "
        "who want a direct entry into combat pacing."
    )
    draw_text_box(draw, (1006, 386), lore, FONT_BODY_XS, COLORS["text_soft"], 286)

    draw_button(draw, (992, 640, 1306, 676), "Create Character", primary=True)
    draw_button(draw, (992, 682, 1306, 716), "Back to Play")
    return img


def draw_settings_header(draw: ImageDraw.ImageDraw, shell):
    x0, y0, x1, y1 = shell
    tabs = ["Video", "Audio", "Security"]
    for idx, tab in enumerate(tabs):
        tx0 = x0 + 24 + idx * 96
        rect = (tx0, y0 + 42, tx0 + 88, y0 + 74)
        draw_button(draw, rect, tab, primary=False)


def screen_settings_video() -> Image.Image:
    img = base_screen(["Play", "Create", "Settings", "Update", "Logout", "Quit"], 2)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (196, 132, 1304, 726)
    draw_shell(img, shell, "Settings")
    draw_settings_header(draw, shell)

    rounded(draw, (220, 222, 1280, 704), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((242, 244), "Display", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw.text((242, 282), "Screen Mode", font=FONT_BODY_XS, fill=COLORS["text_soft"])
    draw_input(draw, (242, 306, 620, 340), "Screen Mode", "Borderless Fullscreen")
    draw.text((242, 356), "Resolution", font=FONT_BODY_XS, fill=COLORS["text_soft"])
    draw_input(draw, (242, 380, 620, 414), "Resolution", "2560 x 1440")

    draw.text((656, 282), "Rendering", font=FONT_BODY_XS, fill=COLORS["text_soft"])
    draw_input(draw, (656, 306, 1038, 340), "Renderer", "2D Sprite Runtime")
    draw_input(draw, (656, 350, 1038, 384), "VSync", "Enabled")
    draw_button(draw, (1056, 306, 1252, 340), "Apply", primary=True)
    draw_button(draw, (1056, 350, 1252, 384), "Restore Defaults")
    return img


def screen_settings_audio() -> Image.Image:
    img = base_screen(["Play", "Create", "Settings", "Update", "Logout", "Quit"], 2)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (196, 132, 1304, 726)
    draw_shell(img, shell, "Settings")
    draw_settings_header(draw, shell)

    rounded(draw, (220, 222, 1280, 704), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((242, 244), "Audio", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw_button(draw, (242, 282, 540, 316), "Muted: OFF")

    # Sliders
    labels = ["Master", "Music", "Effects", "Interface"]
    values = [78, 62, 84, 55]
    y = 352
    for label, value in zip(labels, values):
        draw.text((242, y - 24), label, font=FONT_BODY_XS, fill=COLORS["text_soft"])
        rounded(draw, (242, y, 1068, y + 12), (205, 218, 236), radius=4)
        fill_w = int((1068 - 242) * (value / 100.0))
        rounded(draw, (242, y, 242 + fill_w, y + 12), COLORS["primary"], radius=4)
        draw.ellipse((242 + fill_w - 8, y - 6, 242 + fill_w + 8, y + 18), fill=(248, 250, 255), outline=COLORS["border"], width=1)
        draw.text((1082, y + 6), f"{value}%", anchor="lm", font=FONT_CAPTION, fill=COLORS["text_muted"])
        y += 74

    draw_button(draw, (1096, 650, 1252, 684), "Apply", primary=True)
    return img


def screen_settings_security() -> Image.Image:
    img = base_screen(["Play", "Create", "Settings", "Update", "Logout", "Quit"], 2)
    draw = ImageDraw.Draw(img, "RGBA")
    shell = (196, 132, 1304, 726)
    draw_shell(img, shell, "Settings")
    draw_settings_header(draw, shell)

    rounded(draw, (220, 222, 1280, 704), COLORS["panel"], radius=6, outline=COLORS["border_soft"], width=1)
    draw.text((242, 244), "Multi-factor Authentication", font=FONT_SUBTITLE, fill=COLORS["text"])
    draw_button(draw, (922, 242, 1060, 276), "MFA: ON", primary=True)
    draw_button(draw, (1072, 242, 1200, 276), "Refresh QR")
    draw_button(draw, (1212, 242, 1266, 276), "Copy URI")

    rounded(draw, (242, 298, 706, 650), COLORS["panel_alt"], radius=5, outline=COLORS["border_soft"], width=1)
    # stylized qr blocks
    qx, qy, qs = 310, 360, 250
    rounded(draw, (qx, qy, qx + qs, qy + qs), (248, 250, 255), radius=2, outline=COLORS["border_soft"], width=1)
    for row in range(21):
        for col in range(21):
            if (row * col + row + col) % 3 == 0:
                x = qx + 12 + col * 10
                y = qy + 12 + row * 10
                rounded(draw, (x, y, x + 8, y + 8), (36, 46, 63), radius=1)

    rounded(draw, (724, 298, 1256, 650), COLORS["panel_alt"], radius=5, outline=COLORS["border_soft"], width=1)
    info = (
        "MFA is active for this account.\n\n"
        "Secret: D772WD3GP3ITL4JCP3YGNG5DGAJOSTIH\n\n"
        "Provisioning URI:\n"
        "otpauth://totp/karaxas:account@email.com?..."
    )
    draw_text_box(draw, (744, 320), info, FONT_BODY_XS, COLORS["text_soft"], 486)
    draw.text((242, 668), "Status: MFA QR ready.", font=FONT_CAPTION, fill=COLORS["success"])
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    concepts = {
        "ui_concept_login.png": screen_login(),
        "ui_concept_register.png": screen_register(),
        "ui_concept_update.png": screen_update(),
        "ui_concept_play_empty.png": screen_play_empty(),
        "ui_concept_play_selected.png": screen_play_selected(),
        "ui_concept_create_character.png": screen_create_character(),
        "ui_concept_settings_video.png": screen_settings_video(),
        "ui_concept_settings_audio.png": screen_settings_audio(),
        "ui_concept_settings_security.png": screen_settings_security(),
    }
    for name, img in concepts.items():
        out_path = OUT_DIR / name
        img.convert("RGB").save(out_path, "PNG", optimize=True)
        print(out_path)


if __name__ == "__main__":
    main()
