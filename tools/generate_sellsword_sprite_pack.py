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

# 2D pivot baseline: high-detail 512 sheets with two gameplay directions (left/right).
BASE_FRAME_SIZE = 512
FRAME_SIZE = 512
DIRECTIONS = ["E", "W"]
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
    "outline": (19, 16, 15, 255),
    "skin_shadow": (121, 98, 84, 255),
    "tunic": (64, 106, 89, 255),
    "tunic_shadow": (44, 75, 61, 255),
    "tunic_high": (93, 140, 118, 255),
    "leather": (118, 79, 48, 255),
    "leather_shadow": (79, 51, 33, 255),
    "leather_high": (154, 104, 64, 255),
    "metal": (186, 176, 166, 255),
    "metal_shadow": (126, 119, 113, 255),
    "metal_glint": (223, 216, 205, 255),
    "cloak": (41, 49, 63, 255),
    "cloak_shadow": (25, 32, 44, 255),
    "boot": (26, 23, 26, 255),
    "boot_high": (52, 45, 49, 255),
    "shadow": (0, 0, 0, 168),
}

GENDER_TINTS = {
    "male": {
        "skin": (230, 191, 164, 255),
        "hair": (67, 43, 29, 255),
        "hair_light": (99, 66, 45, 255),
    },
    "female": {
        "skin": (236, 199, 176, 255),
        "hair": (77, 47, 32, 255),
        "hair_light": (112, 71, 50, 255),
    },
}


def _ensure_dirs() -> None:
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in SHEETS_DIR.glob("*.png"):
        stale.unlink()


def _mix(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], t: float) -> Tuple[int, int, int, int]:
    clamped = max(0.0, min(1.0, t))
    return tuple(int(round(a[idx] + (b[idx] - a[idx]) * clamped)) for idx in range(4))


def _shade(color: Tuple[int, int, int, int], factor: float) -> Tuple[int, int, int, int]:
    return (
        int(max(0, min(255, round(color[0] * factor)))),
        int(max(0, min(255, round(color[1] * factor)))),
        int(max(0, min(255, round(color[2] * factor)))),
        color[3],
    )


def _grad_rect(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    top: Tuple[int, int, int, int],
    bottom: Tuple[int, int, int, int],
) -> None:
    ya = int(min(y0, y1))
    yb = int(max(y0, y1))
    xa = int(min(x0, x1))
    xb = int(max(x0, x1))
    span = max(1, yb - ya)
    for y in range(ya, yb + 1):
        t = (y - ya) / float(span)
        draw.line((xa, y, xb, y), fill=_mix(top, bottom, t))


def _soft_shadow(img: Image.Image, box: Tuple[int, int, int, int], alpha: int) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=(0, 0, 0, alpha))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius=max(2, BASE_FRAME_SIZE // 96))))


def _dir_profile(direction: str) -> Dict[str, float]:
    table: Dict[str, Dict[str, float]] = {
        "S": {"side": 0.0, "front": 1.0, "back": 0.0, "lean": 0.0},
        "SW": {"side": -0.55, "front": 0.7, "back": 0.0, "lean": -0.7},
        "W": {"side": -1.0, "front": 0.2, "back": 0.1, "lean": -1.3},
        "NW": {"side": -0.65, "front": 0.0, "back": 0.75, "lean": -0.8},
        "N": {"side": 0.0, "front": 0.0, "back": 1.0, "lean": 0.0},
        "NE": {"side": 0.65, "front": 0.0, "back": 0.75, "lean": 0.8},
        "E": {"side": 1.0, "front": 0.2, "back": 0.1, "lean": 1.3},
        "SE": {"side": 0.55, "front": 0.7, "back": 0.0, "lean": 0.7},
    }
    return table.get(direction, table["S"])


def _motion(anim: str, frame: int, frame_count: int) -> Dict[str, float]:
    t = (frame % frame_count) / float(max(frame_count, 1))
    swing = math.sin(t * math.tau)
    pulse = math.sin((t * math.tau) * 2.0)

    if anim == "idle":
        return {"bob": pulse * 0.45, "stride": 0.0, "arm": swing * 0.35, "torso": swing * 0.08}
    if anim == "walk":
        return {"bob": abs(swing) * 1.5, "stride": swing * 1.6, "arm": -swing * 1.6, "torso": swing * 0.35}
    if anim == "run":
        return {"bob": abs(swing) * 2.5, "stride": swing * 2.4, "arm": -swing * 2.5, "torso": swing * 0.6}
    if anim == "attack":
        strike = math.sin(min(1.0, t * 1.2) * math.pi)
        return {"bob": strike * 0.9, "stride": strike * 1.3, "arm": strike * 3.4, "torso": strike * 1.0}
    if anim == "cast":
        cast = math.sin(t * math.pi)
        return {"bob": cast * 0.4, "stride": 0.0, "arm": cast * 2.4, "torso": cast * 0.4}
    if anim == "hurt":
        hit = math.sin(t * math.pi)
        return {"bob": -hit * 0.75, "stride": 0.0, "arm": -hit * 1.4, "torso": -hit * 1.3}
    if anim == "death":
        d = t
        return {"bob": d * 3.8, "stride": d * 0.8, "arm": d * 0.6, "torso": d * 3.8}
    if anim in {"sit_crossed_legs", "sit_kneel"}:
        breathe = math.sin(t * math.tau) * 0.25
        return {"bob": breathe, "stride": 0.0, "arm": 0.0, "torso": 0.0}
    return {"bob": 0.0, "stride": 0.0, "arm": 0.0, "torso": 0.0}


def _draw_layered_character(gender: str, anim: str, direction: str, frame: int, frame_count: int) -> Image.Image:
    canvas = BASE_FRAME_SIZE
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    profile = _dir_profile(direction)
    motion = _motion(anim, frame, frame_count)
    tint = GENDER_TINTS[gender]

    unit = canvas / float(BASE_FRAME_SIZE)
    side = profile["side"]
    front = profile["front"]
    back = profile["back"]
    side_sign = 1 if side >= 0 else -1

    dead = anim == "death"
    seated = anim in {"sit_crossed_legs", "sit_kneel"}

    cx = int(canvas * 0.5 + profile["lean"] * 22 * unit)
    ground_y = int(canvas * 0.90)
    if seated:
        ground_y = int(canvas * 0.84)
    if dead:
        ground_y = int(canvas * 0.93)

    bob_px = int(round(motion["bob"] * 11 * unit))
    stride_px = int(round(motion["stride"] * 14 * unit))
    arm_px = int(round(motion["arm"] * 12 * unit))
    torso_tilt = int(round(motion["torso"] * 7 * unit))

    hip_y = ground_y - int(canvas * 0.29) - bob_px
    torso_h = int(canvas * 0.31)
    torso_w = int(canvas * (0.30 - abs(side) * 0.05))
    shoulder_w = torso_w + int(canvas * (0.10 - abs(side) * 0.03))
    head_w = int(canvas * (0.19 - abs(side) * 0.02))
    head_h = int(canvas * 0.20)

    torso_left = cx - torso_w // 2 + int(side * 15 * unit)
    torso_right = torso_left + torso_w
    torso_top = hip_y - torso_h + torso_tilt
    shoulder_y = torso_top + int(canvas * 0.06)

    head_center_x = cx + int(side * 24 * unit)
    head_top = torso_top - head_h + int(canvas * 0.01)
    head_left = head_center_x - head_w // 2
    head_right = head_left + head_w
    head_bottom = head_top + head_h

    # Grounding contact and diffuse shadow.
    shadow_w = int(canvas * (0.22 + abs(side) * 0.06 + (0.08 if dead else 0.0)))
    shadow_h = int(canvas * (0.050 + (0.012 if dead else 0.0)))
    _soft_shadow(
        img,
        (
            cx - shadow_w,
            ground_y - int(shadow_h * 0.2),
            cx + shadow_w,
            ground_y + shadow_h,
        ),
        130 if not dead else 155,
    )

    if dead:
        body_left = cx - int(canvas * 0.22)
        body_right = cx + int(canvas * 0.22)
        body_top = ground_y - int(canvas * 0.16)
        body_bottom = ground_y - int(canvas * 0.02)
        draw.rounded_rectangle(
            (body_left, body_top, body_right, body_bottom),
            int(canvas * 0.04),
            fill=PALETTE["cloak_shadow"],
        )
        _grad_rect(
            draw,
            body_left + 2,
            body_top + 2,
            body_right - 2,
            body_bottom - 2,
            _mix(PALETTE["leather"], PALETTE["leather_high"], 0.25),
            PALETTE["leather_shadow"],
        )
        draw.ellipse(
            (
                body_right - int(canvas * 0.11),
                body_top - int(canvas * 0.03),
                body_right + int(canvas * 0.05),
                body_top + int(canvas * 0.13),
            ),
            fill=tint["skin"],
        )
    else:
        leg_top = hip_y + int(canvas * 0.01)
        leg_bottom = ground_y - int(canvas * 0.055)
        leg_w = int(canvas * 0.085)
        leg_gap = int(canvas * 0.02)

        left_leg_x = cx - leg_gap - leg_w + stride_px
        right_leg_x = cx + leg_gap - stride_px
        if seated:
            leg_top = ground_y - int(canvas * 0.12)
            left_leg_x = cx - int(canvas * 0.13)
            right_leg_x = cx + int(canvas * 0.02)
            leg_bottom = ground_y - int(canvas * 0.012)

        far_leg_x = left_leg_x if side_sign > 0 else right_leg_x
        near_leg_x = right_leg_x if side_sign > 0 else left_leg_x

        _grad_rect(
            draw,
            far_leg_x,
            leg_top,
            far_leg_x + leg_w,
            leg_bottom,
            _shade(PALETTE["tunic"], 0.85),
            _shade(PALETTE["tunic_shadow"], 0.85),
        )
        _grad_rect(
            draw,
            near_leg_x,
            leg_top,
            near_leg_x + leg_w,
            leg_bottom,
            PALETTE["tunic_high"],
            PALETTE["tunic_shadow"],
        )

        boot_h = int(canvas * 0.055)
        draw.rounded_rectangle(
            (far_leg_x - 1, leg_bottom - 2, far_leg_x + leg_w + 2, leg_bottom + boot_h),
            int(canvas * 0.015),
            fill=PALETTE["boot"],
        )
        draw.rounded_rectangle(
            (near_leg_x - 1, leg_bottom - 2, near_leg_x + leg_w + 2, leg_bottom + boot_h),
            int(canvas * 0.015),
            fill=PALETTE["boot"],
        )
        draw.line(
            (near_leg_x + 3, leg_bottom + int(boot_h * 0.35), near_leg_x + leg_w - 2, leg_bottom + int(boot_h * 0.35)),
            fill=PALETTE["boot_high"],
            width=max(1, int(canvas / 340)),
        )

        # Cloak/back cloth gets stronger for back-facing directions.
        cloak_alpha = int(150 + back * 85)
        draw.rounded_rectangle(
            (
                torso_left - int(canvas * 0.05),
                shoulder_y,
                torso_right + int(canvas * 0.05),
                hip_y + int(canvas * 0.15),
            ),
            int(canvas * 0.05),
            fill=(PALETTE["cloak"][0], PALETTE["cloak"][1], PALETTE["cloak"][2], cloak_alpha),
        )

        # Torso and armor.
        draw.rounded_rectangle(
            (torso_left, torso_top, torso_right, hip_y + int(canvas * 0.01)),
            int(canvas * 0.05),
            fill=PALETTE["leather"],
        )
        _grad_rect(
            draw,
            torso_left + 2,
            torso_top + 2,
            torso_right - 2,
            hip_y,
            _mix(PALETTE["leather_high"], PALETTE["cloak"], back * 0.3),
            _mix(PALETTE["leather_shadow"], PALETTE["cloak_shadow"], back * 0.35),
        )

        belt_y = torso_top + int(canvas * 0.17)
        draw.rounded_rectangle(
            (torso_left + int(canvas * 0.04), belt_y, torso_right - int(canvas * 0.04), belt_y + int(canvas * 0.03)),
            int(canvas * 0.01),
            fill=PALETTE["leather_shadow"],
        )
        buckle_w = int(canvas * 0.026)
        draw.rounded_rectangle(
            (
                cx - buckle_w // 2,
                belt_y + int(canvas * 0.006),
                cx + buckle_w // 2,
                belt_y + int(canvas * 0.026),
            ),
            int(canvas * 0.008),
            fill=PALETTE["metal"],
        )

        # Shoulder plates.
        shoulder_left = cx - shoulder_w // 2
        shoulder_right = shoulder_left + shoulder_w
        pad_w = int(canvas * 0.11)
        pad_h = int(canvas * 0.09)
        draw.rounded_rectangle(
            (shoulder_left, shoulder_y, shoulder_left + pad_w, shoulder_y + pad_h),
            int(canvas * 0.02),
            fill=PALETTE["metal_shadow"],
        )
        draw.rounded_rectangle(
            (shoulder_right - pad_w, shoulder_y, shoulder_right, shoulder_y + pad_h),
            int(canvas * 0.02),
            fill=PALETTE["metal_shadow"],
        )
        draw.line(
            (shoulder_left + 4, shoulder_y + int(canvas * 0.014), shoulder_left + pad_w - 4, shoulder_y + int(canvas * 0.014)),
            fill=PALETTE["metal_glint"],
            width=max(1, int(canvas / 360)),
        )
        draw.line(
            (
                shoulder_right - pad_w + 4,
                shoulder_y + int(canvas * 0.014),
                shoulder_right - 4,
                shoulder_y + int(canvas * 0.014),
            ),
            fill=PALETTE["metal_glint"],
            width=max(1, int(canvas / 360)),
        )

        # Arms (draw far arm first, near arm later for depth).
        arm_w = int(canvas * 0.073)
        arm_h = int(canvas * 0.19)
        left_arm_x = torso_left - int(canvas * 0.04)
        right_arm_x = torso_right - arm_w + int(canvas * 0.04)
        left_arm_top = shoulder_y + arm_px
        right_arm_top = shoulder_y - arm_px

        far_arm_x = left_arm_x if side_sign > 0 else right_arm_x
        far_arm_top = left_arm_top if side_sign > 0 else right_arm_top
        near_arm_x = right_arm_x if side_sign > 0 else left_arm_x
        near_arm_top = right_arm_top if side_sign > 0 else left_arm_top

        _grad_rect(
            draw,
            far_arm_x,
            far_arm_top,
            far_arm_x + arm_w,
            far_arm_top + arm_h,
            _shade(PALETTE["tunic"], 0.78),
            _shade(PALETTE["tunic_shadow"], 0.72),
        )
        draw.rounded_rectangle(
            (
                far_arm_x,
                far_arm_top + int(arm_h * 0.63),
                far_arm_x + arm_w,
                far_arm_top + arm_h,
            ),
            int(canvas * 0.014),
            fill=_shade(tint["skin"], 0.86),
        )

        # Head and neck.
        neck_w = int(canvas * 0.055)
        neck_top = torso_top - int(canvas * 0.01)
        draw.rounded_rectangle(
            (
                head_center_x - neck_w // 2,
                neck_top,
                head_center_x + neck_w // 2,
                neck_top + int(canvas * 0.04),
            ),
            int(canvas * 0.01),
            fill=_shade(tint["skin"], 0.94),
        )

        draw.rounded_rectangle(
            (head_left, head_top, head_right, head_bottom),
            int(canvas * 0.04),
            fill=tint["skin"],
        )
        _grad_rect(
            draw,
            head_left + 2,
            head_top + 2,
            head_right - 2,
            head_bottom - 2,
            _mix(tint["skin"], _shade(tint["skin"], 1.07), 0.5),
            _mix(tint["skin"], PALETTE["skin_shadow"], 0.46),
        )

        # Hair block with direction-specific silhouette.
        hair_top = head_top - int(canvas * 0.018)
        hair_bottom = head_top + int(canvas * (0.10 + back * 0.07))
        draw.rounded_rectangle(
            (
                head_left - int(canvas * 0.01),
                hair_top,
                head_right + int(canvas * 0.01),
                hair_bottom,
            ),
            int(canvas * 0.03),
            fill=tint["hair"],
        )
        draw.rounded_rectangle(
            (
                head_left + int(canvas * 0.02),
                hair_top + int(canvas * 0.012),
                head_right - int(canvas * 0.02),
                hair_top + int(canvas * 0.038),
            ),
            int(canvas * 0.012),
            fill=tint["hair_light"],
        )

        # Face by orientation: front (two eyes), side (one eye + profile), back (none).
        eye_y = head_top + int(canvas * 0.108)
        if back < 0.55:
            if abs(side) > 0.38:
                eye_x = head_center_x + int(side * head_w * 0.14)
                draw.ellipse(
                    (eye_x - int(canvas * 0.006), eye_y - int(canvas * 0.004), eye_x + int(canvas * 0.006), eye_y + int(canvas * 0.004)),
                    fill=PALETTE["outline"],
                )
                nose_x = head_center_x + int(side * head_w * 0.26)
                draw.line(
                    (nose_x, eye_y + int(canvas * 0.01), nose_x + int(side_sign * canvas * 0.012), eye_y + int(canvas * 0.028)),
                    fill=_shade(PALETTE["outline"], 0.92),
                    width=max(1, int(canvas / 360)),
                )
                mouth_left = head_center_x - int(canvas * 0.01)
                draw.line(
                    (
                        mouth_left,
                        eye_y + int(canvas * 0.045),
                        mouth_left + int(side_sign * canvas * 0.03),
                        eye_y + int(canvas * 0.048),
                    ),
                    fill=_mix(PALETTE["outline"], tint["skin"], 0.40),
                    width=max(1, int(canvas / 420)),
                )
            else:
                eye_dx = int(canvas * 0.026)
                eye_w = int(canvas * 0.006)
                eye_h = int(canvas * 0.004)
                draw.ellipse((head_center_x - eye_dx - eye_w, eye_y - eye_h, head_center_x - eye_dx + eye_w, eye_y + eye_h), fill=PALETTE["outline"])
                draw.ellipse((head_center_x + eye_dx - eye_w, eye_y - eye_h, head_center_x + eye_dx + eye_w, eye_y + eye_h), fill=PALETTE["outline"])
                draw.line(
                    (head_center_x, eye_y + int(canvas * 0.006), head_center_x, eye_y + int(canvas * 0.028)),
                    fill=_mix(PALETTE["outline"], tint["skin"], 0.45),
                    width=max(1, int(canvas / 420)),
                )
                draw.line(
                    (
                        head_center_x - int(canvas * 0.016),
                        eye_y + int(canvas * 0.047),
                        head_center_x + int(canvas * 0.016),
                        eye_y + int(canvas * 0.047),
                    ),
                    fill=_mix(PALETTE["outline"], tint["skin"], 0.38),
                    width=max(1, int(canvas / 420)),
                )

        # Near arm on top.
        _grad_rect(
            draw,
            near_arm_x,
            near_arm_top,
            near_arm_x + arm_w,
            near_arm_top + arm_h,
            _mix(PALETTE["tunic_high"], PALETTE["tunic"], 0.35),
            PALETTE["tunic_shadow"],
        )
        draw.rounded_rectangle(
            (
                near_arm_x,
                near_arm_top + int(arm_h * 0.62),
                near_arm_x + arm_w,
                near_arm_top + arm_h,
            ),
            int(canvas * 0.014),
            fill=tint["skin"],
        )

        # Extra readability accents.
        draw.line(
            (torso_right - 2, torso_top + int(canvas * 0.03), torso_right - 2, hip_y - int(canvas * 0.015)),
            fill=(225, 182, 126, 95),
            width=max(1, int(canvas / 420)),
        )
        draw.line(
            (head_right - 2, head_top + int(canvas * 0.03), head_right - 2, head_top + int(canvas * 0.12)),
            fill=(238, 201, 149, 85),
            width=max(1, int(canvas / 420)),
        )

    # Outline silhouette pass.
    alpha = img.split()[-1]
    expanded = alpha.filter(ImageFilter.MaxFilter(size=3))
    edge_mask = ImageChops.subtract(expanded, alpha)
    outline_img = Image.new("RGBA", img.size, PALETTE["outline"])
    img = Image.composite(outline_img, img, edge_mask)

    if FRAME_SIZE == BASE_FRAME_SIZE:
        return img
    return img.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.LANCZOS)


def _write_sheet(gender: str, anim: str, frame_count: int) -> str:
    sheet = Image.new("RGBA", (FRAME_SIZE * frame_count, FRAME_SIZE * len(DIRECTIONS)), (0, 0, 0, 0))
    for dir_index, direction in enumerate(DIRECTIONS):
        for frame in range(frame_count):
            frame_img = _draw_layered_character(gender, anim, direction, frame, frame_count)
            sheet.alpha_composite(frame_img, (frame * FRAME_SIZE, dir_index * FRAME_SIZE))
    file_name = f"sellsword_{gender}_{anim}_{len(DIRECTIONS)}dir_{frame_count}f_{FRAME_SIZE}.png"
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
            (int(BASE_FRAME_SIZE * 0.35), int(BASE_FRAME_SIZE * 0.12), int(BASE_FRAME_SIZE * 0.65), int(BASE_FRAME_SIZE * 0.33)),
            int(BASE_FRAME_SIZE * 0.05),
            fill=tint["skin"],
        )
        draw.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.30), int(BASE_FRAME_SIZE * 0.35), int(BASE_FRAME_SIZE * 0.70), int(BASE_FRAME_SIZE * 0.70)),
            int(BASE_FRAME_SIZE * 0.06),
            fill=PALETTE["leather"],
        )
        draw.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.34), int(BASE_FRAME_SIZE * 0.70), int(BASE_FRAME_SIZE * 0.66), int(BASE_FRAME_SIZE * 0.88)),
            int(BASE_FRAME_SIZE * 0.04),
            fill=PALETTE["tunic"],
        )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            base = base.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.LANCZOS)
        base.save(layer_root / "base_body.png", "PNG")

        hair = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        h = ImageDraw.Draw(hair)
        h.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.33), int(BASE_FRAME_SIZE * 0.10), int(BASE_FRAME_SIZE * 0.67), int(BASE_FRAME_SIZE * 0.26)),
            int(BASE_FRAME_SIZE * 0.04),
            fill=tint["hair"],
        )
        if gender == "female":
            h.rounded_rectangle(
                (int(BASE_FRAME_SIZE * 0.31), int(BASE_FRAME_SIZE * 0.20), int(BASE_FRAME_SIZE * 0.36), int(BASE_FRAME_SIZE * 0.41)),
                int(BASE_FRAME_SIZE * 0.015),
                fill=tint["hair"],
            )
            h.rounded_rectangle(
                (int(BASE_FRAME_SIZE * 0.64), int(BASE_FRAME_SIZE * 0.20), int(BASE_FRAME_SIZE * 0.69), int(BASE_FRAME_SIZE * 0.41)),
                int(BASE_FRAME_SIZE * 0.015),
                fill=tint["hair"],
            )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            hair = hair.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.LANCZOS)
        hair.save(layer_root / "hair_default.png", "PNG")

        armor = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        a = ImageDraw.Draw(armor)
        a.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.30), int(BASE_FRAME_SIZE * 0.35), int(BASE_FRAME_SIZE * 0.70), int(BASE_FRAME_SIZE * 0.66)),
            int(BASE_FRAME_SIZE * 0.04),
            fill=PALETTE["leather_shadow"],
        )
        a.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.36), int(BASE_FRAME_SIZE * 0.50), int(BASE_FRAME_SIZE * 0.64), int(BASE_FRAME_SIZE * 0.54)),
            int(BASE_FRAME_SIZE * 0.01),
            fill=PALETTE["metal"],
        )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            armor = armor.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.LANCZOS)
        armor.save(layer_root / "armor_brigandine.png", "PNG")

        boots = Image.new("RGBA", (BASE_FRAME_SIZE, BASE_FRAME_SIZE), (0, 0, 0, 0))
        b = ImageDraw.Draw(boots)
        b.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.38), int(BASE_FRAME_SIZE * 0.81), int(BASE_FRAME_SIZE * 0.47), int(BASE_FRAME_SIZE * 0.88)),
            int(BASE_FRAME_SIZE * 0.014),
            fill=PALETTE["boot"],
        )
        b.rounded_rectangle(
            (int(BASE_FRAME_SIZE * 0.53), int(BASE_FRAME_SIZE * 0.81), int(BASE_FRAME_SIZE * 0.62), int(BASE_FRAME_SIZE * 0.88)),
            int(BASE_FRAME_SIZE * 0.014),
            fill=PALETTE["boot"],
        )
        if FRAME_SIZE != BASE_FRAME_SIZE:
            boots = boots.resize((FRAME_SIZE, FRAME_SIZE), resample=Image.Resampling.LANCZOS)
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
