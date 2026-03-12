#!/usr/bin/env python3
"""Generate a simple circular player placeholder sprite PNG."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def build_circle_rgba(size: int, radius: float) -> bytes:
    center = (size - 1) / 2.0
    rows = bytearray()

    for y in range(size):
        rows.append(0)  # no filter for this scanline
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)

            # Anti-aliased edge over ~1.5 px.
            if dist <= radius - 1.5:
                alpha = 255
            elif dist >= radius + 1.5:
                alpha = 0
            else:
                blend = (radius + 1.5 - dist) / 3.0
                alpha = max(0, min(255, int(round(blend * 255))))

            # Warm bronze-ish fill with subtle radial shading.
            shade = max(0.72, min(1.0, 1.08 - dist / (radius * 1.6)))
            red = int(210 * shade)
            green = int(165 * shade)
            blue = int(108 * shade)

            rows.extend((red, green, blue, alpha))

    return bytes(rows)


def write_png(path: Path, width: int, height: int, rgba_scanlines: bytes) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(rgba_scanlines, level=9)
    png = b"".join(
        [
            signature,
            png_chunk(b"IHDR", ihdr),
            png_chunk(b"IDAT", idat),
            png_chunk(b"IEND", b""),
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def main() -> None:
    output = Path("client-app/assets/player_circle.png")
    size = 96
    pixels = build_circle_rgba(size=size, radius=34.0)
    write_png(output, size, size, pixels)
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
