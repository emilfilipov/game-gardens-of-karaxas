#!/usr/bin/env python3
"""Validate the baseline 2D runtime/tooling contract used by release packaging."""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ROOT / "game-client/scripts/client_shell.gd",
    ROOT / "game-client/scripts/world_canvas.gd",
    ROOT / "game-client/scripts/character_podium_preview.gd",
    ROOT / "game-client/scripts/skill_tree_graph.gd",
    ROOT / "tools/generate_sellsword_sprite_pack.py",
    ROOT / "designer-client/designer_tool.py",
]

REQUIRED_SNIPPETS = {
    ROOT / "game-client/scripts/client_shell.gd": [
        'const CHARACTER_PODIUM_PREVIEW_SCENE = preload("res://scripts/character_podium_preview.gd")',
        'const SKILL_TREE_GRAPH_SCENE = preload("res://scripts/skill_tree_graph.gd")',
        'world_renderer_mode: String = "2d"',
        "func _build_account_screen() -> VBoxContainer:",
    ],
    ROOT / "game-client/scripts/world_canvas.gd": [
        "func configure_world(",
        "func configure_runtime(",
        "func set_player_appearance(",
        "func _resolve_actor_frame(",
    ],
    ROOT / "tools/generate_sellsword_sprite_pack.py": [
        "BASE_FRAME_SIZE = 512",
        "FRAME_SIZE = 512",
        'DIRECTIONS = ["E", "W"]',
    ],
}

FORBIDDEN_SNIPPETS = {
    ROOT / "game-client/scripts/client_shell.gd": [
        "WORLD_CANVAS_3D_SCENE",
        "character_podium_preview_3d.gd",
    ],
}

REQUIRED_GENERATED_ASSETS = [
    ROOT / "assets/characters/sellsword_v1/catalog.json",
    ROOT / "assets/characters/sellsword_v1/sheets/sellsword_male_idle_2dir_8f_512.png",
    ROOT / "assets/characters/sellsword_v1/sheets/sellsword_female_idle_2dir_8f_512.png",
]


def fail(message: str) -> int:
    print(f"[2d-contract] FAIL: {message}")
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

    for path, snippets in FORBIDDEN_SNIPPETS.items():
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet in content:
                return fail(f"forbidden snippet '{snippet}' in {path}")

    for path in REQUIRED_GENERATED_ASSETS:
        if not path.exists():
            return fail(f"missing generated 2D asset: {path}")
        if path.stat().st_size < 1024:
            return fail(f"generated 2D asset too small/invalid: {path}")

    for script in [
        ROOT / "tools/generate_sellsword_sprite_pack.py",
        ROOT / "designer-client/designer_tool.py",
    ]:
        py_compile.compile(str(script), doraise=True)

    print("[2d-contract] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
