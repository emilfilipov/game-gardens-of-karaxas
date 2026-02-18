#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
INSTANCE_NAME="${INSTANCE_NAME:-}"
BACKUP_START_TIME="${BACKUP_START_TIME:-03:00}"
RETAINED_BACKUPS="${RETAINED_BACKUPS:-14}"
PITR_DAYS="${PITR_DAYS:-7}"

if [[ -z "$PROJECT_ID" || -z "$INSTANCE_NAME" ]]; then
  echo "Usage: PROJECT_ID=<gcp-project> INSTANCE_NAME=<cloud-sql-instance> $0" >&2
  exit 1
fi

echo "Configuring Cloud SQL backups for ${INSTANCE_NAME} in project ${PROJECT_ID}"

gcloud sql instances patch "$INSTANCE_NAME" \
  --project "$PROJECT_ID" \
  --backup-start-time "$BACKUP_START_TIME" \
  --retained-backups-count "$RETAINED_BACKUPS" \
  --enable-point-in-time-recovery \
  --retained-transaction-log-days "$PITR_DAYS" \
  --quiet

echo "Cloud SQL backup policy updated:"
gcloud sql instances describe "$INSTANCE_NAME" \
  --project "$PROJECT_ID" \
  --format="yaml(settings.backupConfiguration)"
