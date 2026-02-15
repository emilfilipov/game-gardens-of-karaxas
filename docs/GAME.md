# Gardens of Karaxas - Game

## High Concept
Gardens of Karaxas is now an online multiplayer RPG with account-based progression.
Players authenticate into an account lobby where they manage social/community interactions,
create/select characters, and enter gameplay sessions.

## Core Pillars
- Persistent account identity with secure login sessions.
- Character-gated game session entry: a selected character is required to enter the world.
- Flexible character identity via point distribution into stats and skills.
- Live-service readiness through version-gated updates and controlled rollout windows.
- Launcher-driven desktop distribution and patching.

## Account and Lobby Loop
1. Open launcher and authenticate (register or login).
   - Login form remembers and pre-fills the last successfully authenticated email.
   - Register form always opens clean with hint text visible.
2. Enter account lobby (account-only tools and updater access).
3. Create a character or select an existing character.
4. Enter gameplay session with the selected character.
5. Move inside the world prototype with WASD; world-edge borders block out-of-bounds movement.

## Required Frontend Screens
- Combined authentication screen (login/register toggle in a single centered block).
- Account lobby screen.
- Character creation screen.
- Character selection screen.
- In-game world screen.

## Character Direction
- No predefined classes.
- Character creation uses a fixed point budget of 10.
- Players distribute points into stats and skills.
- Each stat/skill increase costs 1 point.
- Character creation includes sex choice (current presets: male/female) with visual preview.
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
