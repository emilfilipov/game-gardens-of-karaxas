#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-}"
ACCESS_TOKEN="${ACCESS_TOKEN:-}"
CLIENT_VERSION="${CLIENT_VERSION:-0.0.0}"
CLIENT_CONTENT_VERSION_KEY="${CLIENT_CONTENT_VERSION_KEY:-unknown}"

if [[ -z "$BASE_URL" || -z "$ACCESS_TOKEN" ]]; then
  echo "Usage: BASE_URL=<backend-url> ACCESS_TOKEN=<admin-bearer-token> $0" >&2
  exit 1
fi

curl -fsS -X POST \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "X-Client-Version: ${CLIENT_VERSION}" \
  -H "X-Client-Content-Version: ${CLIENT_CONTENT_VERSION_KEY}" \
  "${BASE_URL%/}/content/versions/rollback/previous"

echo
echo "Requested rollback to previous content version."
