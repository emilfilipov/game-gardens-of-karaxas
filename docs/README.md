# Ambitions of Peace

Ambitions of Peace is a persistent online medieval war-and-politics RPG in active migration from a prior prototype stack to a Rust-first implementation.
Core simulation contract: all core gameplay systems run in real-time (travel, logistics, trade, espionage, politics, combat); battles run as instanced real-time encounters.

## Canonical Documentation
- `docs/GAME.md` - canonical product/game scope and gameplay contracts.
- `docs/TECHNICAL.md` - canonical architecture, infra, and migration contracts.
- `docs/TASKS.md` - granular execution backlog and strict sequencing for migration work.
- `docs/adr/` - accepted architecture decision records for migration-critical decisions.
- `docs/REDIS_ADOPTION_GATE.md` - explicit Redis cutover thresholds, dual-write migration, and rollback contract.

## Archived Documentation
- `docs/archive/legacy-prototype/` - superseded prototype-era documents retained for historical traceability only.
- `docs/DEPRECATION_AUDIT.md` - deprecation inventory and classification for migration cleanup.

## Current Repository State
Current modules include transitional prototype components plus backend/release infrastructure that remain reusable:
- `launcher/` - Kotlin bootstrap/updater orchestration.
- `game-client/` - legacy Godot runtime prototype (transitional).
- `backend/` - FastAPI online services and Cloud SQL integration, including PostgreSQL outbox event-store tables and LISTEN/NOTIFY wake worker scaffolding for PoC fanout.
- `designer-client/` - legacy external authoring prototype (transitional).
- `sim-core/` - shared Rust simulation-domain contracts (travel + real-time logistics/trade/espionage/politics/battle-instance contract).
- `world-service/` - Rust world-authority service with deterministic tick runner, travel APIs, and real-time logistics/trade/espionage/politics/battle-contract authority endpoints.
- `tooling-core/` - Rust tooling/shared validation scaffold.
- `client-app/` - Rust client runtime scaffold.
- `assets/` - shared content/assets.
- `docs/` - canonical and supporting documentation.
- `docs/archive/` - archived/superseded documentation.
- `scripts/` - packaging/release scripts.
- `tools/` - helper tooling.
- `.github/workflows/` - CI/CD automation.

## Target Technical Direction
- Primary language: Rust.
- Client/runtime direction: Bevy + code-first UI tooling (`bevy_egui`).
- Authority services: Rust (Axum/Tokio) with PostgreSQL persistence.
- Existing FastAPI control-plane services remain active during migration.
- Release artifacts remain in GCS with strict retention cap.
- Client runtime priority is Windows-first; Linux/Steam client parity is deferred until after PoC maturity.

## Build and Test Baseline
Current baseline checks retained during transition:
- `python3 -m compileall backend/app`
- `./gradlew :launcher:test`
- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo test --workspace`

Rust CI workflow:
- `.github/workflows/rust-checks.yml`

Manual sandbox client run (feature-gated):
- `cargo run -p client-app --features sandbox-ui`
- Placeholder player sprite generation: `python3 tools/generate_player_placeholder_png.py`
- Sandbox includes real-time logistics validation controls (army supply status + convoy queue action).
- Sandbox includes real-time trade validation controls (shipment queue + market stock/price readouts).
- Sandbox includes real-time espionage validation controls (informant recruit/report/sweep + reliability/confidence readouts).
- Sandbox includes real-time politics validation controls (standing/office/treaty actions + legitimacy/stability/influence readouts).
- Sandbox includes real-time battle-contract validation controls (encounter start, formation/reserve actions, resolve + instance/result readouts).

## Packaging and Release
- Windows packaging script: `scripts/pack.ps1`
- Release automation: `.github/workflows/release.yml`
- Installer/updater behavior: `docs/INSTALLER.md`
- Standalone + Steam channel strategy: `docs/STEAM_DUAL_DISTRIBUTION.md`
