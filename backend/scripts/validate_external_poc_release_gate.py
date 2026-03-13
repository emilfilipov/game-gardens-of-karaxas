#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = [
    "CHECKLIST.md",
    "GO_NO_GO.md",
    "KNOWN_RISKS.md",
    "ROLLBACK_PROOF.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate external PoC release gate evidence bundle")
    parser.add_argument(
        "--gate-pointer",
        default="docs/release-gates/current_gate.json",
        help="Path to current gate pointer JSON",
    )
    return parser.parse_args()


def require_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required gate file: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Gate file is empty: {path}")
    return text


def main() -> int:
    args = parse_args()
    pointer_path = Path(args.gate_pointer)
    payload = json.loads(require_text(pointer_path))

    gate_id = str(payload.get("gate_id", "")).strip()
    gate_date = str(payload.get("gate_date", "")).strip()
    bundle_dir_raw = str(payload.get("bundle_dir", "")).strip()
    if not gate_id or not gate_date or not bundle_dir_raw:
        raise ValueError(f"Pointer file missing gate_id/gate_date/bundle_dir: {pointer_path}")

    bundle_dir = Path(bundle_dir_raw)
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        raise FileNotFoundError(f"Gate bundle directory missing: {bundle_dir}")

    for filename in REQUIRED_FILES:
        file_path = bundle_dir / filename
        text = require_text(file_path)
        if gate_date not in text:
            raise ValueError(f"Gate date {gate_date} not found in {file_path}")

    go_no_go = require_text(bundle_dir / "GO_NO_GO.md")
    if "Decision: GO" not in go_no_go and "Decision: NO-GO" not in go_no_go:
        raise ValueError("GO_NO_GO.md must include either 'Decision: GO' or 'Decision: NO-GO'")

    rollback = require_text(bundle_dir / "ROLLBACK_PROOF.md")
    if "Rollback Trigger Thresholds" not in rollback:
        raise ValueError("ROLLBACK_PROOF.md must include 'Rollback Trigger Thresholds' section")

    checklist = require_text(bundle_dir / "CHECKLIST.md")
    if "Status: PASS" not in checklist:
        raise ValueError("CHECKLIST.md must include 'Status: PASS' entries")

    print(f"External PoC release gate validated: {gate_id} ({gate_date})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
