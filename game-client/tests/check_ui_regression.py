#!/usr/bin/env python3
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "game-client/tests/ui_golden_manifest.json"
SIGNATURE_PATH = ROOT / "game-client/tests/ui_layout_signature.txt"
SOURCES = [
    ROOT / "game-client/scripts/client_shell.gd",
    ROOT / "game-client/scripts/ui_tokens.gd",
    ROOT / "game-client/scripts/ui_components.gd",
    ROOT / "game-client/scripts/character_podium_preview.gd",
]


def fail(message: str) -> int:
    print(f"[ui-regression] FAIL: {message}")
    return 1


def normalized_text_bytes(path: Path) -> bytes:
    # Normalize line endings so Windows and Linux checkouts hash identically.
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def main() -> int:
    if not MANIFEST_PATH.exists():
        return fail(f"manifest missing: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    shell_text = (ROOT / "game-client/scripts/client_shell.gd").read_text(encoding="utf-8")

    for name in manifest.get("required_builders", []):
        if f"func {name}(" not in shell_text:
            return fail(f"missing required builder: {name}")

    for snippet in manifest.get("forbidden_snippets", []):
        if snippet in shell_text:
            return fail(f"forbidden snippet still present: {snippet}")

    for snippet in manifest.get("required_snippets", []):
        if snippet not in shell_text:
            return fail(f"required snippet missing: {snippet}")

    for raw in manifest.get("golden_images", []):
        path = ROOT / raw
        if not path.exists():
            return fail(f"golden image missing: {raw}")

    digest = hashlib.sha256()
    for path in SOURCES + [MANIFEST_PATH]:
        if not path.exists():
            return fail(f"source missing for signature: {path}")
        digest.update(normalized_text_bytes(path))
    signature = digest.hexdigest()

    update = os.getenv("UPDATE_UI_GOLDEN", "0").strip() == "1"
    if update or not SIGNATURE_PATH.exists():
        SIGNATURE_PATH.write_text(signature + "\n", encoding="utf-8")
        print(f"[ui-regression] updated signature: {signature}")
        return 0

    expected = SIGNATURE_PATH.read_text(encoding="utf-8").strip()
    if expected != signature:
        return fail(
            "UI signature mismatch. Run UPDATE_UI_GOLDEN=1 python3 game-client/tests/check_ui_regression.py to accept updated golden."
        )

    print(f"[ui-regression] PASS signature={signature}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
