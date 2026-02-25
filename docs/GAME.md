# Children of Ikphelion - Game

## High Concept
Children of Ikphelion is an online top-down ARPG.

Current direction:
- Runtime presentation is 2D spritesheet-driven.
- Core gameplay model remains Path of Exile-like (instance-based online ARPG progression).
- UI direction is being rebuilt to a lighter, more pleasant visual style.

## Core Pillars
- Fast, readable top-down combat and movement.
- Character identity through presets, passives/actives, gear, and progression.
- Server-authoritative gameplay values and progression.
- Online account flow with secure auth and MFA.
- Cohesive themed UI across auth/account/world surfaces.
- Login/auth UI should remain concise and player-facing (minimal redundant copy, no internal config/version jargon in main notes text).

## Runtime Flow
1. Launcher starts client and checks updates.
2. User logs in or registers.
3. Optional MFA challenge when enabled.
4. User enters account/character hub.
5. User creates/selects character and presses `Play`.
6. Client requests backend world bootstrap for the selected character.
7. Client joins a gameplay instance (solo/party) or hub zone.

## Online ARPG Model
- **Solo default**: gameplay entry without a party creates/joins a private instance.
- **Party play**: grouped players share instance routing.
- **Town hubs**: shared social visibility.
- **Gameplay zones**: only same-instance players are relevant.

## Character and Account Flow
- Character list/create/select/play remains the primary account loop.
- Account list view remains default even for empty character sets.
- Character list/create no longer use small preview cards.
- The large center account canvas is now reserved for a skill-tree graph surface.
- Character creation stays preset-driven with minimal onboarding fields: name, type, sex.
- Character type lore remains visible in create flow.
- If no character is selected in list view, the list skill-tree graph is intentionally empty.
- Navigation is sidebar-first: auth/account/settings/update/logout/quit actions are presented in a persistent left menu instead of a popup cog menu.
- Sidebar is a compact left-side navigation rail, vertically centered on screen.
- Sidebar menu actions are vertically centered inside that rail and in-content back/exit navigation is intentionally removed.
- Sidebar active menu state is highlighted as selected (not rendered as disabled).

## Skill Tree Direction
- Account list/create screens now include a graph-style skill tree panel as the primary center interaction surface.
- Current implementation is a baseline node/edge interaction scaffold and will be expanded in future iterations.

## Character Art Direction
- Runtime character baseline is 2D spritesheets at **512x512 frame size**.
- Movement/action presentation is standardized to a 2-direction baseline (`E/W`) suitable for mirrored/flipped ARPG presentation.
- Character visuals must support modular equipment overlays so worn gear is visible on player sprites.

## In-Game Systems Direction
- Character Sheet and Inventory are planned first-class in-world ARPG systems.
- Gear changes must propagate to modular sprite composition.

## Tooling Direction
- Game client is runtime-only.
- Level/asset/content authoring is provided through a separate designer tool program.
- Designer publish is backend-mediated for repo/CI orchestration (commit + workflow dispatch path).

## Authority Model
- Server is authoritative for gameplay values and progression.
- Client is authoritative only for presentation and input intent.
- World entry context is backend-authored per bootstrap payload.

## Data Ownership Boundaries
- DB stores durable account/character/progression state.
- Gameplay tuning/config is backend-managed runtime config.

## Security Baseline
- JWT access/refresh session flow.
- Optional MFA setup/challenge flow.
- Server-side validation for gameplay-critical operations.
- Publish drain/version enforcement remains active.

## Update Policy
- Velopack + GCS remains release/update channel.
- Client can trigger update from UI.
- Login requires an up-to-date build (`client_version` must match latest published build).
- Update UX includes themed in-client update status with persisted updater state.
- Release notes are surfaced under the dedicated `Update` menu (not embedded in auth/account screens).
- Update notes use a hybrid source: backend per-build notes first, packaged local notes only as fallback.
- Update notes always include the installed build version header before player-facing bullet points.
- Player-facing update surfaces show only installed client build metadata; backend `latest_version` is not displayed to players.

## Out of Scope (Current Pivot Stage)
- Full economy/trade implementation.
- Matchmaking automation beyond direct party flow.
- Large social system redesigns before core loop stabilization.

## Documentation Rule
`docs/GAME.md` is the canonical product source of truth.
Any gameplay/product change is incomplete until reflected here in the same change.
