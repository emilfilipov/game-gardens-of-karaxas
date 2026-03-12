# External Playtest Hardening Checklist

## Purpose
This checklist is the mandatory readiness gate before enabling any external playtest cohort.

## Security and Abuse Controls
- [ ] Auth controls validated:
  - MFA login path tested,
  - refresh/logout revocation path tested,
  - invalid token and stale session rejection verified.
- [ ] Rate-limit controls validated:
  - auth rate limit lockout,
  - chat write rate limits,
  - gameplay action nonce and action cadence guardrails.
- [ ] Internal service auth validated:
  - signed FastAPI -> world-service calls,
  - replay nonce rejection,
  - scope/service id enforcement.
- [ ] Cloud perimeter controls validated:
  - Cloud Armor policy applied for backend ingress,
  - CORS allow-list reviewed for playtest channels.

## Runtime Reliability and Observability
- [ ] Runtime alerts configured for:
  - tick lag,
  - DB latency,
  - outbox lag,
  - release feed health drift.
- [ ] Dashboard views verified:
  - `GET /ops/release/metrics` runtime health section,
  - `GET /metrics/summary` tick and queue metrics.
- [ ] `backend/scripts/check_world_runtime_alerts.sh` returns expected status in staging.

## Rollback and Backup Drills
- [ ] Cloud SQL backup policy configured (`backend/scripts/configure_cloudsql_backups.sh`).
- [ ] Cloud SQL restore drill executed (`backend/scripts/run_cloudsql_restore_drill.sh`).
- [ ] Release rollback drill executed (`backend/scripts/rollback_release_policy.sh`).
- [ ] Content rollback drill executed (`backend/scripts/rollback_content_publish.sh`).
- [ ] Release artifact retention verified at latest 3 builds.

## Release and Incident Preparedness
- [ ] Patch notes template prepared for current cycle only.
- [ ] Incident severity matrix and response owner list updated.
- [ ] Communication path prepared for playtest outage notices.
- [ ] Fallback mode decision documented (pause playtest vs rollback vs read-only mode).

## Automation Gate
Run before sign-off:

```bash
backend/scripts/validate_playtest_hardening.sh
```

## Sign-Off Record
Create/update a monthly drill report under `docs/playtest-drills/` with:
- date/time,
- operator,
- environment,
- checklist status,
- drill output references,
- follow-up actions.
