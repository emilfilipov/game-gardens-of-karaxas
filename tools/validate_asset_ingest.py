#!/usr/bin/env python3
"""Validate art ingest metadata before runtime/editor consumption."""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9_\\-]+$")
CATEGORY_PATTERN = re.compile(r"^[a-z0-9_\\-]+$")


def _read_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError("file is not a valid PNG")
        header_len = struct.unpack(">I", handle.read(4))[0]
        chunk_type = handle.read(4)
        if chunk_type != b"IHDR" or header_len < 8:
            raise ValueError("missing PNG IHDR header")
        width, height = struct.unpack(">II", handle.read(8))
        return int(width), int(height)


def _validate_entry(entry: dict, repo_root: Path, errors: list[str]) -> None:
    key = str(entry.get("key", "")).strip().lower()
    category = str(entry.get("category", "")).strip().lower()
    path_text = str(entry.get("path", "")).strip()
    width = int(entry.get("width", 0))
    height = int(entry.get("height", 0))
    frame_count = int(entry.get("frame_count", 0))
    pivot_x = float(entry.get("pivot_x", -1.0))
    pivot_y = float(entry.get("pivot_y", -1.0))

    if not key or not NAME_PATTERN.match(key):
        errors.append(f"invalid key '{key}'")
    if not category or not CATEGORY_PATTERN.match(category):
        errors.append(f"asset '{key}' has invalid category '{category}'")
    if not path_text:
        errors.append(f"asset '{key}' has empty path")
        return
    if not NAME_PATTERN.match(Path(path_text).stem.replace(".", "_")):
        errors.append(f"asset '{key}' path stem '{Path(path_text).stem}' violates naming policy")

    asset_path = repo_root / path_text
    if not asset_path.exists():
        errors.append(f"asset '{key}' path does not exist: {path_text}")
        return
    if asset_path.suffix.lower() != ".png":
        errors.append(f"asset '{key}' must be PNG: {path_text}")
        return

    try:
        actual_width, actual_height = _read_png_size(asset_path)
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"asset '{key}' PNG read failed: {exc}")
        return

    if width <= 0 or height <= 0:
        errors.append(f"asset '{key}' has non-positive dimensions in manifest ({width}x{height})")
    if actual_width != width or actual_height != height:
        errors.append(
            f"asset '{key}' dimensions mismatch manifest={width}x{height} actual={actual_width}x{actual_height}"
        )
    if frame_count <= 0:
        errors.append(f"asset '{key}' frame_count must be >= 1")
    if not (0.0 <= pivot_x <= 1.0 and 0.0 <= pivot_y <= 1.0):
        errors.append(f"asset '{key}' pivot must be normalized (0..1)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ISO asset ingest manifest.")
    parser.add_argument(
        "--manifest",
        default="assets/iso_asset_manifest.json",
        help="Path to asset ingest manifest relative to repository root.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = (repo_root / args.manifest).resolve()
    if not manifest_path.exists():
        print(f"[asset-ingest] manifest not found: {manifest_path}")
        return 2

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    if not isinstance(entries, list) or not entries:
        print("[asset-ingest] entries must be a non-empty list")
        return 2

    errors: list[str] = []
    seen_keys: set[str] = set()
    for raw in entries:
        if not isinstance(raw, dict):
            errors.append("manifest entry must be an object")
            continue
        key = str(raw.get("key", "")).strip().lower()
        if key in seen_keys:
            errors.append(f"duplicate key '{key}'")
        seen_keys.add(key)
        _validate_entry(raw, repo_root, errors)

    if errors:
        print("[asset-ingest] validation failed:")
        for item in errors:
            print(f" - {item}")
        return 1

    print(f"[asset-ingest] OK ({len(entries)} assets validated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
