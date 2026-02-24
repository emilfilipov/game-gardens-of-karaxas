# Children of Ikphelion - Game

## High Concept
Children of Ikphelion is an online isometric ARPG.

Play model:
- Players primarily run private gameplay instances (solo by default).
- Party members share gameplay instances when grouped.
- Shared social visibility is limited to town/hub zones.

## Core Pillars
- Fast, readable isometric combat with deep build customization.
- Character identity through creation choices, stats, skills, and equipment.
- Online account progression with secure login and MFA.
- Server-authoritative gameplay values for balance and anti-tamper.
- Branded, themed UI across all client surfaces.

## Runtime Flow
1. Launcher starts client and checks updates.
2. User logs in or registers.
3. Optional MFA challenge during login when enabled.
4. User enters account/character hub.
5. User creates/selects character and presses `Play`.
6. Client requests backend world bootstrap for the selected character (resolved level + spawn + runtime tuning snapshot).
7. Client joins a gameplay instance (solo/party) or hub zone based on destination.

## Online ARPG Model
- **Solo default**: entering gameplay without a party creates or joins a private instance for that character/session.
- **Party play**: invited party members enter a shared instance.
- **Town hubs**: players can see other players and socialize/trade.
- **Gameplay zones**: only players in the same instance are visible/relevant.

## Character Flow (Current Direction)
- Character list/create/select/play remains a first-class flow in the client.
- Current character creator and isometric runtime work are retained and iterated forward.
- Existing proven online hub/list/create UX patterns are reused as baseline while visual polish continues.
- Account hub now uses side navigation (no list/create tabs) with large center podium previews in both list and create flows.
- Character list now uses a single left sidebar: top `Create Character` action plus character cards below (no duplicate list sidebar/headline).
- Character list/create views now consume the full account content area instead of centered boxed layouts.
- Character list/create now include a dual-preview setup:
  - large primary podium preview for inspection/rotation,
  - smaller in-world-scale inset preview synced to the same facing direction.
- Character details now live in a compact bottom-right square panel over the list preview area.
- Character location persistence includes level/floor and coordinates.
- Character creation now focuses on a minimal onboarding flow: **preset + sex + name**.
- Race/background/affiliation/manual stat allocation are no longer player-facing in creation and are sourced from preset/runtime defaults.
- Current production model preset: **Sellsword** with male/female variants.
- Character art source baseline is now **384x384 per frame** (4x upgrade), 8-direction, with starter animation set:
  - idle, walk, run, attack, cast, hurt, death, sit_crossed_legs, sit_kneel.
- Runtime world rendering downsamples these source frames to gameplay scale to keep readability and performance stable.
- Base model starts unarmed and is dressed in rugged leather brigandine/boots for both male and female variants.

## Authority Model
- Server is authoritative for gameplay-relevant values and progression.
- Client is authoritative only for presentation/input intent.
- World entry context is backend-authored per session bootstrap (character + location + runtime tuning hash + version policy snapshot).

Gameplay values sourced from backend include (minimum):
- combat coefficients and base values,
- ability costs/cooldowns/scaling,
- movement and recovery tuning,
- progression breakpoints (xp curves, rewards),
- stat/skill metadata relevant to gameplay evaluation.
- character preset catalogs for base archetype identity and starter allocations.

## Data Ownership Boundaries
- Database stores durable progression and account state:
  - users/sessions,
  - characters,
  - inventory/equipment,
  - quest progression,
  - durable world/instance state as needed.
- Gameplay tuning/config is backend-managed runtime config (file/service), not DB-everything.

## Security Baseline
- Login + JWT access/refresh session flow.
- Optional MFA setup and challenge flow.
- Server-side validation for combat/progression-critical operations.
- Session drain/version enforcement remains active for forced update windows.

## Update Policy
- Velopack + GCS remains the release/update channel.
- Users can trigger update from client UI.
- Force-update policy can block old clients from login after grace windows.

## Out of Scope (for this pivot stage)
- Full economy/trade implementation.
- Matchmaking automation beyond direct party flow.
- Large-scale social systems redesign (guild depth, chat channels expansion) until core online loop is stable.

## Documentation Rule
`docs/GAME.md` is the canonical product source of truth.
Any gameplay/product change is incomplete until reflected here in the same change.
