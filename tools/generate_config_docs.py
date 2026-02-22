#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "game-client/assets/config/schema/game_config.schema.json"
OUT_PATH = ROOT / "docs/CONFIG_FIELDS.md"


def main() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    required = set(schema.get("required", []))

    lines = [
        "# Config Fields",
        "",
        "Generated from `game-client/assets/config/schema/game_config.schema.json`.",
        "",
        "| Root Key | Required | Type | Description |",
        "| --- | --- | --- | --- |",
    ]

    for key in sorted(props.keys()):
        rule = props[key]
        rule_type = str(rule.get("type", "any"))
        desc = str(rule.get("description", ""))
        lines.append(f"| `{key}` | {'Yes' if key in required else 'No'} | `{rule_type}` | {desc} |")

    lines.extend([
        "",
        "## Notes",
        "- Runtime-level validation is enforced in `single_player_shell.gd`.",
        "- Keep this file in sync by running:",
        "  - `python3 tools/generate_config_docs.py`",
    ])

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
