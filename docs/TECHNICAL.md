# Gardens of Karaxas - Technical

## Purpose
Canonical technical source of truth for architecture, module boundaries, update pipeline, and CI/CD behavior.

## Active Architecture

### Runtime stack
- Bootstrap/orchestrator: Kotlin launcher (`launcher/`)
- Game runtime/UI/tools: Godot 4.x (`game-client/`)
- Distribution/update: Velopack + GCS feed

### Decommissioned stack (legacy only)
- FastAPI backend (`backend/`) is no longer required for runtime gameplay.
- PostgreSQL/Cloud SQL live data model is no longer on the active critical path.
- MMO auth/session/social services are retired from active client flow.

## Architecture Guardrails
1. Gameplay logic must stay decoupled from updater/launcher internals.
2. Runtime must boot and run fully offline except update checks.
3. All tunables/content text must come from central local config.
4. Admin tooling edits local data/config; no backend round-trip assumptions.

## Runtime Entry
- Godot scene entrypoint: `game-client/scenes/bootstrap.tscn`
- Active script: `game-client/scripts/single_player_shell.gd`
- Obsolete network shell (`client_shell.gd`) removed from active runtime path.

## UI Foundation
- Shared tokens: `game-client/scripts/ui_tokens.gd`
- Shared components: `game-client/scripts/ui_components.gd`
- Shared character preview: `game-client/scripts/character_podium_preview.gd`
- World renderer/collision/movement surface: `game-client/scripts/world_canvas.gd`
- Level editor interactive canvas: `game-client/scripts/level_editor_canvas.gd`

## Single-Player Feature Surfaces
- Main menu: new/load/settings/update/admin/exit
- Character creation flow with point-budgeted stats/skills
- Local save/load slot system
- In-world play surface with local persistence:
  - combat abilities/cooldowns/resource loop
  - enemy prototype AI and loot drops
  - inventory/equipment interactions
  - NPC interaction + quest progress events
- Admin tab suite:
  - Level Editor
  - Asset Editor
  - Config Editor
  - Diagnostics/log viewer

## Runtime Systems (Current)
- `world_canvas.gd` owns:
  - isometric movement/collision checks
  - combat simulation entrypoints and HUD combat state events
  - enemy spawn/update/death flow
  - pickup and NPC interaction signaling
- `single_player_shell.gd` owns:
  - save-slot orchestration
  - inventory/equipment/quest/dialog state integration
  - settings capture, keybinding mapping, and runtime propagation
  - admin tool forms and persistence actions

## Central Config System

### Authoritative files
- Shipped default template:
  - `game-client/assets/config/game_config.json`
- Runtime-editable copy:
  - `user://config/game_config.json`
- Schema:
  - `game-client/assets/config/schema/game_config.schema.json`
- Generated reference:
  - `docs/CONFIG_FIELDS.md` (via `python3 tools/generate_config_docs.py`)

### Current domains in config
- `meta`
- `update`
- `ui`
- `world`
- `character_creation`
- `gameplay`
- `assets`

### Validation
- Startup validation occurs in `single_player_shell.gd`.
- Admin `Config Editor` exposes local validation and save path.
- Invalid config reports actionable errors in UI/status + local logs.
- Runtime schema checks are enforced through `_validate_with_schema`.

## Save System
- Root: `user://saves`
- Index: `user://saves/index.json`
- Slot payload: `user://saves/slot_<id>.json`
- Level files: `user://designer/levels/*.json`
- Logs: `<install_root>/logs/game.log` and updater logs
- Safety hardening:
  - atomic write (`.tmp` then rename)
  - timestamped backup snapshots
  - read-time fallback restore from latest backup for corrupted JSON
  - manual restore action in load UI

## Update Pipeline (Retained)

### Build/package
- Script: `scripts/pack.ps1`
- Artifacts: `releases/windows/`
- Runtime feed metadata written into payload (`update_repo.txt`)
- Update helper embedded as `UpdateHelper.exe`

### Release workflow
- Workflow: `.github/workflows/release.yml`
- Uses GCS feed upload (`RELEASES`, `.nupkg`, setup exe, portable zip)
- Prefetches previous packages from feed for delta continuity
- No backend release activation callback in active pipeline

## CI/CD Scope (Current)
- Active workflow: release packaging only.
- Deprecated workflows removed from active pipeline:
  - backend deploy workflow
  - backend-only security scan workflow

## Secrets and Variables

### Required (active)
- `KARAXAS_GCS_RELEASE_BUCKET` (repo variable)
- `KARAXAS_GCS_RELEASE_PREFIX` (repo variable, optional fallback `win`)
- `GCP_WORKLOAD_IDENTITY_PROVIDER` (secret)
- `GCP_SERVICE_ACCOUNT` (secret)

### Optional runtime-bundling vars
- `KARAXAS_RUNTIME_HOST` (default `godot`)
- `KARAXAS_GODOT_EXECUTABLE`
- `KARAXAS_GODOT_PROJECT_PATH`
- `KARAXAS_GODOT_WINDOWS_DOWNLOAD_URL`
- `KARAXAS_GODOT_WINDOWS_SHA256`

### Removed/deprecated from active use
- `KARAXAS_BACKEND_OPS_URL`
- `KARAXAS_OPS_TOKEN`
- Backend Cloud Run deploy vars/secrets (`KARAXAS_SERVICE_NAME`, `KARAXAS_DB_*`, etc.)
- Client auth/backend envs in runtime path (`GOK_API_BASE_URL`)

## Testing and Checks
- Launcher tests:
  - `./gradlew :launcher:test`
- Backend syntax sanity:
  - `python3 -m compileall backend/app`
- UI regression harness:
  - `python3 game-client/tests/check_ui_regression.py`
- UI signature update (intentional layout changes only):
  - `UPDATE_UI_GOLDEN=1 python3 game-client/tests/check_ui_regression.py`

## Notes on Legacy Code
- Legacy backend/MMO code may still exist in repository history or dormant modules, but must not be part of active runtime behavior.
- New development must target single-player runtime and local data/config patterns.

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
