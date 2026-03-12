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
  - FastAPI world bootstrap now bridges to Rust world-service signed world-entry endpoint and preserves fallback compatibility if bridge calls fail.
  - FastAPI now includes `POST /gameplay/vertical-slice-loop` orchestration flow for campaign action -> battle instance -> persistence writeback.
- `designer-client/` - legacy external authoring prototype (transitional).
- `sim-core/` - shared Rust simulation-domain contracts (travel + real-time logistics/trade/espionage/politics/battle-instance contract).
- `world-service/` - Rust world-authority service with deterministic tick runner, travel APIs, and real-time logistics/trade/espionage/politics/battle-contract authority endpoints.
- `tooling-core/` - Rust tooling/shared validation scaffold.
  - Deterministic content CLI commands:
    - `cargo run -p tooling-core -- normalize-json --input <pack.json> --output <normalized.json> --signature-output <normalized.sig.json>`
    - `cargo run -p tooling-core -- import-csv --input-dir <csv_dir> --province-id <province_id> --display-name <display_name> --output <pack.json> --signature-output <pack.sig.json>`
    - `cargo run -p tooling-core -- export-csv --input <pack.json> --output-dir <csv_dir>`
    - `cargo run -p tooling-core -- hash --input <pack.json>`
- `client-app/` - Rust client runtime with feature-gated Bevy bootstrap shell (`bootstrap-shell`) and simulation sandbox (`sandbox-ui`).
- `assets/` - shared content/assets.
  - First province pack: `assets/content/provinces/acre/` with CSV source + normalized JSON/signature artifacts.
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
  - Includes deterministic replay gate (`determinism-replay`) for campaign+battle golden snapshot validation.

Manual sandbox client run (feature-gated):
- `cargo run -p client-app --features bootstrap-shell`
- `cargo run -p client-app --features sandbox-ui`
- Placeholder player sprite generation: `python3 tools/generate_player_placeholder_png.py`
- Bootstrap shell supports launcher/session handoff via env vars (`AOP_HANDOFF_ACCESS_TOKEN`, `AOP_HANDOFF_SESSION_ID`, optional user metadata) and performs authenticated `/characters` + `/characters/{id}/world-bootstrap` fetches before campaign entry.
- Bootstrap shell campaign entry now includes a map rendering MVP (settlement nodes, roads/sea routes, army/caravan markers, fog-state coloring, zoom slider).
- Bootstrap shell includes code-first domain panels (`character`, `household`, `logistics`, `trade`, `espionage`, `diplomacy`, `notifications`) with hotkeys (`F1`..`F7`) and persisted layout presets (`client-app/runtime/panel_layout.json` by default).
- Bootstrap shell includes role-gated tools mode for in-client map authoring (settlement/route edit, validation before save, JSON load/save to `client-app/runtime/authored_map.json` by default).
- Bootstrap shell now loads campaign map defaults from `AOP_PROVINCE_PACK_PATH` (default `assets/content/provinces/acre/acre_poc_v1.json`) before falling back to embedded sample map data.
- Sandbox includes real-time logistics validation controls (army supply status + convoy queue action).
- Sandbox includes real-time trade validation controls (shipment queue + market stock/price readouts).
- Sandbox includes real-time espionage validation controls (informant recruit/report/sweep + reliability/confidence readouts).
- Sandbox includes real-time politics validation controls (standing/office/treaty actions + legitimacy/stability/influence readouts).
- Sandbox includes real-time battle-contract validation controls (encounter start, formation/reserve actions, resolve + instance/result readouts).
- Online loop smoke harness (`backend/scripts/smoke_online_loop.py`) now exercises login + character bootstrap + gameplay resolve + vertical-slice battle/writeback endpoint.

## Packaging and Release
- Windows packaging script: `scripts/pack.ps1`
- Release automation: `.github/workflows/release.yml`
- Installer/updater behavior: `docs/INSTALLER.md`
- Standalone + Steam channel strategy: `docs/STEAM_DUAL_DISTRIBUTION.md`
