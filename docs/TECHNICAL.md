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
- Account hub (character list/create/select/play) using side-navigation view switching instead of tab containers
- Account hub list view now uses one unified sidebar (top create action + character rows) with no duplicate list column header/sidebar.
- Character list data refresh is automatic on account view/screen transitions (manual refresh control removed).
- Account hub list/create views render full-width inside the shell content region (not centered boxed sub-layouts).
- Create flow hides the left list sidebar and uses right-panel footer actions (`Create Character` above `Back to Character List`).
- Character creation preset picker (runtime-config driven `preset_key`) with player-selected `sex` (`appearance_key`) and name-only onboarding fields
- Character list/create dual preview stack:
  - large podium preview for authored inspection/rotation,
  - inset top-right world-scale mirror preview synchronized to the same direction.
- Character podium preview now includes grounding anchor visuals (baseline strip + contact shadow) with bottom-foot anchoring to prevent floating.
- World-scale inset preview now supports higher-contrast backdrop/border styling for readability against busy scene backgrounds.
- Character details/actions render as a compact bottom-right square overlay on the list preview surface.
- Settings (including MFA controls)
- Admin tooling (for admin users)
- World runtime (isometric)
- Character art runtime resolves directional animated frames from `assets/characters/sellsword_v1/catalog.json` for both podium preview and in-world actor rendering; the Sellsword generator outputs textured/colorized sheets (not silhouette placeholders).
- Sellsword source sheets are generated at `640x640` frame size (fidelity v2). World runtime still draws actors at gameplay size (`96x96`) via draw-time downscale, so higher source detail does not force world camera/actor scale inflation.
- Auth release notes now refresh whenever the auth screen is shown and fall back to local `patch_notes.md`/`release_notes.md` if summary fetch is unavailable.
- Shared game icon assets are aligned across launcher resources, game-client resources, and installer icons via the `assets/icons/game_icon.*` pipeline.

## Backend Responsibilities
- Auth/session lifecycle:
  - register/login/refresh/logout
  - MFA setup/status/enable/disable
  - websocket ticket issuance
- Character lifecycle:
  - list/create/select/delete
  - location persistence
  - preset-aware character bootstrap (`preset_key` baseline support)
- Content/config delivery:
  - runtime gameplay config endpoint (`/content/runtime-config`)
  - fallback snapshot endpoint (`/content/bootstrap`)
- World entry bootstrap:
  - character world bootstrap endpoint (`/characters/{id}/world-bootstrap`)
  - returns selected character snapshot, resolved level payload, spawn coordinates, runtime config descriptor/domains, and release/version policy snapshot.
- Party/instance lifecycle:
  - party v1 endpoint group (`/party`) for invite/accept/leave/kick/promote-owner flow
  - deterministic world instances (`solo/party/hub`) with session-bound assignment and reconnect metadata
  - runtime instance endpoints (`/instances/current`, `/instances/heartbeat`)
- Gameplay authority:
  - gameplay action resolver (`/gameplay/resolve-action`) for server-side movement sanity, replay/rate checks, skill validation, xp/level progression, and loot grants.
- Release/version enforcement and publish-drain notifications

## Gameplay Config Model (Non-DB-Everything)
- Durable player/account state remains in DB.
- Gameplay tuning is backend-managed runtime config delivered by API.
- Initial file-backed source:
  - `backend/runtime/gameplay_config.json`
- Runtime service:
  - `backend/app/services/runtime_config.py`
  - response contract consumed via `/content/runtime-config`
  - includes curated `character_presets` entries that seed create-flow defaults (appearance/stat/skill/inventory leaning) while the client can still submit overrides.
  - client validates runtime config signature against canonicalized payload before applying
  - client caches last valid runtime config to `runtime_gameplay_cache.json` and falls back to cache when backend is temporarily unavailable.
  - staged/publish/rollback lifecycle:
    - `GET /content/runtime-config/status`
    - `POST /content/runtime-config/stage`
    - `POST /content/runtime-config/publish`
    - `POST /content/runtime-config/rollback`

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
- Anti-cheat v1 guards are active in gameplay action ingestion:
  - movement sanity checks,
  - action rate limiting,
  - nonce replay detection,
  - security event hooks for suspicious behavior.

## CI/CD Scope
- Release packaging/upload workflow:
  - `.github/workflows/release.yml`
- Backend deploy workflow:
  - `.github/workflows/deploy-backend.yml`
- Security scan workflow:
  - `.github/workflows/security-scan.yml`
- Trigger policy:
  - backend code changes run backend checks/deploy flow,
  - backend markdown-only changes are filtered out from deploy execution,
  - deploy workflow runs post-deploy backend health + online-loop smoke checks,
  - launcher/game release workflow remains focused on client/launcher packaging.

## Distribution Channels
- Standalone launcher remains primary (`Velopack + GCS`).
- Dual-distribution Steam strategy is defined in:
  - `docs/STEAM_DUAL_DISTRIBUTION.md`

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
- `KARAXAS_RUNTIME_GAMEPLAY_SIGNATURE_PIN` (optional secret/var for signature pin hardening)

## Testing and Checks
- Backend syntax sanity:
  - `python3 -m compileall backend/app`
- Launcher tests:
  - `./gradlew :launcher:test`
- UI regression harness:
  - `python3 game-client/tests/check_ui_regression.py`
- Sellsword art pack generation:
  - `python3 tools/generate_sellsword_sprite_pack.py`

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
