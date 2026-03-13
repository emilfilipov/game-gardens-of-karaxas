# Operations Runbook

## Scope
Operational runbook for Ambitions of Peace Rust-first runtime/services, release channels, and backend deployment.

## Active CI/CD Workflows
- Release packaging workflow: `.github/workflows/release.yml`
- Backend deploy workflow: `.github/workflows/deploy-backend.yml`
- Rust checks workflow: `.github/workflows/rust-checks.yml`
- Security scan workflow: `.github/workflows/security-scan.yml`

## Standard Change-Set Flow
1. Implement focused change set and required documentation updates.
2. Run relevant local checks.
3. Commit and push.
4. If push includes workflow-triggering paths, monitor GitHub Actions to completion.
5. If push is docs-only and does not match workflow triggers, skip polling and report that condition.

## Release Operations
1. Confirm patch notes contain only current-cycle changes.
2. Run release prechecks (auth/session continuity + packaging tests).
3. Validate external PoC release gate evidence bundle:
   - `python backend/scripts/validate_external_poc_release_gate.py --gate-pointer docs/release-gates/current_gate.json`
4. Push workflow-triggering changes.
5. Verify published artifacts for both channels:
   - game (`win-game`)
   - designer (`win-designer`)
6. Verify release workflow uploaded `windows-installer-smoke-summary` artifact (install/update + gameplay/handoff smoke evidence).
7. Verify retention policy kept only the latest 3 versions per channel/feed/archive.

## Local PoC Bootstrap (Task 037)
### First run
1. Copy `backend/.env.example` to `backend/.env` and configure DB + auth values.
2. Run `scripts/run_local_poc_stack.sh`.
3. Confirm readiness banner and generated handoff file (`client-app/runtime/startup_handoff.local.json`).

### Reset flow
1. Stop stack (`Ctrl+C`).
2. Run `scripts/run_local_poc_stack.sh --reset-runtime`.
3. If needed, skip client launch for service-only debugging: `scripts/run_local_poc_stack.sh --no-client`.

## Failure Handling
### CI failure
1. Identify failing workflow/job.
2. Fetch failing logs (`gh run view <run-id> --log-failed`).
3. Implement focused fix.
4. Push and continue poll/fix cycle.

### Release integrity failure
1. Pause new release pushes.
2. Restore last known-good artifacts from `archive/game` or `archive/designer`.
3. Validate install/update from affected channel.
4. Publish corrective release notes and replacement build.

## Logging Surfaces
- Backend service logs: Cloud Run logs for backend service.
- World-service logs: Cloud Run logs for world-service (or local process logs in dev).
- Local install script output: PowerShell console output from `scripts/install_*.ps1`.

## Observability Dashboards
Primary runtime observability surfaces for the PoC:
- Backend ops metrics: `GET /ops/release/metrics` (authenticated via `x-ops-token`).
  - Required tiles:
    - `runtime_health.db_probe_latency_ms`
    - `runtime_health.outbox_lag.oldest_lag_seconds`
    - `runtime_health.outbox_lag.pending_count`
    - `runtime_health.release_feed.minutes_since_latest_activation`
    - `runtime_health.release_feed.update_feed_url_present`
    - `zone_runtime.world_sync.success_total`
    - `zone_runtime.world_sync.failure_total`
    - `zone_runtime.world_sync.latency_ms.p95_ms`
- World-service summary: `GET /metrics/summary`.
  - Required tiles:
    - `tick_metrics.last_tick_lag_ms`
    - `tick_metrics.max_tick_lag_ms`
    - `tick_metrics.last_tick_duration_ms`
    - `queue_depth`
    - `current_tick`

## Alert Severity Matrix
- Page-worthy alerts:
  - sustained world tick lag above threshold (`last_tick_lag_ms > 2000`),
  - backend DB probe latency above threshold (`db_probe_latency_ms > 250`),
  - outbox lag above threshold (`oldest_lag_seconds > 60`).
- Log-only alerts:
  - release feed URL missing (`update_feed_url_present=false`),
  - release feed stale beyond policy threshold.

## Alert Check Commands
- `OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> WORLD_SERVICE_BASE_URL=<world-service-url> backend/scripts/check_world_runtime_alerts.sh`
- `OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> backend/scripts/check_ops_metrics_guardrails.sh`

## Monthly Cost Guardrails
- Canonical policy: `docs/COST_GUARDRAILS.md`
- Monthly report generator:
  - `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --output docs/cost-reports/YYYY-MM-estimate.md --budget-total 80`

## External Playtest Hardening
- Checklist: `docs/PLAYTEST_HARDENING_CHECKLIST.md`
- Sign-off records: `docs/playtest-drills/`
- Automation gate: `backend/scripts/validate_playtest_hardening.sh`

## Redis Adoption Gate
- Redis adoption remains deferred until thresholds in `docs/REDIS_ADOPTION_GATE.md` are exceeded.
