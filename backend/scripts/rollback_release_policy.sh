#!/usr/bin/env bash
set -euo pipefail

OPS_BASE_URL="${OPS_BASE_URL:-}"
OPS_TOKEN="${OPS_TOKEN:-}"
LATEST_VERSION="${LATEST_VERSION:-}"
MIN_SUPPORTED_VERSION="${MIN_SUPPORTED_VERSION:-}"
LATEST_CONTENT_VERSION_KEY="${LATEST_CONTENT_VERSION_KEY:-}"
MIN_SUPPORTED_CONTENT_VERSION_KEY="${MIN_SUPPORTED_CONTENT_VERSION_KEY:-}"
UPDATE_FEED_URL="${UPDATE_FEED_URL:-}"
GRACE_MINUTES="${GRACE_MINUTES:-5}"

if [[ -z "$OPS_BASE_URL" || -z "$OPS_TOKEN" || -z "$LATEST_VERSION" ]]; then
  echo "Usage: OPS_BASE_URL=<backend-ops-url> OPS_TOKEN=<ops-token> LATEST_VERSION=<version> [MIN_SUPPORTED_VERSION=...] [LATEST_CONTENT_VERSION_KEY=...] [MIN_SUPPORTED_CONTENT_VERSION_KEY=...] [UPDATE_FEED_URL=...] [GRACE_MINUTES=5] $0" >&2
  exit 1
fi

if [[ -z "$MIN_SUPPORTED_VERSION" ]]; then
  MIN_SUPPORTED_VERSION="$LATEST_VERSION"
fi

payload="$(cat <<JSON
{
  "latest_version": "${LATEST_VERSION}",
  "min_supported_version": "${MIN_SUPPORTED_VERSION}",
  "latest_content_version_key": "${LATEST_CONTENT_VERSION_KEY}",
  "min_supported_content_version_key": "${MIN_SUPPORTED_CONTENT_VERSION_KEY}",
  "update_feed_url": "${UPDATE_FEED_URL}",
  "build_release_notes": "Emergency rollback activation",
  "user_facing_notes": "Service rollback applied.",
  "grace_minutes": ${GRACE_MINUTES}
}
JSON
)"

curl -fsS -X POST \
  -H "x-ops-token: ${OPS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "${OPS_BASE_URL%/}/ops/release/activate"

echo
echo "Release policy rollback activation sent."
