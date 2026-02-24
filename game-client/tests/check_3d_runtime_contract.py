#!/usr/bin/env python3
"""Validate the baseline 3D runtime/asset contract used by release packaging."""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ROOT / "game-client/scripts/world_canvas_3d.gd",
    ROOT / "game-client/scripts/character_podium_preview_3d.gd",
    ROOT / "game-client/scripts/sellsword_3d_factory.gd",
    ROOT / "tools/blender/install_blender.py",
    ROOT / "tools/blender/run_blender_headless.py",
    ROOT / "tools/blender/scripts/generate_sellsword_3d_assets.py",
]

REQUIRED_SNIPPETS = {
    ROOT / "game-client/scripts/world_canvas_3d.gd": [
        "func configure_world(",
        "func configure_runtime(",
        "func set_player_appearance(",
        "func _check_transition_trigger()",
    ],
    ROOT / "game-client/scripts/sellsword_3d_factory.gd": [
        "func create_model(",
        "func play_animation(",
        "func create_environment_asset(",
        "const GENERATED_ASSET_PATHS",
    ],
}

REQUIRED_GLBS = [
    ROOT / "assets/3d/generated/sellsword_male.glb",
    ROOT / "assets/3d/generated/sellsword_female.glb",
    ROOT / "assets/3d/generated/ground_tile_stone.glb",
    ROOT / "assets/3d/generated/foliage_grass_a.glb",
    ROOT / "assets/3d/generated/foliage_tree_dead_a.glb",
]


def fail(message: str) -> int:
    print(f"[3d-contract] FAIL: {message}")
    return 1


def main() -> int:
    for path in REQUIRED_FILES:
        if not path.exists():
            return fail(f"missing required file: {path}")

    for path, snippets in REQUIRED_SNIPPETS.items():
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                return fail(f"missing snippet '{snippet}' in {path}")

    for path in REQUIRED_GLBS:
        if not path.exists():
            return fail(f"missing generated GLB asset: {path}")
        if path.stat().st_size < 1024:
            return fail(f"generated GLB too small/invalid: {path}")

    for script in [
        ROOT / "tools/blender/install_blender.py",
        ROOT / "tools/blender/run_blender_headless.py",
        ROOT / "tools/blender/scripts/generate_sellsword_3d_assets.py",
    ]:
        py_compile.compile(str(script), doraise=True)

    print("[3d-contract] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
