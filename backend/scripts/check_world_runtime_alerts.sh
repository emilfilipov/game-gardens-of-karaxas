#!/usr/bin/env bash
set -euo pipefail

OPS_BASE_URL="${OPS_BASE_URL:-}"
OPS_TOKEN="${OPS_TOKEN:-}"
WORLD_SERVICE_BASE_URL="${WORLD_SERVICE_BASE_URL:-}"

PAGE_MAX_TICK_LAG_MS="${PAGE_MAX_TICK_LAG_MS:-2000}"
PAGE_MAX_DB_LATENCY_MS="${PAGE_MAX_DB_LATENCY_MS:-250}"
PAGE_MAX_OUTBOX_LAG_SECONDS="${PAGE_MAX_OUTBOX_LAG_SECONDS:-60}"
LOG_MAX_RELEASE_FEED_STALENESS_MINUTES="${LOG_MAX_RELEASE_FEED_STALENESS_MINUTES:-10080}"

if [[ -z "$OPS_BASE_URL" || -z "$OPS_TOKEN" || -z "$WORLD_SERVICE_BASE_URL" ]]; then
  echo "Usage: OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> WORLD_SERVICE_BASE_URL=<world-service-url> $0" >&2
  exit 1
fi

ops_json="$(curl -fsS -H "x-ops-token: ${OPS_TOKEN}" "${OPS_BASE_URL%/}/ops/release/metrics")"
world_json="$(curl -fsS "${WORLD_SERVICE_BASE_URL%/}/metrics/summary")"

tick_lag_ms="$(python3 -c 'import json,sys;print(float(json.load(sys.stdin).get("tick_metrics",{}).get("last_tick_lag_ms",0.0)))' <<<"$world_json")"
db_latency_ms="$(python3 -c 'import json,sys;print(float(json.load(sys.stdin).get("runtime_health",{}).get("db_probe_latency_ms",0.0)))' <<<"$ops_json")"
outbox_lag_seconds="$(python3 -c 'import json,sys;print(float(json.load(sys.stdin).get("runtime_health",{}).get("outbox_lag",{}).get("oldest_lag_seconds",0.0)))' <<<"$ops_json")"
release_staleness_minutes="$(python3 -c 'import json,sys;value=json.load(sys.stdin).get("runtime_health",{}).get("release_feed",{}).get("minutes_since_latest_activation",0.0);print(float(value if value is not None else 0.0))' <<<"$ops_json")"
release_feed_url_present="$(python3 -c 'import json,sys;print(str(bool(json.load(sys.stdin).get("runtime_health",{}).get("release_feed",{}).get("update_feed_url_present",False))).lower())' <<<"$ops_json")"

page_failures=()
log_warnings=()

if (( $(awk "BEGIN {print ($tick_lag_ms > $PAGE_MAX_TICK_LAG_MS)}") )); then
  page_failures+=("tick_lag_ms=${tick_lag_ms}")
fi
if (( $(awk "BEGIN {print ($db_latency_ms > $PAGE_MAX_DB_LATENCY_MS)}") )); then
  page_failures+=("db_latency_ms=${db_latency_ms}")
fi
if (( $(awk "BEGIN {print ($outbox_lag_seconds > $PAGE_MAX_OUTBOX_LAG_SECONDS)}") )); then
  page_failures+=("outbox_lag_seconds=${outbox_lag_seconds}")
fi

if (( $(awk "BEGIN {print ($release_staleness_minutes > $LOG_MAX_RELEASE_FEED_STALENESS_MINUTES)}") )); then
  log_warnings+=("release_feed_staleness_minutes=${release_staleness_minutes}")
fi
if [[ "$release_feed_url_present" != "true" ]]; then
  log_warnings+=("release_feed_url_present=false")
fi

if (( ${#page_failures[@]} > 0 )); then
  echo "PAGE-WORTHY alert thresholds breached: ${page_failures[*]}" >&2
  if (( ${#log_warnings[@]} > 0 )); then
    echo "Additional log-only warnings: ${log_warnings[*]}" >&2
  fi
  exit 2
fi

if (( ${#log_warnings[@]} > 0 )); then
  echo "LOG-ONLY observability warnings: ${log_warnings[*]}"
else
  echo "Observability runtime health thresholds OK."
fi
