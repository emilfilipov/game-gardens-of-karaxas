# Ambitions of Peace

Ambitions of Peace is a persistent online medieval war-and-politics RPG in active migration from a prior prototype stack to a Rust-first implementation.

## Canonical Documentation
- `docs/GAME.md` - canonical product/game scope and gameplay contracts.
- `docs/TECHNICAL.md` - canonical architecture, infra, and migration contracts.
- `docs/TASKS.md` - granular execution backlog and strict sequencing for migration work.
- `docs/adr/` - accepted architecture decision records for migration-critical decisions.

## Current Repository State
Current modules include transitional prototype components plus backend/release infrastructure that remain reusable:
- `launcher/` - Kotlin bootstrap/updater orchestration.
- `game-client/` - legacy Godot runtime prototype (transitional).
- `backend/` - FastAPI online services and Cloud SQL integration.
- `designer-client/` - legacy external authoring prototype (transitional).
- `assets/` - shared content/assets.
- `docs/` - canonical and supporting documentation.
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

Planned Rust checks (introduced with workspace scaffold):
- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo test --workspace`

## Packaging and Release
- Windows packaging script: `scripts/pack.ps1`
- Release automation: `.github/workflows/release.yml`
- Installer/updater behavior: `docs/INSTALLER.md`
- Standalone + Steam channel strategy: `docs/STEAM_DUAL_DISTRIBUTION.md`
