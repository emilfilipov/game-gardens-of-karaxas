# Gardens of Karaxas - Technical

## Purpose
This is the single source of truth for technical architecture, stack decisions, module boundaries, deployment, and CI/CD behavior.

## Runtime and Service Stack
- Launcher/runtime UI: Kotlin (JVM) Swing launcher module (`launcher/`).
- Backend services: Python FastAPI (`backend/`).
- Database: PostgreSQL (Cloud SQL), database name `karaxas`.
- Migrations: Alembic.
- Service hosting: Google Cloud Run.
- Launcher backend endpoint resolution:
  - Uses `GOK_API_BASE_URL` when explicitly set.
  - Falls back to deployed Cloud Run API URL when not set (instead of localhost), to keep production auth usable by default.

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
- Chat endpoints are now character-gated: users must have an active selected character before chat access.
- This keeps operational complexity low while preserving future split path (`api` + `realtime`) if scale requires it.

## Data Model (Initial)
- `users`: account identity.
  - Includes `is_admin` boolean for backend-authoritative admin gating.
- `user_sessions`: refresh/session records and client version tracking.
- `release_policy`: latest/min-supported version and enforce-after timestamp.
- `characters`: user-owned character builds (stats/skills point allocations).
  - Includes `appearance_key` for visual preset selection persistence.
  - Includes `level` and `experience` (starts at level 1 / 0 XP).
  - Includes nullable `level_id` to map a character to a saved world layout.
  - Includes nullable `location_x`/`location_y` for persisted world coordinates.
  - Character names are globally unique (case-insensitive unique index on `lower(name)`).
- `levels`: named level layouts (grid size, spawn cell, wall-cell list) for world bootstrapping.
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
- Backend release activation notification now retries and is non-blocking for release publishing; transient backend 5xx responses log warnings but do not fail launcher release artifacts.

## Deployment and Infra Pattern
- Cloud Run deployment pattern follows `markd-backend` operational approach.
- `backend/scripts/deploy_cloud_run.sh` builds/pushes container and deploys Cloud Run service with Cloud SQL attachment.
- Same GCP project/region/settings pattern as markd is used; only DB name differs (`karaxas`).

## CI/CD Behavior
- `.md`-only changes must not trigger deployment/release jobs.
- Launcher release workflow (`.github/workflows/release.yml`):
  - ignores markdown-only commits.
  - ignores backend path changes so backend-only commits do not ship a launcher release.
  - prefetches rolling historical delta packages (plus latest full fallback) before `vpk pack`, so update feeds support delta patching across skipped versions.
- Backend deploy workflow (`.github/workflows/deploy-backend.yml`):
  - triggers on backend non-markdown changes.
  - deploys backend to Cloud Run.
  - supports either GitHub-to-GCP WIF auth or service-account JSON auth (`GCP_SA_KEY_JSON`).

## Launcher UI Structure Strategy
- UI is organized with reusable screen scaffolds and layout tokens (`UiScaffold`) to keep alignment consistent across screens.
- Screens are card-based (combined auth, character creation, character selection, update, play) instead of one-off ad hoc layouts.
- Launcher now defaults to borderless fullscreen and keeps a top-right settings menu entry point.
- Launcher keeps the same full-screen background art image, but interactive UI chrome now uses lightweight shape-based rendering (thin borders + painted fills/gradients) instead of PNG-framed button/panel surfaces.
- Launcher button styling is enforced through a shared `BasicButtonUI`-based theme path so all runtime buttons (auth, tabs, action rows, settings cog, and stat +/- controls) render consistently across platform look-and-feels.
- Account tab active-state now uses button highlight styling (background/border emphasis) instead of relying on disabled/dimmed tab text.
- Launcher text styling is normalized to one shared theme font family/color token across labels, buttons, update controls, and rendered patch-note/log text.
- Dropdowns are standardized through a reusable themed combo-box class (shared renderer + arrow button UI) to avoid per-screen styling drift and remove platform-default white dropdown surfaces.
- Scroll containers are standardized through a reusable themed scroll-pane class so list/details/editor panes share consistent opaque/transparent surface behavior, including themed scrollbar track/thumb rendering.
- Cog menu includes minimal updater entry (`Update & Restart`) available from auth/login flow and other screens.
- Cog dropdown styling uses the same launcher theme palette (earth-tone background, gold text, themed borders/hover states).
- Cog dropdown includes a logged-in-only header line with account identity (`Welcome [username].`).
- Combined auth uses a single centered panel (no large shell frame on auth screen) with login/register toggle, centered fields, and bordered solid input styling.
- Register mode now uses `Register` + `Back` actions (instead of `Use Login`) for clearer return-to-login flow.
- Pressing Enter in auth inputs submits login/register depending on current toggle mode.
- Auth form pre-validates email/password/display-name constraints client-side to mirror backend schema and reduce avoidable 422 responses.
- Auth error mapping includes explicit UX strings for wrong credentials (`This account doesn't exist`) and common connectivity failures (offline, timeout, server unavailable, SSL errors).
- Launcher persists lightweight auth preferences in `launcher_prefs.properties` under install root:
  - `last_email` for login prefill.
  - `auto_login_enabled` toggle.
  - `auto_login_refresh_token` for startup refresh-auth.
- Login mode pre-fills `last_email`, while register mode is always reset to empty inputs so hint text remains visible.
- Settings menu item in the cog dropdown is only available when authenticated; auto-login can only be configured there.
- When auto-login is enabled, launcher attempts `POST /auth/refresh` during startup and clears invalid refresh tokens on 401/403.
- Cog dropdown also exposes a logged-in-only `Logout` action.
- Account menu is account-only (no chat/guild panels).
- Account shell now keeps a persistent tab bar (Create/Select) visible across authenticated cards.
- Post-auth default routing is character-count based:
  - no characters -> `create_character`
  - one or more characters -> `select_character`
- Character selection is row-based with per-row `Play` and `Delete` actions (no explicit "Set Active" control in the UI).
- Character row preview/details selection is driven by card-row clicks only; per-row action buttons do not mutate preview selection.
- Launcher still syncs backend selected-character state implicitly on `Play` to satisfy character-gated backend features.
- Character selection uses fixed-size themed character cards with per-row `Play` and `Delete` actions.
- Character cards use fixed-height row layout and horizontal-scroll suppression so the list fits within the selection viewport.
- Admin-only launcher controls (level-builder tab and per-character level assignment dropdown) are gated via `SessionResponse.is_admin` from backend auth flows, not hardcoded email checks.
- Level-builder tool supports drag/erase wall placement and single spawn-point placement on a fixed grid, with named save/load against backend `/levels` APIs.
- Level-builder grid defaults to a larger map footprint (`80x48`) with a zoomed-out editor cell size to keep more of the map visible while editing.
- Level-builder grid dimensions are user-editable at runtime (`width`/`height`) with validation and immediate canvas resize/clamping.
- Level-builder grid size controls are positioned with the grid header (above the editor canvas) for quick on-the-fly sizing while editing.
- Level-builder canvas renders a spawn-cell character sprite marker (using resolved appearance art) instead of only a basic spawn dot marker.
- Manual refresh buttons were removed from authenticated screens; character data now refreshes automatically on relevant transitions and mutations (post-login routing, show select, create, delete).
- Gameplay world is hosted in a dedicated scene container separate from account-card rendering; it is entered from character-row `Play` only.
- `play` scene is currently an empty-world prototype with in-launcher gameplay handoff and WASD movement.
- World prototype enforces border collision at the edge of the playable area to prevent out-of-bounds movement.
- When a character has an assigned `level_id`, gameplay loads spawn/walls from backend level data and applies tile-based wall collision in addition to world-edge collision.
- Launcher persists character runtime location through `POST /characters/{id}/location` when leaving gameplay (or logout/close while in gameplay) and resumes from saved coordinates on next play session.
- Character creation/select screens are structured for art integration (sex-based appearance choice + preview panel) and can load art assets from `assets/characters/` in working dir, install root, payload root, or `GOK_CHARACTER_ART_DIR`.
- Character creation preview now renders a static idle-frame preview (sex/appearance-driven) without a preview-animation mode selector.
- Character art discovery now supports recursive folder scanning and fallback filename matching (in addition to canonical `karaxas_*` names) to reduce preview failures when art files are renamed or moved.
- Release packaging copies `assets/characters/` into payload (`payload/assets/characters`) so installed launcher builds can resolve preview art without relying on local repo folders.
- Character creation point allocation uses a fixed 10-point budget with +/− controls for stat/skill scaffolding.
- Skill-points counter label has been removed from UI while keeping allocation budget enforcement.
- Character art integration currently supports 32x32 idle sprites and 192x128 (4-direction x 6-frame) walk/run sheets for male/female presets.
- Character creation and deletion both perform immediate character-list reloads and UI refreshes to avoid stale list state.
- Account cards now render on opaque themed surfaces to prevent visual overlap artifacts when switching tabs.
- Updater remains accessible through the cog menu (`Update & Restart`) and updater card, but is removed from lobby tab navigation.
- Update card layout uses explicit inner padding; build/version text and patch notes are inset from the brick frame with hidden scrollbars (wheel scroll remains enabled).
- Update flow now uses status-text updates only (no visual progress bar), so updater state is communicated without extra bar controls.
- Updater no-update terminal status is normalized to `Game is up to date.`.
- Update helper applies Velopack updates in silent mode and is built as a windowless helper executable to reduce updater pop-up windows during apply/restart flow.
- Version/date is rendered in a centered footer on the launcher shell.

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
