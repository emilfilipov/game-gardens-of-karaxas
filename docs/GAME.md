# Ambitions of Peace - Game

## High Concept
Ambitions of Peace is a persistent online medieval war-and-politics RPG set in the late 12th-century Levant.

The core experience is not a full 3D open-world MMORPG. The product target is a systems-heavy online strategy RPG with:
- a persistent shared campaign map,
- player-controlled characters who command armies and households,
- instanced tactical battles,
- deep non-combat power paths (trade, logistics, diplomacy, espionage, governance).

## Product Identity and Tone
- Setting tone: historically inspired, politically grounded, morally complex.
- Narrative framing: no good-vs-evil faction simplification.
- Strategic framing: Jerusalem is a high-prestige objective, but regional control of routes, ports, fortresses, and intelligence networks is equally important.

## Core Gameplay Layers
### 1. Campaign Layer (Persistent)
Players operate on a shared top-down region map where they:
- travel,
- trade,
- negotiate,
- manage holdings,
- recruit and supply armies,
- build spy networks,
- contest territorial influence.

Campaign simulation is real-time and continuously advancing (no turn phases).

### 2. Battle Layer (Instanced)
When armies engage, they enter isolated tactical battles focused on:
- troop control,
- formation and positioning,
- morale and reinforcement timing,
- terrain and supply-aware outcomes.

Battles are real-time instances, not turn-based encounters.

Battle outcomes write back to the campaign layer.

## Temporal Model
- One continuous real-time simulation model across campaign and battle contexts.
- All core systems (travel, logistics, trade, espionage, politics, and combat) resolve over elapsed time, not by discrete player turns.

## Design Pillars
- Politics: titles, legitimacy, alliances, offices, influence.
- Logistics: food, horses, materiel, supply lines, transport risk.
- Trade: routes, tariffs, shortages/surpluses, convoy protection.
- Espionage: informants, report quality, misinformation, counter-intelligence.
- Warfare: raids, field battles, sieges, garrisons, territorial pressure.
- Social hierarchy: vassalage, guild/house ties, patronage, reputation.
- Personal progression: character skills, education, renown, identity.

## System Catalogue
This section is the detailed product-level description of all implemented and planned gameplay systems.

### Implemented Foundation Systems
#### Deterministic world tick authority
- Purpose: maintain one canonical progression timeline for all real-time systems.
- Loop: fixed-interval server ticks execute ordered command processing, emit events, and produce replay-safe state snapshots.
- Gameplay impact: all outcomes resolve from authoritative world time, avoiding client divergence and hidden turn-like behavior.

#### Campaign travel and route planning
- Purpose: make geography and route risk first-class strategic constraints.
- Loop: route graph planning computes fastest/safest paths; travel resolves over elapsed route time with risk-aware path selection.
- Gameplay impact: movement decisions are meaningful because route duration, risk profile, and choke points alter strategic tempo.

#### Campaign map rendering MVP (Bevy client)
- Purpose: make strategic world state readable in the Rust client shell.
- Loop: campaign surface renders route overlays, settlement nodes, army/caravan markers, and fog visibility states with zoom-driven readability controls.
- Gameplay impact: players can visually parse movement lanes, visibility, and active actors before full UI panel suite is complete.

#### Real-time logistics simulation
- Purpose: enforce supply constraints and make operational planning decisive.
- Loop: per tick, armies consume stock, queued convoy transfers execute, shortages accumulate pressure, and attrition is applied when supply fails.
- Gameplay impact: army effectiveness is sustained by logistics discipline, not only battle engagements.

#### Real-time trade simulation
- Purpose: make non-combat economic play a power path with strategic leverage.
- Loop: markets hold inventory and targets, shipments traverse deterministic routes with throughput/safety/tariff effects, and periodic shortage/surplus recompute updates local price pressure.
- Gameplay impact: route control and convoy flow now materially shift local economies and downstream strategic leverage.

#### Real-time espionage simulation
- Purpose: make information quality and deception an active strategic layer.
- Loop: informants progress through lifecycle states (active/dormant/burned), report generation emits reliability/confidence metadata with deterministic false-report pressure, and counter-intelligence sweeps detect/neutralize hostile assets over time.
- Gameplay impact: intelligence posture is now a controllable competitive axis rather than binary fog-of-war.

#### Real-time politics simulation
- Purpose: support influence-based progression and strategic leverage outside direct warfare.
- Loop: faction standings shift through actions and treaties, offices/titles are assigned by deterministic rules, and legitimacy/stability/influence drift continuously from current political posture.
- Gameplay impact: players can now gain durable power through governance and diplomatic positioning, not only military actions.

#### Real-time battle instancing contract
- Purpose: connect campaign encounters to deterministic tactical resolution records without breaking world continuity.
- Loop: encounter commands create auditable battle instance records, fixed-step battle ticks advance active instances, and resolved outcomes produce deterministic writeback payloads.
- Gameplay impact: campaign collisions now map to explicit, replay-safe battle lifecycle records before full tactical ruleset complexity is layered in.

#### Tactical battle MVP (real-time)
- Purpose: provide first battlefield command loop inside the deterministic instance contract.
- Loop: players can set formation stance, deploy reserves after timing gates, and observe continuous outcome scoring/morale pressure across fixed steps until resolution.
- Gameplay impact: tactical posture and timing now directly influence battle outcome signals rather than only raw army strength.

#### Real-time manual validation sandbox UI
- Purpose: allow direct manual validation of simulation systems before full vertical-slice UX exists.
- Loop: sandbox surfaces live simulation clock, travel controls, logistics/trade/espionage/politics/battle-contract controls, and world-state readouts each tick.
- Gameplay impact: fast development iteration and early balancing feedback without editor-only workflows.

### Planned Core Gameplay Systems
### Implemented Platform and Validation Systems
#### PostgreSQL LISTEN/NOTIFY outbox worker
- Purpose: provide low-cost PoC wake/fanout path before Redis adoption.
- Loop: outbox row inserts emit PostgreSQL `NOTIFY` payloads with outbox identifiers; reconnecting listeners treat notifications as wake signals and resume idempotent processing from durable outbox claims/cursors.
- Gameplay impact: timely state propagation without early infrastructure cost expansion.

#### Bevy bootstrap shell (login -> world bootstrap -> campaign entry)
- Purpose: provide the first Rust client entry path without external editor/UI tooling.
- Loop: player logs in (or uses launcher handoff session), client fetches authenticated character roster, requests world bootstrap payload for selected character, and FastAPI bridges that request to signed Rust world-entry bootstrap metadata before campaign scene handoff.
- Gameplay impact: establishes the practical account/session-to-world handoff path needed for vertical-slice playability.

#### Code-first gameplay panel suite (`bevy_egui`)
- Purpose: provide controllable vertical-slice domain surfaces without engine-authored editor UI.
- Loop: campaign view renders dedicated `character`, `household`, `logistics`, `trade`, `espionage`, `diplomacy`, and `notifications` panels with standardized hotkeys and saved layout presets.
- Gameplay impact: core strategic interfaces are now navigable through code-defined UI primitives and can evolve deterministically with gameplay systems.

#### Code-first authoring tools mode (map/system editing)
- Purpose: allow internal world/system authoring without external editor dependency.
- Loop: role-gated tools mode edits settlement/route data in-app, validates schema constraints before save, and persists/load authored map JSON for iterative tuning.
- Gameplay impact: playable map/system content can now be created and adjusted directly in the client code/UI workflow.

#### Deterministic content import/export pipeline
- Purpose: keep authored province/system content reviewable, reproducible, and safe to promote between local/dev/prod environments.
- Loop: tooling CLI normalizes JSON packs, converts to/from CSV authoring bundles, validates reference integrity, and emits stable SHA256 signatures for unchanged content.
- Gameplay impact: content iteration can move quickly without silent drift; unchanged content remains byte-stable so regressions are easier to detect.

#### First province content pack (Acre PoC)
- Purpose: establish first concrete vertical-slice region with complete seed data across strategic domains.
- Loop: checked-in Acre pack defines one city, one fortress, connected land/sea routes, two faction baselines, market seeds, and intelligence seeds; client bootstrap map can load this pack by default.
- Gameplay impact: systems are now exercised against a real content slice instead of only synthetic in-code sample data.

#### End-to-end playable vertical-slice loop
- Purpose: validate that account/login/bootstrap flows now reach a full strategic consequence path with persistence.
- Loop: authenticated backend orchestration triggers campaign movement command, starts/resolves a real-time battle instance in world-service, then writes battle-derived progression/location updates back to persistent character state.
- Gameplay impact: one-player PoC loop is now executable without manual debug stitching between independent subsystems.

#### Deterministic replay baseline
- Purpose: detect simulation drift across campaign+battle command streams before runtime changes reach players.
- Loop: world-service replay tests run the same mixed campaign/battle stream twice, compare deterministic snapshot output against committed golden data, and fail CI on divergence.
- Gameplay impact: authority-state regressions are caught early, reducing hidden balance and persistence bugs.

#### Operational observability baseline
- Purpose: keep solo-dev live operations safe by making runtime health degradations visible and actionable.
- Loop: backend/world-service expose runtime health metrics (tick lag, DB latency, outbox lag, release feed health) and operations scripts classify page-worthy vs log-only alerts.
- Gameplay impact: persistent world reliability issues are surfaced earlier, reducing player-facing outages during PoC iteration.

### Planned Platform and Validation Systems
#### Redis adoption gate
- Purpose: prevent premature complexity/cost.
- Loop: migrate only when measured bottlenecks exceed defined latency/contention/backlog thresholds documented in `docs/REDIS_ADOPTION_GATE.md`, then execute staged dual-write validation before consumer cutover.
- Gameplay impact: preserves development velocity and budget while retaining a clear scale path.

#### Replay determinism and operations hardening
- Purpose: guarantee stable outcomes and safe external playtests.
- Loop: replay/golden checks detect divergence; observability and rollback runbooks protect live operations.
- Gameplay impact: predictable world behavior and safer iteration cadence as player exposure grows.

## Player Fantasy
The player is simultaneously:
- a person,
- a commander,
- a household leader,
- a political/economic actor,
- a potential intelligence broker.

Primary progression fantasy: rise from minor local actor to regional power broker.

## Progression Model
### Primary progression tracks
- Character progression: skills, education, reputation, renown.
- Army/household progression: troop quality, officers, morale, supply endurance.
- Political progression: rank, offices, faction standing, legal claims, legitimacy.

### Secondary supporting progression
- Equipment quality and standardization.
- Artisan professions and production roles.
- Education/learning branches.
- Espionage network maturity.

## Espionage Contract
Espionage is a first-class system, not a single button action.

Required gameplay properties:
- informants are socially grounded assets,
- information quality is imperfect and variable,
- misinformation is a strategic tool,
- counter-intelligence can detect/disrupt hostile networks,
- espionage supports war, trade, diplomacy, and governance.

## Non-Combat Role Viability
Non-combat roles must remain competitive in influence gain and strategic relevance:
- merchants,
- logistics organizers,
- governors,
- political operators,
- artisans,
- intelligence specialists.

## Vertical Slice Definition (Current Program Target)
The first production vertical slice must include:
- one province-scale campaign area,
- one major city,
- one fortress,
- one functioning local economy and caravan route,
- faction influence progression,
- espionage network setup + reports,
- army movement and supply pressure,
- one instanced battle type,
- end-to-end account-to-playable loop.

## Out of Scope (Current Cycle)
- Full 3D open-world avatar MMO implementation.
- Massive handcrafted content volume before systems validation.
- Large social/meta systems unrelated to campaign-battle core loop.

## Documentation Rule
`docs/GAME.md` is the canonical product source of truth.
Any gameplay/product change is incomplete until reflected here in the same change.
