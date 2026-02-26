#!/usr/bin/env python3
"""Generate black/white themed variants from concept_art/ui_concept_*.png.

This is a pure visual recolor pass: no layout edits, no structure changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import math

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "concept_art"
OUT_DIR = SRC_DIR / "ui_concept_blackwhite"


def quantize_gray(v: int) -> int:
    # Neutral grayscale ramp biased toward light surfaces and crisp dark accents.
    if v >= 248:
        return 252
    if v >= 232:
        return 244
    if v >= 216:
        return 236
    if v >= 198:
        return 226
    if v >= 178:
        return 212
    if v >= 152:
        return 194
    if v >= 132:
        return 170
    if v >= 108:
        return 142
    if v >= 84:
        return 110
    if v >= 60:
        return 82
    if v >= 38:
        return 52
    return 14


def _is_blue_accent(hue: int, sat: int, val: int) -> bool:
    # Only high-saturation accent blues should collapse into deep black.
    return 130 <= hue <= 195 and sat >= 70 and val <= 238


def _curve_base_tone(gray_v: int) -> int:
    # Lift mid-tones so backgrounds stay airy in monochrome.
    return int((gray_v / 255.0) ** 0.9 * 255)


def _title_band_contrast(y: int, h: int, g: int, base_gray: int) -> int:
    # Recover visual hierarchy in the top banner/title region.
    top_band = int(h * 0.18)
    if y > top_band:
        return g
    # Keep header background light; force dark text/linework to stay visible.
    if base_gray < 130:
        return max(8, int(g * 0.30))
    return max(228, g)


def _neutral_surface_lift(sat: int, g: int) -> int:
    if sat < 20 and g > 150:
        return min(252, int(g * 1.08 + 6))
    return g


def _accent_darkening(hue: int, sat: int, val: int, g: int) -> int:
    if _is_blue_accent(hue, sat, val):
        if sat >= 58:
            return int(g * 0.16)
        if sat >= 44:
            return int(g * 0.30)
        return int(g * 0.55)
    # Keep non-blue dark saturated spots strong, but avoid crushing neutral surfaces.
    if sat >= 65 and val < 120:
        return int(g * 0.40)
    if 130 <= hue <= 195 and sat >= 45 and val <= 180:
        return int(g * 0.62)
    return g


def recolor_one(src: Path, out: Path) -> None:
    rgb = Image.open(src).convert("RGB")
    gray = ImageOps.autocontrast(ImageOps.grayscale(rgb), cutoff=1)
    hue, sat, val = rgb.convert("HSV").split()

    gp = gray.load()
    hp = hue.load()
    sp = sat.load()
    vp = val.load()
    w, h = gray.size
    for y in range(h):
        for x in range(w):
            base = gp[x, y]
            g = _curve_base_tone(base)
            hh = hp[x, y]
            s = sp[x, y]
            vv = vp[x, y]

            if y > int(h * 0.18):
                g = _accent_darkening(hh, s, vv, g)
            g = _neutral_surface_lift(s, g)
            g = _title_band_contrast(y, h, g, base)

            gp[x, y] = quantize_gray(g)

    out.parent.mkdir(parents=True, exist_ok=True)
    gray.convert("RGB").save(out)


def contact_sheet(paths: Iterable[Path], out: Path) -> None:
    images = [Image.open(p).convert("RGB") for p in paths]
    cols = 3
    cell_w = 430
    cell_h = 250
    rows = math.ceil(len(images) / cols)
    canvas = Image.new("RGB", (cell_w * cols, cell_h * rows), "#ffffff")
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    for i, (img, path) in enumerate(zip(images, paths)):
        r = i // cols
        c = i % cols
        x0 = c * cell_w
        y0 = r * cell_h

        preview = img.copy()
        preview.thumbnail((cell_w - 16, 200))
        px = x0 + (cell_w - preview.width) // 2
        py = y0 + 8
        canvas.paste(preview, (px, py))

        d.text((x0 + 10, y0 + 214), path.name, fill="#222222", font=font)
        d.line((x0, y0 + 208, x0 + cell_w, y0 + 208), fill="#d5d5d5", width=1)
        if c > 0:
            d.line((x0, y0, x0, y0 + 208), fill="#d5d5d5", width=1)

    canvas.save(out)


def main() -> None:
    src_files = sorted(SRC_DIR.glob("ui_concept_*.png"))
    if not src_files:
        raise SystemExit("No ui_concept_*.png files found in concept_art/")

    out_files = []
    for src in src_files:
        out = OUT_DIR / src.name.replace("ui_concept_", "ui_concept_bw_")
        recolor_one(src, out)
        out_files.append(out)

    contact_sheet(out_files, OUT_DIR / "ui_concept_bw_contact_sheet.png")


if __name__ == "__main__":
    main()
