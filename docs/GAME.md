# Gardens of Karaxas - Game

## High Concept
Gardens of Karaxas is now an online multiplayer RPG with account-based progression.
Players authenticate into an account lobby where they manage social/community interactions,
create/select characters, and enter gameplay sessions.

## Core Pillars
- Persistent account identity with secure login sessions.
- Social-first lobby: channels, chat, friend list, and guild presence.
- Flexible character identity via point distribution into stats and skills.
- Live-service readiness through version-gated updates and controlled rollout windows.
- Launcher-driven desktop distribution and patching.

## Account and Lobby Loop
1. Open launcher and authenticate (register or login).
2. Enter account lobby.
3. Use social features:
   - Global/direct/guild chat channels.
   - Friend list visibility.
   - Guild membership/rank visibility.
4. Create a character or select an existing character.
5. Start gameplay session.

## Required Frontend Screens
- Login screen.
- Registration screen.
- Account lobby screen.
- Character creation screen.
- Character selection screen.

## Character Direction
- No predefined classes.
- Character creation uses a fixed point budget.
- Players distribute points into stats and skills.
- Exact stat/skill catalogs are intentionally deferred to a later design pass.

## Social Scope (Current)
- Chat scope now:
  - Global channels.
  - Direct messages.
  - Guild chat.
- Guild management UX is planned as a follow-up menu/screen after baseline social/chat scaffolding.

## Update Policy
- Launcher/updater remains the distribution and update authority.
- Backend enforces version policy with a grace window.
- Current grace window target: 5 minutes before forced update lockout.

## Release Intent
- Launcher-first distribution (Windows first).
- Keep architecture portable for Linux/Steam/Android later, but Steam-specific distribution is not a current dependency.

## Open Design Decisions
- Final gameplay session flow after character selection.
- Final stats/skills taxonomy and balancing model.
- Guild management feature depth and permissions model.
- Moderation/reporting model for chat and social systems.

## Documentation Rule
This file is the single source of truth for all non-technical game/product information.

Any gameplay/product decision change is incomplete until this file is updated in the same change.
