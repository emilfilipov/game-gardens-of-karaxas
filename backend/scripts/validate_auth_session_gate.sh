#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "Running auth/session continuity regression gate..."
PYTHONPATH=backend "$PYTHON_BIN" -m pytest -q \
  backend/tests/test_security_edges.py \
  backend/tests/test_publish_drain.py

echo "Auth/session continuity gate passed."
