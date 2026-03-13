# Ambitions of Peace Backend (Transitional FastAPI Control Plane)

FastAPI backend for Ambitions of Peace online account/control-plane systems during migration to the Rust world-authority architecture.

## Features (current scaffold)
- Auth: register/login/refresh/logout
- Account lobby overview
- Character create/list/select
- Gameplay action resolve + real-time orchestration (`/gameplay/resolve-action`, `/gameplay/vertical-slice-loop`, `/gameplay/world-sync`, `/gameplay/battle/start`, `/gameplay/battle/command`, `/gameplay/domain-action`)
- Chat channels/messages + websocket endpoint
- Release policy ops endpoint for forced-update gating
- Ops runtime health metrics (`/ops/release/metrics`) now include DB probe latency, outbox lag, and release-feed health metadata.
- Internal world-service call signing contract (`app/services/world_service_auth.py`) for authenticated FastAPI -> Rust control-plane requests
- Character world bootstrap bridge client (`app/services/world_entry_bridge.py`) for signed FastAPI -> Rust world-entry handoff (`/internal/world-entry/bootstrap`) with compatibility fallback
- PostgreSQL outbox LISTEN/NOTIFY wake worker scaffold (`app/services/outbox_notify_worker.py`) with reconnect loop and startup/shutdown wiring

## Local
1. Copy `backend/.env.example` to `backend/.env` and fill values.
2. Run `backend/scripts/run_local.sh`.
3. For full-stack local bootstrap (world-service + backend + seed + client handoff), run repository command:
   - `scripts/run_local_poc_stack.sh`

## Deploy
Run `backend/scripts/deploy_cloud_run.sh` after setting env vars (or `backend/.env`).

## Ops Guardrails
- Configure baseline Cloud Monitoring alert policies: `backend/scripts/configure_monitoring_alerts.sh`
- Check runtime thresholds (page-worthy + log-only): `backend/scripts/check_world_runtime_alerts.sh`
- Generate monthly cost report (estimate or billing CSV mode): `backend/scripts/generate_monthly_cost_report.py`
- Validate external playtest hardening baseline: `backend/scripts/validate_playtest_hardening.sh`
- Validate external single-player PoC release gate bundle: `backend/scripts/validate_external_poc_release_gate.py`
