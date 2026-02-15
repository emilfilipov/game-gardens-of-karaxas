#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "Missing backend/.env. Copy backend/.env.example and fill values." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

alembic upgrade head
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
