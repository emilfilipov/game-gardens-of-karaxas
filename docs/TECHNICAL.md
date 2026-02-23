# Children of Ikphelion - Technical

## Purpose
Canonical technical source of truth for runtime architecture, backend boundaries, updater pipeline, and CI/CD behavior.

## Active Architecture

### Runtime stack
- Bootstrap/orchestrator: Kotlin launcher (`launcher/`)
- Game client runtime/UI/tools: Godot 4.x (`game-client/`)
- Backend API: FastAPI + PostgreSQL (`backend/`)
- Distribution/update: Velopack + GCS feed

### Directional model
- Online ARPG with instance-aware gameplay.
- Server-authoritative gameplay values and progression validation.
- Client handles rendering/input/UI and sends intent.

## Runtime Entry
- Godot scene entrypoint: `game-client/scenes/bootstrap.tscn`
- Active shell script: `game-client/scripts/client_shell.gd`
- Isometric world runtime: `game-client/scripts/world_canvas.gd`

## Client Surfaces (Current)
- Auth (`login/register`)
- Account hub (character list/create/select/play)
- Settings (including MFA controls)
- Admin tooling (for admin users)
- World runtime (isometric)

## Backend Responsibilities
- Auth/session lifecycle:
  - register/login/refresh/logout
  - MFA setup/status/enable/disable
  - websocket ticket issuance
- Character lifecycle:
  - list/create/select/delete
  - location persistence
- Content/config delivery:
  - runtime gameplay config endpoint (`/content/runtime-config`)
  - fallback snapshot endpoint (`/content/bootstrap`)
- World entry bootstrap:
  - character world bootstrap endpoint (`/characters/{id}/world-bootstrap`)
  - returns selected character snapshot, resolved level payload, spawn coordinates, runtime config descriptor/domains, and release/version policy snapshot.
- Release/version enforcement and publish-drain notifications

## Gameplay Config Model (Non-DB-Everything)
- Durable player/account state remains in DB.
- Gameplay tuning is backend-managed runtime config delivered by API.
- Initial file-backed source:
  - `backend/runtime/gameplay_config.json`
- Runtime service:
  - `backend/app/services/runtime_config.py`
  - response contract consumed via `/content/runtime-config`
  - client validates runtime config signature against canonicalized payload before applying
  - client caches last valid runtime config to `runtime_gameplay_cache.json` and falls back to cache when backend is temporarily unavailable.

## Auth Recovery and Request Resilience
- Godot client now uses authenticated request retry policy:
  - first request with current bearer token,
  - on `401` (non-auth endpoints), execute `/auth/refresh`,
  - retry original request once on successful refresh,
  - if refresh fails, clear local session and route user to auth screen.
- Error decoding now supports both legacy FastAPI `detail` payloads and wrapped `{ "error": ... }` payload shape from API middleware.

## Data Boundaries
- **DB durable state**:
  - users, sessions, characters, levels, inventory/equipment, quest state, audit/security events.
- **Backend runtime config**:
  - combat values, skill coefficients, progression coefficients, option catalogs.
- **Client-local**:
  - presentation preferences and non-authoritative cache.

## Security and Trust
- JWT access/refresh flow with security event logging.
- MFA support for user accounts.
- Request/security hardening in API middleware.
- Rate limiting and session drain policy retained.
- Gameplay-critical operations should be validated server-side before persistence.

## CI/CD Scope
- Release packaging/upload workflow:
  - `.github/workflows/release.yml`
- Backend deploy workflow:
  - `.github/workflows/deploy-backend.yml`
- Trigger policy:
  - backend code changes run backend checks/deploy flow,
  - backend markdown-only changes are filtered out from deploy execution,
  - launcher/game release workflow remains focused on client/launcher packaging.

## Secrets and Variables (Active + Upcoming)
### Active
- `KARAXAS_GCS_RELEASE_BUCKET` (repo variable)
- `KARAXAS_GCS_RELEASE_PREFIX` (repo variable)
- `GCP_WORKLOAD_IDENTITY_PROVIDER` (secret)
- `GCP_SERVICE_ACCOUNT` (secret)

### Backend deploy/runtime (required for online pivot)
- `KARAXAS_SERVICE_NAME`
- `KARAXAS_REGION`
- `KARAXAS_DB_HOST`
- `KARAXAS_DB_PORT`
- `KARAXAS_DB_NAME`
- `KARAXAS_DB_USER`
- `KARAXAS_DB_PASSWORD` (secret)
- `KARAXAS_JWT_SECRET` (secret)
- `KARAXAS_OPS_API_TOKEN` (secret)

## Testing and Checks
- Backend syntax sanity:
  - `python3 -m compileall backend/app`
- Launcher tests:
  - `./gradlew :launcher:test`
- UI regression harness:
  - `python3 game-client/tests/check_ui_regression.py`

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
