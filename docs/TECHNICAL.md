# Gardens of Karaxas - Technical

## Purpose
This is the single source of truth for technical architecture, stack decisions, module boundaries, deployment, and CI/CD behavior.

## Runtime and Service Stack
- Launcher/runtime UI: Kotlin (JVM) Swing launcher module (`launcher/`).
- Backend services: Python FastAPI (`backend/`).
- Database: PostgreSQL (Cloud SQL), database name `karaxas`.
- Migrations: Alembic.
- Service hosting: Google Cloud Run.

## Architecture Rules (Must Hold)
1. Gameplay/runtime logic remains decoupled from launcher/updater internals.
2. Launcher can host account/lobby UX and updater UX, but backend remains authority for auth/session/version-gating.
3. Backend services must be deployable independently from launcher releases.
4. Module boundaries remain explicit:
   - `launcher/` for desktop launcher UI and updater integration.
   - `backend/` for API/realtime/auth/social data services.

## Backend Service Shape (Current)
- Single FastAPI service (modular monolith) with:
  - REST APIs for auth, lobby, characters, chat, and ops.
  - WebSocket endpoint for realtime chat/events.
- This keeps operational complexity low while preserving future split path (`api` + `realtime`) if scale requires it.

## Data Model (Initial)
- `users`: account identity.
- `user_sessions`: refresh/session records and client version tracking.
- `release_policy`: latest/min-supported version and enforce-after timestamp.
- `characters`: user-owned character builds (stats/skills point allocations).
- `friendships`: friend graph.
- `guilds`, `guild_members`: guild presence and rank scaffolding.
- `chat_channels`, `chat_members`, `chat_messages`: global/direct/guild chat model.

## Version Gating and Forced Update Flow
- Backend stores release policy (`latest_version`, `min_supported_version`, `enforce_after`).
- Clients send `X-Client-Version` on API calls.
- If client is older than minimum after `enforce_after`, backend rejects with `426 Upgrade Required` and session revocation.
- Grace window is currently 5 minutes.

## Release Notification Integration
- Launcher release workflow posts to backend ops endpoint:
  - `POST /ops/release/activate`
  - Payload includes new version + `grace_minutes=5`.
- Backend broadcasts `force_update` to connected websocket clients and enforces lockout after grace expires.

## Deployment and Infra Pattern
- Cloud Run deployment pattern follows `markd-backend` operational approach.
- `backend/scripts/deploy_cloud_run.sh` builds/pushes container and deploys Cloud Run service with Cloud SQL attachment.
- Same GCP project/region/settings pattern as markd is used; only DB name differs (`karaxas`).

## CI/CD Behavior
- `.md`-only changes must not trigger deployment/release jobs.
- Launcher release workflow (`.github/workflows/release.yml`):
  - ignores markdown-only commits.
  - ignores backend path changes so backend-only commits do not ship a launcher release.
- Backend deploy workflow (`.github/workflows/deploy-backend.yml`):
  - triggers on backend non-markdown changes.
  - deploys backend to Cloud Run.
  - supports either GitHub-to-GCP WIF auth or service-account JSON auth (`GCP_SA_KEY_JSON`).

## Launcher UI Structure Strategy
- UI is organized with reusable screen scaffolds and layout tokens (`UiScaffold`) to keep alignment consistent across screens.
- Screens are card-based (login, register, lobby, character creation, character selection, update, play) instead of one-off ad hoc layouts.
- Update functionality remains accessible from within account-lobby flow via updater card access.

## Logging Strategy
- Launcher logs to local files in install-root `logs/` (launcher, game, updater logs).
- Backend logs to Cloud Logging via structured application logs.
- Version/auth failures and force-update events are logged on backend.

## Security Baseline
- Access token: JWT (short-lived).
- Refresh/session token: stored as hash in DB.
- Passwords: bcrypt hash via passlib.
- Ops endpoint auth: `x-ops-token` header backed by `OPS_API_TOKEN` secret.

## Documentation Rule
This file is the single source of truth for technical information.

Any technical decision change is incomplete until this file is updated in the same change.
