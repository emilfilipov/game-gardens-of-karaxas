# Gardens of Karaxas - Technical

## Purpose
This is the single source of truth for technical architecture, stack decisions, module boundaries, deployment, and CI/CD behavior.

## Runtime and Service Stack
- Bootstrap/orchestration shell: Kotlin (JVM) module (`launcher/`).
- Unified game UI/runtime/editor host: Godot 4.x module (`game-client/`).
- Backend services: Python FastAPI (`backend/`).
- Database: PostgreSQL (Cloud SQL), database name `karaxas`.
- Migrations: Alembic.
- Service hosting: Google Cloud Run.
- Launcher backend endpoint resolution:
  - Uses `GOK_API_BASE_URL` when explicitly set.
  - Falls back to deployed Cloud Run API URL when not set (instead of localhost), to keep production auth usable by default.

## Architecture Rules (Must Hold)
1. Gameplay/runtime logic remains decoupled from launcher/updater internals.
2. Godot client hosts account/lobby/gameplay/editor UX; backend remains authority for auth/session/version-gating.
3. Backend services must be deployable independently from launcher releases.
4. Module boundaries remain explicit:
   - `launcher/` for bootstrap/update orchestration and runtime process handoff.
   - `game-client/` for all player/admin UI surfaces and gameplay runtime.
   - `backend/` for API/realtime/auth/social data services.

## Engine Host Stack Decision (Locked)
- `GOK-MMO-176` is completed and locked via `docs/ENGINE_SPIKE_GOK_MMO_176.md`.
- Runtime/editor host stack decision:
  - Keep `launcher/` (Kotlin) as thin process/update orchestrator.
  - Adopt `Godot 4.x` as authoritative gameplay runtime and world/editor host (`game-client/` module scaffolded).
  - Keep `backend/` (FastAPI) as authoritative service/data layer.
- Migration is now in Godot-first mode: packaged default runtime host is `godot`.
- `launcher_legacy` mode remains for local diagnostic fallback only and is not the default release path.

## Godot-First Unified Shell (Active)
- Auth, register, account lobby, character list/create, world runtime, updater, and admin log viewer are implemented in `game-client/scripts/client_shell.gd`.
- Shared UI foundation for Godot shell is now split into:
  - `game-client/scripts/ui_tokens.gd` (authoritative palette/spacing/size/radius tokens),
  - `game-client/scripts/ui_components.gd` (shared constructors for labels/buttons/inputs/options and centered shell scaffolds).
- Isometric/shared runtime helpers now include:
  - `game-client/scripts/iso_projection.gd` (world<->screen transforms, tile helpers, stable depth-key helper, fixture self-checks),
  - `game-client/scripts/character_podium_preview.gd` (shared directional podium renderer for character list + creator).
- `ui_tokens` now includes a dedicated compact settings shell size (`shell_settings_w/h`) so settings uses a tighter workspace than account/admin editing screens.
- `ui_components` now also provides reusable primary/secondary button variants, consistent card-panel styles, and section/banner helpers used by auth/account/settings/admin surfaces.
- Shared styleboxes now apply internal content margins so card/button/input children inherit consistent inset padding without per-screen manual offsets.
- Godot helper scripts now resolve cross-script dependencies via explicit `preload(...)` constants (instead of relying on global class-name lookup) to avoid parser-order startup failures in packaged builds.
- Godot shell defaults to borderless fullscreen startup.
- Screen switching in the Godot shell now uses a generic `Control` stack container for Godot 4.3 compatibility (no `StackContainer` dependency).
- Top-right menu is hidden on auth screen; auth screen carries direct `Update & Restart` and `Exit`.
- Gameplay screen now hides non-essential shell chrome/background layers so world rendering gets near full-screen viewport usage.
- Godot shell restores the branded app icon from packaged assets (`res://assets/game_icon.png`) for runtime window/taskbar identity.
- Godot shell startup hardening now avoids stale script preloads, guards optional world-canvas method calls (`set_active`), and uses runtime image loading (with install-path fallbacks) for background/icon assets to avoid importer-dependent startup failures.
- Launcher startup now probes configured runtime host and directly launches Godot shell when host is `godot`.
- If configured host is `godot` and launch fails, startup aborts with a themed error dialog instead of silently dropping into the old Swing account UI.

## Godot Phase 0 Scaffold (Implemented)
- `game-client/` now exists as a Godot 4.x project scaffold with bootstrap scene/script.
- Launcher-to-game handoff contract is now versioned as `gok_runtime_bootstrap_v1`:
  - schema: `game-client/contracts/bootstrap.schema.json`
  - sample payload: `game-client/contracts/bootstrap.example.json`
  - launcher codec/models: `launcher/src/main/kotlin/com/gok/launcher/GameRuntimeBootstrap.kt`
- This phase does not yet replace current in-launcher gameplay flow; it adds the safe integration seam for phased cutover.

## Godot Runtime Handoff (Implemented)
- Launcher now supports a runtime-host switch:
  - `GOK_RUNTIME_HOST=launcher_legacy` (default): keep in-launcher gameplay scene.
  - `GOK_RUNTIME_HOST=godot`: launch external Godot runtime on character `Play`.
- Optional runtime path overrides:
  - `GOK_GODOT_EXECUTABLE` (defaults to `godot4`),
  - `GOK_GODOT_PROJECT_PATH` (defaults to discovered `game-client/` roots).
- Godot executable resolution now prefers bundled runtime binaries in release payload (`game-client/runtime/windows/godot4.exe`) before falling back to configured command names.
- Packaged default runtime settings are now emitted into payload as `runtime_host.properties`:
  - `runtime_host`,
  - `godot_executable`,
  - `godot_project_path`.
- Runtime setting precedence is now:
  - process environment variables (`GOK_*`) first,
  - packaged `runtime_host.properties` second,
  - launcher defaults (`launcher_legacy`, `godot4`) last.
- On `godot` mode:
  - launcher writes per-character bootstrap payload to `install_root/runtime/runtime_bootstrap_<character_id>.json`,
  - launches Godot with `--bootstrap=<path>`,
  - streams runtime stdout/stderr into launcher log for handoff diagnostics,
  - keeps launcher window visible during launch to avoid hidden-window confusion while runtime integration is in progress.
- If Godot launch prerequisites fail, launcher logs the reason and falls back to legacy in-launcher gameplay for continuity.

## Isometric Visual Direction (Locked)
- Reference board: `docs/ART_DIRECTION_BOARD.md`.
- Projection decision: `2:1` isometric (dimetric).
- Scale decisions:
  - logical tile footprint target: `64x32`,
  - character frame authoring target: `128x128`.
- Camera decisions:
  - default zoom `0.80x`,
  - allowed runtime range `0.70x-1.10x`.
- Lighting decisions:
  - warm/vibrant soft global baseline,
  - data-driven per-zone/per-item/per-character effect overrides for grim-dark shifts.
- UI composition decisions:
  - preserve top and bottom safe bands,
  - maintain unobstructed central gameplay region by default.

## Isometric Coordinate Contract (Locked)
- Canonical spec: `docs/ISOMETRIC_COORDINATE_SPEC.md` (`GOK-MMO-175`).
- Locked transform constants:
  - `TILE_W=64`, `TILE_H=32`, `HALF_W=32`, `HALF_H=16`.
  - world->screen: `sx=(wx-wy)*HALF_W`, `sy=(wx+wy)*HALF_H`.
  - screen->world is the exact algebraic inverse after camera/zoom removal.
- Locked ownership/rounding behavior:
  - tile ownership is half-open and resolved with mathematical `floor` + `EPS`.
  - persisted world coordinates are quantized to fixed precision (`FP=1024`).
- Locked pivot/sorting behavior:
  - floor tiles anchor at tile center projection point.
  - characters/props anchor on ground-contact pivots (default normalized `(0.5,1.0)` with data-driven offsets).
  - runtime/editor draw ordering must use the same stable tuple (`floor_order`, `render_layer`, `sort_y_fp`, `sort_x_fp`, `stable_id`).
- Collision and editor picking must use the same inverse transform + tile ownership rules from the canonical spec.
- Hybrid level payload contract and migration documents are now:
  - `docs/LEVEL_SCHEMA_V3.md`
  - `docs/LEVEL_SCHEMA_V3_MIGRATION.md`
- Vertical-slice go/no-go gates are now documented in `docs/ISOMETRIC_VERTICAL_SLICE_GATES.md`.

## Backend Service Shape (Current)
- Single FastAPI service (modular monolith) with:
  - REST APIs for auth, lobby, characters, levels, chat, content, and ops.
  - WebSocket endpoints for realtime chat/events secured by short-lived one-time ws tickets.
  - Events websocket now accepts zone-scope (`zone_scope`) and zone-telemetry (`zone_telemetry`) messages for floor-scoped presence fanout + runtime observability.
- Chat endpoints are now character-gated: users must have an active selected character before chat access.
- This keeps operational complexity low while preserving future split path (`api` + `realtime`) if scale requires it.

## Data Model (Current)
- `users`: account identity.
  - Includes `is_admin` boolean for backend-authoritative admin gating.
  - Includes account MFA fields (`mfa_totp_secret`, `mfa_enabled`, `mfa_enabled_at`) for TOTP-based user security hardening.
- `user_sessions`: refresh/session records and client build/content version tracking.
  - Includes publish-drain state fields (`drain_state`, `drain_event_id`, `drain_deadline_at`, `drain_reason_code`) for non-admin forced relog orchestration.
  - Includes refresh-rotation replay detection fields (`previous_refresh_token_hash`, `refresh_rotated_at`).
- `release_policy`: active build/content release policy (`latest/min-supported` build, `latest/min-supported` content keys, `update_feed_url`, `enforce_after`).
- `release_records`: append-only release activation history (build/content versions, feed URL, build notes, user-facing notes, actor, activation timestamp).
- `characters`: user-owned character builds (stats/skills point allocations).
  - Includes `appearance_key` for visual preset selection persistence.
  - Includes `race`, `background`, and `affiliation` for character identity scaffolds selected in creation UI.
  - Includes `equipment` JSON loadout map (slot -> item visual key) for modular/paperdoll visual composition.
  - Includes `level` and `experience` (starts at level 1 / 0 XP).
  - Includes nullable `level_id` to map a character to a saved world layout.
  - Includes nullable `location_x`/`location_y` for persisted world coordinates.
  - Character names are globally unique (case-insensitive unique index on `lower(name)`).
- `levels`: named level layouts with schema-versioned layered tile payloads (`layer_cells`) plus legacy-compatible derived `wall_cells` for collision fallback.
  - Includes `object_placements` for `schema_version >= 3` hybrid freeform object transforms with stable IDs.
  - Includes `descriptive_name` (player-facing floor label), `order_index` (tower progression ordering), and `transitions` (stairs/ladder/elevator destination links).
  - Planned extension: per-level lighting profile/cycle config for configurable day-night behavior (speed multiplier, start phase/time, and forward/reversed direction).
- `content_versions`: immutable content snapshot headers with lifecycle state (`draft`, `validated`, `active`, `retired`).
- `content_bundles`: per-domain JSON payloads keyed by `content_version_id` + `domain`.
- `publish_drain_events`: publish-triggered drain windows (actor, reason, deadline, targeted/persist/revoked counters, cutoff timestamp).
- `publish_drain_session_audit`: per-session audit rows for drain persistence/despawn/revocation outcomes.
- `ws_connection_tickets`: one-time websocket handshake credentials bound to authenticated sessions.
- `admin_action_audit`: append-only audit records for privileged release/content actions.
- `security_event_audit`: append-only security telemetry for auth/session events (login/refresh/logout/MFA/replay detection and bulk revocation).
- `friendships`: friend graph.
- `guilds`, `guild_members`: guild presence and rank scaffolding.
- `chat_channels`, `chat_members`, `chat_messages`: global/direct/guild chat model.

## Version Gating and Forced Update Flow
- Backend stores release policy for both build and content compatibility.
- Clients send:
  - `X-Client-Version`
  - `X-Client-Content-Version`
- Non-admin sessions are rejected with `426 Upgrade Required` (and revoked when already authenticated) after grace if either:
  - build is below minimum supported build, or
  - content version key is below minimum supported content key.
- Content publishes now emit a logical build-version bump in release metadata while keeping `min_supported_version` unchanged for content-only pushes; this preserves forced relog/update UX without requiring a new binary package.
- Admin sessions are exempt from forced-update lockout for operational validation.
- Grace window is currently 5 minutes.
- Public `GET /release/summary` exposes launcher-facing release state (`update_feed_url`, latest build/content keys, update flags, and DB-backed release notes).

## Release Notification Integration
- Launcher release workflow posts to backend ops endpoint:
  - `POST /ops/release/activate`
  - Payload includes build version, GCS update feed URL, build notes/user-facing notes, and `grace_minutes=5`.
- Backend writes release activation to `release_records` and updates active `release_policy`.
- Backend broadcasts `force_update` to connected websocket clients with build/content minimums and feed URL.
- Content version activation also updates release-policy content keys and triggers the same grace-window force-update broadcast.
- Content version activation/rollback also records a content-only release activation entry with incremented logical latest build marker for synchronized release-note/version history.
- Content/release activation also creates a publish-drain event and begins non-admin session draining with realtime warning/forced-logout events.

## Deployment and Infra Pattern
- Cloud Run deployment pattern follows `markd-backend` operational approach.
- `backend/scripts/deploy_cloud_run.sh` builds/pushes container and deploys Cloud Run service with Cloud SQL attachment.
- Backend container runtime uses a dedicated non-root `app` user to satisfy container hardening baselines.
- Same GCP project/region/settings pattern as markd is used; only DB name differs (`karaxas`).

## CI/CD Behavior
- `.md`-only changes must not trigger deployment/release jobs.
- Launcher release workflow (`.github/workflows/release.yml`):
  - ignores markdown-only commits.
  - ignores backend path changes so backend-only commits do not ship a launcher release.
  - prefetches prior Velopack packages from GCS feed path before `vpk pack` so delta generation remains available across skipped versions.
  - uploads feed artifacts (`RELEASES`, `.nupkg`, setup exe) to GCS feed path and versioned archive path.
  - passes runtime-host default config into packaging via:
    - `KARAXAS_RUNTIME_HOST`,
    - `KARAXAS_GODOT_EXECUTABLE`,
    - `KARAXAS_GODOT_PROJECT_PATH`.
  - when runtime host is `godot`, downloads a Windows Godot runtime archive during CI, optionally verifies SHA256, bundles executable into payload (`game-client/runtime/windows/godot4.exe`), and writes packaged default executable path so users do not require local Godot installation.
  - supports optional Godot bundle inputs:
    - `KARAXAS_GODOT_WINDOWS_DOWNLOAD_URL`,
    - `KARAXAS_GODOT_WINDOWS_SHA256`.
  - validates runtime asset ingest metadata with `tools/validate_asset_ingest.py --manifest assets/iso_asset_manifest.json` and fails release on invalid entries.
  - applies `Cache-Control: no-cache, max-age=0` metadata to mutable feed files (`RELEASES`, setup exe, portable zip, and feed JSON manifests) to prevent stale client/browser caching.
  - defaults runtime host packaging to `godot` when runtime-host env vars are unset.
  - notifies backend release activation endpoint with new build/feed/notes metadata.
- Backend deploy workflow (`.github/workflows/deploy-backend.yml`):
  - triggers on backend non-markdown changes.
  - deploys backend to Cloud Run.
  - uses WIF-only GitHub->GCP auth (no service-account JSON key path).
  - enforces Secret Manager refs for runtime secrets (`*_SECRET_REF`) in CI deploy path.
  - runs post-deploy smoke checks (`/health` + `/health/deep`) and fails workflow on failed deep health.
- Security workflow (`.github/workflows/security-scan.yml`):
  - scans backend dependencies with `pip-audit`.
  - runs Trivy fs scan (vuln/misconfig/secret) and fails on high/critical findings, including Dockerfile root-user misconfiguration.

## Client UI Structure Strategy
- Active path: Godot unified shell (`game-client/scripts/client_shell.gd`) owns auth/account/world/editor/update/log-viewer surfaces.
- Legacy Swing bullets below remain as migration reference until `GOK-MMO-242` removes deprecated launcher UI code paths.
- UI is organized with reusable screen scaffolds and layout tokens (`UiScaffold`) to keep alignment consistent across screens.
- Screens are card-based (combined auth, character creation, character selection, update, play) instead of one-off ad hoc layouts.
- Post-login routing now always lands on `Character List`; empty accounts remain on that tab and show empty-state guidance instead of auto-switching to `Create Character`.
- Character creation tables are content-driven (`character_options`, `stats`, `skills`) and submit allocated stat/skill payloads directly to `/characters`.
- Character creator appearance selector now derives from discovered local art and falls back to a single guaranteed preset (`human_male`) when optional variants are unavailable.
- Character List now exposes both auto-refresh (after create/delete) and an explicit manual `Refresh` action.
- Character List roster rail now includes client-side text search/filter against name and location metadata.
- Character list refresh now performs a deferred second render pass after data load to avoid zero-width pre-layout roster rendering.
- Character flow QA expectations are captured in `docs/CHARACTER_FLOW_QA.md` (empty/single/multi/admin/MFA path coverage).
- Character List row rendering now uses fixed-height themed cards with:
  - selectable row header button for preview binding,
  - action controls centralized in the selected-character detail panel,
  - explicit container minimum sizing to keep rows visible inside scroll surfaces,
  - explicit minimum row width sizing to prevent zero-width/invisible roster cards,
  - a separate location metadata line to improve at-a-glance readability.
- Auth/account/settings surfaces are now rendered inside centered constrained cards to improve hierarchy and reduce full-screen form sprawl.
- Admin tool screens (`Level Editor`, `Level Order`, `Asset Editor`, `Content Versions`) are now also rendered in centered constrained card shells instead of raw full-bleed debug layouts.
- Settings `Video`, `Audio`, and `Security` sections are rendered in themed card blocks rather than plain unstructured tab content.
- Settings tabs now use compact three-column card grids per tab so control density is higher and future options can be added without full-row stretching.
- Global spacing tokens (`xs..xl`) were increased and re-applied to account/settings rails to reduce control crowding and border clipping.
- BoxContainer spacer usage was normalized to end-spacers (`add_spacer(false)`) so settings controls pin to the top of each card instead of drifting toward the bottom.
- Root screen gutters were widened to keep account/settings/admin shells off viewport edges and maintain consistent left-right breathing room.
- Header chrome now uses a centered title with symmetric fixed-width side slots; the cog button is anchored in the right slot and screen-name title swapping is disabled for non-world screens.
- Character load/create flows now emit client log diagnostics for `/characters` fetch/create status and loaded row counts to speed up list-render incident triage.
- Character roster summary buttons now set `Button.alignment` (Godot 4) instead of invalid `horizontal_alignment`, preventing runtime render exceptions that hid list rows despite valid backend responses.
- Character texture loader now checks `ResourceLoader.exists`/`FileAccess.file_exists` before loading `res://` files to avoid noisy startup errors for optional/fallback art filenames.
- World prototype renderer now uses an isometric pass pipeline in `world_canvas.gd`:
  - pass order: floor -> props -> actor -> foreground,
  - stable sorting tuple from `iso_projection.depth_key(...)`,
  - optional draw-order diagnostics hook for depth collisions.
- World prototype movement now maps WASD into isometric vectors and emits 8-direction facing buckets while preserving existing location persistence callbacks (`player_position_changed` + `/characters/{id}/location` path).
- Character List/Creator preview now uses shared `CharacterPodiumPreview` widgets with directional controls and drag-to-rotate input; texture lookup falls back from directional variants to canonical idle assets.
- Character Creator is now implemented as a 4-step TabContainer flow (`Appearance`, `Identity`, `Stats & Skills`, `Review`) with step validation helpers, grouped review errors, unsaved-leave confirmation dialog, and final submit gating.
- Character roster rail now includes search + sort (`name`, `level`, `location`) and concise row cards; detailed XP/build text remains in the right-side detail panel.
- Settings now persists and applies a `reduced_motion` preference used by screen transitions and podium preview animation.
- `ui_components.gd` now applies shared hover-motion emphasis to themed buttons (unless reduced motion suppresses runtime tween usage in consuming screens).
- Added automated character roundtrip tests:
  - backend route-level create->list regression (`backend/tests/test_character_list_roundtrip.py`),
  - launcher client contract regression with mocked `/characters` backend (`launcher/src/test/kotlin/com/gok/launcher/KaraxasBackendClientCharacterFlowTest.kt`).
- Screen switching in `client_shell.gd` now applies short fade-in transitions to improve perceived fluidity while preserving deterministic screen ownership.
- Footer text is version-only; transient welcome/status chatter is no longer rendered in footer/account surfaces.
- Dropdown popups are sanitized to non-checkable list behavior (no radio/check glyphs), and skill buttons use a themed custom tooltip popup instead of default tooltip behavior.
- Launcher now defaults to borderless fullscreen and keeps a top-right settings menu entry point.
- Startup window-mode application now guards undecorated-frame transitions to avoid `IllegalComponentStateException` on already-displayable windows.
- Launcher keeps the same full-screen background art image, but interactive UI chrome now uses lightweight shape-based rendering (thin borders + painted fills/gradients) instead of PNG-framed button/panel surfaces.
- Launcher button styling is enforced through a shared `BasicButtonUI`-based theme path so all runtime buttons (auth, tabs, action rows, settings cog, and stat +/- controls) render consistently across platform look-and-feels.
- Account tab active-state now uses button highlight styling (background/border emphasis) instead of relying on disabled/dimmed tab text.
- Launcher text styling is normalized to one shared theme font family/color token across labels, buttons, update controls, and rendered patch-note/log text.
- Dropdowns are standardized through a reusable themed combo-box class (shared renderer + arrow button UI) to avoid per-screen styling drift and remove platform-default white dropdown surfaces.
- Scroll containers are standardized through a reusable themed scroll-pane class so list/details/editor panes share consistent opaque/transparent surface behavior, including themed scrollbar track/thumb rendering.
- Auth screen now includes a compact built-in updater panel (`Update & Restart`, status text, release-notes preview, build label).
- Auth updater panel now hydrates release notes/feed metadata from backend DB-backed release summary when reachable, with local patch-note fallback.
- Cog menu is hidden on the auth screen and remains available only after login.
- Cog dropdown still includes updater entry for authenticated flows.
- Updater and log-viewer actions are now decoupled in the cog dropdown:
  - all authenticated users keep `Update & Restart`,
  - admin-only `Log Viewer` opens log surfaces without starting update checks.
- While gameplay scene is active, cog dropdown is restricted to `Settings`, `Logout Character`, `Logout Account`, and `Exit` only.
- Cog dropdown styling uses the same launcher theme palette (earth-tone background, gold text, themed borders/hover states).
- Cog dropdown menu items use a themed basic menu-item UI delegate so hover/selection highlights stay in-theme (no platform-default blue highlight bleed).
- Cog dropdown includes a logged-in-only header line with account identity (`Welcome username.`) outside gameplay scene.
- Combined auth uses a single centered panel (no large shell frame on auth screen) with login/register toggle, centered fields, and bordered solid input styling.
- Combined auth panel now includes a direct `Exit` button alongside login/register actions.
- Register mode now uses `Register` + `Back` actions (instead of `Use Login`) for clearer return-to-login flow.
- Pressing Enter in auth inputs submits login/register depending on current toggle mode.
- Auth screen now enforces explicit Tab/Shift+Tab focus chains across visible auth inputs for both Login and Register modes.
- Auth form pre-validates email/password/display-name constraints client-side to mirror backend schema and reduce avoidable 422 responses.
- Login form includes an optional MFA OTP field and forwards `otp_code` on login when provided.
- Auth error mapping includes explicit UX strings for wrong credentials (`This account doesn't exist`) and common connectivity failures (offline, timeout, server unavailable, SSL errors).
- Launcher persists lightweight auth preferences in `launcher_prefs.properties` under install root:
  - `last_email` for login prefill.
  - `auto_login_enabled` toggle.
  - `auto_login_refresh_token` for startup refresh-auth.
- Login mode pre-fills `last_email`, while register mode is always reset to empty inputs so hint text remains visible.
- Settings menu item in the cog dropdown is only available when authenticated.
- Authenticated settings now open as a full in-launcher screen (not a popup) with a sidebar tab layout (`Video`, `Audio`, `Security`) and a large section panel.
- Video settings support `Borderless Fullscreen` and `Windowed` modes and apply immediately on change.
- Audio settings support mute toggle and master volume slider (persisted for runtime audio integration).
- Security settings expose MFA status plus a single toggle-based enable/disable flow that does not require OTP entry in settings.
- MFA setup/enrollment QR now renders inline in a two-column Security panel (QR preview + secret/URI details), with `Refresh QR` and `Copy URI` helpers.
- MFA settings toggle executes enable/disable directly, automatically reverts visual toggle state on API failure, and refreshes status from `/auth/mfa/status` after each successful toggle.
- MFA disable now clears the stored TOTP secret server-side (`mfa_totp_secret=NULL`, `mfa_enabled=false`) so later re-enable always requires fresh QR enrollment.
- Login MFA challenge now triggers only when `mfa_enabled=true`; accounts with a configured secret but MFA toggled OFF must be able to authenticate without OTP.
- Automatic login remains a persisted user setting, but launcher startup always requires manual login to keep startup deterministic on the auth screen.
- Stored auto-login refresh tokens are only used after an authenticated session updates settings, and are not consumed during app startup.
- Cog dropdown also exposes a logged-in-only `Logout` action.
- Account menu is account-only (no chat/guild panels).
- Account shell now keeps a persistent tab bar (Create/Select) visible across authenticated cards.
- Post-auth default routing always opens `Character List` (including empty accounts).
- Character List now uses a 3-column shell: roster rail (left), selected character podium preview (center), and detail/action panel (right).
- Character List columns now use fixed-width side rails plus an expanding center panel (non-draggable), preventing accidental column collapse/overlap from splitter drift.
- Character row preview/details selection is driven by card-row clicks only.
- `Play` and `Delete` actions are bound to the currently selected character in the right detail panel.
- Admin spawn-override selection is bound to the selected character in the detail panel.
- Launcher still syncs backend selected-character state implicitly on `Play` to satisfy character-gated backend features.
- Character selection uses fixed-size themed character cards in the roster rail with a separate location metadata line.
- Character cards use fixed-height row layout and horizontal-scroll suppression so the list fits within the selection viewport.
- Admin-only launcher controls (level-builder tab and per-character play-level override dropdown) are gated via `SessionResponse.is_admin` from backend auth flows, not hardcoded email checks.
- Cog dropdown admin menu includes `Level Editor`, `Level Order`, `Asset Editor`, and `Content Versions`.
- Asset Editor now uses a staged workflow:
  - `Save Local` records item edits in a persistent local draft queue (`asset_editor_local_draft.json`) that survives launcher restarts.
  - Right-side pending-changes panel tracks staged items before publish.
  - `Publish Changes` writes staged domains to the current backend content draft and clears local staged changes on success.
- Level Editor now uses a staged workflow parallel to Asset Editor:
  - `Save Local` records level payload edits in a persistent local draft queue (`level_editor_local_draft.json`) that survives launcher restarts.
  - Right-side pending-changes panel tracks staged level drafts before publish.
  - `Publish Changes` writes all staged levels to backend `/levels` and clears local staged changes on success.
- Content Versions screen provides:
  - searchable version-history cards,
  - clear active-version badge/highlight,
  - `Publish` (activate draft/validated) and `Revert To` (activate retired) controls,
  - compare mode with two searchable version selectors and side-by-side item-state rendering with changed-item markers.
- Level-builder tool now supports layered tile editing with an active-layer selector, per-layer visibility toggles, and a fixed-size side asset palette split into 3 layer columns (Layer 0/1/2) with expansion-ready fixed-size asset boxes.
- Asset palette entries render visual previews/icons and themed hover tooltips so asset semantics are discoverable in-editor.
- Level-builder now includes transition assets (`stairs_passage`, `ladder_passage`, `elevator_platform`) with per-cell destination-level configuration dialogs.
- Level save payload now includes transition-link metadata in addition to layered tile payloads.
- Level-builder is rendered in a dedicated scene (outside account card stack) with compact top controls for faster editing workflows.
- Level-builder scene header strip now contains `Reload`, `Load`, `Save Local`, `Publish Changes`, and `Back`, plus the load-dropdown and level-name input placed adjacent to their respective actions.
- Level-builder header now includes technical `name`, player-facing `descriptive_name`, and optional `order_index` inputs used by tower-floor routing/order.
- Level-builder header input widths are intentionally compact (`name`, `descriptive_name`, `order_index`) so `Save Local` remains visible on narrower window widths.
- Lower editor rows are reserved for level-editing controls and viewport/grid inputs.
- Level-builder grid defaults to a large logical footprint (`100000x100000`) and uses viewport panning for editing.
- Level-builder top controls are split into two compact rows and grid canvas minimum size is constrained so the scene stays within visible screen bounds on common desktop resolutions.
- Level-builder grid dimensions are user-editable at runtime (`width`/`height`) with validation and immediate canvas resize/clamping.
- Level-builder grid size controls are positioned with the grid header (above the editor canvas) for quick on-the-fly sizing while editing.
- Level-builder grid is now virtualized/pannable and supports up to `100000x100000` logical dimensions without allocating a full pixel canvas of that size.
- Level-builder canvas now renders a radar-ping spawn marker placeholder rather than character art for clearer spawn-point editing.
- Level-builder save/load payload uses explicit layered schema (`schema_version=2`) and keeps backward compatibility with legacy wall-only payloads.
- Admin `Level Order` scene provides explicit reorder controls (move up/down) and publishes ordering to backend via `POST /levels/order`.
- Admin `Level Editor` and `Asset Editor` panels now use larger near-full-height content layouts to maximize vertical workspace within the launcher shell.
- Admin editor scene/panel sizing is expanded toward near full-screen usage, and Asset Editor side rails (left card list + right pending list) are compacted with smaller asset icons to prioritize the central edit pane.
- Manual refresh buttons were removed from authenticated screens; character data now refreshes automatically on relevant transitions and mutations (post-login routing, show select, create, delete).
- Gameplay world is hosted in a dedicated scene container separate from account-card rendering; it is entered from character-row `Play` only.
- Scene card containers are now pinned to full client bounds (single fullscreen card cell) so gameplay/editor/auth shells do not inherit small preferred-size layout behavior.
- `play` scene is currently an empty-world prototype with in-launcher gameplay handoff and WASD movement.
- While launcher-hosted gameplay is active, root launcher background art/title/footer are disabled so world rendering uses full client area.
- World prototype enforces border collision at the edge of the playable area to prevent out-of-bounds movement.
- When a character has an assigned `level_id`, gameplay loads layered level data and renders deterministic layer order (`0 -> 1 -> player -> 2`).
- If a character has no `level_id`, launcher falls back to backend `GET /levels/first` and enters the first ordered tower floor.
- Runtime preloads linked destination floors when player approaches transition cells and swaps floors in-scene when stepping on configured transitions (no separate loading card).
- Runtime collision map is derived only from configured collision-layer assets on layer `1` (currently `wall_block`, `tree_oak`) plus world-edge collision.
- Launcher persists character runtime location through `POST /characters/{id}/location` when leaving gameplay (or logout/close while in gameplay) and resumes from saved coordinates on next play session.
- Character creation/select screens are structured for art integration (sex-based appearance choice + preview panel) and can load art assets from `assets/characters/` in working dir, install root, payload root, or `GOK_CHARACTER_ART_DIR`.
- Character creation preview now renders a static idle-frame preview (sex/appearance-driven) without a preview-animation mode selector.
- Character art discovery now supports recursive folder scanning and fallback filename matching (in addition to canonical `karaxas_*` names) to reduce preview failures when art files are renamed or moved.
- Character art discovery also probes ancestor directories from `user.dir` so previews keep working when launcher is started from `repo/launcher` (not only repo root or installed payload paths).
- Sex-to-appearance mapping now uses token-safe matching (`female`/`male` boundary checks) to avoid substring collisions like `female` matching `male`.
- Preview image scaling is aspect-preserving with nearest-neighbor interpolation to keep sprite proportions and pixel art sharpness.
- Create-character preview rendering now targets a fixed preview surface size so initial render and sex-switch updates keep identical zoom.
- Level tile discovery now scans `assets/tiles/` roots (repo, install, payload, ancestor cwd roots, and optional `GOK_LEVEL_ART_DIR`) for layered map sprites.
- Release packaging copies `assets/characters/` into payload (`payload/assets/characters`) so installed launcher builds can resolve preview art without relying on local repo folders.
- Release packaging also copies `assets/tiles/` into payload (`payload/assets/tiles`) so layered level art is available in installed builds.
- Launcher fetches `/content/bootstrap` on startup and caches the last known good snapshot as `content_bootstrap_cache.json`.
- Launcher falls back to cached content when network fetch fails.
- Launcher blocks character creation/gameplay when no valid content snapshot exists.
- Character creation point allocation now uses content-driven point budget/stat caps with +/− controls for stats and themed rectangular toggle choices for skills.
- Character creation now uses expanded two-column stat allocation rows and includes scaffold dropdowns (race/background/affiliation) above the skills area.
- Stat allocation rows now use fixed-size cards with square +/- controls and companion fixed-size description cards for each stat entry.
- Skill selection uses fixed-size square themed buttons arranged as two rows with six slots per row.
- Skill hover details are rendered through a shared HTML tooltip template containing name, costs (mana/energy/life), effects, damage+cooldown, type tag, and description sections.
- Skill/stat labels, descriptions, and tooltips are sourced from active content payloads (with embedded defaults only as fallback).
- Tooltip rendering is now explicitly themed via UI defaults (background/foreground/border/font) and tuned ToolTipManager timings (short initial delay, long dismiss delay, zero reshow delay) for more stable hover behavior.
- Character creation now renders Name/Sex/Race/Background/Affiliation in one horizontal identity row, with fixed-size stats/skills tables and fixed-size row controls to prevent layout drift.
- Character creation action row now includes a live point-budget label (`x/N points left`) anchored immediately left of the `Create Character` button.
- Launcher character create API payload now forwards race/background/affiliation and backend persists them in `characters`; list/create responses return those fields for UI/detail rendering.
- Backend character creation now initializes new characters at the first ordered floor spawn (`levels.order_index` ascending) when at least one floor exists.
- Gameplay movement speed baseline now reads from content tuning (`tuning.movement_speed`) instead of hardcoded launcher constants.
- Service error formatting now maps `401/403` and `invalid token` responses to a clear session-expiry message (`Session expired or invalid token. Please log in again.`), including level-builder operations.
- Character selection panel title is now sourced from the list container border (`Character List`) and the details panel title is `Character details`.
- Character preview rendering normalizes sprite frames to a fixed preview canvas before scaling, keeping sex-switch preview zoom consistent.
- Character art integration now supports both 4-direction and 8-direction walk/run sheets (auto-detected from filenames/sheet metadata) with deterministic runtime fallback to 4-direction behavior.
- Isometric migration target keeps full 8-direction action coverage (`N`,`NE`,`E`,`SE`,`S`,`SW`,`W`,`NW`) as the primary runtime direction contract.
- Assets content domain now includes modular equipment slot/visual metadata (`equipment_slots`, `equipment_visuals`) with backend validation and launcher bootstrap parsing for paperdoll rollout.
- Rendering mood baseline targets warm/vibrant palette + soft lighting, while data-driven effect layers are expected to support per-item/per-character/per-zone overrides for darker/grim presentation without replacing base assets.
- Character creation and deletion both perform immediate character-list reloads and UI refreshes to avoid stale list state.
- Account cards now render on opaque themed surfaces to prevent visual overlap artifacts when switching tabs.
- Updater is accessible directly on auth (embedded panel) and through cog menu / updater card for authenticated flows; it remains removed from lobby tab navigation.
- Update card layout uses explicit inner padding; build/version text and patch notes are inset from the brick frame with hidden scrollbars (wheel scroll remains enabled).
- Update flow now uses status-text updates only (no visual progress bar), so updater state is communicated without extra bar controls.
- Updater no-update terminal status is normalized to `Game is up to date.`.
- Updater no-update path never auto-restarts launcher runtime; restart is only triggered when an update is actually being applied.
- Update helper applies Velopack updates in silent mode and is built as a windowless helper executable to reduce updater pop-up windows during apply/restart flow.
- Launcher/update-helper no longer inject or resolve GitHub/Velopack repository tokens in client runtime update flow; update source is the backend-provided GCS feed URL.
- Launcher now keeps a dedicated realtime event websocket (`/events/ws`) active while authenticated and responds to publish-drain events by returning non-admin users to auth after state-save.
- Launcher now publishes active-floor scope and adjacent-floor preview scope over realtime events; backend zone presence fanout is filtered by this scope to prevent cross-floor ghost events.
- Gameplay loop updates (movement/preload/transition/presence emit) are now hard-gated to visible gameplay scene state to prevent background scene overlap artifacts.
- Version/date is rendered in a centered footer on the launcher shell.

## Logging Strategy
- Launcher logs to local files in install-root `logs/` (launcher, game, updater logs).
- Backend logs to Cloud Logging via structured application logs.
- Version/auth failures and force-update events are logged on backend.
- Auth/session security events are also persisted in immutable `security_event_audit` rows and surfaced via ops APIs/metrics.
- Error responses include `X-Request-ID` so launcher/user reports can be correlated directly with backend logs.

## Security Baseline
- Access token: JWT (short-lived, HS256 via `PyJWT`).
- Refresh/session token: stored as hash in DB with rotation and replay detection (reuse triggers bulk session revocation).
- Passwords: bcrypt hash via passlib.
- Account auth hardening: TOTP-enabled MFA APIs for all authenticated users plus shorter admin refresh-session TTL.
- MFA status reads now resolve against a fresh DB user row on each request (`/auth/mfa/status`) to prevent stale session-context state in security UI.
- Ops endpoint auth: `x-ops-token` header backed by `OPS_API_TOKEN` secret.
- Websocket auth uses one-time short-lived ws tickets (`POST /auth/ws-ticket`) instead of bearer-token query params.
- Backend returns sanitized error envelopes (with request id/path/timestamp) and no raw exception payload leakage.
- Security middleware enforces secure response headers, optional CORS allowlist, and request-body size caps.
- Auth/chat writes are guarded by per-IP/per-account rate limits with lockout/backoff.
- DB transport defaults to `sslmode=require` unless explicitly overridden.
- Deploy script supports Secret Manager references (`*_SECRET_REF`) for runtime secrets.
- Privileged actions are persisted in immutable audit tables (`admin_action_audit`, publish-drain audit tables).
- Security telemetry is persisted in immutable `security_event_audit` and exposed at `GET /ops/release/security-audit`.

## Strategic Architecture Status
### 1) Layered World/Level Data (Implemented)
- Level content model now supports explicit render/edit layers with deterministic ordering.
- Current reserved semantics:
  - `layer 0`: ground/foliage/background tiles.
  - `layer 1`: gameplay entities/obstacles (collision-relevant).
  - `layer 2`: ambient/weather/overlays (non-collision by default).
- Runtime collision extraction is now layer-filtered and asset-filtered.
- Legacy single-layer level payloads are auto-adapted to layered format on read/save paths.
- Launcher golden tests now cover layered payload serialization/deserialization plus legacy wall fallback.

### 2) Data-Driven Content Snapshot System (Implemented Baseline)
- Content domains currently active:
  - progression curves and level-up rewards,
  - skill/stat numeric tuning and coefficients,
  - tooltip/description text payloads,
  - UI option catalogs (dropdown/radio/menu choices),
  - shared constants (movement speed, attack speed, cooldown families, etc.).
- Backend remains formula-authoritative; content values are inputs to formulas, not replacements for logic code.
- Content versioning model uses:
  - immutable `content_version` snapshots,
  - publish state transitions (`draft` -> `validated` -> `active`),
  - atomic active-version swap in backend cache.
- Backend startup seeds/repairs required domains and keeps an in-memory active snapshot cache.
- Launcher consumes content snapshots for character-create options/tooltips and local tuning constants.
- Launcher persists last known good content cache and blocks gameplay/create when no valid snapshot exists.
- Deterministic tests validate sample skill execution against content snapshot values.

### 3) Content Publish Session-Drain Flow (Implemented)
- Admin publish/release activation now triggers a persisted drain window (`publish_drain_events`) for non-admin sessions (admins remain exempt).
- Implemented drain sequence:
  1. lock publish drain capacity (prevents overlapping drains),
  2. mark non-admin sessions as `draining` with deadline + reason,
  3. flush/despawn selected-character world presence before cutoff,
  4. broadcast `content_publish_started` and warning events over websocket,
  5. revoke draining non-admin sessions at cutoff (`content_publish_forced_logout`),
  6. enforce deterministic API/auth denial (`publish_drain_logout`) after deadline.
- Audit tables capture publisher, reason/version keys, targeted sessions, persistence/despawn success counts, revocations, and cutoff time.
- Emergency rollback is available via `POST /content/versions/rollback/previous`.

### 4) Rollout/Hardening Approach (Implemented Baseline)
- Feature-phase controls are available via environment flags:
  - `CONTENT_FEATURE_PHASE` (`snapshot_readonly`, `snapshot_runtime`, `drain_enforced`),
  - `PUBLISH_DRAIN_ENABLED`,
  - `REQUEST_RATE_LIMIT_ENABLED`.
- Operational visibility endpoints:
  - `GET /ops/release/feature-flags`
  - `GET /ops/release/metrics`
  - `GET /ops/release/admin-audit`
- `GET /ops/release/metrics` now includes `zone_runtime` telemetry:
  - preload latency samples (success/failed),
  - transition handoff success/fail/fallback counters,
  - zone-scope update count,
  - zone-broadcast event/recipient counters.
- Content contract compatibility is signed and enforced:
  - `/content/bootstrap` includes `content_contract_signature`,
  - launcher forwards `X-Client-Content-Contract`,
  - backend blocks non-admin auth on contract mismatch.
- Runbooks and go/no-go checklists are documented in:
  - `docs/OPERATIONS.md`
  - `docs/SECURITY.md`
  - `docs/TOWER_ADMIN_CHECKLIST.md`.

## Documentation Rule
This file is the single source of truth for technical information.

Any technical decision change is incomplete until this file is updated in the same change.
