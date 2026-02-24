#!/usr/bin/env python3
"""Run a Blender python export script in background mode.

Reads BLENDER_BIN from either environment or .tools/blender/manifest.env.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / ".tools/blender/manifest.env"


def _load_manifest_bin() -> str:
    if not MANIFEST.exists():
        return ""
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.startswith("BLENDER_BIN="):
            return line.split("=", 1)[1].strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, help="Path to blender python script")
    parser.add_argument("--", dest="passthrough", nargs="*")
    args, extras = parser.parse_known_args()

    blender_bin = os.environ.get("BLENDER_BIN", "").strip() or _load_manifest_bin()
    if not blender_bin:
        raise SystemExit("BLENDER_BIN is not configured. Run tools/blender/install_blender.py first.")

    script_path = Path(args.script).resolve()
    if not script_path.exists():
        raise SystemExit(f"script not found: {script_path}")

    cmd = [
        blender_bin,
        "--background",
        "--factory-startup",
        "--python",
        str(script_path),
    ]
    if extras:
        cmd.append("--")
        cmd.extend(extras)

    print("[blender-headless] running", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
