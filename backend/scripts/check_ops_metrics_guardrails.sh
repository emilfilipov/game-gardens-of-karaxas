#!/usr/bin/env bash
set -euo pipefail

OPS_BASE_URL="${OPS_BASE_URL:-}"
OPS_TOKEN="${OPS_TOKEN:-}"
MAX_DRAIN_ACTIVE="${MAX_DRAIN_ACTIVE:-1}"
MAX_PERSIST_FAILED="${MAX_PERSIST_FAILED:-0}"
MAX_RATE_LIMIT_BLOCKED_KEYS="${MAX_RATE_LIMIT_BLOCKED_KEYS:-200}"

if [[ -z "$OPS_BASE_URL" || -z "$OPS_TOKEN" ]]; then
  echo "Usage: OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> $0" >&2
  exit 1
fi

json="$(curl -fsS \
  -H "x-ops-token: ${OPS_TOKEN}" \
  "${OPS_BASE_URL%/}/ops/release/metrics")"

drain_active="$(python3 -c 'import json,sys;print(int(json.load(sys.stdin).get("publish_drain",{}).get("drain_events_active",0)))' <<<"$json")"
persist_failed="$(python3 -c 'import json,sys;print(int(json.load(sys.stdin).get("publish_drain",{}).get("drain_persist_failed_total",0)))' <<<"$json")"
blocked_keys="$(python3 -c 'import json,sys;print(int(json.load(sys.stdin).get("rate_limiter",{}).get("blocked_keys",0)))' <<<"$json")"

if (( drain_active > MAX_DRAIN_ACTIVE )); then
  echo "Guardrail failed: active drains ${drain_active} > ${MAX_DRAIN_ACTIVE}" >&2
  exit 2
fi
if (( persist_failed > MAX_PERSIST_FAILED )); then
  echo "Guardrail failed: publish drain persist failures ${persist_failed} > ${MAX_PERSIST_FAILED}" >&2
  exit 3
fi
if (( blocked_keys > MAX_RATE_LIMIT_BLOCKED_KEYS )); then
  echo "Guardrail failed: blocked rate-limit keys ${blocked_keys} > ${MAX_RATE_LIMIT_BLOCKED_KEYS}" >&2
  exit 4
fi

echo "Ops metrics guardrails OK."
