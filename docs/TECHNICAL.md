# Children of Ikphelion - Technical

## Purpose
Canonical technical source of truth for runtime architecture, backend boundaries, updater pipeline, and CI/CD behavior.

## Active Architecture

### Runtime Stack
- Bootstrap/orchestrator: Kotlin launcher (`launcher/`)
- Game runtime client: Godot 4.x (`game-client/`)
- Online backend API: FastAPI + PostgreSQL (`backend/`)
- Distribution/update: Velopack + GCS feed
- External content tooling: standalone designer program (`designer-client/`)

### Directional Model
- Online ARPG with instance-aware gameplay.
- Server-authoritative gameplay values and progression.
- Client handles rendering/input/UI and sends gameplay intent.

## Runtime Entry
- Godot scene entrypoint: `game-client/scenes/bootstrap.tscn`
- Active shell script: `game-client/scripts/client_shell.gd`
- Active world runtime: `game-client/scripts/world_canvas.gd` (2D baseline)

## Client Surfaces (Current)
- Auth (`login/register`)
- Account hub (character list/create/select/play)
- World runtime
- Settings and log viewer

### Account UX Baseline
- Character list uses one left sidebar with top `Create Character` action and character rows below.
- List remains default account view even when no characters exist.
- List/create center area now hosts skill-tree graph (`skill_tree_graph.gd`).
- Character list/create small preview cards are removed.
- List graph is cleared when no character selection exists.
- Character actions (`Play`, `Delete`) stay selection-gated.

### 2D Character Pipeline Baseline
- Runtime character preview/world actor use spritesheet catalog at:
  - `assets/characters/sellsword_v1/catalog.json`
- Baseline frame size: `512x512`
- Baseline directions: `E/W` (`2dir` sheets)
- Generator:
  - `tools/generate_sellsword_sprite_pack.py`

### UI Direction Baseline
- Tokenized UI palette moved to lighter visual language in `ui_tokens.gd`.
- Account shell composition supports graph-first center content and compact right-side preview/details.
- Button hover feedback is highlight-only (no hover scale tween/growth).

## Backend Responsibilities
- Auth/session lifecycle (register/login/refresh/logout + MFA)
- Character lifecycle (list/create/select/delete/location/bootstrap)
- Content/config delivery (`/content/runtime-config`, `/content/bootstrap`)
- Level authoring APIs (`/levels`) for external designer tooling
- Runtime publish/version operations under `/content/*`
- Designer publish orchestration under `/designer/publish` (backend-mediated GitHub commit + workflow dispatch)
- Gameplay authority (`/gameplay/resolve-action`)
- Release notes authority for builds via `release_records` (served through `/release/summary`)

## Tooling Split
- Runtime game client no longer exposes editor navigation in production menu flow.
- External authoring tool is provided at:
  - `designer-client/designer_tool.py`
- Designer client currently supports:
  - backend login/refresh flow using `/auth/login` and `/auth/refresh`
  - load/save level payloads via `/levels`
  - load/stage/publish runtime config via `/content/runtime-config/*`
  - backend-mediated repo/CI publish request via `/designer/publish`

## Auth and Version Gates
- Backend auth gates enforce latest-build login for all users (no admin bypass for outdated builds).
- Contract mismatch and force-update checks still apply after latest-build gate.

## Updater UX Contract
- Game client update flow writes/reads updater status at `<install_root>/logs/update_status.json`.
- Update helper publishes stage + progress metrics (`percent`, `speed_bps`, `downloaded_bytes`, `total_bytes`).
- Game auth UI renders themed progress state and can resume status display on relaunch.
- Release notes/version metadata now resolve from the active executable payload first, then install-root fallbacks, to prevent stale notes/version labels after updates.
- Hybrid notes contract: login surfaces fetch per-build notes from backend (`client_user_facing_notes` / `client_build_release_notes`) and only fall back to packaged local files when backend notes are unavailable.

## Packaging Contract
- One installer payload now includes:
  - `ChildrenOfIkphelionLauncher.exe` (game launcher/runtime entry),
  - `designer/ChildrenOfIkphelionDesigner.exe` (designer executable).
- Velopack hook handling creates/removes desktop shortcuts for both game and designer executables.
- Icon set is unified across game, launcher, and setup wrapper assets (transparent `COI` light-blue mark).

## Gameplay Config Model
- Durable player/account state remains in DB.
- Gameplay tuning is backend-managed runtime config delivered by API.
- Active source file:
  - `backend/runtime/gameplay_config.json`
- Runtime config service:
  - `backend/app/services/runtime_config.py`

## Security and Trust
- JWT access/refresh with security event logging
- MFA support
- Middleware hardening and rate limiting
- Server-side validation for gameplay-critical operations

## CI/CD Scope
- Release workflow: `.github/workflows/release.yml`
- Backend deploy workflow: `.github/workflows/deploy-backend.yml`
- Security scan workflow: `.github/workflows/security-scan.yml`

### Release Validation Gates (Current)
- Asset ingest validation
- UI regression harness
- 2D runtime contract harness

## Testing and Checks
- Backend syntax sanity:
  - `python3 -m compileall backend/app`
- Launcher tests:
  - `./gradlew :launcher:test`
- 2D runtime contract harness:
  - `python3 game-client/tests/check_2d_runtime_contract.py`
- UI regression harness:
  - `python3 game-client/tests/check_ui_regression.py`
- Sellsword art pack generation:
  - `python3 tools/generate_sellsword_sprite_pack.py`
- Asset ingest manifest validation:
  - `python3 tools/validate_asset_ingest.py --manifest assets/iso_asset_manifest.json`

## Distribution Channels
- Standalone launcher remains primary (`Velopack + GCS`).
- Dual-distribution Steam strategy remains documented in:
  - `docs/STEAM_DUAL_DISTRIBUTION.md`

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
