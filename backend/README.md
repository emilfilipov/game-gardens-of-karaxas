# Karaxas Backend

FastAPI backend for Gardens of Karaxas MMORPG account/lobby systems.

## Features (current scaffold)
- Auth: register/login/refresh/logout
- Account lobby overview
- Character create/list/select
- Chat channels/messages + websocket endpoint
- Release policy ops endpoint for forced-update gating

## Local
1. Copy `backend/.env.example` to `backend/.env` and fill values.
2. Run `backend/scripts/run_local.sh`.

## Deploy
Run `backend/scripts/deploy_cloud_run.sh` after setting env vars (or `backend/.env`).
