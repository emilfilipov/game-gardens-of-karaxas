# Operations Runbook (Transitional)

## Scope
Operational runbook for Ambitions of Peace during migration from legacy prototype modules to Rust-first runtime/services.

## Active CI/CD Workflows
- Release packaging workflow: `.github/workflows/release.yml`
- Backend deploy workflow: `.github/workflows/deploy-backend.yml`
- Security scan workflow: `.github/workflows/security-scan.yml`

## Standard Change-Set Flow
1. Implement focused change set and required documentation updates.
2. Run relevant local checks for changed surfaces.
3. Commit and push.
4. If push includes workflow-triggering paths, monitor GitHub Actions to completion.
5. If push is docs-only and does not match workflow triggers, skip polling and report that condition.

## Release Operations (Current)
1. Confirm patch notes contain only current-cycle changes.
2. Run release prechecks used by workflow gates.
3. Push workflow-triggering changes.
4. Verify generated artifacts in `releases/windows/` and GCS feed/archive paths.
5. Confirm retention policy keeps latest 3 feed/archive build versions.

## Failure Handling
### CI failure
1. Identify failing workflow/job.
2. Collect failing logs (`gh run view <run-id> --log-failed`).
3. Implement focused fix.
4. Push and repeat poll/fix cycle.

### Release integrity failure
1. Pause new release pushes.
2. Restore last known-good feed artifacts from archive path.
3. Validate updater behavior from installed client.
4. Publish corrective release notes and replacement build.

## Logging Surfaces
- launcher logs: `<install_root>/logs/launcher.log`
- runtime logs: `<install_root>/logs/game.log`
- updater logs: `<install_root>/logs/velopack.log`
- updater status: `<install_root>/logs/update_status.json`

## Observability Dashboards
Primary runtime observability surfaces for the PoC:
- Backend ops metrics: `GET /ops/release/metrics` (authenticated via `x-ops-token`).
  - Required dashboard tiles:
    - `runtime_health.db_probe_latency_ms`
    - `runtime_health.outbox_lag.oldest_lag_seconds`
    - `runtime_health.outbox_lag.pending_count`
    - `runtime_health.release_feed.minutes_since_latest_activation`
    - `runtime_health.release_feed.update_feed_url_present`
- World-service metrics summary: `GET /metrics/summary`.
  - Required dashboard tiles:
    - `tick_metrics.last_tick_lag_ms`
    - `tick_metrics.max_tick_lag_ms`
    - `tick_metrics.last_tick_duration_ms`
    - `queue_depth`
    - `current_tick`

## Alert Severity Matrix
- Page-worthy alerts:
  - world tick lag above threshold (`last_tick_lag_ms > 2000` for sustained checks),
  - backend DB probe latency above threshold (`db_probe_latency_ms > 250`),
  - outbox lag above threshold (`oldest_lag_seconds > 60`).
- Log-only alerts:
  - release feed URL missing (`update_feed_url_present=false`),
  - release feed staleness above policy threshold (`minutes_since_latest_activation > 10080` by default).

## Alert Check Commands
- Existing Cloud Monitoring policy script:
  - `backend/scripts/configure_monitoring_alerts.sh`
- Runtime threshold check script (page-worthy + log-only split):
  - `OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> WORLD_SERVICE_BASE_URL=<world-service-url> backend/scripts/check_world_runtime_alerts.sh`
- Existing release guardrails check:
  - `OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> backend/scripts/check_ops_metrics_guardrails.sh`

## Monthly Cost Guardrails
- Canonical policy: `docs/COST_GUARDRAILS.md`
- Monthly report generator:
  - `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --output docs/cost-reports/YYYY-MM-estimate.md --budget-total 80`
- Billing export mode:
  - `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --billing-csv <billing_export.csv> --output docs/cost-reports/YYYY-MM-report.md --budget-total 80`

## Redis Adoption Gate Reference
- Redis adoption is controlled by `docs/REDIS_ADOPTION_GATE.md`.
- Do not enable Redis-backed fanout paths unless the documented thresholds, preconditions, and rollback drill requirements are satisfied.
