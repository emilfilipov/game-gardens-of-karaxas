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
    # Tight neutral grayscale palette for a crisp black/white look.
    if v >= 246:
        return 252
    if v >= 226:
        return 238
    if v >= 204:
        return 220
    if v >= 178:
        return 194
    if v >= 152:
        return 166
    if v >= 124:
        return 136
    if v >= 96:
        return 104
    if v >= 72:
        return 76
    if v >= 48:
        return 44
    return 16


def recolor_one(src: Path, out: Path) -> None:
    rgb = Image.open(src).convert("RGB")
    gray = ImageOps.autocontrast(ImageOps.grayscale(rgb), cutoff=1)
    sat = rgb.convert("HSV").split()[1]

    gp = gray.load()
    sp = sat.load()
    w, h = gray.size
    for y in range(h):
        for x in range(w):
            g = gp[x, y]
            s = sp[x, y]

            # Darken saturated UI accents (old blue states) into strong black anchors.
            if s > 42:
                g = int(g * 0.23)
            elif s > 26:
                g = int(g * 0.55)

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
