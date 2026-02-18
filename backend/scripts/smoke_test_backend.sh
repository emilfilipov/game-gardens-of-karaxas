#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${BACKEND_BASE_URL:-}}"
if [[ -z "$BASE_URL" ]]; then
  echo "Usage: $0 <backend-base-url>" >&2
  exit 1
fi

base="${BASE_URL%/}"

echo "Running backend smoke tests against ${base}"

health_code="$(curl -fsS -o /tmp/gok-health.json -w '%{http_code}' "${base}/health")"
if [[ "$health_code" != "200" ]]; then
  echo "Smoke check failed: /health returned ${health_code}" >&2
  exit 1
fi

deep_code="$(curl -fsS -o /tmp/gok-health-deep.json -w '%{http_code}' "${base}/health/deep")"
if [[ "$deep_code" != "200" ]]; then
  echo "Smoke check failed: /health/deep returned ${deep_code}" >&2
  exit 1
fi

if ! grep -q '"ok"[[:space:]]*:[[:space:]]*true' /tmp/gok-health.json; then
  echo "Smoke check failed: /health payload missing ok=true" >&2
  exit 1
fi
if ! grep -q '"ok"[[:space:]]*:[[:space:]]*true' /tmp/gok-health-deep.json; then
  echo "Smoke check failed: /health/deep payload missing ok=true" >&2
  exit 1
fi

echo "Smoke checks passed."
