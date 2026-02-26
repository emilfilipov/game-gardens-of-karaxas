#!/usr/bin/env python3
"""
Generate a fresh radial-menu concept reboot from the canonical ui_concept_*.png baseline set.
This script intentionally avoids previous concept branches and writes only into:
  concept_art/option_radial_reboot_blackwhite/pass_XX/
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "concept_art"
OUT_ROOT = BASE / "option_radial_reboot_blackwhite"

SCENES = {
    "boot": "ui_concept_login.png",
    "gateway": "ui_concept_login.png",
    "register": "ui_concept_register.png",
    "play_empty": "ui_concept_play_empty.png",
    "play_selected": "ui_concept_play_selected.png",
    "create": "ui_concept_create_character.png",
    "system": "ui_concept_settings_security.png",
    "update": "ui_concept_update.png",
}

WORLD = {
    "COI": (0, 0),
    "Auth": (-220, -120),
    "Register": (-420, -120),
    "Play": (250, 0),
    "Create": (250, 180),
    "System": (0, 240),
    "Update": (-220, 180),
    "Quit": (-420, 180),
}

EDGES = [
    ("COI", "Auth", "enter"),
    ("Auth", "Register", "create account"),
    ("Auth", "Play", "go to lobby"),
    ("COI", "System", "settings"),
    ("COI", "Update", "patch notes"),
    ("Update", "Quit", "quit"),
    ("Play", "Create", "new character"),
]

FOCUS = {
    "boot": "COI",
    "gateway": "Auth",
    "register": "Register",
    "play_empty": "Play",
    "play_selected": "Play",
    "create": "Create",
    "system": "System",
    "update": "Update",
}

NODE_SHORT = {
    "COI": "COI",
    "Auth": "A",
    "Register": "R",
    "Play": "P",
    "Create": "+",
    "System": "S",
    "Update": "U",
    "Quit": "Q",
}

PAL = {
    "bg": "#f4f4f6",
    "bg_grid": "#e2e5ea",
    "ink": "#12151b",
    "ink_soft": "#5d6470",
    "panel": "#fcfcfd",
    "panel_dim": "#f1f2f5",
    "line": "#b8bec9",
    "accent": "#11161f",
    "accent2": "#252b37",
    "active": "#000000",
    "btn_text": "#ffffff",
    "chip": "#ebedf2",
}


def load_fonts() -> Dict[str, ImageFont.ImageFont]:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    def font(size: int, mono: bool = False) -> ImageFont.ImageFont:
        if mono:
            mono_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
            if Path(mono_path).exists():
                return ImageFont.truetype(mono_path, size=size)
        for c in candidates:
            if Path(c).exists():
                return ImageFont.truetype(c, size=size)
        return ImageFont.load_default()

    return {
        "title": font(38),
        "h1": font(30),
        "h2": font(24),
        "body": font(18),
        "small": font(14),
        "tiny": font(12),
        "mono": font(13, mono=True),
    }


F = load_fonts()


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def node_blob(center: Tuple[int, int], radius: int, seed: int) -> List[Tuple[float, float]]:
    rnd = random.Random(seed)
    cx, cy = center
    pts: List[Tuple[float, float]] = []
    count = 42
    for i in range(count):
        ang = (2 * math.pi * i) / count
        wob = 0.74 + rnd.random() * 0.46
        scallop = 1.0 + 0.12 * math.sin(ang * 7 + rnd.random() * 0.9)
        r = radius * wob * scallop
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    return pts


def draw_background(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)
    w, h = img.size
    d.rectangle((0, 0, w, h), fill=PAL["bg"])
    step = 96
    for y in range(0, h, step):
        d.line((0, y, w, y), fill=PAL["bg_grid"], width=1)


def screen_pos(node: str, focus: str, size: Tuple[int, int]) -> Tuple[int, int]:
    w, h = size
    cx, cy = w // 2, h // 2
    fx, fy = WORLD[focus]
    nx, ny = WORLD[node]
    return int(cx + (nx - fx)), int(cy + (ny - fy))


def draw_edge(d: ImageDraw.ImageDraw, a: Tuple[int, int], b: Tuple[int, int], active: bool) -> None:
    color = PAL["accent2"] if active else PAL["line"]
    width = 3 if active else 2
    ax, ay = a
    bx, by = b
    mx = int((ax + bx) / 2)
    d.line((ax, ay, mx, ay), fill=color, width=width)
    d.line((mx, ay, bx, by), fill=color, width=width)


def draw_chip(d: ImageDraw.ImageDraw, at: Tuple[int, int], text: str) -> None:
    x, y = at
    tw = int(F["tiny"].getlength(text)) + 18
    th = 22
    r = 8
    d.rounded_rectangle((x - tw // 2, y - th // 2, x + tw // 2, y + th // 2), radius=r, fill=PAL["chip"], outline=PAL["line"], width=1)
    d.text((x, y), text, anchor="mm", font=F["tiny"], fill=PAL["ink_soft"])


def draw_node(d: ImageDraw.ImageDraw, node: str, p: Tuple[int, int], active: bool) -> None:
    x, y = p
    base_r = 54 if active else 38
    pts = node_blob((x, y), base_r, seed=hash((node, x, y)) & 0xFFFF)
    fill = PAL["active"] if active else PAL["accent2"]
    d.polygon(pts, fill=fill, outline=PAL["ink"])
    if active:
        d.ellipse((x - base_r - 10, y - base_r - 10, x + base_r + 10, y + base_r + 10), outline="#404754", width=2)
    d.text((x, y), NODE_SHORT[node], anchor="mm", font=F["h2"], fill="#ffffff")


def card(d: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], title: str) -> None:
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=14, fill=PAL["panel"], outline=PAL["line"], width=2)
    d.text((x0 + 20, y0 + 22), title, font=F["h2"], fill=PAL["ink"], anchor="ls")
    d.line((x0 + 16, y0 + 34, x1 - 16, y0 + 34), fill=PAL["bg_grid"], width=1)


def input_line(d: ImageDraw.ImageDraw, x: int, y: int, w: int, txt: str) -> int:
    h = 34
    d.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
    d.text((x + 12, y + h // 2), txt, anchor="lm", font=F["body"], fill=PAL["ink_soft"])
    return y + h + 10


def button(d: ImageDraw.ImageDraw, x: int, y: int, w: int, txt: str, dark: bool = True) -> int:
    h = 34
    fill = PAL["accent"] if dark else PAL["panel_dim"]
    txt_c = PAL["btn_text"] if dark else PAL["ink"]
    d.rounded_rectangle((x, y, x + w, y + h), radius=9, fill=fill, outline=PAL["line"], width=1)
    d.text((x + w // 2, y + h // 2), txt, anchor="mm", font=F["body"], fill=txt_c)
    return y + h + 10


def graph_preview(d: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], selected: bool) -> None:
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=10, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
    for x in range(x0 + 20, x1 - 8, 58):
        d.line((x, y0 + 12, x, y1 - 12), fill=PAL["bg_grid"], width=1)
    for y in range(y0 + 12, y1 - 8, 52):
        d.line((x0 + 12, y, x1 - 12, y), fill=PAL["bg_grid"], width=1)
    if not selected:
        d.text(((x0 + x1) // 2, (y0 + y1) // 2), "No character selected", anchor="mm", font=F["body"], fill=PAL["ink_soft"])
        return
    pts = [(x0 + 74, y0 + 150), (x0 + 150, y0 + 176), (x0 + 236, y0 + 132), (x0 + 304, y0 + 168), (x0 + 372, y0 + 124)]
    center = (x0 + 236, y0 + 176)
    extra = [(x0 + 236, y0 + 86), (x0 + 212, y0 + 232), (x0 + 300, y0 + 232)]
    seg = [pts[0], pts[1], center, pts[3], pts[4], center, extra[0], center, extra[1], center, extra[2]]
    d.line(seg, fill=PAL["accent2"], width=3)
    for p in [*pts, center, *extra]:
        d.ellipse((p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8), fill=PAL["accent"], outline="#ffffff", width=1)


def draw_panel(d: ImageDraw.ImageDraw, mode: str, size: Tuple[int, int]) -> None:
    w, h = size
    box = (w // 2 - 270, h // 2 - 180, w // 2 + 270, h // 2 + 180)

    if mode == "boot":
        x0, y0, x1, y1 = box
        card(d, box, "COI")
        d.text(((x0 + x1) // 2, y0 + 150), "Click center orb to open radial routes", anchor="mm", font=F["body"], fill=PAL["ink_soft"])
        d.text(((x0 + x1) // 2, y0 + 180), "No sidebars. Graph-first navigation.", anchor="mm", font=F["small"], fill=PAL["ink_soft"])
        return

    titles = {
        "gateway": "Gateway",
        "register": "Create Account",
        "play_empty": "Play Hub",
        "play_selected": "Play Hub",
        "create": "Create Character",
        "system": "System",
        "update": "Update",
    }
    card(d, box, titles[mode])
    x0, y0, x1, y1 = box

    if mode == "gateway":
        y = y0 + 52
        y = input_line(d, x0 + 20, y, 280, "Email")
        y = input_line(d, x0 + 20, y, 280, "Password")
        y = input_line(d, x0 + 20, y, 280, "MFA (optional)")
        button(d, x0 + 20, y, 280, "Continue")
        card(d, (x0 + 320, y0 + 44, x1 - 20, y1 - 18), "Patch Snapshot")
        d.text((x0 + 340, y0 + 96), "Build: v1.0.157", font=F["small"], fill=PAL["ink_soft"], anchor="ls")
        d.text((x0 + 340, y0 + 120), "- Login + register + update in one node.", font=F["small"], fill=PAL["ink_soft"], anchor="ls")
        d.text((x0 + 340, y0 + 142), "- Play node unlocks after auth.", font=F["small"], fill=PAL["ink_soft"], anchor="ls")
        button(d, x0 + 336, y1 - 62, 180, "Check Update")

    elif mode == "register":
        y = y0 + 52
        y = input_line(d, x0 + 20, y, 300, "Display Name")
        y = input_line(d, x0 + 20, y, 300, "Email")
        y = input_line(d, x0 + 20, y, 300, "Password")
        button(d, x0 + 20, y, 300, "Create Account")
        d.text((x0 + 340, y0 + 90), "Registration returns to auth node.", font=F["small"], fill=PAL["ink_soft"], anchor="ls")

    elif mode == "play_empty":
        d.rounded_rectangle((x0 + 20, y0 + 54, x0 + 190, y1 - 70), radius=10, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
        d.text((x0 + 34, y0 + 80), "Roster", anchor="ls", font=F["body"], fill=PAL["ink"])
        d.text((x0 + 34, y0 + 110), "No character selected", anchor="ls", font=F["small"], fill=PAL["ink_soft"])
        graph_preview(d, (x0 + 205, y0 + 54, x1 - 20, y1 - 110), selected=False)
        button(d, x0 + 20, y1 - 58, 100, "Save")
        button(d, x0 + 130, y1 - 58, 100, "Play")

    elif mode == "play_selected":
        d.rounded_rectangle((x0 + 20, y0 + 54, x0 + 190, y1 - 70), radius=10, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
        d.text((x0 + 34, y0 + 80), "Roster", anchor="ls", font=F["body"], fill=PAL["ink"])
        d.rounded_rectangle((x0 + 32, y0 + 96, x0 + 178, y0 + 126), radius=7, fill=PAL["accent"], outline=PAL["line"], width=1)
        d.text((x0 + 42, y0 + 112), "Sellsword", anchor="lm", font=F["small"], fill="#ffffff")
        d.rounded_rectangle((x0 + 32, y0 + 132, x0 + 178, y0 + 162), radius=7, fill=PAL["panel"], outline=PAL["line"], width=1)
        d.text((x0 + 42, y0 + 148), "Scout", anchor="lm", font=F["small"], fill=PAL["ink_soft"])
        graph_preview(d, (x0 + 205, y0 + 54, x1 - 20, y1 - 110), selected=True)
        d.text((x0 + 210, y1 - 92), "Node: Core | Routes: Resolve, Dexterity, Vitality", anchor="ls", font=F["small"], fill=PAL["ink_soft"])
        button(d, x0 + 20, y1 - 58, 100, "Save")
        button(d, x0 + 130, y1 - 58, 100, "Play")
        button(d, x0 + 240, y1 - 58, 100, "Delete", dark=False)

    elif mode == "create":
        d.rounded_rectangle((x0 + 20, y0 + 54, x0 + 180, y1 - 20), radius=10, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
        d.text((x0 + 34, y0 + 80), "Archetypes", anchor="ls", font=F["body"], fill=PAL["ink"])
        d.rounded_rectangle((x0 + 32, y0 + 94, x0 + 168, y0 + 132), radius=8, fill=PAL["accent"], outline=PAL["line"], width=1)
        d.text((x0 + 42, y0 + 108), "Sellsword", anchor="lm", font=F["small"], fill="#ffffff")
        d.rounded_rectangle((x0 + 32, y0 + 140, x0 + 168, y0 + 178), radius=8, fill=PAL["panel"], outline=PAL["line"], width=1)
        d.text((x0 + 42, y0 + 156), "Scout", anchor="lm", font=F["small"], fill=PAL["ink_soft"])
        y = y0 + 54
        y = input_line(d, x0 + 200, y, 280, "Character Name")
        y = input_line(d, x0 + 200, y, 280, "Sellsword")
        y = input_line(d, x0 + 200, y, 280, "Male")
        d.rounded_rectangle((x0 + 200, y, x1 - 20, y + 104), radius=9, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
        d.text((x0 + 212, y + 24), "Sellsword starts at Core and can branch to Resolve / Vitality.", anchor="ls", font=F["small"], fill=PAL["ink_soft"])
        button(d, x0 + 200, y + 114, 280, "Create Character")

    elif mode == "system":
        d.text((x0 + 20, y0 + 56), "Audio", anchor="ls", font=F["body"], fill=PAL["ink"])
        for i, label in enumerate(["Master", "Music", "Effects", "Interface"]):
            yy = y0 + 88 + i * 40
            d.text((x0 + 20, yy), label, anchor="ls", font=F["small"], fill=PAL["ink_soft"])
            d.line((x0 + 86, yy - 2, x0 + 320, yy - 2), fill=PAL["line"], width=4)
            d.line((x0 + 86, yy - 2, x0 + 200 + i * 12, yy - 2), fill=PAL["accent"], width=4)
        card(d, (x0 + 340, y0 + 54, x1 - 20, y1 - 20), "MFA")
        button(d, x0 + 358, y0 + 96, 120, "MFA: ON")
        button(d, x0 + 486, y0 + 96, 90, "Refresh", dark=False)
        button(d, x0 + 580, y0 + 96, 86, "Copy URI", dark=False)
        button(d, x1 - 130, y1 - 58, 100, "Apply")

    elif mode == "update":
        d.text((x0 + 20, y0 + 60), "Build: v1.0.157", anchor="ls", font=F["body"], fill=PAL["ink"])
        d.rounded_rectangle((x0 + 20, y0 + 80, x1 - 20, y1 - 70), radius=8, fill=PAL["panel_dim"], outline=PAL["line"], width=1)
        lines = [
            "Release Notes",
            "- Graph-radial traversal mode reboot from baseline ui_concept pack.",
            "- Black/white theme pass and tighter panel composition.",
            "- Register/login/update semantics preserved.",
        ]
        for i, t in enumerate(lines):
            d.text((x0 + 32, y0 + 108 + i * 28), t, anchor="ls", font=F["small"], fill=PAL["ink_soft"])
        button(d, x0 + 20, y1 - 58, x1 - x0 - 40, "Check for Update")


def scene(mode: str) -> Image.Image:
    with Image.open(BASE / SCENES[mode]).convert("RGB") as src:
        w, h = src.size

    img = Image.new("RGB", (w, h), PAL["bg"])
    draw_background(img)
    d = ImageDraw.Draw(img)

    focus = FOCUS[mode]
    # Draw edges first
    for a, b, label in EDGES:
        pa = screen_pos(a, focus, (w, h))
        pb = screen_pos(b, focus, (w, h))
        active = (a == focus or b == focus)
        draw_edge(d, pa, pb, active)
        mx, my = (pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2
        draw_chip(d, (mx, my - 16), label)

    # Draw nodes
    for n in WORLD:
        p = screen_pos(n, focus, (w, h))
        if -120 <= p[0] <= w + 120 and -120 <= p[1] <= h + 120:
            draw_node(d, n, p, active=(n == focus))

    # Focus panel
    draw_panel(d, mode, (w, h))

    # subtle footer
    d.text((w - 18, h - 14), "pass_01", anchor="rs", font=F["tiny"], fill=PAL["ink_soft"])
    return img


def contact_sheet(paths: Iterable[Path], out_path: Path) -> None:
    items = [Image.open(p).convert("RGB") for p in paths]
    cols = 3
    cell_w, cell_h = 430, 250
    rows = math.ceil(len(items) / cols)
    canvas = Image.new("RGB", (cols * cell_w, rows * cell_h), "#ffffff")
    d = ImageDraw.Draw(canvas)
    for i, (im, p) in enumerate(zip(items, paths)):
        r, c = divmod(i, cols)
        x0, y0 = c * cell_w, r * cell_h
        th = 210
        preview = im.copy()
        preview.thumbnail((cell_w - 16, th - 16))
        px = x0 + (cell_w - preview.width) // 2
        py = y0 + 8
        canvas.paste(preview, (px, py))
        d.text((x0 + 10, y0 + th + 10), p.name, font=F["body"], fill="#263042")
        d.line((x0, y0 + th, x0 + cell_w, y0 + th), fill="#d6dce6", width=1)
        if c > 0:
            d.line((x0, y0, x0, y0 + th), fill="#d6dce6", width=1)
    canvas.save(out_path)


def write_process(pass_dir: Path) -> None:
    text = """Pass 01 (Radial Reboot - Black/White)
1. Plan
- Reboot from ui_concept_* baseline only (no reuse of deprecated concept families).
- Remove headline dependence and pivot to graph-radial navigation with a centered COI orb.
- Keep feature parity by mapping auth/register/play/create/system/update into focused node panels.

2. Draw/Generate
- Custom radial blob nodes + edge-route chips.
- Camera-centered node traversal composition (focused node in center, surrounding nodes partially visible).
- Black/white high-contrast controls and compact panel payloads.

3. Review Targets (for next pass)
- Increase visual fidelity of node art (more layered shading/pixel texture).
- Reduce chip overlap on dense edges.
- Tighten panel-to-node alignment and improve menu readability at distance.
"""
    (pass_dir / "process.md").write_text(text, encoding="utf-8")


def generate(pass_no: int) -> None:
    if pass_no != 1:
        raise SystemExit("This reboot script intentionally starts from pass 01 only.")

    pass_dir = OUT_ROOT / f"pass_{pass_no:02d}"
    pass_dir.mkdir(parents=True, exist_ok=True)

    saved: List[Path] = []
    order = ["boot", "gateway", "register", "play_empty", "play_selected", "create", "system", "update"]
    for mode in order:
        im = scene(mode)
        out = pass_dir / f"radial_{mode}.png"
        im.save(out)
        saved.append(out)

    contact_sheet(saved, pass_dir / "radial_contact_sheet.png")
    write_process(pass_dir)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", type=int, default=1, dest="pass_no")
    args = ap.parse_args()
    generate(args.pass_no)


if __name__ == "__main__":
    main()
