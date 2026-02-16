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

## Account and Menu Loop
1. Open launcher and authenticate (register or login).
   - Login form remembers and pre-fills the last successfully authenticated email.
   - Register form always opens clean with hint text visible.
   - Register mode actions are `Register` and `Back` (returns to login mode).
2. Enter account menu with persistent tab navigation (Create/Select).
   - Top-right menu shows `Welcome [username].` and logged-in account actions.
   - Admin-only menus/features are unlocked by the account's backend `is_admin` flag (not by hardcoded email).
   - Authenticated tab order is `Character List` (left), `Create Character` (middle), `Levels` (right/admin-only).
3. Default post-login routing:
   - No characters: open Character Creation.
   - Has characters: open Character Selection.
4. On character selection, each row includes direct `Play` and `Delete` actions.
   - Character preview/details update only when the character card row itself is clicked.
   - Action buttons do not change the current preview selection.
   - Admin accounts also get per-character map assignment controls in each row.
5. Enter gameplay session from the chosen character row (`Play` action on that row only).
   - World/session opens in a dedicated gameplay scene (separate from lobby/select cards).
   - If the character has a map assignment, the session loads that level layout and spawn.
6. Move inside the world prototype with WASD; world-edge borders block out-of-bounds movement.
   - Wall tiles from the loaded level are also collidable.

## Required Frontend Screens
- Combined authentication screen (login/register toggle in a single centered block).
- Account menu shell screen (Create/Select tabs).
- Character creation screen.
- Character selection screen.
- In-game world screen.
- Admin-only level builder screen (save/load named levels with spawn + wall layout).
- Shared menu/form controls use a consistent thin-border panel/button style over the same background key art.

## Character Direction
- No predefined classes.
- Character creation uses a fixed point budget of 10.
- Players distribute points into stats and skills.
- Each stat/skill increase costs 1 point.
- Character names are globally unique (case-insensitive).
- Characters start at level 1 with 0 XP.
- Current level progression scaffold uses 100 XP per level.
- Character creation includes sex choice (current presets: male/female) with visual preview.
- Character creation preview is currently static (idle frame) and no longer includes a preview-animation selector.
- Initial visual presets currently wired: human male and human female.
- Exact stat/skill catalogs are intentionally deferred to a later design pass.

## Social Scope (Current)
- Chat and guild management UX are deferred while world-entry and character/session scaffolding are being hardened.
- Guild management remains planned as a dedicated in-game follow-up menu/screen.

## Update Policy
- Launcher/updater remains the distribution and update authority.
- Backend enforces version policy with a grace window.
- Current grace window target: 5 minutes before forced update lockout.
- Optional automatic login is configured from in-session settings only (not from pre-login auth screen).
- Updater access is no longer a lobby tab; it is available from the top-right menu entry.
- Updater progression is shown through status text messages in the update screen (no progress bar widget).

## Release Intent
- Launcher-first distribution (Windows first).
- Keep architecture portable for Linux/Steam/Android later, but Steam-specific distribution is not a current dependency.

## Open Design Decisions
- Final stats/skills taxonomy and balancing model.
- World content population and spawn/zone architecture beyond current empty-world prototype.
- Reintroduction sequence for in-game chat/guild UX on top of the world session screen.
- Guild management feature depth and permissions model.
- Moderation/reporting model for future chat and social systems.

## Documentation Rule
This file is the single source of truth for all non-technical game/product information.

Any gameplay/product decision change is incomplete until this file is updated in the same change.
