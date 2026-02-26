#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFont

W, H = 1366, 768
ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "concept_art" / "shadow_graph"

PAL_SHADOW = {
    "bg": (247, 248, 250, 255),
    "ink": (21, 26, 38, 255),
    "ink_soft": (54, 60, 78, 255),
    "shadow_blob": (32, 39, 58, 230),
    "shadow_blob_hi": (58, 67, 94, 210),
    "edge": (64, 73, 100, 255),
    "edge_text": (47, 54, 74, 255),
    "accent": (83, 142, 220, 255),
    "label_bg": (236, 239, 245, 240),
}

PAL_BLOOD = {
    "bg": (250, 248, 247, 255),
    "ink": (43, 20, 24, 255),
    "ink_soft": (75, 36, 43, 255),
    "shadow_blob": (110, 14, 24, 228),
    "shadow_blob_hi": (161, 28, 40, 210),
    "edge": (134, 18, 32, 255),
    "edge_text": (82, 20, 28, 255),
    "accent": (184, 27, 41, 255),
    "label_bg": (246, 234, 236, 240),
}

PAL_MONO = {
    "bg": (246, 246, 247, 255),
    "bg_line": (226, 227, 230, 255),
    "ink": (20, 20, 24, 255),
    "ink_soft": (64, 66, 74, 255),
    "blob_outer": (12, 13, 18, 255),
    "blob_mid": (28, 30, 38, 255),
    "blob_inner": (48, 50, 60, 255),
    "edge": (22, 23, 30, 255),
    "edge_soft": (92, 95, 106, 255),
    "panel": (248, 248, 250, 240),
    "panel_border": (194, 197, 205, 255),
    "chip": (236, 237, 241, 255),
    "chip_border": (184, 187, 195, 255),
    "button": (24, 25, 31, 255),
    "button_text": (248, 248, 250, 255),
    "disabled": (166, 169, 177, 255),
}


def font(cands, size):
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_H1 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 34)
F_H2 = font(["Cinzel-Regular.ttf", "DejaVuSerif.ttf"], 20)
F_TX = font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 15)
F_SM = font(["EBGaramond-Regular.ttf", "DejaVuSerif.ttf"], 12)


def rough_blob(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, seed: int, fill, outline, pal):
    rng = Random(seed)
    pts = []
    steps = 28
    for i in range(steps):
        ang = (2 * math.pi * i) / steps
        rr = r + rng.randint(-10, 10)
        x = int(cx + math.cos(ang) * rr)
        y = int(cy + math.sin(ang) * rr)
        pts.append((x, y))
    draw.polygon(pts, fill=fill, outline=outline)
    # pixel-art-ish noise patches
    for _ in range(48):
        px = rng.randint(cx - r + 8, cx + r - 8)
        py = rng.randint(cy - r + 8, cy + r - 8)
        if (px - cx) ** 2 + (py - cy) ** 2 < (r - 6) ** 2:
            s = rng.choice([2, 3, 4])
            draw.rectangle((px, py, px + s, py + s), fill=pal["shadow_blob_hi"])


def draw_edge(draw: ImageDraw.ImageDraw, p0, p1, text: str, pal):
    x0, y0 = p0
    x1, y1 = p1
    draw.line((x0, y0, x1, y1), fill=pal["edge"], width=4)
    # arrow tip
    vx, vy = x1 - x0, y1 - y0
    ln = max(1.0, math.hypot(vx, vy))
    ux, uy = vx / ln, vy / ln
    px, py = -uy, ux
    tip = (x1, y1)
    l = (int(x1 - ux * 14 + px * 7), int(y1 - uy * 14 + py * 7))
    r = (int(x1 - ux * 14 - px * 7), int(y1 - uy * 14 - py * 7))
    draw.polygon([tip, l, r], fill=pal["edge"])
    # edge label
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2
    w = max(94, len(text) * 7 + 20)
    h = 26
    draw.rounded_rectangle((mx - w // 2, my - h // 2, mx + w // 2, my + h // 2), radius=8, fill=pal["label_bg"], outline=(190, 197, 210, 255), width=1)
    draw.text((mx, my), text, anchor="mm", font=F_SM, fill=pal["edge_text"])


def draw_camera_travel_hint(draw: ImageDraw.ImageDraw, p0, p1, pal):
    x0, y0 = p0
    x1, y1 = p1
    for t in [0.2, 0.4, 0.6, 0.8]:
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t)
        r = 5
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(pal["edge"][0], pal["edge"][1], pal["edge"][2], 120), outline=(255, 255, 255, 190), width=1)


def draw_menu_panel(draw: ImageDraw.ImageDraw, anchor_xy, kind: str, pal):
    ax, ay = anchor_xy
    # Keep panel near node while staying on-screen.
    px = min(max(40, ax + 70), W - 440)
    py = min(max(90, ay - 120), H - 290)
    panel = (px, py, px + 390, py + 220)
    draw.rounded_rectangle(panel, radius=12, fill=(248, 249, 252, 236), outline=(188, 197, 212, 255), width=2)
    # connector from node to panel
    draw.line((ax + 24, ay, px, py + 36), fill=pal["edge"], width=3)
    draw.text((px + 16, py + 16), kind.title(), font=F_H2, fill=pal["ink"])

    if kind == "auth":
        draw.rounded_rectangle((px + 16, py + 46, px + 374, py + 74), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 60), "Email", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 82, px + 374, py + 110), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 96), "Password", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 118, px + 374, py + 146), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 132), "MFA (optional)", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 158, px + 190, py + 190), radius=7, fill=pal["accent"], outline=pal["edge"], width=1)
        draw.text((px + 103, py + 174), "Login", anchor="mm", font=F_TX, fill=(246, 248, 252, 255))
        draw.rounded_rectangle((px + 200, py + 158, px + 374, py + 190), radius=7, fill=(231, 230, 220, 255), outline=pal["edge"], width=1)
        draw.text((px + 287, py + 174), "Register", anchor="mm", font=F_TX, fill=pal["ink"])
    elif kind == "register":
        draw.rounded_rectangle((px + 16, py + 46, px + 374, py + 74), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 60), "Display Name", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 82, px + 374, py + 110), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 96), "Email", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 118, px + 374, py + 146), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 132), "Password", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 158, px + 374, py + 190), radius=7, fill=pal["accent"], outline=pal["edge"], width=1)
        draw.text((px + 195, py + 174), "Create Account", anchor="mm", font=F_TX, fill=(246, 248, 252, 255))
        draw.rounded_rectangle((px + 16, py + 194, px + 374, py + 218), radius=7, fill=(231, 230, 220, 255), outline=pal["edge"], width=1)
        draw.text((px + 195, py + 206), "Back to Login", anchor="mm", font=F_SM, fill=pal["ink"])
    elif kind in {"play", "play_empty", "play_selected"}:
        draw.rounded_rectangle((px + 16, py + 46, px + 150, py + 196), radius=8, fill=(236, 240, 247, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 24, py + 56), "Characters", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 24, py + 78, px + 142, py + 106), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 32, py + 92), "Create +", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 160, py + 46, px + 374, py + 166), radius=8, fill=(236, 240, 247, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 170, py + 56), "Build graph", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 170, py + 74, px + 364, py + 156), radius=6, fill=(242, 244, 248, 255), outline=(188, 197, 212, 255), width=1)
        if kind == "play_empty":
            draw.text((px + 268, py + 114), "No character selected", anchor="mm", font=F_SM, fill=pal["ink_soft"])
            draw.text((px + 268, py + 130), "Choose a hero node", anchor="mm", font=F_SM, fill=pal["ink_soft"])
            draw.rounded_rectangle((px + 160, py + 174, px + 258, py + 202), radius=7, fill=(205, 210, 220, 255), outline=(188, 197, 212, 255), width=1)
            draw.text((px + 209, py + 188), "Play", anchor="mm", font=F_TX, fill=(232, 234, 240, 255))
            draw.rounded_rectangle((px + 266, py + 174, px + 364, py + 202), radius=7, fill=(205, 210, 220, 255), outline=(188, 197, 212, 255), width=1)
            draw.text((px + 315, py + 188), "Delete", anchor="mm", font=F_TX, fill=(232, 234, 240, 255))
        else:
            draw.rounded_rectangle((px + 24, py + 112, px + 142, py + 140), radius=6, fill=pal["accent"], outline=pal["edge"], width=1)
            draw.text((px + 32, py + 126), "Sellsword", font=F_SM, fill=(246, 248, 252, 255))
            draw.rounded_rectangle((px + 24, py + 146, px + 142, py + 174), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
            draw.text((px + 32, py + 160), "Scout", font=F_SM, fill=pal["ink_soft"])
            draw.rounded_rectangle((px + 160, py + 174, px + 258, py + 202), radius=7, fill=pal["accent"], outline=pal["edge"], width=1)
            draw.text((px + 209, py + 188), "Play", anchor="mm", font=F_TX, fill=(246, 248, 252, 255))
            draw.rounded_rectangle((px + 266, py + 174, px + 364, py + 202), radius=7, fill=(231, 230, 220, 255), outline=pal["edge"], width=1)
            draw.text((px + 315, py + 188), "Delete", anchor="mm", font=F_TX, fill=pal["ink"])
    elif kind == "create":
        draw.rounded_rectangle((px + 16, py + 46, px + 374, py + 74), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 60), "Character Name", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 82, px + 374, py + 110), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 96), "Sellsword", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 118, px + 374, py + 146), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 132), "Male", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 152, px + 374, py + 190), radius=8, fill=(236, 240, 247, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 165), "Lore starts near Core with Resolve", font=F_SM, fill=pal["ink_soft"])
        draw.text((px + 26, py + 179), "and Vitality routes.", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 194, px + 374, py + 218), radius=7, fill=pal["accent"], outline=pal["edge"], width=1)
        draw.text((px + 195, py + 206), "Create Character", anchor="mm", font=F_TX, fill=(246, 248, 252, 255))
    elif kind == "system":
        draw.text((px + 16, py + 48), "Audio", font=F_SM, fill=pal["ink_soft"])
        for i, y in enumerate([68, 96, 124]):
            draw.rounded_rectangle((px + 70, py + y, px + 360, py + y + 8), radius=3, fill=(205, 214, 228, 255), outline=(188, 197, 212, 255), width=1)
            draw.rounded_rectangle((px + 70, py + y, px + (260 if i == 0 else 210 if i == 1 else 240), py + y + 8), radius=3, fill=pal["accent"], outline=pal["accent"], width=1)
        draw.rounded_rectangle((px + 16, py + 144, px + 374, py + 170), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 157), "MFA: ON", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 176, px + 190, py + 206), radius=7, fill=(231, 230, 220, 255), outline=pal["edge"], width=1)
        draw.text((px + 103, py + 191), "Refresh QR", anchor="mm", font=F_SM, fill=pal["ink"])
        draw.rounded_rectangle((px + 200, py + 176, px + 374, py + 206), radius=7, fill=(231, 230, 220, 255), outline=pal["edge"], width=1)
        draw.text((px + 287, py + 191), "Copy URI", anchor="mm", font=F_SM, fill=pal["ink"])
    elif kind == "update":
        draw.rounded_rectangle((px + 16, py + 46, px + 374, py + 74), radius=6, fill=(235, 239, 246, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 60), "Build: v1.0.157", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 80, px + 374, py + 178), radius=8, fill=(236, 240, 247, 255), outline=(188, 197, 212, 255), width=1)
        draw.text((px + 26, py + 94), "- Graph-native menu prototype", font=F_SM, fill=pal["ink_soft"])
        draw.text((px + 26, py + 112), "- Login gates play hub", font=F_SM, fill=pal["ink_soft"])
        draw.text((px + 26, py + 130), "- Camera pan between menu nodes", font=F_SM, fill=pal["ink_soft"])
        draw.rounded_rectangle((px + 16, py + 184, px + 374, py + 214), radius=7, fill=pal["accent"], outline=pal["edge"], width=1)
        draw.text((px + 195, py + 199), "Check for Update", anchor="mm", font=F_TX, fill=(246, 248, 252, 255))


def world_nodes():
    return {
        "logo": (0, 0, 54),
        "auth": (-260, -120, 42),
        "register": (-430, -60, 40),
        "play_hub": (260, -20, 50),
        "create": (180, 210, 46),
        "settings": (-90, 250, 44),
        "update": (-360, 170, 44),
        "quit": (-520, 220, 36),
        "char_sellsword": (470, -150, 38),
        "char_scout": (540, 30, 36),
        "char_slot3": (660, 230, 34),
        "mfa": (-180, 390, 34),
    }


def world_edges():
    return [
        ("logo", "auth", "enter account"),
        ("auth", "register", "create account"),
        ("auth", "play_hub", "login success"),
        ("logo", "settings", "system"),
        ("logo", "update", "patch notes"),
        ("logo", "quit", "quit game"),
        ("play_hub", "create", "new character"),
        ("play_hub", "char_sellsword", "select hero"),
        ("play_hub", "char_scout", "select hero"),
        ("play_hub", "char_slot3", "empty slot"),
        ("settings", "mfa", "security / MFA"),
    ]


def to_screen(world_xy, cam_xy):
    wx, wy = world_xy
    cx, cy = cam_xy
    return int(W / 2 + (wx - cx)), int(H / 2 + (wy - cy))


def draw_background(draw: ImageDraw.ImageDraw, pal):
    draw.rectangle((0, 0, W, H), fill=pal["bg"])
    for y in range(0, H, 96):
        draw.line((0, y, W, y), fill=(236, 238, 242, 255), width=1)


def draw_logo_text(draw: ImageDraw.ImageDraw, pal):
    draw.text((W // 2, 52), "Children of Ikphelion", anchor="mm", font=F_H1, fill=pal["ink"])


def palette_for_pass(pass_no: int):
    return PAL_SHADOW if pass_no % 2 == 1 else PAL_BLOOD


def draw_bw_background(draw: ImageDraw.ImageDraw, seed: int):
    rng = Random(seed)
    draw.rectangle((0, 0, W, H), fill=PAL_MONO["bg"])
    for y in range(0, H, 96):
        draw.line((0, y, W, y), fill=PAL_MONO["bg_line"], width=1)
    for _ in range(520):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        c = 250 if rng.random() > 0.5 else 239
        a = rng.randint(16, 42)
        draw.point((x, y), fill=(c, c, c, a))


def noisy_blob_points(cx: int, cy: int, r: int, count: int, seed: int):
    rng = Random(seed)
    pts = []
    for i in range(count):
        ang = (2 * math.pi * i) / count
        wave = 0.08 * math.sin(ang * 7) + 0.05 * math.cos(ang * 5)
        jitter = rng.uniform(-0.08, 0.08)
        rr = r * (1.0 + wave + jitter)
        pts.append((int(cx + math.cos(ang) * rr), int(cy + math.sin(ang) * rr)))
    return pts


def draw_hifi_shadow_blob(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, seed: int):
    outer = noisy_blob_points(cx, cy, r, 96, seed)
    draw.polygon(outer, fill=PAL_MONO["blob_outer"], outline=(0, 0, 0, 255))
    for i, col in enumerate([PAL_MONO["blob_mid"], PAL_MONO["blob_inner"]], start=1):
        s = 1.0 - (0.08 * i)
        pts = []
        for x, y in outer:
            pts.append((int(cx + (x - cx) * s), int(cy + (y - cy) * s)))
        draw.polygon(pts, fill=col)
    # soft sheen
    draw.ellipse((cx - r + 48, cy - r + 36, cx + 12, cy - r + 132), fill=(255, 255, 255, 18))
    # pixel texture
    rng = Random(seed + 333)
    for _ in range(800):
        px = rng.randint(cx - r + 14, cx + r - 14)
        py = rng.randint(cy - r + 14, cy + r - 14)
        if (px - cx) ** 2 + (py - cy) ** 2 > (r - 20) ** 2:
            continue
        s = rng.choice([1, 2, 2, 3])
        tint = rng.choice([(8, 9, 12, 100), (58, 61, 74, 65), (90, 94, 108, 36)])
        draw.rectangle((px, py, px + s, py + s), fill=tint)


def edge_start_on_blob(cx: int, cy: int, r: int, angle_deg: float):
    a = math.radians(angle_deg)
    return int(cx + math.cos(a) * (r - 6)), int(cy + math.sin(a) * (r - 6))


def draw_route_edge(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, angle_deg: float, label: str, active: bool = True):
    sx, sy = edge_start_on_blob(cx, cy, r, angle_deg)
    a = math.radians(angle_deg)
    ex = int(sx + math.cos(a) * 162)
    ey = int(sy + math.sin(a) * 162)
    col = PAL_MONO["edge"] if active else PAL_MONO["edge_soft"]
    draw.line((sx, sy, ex, ey), fill=col, width=5)
    # arrow cap
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    tip = (ex, ey)
    l = (int(ex - ux * 14 + px * 8), int(ey - uy * 14 + py * 8))
    rr = (int(ex - ux * 14 - px * 8), int(ey - uy * 14 - py * 8))
    draw.polygon([tip, l, rr], fill=col)
    # edge label chip
    tw = max(102, len(label) * 8 + 20)
    th = 30
    lx = int(sx + math.cos(a) * 92)
    ly = int(sy + math.sin(a) * 92)
    chip_fill = PAL_MONO["chip"] if active else (230, 231, 235, 255)
    text_fill = PAL_MONO["ink_soft"] if active else PAL_MONO["disabled"]
    draw.rounded_rectangle((lx - tw // 2, ly - th // 2, lx + tw // 2, ly + th // 2), radius=8, fill=chip_fill, outline=PAL_MONO["chip_border"], width=1)
    draw.text((lx, ly), label, anchor="mm", font=F_SM, fill=text_fill)


def draw_node_content_shell(draw: ImageDraw.ImageDraw, cx: int, cy: int, w: int, h: int):
    box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    draw.rounded_rectangle(box, radius=14, fill=PAL_MONO["panel"], outline=PAL_MONO["panel_border"], width=2)
    return box


def draw_field(draw: ImageDraw.ImageDraw, x0: int, y0: int, w: int, label: str):
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + 34), radius=7, fill=(241, 243, 247, 255), outline=PAL_MONO["panel_border"], width=1)
    draw.text((x0 + 12, y0 + 17), label, anchor="lm", font=F_TX, fill=PAL_MONO["ink_soft"])


def draw_button(draw: ImageDraw.ImageDraw, x0: int, y0: int, w: int, text: str, enabled: bool = True):
    if enabled:
        fill = PAL_MONO["button"]
        text_fill = PAL_MONO["button_text"]
        outline = PAL_MONO["edge"]
    else:
        fill = (208, 210, 218, 255)
        text_fill = (232, 233, 237, 255)
        outline = (186, 189, 197, 255)
    draw.rounded_rectangle((x0, y0, x0 + w, y0 + 36), radius=8, fill=fill, outline=outline, width=1)
    draw.text((x0 + w // 2, y0 + 18), text, anchor="mm", font=F_TX, fill=text_fill)


def draw_mini_graph(draw: ImageDraw.ImageDraw, box, muted: bool = False):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, fill=(244, 245, 249, 255), outline=PAL_MONO["panel_border"], width=1)
    for x in range(x0 + 24, x1 - 12, 44):
        draw.line((x, y0 + 14, x, y1 - 12), fill=(223, 226, 233, 255), width=1)
    for y in range(y0 + 14, y1 - 12, 42):
        draw.line((x0 + 14, y, x1 - 12, y), fill=(223, 226, 233, 255), width=1)
    col = (92, 98, 116, 255) if not muted else (165, 170, 182, 255)
    node = (58, 128, 106, 102, 170, 126, 230, 162, 274, 118, 314, 174, 350, 102)
    points = [(x0 + node[i], y0 + node[i + 1]) for i in range(0, len(node), 2)]
    links = [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (2, 6)]
    for a, b in links:
        draw.line((points[a][0], points[a][1], points[b][0], points[b][1]), fill=col, width=3)
    for i, (nx, ny) in enumerate(points):
        fill = (28, 30, 38, 255) if not muted else (150, 154, 166, 255)
        if i in {0, 6} and not muted:
            fill = (46, 49, 61, 255)
        draw.ellipse((nx - 10, ny - 10, nx + 10, ny + 10), fill=fill, outline=(235, 236, 240, 255), width=1)


def draw_zoom_node_scene(title: str, mode: str, edges: list[tuple[float, str, bool]], seed: int):
    img = Image.new("RGBA", (W, H), PAL_MONO["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_bw_background(d, seed)
    cx, cy, r = W // 2, H // 2 + 18, 314
    draw_hifi_shadow_blob(d, cx, cy, r, seed + 17)
    d.text((cx, 44), "COI", anchor="mm", font=F_H1, fill=(34, 35, 45, 255))
    d.text((cx, 76), "Children of Ikphelion", anchor="mm", font=F_TX, fill=(64, 66, 74, 255))
    for ang, lbl, active in edges:
        draw_route_edge(d, cx, cy, r, ang, lbl, active)

    shell = draw_node_content_shell(d, cx, cy, 560, 450)
    x0, y0, x1, y1 = shell
    d.text((x0 + 18, y0 + 18), title, font=F_H2, fill=PAL_MONO["ink"])

    if mode == "boot":
        d.text((cx, cy - 32), "COI", anchor="mm", font=F_H1, fill=PAL_MONO["ink"])
        d.text((cx, cy + 12), "Click center node to reveal routes", anchor="mm", font=F_TX, fill=PAL_MONO["ink_soft"])
    elif mode == "logo":
        d.text((x0 + 22, y0 + 62), "Choose a route by clicking an edge label.", font=F_TX, fill=PAL_MONO["ink_soft"])
        d.text((x0 + 22, y0 + 88), "Auth gates access to Play Hub.", font=F_TX, fill=PAL_MONO["ink_soft"])
        d.text((x0 + 22, y0 + 132), "Routes:", font=F_TX, fill=PAL_MONO["ink"])
        for idx, txt in enumerate(["enter account", "patch notes", "system", "quit"]):
            d.text((x0 + 36, y0 + 162 + idx * 28), f"- {txt}", font=F_TX, fill=PAL_MONO["ink_soft"])
    elif mode == "auth":
        draw_field(d, x0 + 18, y0 + 56, 524, "Email")
        draw_field(d, x0 + 18, y0 + 98, 524, "Password")
        draw_field(d, x0 + 18, y0 + 140, 524, "MFA (optional)")
        draw_button(d, x0 + 18, y0 + 186, 524, "Login")
        d.text((x0 + 18, y0 + 236), "On success, camera travels to Play Hub node.", font=F_SM, fill=PAL_MONO["ink_soft"])
    elif mode == "register":
        draw_field(d, x0 + 18, y0 + 56, 524, "Display Name")
        draw_field(d, x0 + 18, y0 + 98, 524, "Email")
        draw_field(d, x0 + 18, y0 + 140, 524, "Password")
        draw_button(d, x0 + 18, y0 + 186, 524, "Create Account")
        d.text((x0 + 18, y0 + 236), "After register, return via edge route to Auth.", font=F_SM, fill=PAL_MONO["ink_soft"])
    elif mode == "play_empty":
        d.text((x0 + 18, y0 + 56), "Roster", font=F_TX, fill=PAL_MONO["ink"])
        d.rounded_rectangle((x0 + 18, y0 + 82, x0 + 188, y0 + 320), radius=8, fill=(241, 243, 247, 255), outline=PAL_MONO["panel_border"], width=1)
        d.text((x0 + 30, y0 + 104), "No character selected", font=F_SM, fill=PAL_MONO["ink_soft"])
        draw_mini_graph(d, (x0 + 202, y0 + 82, x1 - 18, y0 + 320), muted=True)
        draw_button(d, x0 + 18, y0 + 336, 168, "Save Build", enabled=False)
        draw_button(d, x0 + 196, y0 + 336, 168, "Play", enabled=False)
    elif mode == "play_selected":
        d.text((x0 + 18, y0 + 56), "Roster", font=F_TX, fill=PAL_MONO["ink"])
        d.rounded_rectangle((x0 + 18, y0 + 82, x0 + 188, y0 + 320), radius=8, fill=(241, 243, 247, 255), outline=PAL_MONO["panel_border"], width=1)
        d.rounded_rectangle((x0 + 28, y0 + 102, x0 + 178, y0 + 132), radius=7, fill=(33, 35, 44, 255), outline=PAL_MONO["edge"], width=1)
        d.text((x0 + 40, y0 + 117), "Sellsword", font=F_SM, fill=(246, 248, 250, 255))
        d.rounded_rectangle((x0 + 28, y0 + 142, x0 + 178, y0 + 172), radius=7, fill=(234, 236, 240, 255), outline=PAL_MONO["panel_border"], width=1)
        d.text((x0 + 40, y0 + 157), "Scout", font=F_SM, fill=PAL_MONO["ink_soft"])
        draw_mini_graph(d, (x0 + 202, y0 + 82, x1 - 18, y0 + 320))
        d.text((x0 + 202, y0 + 338), "Node: Core  |  Routes: Resolve, Dexterity, Vitality", font=F_SM, fill=PAL_MONO["ink_soft"])
        draw_button(d, x0 + 18, y0 + 364, 168, "Save Build", enabled=True)
        draw_button(d, x0 + 196, y0 + 364, 168, "Play", enabled=True)
    elif mode == "create":
        draw_field(d, x0 + 18, y0 + 56, 524, "Character Name")
        draw_field(d, x0 + 18, y0 + 98, 524, "Sellsword")
        draw_field(d, x0 + 18, y0 + 140, 524, "Male")
        d.text((x0 + 18, y0 + 194), "Archetype starts at Core and branches to Resolve/Vitality.", font=F_SM, fill=PAL_MONO["ink_soft"])
        draw_mini_graph(d, (x0 + 18, y0 + 216, x1 - 18, y0 + 370))
        draw_button(d, x0 + 18, y0 + 382, 524, "Create Character", enabled=True)
    elif mode == "system":
        d.text((x0 + 18, y0 + 60), "Audio", font=F_TX, fill=PAL_MONO["ink"])
        for i, (name, width) in enumerate([("Master", 360), ("Music", 300), ("Effects", 340), ("Interface", 280)]):
            yy = y0 + 92 + i * 42
            d.text((x0 + 18, yy - 10), name, font=F_SM, fill=PAL_MONO["ink_soft"])
            d.rounded_rectangle((x0 + 100, yy - 4, x0 + 502, yy + 4), radius=3, fill=(214, 217, 225, 255), outline=PAL_MONO["panel_border"], width=1)
            d.rounded_rectangle((x0 + 100, yy - 4, x0 + 100 + width, yy + 4), radius=3, fill=PAL_MONO["button"], outline=PAL_MONO["button"], width=1)
        d.rounded_rectangle((x0 + 18, y0 + 274, x0 + 256, y0 + 316), radius=8, fill=(241, 243, 247, 255), outline=PAL_MONO["panel_border"], width=1)
        d.text((x0 + 32, y0 + 294), "MFA: ON", font=F_TX, fill=PAL_MONO["ink"])
        draw_button(d, x0 + 264, y0 + 280, 132, "Refresh QR", enabled=False)
        draw_button(d, x0 + 404, y0 + 280, 138, "Copy URI", enabled=False)
    elif mode == "update":
        draw_field(d, x0 + 18, y0 + 56, 524, "Build: v1.0.157")
        d.rounded_rectangle((x0 + 18, y0 + 98, x1 - 18, y0 + 342), radius=9, fill=(242, 244, 248, 255), outline=PAL_MONO["panel_border"], width=1)
        for i, line in enumerate([
            "- Graph navigation is node-native.",
            "- Auth now gates Play hub access.",
            "- Menus render inside focused nodes.",
            "- Black/white shadow theme enabled.",
        ]):
            d.text((x0 + 30, y0 + 126 + i * 30), line, font=F_TX, fill=PAL_MONO["ink_soft"])
        draw_button(d, x0 + 18, y0 + 356, 524, "Check for Update", enabled=True)

    # Node history traversal affordance:
    # Back always returns to the previously focused node (camera pans back).
    if mode == "boot":
        draw_button(d, x0 + 18, y1 - 46, 150, "Back", enabled=False)
        d.text((x0 + 178, y1 - 27), "No previous node yet", anchor="lm", font=F_SM, fill=PAL_MONO["disabled"])
    else:
        draw_button(d, x0 + 18, y1 - 46, 150, "Back", enabled=True)
        d.text((x0 + 178, y1 - 27), "Returns to previous node", anchor="lm", font=F_SM, fill=PAL_MONO["ink_soft"])

    return img


def zoom_scene_map():
    return {
        "shadow_boot_logo_node": ("COI Node", "boot", []),
        "shadow_logo_routes_node": (
            "COI Node",
            "logo",
            [(-152, "enter account", True), (-36, "patch notes", True), (64, "system", True), (152, "quit", True)],
        ),
        "shadow_auth_node_menu": (
            "Auth Node",
            "auth",
            [(-150, "register", True), (-72, "update", True), (16, "system", True), (96, "quit", True), (156, "play (locked)", False)],
        ),
        "shadow_register_node_menu": (
            "Register Node",
            "register",
            [(-154, "auth", True), (-38, "update", True), (84, "quit", True)],
        ),
        "shadow_play_node_empty": (
            "Play Hub Node",
            "play_empty",
            [(-150, "auth", True), (-54, "create", True), (22, "settings", True), (92, "update", True), (156, "select hero", True)],
        ),
        "shadow_play_node_selected": (
            "Play Hub Node",
            "play_selected",
            [(-150, "auth", True), (-54, "create", True), (22, "settings", True), (92, "update", True), (156, "hero routes", True)],
        ),
        "shadow_create_node_menu": (
            "Create Node",
            "create",
            [(-154, "play hub", True), (-44, "archetype", True), (78, "settings", True), (154, "auth", True)],
        ),
        "shadow_system_node_menu": (
            "System Node",
            "system",
            [(-152, "security / MFA", True), (-58, "play", True), (36, "auth", True), (138, "update", True)],
        ),
        "shadow_update_node_menu": (
            "Update Node",
            "update",
            [(-152, "auth", True), (-52, "play", True), (56, "system", True), (148, "quit", True)],
        ),
    }


def render_zoom_pass(pass_no: int):
    pass_dir = OUT_ROOT / f"pass_{pass_no:02d}"
    pass_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (title, mode, edges) in zoom_scene_map().items():
        img = draw_zoom_node_scene(title, mode, edges, seed=7000 + pass_no * 53 + len(name))
        p = pass_dir / f"{name}.png"
        img.save(p)
        paths.append(p)
    contact_sheet(paths, pass_dir / "shadow_contact_sheet.png")
    write_process(pass_no, pass_dir)


def draw_graph_scene(pass_no: int, cam_xy, only_logo=False, highlight=None, logged_in=False):
    pal = palette_for_pass(pass_no)
    img = Image.new("RGBA", (W, H), pal["bg"])
    d = ImageDraw.Draw(img, "RGBA")
    draw_background(d, pal)
    if pass_no <= 2:
        draw_logo_text(d, pal)

    nodes = world_nodes()
    edges = world_edges()
    if not only_logo:
        for a, b, lbl in edges:
            p0 = to_screen((nodes[a][0], nodes[a][1]), cam_xy)
            p1 = to_screen((nodes[b][0], nodes[b][1]), cam_xy)
            # reduce label clutter on advanced passes by labeling only from central / hub routes
            if pass_no >= 3 and lbl in {"select hero", "empty slot"}:
                d.line((p0[0], p0[1], p1[0], p1[1]), fill=pal["edge"], width=4)
            else:
                draw_edge(d, p0, p1, lbl, pal)

    for name, (wx, wy, r) in nodes.items():
        if only_logo and name != "logo":
            continue
        x, y = to_screen((wx, wy), cam_xy)
        fill = pal["shadow_blob"]
        if name == highlight:
            fill = pal["accent"]
        if not logged_in and name in {"play_hub", "create", "char_sellsword", "char_scout", "char_slot3"}:
            fill = (140, 146, 160, 180)
        rough_blob(d, x, y, r, seed=9000 + len(name) * 13 + x + y + pass_no * 27, fill=fill, outline=pal["ink_soft"], pal=pal)
        label_map = {
            "char_sellsword": "Sellsword",
            "char_scout": "Scout",
            "char_slot3": "Slot 3",
            "play_hub": "Play",
        }
        label = "COI" if name == "logo" else label_map.get(name, name.replace("_", " ").title())
        # avoid label clipping for mostly offscreen nodes
        if 20 < x < W - 20 and 20 < y < H - 20:
            txt_fill = (245, 248, 252, 255) if logged_in or name not in {"play_hub", "create", "char_sellsword", "char_scout", "char_slot3"} else (226, 229, 236, 255)
            d.text((x, y), label, anchor="mm", font=F_TX, fill=txt_fill)

    if only_logo:
        d.text((W // 2, H // 2 + 90), "Click the center node to reveal the graph", anchor="mm", font=F_TX, fill=pal["ink_soft"])
    return img


def scene_boot(pass_no: int):
    return draw_graph_scene(pass_no, (0, 0), only_logo=True, highlight="logo")


def scene_reveal(pass_no: int):
    # pre-login expanded graph view
    return draw_graph_scene(pass_no, (0, 0), only_logo=False, highlight="logo", logged_in=False)


def scene_pan_to_play(pass_no: int):
    # intermediate camera move towards play_hub
    img = draw_graph_scene(pass_no, (140, -10), only_logo=False, highlight="play_hub", logged_in=True)
    d = ImageDraw.Draw(img, "RGBA")
    p0 = to_screen((0, 0), (140, -10))
    p1 = to_screen((260, -20), (140, -10))
    draw_camera_travel_hint(d, p0, p1, palette_for_pass(pass_no))
    return img


def scene_play_focus(pass_no: int):
    # play hub centered
    img = draw_graph_scene(pass_no, (260, -20), only_logo=False, highlight="play_hub", logged_in=True)
    d = ImageDraw.Draw(img, "RGBA")
    play_xy = to_screen((260, -20), (260, -20))
    draw_menu_panel(d, play_xy, "play", palette_for_pass(pass_no))
    return img


def scene_character_cluster(pass_no: int):
    # move to right character branch cluster
    img = draw_graph_scene(pass_no, (470, -70), only_logo=False, highlight="char_sellsword", logged_in=True)
    d = ImageDraw.Draw(img, "RGBA")
    create_xy = to_screen((180, 210), (470, -70))
    draw_menu_panel(d, create_xy, "create", palette_for_pass(pass_no))
    return img


def scene_auth_focus(pass_no: int):
    img = draw_graph_scene(pass_no, (-260, -120), only_logo=False, highlight="auth", logged_in=False)
    d = ImageDraw.Draw(img, "RGBA")
    auth_xy = to_screen((-260, -120), (-260, -120))
    draw_menu_panel(d, auth_xy, "auth", palette_for_pass(pass_no))
    return img


def scene_register_focus(pass_no: int):
    img = draw_graph_scene(pass_no, (-430, -60), only_logo=False, highlight="register", logged_in=False)
    d = ImageDraw.Draw(img, "RGBA")
    register_xy = to_screen((-430, -60), (-430, -60))
    draw_menu_panel(d, register_xy, "register", palette_for_pass(pass_no))
    return img


def scene_play_empty_focus(pass_no: int):
    img = draw_graph_scene(pass_no, (260, -20), only_logo=False, highlight="play_hub", logged_in=True)
    d = ImageDraw.Draw(img, "RGBA")
    play_xy = to_screen((260, -20), (260, -20))
    draw_menu_panel(d, play_xy, "play_empty", palette_for_pass(pass_no))
    return img


def scene_play_selected_focus(pass_no: int):
    img = draw_graph_scene(pass_no, (470, -70), only_logo=False, highlight="char_sellsword", logged_in=True)
    d = ImageDraw.Draw(img, "RGBA")
    selected_xy = to_screen((470, -150), (470, -70))
    draw_menu_panel(d, selected_xy, "play_selected", palette_for_pass(pass_no))
    return img


def scene_system_focus(pass_no: int):
    img = draw_graph_scene(pass_no, (-90, 250), only_logo=False, highlight="settings", logged_in=True)
    d = ImageDraw.Draw(img, "RGBA")
    settings_xy = to_screen((-90, 250), (-90, 250))
    draw_menu_panel(d, settings_xy, "system", palette_for_pass(pass_no))
    return img


def scene_update_focus(pass_no: int):
    img = draw_graph_scene(pass_no, (-360, 170), only_logo=False, highlight="update", logged_in=False)
    d = ImageDraw.Draw(img, "RGBA")
    update_xy = to_screen((-360, 170), (-360, 170))
    draw_menu_panel(d, update_xy, "update", palette_for_pass(pass_no))
    return img


def contact_sheet(paths: list[Path], out: Path):
    thumbs = []
    for p in paths:
        thumbs.append((p.stem, Image.open(p).convert("RGBA").resize((410, 230), Image.Resampling.LANCZOS)))
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    pal = PAL_SHADOW
    sheet = Image.new("RGBA", (cols * 420 + 24, rows * 272 + 24), pal["bg"])
    d = ImageDraw.Draw(sheet, "RGBA")
    for i, (name, th) in enumerate(thumbs):
        c = i % cols
        r = i // cols
        x = 12 + c * 420
        y = 12 + r * 272
        d.rounded_rectangle((x, y, x + 410, y + 230), radius=8, fill=(241, 243, 248, 255), outline=(190, 198, 212, 255), width=1)
        sheet.paste(th, (x, y), th)
        d.text((x, y + 238), f"{name}.png", font=F_TX, fill=pal["ink"])
    sheet.save(out)


def write_process(pass_no: int, pass_dir: Path):
    style = "shadow blobs" if pass_no % 2 == 1 else "blood puddles"
    if pass_no == 1:
        txt = (
            f"# Shadow Graph Pass {pass_no:02d}\n\n"
            "- Plan: Build graph-native navigation with one central logo node first, then reveal a wider node network.\n"
            "- Draw: Created custom shadow-blob pixel-style nodes, edge labels, and multi-frame camera navigation mockups.\n"
            "- Review: Readability is promising, but node text and label density need tuning.\n"
            "- Next: test blood-puddle palette and improve label legibility in pass 2.\n"
        )
    elif pass_no == 2:
        txt = (
            f"# Shadow Graph Pass {pass_no:02d}\n\n"
            "- Plan: Keep graph navigation but test blood-puddle style and improve text clarity.\n"
            "- Draw: Switched to blood palette, enlarged edge tags, and improved on-screen label safety.\n"
            "- Review: Contrast is stronger, but graph still feels crowded in hub branches.\n"
            "- Next: reduce edge-label clutter and add camera-travel affordance cues in pass 3.\n"
        )
    elif pass_no < 5:
        txt = (
            f"# Shadow Graph Pass {pass_no:02d}\n\n"
            f"- Plan: Keep `{style}` while reducing route clutter and reinforcing camera movement intent.\n"
            "- Draw: Added travel breadcrumb markers, selective edge labels, compact node naming, and explicit login-gated Play Hub flow (`logo -> auth -> play`).\n"
            "- Review: Validate that pre-login graph no longer allows direct Play routing and camera traversal still reads clearly.\n"
            "- Next: continue with focused readability + hierarchy passes.\n"
        )
    elif pass_no < 6:
        txt = (
            f"# Shadow Graph Pass {pass_no:02d}\n\n"
            "- Plan: Keep graph-native navigation but ensure each focused node shows an actual functional menu payload.\n"
            "- Draw: Added explicit menu panels for auth, register, play-empty, play-selected, create, system(MFA), and update states.\n"
            "- Review: Graph now reads as navigation + usable UI payload instead of nodes-only mockups.\n"
            "- Next: iterate on panel anchoring and visual hierarchy once flow is approved.\n"
        )
    else:
        txt = (
            f"# Shadow Graph Pass {pass_no:02d}\n\n"
            "- Plan: Move to zoomed-node UX where only one focused node is visible and routes are edge-click navigation.\n"
            "- Draw: Built high-fidelity monochrome shadow-blob node shells with in-node menus (auth/register/play/create/system/update) and route chips on edges.\n"
            "- Review: This pass aligns to node-centric navigation and removes floating side panels.\n"
            "- Next: refine edge placement density and per-node information hierarchy after review.\n"
        )
    (pass_dir / "process.md").write_text(txt, encoding="utf-8")


def render_pass(pass_no: int):
    if pass_no >= 6:
        render_zoom_pass(pass_no)
        return
    pass_dir = OUT_ROOT / f"pass_{pass_no:02d}"
    pass_dir.mkdir(parents=True, exist_ok=True)
    imgs = {
        "shadow_boot_logo_node": scene_boot(pass_no),
        "shadow_graph_revealed": scene_reveal(pass_no),
        "shadow_auth_focus_menu": scene_auth_focus(pass_no),
        "shadow_register_focus_menu": scene_register_focus(pass_no),
        "shadow_camera_pan_to_play": scene_pan_to_play(pass_no),
        "shadow_play_hub_focus": scene_play_focus(pass_no),
        "shadow_play_hub_empty_menu": scene_play_empty_focus(pass_no),
        "shadow_play_hub_selected_menu": scene_play_selected_focus(pass_no),
        "shadow_character_cluster": scene_character_cluster(pass_no),
        "shadow_system_focus_menu": scene_system_focus(pass_no),
        "shadow_update_focus_menu": scene_update_focus(pass_no),
    }
    paths = []
    for name, img in imgs.items():
        p = pass_dir / f"{name}.png"
        img.save(p)
        paths.append(p)
    contact_sheet(paths, pass_dir / "shadow_contact_sheet.png")
    write_process(pass_no, pass_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass", dest="pass_no", required=True, type=int)
    args = parser.parse_args()
    render_pass(args.pass_no)


if __name__ == "__main__":
    main()
