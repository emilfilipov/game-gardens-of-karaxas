# Children of Ikphelion - Game

## High Concept
Children of Ikphelion is an online isometric ARPG.

Current migration direction:
- Runtime presentation is now on an initial Godot 3D foundation path while preserving the online ARPG gameplay model.
- Camera target remains angled and distanced readability inspired by Path of Exile (further tuning in active backlog).

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
- Character list now uses a single left sidebar with top `Create Character` action plus character cards below (no duplicate list sidebar/headline).
- Character list refresh is automatic when switching account views/screens (no manual refresh button).
- Character list remains the default account view even when no characters exist (no forced switch into create view on empty lists).
- Character list/create views now consume the full account content area instead of centered boxed layouts.
- Character creation view hides the left list sidebar and keeps flow actions on the right panel (`Create Character` above `Back to Character List`).
- Character creation now submits immediately (no create confirmation popup) and the create-preview headline above the model is removed.
- Character list/create now include a dual-preview setup using 3D character previews:
  - large primary podium preview for inspection/rotation,
  - smaller in-world-scale inset preview synced to the same facing direction.
- Character previews now include explicit grounding cues (baseline anchor + contact shadow + floor strip) to avoid floating.
- Character-creation inset world-scale preview includes stronger backdrop contrast and thin border for visibility.
- Character details now live in a compact bottom-right square panel over the list preview area.
- List actions (`Play`, `Delete`) and spawn override controls are disabled until a character is selected.
- Character location persistence includes level/floor and coordinates.
- Character creation now focuses on a minimal onboarding flow: **preset + sex + name**.
- Create-field ordering is now: **Character Name -> Character Type -> Sex -> Character Type Lore**.
- Starter-skills text is not shown in the create lore panel.
- Race/background/affiliation/manual stat allocation are no longer player-facing in creation and are sourced from preset/runtime defaults.
- Current production model preset: **Sellsword** with male/female variants.
- 3D Sellsword baseline templates now exist for both male/female and are used by new 3D preview/world scaffolds.
- Character art source baseline is now **640x640 per frame** (fidelity v3 authored detail), 8-direction, with starter animation set:
  - idle, walk, run, attack, cast, hurt, death, sit_crossed_legs, sit_kneel.
- Directional sprites now render visibly different front/side/back facing poses (including away-from-camera views) with smoother, less blocky model rendering.
- Runtime world rendering downsamples these source frames to gameplay scale to keep readability and performance stable.
- Base model starts unarmed and is dressed in rugged leather brigandine/boots for both male and female variants.
- Game icon assets are sourced from `icon_2.png` and propagated to launcher/client/installer icon targets.
- Starter 3D environment kit (basic ground + foliage scenes) is now available to seed early level construction.

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
