#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$ROOT_DIR/.venv"
RUNTIME_DIR="$ROOT_DIR/runtime/local-stack"
LOG_DIR="$RUNTIME_DIR/logs"
HANDOFF_PATH="$ROOT_DIR/client-app/runtime/startup_handoff.local.json"

BACKEND_URL="${AOP_API_BASE_URL:-http://127.0.0.1:8000}"
WORLD_URL="${AOP_WORLD_SERVICE_BASE_URL:-http://127.0.0.1:8088}"

RUN_CLIENT=1
RUN_SEED=1
RUN_BACKEND_SMOKE=1
RESET_RUNTIME=0

usage() {
  cat <<'EOF'
Usage: scripts/run_local_poc_stack.sh [options]

Options:
  --no-client            Start services and seed account, but do not launch client runtime.
  --skip-seed            Start services only (no account/character seed).
  --skip-backend-smoke   Skip backend online loop smoke harness.
  --reset-runtime        Delete generated runtime/log artifacts before start.
  -h, --help             Show this help.

This command starts world-service + backend, waits for readiness, seeds a deterministic
PoC account/character, and launches client bootstrap shell with a generated handoff file.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-client)
      RUN_CLIENT=0
      shift
      ;;
    --skip-seed)
      RUN_SEED=0
      shift
      ;;
    --skip-backend-smoke)
      RUN_BACKEND_SMOKE=0
      shift
      ;;
    --reset-runtime)
      RESET_RUNTIME=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  echo "Missing backend/.env. Copy backend/.env.example and fill values first." >&2
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Missing .venv Python at $VENV_DIR/bin/python. Create virtual env and install backend requirements." >&2
  exit 1
fi

if [[ ! -x "$HOME/.cargo/bin/cargo" ]]; then
  echo "Cargo not found at ~/.cargo/bin/cargo." >&2
  exit 1
fi

mkdir -p "$LOG_DIR" "$(dirname "$HANDOFF_PATH")"
if [[ "$RESET_RUNTIME" -eq 1 ]]; then
  rm -rf "$RUNTIME_DIR" "$ROOT_DIR/client-app/runtime"
  mkdir -p "$LOG_DIR" "$(dirname "$HANDOFF_PATH")"
fi

set -a
# shellcheck disable=SC1091
source "$BACKEND_DIR/.env"
set +a

export AOP_API_BASE_URL="$BACKEND_URL"
export AOP_CLIENT_VERSION="${AOP_CLIENT_VERSION:-dev-0.1.0}"
export AOP_CLIENT_CONTENT_VERSION_KEY="${AOP_CLIENT_CONTENT_VERSION_KEY:-runtime_gameplay_v1}"
export WORLD_SERVICE_BASE_URL="$WORLD_URL"

if [[ -z "${WORLD_SERVICE_INTERNAL_AUTH_SECRET:-}" ]]; then
  export WORLD_SERVICE_INTERNAL_AUTH_SECRET="${WORLD_SERVICE_AUTH_SECRET:-dev-only-change-me}"
fi
if [[ -z "${WORLD_SERVICE_ALLOWED_CALLER_ID:-}" ]]; then
  export WORLD_SERVICE_ALLOWED_CALLER_ID="${WORLD_SERVICE_CALLER_ID:-fastapi-control-plane}"
fi
if [[ -z "${WORLD_SERVICE_ALLOWED_SCOPES:-}" ]]; then
  export WORLD_SERVICE_ALLOWED_SCOPES="${WORLD_SERVICE_SCOPE:-world.control.mutate}"
fi
if [[ -z "${WORLD_SERVICE_REQUIRED_SCOPE:-}" ]]; then
  export WORLD_SERVICE_REQUIRED_SCOPE="${WORLD_SERVICE_SCOPE:-world.control.mutate}"
fi
if [[ -z "${WORLD_SERVICE_BIND_ADDR:-}" ]]; then
  export WORLD_SERVICE_BIND_ADDR="127.0.0.1:8088"
fi

WORLD_LOG="$LOG_DIR/world-service.log"
BACKEND_LOG="$LOG_DIR/backend.log"

WORLD_PID=""
BACKEND_PID=""

cleanup() {
  local status=$?
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$WORLD_PID" ]] && kill -0 "$WORLD_PID" 2>/dev/null; then
    kill "$WORLD_PID" >/dev/null 2>&1 || true
    wait "$WORLD_PID" >/dev/null 2>&1 || true
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

wait_for_http() {
  local url="$1"
  local label="$2"
  local attempts=120
  local sleep_seconds=1
  local i
  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[$label] ready at $url"
      return 0
    fi
    sleep "$sleep_seconds"
  done
  echo "Timed out waiting for $label at $url" >&2
  return 1
}

echo "Starting world-service..."
(
  cd "$ROOT_DIR"
  exec "$HOME/.cargo/bin/cargo" run -p world-service
) >"$WORLD_LOG" 2>&1 &
WORLD_PID=$!

wait_for_http "$WORLD_URL/readyz" "world-service"

echo "Applying backend migrations..."
(
  cd "$BACKEND_DIR"
  exec "$VENV_DIR/bin/alembic" upgrade head
) >>"$BACKEND_LOG" 2>&1

echo "Starting backend API..."
(
  cd "$BACKEND_DIR"
  exec "$VENV_DIR/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000
) >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

wait_for_http "$BACKEND_URL/health" "backend"
wait_for_http "$BACKEND_URL/health/deep" "backend-deep"

if [[ "$RUN_SEED" -eq 1 ]]; then
  echo "Seeding deterministic PoC account + character..."
  (
    cd "$ROOT_DIR"
    "$VENV_DIR/bin/python" backend/scripts/seed_local_poc_account.py \
      --base-url "$BACKEND_URL" \
      --output-handoff "$HANDOFF_PATH"
  )
fi

if [[ "$RUN_BACKEND_SMOKE" -eq 1 ]]; then
  echo "Running backend vertical-slice smoke..."
  (
    cd "$ROOT_DIR"
    "$VENV_DIR/bin/python" backend/scripts/smoke_online_loop.py --base-url "$BACKEND_URL"
  )
fi

echo ""
echo "Stack is ready."
echo "  Backend:       $BACKEND_URL"
echo "  World service: $WORLD_URL"
echo "  Backend log:   $BACKEND_LOG"
echo "  World log:     $WORLD_LOG"
echo "  Handoff file:  $HANDOFF_PATH"
echo ""
echo "Smoke references:"
echo "  Backend smoke:  python3 backend/scripts/smoke_online_loop.py --base-url $BACKEND_URL"
echo "  Client smoke:   ~/.cargo/bin/cargo run -p client-app --features bootstrap-shell -- --handoff-file $HANDOFF_PATH"

if [[ "$RUN_CLIENT" -eq 0 ]]; then
  echo "--no-client set; services stay active. Press Ctrl+C to stop."
  wait
  exit 0
fi

echo "Launching client bootstrap shell..."
(
  cd "$ROOT_DIR"
  AOP_API_BASE_URL="$BACKEND_URL" \
  AOP_CLIENT_VERSION="${AOP_CLIENT_VERSION}" \
  AOP_CLIENT_CONTENT_VERSION_KEY="${AOP_CLIENT_CONTENT_VERSION_KEY}" \
  exec "$HOME/.cargo/bin/cargo" run -p client-app --features bootstrap-shell -- --handoff-file "$HANDOFF_PATH"
)
