#!/usr/bin/env python3
"""Generate Children of Ikphelion sellsword v1 sprite pack.

Outputs:
- Runtime sheets (PNG + metadata JSON) for male/female, 8 directions.
- Layered-ready source slices for future equipment overlays.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "assets/characters/sellsword_v1"
SHEETS_DIR = PACK_ROOT / "sheets"
LAYERS_DIR = PACK_ROOT / "layers"

BASE_FRAME_SIZE = 160
FRAME_SIZE = 640
DIRECTIONS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
ANIMATIONS = {
    "idle": {"frames": 8, "fps": 8},
    "walk": {"frames": 8, "fps": 10},
    "run": {"frames": 8, "fps": 14},
    "attack": {"frames": 8, "fps": 12},
    "cast": {"frames": 8, "fps": 12},
    "hurt": {"frames": 6, "fps": 12},
    "death": {"frames": 8, "fps": 10},
    "sit_crossed_legs": {"frames": 6, "fps": 6},
    "sit_kneel": {"frames": 6, "fps": 6},
}


PALETTE = {
    "outline": (18, 14, 13, 255),
    "brigandine": (117, 80, 48, 255),
    "brigandine_mid": (98, 68, 41, 255),
    "brigandine_shade": (72, 49, 30, 255),
    "cloth": (63, 108, 86, 255),
    "cloth_mid": (53, 88, 72, 255),
    "cloth_shade": (42, 69, 56, 255),
    "belt": (112, 74, 45, 255),
    "belt_dark": (79, 49, 31, 255),
    "boot": (28, 24, 27, 255),
    "boot_highlight": (51, 45, 50, 255),
    "metal": (176, 165, 151, 255),
    "metal_shadow": (120, 112, 103, 255),
    "accent_warm": (194, 132, 67, 255),
    "cloak": (40, 48, 61, 255),
    "cloak_shadow": (28, 35, 46, 255),
}

GENDER_TINTS = {
    "male": {
        "skin": (228, 192, 166, 255),
        "hair": (61, 40, 28, 255),
        "hair_light": (87, 58, 40, 255),
    },
    "female": {
        "skin": (236, 197, 176, 255),
        "hair": (74, 45, 31, 255),
        "hair_light": (103, 64, 44, 255),
    },
}


def _ensure_dirs() -> None:
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in SHEETS_DIR.glob("*.png"):
        stale.unlink()


def _dir_profile(direction: str) -> Dict[str, int]:
    table = {
        "S": {"lean": 0, "depth": 0, "side": 0},
        "SW": {"lean": -2, "depth": 1, "side": -1},
        "W": {"lean": -4, "depth": 2, "side": -2},
        "NW": {"lean": -2, "depth": 3, "side": -1},
        "N": {"lean": 0, "depth": 4, "side": 0},
        "NE": {"lean": 2, "depth": 3, "side": 1},
        "E": {"lean": 4, "depth": 2, "side": 2},
        "SE": {"lean": 2, "depth": 1, "side": 1},
    }
    return table.get(direction, table["S"])


def _motion(anim: str, frame: int, frame_count: int) -> Dict[str, float]:
    t = (frame % frame_count) / float(max(frame_count, 1))
    swing = math.sin(t * math.tau)
    pulse = math.sin((t * math.tau) * 2.0)

    if anim == "idle":
        return {"bob": pulse * 0.4, "stride": 0.0, "arm": swing * 0.5, "torso": 0.0}
    if anim == "walk":
        return {"bob": abs(swing) * 1.4, "stride": swing * 3.0, "arm": -swing * 2.3, "torso": swing * 0.6}
    if anim == "run":
        return {"bob": abs(swing) * 2.2, "stride": swing * 4.8, "arm": -swing * 3.2, "torso": swing * 1.1}
    if anim == "attack":
        strike = math.sin(min(1.0, t * 1.3) * math.pi)
        return {"bob": strike * 0.8, "stride": strike * 3.6, "arm": strike * 5.0, "torso": strike * 1.5}
    if anim == "cast":
        cast = math.sin(t * math.pi)
        return {"bob": cast * 0.5, "stride": 0.0, "arm": cast * 4.0, "torso": 0.0}
    if anim == "hurt":
        hit = math.sin(t * math.pi)
        return {"bob": -hit * 0.6, "stride": 0.0, "arm": -hit * 2.0, "torso": -hit * 2.4}
    if anim == "death":
        d = t
        return {"bob": d * 4.0, "stride": d * 2.0, "arm": d * 1.5, "torso": d * 12.0}
    if anim == "sit_crossed_legs":
        breathe = math.sin(t * math.tau) * 0.25
        return {"bob": breathe, "stride": 0.0, "arm": 0.0, "torso": 0.0}
    if anim == "sit_kneel":
        breathe = math.sin(t * math.tau) * 0.25
        return {"bob": breathe, "stride": 0.0, "arm": 0.0, "torso": 0.0}
    return {"bob": 0.0, "stride": 0.0, "arm": 0.0, "torso": 0.0}


def _draw_layered_character(gender: str, anim: str, direction: str, frame: int, frame_count: int) -> Image.Image:
    canvas = BASE_FRAME_SIZE
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    profile = _dir_profile(direction)
    mot = _motion(anim, frame, frame_count)
    tint = GENDER_TINTS[gender]

    def _lerp_color(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], t: float) -> Tuple[int, int, int, int]:
        clamped = max(0.0, min(1.0, t))
        return tuple(int(round(a[idx] + (b[idx] - a[idx]) * clamped)) for idx in range(4))

    def _paint_vertical_gradient(
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        top: Tuple[int, int, int, int],
        mid: Tuple[int, int, int, int],
        bottom: Tuple[int, int, int, int],
    ) -> None:
        y0_i = int(min(y0, y1))
        y1_i = int(max(y0, y1))
        x0_i = int(min(x0, x1))
        x1_i = int(max(x0, x1))
        h = max(1, y1_i - y0_i)
        for y in range(y0_i, y1_i + 1):
            t = (y - y0_i) / float(h)
            row_color = _lerp_color(top, mid, t * 2.0) if t < 0.5 else _lerp_color(mid, bottom, (t - 0.5) * 2.0)
            draw.line((x0_i, y, x1_i, y), fill=row_color)

    cx = canvas // 2 + profile["lean"] * 2
    ground_y = int(canvas * 0.865)
    bob = int(round(mot["bob"] * 1.8))
    torso_tilt = int(round(mot["torso"] * 1.2))
    stride = int(round(mot["stride"] * 1.5))
    arm_swing = int(round(mot["arm"] * 1.4))

    leg_h = int(canvas * 0.29)
    torso_h = int(canvas * 0.31)
    torso_w = int(canvas * 0.35) - profile["depth"] * 2
    shoulder_w = torso_w + int(canvas * 0.08)
    head_w = int(canvas * 0.23) - profile["depth"]
    head_h = int(canvas * 0.19)

    seated = anim in {"sit_crossed_legs", "sit_kneel"}
    dead = anim == "death"
    hurt = anim == "hurt"

    if dead:
        ground_y += int(canvas * 0.04)
    if seated:
        ground_y -= int(canvas * 0.07)

    hip_y = ground_y - leg_h - bob
    torso_top = hip_y - torso_h + max(0, torso_tilt)
    shoulder_y = torso_top + int(canvas * 0.05)
    head_top = torso_top - head_h + (2 if hurt else 0)
    torso_left = cx - torso_w // 2
    torso_right = torso_left + torso_w
    shoulder_left = cx - shoulder_w // 2
    shoulder_right = shoulder_left + shoulder_w

    # Cloak/backdrop layer.
    if not seated and not dead:
        draw.rounded_rectangle(
            (shoulder_left - 4, shoulder_y + 4, shoulder_right + 4, hip_y + int(canvas * 0.14)),
            int(canvas * 0.04),
            fill=PALETTE["cloak_shadow"],
        )
        draw.rounded_rectangle(
            (
                shoulder_left - 2 + profile["side"],
                shoulder_y + 8,
                shoulder_right + 2 + profile["side"],
                hip_y + int(canvas * 0.12),
            ),
            int(canvas * 0.04),
            fill=PALETTE["cloak"],
        )

    # Legs/boots.
    if seated:
        if anim == "sit_crossed_legs":
            draw.rounded_rectangle(
                (cx - int(canvas * 0.16), ground_y - int(canvas * 0.10), cx + int(canvas * 0.16), ground_y - 2),
                int(canvas * 0.03),
                fill=PALETTE["cloth_shade"],
            )
            draw.rounded_rectangle(
                (cx - int(canvas * 0.10), ground_y - int(canvas * 0.08), cx + int(canvas * 0.10), ground_y - 1),
                int(canvas * 0.03),
                fill=PALETTE["boot"],
            )
        else:
            draw.rounded_rectangle(
                (cx - int(canvas * 0.12), ground_y - int(canvas * 0.15), cx + int(canvas * 0.12), ground_y - 2),
                int(canvas * 0.03),
                fill=PALETTE["cloth_shade"],
            )
            draw.rounded_rectangle(
                (cx - int(canvas * 0.08), ground_y - int(canvas * 0.10), cx + int(canvas * 0.08), ground_y - 1),
                int(canvas * 0.02),
                fill=PALETTE["boot"],
            )
    elif dead:
        draw.rounded_rectangle(
            (cx - int(canvas * 0.20), ground_y - int(canvas * 0.10), cx + int(canvas * 0.20), ground_y - 2),
            int(canvas * 0.03),
            fill=PALETTE["cloth_shade"],
        )
        draw.rounded_rectangle(
            (cx + int(canvas * 0.08), ground_y - int(canvas * 0.09), cx + int(canvas * 0.21), ground_y - 1),
            int(canvas * 0.02),
            fill=PALETTE["boot"],
        )
    else:
        shin_w = int(canvas * 0.09)
        left_leg_x = cx - int(canvas * 0.11) - stride // 2
        right_leg_x = cx + int(canvas * 0.02) + stride // 2
        _paint_vertical_gradient(
            left_leg_x,
            hip_y + 1,
            left_leg_x + shin_w,
            ground_y - int(canvas * 0.06),
            PALETTE["cloth"],
            PALETTE["cloth_mid"],
            PALETTE["cloth_shade"],
        )
        _paint_vertical_gradient(
            right_leg_x,
            hip_y + 1,
            right_leg_x + shin_w,
            ground_y - int(canvas * 0.06),
            PALETTE["cloth_mid"],
            PALETTE["cloth_shade"],
            PALETTE["cloth_shade"],
        )
        draw.rounded_rectangle(
            (left_leg_x - 1, ground_y - int(canvas * 0.06), left_leg_x + shin_w + 1, ground_y - 1),
            int(canvas * 0.02),
            fill=PALETTE["boot"],
        )
        draw.rounded_rectangle(
            (right_leg_x - 1, ground_y - int(canvas * 0.06), right_leg_x + shin_w + 1, ground_y - 1),
            int(canvas * 0.02),
            fill=PALETTE["boot"],
        )
        draw.line(
            (left_leg_x + 1, ground_y - int(canvas * 0.04), left_leg_x + shin_w - 2, ground_y - int(canvas * 0.04)),
            fill=PALETTE["boot_highlight"],
            width=1,
        )
        draw.line(
            (right_leg_x + 1, ground_y - int(canvas * 0.04), right_leg_x + shin_w - 2, ground_y - int(canvas * 0.04)),
            fill=PALETTE["boot_highlight"],
            width=1,
        )

    # Torso leather brigandine.
    draw.rounded_rectangle((torso_left, torso_top, torso_right, hip_y + 2), int(canvas * 0.05), fill=PALETTE["brigandine"])
    _paint_vertical_gradient(
        torso_left + 2,
        torso_top + 2,
        torso_right - 2,
        hip_y - 1,
        PALETTE["brigandine"],
        PALETTE["brigandine_mid"],
        PALETTE["brigandine_shade"],
    )
    draw.rounded_rectangle(
        (torso_left + int(canvas * 0.06), torso_top + int(canvas * 0.11), torso_right - int(canvas * 0.06), torso_top + int(canvas * 0.16)),
        int(canvas * 0.02),
        fill=PALETTE["belt"],
    )
    draw.rectangle(
        (cx - int(canvas * 0.02), torso_top + int(canvas * 0.12), cx + int(canvas * 0.02), torso_top + int(canvas * 0.15)),
        fill=PALETTE["belt_dark"],
    )
    draw.rounded_rectangle(
        (cx - int(canvas * 0.015), torso_top + int(canvas * 0.13), cx + int(canvas * 0.015), torso_top + int(canvas * 0.145)),
        int(canvas * 0.01),
        fill=PALETTE["metal"],
    )

    # Shoulder plates.
    draw.rounded_rectangle(
        (shoulder_left, shoulder_y, shoulder_left + int(canvas * 0.11), shoulder_y + int(canvas * 0.08)),
        int(canvas * 0.025),
        fill=PALETTE["metal_shadow"],
    )
    draw.rounded_rectangle(
        (shoulder_right - int(canvas * 0.11), shoulder_y, shoulder_right, shoulder_y + int(canvas * 0.08)),
        int(canvas * 0.025),
        fill=PALETTE["metal_shadow"],
    )
    draw.line(
        (shoulder_left + 2, shoulder_y + 3, shoulder_left + int(canvas * 0.10), shoulder_y + 3),
        fill=PALETTE["metal"],
        width=1,
    )
    draw.line(
        (shoulder_right - int(canvas * 0.10), shoulder_y + 3, shoulder_right - 2, shoulder_y + 3),
        fill=PALETTE["metal"],
        width=1,
    )

    # Arms.
    if not seated and not dead:
        forearm_w = int(canvas * 0.08)
        left_arm_x = torso_left - forearm_w + 2
        right_arm_x = torso_right - 2
        left_top = shoulder_y + arm_swing
        right_top = shoulder_y - arm_swing
        _paint_vertical_gradient(
            left_arm_x,
            left_top,
            left_arm_x + forearm_w,
            left_top + int(canvas * 0.16),
            PALETTE["cloth"],
            PALETTE["cloth_mid"],
            PALETTE["cloth_shade"],
        )
        _paint_vertical_gradient(
            right_arm_x,
            right_top,
            right_arm_x + forearm_w,
            right_top + int(canvas * 0.16),
            PALETTE["cloth_mid"],
            PALETTE["cloth_shade"],
            PALETTE["cloth_shade"],
        )
        draw.rounded_rectangle(
            (left_arm_x, left_top + int(canvas * 0.11), left_arm_x + forearm_w, left_top + int(canvas * 0.17)),
            int(canvas * 0.02),
            fill=tint["skin"],
        )
        draw.rounded_rectangle(
            (right_arm_x, right_top + int(canvas * 0.11), right_arm_x + forearm_w, right_top + int(canvas * 0.17)),
            int(canvas * 0.02),
            fill=tint["skin"],
        )

    # Head.
    head_left = cx - head_w // 2
    head_right = head_left + head_w
    head_bottom = head_top + head_h
    draw.rounded_rectangle((head_left, head_top, head_right, head_bottom), int(canvas * 0.03), fill=tint["skin"])
    _paint_vertical_gradient(
        head_left + 1,
        head_top + 1,
        head_right - 1,
        head_bottom - 1,
        tint["skin"],
        tint["skin"],
        _lerp_color(tint["skin"], (106, 84, 74, 255), 0.20),
    )

    # Hair (rugged look).
    hair_pad = int(canvas * 0.02) if gender == "female" else int(canvas * 0.01)
    draw.rounded_rectangle(
        (head_left - 2, head_top - 2, head_right + 2, head_top + int(canvas * 0.10) + hair_pad),
        int(canvas * 0.03),
        fill=tint["hair"],
    )
    draw.rectangle(
        (head_left + 2, head_top + int(canvas * 0.05), head_right - 2, head_top + int(canvas * 0.08) + hair_pad),
        fill=tint["hair_light"],
    )
    if gender == "female":
        draw.rectangle(
            (head_left - 2, head_top + int(canvas * 0.08), head_left + int(canvas * 0.03), head_top + int(canvas * 0.18)),
            fill=tint["hair"],
        )
        draw.rectangle(
            (head_right - int(canvas * 0.03), head_top + int(canvas * 0.08), head_right + 2, head_top + int(canvas * 0.18)),
            fill=tint["hair"],
        )
    else:
        draw.rectangle(
            (head_left + int(canvas * 0.06), head_top + int(canvas * 0.13), head_right - int(canvas * 0.06), head_top + int(canvas * 0.145)),
            fill=(98, 74, 61, 255),
        )

    # Face accents.
    eye_y = head_top + int(canvas * 0.105)
    brow = _lerp_color(tint["hair"], PALETTE["outline"], 0.35)
    draw.line((cx - int(canvas * 0.07), eye_y - 2, cx - int(canvas * 0.03), eye_y - 2), fill=brow, width=1)
    draw.line((cx + int(canvas * 0.03), eye_y - 2, cx + int(canvas * 0.07), eye_y - 2), fill=brow, width=1)
    draw.line((cx - int(canvas * 0.055), eye_y, cx - int(canvas * 0.03), eye_y), fill=PALETTE["outline"], width=1)
    draw.line((cx + int(canvas * 0.03), eye_y, cx + int(canvas * 0.055), eye_y), fill=PALETTE["outline"], width=1)
    draw.line(
        (cx - int(canvas * 0.03), head_top + int(canvas * 0.145), cx + int(canvas * 0.03), head_top + int(canvas * 0.145)),
        fill=(104, 79, 67, 255),
        width=1,
    )

    # Decorative studs and warm accents on armor.
    stud_y = torso_top + int(canvas * 0.08)
    draw.ellipse((torso_left + int(canvas * 0.09), stud_y, torso_left + int(canvas * 0.11), stud_y + int(canvas * 0.02)), fill=PALETTE["metal"])
    draw.ellipse((torso_right - int(canvas * 0.11), stud_y, torso_right - int(canvas * 0.09), stud_y + int(canvas * 0.02)), fill=PALETTE["metal"])
    draw.line(
        (torso_left + int(canvas * 0.08), torso_top + int(canvas * 0.18), torso_right - int(canvas * 0.08), torso_top + int(canvas * 0.18)),
        fill=PALETTE["accent_warm"],
        width=1,
    )

    # Rim light from upper right to strengthen readability on dark backgrounds.
    rim_alpha = 90
    draw.line(
        (torso_right - 2, torso_top + 4, torso_right - 2, hip_y - 2),
        fill=(228, 181, 121, rim_alpha),
        width=1,
    )
    draw.line(
        (head_right - 2, head_top + 2, head_right - 2, head_top + int(canvas * 0.12)),
        fill=(236, 198, 142, rim_alpha),
        width=1,
    )

    # Outline pass. Keep interior colors intact and draw border only around the silhouette.
    alpha = img.split()[-1]
    expanded = alpha.filter(ImageFilter.MaxFilter(size=3))
    edge_mask = ImageChops.subtract(expanded, alpha)
    outline_img = Image.new("RGBA", img.size, PALETTE["outline"])
    img = Image.composite(outline_img, img, edge_mask)

    if FRAME_SIZE == BASE_FRAME_SIZE:
        return img
    return img.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.NEAREST)


def _write_sheet(gender: str, anim: str, frame_count: int) -> str:
    sheet = Image.new("RGBA", (FRAME_SIZE * frame_count, FRAME_SIZE * len(DIRECTIONS)), (0, 0, 0, 0))
    for dir_index, direction in enumerate(DIRECTIONS):
        for frame in range(frame_count):
            frame_img = _draw_layered_character(gender, anim, direction, frame, frame_count)
            sheet.alpha_composite(frame_img, (frame * FRAME_SIZE, dir_index * FRAME_SIZE))
    file_name = f"sellsword_{gender}_{anim}_8dir_{frame_count}f_{FRAME_SIZE}.png"
    path = SHEETS_DIR / file_name
    sheet.save(path, "PNG")
    return file_name


def _write_layer_sources() -> None:
    # Layer placeholders for future item overlays and art iteration.
    for gender in ("male", "female"):
        layer_root = LAYERS_DIR / gender
        layer_root.mkdir(parents=True, exist_ok=True)
        for stale in layer_root.glob("*.png"):
            stale.unlink()
        base = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base)
        tint = GENDER_TINTS[gender]
        draw.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.36), int(BASE_FRAME_SIZE * 0.17), int(BASE_FRAME_SIZE * 0.64), int(BASE_FRAME_SIZE * 0.35)),
            int(BASE_FRAME_SIZE * 0.04),
            fill=tint["skin"],
        )
        draw.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.30), int(BASE_FRAME_SIZE * 0.36), int(BASE_FRAME_SIZE * 0.70), int(BASE_FRAME_SIZE * 0.66)),
            int(BASE_FRAME_SIZE * 0.05),
            fill=PALETTE["brigandine"],
        )
        draw.rectangle(
            (int(BASE_FRAME_SIZE * 0.34), int(BASE_FRAME_SIZE * 0.67), int(BASE_FRAME_SIZE * 0.66), int(BASE_FRAME_SIZE * 0.85)),
            fill=PALETTE["cloth"],
        )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            base = base.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.NEAREST)
        base.save(layer_root / "base_body.png", "PNG")

        hair = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        h = ImageDraw.Draw(hair)
        h.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.34), int(BASE_FRAME_SIZE * 0.14), int(BASE_FRAME_SIZE * 0.66), int(BASE_FRAME_SIZE * 0.27)),
            int(BASE_FRAME_SIZE * 0.03),
            fill=tint["hair"],
        )
        if gender == "female":
            h.rectangle(
                (int(BASE_FRAME_SIZE * 0.33), int(BASE_FRAME_SIZE * 0.23), int(BASE_FRAME_SIZE * 0.36), int(BASE_FRAME_SIZE * 0.37)),
                fill=tint["hair"],
            )
            h.rectangle(
                (int(BASE_FRAME_SIZE * 0.64), int(BASE_FRAME_SIZE * 0.23), int(BASE_FRAME_SIZE * 0.67), int(BASE_FRAME_SIZE * 0.37)),
                fill=tint["hair"],
            )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            hair = hair.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.NEAREST)
        hair.save(layer_root / "hair_default.png", "PNG")

        armor = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        a = ImageDraw.Draw(armor)
        a.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.30), int(BASE_FRAME_SIZE * 0.36), int(BASE_FRAME_SIZE * 0.70), int(BASE_FRAME_SIZE * 0.64)),
            int(BASE_FRAME_SIZE * 0.04),
            fill=PALETTE["brigandine_shade"],
        )
        a.rectangle(
            (int(BASE_FRAME_SIZE * 0.34), int(BASE_FRAME_SIZE * 0.47), int(BASE_FRAME_SIZE * 0.66), int(BASE_FRAME_SIZE * 0.50)),
            fill=PALETTE["belt"],
        )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            armor = armor.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.NEAREST)
        armor.save(layer_root / "armor_brigandine.png", "PNG")

        boots = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        b = ImageDraw.Draw(boots)
        b.rectangle(
            (int(BASE_FRAME_SIZE * 0.38), int(BASE_FRAME_SIZE * 0.80), int(BASE_FRAME_SIZE * 0.46), int(BASE_FRAME_SIZE * 0.86)),
            fill=PALETTE["boot"],
        )
        b.rectangle(
            (int(BASE_FRAME_SIZE * 0.54), int(BASE_FRAME_SIZE * 0.80), int(BASE_FRAME_SIZE * 0.62), int(BASE_FRAME_SIZE * 0.86)),
            fill=PALETTE["boot"],
        )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            boots = boots.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.NEAREST)
        boots.save(layer_root / "boots_leather.png", "PNG")


def _write_catalog(files_by_gender: Dict[str, Dict[str, str]]) -> None:
    payload: Dict[str, object] = {
        "schema_version": 1,
        "pack": "sellsword_v1",
        "frame_size": FRAME_SIZE,
        "directions": DIRECTIONS,
        "models": {},
    }
    for gender in ("male", "female"):
        appearance_key = f"human_{gender}"
        anim_rows: Dict[str, object] = {}
        for anim, meta in ANIMATIONS.items():
            anim_rows[anim] = {
                "sheet": f"sheets/{files_by_gender[gender][anim]}",
                "frames": int(meta["frames"]),
                "fps": int(meta["fps"]),
            }
        payload["models"][appearance_key] = {
            "preset": "sellsword",
            "gender": gender,
            "animations": anim_rows,
        }
    (PACK_ROOT / "catalog.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    _ensure_dirs()
    _write_layer_sources()
    files_by_gender: Dict[str, Dict[str, str]] = {"male": {}, "female": {}}
    for gender in ("male", "female"):
        for anim, meta in ANIMATIONS.items():
            files_by_gender[gender][anim] = _write_sheet(gender, anim, int(meta["frames"]))
    _write_catalog(files_by_gender)
    print(f"[sellsword-pack] generated pack at {PACK_ROOT}")


if __name__ == "__main__":
    main()
