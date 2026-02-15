#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "$ENV_FILE" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    eval "$(ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
import shlex
from pathlib import Path

path = Path(os.environ["ENV_FILE"])
for raw in path.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    print(f"export {key}={shlex.quote(value)}")
PY
)"
  else
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
fi

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required env var: ${name}" >&2
    exit 1
  fi
}

require_var PROJECT_ID
require_var REGION
require_var SERVICE_NAME
require_var CLOUD_SQL_INSTANCE
require_var AR_REPO
require_var IMAGE_NAME
require_var JWT_SECRET
require_var OPS_API_TOKEN
require_var DB_NAME
require_var DB_USER
require_var DB_PASSWORD

DB_PORT="${DB_PORT:-5432}"
DB_SSLMODE="${DB_SSLMODE:-disable}"
DB_CONNECT_TIMEOUT="${DB_CONNECT_TIMEOUT:-5}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
JWT_ISSUER="${JWT_ISSUER:-karaxas}"
JWT_AUDIENCE="${JWT_AUDIENCE:-karaxas-client}"
JWT_ACCESS_TTL_MINUTES="${JWT_ACCESS_TTL_MINUTES:-15}"
JWT_REFRESH_TTL_DAYS="${JWT_REFRESH_TTL_DAYS:-30}"
VERSION_GRACE_MINUTES_DEFAULT="${VERSION_GRACE_MINUTES_DEFAULT:-5}"
SKIP_BOOTSTRAP="${SKIP_BOOTSTRAP:-0}"

DB_HOST="/cloudsql/${CLOUD_SQL_INSTANCE}"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI not found. Install gcloud and try again." >&2
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Install Docker and try again." >&2
  exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null

if [[ "$SKIP_BOOTSTRAP" != "1" ]]; then
  gcloud services enable run.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com >/dev/null

  PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='get(projectNumber)')"
  RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:${RUN_SA}" \
    --role "roles/cloudsql.client" \
    --quiet >/dev/null

  if ! gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$AR_REPO" \
      --repository-format=docker \
      --location "$REGION"
  fi
fi

docker build -t "$IMAGE_URI" -f "${ROOT_DIR}/Dockerfile" "$REPO_ROOT"
docker push "$IMAGE_URI"

RUNTIME_VARS=(
  "JWT_SECRET=${JWT_SECRET}"
  "JWT_ISSUER=${JWT_ISSUER}"
  "JWT_AUDIENCE=${JWT_AUDIENCE}"
  "JWT_ACCESS_TTL_MINUTES=${JWT_ACCESS_TTL_MINUTES}"
  "JWT_REFRESH_TTL_DAYS=${JWT_REFRESH_TTL_DAYS}"
  "OPS_API_TOKEN=${OPS_API_TOKEN}"
  "VERSION_GRACE_MINUTES_DEFAULT=${VERSION_GRACE_MINUTES_DEFAULT}"
  "DB_HOST=${DB_HOST}"
  "DB_PORT=${DB_PORT}"
  "DB_NAME=${DB_NAME}"
  "DB_USER=${DB_USER}"
  "DB_PASSWORD=${DB_PASSWORD}"
  "DB_SSLMODE=${DB_SSLMODE}"
  "DB_CONNECT_TIMEOUT=${DB_CONNECT_TIMEOUT}"
)

RUNTIME_VARS_CSV="$(IFS=#; echo "${RUNTIME_VARS[*]}")"
ENV_DELIM="^#^"

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_URI" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --add-cloudsql-instances "$CLOUD_SQL_INSTANCE" \
  --set-env-vars "${ENV_DELIM}${RUNTIME_VARS_CSV}" \
  --quiet

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='get(status.url)')"
echo "Cloud Run service deployed: ${SERVICE_NAME}"
echo "Service URL: ${SERVICE_URL}"
