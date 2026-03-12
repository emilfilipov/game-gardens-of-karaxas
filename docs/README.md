# Ambitions of Peace

Ambitions of Peace is a persistent online medieval war-and-politics RPG in active migration from a prior prototype stack to a Rust-first implementation.

## Canonical Documentation
- `docs/GAME.md` - canonical product/game scope and gameplay contracts.
- `docs/TECHNICAL.md` - canonical architecture, infra, and migration contracts.
- `docs/TASKS.md` - granular execution backlog and strict sequencing for migration work.
- `docs/adr/` - accepted architecture decision records for migration-critical decisions.

## Archived Documentation
- `docs/archive/legacy-prototype/` - superseded prototype-era documents retained for historical traceability only.
- `docs/DEPRECATION_AUDIT.md` - deprecation inventory and classification for migration cleanup.

## Current Repository State
Current modules include transitional prototype components plus backend/release infrastructure that remain reusable:
- `launcher/` - Kotlin bootstrap/updater orchestration.
- `game-client/` - legacy Godot runtime prototype (transitional).
- `backend/` - FastAPI online services and Cloud SQL integration.
- `designer-client/` - legacy external authoring prototype (transitional).
- `sim-core/` - shared Rust simulation-domain contracts scaffold.
- `world-service/` - Rust world-authority service skeleton (Axum + health/readiness/config endpoints + tracing/request IDs).
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

## Build and Test Baseline
Current baseline checks retained during transition:
- `python3 -m compileall backend/app`
- `./gradlew :launcher:test`
- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo test --workspace`

Rust CI workflow:
- `.github/workflows/rust-checks.yml`

## Packaging and Release
- Windows packaging script: `scripts/pack.ps1`
- Release automation: `.github/workflows/release.yml`
- Installer/updater behavior: `docs/INSTALLER.md`
- Standalone + Steam channel strategy: `docs/STEAM_DUAL_DISTRIBUTION.md`
