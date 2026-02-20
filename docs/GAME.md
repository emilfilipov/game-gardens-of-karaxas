# Gardens of Karaxas - Game

## High Concept
Gardens of Karaxas is now an online multiplayer RPG with account-based progression.
Players authenticate into an account menu shell where they manage social/community interactions,
create/select characters, and enter gameplay sessions.

## Core Pillars
- Persistent account identity with secure login sessions.
- Character-gated game session entry from character list row actions.
- Flexible character identity via point distribution into stats and skills.
- Live-service readiness through version-gated updates and controlled rollout windows.
- Launcher-driven desktop distribution and patching.
- Visual direction baseline: warm/vibrant color palette with soft global lighting; mood can be shifted per item/character/zone via effects toward darker grim-themed presentation.

## Isometric Direction Lock
- `GOK-MMO-174` is approved and locked through `docs/ART_DIRECTION_BOARD.md`.
- `GOK-MMO-175` is approved and locked through `docs/ISOMETRIC_COORDINATE_SPEC.md`.
- Projection choice is locked to `2:1` isometric (dimetric) with MMO-friendly slightly zoomed-out camera baseline.
- Baseline look stays warm/vibrant and readable; mood darkening is handled through effect layers (per-zone/per-item/per-character), not by replacing global base style.

## Account and Menu Loop
1. Open launcher and authenticate (register or login).
   - Login form remembers and pre-fills the last successfully authenticated email.
   - Register form always opens clean with hint text visible.
   - Register mode actions are `Register` and `Back` (returns to login mode).
2. Enter account menu with persistent tab navigation (Create/Select).
   - Top-right menu shows `Welcome username.` and logged-in account actions.
   - Admin-only menus/features are unlocked by the account's backend `is_admin` flag (not by hardcoded email).
   - Authenticated tab order is `Character List` (left) and `Create Character` (right).
   - Admin tools (`Level Editor`, `Asset Editor`, `Content Versions`) are opened from the top-right cog menu.
3. Default post-login routing:
   - No characters: open Character Creation.
   - Has characters: open Character Selection.
4. On character selection, each row includes direct `Play` and `Delete` actions.
   - Character preview/details update only when the character card row itself is clicked.
   - Action buttons do not change the current preview selection.
   - Admin accounts also get a per-character level override dropdown in each row; choosing a level there forces spawn at that level's spawn point for that play launch.
   - Character rows show current location (area + coordinates when known).
5. Enter gameplay session from the chosen character row (`Play` action on that row only).
   - World/session opens in a dedicated gameplay scene (separate from lobby/select cards).
   - Runtime host switch now exists: default flow uses the in-launcher gameplay scene; Godot host mode can launch external game runtime for the same character handoff.
   - In launcher-hosted gameplay, launcher title art/chrome is hidden so the world scene uses the full client area.
   - If the character has a map assignment, the session loads that level/floor layout and spawn.
   - New characters now start on the first tower floor (lowest configured floor order) at that floor's spawn point.
   - Returning characters resume from their persisted location (floor + coordinates).
   - Character location is persisted (floor/level + coordinates) so the next login resumes from the last saved position.
6. Move inside the world prototype with WASD; world-edge borders block out-of-bounds movement.
   - Collision currently comes from layer-1 collidable tiles (for example walls/trees) from the loaded level.
   - Transition assets (`stairs`, `ladder`, `elevator`) allow seamless floor-to-floor travel without loading screens.
   - Adjacent linked floors are preloaded when the player approaches a transition trigger zone.
   - Runtime renders only the active floor scene; adjacent floors are preload-only until transition handoff.
7. Authenticated players can open a full Settings screen from the top-right menu.
   - Settings screen uses sidebar tabs: `Video`, `Audio`, `Security`.
   - `Save` prompts with a themed confirmation modal when changes exist and keeps edits if user chooses `No`.
   - `Cancel` prompts with a themed confirmation modal when unsaved changes exist before leaving settings.
   - `Video` includes screen mode (`Borderless Fullscreen` / `Windowed`).
   - `Audio` includes mute toggle and master volume slider.
   - `Security` includes MFA setup/status and a compact MFA toggle flow for all users.
   - MFA toggle is applied with a single on/off control plus adjacent authenticator code field.
   - MFA setup displays a scannable QR code (plus copy secret/URI actions) in a fully themed enrollment popup with no placeholder/system dialog chrome.
   - Once MFA secret enrollment exists for an account, login requires a valid MFA code (password-only login is blocked).

## Required Frontend Screens
- Combined authentication screen (login/register toggle in a single centered block) with integrated updater/release-notes panel.
  - Auth panel includes a direct `Exit` action so players can close the game without authenticating.
- Account menu shell screen (Create/Select tabs).
- Character creation screen.
- Character selection screen.
- In-game world screen.
- Authenticated settings screen (sidebar tabs + central settings panel + explicit save/cancel confirmation flow).
- Admin-only level builder screen (load named layered levels, stage local drafts, and publish queued level changes with spawn + tile/object layout).
- Admin-only level-order screen (drag/drop floor cards to reorder tower progression and publish order).
- Admin-only asset editor screen (searchable editable-content cards + large item editor panel + right-side staged-change queue with `Save Local` and `Publish Changes`).
- Admin-only content versions screen (version history cards, active-version highlight, publish/revert controls, and side-by-side compare).
- Shared menu/form controls use a consistent thin-border panel/button style over the same background key art.

## Character Direction
- No predefined classes.
- Character creation uses a content-driven point budget (current default: 10).
- Players distribute points into stats and skills.
- Each stat/skill increase costs 1 point.
- Character names are globally unique (case-insensitive).
- Characters start at level 1 with 0 XP.
- Level progression uses content-driven XP requirements (current default: 100 XP per level).
- Character creation includes sex choice (current presets: male/female) with visual preview.
- Character creation preview is currently static (idle frame) and no longer includes a preview-animation selector.
- Sex switching must always map to the correct preset in both directions (male->female and female->male) without substring ambiguity.
- Character preview rendering preserves sprite aspect ratio to avoid stretching between male/female presets.
- Character creation preview uses a fixed render target so initial load and sex-switch states keep the same zoom level.
- Character creation layout uses split tables: expanded multi-column stats on the left and skill choices on the right.
- Stats allocation rows now use fixed-size cards with square `- / +` controls and a right-side short description card per stat.
- Stats scaffold is expanded to include additional placeholders beyond the base six stats.
- Level-1 starter skills currently scaffolded: Ember, Cleave, Quick Strike, Bandage.
- Skill choices use fixed-size square themed buttons with six slots per row.
- Skill hover tooltips use a standardized info template:
  - full name
  - mana/energy/life cost
  - effects
  - damage and cooldown
  - skill type tag
  - description box
- Current starter skill tooltips are loaded from active content data.
- Skill tooltips are themed to the game palette and stay visible longer for reliable hover inspection.
- Character creation identity controls are aligned in one horizontal row: Name, Sex, Race, Background, Affiliation.
- Character creation footer shows a live point budget label (`x/N points left`) beside the `Create Character` action.
- Character creation selections are persisted on character records (stats, skills, race, background, affiliation, appearance).
- Character creation now also persists a per-character equipment loadout map (slot -> item visual key) for future modular visual rendering.
- Character art loading accepts both canonical filenames and fallback naming/folder layouts so male/female previews continue working when asset files are reorganized.
- Initial visual presets currently wired: human male and human female.
- Launcher runtime now supports 8-direction movement/action sprite sheets (`N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`) with automatic fallback to existing 4-direction sheets.
- Modular equipment-driven visuals are now scaffolded in DB content (slot + item visual definitions + default slot mappings), with full render layering/paperdoll rollout still in progress.
- Exact stat/skill catalogs are intentionally deferred to a later design pass.

## Social Scope (Current)
- Chat and guild management UX are deferred while world-entry and character/session scaffolding are being hardened.
- Guild management remains planned as a dedicated in-game follow-up menu/screen.

## Update Policy
- Launcher/updater remains the distribution and update authority.
- Backend enforces release policy for both build version and content version with a grace window.
- Current grace window target: 5 minutes before forced update lockout.
- Optional automatic login is configured from in-session settings only (not from pre-login auth screen).
- Startup always opens on the authentication screen; players must explicitly log in each launch.
- Pre-login updater access is embedded directly in the authentication screen (`Update & Restart` + compact release notes).
- Updater access is no longer a lobby tab; authenticated users can still access updater from the top-right menu.
- Updater progression is shown through status text messages in the update screen (no progress bar widget).
- When no update is available, updater status reads `Game is up to date.`.
- Release metadata and release notes are sourced from backend database records (not launcher-bundled static notes only).
- Admin content publishes now also advance a logical release/build marker in release metadata even when no new binary build is produced.
- Login is blocked for non-admin users until client build and client content version are aligned with currently published release policy.
- Login is also blocked for non-admin users when client/backend content contract signatures diverge, preventing incompatible live-data schemas.
- On publish, non-admin players are forced out after grace window and returned to login, where they can choose when to click `Update & Restart`.
- Publish-triggered drain warnings are delivered live during active sessions and end in forced return to login for non-admin users at cutoff.
- When `Update & Restart` finds no binary package delta, launcher still restarts in admin-publish flows to re-sync content snapshot and complete relog/update gating.
- Update feed source is GCS-backed Velopack hosting.
- Admin level editor now uses a larger, zoomed-out grid and shows a radar-ping marker at spawn position.
- Admin `Level Editor` and `Asset Editor` now occupy a larger near full-screen workspace; Asset Editor side columns/icons are reduced to give more room to the main edit surface.
- Admin level editor grid dimensions can be edited on the fly (width/height) before saving levels.
- Admin level editor now keeps `Reload`, `Load`, `Save Local`, `Publish Changes`, and `Back` in the top strip; the strip also contains the `Load Existing` dropdown and `Save Level` name box.
- The editor body below is focused on build controls and grid interaction only.
- `Save Local` requires a non-empty level name and stages current grid size, spawn, and layered tile/object data in a persistent local draft queue.
- `Publish Changes` writes all staged local level drafts to the backend and clears the local queue on success.
- Level builder opens as a separate dedicated scene for admins.
- Level builder now uses a compact control strip and a virtual panning grid that supports up to 100000x100000 logical dimensions.
- Level builder includes a fixed-size side palette split into 3 fixed-width columns (Layer 0/1/2), with fixed-size asset boxes for expansion-ready asset catalogs.
- Asset boxes render visual previews and provide hover tooltips describing each asset and its intended usage.
- Level builder now supports transition assets (`stairs`, `ladder`, `elevator`) and per-cell destination linking to other levels.
- Level builder now includes both technical level name and descriptive level name fields; descriptive names are used for player-facing floor labels.
- Level builder includes a right-side pending-drafts panel so admins can review staged changes before publishing.
- Staged level drafts persist across launcher restarts until published.
- In-game cog menu is now minimized to gameplay actions only: `Settings`, `Logout Character`, `Logout Account`, `Exit Game`.
- Admin tower-floor QA checklist for linked-level validation is maintained in `docs/TOWER_ADMIN_CHECKLIST.md`.
- Level builder supports explicit rendering layers with active-layer editing and visibility toggles:
  - Layer 0: ground/foliage (`grass` tile scaffold).
  - Layer 1: gameplay entities/obstacles and spawn tool (`wall`, `tree`, `spawn` scaffold).
  - Layer 2: weather/ambient overlays (`cloud` scaffold).

## Release Intent
- Launcher-first distribution (Windows first).
- Keep architecture portable for Linux/Steam/Android later, but Steam-specific distribution is not a current dependency.
- Runtime host direction is now locked: launcher stays the account/update shell, while gameplay/world/editor runtime migrates to Godot 4.x.

## Live Content Model (Implemented Baseline)
- Non-logic gameplay content is now delivered through database-managed configuration snapshots:
  - level-up requirements and rewards,
  - skill numerical values and tooltip/presentation text,
  - stat metadata and stat-to-skill scaling constants,
  - dropdown/radio option catalogs used by account/character menus.
- Keep formulas and authoritative execution logic in backend code; only tunable values and presentation data move to DB.
- Launcher fetches active content at startup and uses cached snapshot fallback if network fetch fails.
- If no valid content snapshot is available, character creation/gameplay is blocked until content sync succeeds.

## Content Publish Drain (Implemented)
- Content publishes now trigger a controlled non-admin session drain:
  - active sessions are tagged as draining with a cutoff deadline,
  - selected character world presence is detached before cutoff,
  - live warning/forced-logout events are delivered over realtime channel,
  - non-admin users are returned to login at cutoff and must update/relog,
  - admin sessions remain online for verification/ops.

## Open Design Decisions
- Final stats/skills taxonomy and balancing model.
- World content population and spawn/zone architecture beyond current empty-world prototype.
- Day/night system tuning per zone/floor (including reversed cycles and custom cycle speeds).
- Reintroduction sequence for in-game chat/guild UX on top of the world session screen.
- Guild management feature depth and permissions model.
- Moderation/reporting model for future chat and social systems.
- Final equipment slot taxonomy and art-quality bar for production-ready item visual variants.

## Documentation Rule
This file is the single source of truth for all non-technical game/product information.

Any gameplay/product decision change is incomplete until this file is updated in the same change.
