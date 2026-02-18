# Operations Runbook

## Rollout Phases (`CONTENT_FEATURE_PHASE`)
- `snapshot_readonly`: bootstrap/read-only content APIs; admin content writes and activation are blocked.
- `snapshot_runtime`: content write/validate allowed; activation/rollback blocked.
- `drain_enforced`: full publish flow enabled (activation + drain + forced logout).

## Publish Runbook
1. Validate target content version from `Content Versions` panel.
2. Confirm no active drain lock (`GET /ops/release/metrics` -> `publish_drain.drain_events_active == 0`).
3. Activate target content version.
4. Verify metrics:
   - active content key updated,
   - drain event started,
   - warning/forced-logout counters increasing for non-admin users.
5. Confirm admin session remains active.
6. Confirm non-admin sessions return to login and are blocked until updated.
7. Confirm release summary now reports incremented logical latest build marker for the published content version.

## Emergency Rollback Runbook
1. Trigger `POST /content/versions/rollback/previous` (admin).
2. Confirm new active key via `/content/bootstrap` and `/ops/release/metrics`.
3. Verify rollback drain event completed.
4. Validate login/gameplay on a non-admin account with the expected compatible build/content.

### Rollback Helpers
- Content rollback helper:
```bash
BASE_URL=https://<backend-url> \
ACCESS_TOKEN=<admin-access-token> \
backend/scripts/rollback_content_publish.sh
```
- Release policy rollback helper:
```bash
OPS_BASE_URL=https://<backend-url> \
OPS_TOKEN=<ops-token> \
LATEST_VERSION=<target-version> \
MIN_SUPPORTED_VERSION=<target-min> \
LATEST_CONTENT_VERSION_KEY=<content-key> \
MIN_SUPPORTED_CONTENT_VERSION_KEY=<content-key> \
UPDATE_FEED_URL=https://storage.googleapis.com/<bucket>/<prefix> \
backend/scripts/rollback_release_policy.sh
```

## Observability Endpoints
- `GET /ops/release/metrics` (ops token): active release/content, snapshot latency stats, drain counters, rate-limit counters.
- `GET /ops/release/feature-flags` (ops token): current rollout/security flags.
- `GET /ops/release/admin-audit` (ops token): append-only privileged action log.
- `GET /ops/release/security-audit` (ops token): immutable auth/session security event stream (filterable by `event_type`).

## Publish-Drain Load Probe
- Script: `backend/scripts/publish_drain_stress_probe.py`.
- Purpose: compare request status distribution and latency before/after publish drain.
- Example:
```bash
python3 backend/scripts/publish_drain_stress_probe.py \
  --base-url https://<backend-url> \
  --tokens-file tokens.txt \
  --requests 1000 \
  --concurrency 80
```

## Content Contract Compatibility
- Contract is signed by backend (`content_contract_signature`) and returned by `/content/bootstrap`.
- Launcher includes the signature in `X-Client-Content-Contract`.
- Non-admin auth is rejected with `content_contract_mismatch` when signature diverges.

## Go/No-Go Checklist
- `Deploy Backend` and `Release` workflows green.
- Post-deploy smoke checks (`/health`, `/health/deep`) green.
- No active drain lock before publish.
- Snapshot latency p95 within expected range.
- Forced logout count matches connected non-admin sessions.
- No elevated `rate_limit_exceeded`/auth error anomalies after rollout.

## Backup and Restore Drill
- Configure backup policy:
```bash
PROJECT_ID=<project-id> \
INSTANCE_NAME=<cloud-sql-instance> \
BACKUP_START_TIME=03:00 \
RETAINED_BACKUPS=14 \
PITR_DAYS=7 \
backend/scripts/configure_cloudsql_backups.sh
```
- Run restore drill (clone-based rehearsal):
```bash
PROJECT_ID=<project-id> \
SOURCE_INSTANCE=<prod-instance> \
DRILL_INSTANCE=<temporary-restore-instance> \
backend/scripts/run_cloudsql_restore_drill.sh
```

## Monitoring Alerts Bootstrap
- Create baseline Cloud Monitoring alert policies:
```bash
PROJECT_ID=<project-id> \
SERVICE_NAME=karaxas-backend \
NOTIFICATION_CHANNEL=projects/<project>/notificationChannels/<id> \
backend/scripts/configure_monitoring_alerts.sh
```
- Add guardrail probe for publish/auth anomalies (use from cron/Cloud Scheduler/Cloud Run Job):
```bash
OPS_BASE_URL=https://<backend-url> \
OPS_TOKEN=<ops-token> \
MAX_DRAIN_ACTIVE=1 \
MAX_PERSIST_FAILED=0 \
MAX_RATE_LIMIT_BLOCKED_KEYS=200 \
backend/scripts/check_ops_metrics_guardrails.sh
```
