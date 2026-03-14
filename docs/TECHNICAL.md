# Ambitions of Peace - Technical

## Purpose
Canonical technical source of truth for runtime architecture, backend/service boundaries, release/distribution behavior, and migration sequencing.

## Architecture Decision Records
Accepted ADRs for the current migration program:
- `docs/adr/0001-rust-first-runtime-and-services.md`
- `docs/adr/0002-bevy-code-first-ui-and-tooling.md`
- `docs/adr/0003-phased-fastapi-to-rust-authority-migration.md`
- `docs/adr/0004-redis-deferral-and-adoption-gate.md`

## Current State Summary (As Of 2026-03-13)
Active repository stack is now Rust-first plus a retained FastAPI control plane:
- FastAPI + PostgreSQL backend (`backend/`)
- Rust world authority service (`world-service/`)
- Rust simulation contracts/tooling (`sim-core/`, `tooling-core/`)
- Rust Bevy runtime (`client-app/`)
- Standalone designer client (`designer-client/`)
- GCS dual-channel release pipeline (game/designer) with 3-version retention

Legacy Kotlin/Godot/Gradle/Blender prototype modules and their superseded prototype documentation are removed from active tracking.

## Architecture Direction
### Primary language and framework choice
- Primary language: Rust
- Client runtime/framework: Bevy
- In-game and tool UI: egui (`bevy_egui`)
- World/simulation service runtime: Axum + Tokio
- Persistence: PostgreSQL (Cloud SQL)

### Why this is canonical
- Single-language system implementation path across gameplay logic, tools, and authority services.
- Code-first workflow for UI/editor/tooling (no mandatory engine editor UI dependency).
- Strong performance and memory safety profile suitable for long-lived online simulation services.

## Platform Contracts
### GCP services kept in active use
- Cloud SQL PostgreSQL: canonical persistent game state and release metadata.
- Cloud Run: API/control-plane services.
- GCS: release artifacts and downloadable build payloads.
- Artifact Registry: container images.
- GitHub Actions + GCP Workload Identity Federation: CI/CD authentication and deployment.

### Release artifact policy
- Release binaries remain in GCS.
- GCS feed/archive retention keeps only the latest 3 build versions.
- PostgreSQL stores release metadata (version/channel/checksum/notes/publish timestamps), not binary payload blobs.
- Release workflow publishes installer-first Windows game artifacts plus launcher-managed update payloads:
  - installer: `AmbitionsOfPeace-game-installer-win-x64-<version>.exe` + `.sha256`,
  - full runtime payload: `AmbitionsOfPeace-client-app-win-x64-<version>.zip` + `.manifest.json` + `.sha256`,
  - optional runtime deltas: `AmbitionsOfPeace-client-delta-<to_version>-from-<from_version>.zip` + `.sha256` (file-level incremental update path).
- Designer channel remains zip-based: `AmbitionsOfPeace-designer-client-win-x64-<version>.zip` + `.manifest.json` + `.sha256`.

### Redis policy
- Redis is deferred for PoC cost control.
- PoC eventing uses PostgreSQL outbox + LISTEN/NOTIFY where practical.
- Redis (Memorystore) adoption trigger is defined by measured latency/contention/throughput pressure, not by assumption.
- Canonical adoption gate and migration/rollback contract: `docs/REDIS_ADOPTION_GATE.md`.

## Runtime and Service Topology (Target)
### Control plane (transitional)
- Existing FastAPI auth/session/account/content/release endpoints remain operational during migration.
- FastAPI now exposes authenticated vertical-slice orchestration endpoint `POST /gameplay/vertical-slice-loop` to run the PoC loop (campaign command dispatch -> battle instance lifecycle -> persistence writeback) while keeping login/account/session contracts intact.
- FastAPI now also exposes authenticated world-sync feed endpoint `POST /gameplay/world-sync` that advances deterministic world ticks and returns the current multi-domain snapshot (`travel/logistics/trade/espionage/politics/battle`) for client polling.
- FastAPI now also exposes authenticated battle control endpoints `POST /gameplay/battle/start` and `POST /gameplay/battle/command` for real-time client battle scene actions.
- FastAPI now also exposes authenticated domain action endpoint `POST /gameplay/domain-action` for logistics/trade/espionage/politics panel actions.
- FastAPI ops metrics endpoint `GET /ops/release/metrics` now includes runtime health probes for DB latency, outbox lag, and release feed health metadata.

### New world authority plane
- Rust world service (`world-service`) now provides the initial Axum skeleton with env-driven config and health/readiness/config endpoints; it will expand to own campaign simulation ticks, economic/logistics simulation, espionage state, and instanced battle authority orchestration.
- FastAPI -> world-service privileged control calls now use an HMAC-SHA256 signed request contract (`x-aop-service-id`, `x-aop-scope`, `x-aop-timestamp`, `x-aop-nonce`, `x-aop-body-sha256`, `x-aop-signature`) with strict scope checks.
- Privileged mutation routes in world-service (`/internal/control/commands`) enforce timestamp skew limits and nonce replay detection via in-memory replay window cache (PoC baseline).
- World-service now also exposes signed internal world-entry bootstrap endpoint (`POST /internal/world-entry/bootstrap`) that returns campaign tick, nearest settlement anchor, and travel-map snapshot metadata for FastAPI handoff.
- FastAPI `/characters/{character_id}/world-bootstrap` now bridges through `backend/app/services/world_entry_bridge.py` to call the Rust world-entry endpoint and stores result under `player_runtime.world_entry_bridge` with compatibility-preserving fallback behavior.
- World service now includes deterministic single-shard tick runner primitives (`world-service/src/tick_runner.rs`) with fixed cadence execution, deterministic command ordering, periodic snapshot hashing/checkpoints, and tick lag/duration metrics.
- Tick runner now also executes a deterministic real-time logistics subsystem each tick (supply consumption, queued convoy transfers, shortage pressure, and attrition effects) backed by shared `sim-core` contracts.
- Tick runner now also executes a deterministic real-time trade subsystem each tick (shipment execution with throughput/safety/tariff effects plus periodic market price recompute from shortage/surplus pressure).
- Tick runner now also executes a deterministic real-time espionage subsystem each tick (informant lifecycle drift, reliability/deception pressure, deterministic report generation, and counter-intelligence sweep resolution).
- Tick runner now also executes a deterministic real-time politics subsystem each tick (standing deltas, office assignment, treaty state transitions, and legitimacy/stability/influence recompute).
- Tick runner now also executes a deterministic real-time battle instance contract subsystem each tick (instance creation, fixed-step advancement, tactical formation/reserve effects, continuous outcome scoring, and deterministic resolution/writeback payload generation).
- Signed internal endpoint `/internal/control/tick` advances deterministic ticks for PoC orchestration/testing.
- World service now exposes deterministic travel APIs backed by shared `sim-core` graph contracts:
  - `GET /travel/map`
  - `GET /travel/adjacency/{settlement_id}`
  - `POST /travel/plan`
- World service now also exposes deterministic logistics state API backed by the same tick authority loop:
  - `GET /logistics/state`
- World service now also exposes deterministic trade state API backed by the same tick authority loop:
  - `GET /trade/state`
- World service now also exposes deterministic espionage state API backed by the same tick authority loop:
  - `GET /espionage/state`
- World service now also exposes deterministic politics state API backed by the same tick authority loop:
  - `GET /politics/state`
- World service now also exposes deterministic battle instance state API backed by the same tick authority loop:
  - `GET /battle/state`
- World service now also exposes runtime summary metrics API for observability dashboards/alert checks:
  - `GET /metrics/summary`
- Internal signed control command contract now includes logistics convoy transfer queueing (`queue_supply_transfer`) through `/internal/control/commands`.
- Internal signed control command contract now also includes trade shipment queueing (`queue_trade_shipment`) through `/internal/control/commands`.
- Internal signed control command contract now also includes espionage queueing actions (`recruit_informant`, `request_intel_report`, `counter_intel_sweep`) through `/internal/control/commands`.
- Internal signed control command contract now also includes politics actions (`assign_political_office`, `set_treaty_status`) while `set_faction_stance` feeds deterministic politics standing updates.
- Internal signed control command contract now also includes battle contract actions (`start_battle_encounter`, `force_resolve_battle_instance`) for campaign encounter -> instance lifecycle control.
- Internal signed control command contract now also includes tactical battle controls (`set_battle_formation`, `deploy_battle_reserve`) for instance-level formation/reserve decisions.
- Internal signed bridge contract now also includes world-entry handoff (`/internal/world-entry/bootstrap`) consumed by FastAPI auth/session/character bootstrap flow.
- FastAPI world-service control client (`backend/app/services/world_service_control.py`) now orchestrates signed command dispatch and tick advancement (`/internal/control/commands`, `/internal/control/tick`) plus battle-state reads (`/battle/state`) for vertical-slice loop execution.
- FastAPI world-service control client now also aggregates multi-domain world sync snapshots by combining `/internal/control/tick` with `/travel/map`, `/logistics/state`, `/trade/state`, `/espionage/state`, `/politics/state`, `/battle/state`, and `/metrics/summary`.
- `POST /gameplay/world-sync` payload now includes authoritative `world.character` and derived `world.household` summaries in addition to domain snapshots to support live panel hydration.
- Shared Rust domain crates provide deterministic rules used by both service and client presentation layers.
- Shared Rust domain crate `sim-core` now defines typed entity IDs, command/event envelopes, and schema compatibility policy consumed by both `world-service` and `client-app`.
- Shared `sim-core` now also includes travel-domain contracts/planner logic (route adjacency, fastest/safest route planning, risk modifiers, deterministic route risk bands, choke-point detection, and arrival estimates).
- Campaign traversal is now rendered in client sandbox using route-duration-driven real-time interpolation tied to campaign clock scale (not distance-speed heuristics).
- Battle architecture contract is real-time instanced simulation authority (fixed-step runtime), not turn-based resolution.
- Real-time is the global gameplay contract: logistics, trade, espionage, and politics systems are also continuous-time simulations executed on fixed deterministic ticks.

### Client
- Bevy client renders campaign and battle surfaces.
- Client sends intent; authority services resolve final state transitions.
- Designer tooling is delivered as a dedicated, separately packaged client/update channel so authoring workflows are decoupled from player runtime releases.
- `client-app` now includes a feature-gated Bevy bootstrap shell (`cargo run -p client-app --features bootstrap-shell`) with:
  - credential login to FastAPI `/auth/login`,
  - external startup handoff contract via `--handoff-file` / `--handoff-json` or env (`AOP_HANDOFF_PATH` / `AOP_HANDOFF_JSON`) with schema validation, expiry checks, and backend config overrides (`api_base_url`, `client_version`, `client_content_version_key`),
  - legacy env handoff compatibility (`AOP_HANDOFF_ACCESS_TOKEN`, `AOP_HANDOFF_SESSION_ID`, etc.) as fallback during migration,
  - authenticated character roster fetch from `/characters`,
  - session bootstrap fetch from `/characters/{character_id}/world-bootstrap`,
  - campaign entry scene handoff with spawned player marker at bootstrap world coordinates,
  - actionable stale/invalid handoff handling that clears rejected handoff sessions and returns user to login.
- Bootstrap shell campaign view now includes a rendering MVP for strategic map surfaces:
  - settlement nodes and road/sea route overlays from shared `sim-core` travel graph data,
  - deterministic sample army/caravan marker animation along routes,
  - fog visibility states (`visible` / `shrouded` / `obscured`) and zoom controls for readability checks.
- Bootstrap shell now also includes code-first gameplay domain panels via `bevy_egui`:
  - `character`, `household`, `logistics`, `trade`, `espionage`, `diplomacy`, and `notifications`,
  - unified keyboard toggles (`F1`..`F7`) and panel toolbar controls,
  - persisted panel state + layout preset save/load (`strategist`, `operations`) through JSON snapshot file (`AOP_PANEL_LAYOUT_PATH`, default `client-app/runtime/panel_layout.json`).
- Bootstrap shell now also runs an authenticated world-sync polling loop against `POST /gameplay/world-sync`:
  - deterministic tick-ordered snapshot application (ignore regressed ticks),
  - reconnect/backoff strategy (`1s` base up to `10s`),
  - stale-data surface when no successful sync is received before `stale_after_ms`,
  - server/client clock alignment metadata for campaign tick projection in UI.
- Bootstrap shell now includes a playable real-time battle scene window:
  - fixed-step visual battle clock and front-line rendering,
  - live unit markers + morale/pressure summaries,
  - real-time tactical action controls wired to backend `battle/start` + `battle/command` routes.
- Bootstrap shell gameplay panels are now fully wired to authoritative data + actions:
  - panels hydrate from live `world-sync` character/household/domain payloads,
  - panel actions dispatch through `POST /gameplay/domain-action`,
  - optimistic in-flight guards and explicit success/error state are surfaced in UI.
- Bootstrap shell UI draw system now executes in `bevy_egui` primary context pass (`EguiPrimaryContextPass`) to prevent startup-time egui font/context panics on packaged Windows runtime launch.
- Bootstrap shell now includes role-gated code-first map authoring tools mode:
  - enable via `AOP_TOOLS_ENABLED=true` or `AOP_TOOLS_ROLE=designer|admin`,
  - edit settlements (camp/village/town/city/fortress) and routes in-app, run schema validation before save, and view inline validation errors,
  - load/save authored map JSON (`AOP_TOOLS_MAP_PATH`, default `client-app/runtime/authored_map.json`) and apply validated graphs to live map rendering.
- `designer-client` now includes world-design primitives and promotion controls:
  - local deterministic validation/hash generation (`designer-client/world_design.py`),
  - backend stage endpoint `POST /designer/world-pack/stage`,
  - backend activate/publish endpoint `POST /designer/world-pack/activate` producing versioned pack/signature/latest pointers under `assets/content/provinces/<province_id>/`,
  - backend deactivate/rollback endpoints (`POST /designer/world-pack/deactivate`, `POST /designer/world-pack/rollback`) maintaining per-province promotion history in `assets/content/provinces/<province_id>/versions.json` with runtime continuity cache under `backend/runtime/designer_world_state/`.
- First province content pack baseline is now checked in at `assets/content/provinces/acre/`:
  - one city (`Acre Port`) and one fortress (`Montmusard Fortress`),
  - connected land + sea routes, faction setup, market seeds, and intelligence seeds,
  - deterministic generated pack/signature artifacts (`acre_poc_v1.json`, `acre_poc_v1.sig.json`) from CSV source using `tooling-core`.
- Bootstrap shell campaign map default source now attempts to load `AOP_PROVINCE_PACK_PATH` (default `assets/content/provinces/acre/acre_poc_v1.json`) before falling back to the in-code sample graph.
- `tooling-core` now provides deterministic authored-content import/export pipeline CLI:
  - normalize and validate province packs from JSON (`cargo run -p tooling-core -- normalize-json ...`),
  - import/export canonical CSV bundles (`import-csv` / `export-csv`),
  - emit deterministic SHA256 signature metadata for review/approval (`--signature-output` or `hash` command),
  - enforce canonical ordering and reference validation before output to keep repeated exports hash-identical.
- `client-app` now includes a feature-gated manual sandbox UI (`cargo run -p client-app --features sandbox-ui`) with map rendering, route dispatch controls, and simulation clocks for PoC systems validation.
- Sandbox UI now includes a real-time logistics panel (army stocks/shortage status + convoy queue button) powered by shared `sim-core` logistics rules for manual system validation.
- Sandbox UI now also includes a real-time trade panel (shipment queue control + market stock/price/pressure readouts) powered by shared `sim-core` trade rules.
- Sandbox UI now also includes a real-time espionage panel (informant recruit/report/sweep controls + status/report readouts) powered by shared `sim-core` espionage rules.
- Sandbox UI now also includes a real-time politics panel (standing/office/treaty controls + legitimacy/stability/influence readouts) powered by shared `sim-core` politics rules.
- Sandbox UI now also includes a real-time battle contract panel (encounter start, formation/reserve controls, force-resolve controls + live instance/result readouts) powered by shared `sim-core` battle contract rules.
- Placeholder player sprite asset is generated in-repo (`tools/generate_player_placeholder_png.py` -> `client-app/assets/player_circle.png`) to keep early UI flow asset-stable.
- Local one-command PoC bootstrap now exists at `scripts/run_local_poc_stack.sh`:
  - starts `world-service` + backend with readiness gates,
  - runs deterministic account/character seed (`backend/scripts/seed_local_poc_account.py`),
  - emits startup handoff payload (`client-app/runtime/startup_handoff.local.json`),
  - can run backend smoke and launch `client-app` bootstrap shell automatically.
- Runtime priority is Windows-first for client delivery and manual validation loops; Linux/Steam client parity is deferred until post-PoC hardening.

### Character Identity and Skill Book Architecture (Planned)
- Character creation will require four permanent identity selections: `faction`, `origin`, `profession`, `aspiration`.
- Each identity option will carry explicit `upside` and `downside` modifier bundles; persistence layer must enforce both are present.
- Identity selections are immutable after creation in the current cycle (future respec mechanics out of scope).
- Education progression will be modeled as a separate XP-backed skill book with benefits-only node effects.
- Skill-book model will include language proficiency nodes by dimension (`speak`, `read`, `write`) per language.
- Communication/document systems will consume language proficiency checks and optional helper contracts (interpreter/translator) for fallback access.

## Data and Eventing Model
### Persistence
- PostgreSQL is canonical source of truth for durable entities/events.
- Schema versioning remains migration-driven and source-controlled.
- Campaign schema baseline is now established via `backend/alembic/versions/0021_campaign_world_foundation.py` with durable tables for regions, settlements, routes, factions, households, armies, caravans, and espionage assets.
- ORM mappings for these entities are defined in `backend/app/models/campaign_world.py` for incremental authority-service integration.
- Planned character-depth persistence additions:
  - identity option definitions and per-character identity selections,
  - XP ledger + spend journal,
  - skill-book node definitions + per-character progression,
  - per-language proficiency state (`speak`/`read`/`write`) per character.

### Eventing (PoC phase)
- Transactional outbox table for service events.
- LISTEN/NOTIFY for low-volume wakeup/fanout signaling.
- Replay-safe processors for idempotent side effects.
- Baseline schema is now present via `backend/alembic/versions/0022_event_store_outbox.py`:
  - `world_events` (append-only event journal),
  - `world_outbox` (durable dispatch queue with retry lock fields),
  - `world_command_idempotency` (scope/key/request-hash dedupe records),
  - `world_processor_cursors` (restart-safe processor checkpoints).
- PostgreSQL `LISTEN/NOTIFY` wake-up path is now wired for outbox inserts:
  - migration `backend/alembic/versions/0023_outbox_notify_trigger.py` adds `world_outbox_notify_insert()` + `trg_world_outbox_notify_insert` on `world_outbox`,
  - FastAPI control plane now starts a reconnecting listener worker (`backend/app/services/outbox_notify_worker.py`) on startup and stops it on shutdown,
  - wake semantics are payload-aware (`outbox_id`, `topic`) while durable replay/idempotency remains grounded in outbox row claiming.

### Eventing (scale phase)
- Introduce Redis and/or Pub/Sub for high-frequency hot-path fanout only after `docs/REDIS_ADOPTION_GATE.md` thresholds and preconditions are met.

## Security and Authority Model
- Server authoritative for gameplay outcomes, progression values, and persistent state transitions.
- Clients are authoritative only for input intent and presentation.
- Existing auth/session policy remains in place while gameplay authority shifts to Rust services.
- Inter-service mutation calls from FastAPI are authenticated with scope-limited shared credentials and signed payload verification; invalid signatures, stale timestamps, and replayed nonces are rejected.
- Release gating requirement: login/register/refresh/logout and force-revocation/session-drain paths must remain covered by regression checks during migration cleanup.

## Build, Packaging, and Distribution
- Windows distribution is channel-based in GCS, with installer-first game delivery.
- Release workflow execution now targets the self-hosted Windows runner label set `[self-hosted, windows, x64, aop-release]` to reuse local toolchains/caches and reduce release latency; workflow run steps use Windows PowerShell shell with `-ExecutionPolicy Bypass` so `pwsh` installation and machine-wide execution-policy changes are not required on the host.
- Self-hosted release workflow bootstraps `gcloud` from Google Cloud SDK release zips (runner-local, non-admin) when missing and exports Cloud SDK bin paths through `GITHUB_PATH` for subsequent release steps.
- Self-hosted release workflow bootstraps Rust via `rustup` and resolves NSIS via installed paths or portable zip fallback (all non-admin) to avoid WSL/bash and Chocolatey elevation dependencies under Windows service runner accounts.
- Release workflow builds/packages:
  - launcher runtime: `launcher-app` (Windows executable embedded in game installer)
  - game installer: `AmbitionsOfPeace-game-installer-win-x64-<version>.exe`
  - game runtime payload: `AmbitionsOfPeace-client-app-win-x64-<version>.zip`
  - game runtime deltas (when compatible source versions exist in retained feed): `AmbitionsOfPeace-client-delta-<to_version>-from-<from_version>.zip`
  - designer runtime: `AmbitionsOfPeace-designer-client-win-x64-<version>.zip`
- Game channel publishes installer/checksum metadata, full runtime payload metadata, delta descriptors, and `latest.json` pointer fields.
- Designer channel publishes deterministic zip manifest/checksum metadata and `latest.json`.
- Feed and archive retention are pruned to latest 3 versions per channel.
- Install/update helpers are script-based (`scripts/install_game_client.ps1`, `scripts/install_designer_client.ps1`).
- Game installer executable is built in CI via NSIS (`scripts/build_game_installer.ps1`) from the packaged runtime zip and embeds `launcher-app` as the primary player entrypoint.
- Launcher (`launcher-app`) is the runtime auth/update gate:
  - login-only surface is rendered first; launcher content/news/update controls render only after authentication,
  - explicit `Login` and `Play` actions are decoupled so account auth can occur without starting gameplay runtime,
  - authenticated launcher auto-refreshes release summary + feed metadata every 60 seconds,
  - in-window news/patch notes rendering via `/release/summary` using `x-client-version` and `x-client-content-version` headers,
  - feed resolution fallback chain (`release summary feed` -> `session feed` -> packaged default `win-game`) to survive stale backend policy feed pointers,
  - progress-visible update flow (delta-first, full-installer fallback),
  - account actions are consolidated in top-right menu with logout available when runtime launch is not active,
  - startup handoff generation and full-screen game launch command.
  - production-first launcher defaults are compile-time injected in CI (`AOP_DEFAULT_API_BASE_URL`) and release launcher uses Windows GUI subsystem (no companion console window).
- Runtime bundles now include `release_version.txt` marker for deterministic install/update acceptance verification.
- Release workflow now runs Windows installer acceptance smoke (`scripts/windows_installer_acceptance_smoke.ps1`) plus gameplay/handoff regression tests before GCS publish.
- Release workflow now also enforces dated external PoC release-gate evidence validation (`backend/scripts/validate_external_poc_release_gate.py`).

## Validation and Quality Gates
Current baseline checks retained during transition:
- `python3 -m compileall backend/app`
- `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_security_edges.py backend/tests/test_publish_drain.py`
- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo test --workspace`
- Tooling deterministic content smoke:
  - `cargo run -p tooling-core -- normalize-json --input <pack.json> --output <normalized.json> --signature-output <normalized.sig.json>`
  - `cargo run -p tooling-core -- import-csv --input-dir <csv_dir> --province-id <province_id> --display-name <display_name> --output <pack.json> --signature-output <pack.sig.json>`
  - `cargo run -p tooling-core -- export-csv --input <pack.json> --output-dir <csv_dir>`
- Province-pack bootstrap smoke:
  - `AOP_PROVINCE_PACK_PATH=assets/content/provinces/acre/acre_poc_v1.json cargo test -p client-app --features bootstrap-shell`
- FastAPI world-entry bridge regression smoke:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_world_entry_bridge.py backend/tests/test_world_bootstrap_3d_contract.py`
- Designer world-pack promotion smoke:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_designer_world_promotion.py backend/tests/test_designer_publish_routes.py`
- Vertical-slice loop regression smoke:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_vertical_slice_loop.py`
  - `python3 backend/scripts/smoke_online_loop.py --base-url <backend_base_url>`
- Deterministic replay/golden smoke:
  - `cargo test -p world-service replay_`
- Observability threshold smoke:
  - `OPS_BASE_URL=<backend-url> OPS_TOKEN=<ops-token> WORLD_SERVICE_BASE_URL=<world-service-url> backend/scripts/check_world_runtime_alerts.sh`
- World-sync backend contract smoke:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_world_sync_feed.py`
- Battle/domain backend contract smoke:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_battle_commands.py backend/tests/test_domain_actions.py`
- Cost guardrail report smoke:
  - `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --output docs/cost-reports/YYYY-MM-estimate.md --budget-total 80`
- Playtest hardening baseline smoke:
  - `backend/scripts/validate_playtest_hardening.sh`
- Windows Rust runtime packaging smoke:
  - `python tools/package_client_app_release.py --version <x.y.z> --exe <path/to/client-app.exe> --output-dir releases/game`
  - `python tools/package_designer_client_release.py --version <x.y.z> --output-dir releases/designer`
  - `python tools/build_runtime_delta.py --from-version <a.b.c> --to-version <x.y.z> --from-zip <path/to/old.zip> --to-zip <path/to/new.zip> --output-dir releases/game`
  - `powershell -ExecutionPolicy Bypass -File scripts/build_game_installer.ps1 -Version <x.y.z> -RuntimeZip <path/to/game-runtime.zip> -OutputDir releases/game`
- Windows installer acceptance smoke:
  - `powershell -ExecutionPolicy Bypass -File scripts/windows_installer_acceptance_smoke.ps1 -FeedRoot <local-feed-root> -SummaryPath <summary.md>`
- External PoC release gate evidence smoke:
  - `python backend/scripts/validate_external_poc_release_gate.py --gate-pointer docs/release-gates/current_gate.json`
- Client bootstrap shell smoke: `cargo run -p client-app --features bootstrap-shell`
- One-command local stack smoke: `scripts/run_local_poc_stack.sh --no-client`
- Manual sandbox smoke (Windows-first): `cargo run -p client-app --features sandbox-ui`.
- CI now includes Windows client sandbox compile gate (`client-windows-sandbox`) and deterministic replay gate (`determinism-replay`) in `.github/workflows/rust-checks.yml`.
- Regression policy: each implemented simulation subsystem must include deterministic unit tests plus payload serialization roundtrip tests to prevent cross-system breakage during rapid iteration.

Migration-era additions (implemented in scaffold phase):
- Rust CI workflow: `.github/workflows/rust-checks.yml`

Migration-era additions still pending:
- long-horizon multi-scenario replay/golden suites beyond current campaign+battle baseline
- broader API contract compatibility tests (FastAPI <-> Rust world service gameplay endpoints beyond inter-service auth boundary)

## Cost-Control Baseline (PoC)
- Keep Cloud Run minimum instances at zero unless a warm instance is operationally required.
- Keep GCS artifact retention at 3 builds.
- Defer Redis/Memorystore until objective performance triggers occur.
- Monthly guardrail and reporting policy is defined in `docs/COST_GUARDRAILS.md`.
- Monthly report generation command: `backend/scripts/generate_monthly_cost_report.py --month YYYY-MM --output docs/cost-reports/YYYY-MM-estimate.md --budget-total 80`.

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
