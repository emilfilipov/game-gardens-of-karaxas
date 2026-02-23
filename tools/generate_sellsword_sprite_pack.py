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

FRAME_SIZE = 96
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
    "outline": (24, 18, 16, 255),
    "brigandine": (107, 78, 56, 255),
    "brigandine_shade": (82, 59, 43, 255),
    "cloth": (66, 108, 86, 255),
    "cloth_shade": (48, 80, 63, 255),
    "belt": (98, 62, 41, 255),
    "boot": (29, 26, 28, 255),
    "metal": (160, 151, 145, 255),
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
    img = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    profile = _dir_profile(direction)
    mot = _motion(anim, frame, frame_count)
    tint = GENDER_TINTS[gender]

    cx = FRAME_SIZE // 2 + profile["lean"]
    ground_y = 82
    bob = int(round(mot["bob"]))
    torso_tilt = int(round(mot["torso"]))

    leg_h = 18
    torso_h = 23
    torso_w = 28 - profile["depth"] * 2
    head_w = 20 - profile["depth"]
    head_h = 17

    seated = anim in {"sit_crossed_legs", "sit_kneel"}
    dead = anim == "death"
    hurt = anim == "hurt"

    if dead:
        ground_y += 6
    if seated:
        ground_y -= 6

    hip_y = ground_y - leg_h - bob
    torso_top = hip_y - torso_h + max(0, torso_tilt)
    head_top = torso_top - head_h + (1 if hurt else 0)

    # Legs/boots.
    stride = int(round(mot["stride"]))
    if seated:
        if anim == "sit_crossed_legs":
            draw.rounded_rectangle((cx - 15, ground_y - 10, cx + 15, ground_y - 2), 3, fill=PALETTE["cloth_shade"])
            draw.rounded_rectangle((cx - 9, ground_y - 8, cx + 9, ground_y - 1), 3, fill=PALETTE["boot"])
        else:
            draw.rounded_rectangle((cx - 11, ground_y - 16, cx + 11, ground_y - 2), 3, fill=PALETTE["cloth_shade"])
            draw.rounded_rectangle((cx - 8, ground_y - 11, cx + 8, ground_y - 1), 2, fill=PALETTE["boot"])
    elif dead:
        draw.rounded_rectangle((cx - 18, ground_y - 8, cx + 18, ground_y - 2), 3, fill=PALETTE["cloth_shade"])
        draw.rounded_rectangle((cx + 8, ground_y - 8, cx + 18, ground_y - 2), 2, fill=PALETTE["boot"])
    else:
        left_leg_x = cx - 10 - stride // 2
        right_leg_x = cx + 2 + stride // 2
        draw.rectangle((left_leg_x, hip_y + 1, left_leg_x + 8, ground_y - 5), fill=PALETTE["cloth"])
        draw.rectangle((right_leg_x, hip_y + 1, right_leg_x + 8, ground_y - 5), fill=PALETTE["cloth_shade"])
        draw.rectangle((left_leg_x, ground_y - 5, left_leg_x + 8, ground_y - 1), fill=PALETTE["boot"])
        draw.rectangle((right_leg_x, ground_y - 5, right_leg_x + 8, ground_y - 1), fill=PALETTE["boot"])

    # Torso leather brigandine.
    torso_left = cx - torso_w // 2
    torso_right = torso_left + torso_w
    draw.rounded_rectangle((torso_left, torso_top, torso_right, hip_y + 1), 4, fill=PALETTE["brigandine"])
    draw.rectangle((torso_left + 3, torso_top + 3, torso_right - 3, hip_y - 2), fill=PALETTE["brigandine_shade"])
    draw.rectangle((torso_left + 1, torso_top + 10, torso_right - 1, torso_top + 11), fill=PALETTE["belt"])

    # Arms.
    if not seated and not dead:
        arm_swing = int(round(mot["arm"]))
        shoulder_y = torso_top + 4
        left_arm_x = torso_left - 6
        right_arm_x = torso_right - 2
        draw.rectangle((left_arm_x, shoulder_y + arm_swing, left_arm_x + 6, shoulder_y + 14 + arm_swing), fill=PALETTE["cloth"])
        draw.rectangle((right_arm_x, shoulder_y - arm_swing, right_arm_x + 6, shoulder_y + 14 - arm_swing), fill=PALETTE["cloth_shade"])
        draw.rectangle((left_arm_x, shoulder_y + 12 + arm_swing, left_arm_x + 6, shoulder_y + 16 + arm_swing), fill=tint["skin"])
        draw.rectangle((right_arm_x, shoulder_y + 12 - arm_swing, right_arm_x + 6, shoulder_y + 16 - arm_swing), fill=tint["skin"])

    # Head.
    head_left = cx - head_w // 2
    head_right = head_left + head_w
    head_bottom = head_top + head_h
    draw.rounded_rectangle((head_left, head_top, head_right, head_bottom), 4, fill=tint["skin"])

    # Hair (rugged look).
    hair_pad = 2 if gender == "female" else 1
    draw.rounded_rectangle((head_left - 1, head_top - 1, head_right + 1, head_top + 8 + hair_pad), 4, fill=tint["hair"])
    draw.rectangle((head_left + 1, head_top + 5, head_right - 1, head_top + 7 + hair_pad), fill=tint["hair_light"])
    if gender == "female":
        # Slightly longer side strands.
        draw.rectangle((head_left - 1, head_top + 8, head_left + 2, head_top + 14), fill=tint["hair"])
        draw.rectangle((head_right - 2, head_top + 8, head_right + 1, head_top + 14), fill=tint["hair"])
    else:
        # Rugged stubble.
        draw.rectangle((head_left + 4, head_top + 12, head_right - 4, head_top + 13), fill=(96, 73, 60, 255))

    # Brigandine metal clasp.
    clasp_y = torso_top + 6
    draw.rectangle((cx - 1, clasp_y, cx + 1, clasp_y + 3), fill=PALETTE["metal"])

    # Outline pass. Keep interior colors intact and draw border only around the silhouette.
    alpha = img.split()[-1]
    expanded = alpha.filter(ImageFilter.MaxFilter(size=3))
    edge_mask = ImageChops.subtract(expanded, alpha)
    outline_img = Image.new("RGBA", img.size, PALETTE["outline"])
    img = Image.composite(outline_img, img, edge_mask)

    return img


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
        base = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base)
        tint = GENDER_TINTS[gender]
        draw.rounded_rectangle((34, 16, 62, 33), 5, fill=tint["skin"])
        draw.rounded_rectangle((30, 34, 66, 62), 5, fill=PALETTE["brigandine"])
        draw.rectangle((34, 63, 62, 80), fill=PALETTE["cloth"])
        base.save(layer_root / "base_body.png", "PNG")

        hair = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
        h = ImageDraw.Draw(hair)
        h.rounded_rectangle((33, 13, 63, 26), 4, fill=tint["hair"])
        if gender == "female":
            h.rectangle((32, 22, 35, 34), fill=tint["hair"])
            h.rectangle((61, 22, 64, 34), fill=tint["hair"])
        hair.save(layer_root / "hair_default.png", "PNG")

        armor = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
        a = ImageDraw.Draw(armor)
        a.rounded_rectangle((30, 34, 66, 60), 4, fill=PALETTE["brigandine_shade"])
        a.rectangle((34, 43, 62, 45), fill=PALETTE["belt"])
        armor.save(layer_root / "armor_brigandine.png", "PNG")

        boots = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE), (0, 0, 0, 0))
        b = ImageDraw.Draw(boots)
        b.rectangle((36, 77, 44, 82), fill=PALETTE["boot"])
        b.rectangle((52, 77, 60, 82), fill=PALETTE["boot"])
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
