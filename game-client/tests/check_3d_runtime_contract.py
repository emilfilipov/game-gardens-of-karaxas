#!/usr/bin/env python3
"""Validate the baseline 3D runtime contract used by release packaging."""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ROOT / "game-client/scripts/client_shell.gd",
    ROOT / "game-client/scripts/world_canvas_3d.gd",
    ROOT / "game-client/scripts/sellsword_3d_factory.gd",
    ROOT / "game-client/scripts/skill_tree_graph.gd",
    ROOT / "designer-client/designer_tool.py",
]

REQUIRED_SNIPPETS = {
    ROOT / "game-client/scripts/client_shell.gd": [
        'const WORLD_CANVAS_3D_SCENE = preload("res://scripts/world_canvas_3d.gd")',
        'world_renderer_mode: String = "3d"',
        "func _resolve_world_renderer_mode_from_domains() -> String:",
        "GAME_TITLE = \"Plompers Arena Inc.\"",
    ],
    ROOT / "game-client/scripts/world_canvas_3d.gd": [
        "func configure_world(",
        "func configure_runtime(runtime_cfg: Dictionary) -> void:",
        "func set_player_appearance(appearance_key: String) -> void:",
        "_spawn_default_environment()",
        "_apply_player_reveal_feedback",
    ],
    ROOT / "game-client/scripts/sellsword_3d_factory.gd": [
        "_build_plomper_ball_model",
        "normalized.begins_with(\"plomper\")",
    ],
}

FORBIDDEN_SNIPPETS = {
    ROOT / "game-client/scripts/client_shell.gd": [
        'world_renderer_mode: String = "2d"',
    ],
}


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

    for path, snippets in FORBIDDEN_SNIPPETS.items():
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet in content:
                return fail(f"forbidden snippet '{snippet}' in {path}")

    for script in [
        ROOT / "designer-client/designer_tool.py",
        ROOT / "game-client/tests/check_3d_runtime_contract.py",
    ]:
        py_compile.compile(str(script), doraise=True)

    print("[3d-contract] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
