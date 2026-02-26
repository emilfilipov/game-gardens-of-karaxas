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
- Auth/login layout is simplified and form-only (redundant section headings and in-panel auth navigation removed).
- Release notes are rendered only in the dedicated `Update` screen; auth/account surfaces no longer embed notes panels.
- Primary shell navigation is now a persistent left sidebar; legacy cogwheel popup menu flow is removed from the Godot client shell.
- Sidebar is rendered as a compact panel centered on the left edge; its button stack is centered within the panel.
- Auth/create/update menu shells now share a smaller unified footprint to reduce empty space.
- Menu selection state is sidebar-driven across auth/session states.
- Selected sidebar items now use explicit highlighted styling instead of disabled-state rendering.
- Auth form controls are compacted (narrower card, reduced field/button heights, smaller input text size) to avoid oversized login/register affordances.
- Auth shell and card sizing are now split from update-shell sizing (`AUTH_SHELL_SIZE` vs `UPDATE_SHELL_SIZE`) so login/register can stay significantly tighter without constraining update notes UX.
- Auth status messaging is contextual-only: blank state hides the status row entirely, then shows it only for validation/error/progress feedback.
- Update-screen build metadata is pinned above the scrollable notes region.
- Update release notes default to top-of-document on refresh (no bottom auto-scroll).
- Concept exploration references are generated under `concept_art/option_atlas_workspace`, `concept_art/option_dual_pane_studio`, and `concept_art/option_command_palette` via `tools/generate_ui_concept_variants.py`; older standalone `concept_art/sellsword_front.png` and `concept_art/sellsword_back.png` references were intentionally retired.
- Current exploration revision enforces auth-side `Login/Register/Quit` navigation (no redundant auth `Update` button), includes explicit registration mockups for all concept families, and keeps graph context visible in both selection and creation surfaces.
- Additional exploratory family `concept_art/option_crazy_flux` is generated through `tools/generate_ui_concept_crazy.py` with five iterative passes (`pass_1..pass_5`) and explicit pass-by-pass notes; this branch experiments with non-rectangular/slanted panel structures, rail-node navigation affordances, and graph-centric asymmetric shells while preserving required auth/update/MFA/character-flow feature surfaces.
- Additional exploratory family `concept_art/option_nova_10pass` is generated through `tools/generate_ui_concept_nova10.py` with ten iterative passes (`pass_01..pass_10`) produced as a generate-review-improve loop; this branch explores non-headline branding (`COI` emblem crest), mixed geometry shells (wedge/floating/stage/hybrid), auth/update fusion, and consolidated workspace IA while retaining full feature-surface parity.
- Additional exploratory family `concept_art/option_outsidebox_20pass` is generated through `tools/generate_ui_concept_outsidebox_20.py` with twenty iterative passes (`pass_01..pass_20`) following a plan/draw/generate/evaluate cadence; this branch uses a solid-color background, icon-first navigation experiments (top dock, right utility rail, bottom dock, radial cluster), and custom-drawn crest/corner motifs to break away from strict rectangular shell repetition while preserving the same feature capability set.
- New exploratory family `concept_art/shadow_graph` is generated through `tools/generate_shadow_graph_concepts.py` using strict single-pass iteration. Current passes (`pass_01..pass_06`) now include a zoomed-node mode where only the focused node is presented on screen, each node contains its relevant menu payload, node-to-node navigation is represented by edge route chips, and an explicit in-node `Back` control models previous-node camera-history traversal.

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
- Game update UI renders themed progress state and can resume status display on relaunch.
- Release notes/version metadata now resolve from the active executable payload first, then install-root fallbacks, to prevent stale notes/version labels after updates.
- Hybrid notes contract: the update surface fetches per-build notes from backend (`client_user_facing_notes` / `client_build_release_notes`) and only falls back to packaged local files when backend notes are unavailable.
- Update notes rendering prepends the installed build-version header (`Build`) before the bullet list for manual version sanity checks.
- Footer status text now shows only the build version marker (content config key is intentionally hidden from player-facing auth UI).
- Release summary refresh now runs during startup/auth entry so update notes are current before users open the Update menu.
- Update check flow preserves current menu context for non-restart outcomes (up-to-date/unavailable/failure) to avoid unexpected screen switches.
- Character list refresh no longer force-switches account view mode to list when user is in create mode.

## Release Policy Sync
- Release workflow now attempts backend release-policy activation after successful package upload when `KARAXAS_OPS_BASE_URL` and `KARAXAS_OPS_API_TOKEN` are configured.
- Backend release activation rejects accidental `latest_version` regression by default; explicit rollback must opt in via `allow_version_regression=true`.
- Rollback helper script sets `allow_version_regression=true` to preserve intentional rollback capability.
- Release workflow now prunes GCS feed/archive artifacts to retain only the 5 newest build versions, preserving short delta chains while controlling storage growth.

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
- Release workflow push triggers use a strict runtime/package allowlist (`launcher/**`, `game-client/**`, `designer-client/**`, `assets/**`, `scripts/**`, Gradle wrapper/build files) so docs/concepts/tooling-only commits cannot auto-publish new client versions.

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
