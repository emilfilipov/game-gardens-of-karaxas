# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Current Program
- Program name: `AOP-PIVOT-RUST-POC`
- Program objective: migrate from current prototype stack to a Rust-first, code-first persistent online war-and-politics RPG vertical slice.
- Canonical references:
  - `docs/GAME.md`
  - `docs/TECHNICAL.md`

## Active Backlog
| Task ID | Status | Complexity | Depends On | Detailed Description |
| --- | --- | --- | --- | --- |
| AOP-PIVOT-001 | ✅ | 2 | - | Reset canonical docs from prior prototype direction to Crusades-era persistent strategy RPG scope and Rust-first architecture contract. |
| AOP-PIVOT-002 | ✅ | 1 | - | Reduce release artifact retention from 5 to 3 versions in CI release workflow and supporting installer documentation. |
| AOP-PIVOT-003 | ✅ | 2 | AOP-PIVOT-001 | Create repository-level architecture decision records (ADR set) for engine/runtime, backend language strategy, and phased migration boundaries. |
| AOP-PIVOT-032 | ✅ | 2 | AOP-PIVOT-003 | Audit and remove redundant/deprecated files and documentation from the pre-pivot prototype while preserving required compatibility artifacts. |
| AOP-PIVOT-004 | ✅ | 3 | AOP-PIVOT-003 | Create Rust workspace scaffold (`sim-core`, `world-service`, `tooling-core`, `client-app`) with unified formatting/lint/test toolchain and CI wiring. |
| AOP-PIVOT-005 | ✅ | 3 | AOP-PIVOT-004 | Add shared domain contracts crate for deterministic simulation types/events used by both service and client. |
| AOP-PIVOT-006 | ✅ | 3 | AOP-PIVOT-004 | Stand up Rust world service shell (Axum + health/readiness/config endpoints + structured logging + tracing IDs). |
| AOP-PIVOT-007 | ✅ | 3 | AOP-PIVOT-006 | Introduce service-to-service auth/signing model between legacy FastAPI control plane and Rust world service. |
| AOP-PIVOT-008 | ✅ | 3 | AOP-PIVOT-005 | Define PostgreSQL schema set for campaign world entities (region, settlement, route, faction, household, army, caravan, espionage asset). |
| AOP-PIVOT-009 | ✅ | 4 | AOP-PIVOT-008 | Implement migration-managed event store + outbox + idempotency keys + event replay cursors. |
| AOP-PIVOT-010 | ✅ | 4 | AOP-PIVOT-009 | Implement simulation tick runner (single region shard) with deterministic step ordering and snapshot checkpoint persistence. |
| AOP-PIVOT-011 | ✅ | 3 | AOP-PIVOT-010 | Implement campaign map graph model with travel times, route risk, and settlement adjacency APIs, then bind client movement to route-duration real-time progression. |
| AOP-PIVOT-012 | ✅ | 4 | AOP-PIVOT-010 | Implement real-time logistics model (food, horses, materiel, supply decay, convoy movement) with server-authoritative outcomes. |
| AOP-PIVOT-013 | ✅ | 4 | AOP-PIVOT-010 | Implement real-time trade model (market inventory, price pressure, tariffs, shortages/surpluses) with periodic economy recompute jobs. |
| AOP-PIVOT-014 | ✅ | 4 | AOP-PIVOT-010 | Implement real-time espionage model (informant recruitment, reliability score, false reports, counter-intelligence actions). |
| AOP-PIVOT-015 | ✅ | 3 | AOP-PIVOT-010 | Implement real-time politics model (faction standing, offices, legitimacy metrics, treaty records, influence deltas). |
| AOP-PIVOT-016 | ✅ | 4 | AOP-PIVOT-011 | Implement real-time battle instancing contract (campaign encounter -> battle instance record -> battle result writeback) with fixed-step authority loop. |
| AOP-PIVOT-017 | ✅ | 3 | AOP-PIVOT-016 | Implement first real-time tactical battle ruleset MVP (formation controls, morale pressure, reserve timing, continuous outcome scoring). |
| AOP-PIVOT-018 | ✅ | 3 | AOP-PIVOT-006 | Add PostgreSQL LISTEN/NOTIFY worker for PoC fanout and wake-up semantics tied to outbox rows. |
| AOP-PIVOT-019 | ✅ | 2 | AOP-PIVOT-018 | Add explicit Redis adoption gate document and metrics thresholds (p95 write latency, fanout lag, queue backlog, lock contention). |
| AOP-PIVOT-020 | ✅ | 3 | AOP-PIVOT-004 | Build Bevy client bootstrap shell with login handoff, session bootstrap fetch, and campaign map entry scene. |
| AOP-PIVOT-021 | ✅ | 3 | AOP-PIVOT-020 | Implement Bevy campaign map rendering MVP (province map tiles, settlements, roads, army/caravan markers, fog visibility states). |
| AOP-PIVOT-022 | ✅ | 4 | AOP-PIVOT-021 | Implement code-first in-game UI panels via `bevy_egui` (character, household, logistics, trade, espionage, diplomacy, notifications). |
| AOP-PIVOT-023 | ✅ | 3 | AOP-PIVOT-022 | Build code-first tools mode for map/system authoring (no external editor dependency), including save/load and schema validation. |
| AOP-PIVOT-024 | ⬜ | 3 | AOP-PIVOT-023 | Implement CLI import/export pipelines for authored content (JSON/CSV) with deterministic normalization and hash signatures. |
| AOP-PIVOT-025 | ⬜ | 3 | AOP-PIVOT-024 | Implement first province content pack (Acre region + one city + one fortress + connected trade routes + faction setup). |
| AOP-PIVOT-026 | ⬜ | 3 | AOP-PIVOT-025 | Bridge FastAPI auth/session/character selection flow to Rust world entry endpoint without breaking existing launcher/login paths. |
| AOP-PIVOT-027 | ⬜ | 3 | AOP-PIVOT-026 | Implement end-to-end playable loop: login -> character select -> campaign actions -> battle instance -> persistence writeback. |
| AOP-PIVOT-028 | ⬜ | 4 | AOP-PIVOT-027 | Add deterministic replay validation suite for campaign and battle outcomes with golden snapshots. |
| AOP-PIVOT-029 | ⬜ | 3 | AOP-PIVOT-027 | Add operational dashboards/alerts for world tick lag, DB latency, outbox lag, release feed publish health. |
| AOP-PIVOT-030 | ⬜ | 2 | AOP-PIVOT-029 | Define monthly PoC cost report process and enforce budget guardrails for Cloud Run, Cloud SQL, GCS, and optional Redis adoption. |
| AOP-PIVOT-031 | ⬜ | 3 | AOP-PIVOT-027 | Prepare external playtest hardening checklist (security, abuse controls, rollback drills, release rollback, data backups). |
| AOP-PIVOT-033 | ✅ | 2 | AOP-PIVOT-010 | Add manual validation Bevy sandbox surface (clock panel + route planning controls + route-time-driven moving player placeholder sprite generated as PNG) for local systems smoke testing. |
| AOP-PIVOT-034 | ✅ | 3 | AOP-PIVOT-014 | Expand deterministic regression/unit-test matrix across implemented simulation systems to catch cross-system side effects quickly. |

## Detailed Task Specs

### AOP-PIVOT-001 - Canonical Documentation Reset
- Objective: establish new canonical scope and architecture for the Crusades-era strategy RPG direction.
- Implementation checklist:
  - rewrite `docs/GAME.md` to new game pillars and loop,
  - rewrite `docs/TECHNICAL.md` to Rust/Bevy/Axum architecture,
  - remove obsolete Plompers-specific canonical requirements.
- Acceptance criteria:
  - both canonical docs align with the same product direction,
  - no canonical references to the old bouncy-ball arena scope remain.
- Validation:
  - manual review of `docs/GAME.md` and `docs/TECHNICAL.md`.

### AOP-PIVOT-002 - Release Retention Hard Cap
- Objective: minimize artifact storage growth while retaining rollback safety.
- Implementation checklist:
  - set CI retention to 3 latest versions in release prune step,
  - update installer/release docs to match retention value.
- Acceptance criteria:
  - workflow prune logic keeps 3 newest feed/archive versions,
  - docs match workflow behavior.
- Validation:
  - `grep -n "keepVersionCount" .github/workflows/release.yml docs/INSTALLER.md`

### AOP-PIVOT-003 - ADR Baseline
- Objective: make migration decisions explicit and traceable.
- Implementation checklist:
  - add ADR for Rust-first architecture,
  - add ADR for Bevy + code-first UI/tooling,
  - add ADR for phased FastAPI -> Rust authority transition,
  - add ADR for deferred Redis adoption strategy.
- Acceptance criteria:
  - ADRs reviewed and linked from `docs/TECHNICAL.md`.
- Validation:
  - docs link check + repository grep for ADR IDs.

### AOP-PIVOT-032 - Repository Cleanup and Deprecation Removal
- Objective: reduce migration noise and remove stale prototype assets/docs that can cause implementation drift.
- Implementation checklist:
  - inventory deprecated runtime/tooling/docs that are no longer part of the Ambitions of Peace target architecture,
  - classify each item as delete/archive/keep-for-compatibility,
  - remove or archive deprecated files with explicit commit notes,
  - update surviving docs to remove stale references and add migration notes where needed.
- Acceptance criteria:
  - no conflicting legacy product-direction docs remain in active references,
  - retained legacy artifacts are explicitly marked as compatibility-only.
- Validation:
  - `git diff --name-status` review + grep audit for deprecated scope terms.

### AOP-PIVOT-004 - Rust Workspace Scaffold
- Objective: create implementation foundation for all new modules.
- Implementation checklist:
  - add top-level Cargo workspace,
  - create crates: `sim-core`, `world-service`, `client-app`, `tooling-core`,
  - configure `rustfmt`, clippy, workspace test command,
  - add CI job for Rust checks.
- Acceptance criteria:
  - workspace builds in CI and local dev machine,
  - all crates pass baseline lint/test gates.
- Validation:
  - `cargo fmt --all -- --check`
  - `cargo clippy --workspace --all-targets -- -D warnings`
  - `cargo test --workspace`

### AOP-PIVOT-005 - Shared Simulation Contracts
- Objective: prevent client/server divergence in core simulation typing.
- Implementation checklist:
  - define IDs/newtypes for entities,
  - define serializable command and event envelopes,
  - define versioned schema compatibility policy.
- Acceptance criteria:
  - same crate imported by world service and client app,
  - compatibility tests enforce schema versioning.
- Validation:
  - Rust unit tests + serde roundtrip tests.

### AOP-PIVOT-006 - World Service Skeleton
- Objective: provide deployable Rust authority service baseline.
- Implementation checklist:
  - add Axum service bootstrap,
  - config + secrets loading,
  - health/readiness endpoints,
  - structured request logging + trace IDs.
- Acceptance criteria:
  - service deployable to Cloud Run,
  - health probes succeed,
  - logs include request/trace identifiers.
- Validation:
  - local run + Cloud Run smoke request.

### AOP-PIVOT-007 - Inter-Service Auth Boundary
- Objective: secure FastAPI-to-Rust world control calls.
- Implementation checklist:
  - define signed token contract or mTLS-equivalent gate,
  - enforce scope-limited service credentials,
  - add replay protection for privileged mutation endpoints.
- Acceptance criteria:
  - unauthorized cross-service calls are rejected,
  - privileged calls are auditable.
- Validation:
  - integration tests for allow/deny cases.

### AOP-PIVOT-008 - Campaign Schema Foundation
- Objective: model durable world entities for campaign systems.
- Implementation checklist:
  - create tables and indexes for map/faction/household/army/caravan/espionage domains,
  - define foreign key and cascade behavior,
  - add migration rollback safety notes.
- Acceptance criteria:
  - migrations apply/rollback cleanly,
  - schema supports planned vertical slice queries.
- Validation:
  - migration test + query explain review.

### AOP-PIVOT-009 - Event Store and Outbox
- Objective: support replay, auditing, and reliable async side effects.
- Implementation checklist:
  - implement append-only events table,
  - add transactional outbox table,
  - add idempotency keys and processing cursors.
- Acceptance criteria:
  - duplicate command submissions resolve safely,
  - processors can resume after interruption.
- Validation:
  - replay tests + failure-injection tests.

### AOP-PIVOT-010 - Deterministic Tick Runner
- Objective: authoritative world progression loop for one shard.
- Implementation checklist:
  - fixed tick cadence and deterministic processing order,
  - periodic snapshot checkpointing,
  - tick lag metrics.
- Acceptance criteria:
  - identical input stream reproduces identical output state,
  - tick lag remains under target threshold in local tests.
- Validation:
  - determinism test harness + perf smoke.

### AOP-PIVOT-011 - Campaign Graph and Travel
- Objective: make movement and geography first-class simulation inputs.
- Implementation checklist:
  - region graph and route definitions,
  - travel-time and risk calculation APIs,
  - client interpolation tied to route segment `travel_hours` and campaign clock rate,
  - settlement adjacency and choke-point contracts.
- Acceptance criteria:
  - travel and interception queries are deterministic and validated,
  - visual movement timing matches route duration at configured campaign time scale.
- Validation:
  - route/path integration tests.

### AOP-PIVOT-033 - Manual Sandbox Surface
- Objective: provide a low-friction visual/manual validation surface before full vertical-slice UI is complete.
- Implementation checklist:
  - add feature-gated Bevy sandbox client mode,
  - render campaign route graph and settlement markers from shared simulation graph,
  - provide manual route dispatch controls and clock panel for fast validation loops,
  - generate player placeholder sprite PNG asset in-repo.
- Acceptance criteria:
  - local run produces interactive map sandbox and moving player marker,
  - sandbox works without requiring ad-hoc editor setup.
- Validation:
  - `cargo run -p client-app --features sandbox-ui` (Windows-first validation target).

### AOP-PIVOT-012 - Logistics Simulation
- Objective: enforce supply constraints as strategic pressure.
- Implementation checklist:
  - supply inventory model,
  - attrition/consumption rules in continuous time,
  - convoy supply transfer events.
- Acceptance criteria:
  - unsupplied forces degrade predictably,
  - supply actions affect campaign outcomes.
- Validation:
  - scenario tests (supplied vs unsupplied outcomes).

### AOP-PIVOT-013 - Trade Simulation
- Objective: create non-combat power path with strategic economic effects.
- Implementation checklist:
  - market inventory and price model,
  - tariffs and route safety impact in continuous time,
  - shortage/surplus update job.
- Acceptance criteria:
  - trade actions measurably affect local economies and political leverage.
- Validation:
  - economy progression tests over N ticks.

### AOP-PIVOT-014 - Espionage Simulation
- Objective: implement imperfect information as core gameplay.
- Implementation checklist:
  - informant entity lifecycle,
  - reliability and deception parameters that evolve in continuous time,
  - counter-intelligence detection/conflict flows.
- Acceptance criteria:
  - reports include confidence/reliability metadata,
  - misinformation and detection outcomes are reproducible.
- Validation:
  - espionage scenario tests and replay consistency checks.

### AOP-PIVOT-034 - Cross-System Regression Test Matrix
- Objective: ensure changes in one subsystem do not silently regress other implemented systems.
- Implementation checklist:
  - expand `sim-core` coverage for espionage lifecycle transitions, passive report cadence, and deterministic false-report/counter-intel outcomes,
  - add serialization roundtrip tests for newly introduced espionage command/event payload variants,
  - add world-service integration tests covering espionage command queue + tick advance + state readback,
  - run full workspace lint/test gate after test additions.
- Acceptance criteria:
  - all implemented real-time subsystems (travel, logistics, trade, espionage) have deterministic unit/integration test coverage for key behavior,
  - payload compatibility tests cover newly added command/event variants used across service boundaries.
- Validation:
  - `cargo test --workspace`
  - `cargo clippy --workspace --all-targets -- -D warnings`

### AOP-PIVOT-015 - Political Systems
- Objective: allow influence-based progression outside military strength.
- Implementation checklist:
  - faction standing deltas in continuous time,
  - office/title assignment rules,
  - treaty and legitimacy records.
- Acceptance criteria:
  - political actions unlock gameplay options and constraints.
- Validation:
  - integration tests for rank/office/treaty transitions.

### AOP-PIVOT-016 - Battle Instance Contract
- Objective: formalize campaign-to-battle and battle-to-campaign state handoff for real-time instanced combat.
- Implementation checklist:
  - encounter trigger rules,
  - battle instance record schema,
  - fixed-step real-time battle loop contract and deterministic resolution payload contract.
- Acceptance criteria:
  - each encounter has auditable pre/post state,
  - writeback can be replayed safely.
- Validation:
  - end-to-end contract tests.

### AOP-PIVOT-017 - Tactical Battle MVP
- Objective: provide first command-focused real-time battle implementation.
- Implementation checklist:
  - formation and reserve controls in continuous time,
  - morale pressure system,
  - outcome score and casualty model sampled from fixed-step simulation.
- Acceptance criteria:
  - battle results produce strategic consequences in campaign layer.
- Validation:
  - tactical simulation tests + campaign writeback tests.

### AOP-PIVOT-018 - PostgreSQL LISTEN/NOTIFY Worker
- Objective: low-cost PoC event fanout without Redis dependency.
- Implementation checklist:
  - implement NOTIFY trigger points from outbox writes,
  - implement resilient LISTEN worker with reconnect,
  - keep events replay-safe and idempotent.
- Acceptance criteria:
  - service wakeup latency within PoC target,
  - no lost durable events (outbox remains source of truth).
- Validation:
  - integration tests with worker restarts.

### AOP-PIVOT-019 - Redis Adoption Gate
- Objective: avoid premature managed Redis spend.
- Implementation checklist:
  - define objective cutover metrics,
  - define migration plan for cache/session/queue pathways,
  - document rollback and dual-write period strategy.
- Acceptance criteria:
  - clear go/no-go criteria exists before enabling Memorystore.
- Validation:
  - gate document approved and linked from `docs/TECHNICAL.md`.

### AOP-PIVOT-020 - Bevy Client Bootstrap
- Objective: establish playable Rust client entry path.
- Implementation checklist:
  - implement app bootstrap and scene/state management,
  - implement auth/session bootstrap fetch,
  - show campaign entry view on successful bootstrap.
- Acceptance criteria:
  - user can authenticate and load campaign shell via Bevy client.
- Validation:
  - manual login-to-shell flow + integration smoke.

### AOP-PIVOT-021 - Campaign Map Rendering MVP
- Objective: visualize strategic world state in client.
- Implementation checklist:
  - map rendering pipeline,
  - route and settlement overlays,
  - army/caravan marker rendering.
- Acceptance criteria:
  - map readability and event updates are stable at target zoom levels.
- Validation:
  - rendering smoke checks + perf capture.

### AOP-PIVOT-022 - Code-First Gameplay UI Panels
- Objective: deliver required gameplay surfaces without editor-authored UI.
- Implementation checklist:
  - implement `bevy_egui` panels for core domains,
  - unify keyboard/mouse navigation patterns,
  - add panel state persistence and layout presets.
- Acceptance criteria:
  - all vertical-slice control surfaces are usable from code-defined UI.
- Validation:
  - UI integration tests + manual workflow runbook.

### AOP-PIVOT-023 - Code-First Authoring Tools Mode
- Objective: build internal level/system authoring inside codebase.
- Implementation checklist:
  - implement tools mode toggle and role gating,
  - implement map node/route/settlement editing commands,
  - implement validation/error surface before save.
- Acceptance criteria:
  - authored data can be produced without external editor UI.
- Validation:
  - tool output schema validation tests.

### AOP-PIVOT-024 - Content Import/Export CLI
- Objective: deterministic content pipeline for versioning and review.
- Implementation checklist:
  - implement CLI converters for JSON/CSV formats,
  - implement canonical ordering and normalization,
  - emit content hashes and signatures.
- Acceptance criteria:
  - repeated export of unchanged content yields identical hashes.
- Validation:
  - snapshot tests for converter outputs.

### AOP-PIVOT-025 - First Province Content Pack
- Objective: assemble first playable strategic region.
- Implementation checklist:
  - configure one city + one fortress + route network,
  - configure factions and initial power distribution,
  - configure baseline markets and intelligence seeds.
- Acceptance criteria:
  - province content boots cleanly and supports all core actions.
- Validation:
  - content validation CLI + in-client smoke run.

### AOP-PIVOT-026 - Legacy Control Plane Bridge
- Objective: preserve existing auth/account/release workflows while migrating gameplay authority.
- Implementation checklist:
  - maintain FastAPI auth/session endpoints,
  - forward world bootstrap handoff to Rust service,
  - preserve launcher compatibility contract.
- Acceptance criteria:
  - existing login/account flow remains functional during migration.
- Validation:
  - regression tests for auth/account/bootstrap endpoints.

### AOP-PIVOT-027 - End-to-End Vertical Slice Loop
- Objective: prove concept loop from login to strategic consequence.
- Implementation checklist:
  - wire campaign action execution,
  - wire battle instance trigger and completion,
  - wire persistence and reload integrity.
- Acceptance criteria:
  - one-player loop is fully playable without debug shortcuts.
- Validation:
  - scripted e2e smoke checklist and recorded run.

### AOP-PIVOT-028 - Determinism Replay Suite
- Objective: prevent simulation drift and hidden authority bugs.
- Implementation checklist:
  - capture command streams,
  - replay against snapshots,
  - fail on divergence in entity states/events.
- Acceptance criteria:
  - replay tests pass across clean environments.
- Validation:
  - deterministic replay CI job.

### AOP-PIVOT-029 - Observability and Alerts
- Objective: operationally safe solo-dev runtime monitoring.
- Implementation checklist:
  - instrument tick latency, DB latency, outbox lag,
  - publish dashboards,
  - define page-worthy vs log-only alert severities.
- Acceptance criteria:
  - critical failure modes generate actionable alerts.
- Validation:
  - alert fire drills and runbook verification.

### AOP-PIVOT-030 - Cost Guardrails
- Objective: keep PoC spend predictable.
- Implementation checklist:
  - define monthly budget target and threshold alerts,
  - report Cloud Run/SQL/GCS costs monthly,
  - enforce no-Redis-by-default policy unless adoption gate is met.
- Acceptance criteria:
  - monthly cost report exists and is linked in docs/tasks notes.
- Validation:
  - monthly billing export review checklist.

### AOP-PIVOT-031 - Playtest Hardening Checklist
- Objective: prepare first external testing pass safely.
- Implementation checklist:
  - security and abuse control review,
  - rollback and backup drill,
  - release feed rollback verification,
  - incident response checklist.
- Acceptance criteria:
  - first external playtest can be run with documented rollback path.
- Validation:
  - hardening checklist sign-off.

## Sequencing Guide (Strict Order)
1. Program setup tasks: `AOP-PIVOT-003`, `AOP-PIVOT-032`, then `AOP-PIVOT-004` to `AOP-PIVOT-007`.
2. Persistence/simulation foundation: `AOP-PIVOT-008` to `AOP-PIVOT-019`.
3. Client/tooling buildout: `AOP-PIVOT-020` to `AOP-PIVOT-024`.
4. Vertical slice assembly: `AOP-PIVOT-025` to `AOP-PIVOT-028`.
5. Operations and launch readiness: `AOP-PIVOT-029` to `AOP-PIVOT-031`.

## Resume Protocol
When work resumes after a pause:
1. Read `docs/GAME.md` and `docs/TECHNICAL.md` first.
2. Continue from the first non-`✅` task in sequencing order.
3. Do not start a higher-order task until all dependencies are `✅`.
4. For each completed task, update this file in the same commit.

## Completed (Current Cycle)
| Task ID | Status | Complexity | Depends On | Detailed Description |
| --- | --- | --- | --- | --- |
| AOP-PIVOT-001 | ✅ | 2 | - | Canonical docs migrated to the new Crusades-era strategy RPG direction and Rust-first architecture contract. |
| AOP-PIVOT-002 | ✅ | 1 | - | Release retention policy updated to latest 3 builds and documentation aligned. |
| AOP-PIVOT-003 | ✅ | 2 | AOP-PIVOT-001 | ADR baseline created under `docs/adr/` and linked from `docs/TECHNICAL.md`. |
| AOP-PIVOT-032 | ✅ | 2 | AOP-PIVOT-003 | Legacy prototype docs archived under `docs/archive/legacy-prototype/`, active operations/security docs rewritten, and deprecation audit recorded in `docs/DEPRECATION_AUDIT.md`. |
| AOP-PIVOT-004 | ✅ | 3 | AOP-PIVOT-003 | Rust workspace scaffolded (`sim-core`, `world-service`, `tooling-core`, `client-app`) with root Cargo workspace, rust toolchain config, and CI workflow `rust-checks.yml`. |
| AOP-PIVOT-005 | ✅ | 3 | AOP-PIVOT-004 | Shared contracts implemented in `sim-core` (typed IDs, command/event envelopes, schema compatibility checks) and consumed by `world-service` and `client-app`. |
| AOP-PIVOT-006 | ✅ | 3 | AOP-PIVOT-004 | `world-service` now boots an Axum server with env-based config, `/healthz` + `/readyz` + `/config` endpoints, request-ID propagation, and structured tracing. |
| AOP-PIVOT-007 | ✅ | 3 | AOP-PIVOT-006 | Added HMAC-signed FastAPI -> Rust internal call contract with scope enforcement, nonce replay protection, and allow/deny integration tests for privileged `/internal/control/commands` calls. |
| AOP-PIVOT-008 | ✅ | 3 | AOP-PIVOT-005 | Added Alembic migration `0021_campaign_world_foundation` and ORM models for campaign regions, settlements, routes, factions, households, armies, caravans, and espionage assets with FK/index and downgrade order safety coverage. |
| AOP-PIVOT-009 | ✅ | 4 | AOP-PIVOT-008 | Added migration `0022_event_store_outbox`, event-pipeline ORM models/services, and replay/idempotency/outbox-resume tests for duplicate-safe command handling and restart-safe processor progress. |
| AOP-PIVOT-010 | ✅ | 4 | AOP-PIVOT-009 | Implemented deterministic `TickRunner` (fixed cadence, deterministic command ordering, periodic snapshot checkpoints, lag/duration metrics) and wired signed internal control endpoints for queueing commands and advancing ticks. |
| AOP-PIVOT-011 | ✅ | 3 | AOP-PIVOT-010 | Added deterministic travel graph/pathing domain in `sim-core` (adjacency, risk modifiers, fastest/safest planning, choke-point detection, arrival estimates), exposed world-service travel map/adjacency/plan APIs, and aligned client sandbox movement to route-duration real-time progression. |
| AOP-PIVOT-012 | ✅ | 4 | AOP-PIVOT-010 | Added shared `sim-core` logistics domain (supply stocks, convoy transfers, shortage-driven attrition), integrated logistics processing into `world-service` deterministic ticks with signed `queue_supply_transfer` command support and `GET /logistics/state`, and expanded sandbox UI with real-time logistics status/convoy controls for manual validation. |
| AOP-PIVOT-013 | ✅ | 4 | AOP-PIVOT-010 | Added shared `sim-core` trade domain (markets, trade routes, shipment throughput/safety/tariff effects, periodic shortage/surplus price recompute), integrated trade processing into `world-service` deterministic ticks with signed `queue_trade_shipment` command support and `GET /trade/state`, and expanded sandbox UI with real-time trade shipment/market validation controls. |
| AOP-PIVOT-014 | ✅ | 4 | AOP-PIVOT-010 | Added shared `sim-core` espionage domain (informant lifecycle states, deterministic report confidence/reliability metadata, false-report pressure, and counter-intelligence sweep outcomes), integrated espionage processing into `world-service` deterministic ticks with signed `recruit_informant`/`request_intel_report`/`counter_intel_sweep` command support and `GET /espionage/state`, and expanded sandbox UI with real-time espionage controls/state reporting. |
| AOP-PIVOT-015 | ✅ | 3 | AOP-PIVOT-010 | Added shared `sim-core` politics domain (faction standing deltas, deterministic office assignment rules, treaty records/state transitions, legitimacy/stability/influence recompute), integrated politics processing into `world-service` deterministic ticks with signed `assign_political_office`/`set_treaty_status` support and `GET /politics/state`, and expanded sandbox UI with real-time politics controls and status readouts. |
| AOP-PIVOT-016 | ✅ | 4 | AOP-PIVOT-011 | Added shared `sim-core` battle contract domain (encounter rules, fixed-step instance advancement, deterministic resolution/writeback payload records), integrated battle processing into `world-service` deterministic ticks with signed `start_battle_encounter`/`force_resolve_battle_instance` support and `GET /battle/state`, and expanded sandbox UI with real-time battle contract controls and instance/result readouts. |
| AOP-PIVOT-017 | ✅ | 3 | AOP-PIVOT-016 | Extended the battle contract to a tactical MVP with deterministic formation controls, reserve deployment timing gates, morale/outcome scoring pressure, new signed tactical commands (`set_battle_formation`, `deploy_battle_reserve`), and updated sandbox/manual validation coverage for tactical decisions. |
| AOP-PIVOT-018 | ✅ | 3 | AOP-PIVOT-006 | Added PostgreSQL outbox insert trigger migration (`0023_outbox_notify_trigger`) plus reconnecting LISTEN worker scaffolding (`backend/app/services/outbox_notify_worker.py`) wired into FastAPI startup/shutdown, with restart-oriented tests validating wake semantics and replay-safe outbox claiming behavior. |
| AOP-PIVOT-019 | ✅ | 2 | AOP-PIVOT-018 | Added explicit Redis adoption gate document (`docs/REDIS_ADOPTION_GATE.md`) with concrete threshold metrics (write latency, fanout lag, backlog, lock contention), staged dual-write migration plan, rollback sequence, and canonical links from technical/ops docs. |
| AOP-PIVOT-020 | ✅ | 3 | AOP-PIVOT-004 | Implemented feature-gated Bevy bootstrap shell (`client-app --features bootstrap-shell`) with login flow, optional session handoff env support, authenticated character roster/world-bootstrap fetches, campaign entry scene marker spawn, and client-shell unit tests for error parsing/selection behavior. |
| AOP-PIVOT-021 | ✅ | 3 | AOP-PIVOT-020 | Extended bootstrap shell campaign entry with map rendering MVP from shared travel graph data (settlement nodes, road/sea routes, army+caravan markers, fog visibility states, zoom controls) for strategic readability validation. |
| AOP-PIVOT-022 | ✅ | 4 | AOP-PIVOT-021 | Added code-first `bevy_egui` domain panel suite (`character`, `household`, `logistics`, `trade`, `espionage`, `diplomacy`, `notifications`) with unified keyboard navigation (`F1`..`F7`), persisted panel state, and layout presets (`strategist`/`operations`) with save/load support. |
| AOP-PIVOT-023 | ✅ | 3 | AOP-PIVOT-022 | Added role-gated in-client tools mode for map/system authoring: settlement/route editors, validation/error surface before save, and authored map JSON load/save/apply workflow (`AOP_TOOLS_MAP_PATH`). |
| AOP-PIVOT-033 | ✅ | 2 | AOP-PIVOT-010 | Added feature-gated Bevy sandbox in `client-app` with live clocks, route-planning controls, and animated player marker loaded from generated placeholder asset `client-app/assets/player_circle.png`. |
| AOP-PIVOT-034 | ✅ | 3 | AOP-PIVOT-014 | Expanded deterministic regression tests across implemented systems by adding espionage lifecycle/passive-report unit tests, serialization roundtrip tests for new espionage command/event payloads, and world-service espionage command->tick->state integration coverage. |
