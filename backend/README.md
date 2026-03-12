# Ambitions of Peace Backend (Transitional FastAPI Control Plane)

FastAPI backend for Ambitions of Peace online account/control-plane systems during migration to the Rust world-authority architecture.

## Features (current scaffold)
- Auth: register/login/refresh/logout
- Account lobby overview
- Character create/list/select
- Chat channels/messages + websocket endpoint
- Release policy ops endpoint for forced-update gating
- Internal world-service call signing contract (`app/services/world_service_auth.py`) for authenticated FastAPI -> Rust control-plane requests
- Character world bootstrap bridge client (`app/services/world_entry_bridge.py`) for signed FastAPI -> Rust world-entry handoff (`/internal/world-entry/bootstrap`) with compatibility fallback
- PostgreSQL outbox LISTEN/NOTIFY wake worker scaffold (`app/services/outbox_notify_worker.py`) with reconnect loop and startup/shutdown wiring

## Local
1. Copy `backend/.env.example` to `backend/.env` and fill values.
2. Run `backend/scripts/run_local.sh`.

## Deploy
Run `backend/scripts/deploy_cloud_run.sh` after setting env vars (or `backend/.env`).
