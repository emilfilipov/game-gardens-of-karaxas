#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

required_paths=(
  "backend/scripts/rollback_release_policy.sh"
  "backend/scripts/rollback_content_publish.sh"
  "backend/scripts/run_cloudsql_restore_drill.sh"
  "backend/scripts/configure_cloudsql_backups.sh"
  "backend/scripts/configure_cloud_armor.sh"
  "docs/PLAYTEST_HARDENING_CHECKLIST.md"
)

for path in "${required_paths[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required hardening artifact: $path" >&2
    exit 2
  fi
done

python3 -m compileall backend/app

if [[ -x ".venv/bin/python" ]]; then
  PYTHONPATH=backend .venv/bin/python -m pytest -q \
    backend/tests/test_world_entry_bridge.py \
    backend/tests/test_vertical_slice_loop.py \
    backend/tests/test_ops_runtime_health.py
else
  echo "Skipping pytest hardening subset because .venv/bin/python is missing" >&2
fi

echo "Playtest hardening baseline verification passed."
echo "Manual drills still required before external playtest:"
echo "  1. Cloud SQL restore drill using backend/scripts/run_cloudsql_restore_drill.sh"
echo "  2. Release rollback drill using backend/scripts/rollback_release_policy.sh"
echo "  3. Content publish rollback drill using backend/scripts/rollback_content_publish.sh"
