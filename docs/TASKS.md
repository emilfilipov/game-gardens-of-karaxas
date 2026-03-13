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
| AOP-PIVOT-024 | ✅ | 3 | AOP-PIVOT-023 | Implement CLI import/export pipelines for authored content (JSON/CSV) with deterministic normalization and hash signatures. |
| AOP-PIVOT-025 | ✅ | 3 | AOP-PIVOT-024 | Implement first province content pack (Acre region + one city + one fortress + connected trade routes + faction setup). |
| AOP-PIVOT-026 | ✅ | 3 | AOP-PIVOT-025 | Bridge FastAPI auth/session/character selection flow to Rust world entry endpoint without breaking existing login/account paths. |
| AOP-PIVOT-027 | ✅ | 3 | AOP-PIVOT-026 | Implement end-to-end playable loop: login -> character select -> campaign actions -> battle instance -> persistence writeback. |
| AOP-PIVOT-028 | ✅ | 4 | AOP-PIVOT-027 | Add deterministic replay validation suite for campaign and battle outcomes with golden snapshots. |
| AOP-PIVOT-029 | ✅ | 3 | AOP-PIVOT-027 | Add operational dashboards/alerts for world tick lag, DB latency, outbox lag, release feed publish health. |
| AOP-PIVOT-030 | ✅ | 2 | AOP-PIVOT-029 | Define monthly PoC cost report process and enforce budget guardrails for Cloud Run, Cloud SQL, GCS, and optional Redis adoption. |
| AOP-PIVOT-031 | ✅ | 3 | AOP-PIVOT-027 | Prepare external playtest hardening checklist (security, abuse controls, rollback drills, release rollback, data backups). |
| AOP-PIVOT-033 | ✅ | 2 | AOP-PIVOT-010 | Add manual validation Bevy sandbox surface (clock panel + route planning controls + route-time-driven moving player placeholder sprite generated as PNG) for local systems smoke testing. |
| AOP-PIVOT-034 | ✅ | 3 | AOP-PIVOT-014 | Expand deterministic regression/unit-test matrix across implemented simulation systems to catch cross-system side effects quickly. |
| AOP-PIVOT-035 | ✅ | 3 | AOP-PIVOT-027 | Productize Windows runtime packaging for `client-app` and ship it through existing GCS release channels with deterministic asset manifests. |
| AOP-PIVOT-036 | ✅ | 3 | AOP-PIVOT-035 | Harden external handoff integration into Windows `client-app` startup via structured startup handoff contract (`--handoff-file`/`AOP_HANDOFF_PATH`), config override support, and graceful stale-session fallback to login without manual env wiring. |
| AOP-PIVOT-037 | ⬜ | 2 | AOP-PIVOT-036 | Add one-command local PoC stack bootstrap (backend + world-service + client runtime) with seeded account/character for install-and-launch validation. |
| AOP-PIVOT-038 | ⬜ | 4 | AOP-PIVOT-037 | Implement authenticated real-time world state sync path from world-service to client map UI (polling/SSE baseline without Redis dependency). |
| AOP-PIVOT-039 | ⬜ | 4 | AOP-PIVOT-038 | Build first playable real-time battle scene in `client-app` (code-first UI + fixed-step visual loop) wired to existing battle authority endpoints. |
| AOP-PIVOT-040 | ⬜ | 3 | AOP-PIVOT-039 | Wire gameplay UI panels to live backend/world-service data and action endpoints (remove remaining static placeholder panel content). |
| AOP-PIVOT-041 | ⬜ | 3 | AOP-PIVOT-040 | Add Windows installer acceptance smoke suite that validates game/designer channel install/update, login handoff, campaign entry, and one vertical-slice battle outcome. |
| AOP-PIVOT-042 | ⬜ | 2 | AOP-PIVOT-041 | Finalize first single-player external PoC release checklist with dated go/no-go evidence bundle and rollback proof artifacts. |
| AOP-PIVOT-043 | ✅ | 2 | AOP-PIVOT-032 | Remove deprecated non-runtime artifact sets (legacy concept-art bundle) and update deprecation docs while scheduling full legacy module retirement work. |
| AOP-PIVOT-044 | ✅ | 3 | AOP-PIVOT-043 | Add auth/session continuity gate covering register/login/refresh/logout/session-drain force-logout behavior so migration cleanup cannot regress account security flows. |
| AOP-PIVOT-045 | ✅ | 3 | AOP-PIVOT-036 | Scaffold dedicated designer client module with separate runtime profile and code-first map/system editing shell decoupled from game runtime binaries. |
| AOP-PIVOT-046 | ✅ | 4 | AOP-PIVOT-045 | Implement designer world-authoring primitives for spawn points, camps, towns, villages, route anchors, and validation constraints with deterministic export output. |
| AOP-PIVOT-047 | ✅ | 4 | AOP-PIVOT-046 | Implement designer-to-game content promotion flow (signed pack generation, version metadata, stage/activate/deactivate/rollback controls, runtime continuity state) so authored map/system changes can be deployed safely with auditable rollback operations. |
| AOP-PIVOT-048 | ✅ | 3 | AOP-PIVOT-047 | Add fully separate designer installer/update release channel in GCS (artifact naming, feed URL, retention, rollback) decoupled from game client release flow. |
| AOP-PIVOT-049 | ✅ | 3 | AOP-PIVOT-036 | Remove Kotlin launcher/Godot/Gradle legacy runtime artifacts after Rust runtime + channel packaging parity reached baseline. |
| AOP-PIVOT-050 | ✅ | 2 | AOP-PIVOT-049 | Scrape remaining deprecated prototype docs/assets/tooling references (art-pipeline leftovers, legacy archive docs, stale asset generators) and align canonical docs with the final Rust-only repository surface. |

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
  - preserve external handoff compatibility contract.
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

### AOP-PIVOT-035 - Windows Runtime Packaging Productization
- Objective: make Rust client runtime installable/updatable through the existing Windows release path.
- Implementation checklist:
  - produce Windows `client-app` release artifact with required runtime assets and deterministic manifest,
  - update release workflow to publish `client-app` package and checksum metadata to GCS,
  - ensure retention/prune flow keeps only latest 3 valid client artifacts per channel,
  - document install/runtime layout and external handoff assumptions in installer/technical docs.
- Acceptance criteria:
  - latest release feed exposes launchable Windows `client-app` artifact with checksum,
  - installer/update flow can fetch and place runtime artifact without manual file copying.
- Validation:
  - release workflow artifact inspection + checksum verification,
  - local Windows install smoke against generated release feed.

### AOP-PIVOT-036 - External Handoff Integration Hardening
- Objective: remove manual bootstrap environment setup by hardening external handoff into `client-app`.
- Implementation checklist:
  - define stable handoff contract input (token/session/character/runtime URLs) for external launchers/installers,
  - harden client bootstrap-shell handoff parsing/validation and explicit user-facing errors for stale sessions,
  - add integration tests for expected handoff combinations and missing-value fallback behavior.
- Acceptance criteria:
  - user can complete login and enter campaign scene without manual shell/env manipulation,
  - invalid or expired handoff payloads fail gracefully with actionable UI messaging.
- Validation:
  - `cargo test -p client-app --features bootstrap-shell`.

### AOP-PIVOT-037 - One-Command Local PoC Stack Bootstrap
- Objective: ensure a fresh install can run the full PoC loop quickly with minimal manual setup.
- Implementation checklist:
  - add script/tool to start backend + world-service + client runtime with aligned env defaults,
  - provide deterministic seed path for one test account and one playable character,
  - add health checks/wait gates so client starts only after services are ready,
  - write operator runbook for first-run and reset flows.
- Acceptance criteria:
  - single command brings up a playable local stack from clean checkout (excluding dependency install),
  - seeded user can reach campaign entry reliably.
- Validation:
  - local bootstrap script run + automated readiness checks,
  - backend/client smoke tests referenced from script output.

### AOP-PIVOT-038 - Real-Time World Sync Channel
- Objective: move from static/bootstrap-only world data to continuous real-time campaign updates in client UI.
- Implementation checklist:
  - add authenticated world-state delta/snapshot feed endpoint (polling or SSE baseline),
  - implement client-side sync loop with deterministic state application and clock alignment,
  - include reconnect/backoff behavior and stale-data indicator surfaces,
  - instrument feed latency/failure metrics in ops endpoints.
- Acceptance criteria:
  - map state (positions, supply/trade/espionage indicators, alerts) updates continuously without manual refresh,
  - reconnect behavior preserves consistency after transient service interruptions.
- Validation:
  - integration tests for feed auth/reconnect/state application,
  - manual sandbox/bootstrap-shell sync smoke with forced disconnect/reconnect.

### AOP-PIVOT-039 - Playable Real-Time Battle Scene
- Objective: replace contract-only battle controls with a minimal playable visual battle scene.
- Implementation checklist:
  - add battle scene rendering layer with unit markers, front lines, morale/pressure HUD, and time controls,
  - wire formation/reserve/tactical actions to signed backend/world-service battle commands,
  - display authoritative battle progress/result events and return-to-campaign writeback summary,
  - add deterministic battle-scene simulation tests for command timing and state projection.
- Acceptance criteria:
  - user can enter battle instance, issue tactical actions in real time, and observe authoritative resolve in-client,
  - battle result writes back to campaign and character progression surfaces.
- Validation:
  - `cargo test -p client-app`,
  - backend/world-service integration tests for battle command/resolve flow,
  - manual local battle playthrough smoke.

### AOP-PIVOT-040 - Live Data Wiring for Gameplay Panels
- Objective: ensure gameplay UI panels reflect authoritative runtime data rather than placeholder/static values.
- Implementation checklist:
  - bind character/household/logistics/trade/espionage/diplomacy/notifications panels to live API data models,
  - implement optimistic-action guards + conflict/error handling for panel actions,
  - add panel refresh cadence contracts to avoid stale indicators,
  - add regression tests for panel data adapters and action response mapping.
- Acceptance criteria:
  - all shipped gameplay panels show live authoritative data during play sessions,
  - panel actions provide clear success/failure feedback and stay consistent after reconnect.
- Validation:
  - client-app panel adapter tests,
  - backend route contract tests,
  - manual panel verification during vertical-slice loop.

### AOP-PIVOT-041 - Windows Installer Acceptance Smoke Suite
- Objective: continuously verify end-to-end install-and-play basics on the Windows-first delivery path.
- Implementation checklist:
  - add smoke automation for installer/update/install-dir verification across game/designer channels,
  - validate login handoff to client runtime and campaign entry on latest release artifacts,
  - automate one campaign action + one battle action + result writeback verification,
  - publish smoke artifacts/log summary for each release run.
- Acceptance criteria:
  - release pipeline fails fast when installer or runtime handoff regresses,
  - smoke evidence is attached for successful release candidate runs.
- Validation:
  - CI smoke workflow on Windows runner,
  - manual fallback smoke execution docs.

### AOP-PIVOT-042 - First External PoC Release Gate
- Objective: formalize the first single-player external release decision with auditable operational evidence.
- Implementation checklist:
  - compile dated release-readiness checklist results (security, runtime health, cost guardrails, rollback drills),
  - capture release candidate install/play smoke evidence and known-risk ledger,
  - produce go/no-go memo with rollback trigger thresholds and on-call/incident contacts.
- Acceptance criteria:
  - first external PoC release has explicit dated sign-off package and rollback plan,
  - unresolved risks are documented with mitigation and owner.
- Validation:
  - completed evidence bundle in docs,
  - release gate script/report review sign-off.

### AOP-PIVOT-043 - Deprecated Artifact Cleanup (Safe Scope)
- Objective: reduce migration noise by deleting deprecated non-runtime assets and legacy runtime stacks.
- Implementation checklist:
  - delete legacy concept-art bundle no longer used by active docs/runtime/release flows,
  - update deprecation audit doc with explicit cleanup notes and rationale,
  - remove Kotlin/Godot/Gradle/Blender compatibility modules once Rust-first replacement baselines are in place.
- Acceptance criteria:
  - deprecated concept-art files are removed from repository tracking,
  - removed legacy modules have replacement runtime/release/docs paths documented.
- Validation:
  - `git diff --name-status` confirms removed concept-art paths,
  - grep audit confirms no active-doc references to removed concept-art paths.

### AOP-PIVOT-044 - Auth/Session Continuity Gate
- Objective: guarantee account/session security flows survive ongoing migration cleanup.
- Implementation checklist:
  - add/expand regression tests for register/login/refresh/logout endpoints,
  - add explicit force-logout/session-drain regression cases (revocation propagation to API + websocket),
  - add runbook check entry confirming auth gate passes before release promotion.
- Acceptance criteria:
  - auth/session tests fail on regressions in login, refresh rotation/reuse detection, logout, or forced revocation behavior,
  - release readiness checks include auth/session gate output.
- Validation:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_security_edges.py backend/tests/test_publish_drain.py`.

### AOP-PIVOT-045 - Dedicated Designer Client Scaffold
- Objective: create a standalone designer runtime path decoupled from player game runtime packaging.
- Implementation checklist:
  - scaffold dedicated designer module/runtime entrypoint with code-first UI shell,
  - define shared contracts with `tooling-core` for map/system authoring payloads,
  - add role/auth guardrail expectations for designer operations.
- Acceptance criteria:
  - designer client can launch independently from game client build/install,
  - baseline designer shell can load/write authored world data through defined schema contracts.
- Validation:
  - module unit tests + launch smoke command documented in `docs/README.md`.

### AOP-PIVOT-046 - Designer World Authoring Primitives
- Objective: provide first practical world-design workflow for spawn/camp/town/village placement and route layout.
- Implementation checklist:
  - implement primitives for spawn points, camps, towns, villages, and route anchors,
  - add snapping/validation rules for map bounds, duplicate IDs, and route integrity,
  - support deterministic export to versionable content pack format.
- Acceptance criteria:
  - designer can author and save a valid world slice containing all required primitive types,
  - invalid layouts fail with explicit validation errors before export.
- Validation:
  - deterministic export tests + schema validation tests.

### AOP-PIVOT-047 - Designer-to-Game Content Promotion
- Objective: make designer-authored changes deployable into game runtime through controlled version promotion.
- Implementation checklist:
  - create signed promotion artifact contract from designer export to runtime content pack,
  - add staged activation endpoint/command path with rollback metadata,
  - record promotion audit trail in PostgreSQL release/content metadata.
- Acceptance criteria:
  - promoted designer content can be activated/deactivated by version key without manual file surgery,
  - every promotion is auditable with actor/time/version metadata.
- Validation:
  - integration tests for promote/activate/rollback flows + signature checks.

### AOP-PIVOT-048 - Separate Designer Release Channel
- Objective: decouple designer installer/update lifecycle from game client player releases.
- Implementation checklist:
  - add dedicated GCS feed/archive prefix + artifact naming for designer channel,
  - enforce independent retention and rollback controls,
  - document installer/update process for designer-only distribution.
- Acceptance criteria:
  - designer channel can publish/rollback without touching game-runtime feed artifacts,
  - update URLs and manifests are distinct per channel.
- Validation:
  - CI channel publish smoke + rollback smoke.

### AOP-PIVOT-049 - Kotlin Launcher Retirement Gate
- Objective: retire Kotlin launcher/Godot/Gradle artifacts after replacement parity is proven.
- Implementation checklist:
  - define parity checklist for runtime handoff/update/auth compatibility in Rust-first runtime/install path,
  - execute side-by-side validation runs for replacement channel workflows,
  - remove Kotlin launcher/Godot/Gradle module/workflow dependencies once parity is signed off.
- Acceptance criteria:
  - no required player/designer flow depends on launcher/Godot compatibility modules at removal time,
  - repository and release workflow no longer require Kotlin/Godot/Gradle artifacts.
- Validation:
  - parity checklist sign-off + successful release candidate without legacy stack artifacts.

### AOP-PIVOT-050 - Final Deprecated Artifact Scrape
- Objective: complete post-migration deprecation cleanup by removing remaining prototype-era documents, assets, and generators that are no longer part of runtime delivery.
- Implementation checklist:
  - remove stale legacy-prototype docs and obsolete art-pipeline contracts/manifests from repository tracking,
  - remove unused prototype icons/tiles/character bundles and generator scripts,
  - update canonical docs/task ledger/deprecation audit to reflect the final active module and asset set.
- Acceptance criteria:
  - only active Rust-first runtime/tooling assets remain tracked for gameplay and release flows,
  - no canonical docs describe deleted archive paths as active references.
- Validation:
  - grep audit for removed path references + canonical doc review.

## Sequencing Guide (Strict Order)
1. Program setup tasks: `AOP-PIVOT-003`, `AOP-PIVOT-032`, then `AOP-PIVOT-004` to `AOP-PIVOT-007`.
2. Persistence/simulation foundation: `AOP-PIVOT-008` to `AOP-PIVOT-019`.
3. Client/tooling buildout: `AOP-PIVOT-020` to `AOP-PIVOT-024`.
4. Vertical slice assembly: `AOP-PIVOT-025` to `AOP-PIVOT-028`.
5. Operations and launch readiness: `AOP-PIVOT-029` to `AOP-PIVOT-031`.
6. Productization and release hardening: `AOP-PIVOT-035` to `AOP-PIVOT-042`.
7. Cleanup, auth continuity, and designer pipeline: `AOP-PIVOT-043` to `AOP-PIVOT-050`.

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
| AOP-PIVOT-032 | ✅ | 2 | AOP-PIVOT-003 | Legacy prototype docs removed from active tracking, active operations/security docs rewritten, and deprecation audit recorded in `docs/DEPRECATION_AUDIT.md`. |
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
| AOP-PIVOT-024 | ✅ | 3 | AOP-PIVOT-023 | Implemented `tooling-core` deterministic content CLI for JSON normalization, CSV import/export, and SHA256 signature emission with normalization/roundtrip/snapshot tests to guarantee stable converter output hashes. |
| AOP-PIVOT-025 | ✅ | 3 | AOP-PIVOT-024 | Added first Acre province content pack under `assets/content/provinces/acre/` (city + fortress + connected land/sea routes + faction setup + market/intelligence seeds), generated deterministic pack/signature artifacts, and wired client bootstrap map fallback to consume this pack path (`AOP_PROVINCE_PACK_PATH`). |
| AOP-PIVOT-026 | ✅ | 3 | AOP-PIVOT-025 | Added signed Rust world-service world-entry endpoint (`/internal/world-entry/bootstrap`) and FastAPI bridge client (`world_entry_bridge.py`) wired into `/characters/{id}/world-bootstrap` with compatibility-preserving fallback (`player_runtime.world_entry_bridge`) so login/bootstrap flows continue even when bridge calls fail. |
| AOP-PIVOT-027 | ✅ | 3 | AOP-PIVOT-026 | Added authenticated backend orchestration endpoint `/gameplay/vertical-slice-loop` that issues campaign move + battle lifecycle commands to world-service, advances ticks, reads battle resolution, and persists character writeback (xp/level/location), with smoke harness + regression tests proving login->bootstrap->campaign->battle->persistence flow. |
| AOP-PIVOT-028 | ✅ | 4 | AOP-PIVOT-027 | Added world-service deterministic replay suite with campaign+battle golden snapshot artifact (`world-service/tests/golden/campaign_battle_replay_v1.json`), replay determinism tests (`replay_*`), and dedicated CI gate job (`determinism-replay`) in Rust checks workflow. |
| AOP-PIVOT-029 | ✅ | 3 | AOP-PIVOT-027 | Added observability runtime instrumentation/outputs for world tick metrics (`/metrics/summary`), backend DB latency + outbox lag + release-feed health (`/ops/release/metrics.runtime_health`), alert severity split (page-worthy vs log-only), and executable alert check script (`backend/scripts/check_world_runtime_alerts.sh`) with updated ops runbook/dashboard contract. |
| AOP-PIVOT-030 | ✅ | 2 | AOP-PIVOT-029 | Added PoC cost guardrail policy doc (`docs/COST_GUARDRAILS.md`), monthly report generator (`backend/scripts/generate_monthly_cost_report.py`), and current monthly estimate report (`docs/cost-reports/2026-03-estimate.md`) covering Cloud Run/SQL/GCS/Artifact Registry/Redis with threshold status. |
| AOP-PIVOT-031 | ✅ | 3 | AOP-PIVOT-027 | Added external playtest hardening runbook/checklist (`docs/PLAYTEST_HARDENING_CHECKLIST.md`), baseline sign-off record (`docs/playtest-drills/2026-03-initial-signoff.md`), and executable hardening gate script (`backend/scripts/validate_playtest_hardening.sh`) covering security/abuse controls, rollback/backup drill readiness, and incident prep checklist. |
| AOP-PIVOT-033 | ✅ | 2 | AOP-PIVOT-010 | Added feature-gated Bevy sandbox in `client-app` with live clocks, route-planning controls, and animated player marker loaded from generated placeholder asset `client-app/assets/player_circle.png`. |
| AOP-PIVOT-034 | ✅ | 3 | AOP-PIVOT-014 | Expanded deterministic regression tests across implemented systems by adding espionage lifecycle/passive-report unit tests, serialization roundtrip tests for new espionage command/event payloads, and world-service espionage command->tick->state integration coverage. |
| AOP-PIVOT-035 | ✅ | 3 | AOP-PIVOT-027 | Release workflow now builds `client-app` (`bootstrap-shell`) on Windows, packages a versioned Rust runtime artifact (`AmbitionsOfPeace-client-app-win-x64-<version>.zip`) plus deterministic manifest/checksum via `tools/package_client_app_release.py`, uploads artifacts to GCS feed/archive paths, and prunes feed versions to latest 3. |
| AOP-PIVOT-036 | ✅ | 3 | AOP-PIVOT-035 | Added structured Windows startup handoff integration in `client-app` (`--handoff-file`, `--handoff-json`, `AOP_HANDOFF_PATH`, `AOP_HANDOFF_JSON`), contract validation/expiry checks with backend config overrides, legacy env compatibility fallback, stale-session actionable login reset behavior, and bootstrap-shell unit coverage for handoff parsing/error cases. |
| AOP-PIVOT-043 | ✅ | 2 | AOP-PIVOT-032 | Removed deprecated tracked `concept_art/` assets and legacy concept-art generation helper scripts under `tools/`, then executed broader legacy runtime cleanup planning. |
| AOP-PIVOT-044 | ✅ | 3 | AOP-PIVOT-043 | Added explicit auth/session continuity regression gate script (`backend/scripts/validate_auth_session_gate.sh`) and wired it into backend/release CI checks so login/refresh/logout/publish-drain regressions fail fast during migration cleanup. |
| AOP-PIVOT-045 | ✅ | 3 | AOP-PIVOT-036 | Extended standalone `designer-client` shell with dedicated world-design surface and authenticated stage/activate controls decoupled from player runtime binaries. |
| AOP-PIVOT-046 | ✅ | 4 | AOP-PIVOT-045 | Implemented world-authoring primitives and deterministic validation/hash utilities (`designer-client/world_design.py`) for camps/villages/towns/cities/fortresses, routes, and spawn points. |
| AOP-PIVOT-047 | ✅ | 4 | AOP-PIVOT-046 | Completed designer promotion parity by extending backend world-pack flow with explicit deactivate/rollback endpoints, per-province promotion manifest/version history (`versions.json`), runtime continuity cache (`backend/runtime/designer_world_state/`), expanded route/service tests, and designer-client UI controls for stage/activate/deactivate/rollback operations. |
| AOP-PIVOT-048 | ✅ | 3 | AOP-PIVOT-047 | Added separate game/designer GCS release channels in `.github/workflows/release.yml`, deterministic designer packaging (`tools/package_designer_client_release.py`), and per-channel install scripts (`scripts/install_game_client.ps1`, `scripts/install_designer_client.ps1`). |
| AOP-PIVOT-049 | ✅ | 3 | AOP-PIVOT-036 | Removed deprecated Kotlin/Godot/Gradle/Blender runtime artifacts (`launcher/`, `game-client/`, Gradle wrappers, blender/tool wrappers) and updated canonical docs to the Rust-only runtime path. |
| AOP-PIVOT-050 | ✅ | 2 | AOP-PIVOT-049 | Removed residual prototype documentation/assets/tooling (`docs/archive/legacy-prototype/*`, `docs/ART_PIPELINE_CONTRACT.md`, `assets/tiles/*`, `assets/characters/sellsword_v1/*`, obsolete icon/manifest files, and legacy sprite ingest generators) and aligned canonical docs/deprecation audit to the final post-migration repository shape. |
