#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
SOURCE_INSTANCE="${SOURCE_INSTANCE:-}"
DRILL_INSTANCE="${DRILL_INSTANCE:-}"

if [[ -z "$PROJECT_ID" || -z "$SOURCE_INSTANCE" || -z "$DRILL_INSTANCE" ]]; then
  echo "Usage: PROJECT_ID=<gcp-project> SOURCE_INSTANCE=<prod-instance> DRILL_INSTANCE=<temporary-instance> $0" >&2
  exit 1
fi

echo "Starting restore drill by cloning ${SOURCE_INSTANCE} -> ${DRILL_INSTANCE}"
gcloud sql instances clone "$SOURCE_INSTANCE" "$DRILL_INSTANCE" \
  --project "$PROJECT_ID" \
  --quiet

echo "Waiting for clone operation to complete..."
gcloud sql operations wait \
  "$(gcloud sql operations list --project "$PROJECT_ID" --instance "$DRILL_INSTANCE" --limit 1 --format='value(name)')" \
  --project "$PROJECT_ID"

echo "Running connectivity check against drill instance metadata..."
gcloud sql instances describe "$DRILL_INSTANCE" --project "$PROJECT_ID" --format="yaml(state,region,databaseVersion)"

echo "Restore drill complete. Delete the drill instance when validation is done:"
echo "gcloud sql instances delete \"$DRILL_INSTANCE\" --project \"$PROJECT_ID\" --quiet"
