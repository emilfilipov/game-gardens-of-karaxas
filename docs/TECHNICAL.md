# Children of Ikphelion - Technical

## Purpose
Canonical technical source of truth for runtime architecture, backend boundaries, updater pipeline, and CI/CD behavior.

## Active Architecture

### Runtime stack
- Bootstrap/orchestrator: Kotlin launcher (`launcher/`)
- Game client runtime/UI/tools: Godot 4.x (`game-client/`)
- Backend API: FastAPI + PostgreSQL (`backend/`)
- Distribution/update: Velopack + GCS feed

3D migration is now in active implementation:
- Godot 3D runtime/world scaffold exists (`world_canvas_3d.gd`) with runtime renderer mode toggle (`2d`/`3d`) and 3D default fallback.
- 3D world runtime now consumes authored object payloads (`objects`) as primary placement source, with spawn-marker yaw/z support, blocker registration, transition trigger checks, and baseline navmesh region generation.
- Programmatic Blender headless asset pipeline is active under `tools/blender/`, including pinned install, local shared-lib fallback wiring, and GLB export scripts consumed by runtime model loading.

### Directional model
- Online ARPG with instance-aware gameplay.
- Server-authoritative gameplay values and progression validation.
- Client handles rendering/input/UI and sends intent.

## Runtime Entry
- Godot scene entrypoint: `game-client/scenes/bootstrap.tscn`
- Active shell script: `game-client/scripts/client_shell.gd`
- Isometric world runtime: `game-client/scripts/world_canvas.gd`
- 3D world runtime scaffold: `game-client/scripts/world_canvas_3d.gd`

## Client Surfaces (Current)
- Auth (`login/register`)
- Account hub (character list/create/select/play) using side-navigation view switching instead of tab containers
- Account hub list view now uses one unified sidebar (top create action + character rows) with no duplicate list column header/sidebar.
- Character list data refresh is automatic on account view/screen transitions (manual refresh control removed).
- Account hub list view remains the default even for empty character sets (no forced create-mode redirect on `/characters` empty payloads).
- Account hub list/create views render full-width inside the shell content region (not centered boxed sub-layouts).
- Create flow hides the left list sidebar and uses right-panel footer actions (`Create Character` above `Back to Character List`).
- Character create submit path no longer uses a confirmation dialog; create requests post directly after validation.
- Character creation preset picker (runtime-config driven `preset_key`) with player-selected `sex` (`appearance_key`) and name-only onboarding fields
- Character list/create dual preview stack:
  - large 3D podium preview for authored inspection/rotation,
  - inset top-right 3D world-scale mirror preview synchronized to the same direction.
- Character podium preview now includes grounding anchor visuals (baseline strip + contact shadow) with bottom-foot anchoring to prevent floating.
- World-scale inset preview now supports higher-contrast backdrop/border styling for readability against busy scene backgrounds.
- Character details/actions render as a compact bottom-right square overlay on the list preview surface.
- Create podium preview title text is disabled (no `Character Type` headline above the model).
- Settings (including MFA controls)
- Admin tooling (for admin users)
- World runtime now supports both:
  - `2d` path (`world_canvas.gd`) for compatibility fallback,
  - `3d` path (`world_canvas_3d.gd`) as active migration baseline.
- 3D runtime movement now supports runtime-config keybind overrides and walk/run state mapping with animation-state playback.
- 3D runtime transitions emit `transition_requested` from trigger volumes encoded in level transition payloads.
- Character art runtime resolves directional animated frames from `assets/characters/sellsword_v1/catalog.json` for both podium preview and in-world actor rendering; the Sellsword generator outputs textured/colorized sheets (not silhouette placeholders).
- Sellsword source sheets remain `640x640` at runtime contract size, but fidelity v3 now draws at a 4x larger authored base canvas (`BASE_FRAME_SIZE=640`) with smoother anti-aliased rendering and direction-specific front/side/back pose silhouettes before sheet emission.
- 3D sellsword actor loading in `game-client/scripts/sellsword_3d_factory.gd` now prefers generated GLB assets (`assets/3d/generated/*.glb`) and falls back to procedural meshes only when generated assets are unavailable.
- Factory-managed animation contract now guarantees presence/playback of: `idle`, `walk`, `run`, `attack`, `cast`, `hurt`, `death`.
- Current generated male sellsword shape/material profile is guided by concept references at:
  - `concept_art/sellsword_front.png`
  - `concept_art/sellsword_back.png`
- Character list load path now logs API diagnostics (`rows` count + failure status/message) so client logs can confirm frontend/backend `/characters` contract flow for specific accounts.
- Character actions are now selection-gated in account view (`Play/Delete` disabled until selected character).
- Asset ingest manifest entries for Sellsword idle sheets track `*_640` assets so release-time ingest validation matches generated sprite-pack outputs.
- Auth release notes now refresh whenever the auth screen is shown and fall back to local `patch_notes.md`/`release_notes.md` if summary fetch is unavailable.
- Shared game icon assets are aligned across launcher resources, game-client resources, and installer icons via the `assets/icons/game_icon.*` pipeline, regenerated from root source `icon_2.png`.
- Starter 3D environment scenes are available at:
  - `game-client/scenes/environment/ground_tile_stone_3d.tscn`
  - `game-client/scenes/environment/foliage_grass_a_3d.tscn`
  - `game-client/scenes/environment/foliage_tree_dead_3d.tscn`
- Blender automation tooling is available at:
  - `tools/blender/install_blender.py`
  - `tools/blender/run_blender_headless.py`
  - `tools/blender/scripts/generate_sellsword_3d_assets.py`
- Generated GLB outputs currently expected by runtime and CI contract checks:
  - `assets/3d/generated/sellsword_male.glb`
  - `assets/3d/generated/sellsword_female.glb`
  - `assets/3d/generated/ground_tile_stone.glb`
  - `assets/3d/generated/foliage_grass_a.glb`
  - `assets/3d/generated/foliage_tree_dead_a.glb`

## Backend Responsibilities
- Auth/session lifecycle:
  - register/login/refresh/logout
  - MFA setup/status/enable/disable
  - websocket ticket issuance
- Character lifecycle:
  - list/create/select/delete
  - `/characters` list is user-scoped (returns only characters owned by the authenticated account, including admin accounts)
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
  - release workflow now triggers on markdown/docs changes (only backend path remains ignored),
  - deploy workflow runs post-deploy backend health + online-loop smoke checks,
  - launcher/game release workflow remains focused on client/launcher packaging and now includes `3D Runtime Contract` validation.

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
- 3D runtime contract harness:
  - `python3 game-client/tests/check_3d_runtime_contract.py`
- Sellsword art pack generation:
  - `python3 tools/generate_sellsword_sprite_pack.py`
- Blender toolchain install:
  - `python3 tools/blender/install_blender.py --version 4.2.3`
- Blender headless 3D asset export:
  - `python3 tools/blender/run_blender_headless.py --script tools/blender/scripts/generate_sellsword_3d_assets.py`
- Asset ingest manifest validation:
  - `python3 tools/validate_asset_ingest.py --manifest assets/iso_asset_manifest.json`

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
