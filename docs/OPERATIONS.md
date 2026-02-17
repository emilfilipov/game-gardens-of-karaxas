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

## Emergency Rollback Runbook
1. Trigger `POST /content/versions/rollback/previous` (admin).
2. Confirm new active key via `/content/bootstrap` and `/ops/release/metrics`.
3. Verify rollback drain event completed.
4. Validate login/gameplay on a non-admin account with the expected compatible build/content.

## Observability Endpoints
- `GET /ops/release/metrics` (ops token): active release/content, snapshot latency stats, drain counters, rate-limit counters.
- `GET /ops/release/feature-flags` (ops token): current rollout/security flags.
- `GET /ops/release/admin-audit` (ops token): append-only privileged action log.

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
- No active drain lock before publish.
- Snapshot latency p95 within expected range.
- Forced logout count matches connected non-admin sessions.
- No elevated `rate_limit_exceeded`/auth error anomalies after rollout.
