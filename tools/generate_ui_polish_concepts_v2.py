#!/usr/bin/env python3
"""Generate v2 UI exploration concepts without overwriting the baseline set."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "concept_art" / "v2"
W, H = 1366, 768

C = {
    "bg": (194, 209, 229),
    "header": (186, 203, 225),
    "shell": (224, 234, 246, 238),
    "panel": (236, 242, 250, 246),
    "panel_alt": (228, 236, 247, 246),
    "border": (146, 169, 199, 220),
    "border_soft": (165, 183, 210, 188),
    "text": (27, 44, 72),
    "text_soft": (62, 82, 108),
    "text_muted": (88, 106, 132),
    "primary": (82, 138, 210),
    "primary_text": (244, 249, 255),
    "button": (246, 244, 235),
    "button_text": (57, 74, 100),
    "success": (86, 168, 110),
    "warning": (237, 173, 84),
}


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


F_TITLE = _font(ROOT / "game-client" / "assets" / "fonts" / "cinzel.ttf", 58)
F_H = _font(ROOT / "game-client" / "assets" / "fonts" / "cinzel.ttf", 18)
F_B = _font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 24)
F_SM = _font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 20)
F_XS = _font(ROOT / "game-client" / "assets" / "fonts" / "cormorant_garamond.ttf", 17)


def rr(draw: ImageDraw.ImageDraw, rect, fill, r=9, outline=None, w=1):
    draw.rounded_rectangle(rect, radius=r, fill=fill, outline=outline, width=w)


def _split_token(draw: ImageDraw.ImageDraw, token: str, font, max_w: int) -> list[str]:
    if draw.textlength(token, font=font) <= max_w:
        return [token]
    parts: list[str] = []
    i = 0
    while i < len(token):
        j = i + 1
        while j <= len(token) and draw.textlength(token[i:j], font=font) <= max_w:
            j += 1
        end = max(i + 1, j - 1)
        parts.append(token[i:end])
        i = end
    return parts


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


def btn(draw: ImageDraw.ImageDraw, rect, label: str, primary: bool = False):
    fill = C["primary"] if primary else C["button"]
    text = C["primary_text"] if primary else C["button_text"]
    rr(draw, rect, fill, r=4, outline=C["border_soft"], w=1)
    draw.text(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), label, anchor="mm", font=F_SM, fill=text)


def input_field(draw: ImageDraw.ImageDraw, rect, label: str, value: str = ""):
    rr(draw, rect, C["panel_alt"], r=4, outline=C["border_soft"], w=1)
    draw.text((rect[0] + 10, (rect[1] + rect[3]) // 2), value if value else label, anchor="lm", font=F_XS, fill=C["text"] if value else C["text_muted"])


def base(nav_items: list[str], active: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), C["bg"] + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, 100), fill=C["header"] + (130,))
    d.text((W // 2, 44), "Children of Ikphelion", anchor="mm", font=F_TITLE, fill=C["text"])
    d.line((24, 98, W - 24, 98), fill=C["border_soft"], width=1)

    sx, sy, sw, sh = 26, 156, 134, 444
    rr(d, (sx, sy, sx + sw, sy + sh), C["shell"], r=8, outline=C["border"], w=1)

    by = sy + 90
    for i, item in enumerate(nav_items):
        rect = (sx + 16, by + i * 44, sx + sw - 16, by + i * 44 + 34)
        btn(d, rect, item, primary=(i == active))
    return img


def screen_login() -> Image.Image:
    img = base(["Login", "Register", "Update", "Quit"], 0)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (276, 184, 1088, 584)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)

    left = (302, 214, 774, 544)
    rr(d, left, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((324, 240), "Account Access", font=F_H, fill=C["text"])

    input_field(d, (324, 276, 752, 310), "Email", "admin@admin.com")
    input_field(d, (324, 320, 752, 354), "Password")
    input_field(d, (324, 364, 752, 398), "MFA Code (optional)")
    btn(d, (324, 416, 752, 452), "Login", primary=True)

    d.text((324, 500), "Client version: v1.0.157", font=F_XS, fill=C["text_muted"])
    d.text((752, 500), "MFA available in Security settings", anchor="ra", font=F_XS, fill=C["text_muted"])

    right = (792, 214, 1062, 544)
    rr(d, right, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((814, 240), "Quick Notes", font=F_H, fill=C["text"])
    tbox(d, (814, 274), "A clean pre-login lobby focused on account entry and update awareness.", F_XS, C["text_soft"], 224, max_lines=7)
    return img


def screen_register() -> Image.Image:
    img = base(["Login", "Register", "Update", "Quit"], 1)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (276, 184, 1088, 584)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)

    card = (302, 214, 774, 544)
    rr(d, card, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((324, 240), "Create Account", font=F_H, fill=C["text"])

    input_field(d, (324, 276, 752, 310), "Display Name")
    input_field(d, (324, 320, 752, 354), "Email")
    input_field(d, (324, 364, 752, 398), "Password")
    btn(d, (324, 416, 752, 452), "Register", primary=True)

    rules = (792, 214, 1062, 544)
    rr(d, rules, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((814, 240), "Registration Rules", font=F_H, fill=C["text"])
    tbox(d, (814, 274), "Display names are unique.\n\nMFA setup is available after first successful login.", F_XS, C["text_soft"], 224, max_lines=8)
    return img


def screen_update() -> Image.Image:
    img = base(["Login", "Register", "Update", "Quit"], 2)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (264, 144, 1110, 628)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)

    top = (292, 174, 1082, 230)
    rr(d, top, C["panel_alt"], r=6, outline=C["border_soft"], w=1)
    d.text((314, 192), "Installed Build", font=F_XS, fill=C["text_muted"])
    d.text((314, 208), "v1.0.157", font=F_SM, fill=C["text"])
    d.text((520, 192), "Channel", font=F_XS, fill=C["text_muted"])
    d.text((520, 208), "Stable / Live", font=F_SM, fill=C["text"])
    d.text((760, 192), "Status", font=F_XS, fill=C["text_muted"])
    d.text((760, 208), "Up to date", font=F_SM, fill=C["success"])

    notes = (292, 244, 1082, 556)
    rr(d, notes, C["panel"], r=6, outline=C["border_soft"], w=1)
    d.text((314, 266), "Release Notes", font=F_H, fill=C["text"])
    bullet = [
        "Single-tone backdrop for calmer menu reading.",
        "Compact side navigation with fixed interaction rhythm.",
        "Character hub split into role-specific cards.",
        "Text wrapping hardened to avoid overflow artifacts.",
    ]
    y = 302
    for line in bullet:
        tbox(d, (322, y), f"- {line}", F_XS, C["text_soft"], 730, max_lines=2)
        y += 38

    btn(d, (292, 570, 688, 606), "Check for Update", primary=True)
    btn(d, (700, 570, 1082, 606), "View Update Logs", primary=False)
    return img


def screen_play_empty() -> Image.Image:
    img = base(["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (178, 116, 1340, 744)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)

    roster = (202, 154, 452, 716)
    rr(d, roster, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((222, 178), "Characters", font=F_H, fill=C["text"])
    btn(d, (222, 212, 430, 246), "Create Character", primary=True)
    tbox(d, (222, 278), "No characters found.\nCreate a hero to unlock Play.", F_SM, C["text_muted"], 204, max_lines=5)

    launch = (466, 154, 1030, 716)
    rr(d, launch, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((486, 178), "Session Launch", font=F_H, fill=C["text"])
    tbox(d, (486, 222), "Character selection is now focused and minimal. Build planning can remain a dedicated offline tool instead of occupying this lobby by default.", F_SM, C["text_soft"], 520, max_lines=9)

    rr(d, (486, 392, 1010, 690), C["panel_alt"], r=6, outline=C["border_soft"], w=1)
    d.text((748, 532), "No character selected", anchor="mm", font=F_B, fill=C["text_muted"])

    details = (1044, 154, 1320, 716)
    rr(d, details, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((1064, 178), "Character Details", font=F_H, fill=C["text"])
    tbox(d, (1064, 220), "Select a character to view spawn location, class profile, and launch actions.", F_SM, C["text_muted"], 230, max_lines=8)
    btn(d, (1064, 670, 1186, 706), "Play", primary=False)
    btn(d, (1192, 670, 1298, 706), "Delete", primary=False)
    return img


def screen_play_selected() -> Image.Image:
    img = base(["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 0)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (178, 116, 1340, 744)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)

    roster = (202, 154, 452, 716)
    rr(d, roster, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((222, 178), "Characters", font=F_H, fill=C["text"])
    btn(d, (222, 212, 430, 246), "Create Character")

    rr(d, (222, 278, 430, 328), C["primary"], r=5, outline=C["border_soft"], w=1)
    d.text((236, 292), "Sellsword", font=F_SM, fill=C["primary_text"])
    d.text((236, 312), "Lv 5 | Ironhold", font=F_XS, fill=C["primary_text"])
    rr(d, (222, 336, 430, 386), C["panel_alt"], r=5, outline=C["border_soft"], w=1)
    d.text((236, 350), "Scout", font=F_SM, fill=C["text"])
    d.text((236, 370), "Lv 2 | Khar Grotto", font=F_XS, fill=C["text_muted"])

    center = (466, 154, 1030, 716)
    rr(d, center, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((486, 178), "Selected Character", font=F_H, fill=C["text"])
    rr(d, (486, 214, 1010, 406), C["panel_alt"], r=6, outline=C["border_soft"], w=1)

    stats = [
        ("Class", "Mercenary"),
        ("Power", "112"),
        ("Armor", "84"),
        ("Crit", "8.7%"),
    ]
    x = 510
    y = 238
    for k, v in stats:
        d.text((x, y), k, font=F_XS, fill=C["text_muted"])
        d.text((x, y + 18), v, font=F_SM, fill=C["text"])
        y += 58

    d.text((510, 470), "Move Speed", font=F_XS, fill=C["text_muted"])
    d.text((510, 488), "+12%", font=F_SM, fill=C["text"])

    tbox(d, (486, 534), "Build Planner is optional here. Keep this lobby optimized for character launch speed and clarity.", F_SM, C["text_soft"], 520, max_lines=4)
    btn(d, (486, 618, 764, 654), "Open Build Planner (Offline)")

    right = (1044, 154, 1320, 716)
    rr(d, right, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((1064, 178), "Character Details", font=F_H, fill=C["text"])
    tbox(d, (1064, 220), "Name: Sellsword\nClass: Mercenary\nSex: Male\nZone: Ironhold\nFacing: East", F_SM, C["text_soft"], 230, max_lines=8)
    d.text((1064, 414), "Spawn Override (Admin)", font=F_XS, fill=C["text_muted"])
    input_field(d, (1064, 438, 1298, 472), "Current location", "Current location")
    btn(d, (1064, 670, 1186, 706), "Play", primary=True)
    btn(d, (1192, 670, 1298, 706), "Delete")
    return img


def screen_create() -> Image.Image:
    img = base(["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 1)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (178, 116, 1340, 744)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)

    arch = (202, 154, 468, 716)
    rr(d, arch, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((222, 178), "Archetypes", font=F_H, fill=C["text"])
    rr(d, (222, 212, 448, 276), C["primary"], r=5, outline=C["border_soft"], w=1)
    d.text((236, 226), "Sellsword", font=F_SM, fill=C["primary_text"])
    tbox(d, (236, 246), "Durable melee opener", F_XS, C["primary_text"], 200, max_lines=2)
    rr(d, (222, 286, 448, 350), C["panel_alt"], r=5, outline=C["border_soft"], w=1)
    d.text((236, 300), "Scout", font=F_SM, fill=C["text"])
    tbox(d, (236, 320), "Mobile precision style", F_XS, C["text_muted"], 200, max_lines=2)

    form = (482, 154, 1030, 716)
    rr(d, form, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((502, 178), "Identity & Core Choices", font=F_H, fill=C["text"])

    input_field(d, (502, 214, 1008, 248), "Character Name")
    input_field(d, (502, 258, 1008, 292), "Character Type", "Sellsword")
    input_field(d, (502, 302, 1008, 336), "Sex", "Male")

    rr(d, (502, 354, 1008, 644), C["panel_alt"], r=6, outline=C["border_soft"], w=1)
    d.text((522, 378), "Lore", font=F_H, fill=C["text"])
    lore = "Sellswords are frontline contractors hardened by border conflicts. They are intended as a straightforward entry with strong survivability and stable momentum in early progression."
    tbox(d, (522, 410), lore, F_SM, C["text_soft"], 470, max_lines=10)

    btn(d, (502, 670, 1008, 706), "Create Character", primary=True)

    side = (1044, 154, 1320, 716)
    rr(d, side, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((1064, 178), "Optional Tools", font=F_H, fill=C["text"])
    tbox(d, (1064, 220), "Build planning can stay separate from creation. Keep creation flow focused on identity and class intent.", F_SM, C["text_soft"], 230, max_lines=9)
    btn(d, (1064, 570, 1298, 606), "Open Planner")
    btn(d, (1064, 670, 1298, 706), "Back to Play")
    return img


def screen_settings_audio() -> Image.Image:
    img = base(["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 2)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (178, 132, 1320, 724)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)
    d.text((202, 156), "Settings", font=F_H, fill=C["text"])
    btn(d, (202, 186, 292, 220), "Video")
    btn(d, (298, 186, 388, 220), "Audio", primary=True)
    btn(d, (394, 186, 484, 220), "Security")

    body = (202, 236, 1294, 702)
    rr(d, body, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((224, 260), "Audio Mix", font=F_H, fill=C["text"])

    labels = ["Master", "Music", "Effects", "Interface"]
    values = [78, 62, 84, 55]
    y = 308
    for name, val in zip(labels, values):
        d.text((224, y - 20), name, font=F_SM, fill=C["text_soft"])
        rr(d, (224, y, 1030, y + 12), (205, 218, 236), r=4)
        w_fill = int((1030 - 224) * (val / 100))
        rr(d, (224, y, 224 + w_fill, y + 12), C["primary"], r=4)
        d.ellipse((224 + w_fill - 7, y - 6, 224 + w_fill + 7, y + 18), fill=(248, 250, 255), outline=C["border"], width=1)
        d.text((1040, y + 6), f"{val}%", anchor="lm", font=F_XS, fill=C["text_muted"])
        y += 72

    btn(d, (1080, 654, 1270, 690), "Apply", primary=True)
    return img


def screen_settings_security() -> Image.Image:
    img = base(["Play", "Create", "Settings", "Update", "Log Out", "Quit"], 2)
    d = ImageDraw.Draw(img, "RGBA")

    shell = (178, 132, 1320, 724)
    rr(d, shell, C["shell"], r=10, outline=C["border_soft"], w=1)
    d.text((202, 156), "Settings", font=F_H, fill=C["text"])
    btn(d, (202, 186, 292, 220), "Video")
    btn(d, (298, 186, 388, 220), "Audio")
    btn(d, (394, 186, 484, 220), "Security", primary=True)

    body = (202, 236, 1294, 702)
    rr(d, body, C["panel"], r=7, outline=C["border_soft"], w=1)
    d.text((224, 260), "Multi-factor Authentication", font=F_H, fill=C["text"])

    btn(d, (920, 252, 1046, 286), "MFA: ON", primary=True)
    btn(d, (1056, 252, 1178, 286), "Refresh QR")
    btn(d, (1188, 252, 1270, 286), "Copy URI")

    rr(d, (224, 304, 694, 650), C["panel_alt"], r=6, outline=C["border_soft"], w=1)
    rr(d, (266, 346, 500, 580), (248, 250, 255), r=2, outline=C["border_soft"], w=1)
    for r in range(21):
        for c in range(21):
            if (r * c + r + c) % 3 == 0:
                x = 280 + c * 10
                y = 360 + r * 10
                rr(d, (x, y, x + 8, y + 8), (36, 46, 63), r=1)

    rr(d, (714, 304, 1270, 650), C["panel_alt"], r=6, outline=C["border_soft"], w=1)
    info = "MFA is active for this account.\n\nSecret: D772WD3GP3ITL4JCP3YGNG5DGAJOSTIH\n\nProvisioning URI:\notpauth://totp/karaxas:account@email.com?issuer=karaxas"
    tbox(d, (736, 332), info, F_SM, C["text_soft"], 520, max_lines=10)
    d.text((224, 668), "Status: MFA QR ready.", font=F_XS, fill=C["success"])
    return img


def contact_sheet(images: dict[str, Image.Image]) -> Image.Image:
    keys = list(images.keys())
    cols = 3
    rows = (len(keys) + cols - 1) // cols
    tw, th = 420, 236
    pad = 18
    label_h = 24
    out = Image.new("RGBA", (cols * tw + (cols + 1) * pad, rows * (th + label_h) + (rows + 1) * pad), C["bg"] + (255,))
    d = ImageDraw.Draw(out, "RGBA")

    for i, key in enumerate(keys):
        row, col = divmod(i, cols)
        x = pad + col * tw
        y = pad + row * (th + label_h)
        rr(d, (x, y, x + tw, y + th), C["panel"], r=6, outline=C["border_soft"], w=1)
        thumb = images[key].convert("RGB").resize((tw - 12, th - 12), Image.Resampling.BICUBIC)
        out.paste(thumb, (x + 6, y + 6))
        d.text((x, y + th + 5), key, font=F_XS, fill=C["text"])
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    concepts = {
        "ui_v2_login.png": screen_login(),
        "ui_v2_register.png": screen_register(),
        "ui_v2_update.png": screen_update(),
        "ui_v2_play_empty.png": screen_play_empty(),
        "ui_v2_play_selected.png": screen_play_selected(),
        "ui_v2_create_character.png": screen_create(),
        "ui_v2_settings_audio.png": screen_settings_audio(),
        "ui_v2_settings_security.png": screen_settings_security(),
    }

    for name, image in concepts.items():
        path = OUT_DIR / name
        image.convert("RGB").save(path, "PNG", optimize=True)
        print(path)

    sheet = contact_sheet(concepts)
    sheet_path = OUT_DIR / "ui_v2_contact_sheet.png"
    sheet.convert("RGB").save(sheet_path, "PNG", optimize=True)
    print(sheet_path)


if __name__ == "__main__":
    main()
