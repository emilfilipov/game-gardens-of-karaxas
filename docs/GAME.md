# Plompers Arena Inc. - Game

## High Concept
Plompers Arena Inc. is an online top-down arena battle royale where players control bouncy-ball fighters and compete to become the top spot holder for "bounciest ball."

This is a product refactor mandate:
- Runtime gameplay presentation pivots from 2D to 3D.
- Camera remains top-down / Path of Exile-like (high-angle, readability-first).
- Existing account flow and skill-graph viewer functionality must be preserved.
- UI style is black and white, based on `concept_art/ui_concept_blackwhite/` direction.
- World/assets default to black and white and gain color only through player interaction.

Current implemented vertical-slice baseline:
- Account/login/character flow remains active and can route into 3D runtime.
- First 3D arena fallback is a flat grass field with wall boundaries.
- Player avatar in 3D runtime is currently a plomper-ball prototype.
- Interaction currently reveals localized ground/grass/wall color feedback.

## Core Pillars
- Physics-forward bouncy-ball combat in a readable top-down 3D arena.
- Last-player-standing / top-rank arena loop with quick match pacing.
- Character progression and build expression through the retained skill graph.
- Black/white baseline world with interaction-driven color reveal as core visual identity.
- Online login/account/character continuity with server-authoritative progression values.

## Runtime Flow
1. Launcher starts client and checks updates.
2. User logs in or registers.
3. Optional MFA challenge when enabled.
4. User enters account/character hub.
5. User creates/selects character and presses `Play`.
6. Client requests backend world bootstrap for the selected character.
7. Client joins an arena instance and spawns into the 3D top-down battle map.

## Arena/Battle Royale Direction
- Match format is arena elimination/placement focused.
- Player avatar fantasy is a combat-capable bouncy ball ("Plomper").
- Primary objective: outlast/outplay opponents and secure the top ranking.
- Collision, momentum, and bounce control are first-class combat expression.
- Skill graph remains available for build strategy and progression decisions.

## Character and Account Flow
- Login/register/MFA/account/character selection flow remains intact.
- Character list/create/select/play remains the primary loop.
- Skill graph viewer remains visible and usable in account list/create context.
- Graph interactions and progression data remain compatible with backend authority model.
- Refactor may change visual shell and 3D preview behavior, but not remove the graph surface.

## UI Direction
- Canonical UI style is black/white themed.
- `concept_art/ui_concept_blackwhite/` is the primary concept reference for shell composition.
- Existing functionality remains: auth, account, character management, update, settings, and graph viewer.
- UI copy/layout should stay concise and player-facing.

## World and Asset Colorization Rule
- All environment objects, props, foliage, and interactive surfaces start in black and white.
- Color appears only where interaction happens (examples: stepped grass turns green, impact points on walls gain color).
- Color reveal is gameplay feedback, not a random post effect.
- Colorization must remain localized and readable from top-down camera distance.

## Level Direction for First 3D Vertical Slice
- Initial playable level is a flat arena surface with grass foliage.
- Level is intentionally simple to validate movement/combat readability and visual color-reveal behavior.
- Spawn flow must support login -> character select/create -> load into this level.

## In-Game Systems Direction
- Character Sheet, Inventory, and progression systems remain in scope and must survive the pivot.
- Gear/progression data contracts remain server-authoritative.
- The 3D pivot does not remove progression depth; it changes presentation and combat embodiment.

## Authority Model
- Server is authoritative for gameplay values and progression.
- Client is authoritative for presentation, input intent, and visual feedback.
- World entry context is backend-authored per bootstrap payload.

## Out of Scope (Current Refactor Cycle)
- Large non-essential social redesigns.
- Expansion maps before first arena vertical slice is stable.
- Removing existing account/graph flows in favor of temporary shortcuts.

## Documentation Rule
`docs/GAME.md` is the canonical product source of truth.
Any gameplay/product change is incomplete until reflected here in the same change.
