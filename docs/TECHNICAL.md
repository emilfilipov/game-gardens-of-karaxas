# Ambitions of Peace - Technical

## Purpose
Canonical technical source of truth for runtime architecture, backend/service boundaries, release/distribution behavior, and migration sequencing.

## Architecture Decision Records
Accepted ADRs for the current migration program:
- `docs/adr/0001-rust-first-runtime-and-services.md`
- `docs/adr/0002-bevy-code-first-ui-and-tooling.md`
- `docs/adr/0003-phased-fastapi-to-rust-authority-migration.md`
- `docs/adr/0004-redis-deferral-and-adoption-gate.md`

## Current State Summary (As Of 2026-03-12)
The repository currently contains a prior prototype stack:
- Kotlin launcher (`launcher/`)
- Godot runtime client (`game-client/`)
- FastAPI + PostgreSQL backend (`backend/`)
- Velopack + GCS release pipeline

This state is treated as transitional. The active implementation target is the Crusades-era persistent strategy RPG model documented in `docs/GAME.md`.

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

### Redis policy
- Redis is deferred for PoC cost control.
- PoC eventing uses PostgreSQL outbox + LISTEN/NOTIFY where practical.
- Redis (Memorystore) adoption trigger is defined by measured latency/contention/throughput pressure, not by assumption.

## Runtime and Service Topology (Target)
### Control plane (transitional)
- Existing FastAPI auth/session/account/content/release endpoints remain operational during migration.

### New world authority plane
- Rust world service owns campaign simulation ticks, economic/logistics simulation, espionage state, and instanced battle authority orchestration.
- Shared Rust domain crates provide deterministic rules used by both service and client presentation layers.

### Client
- Bevy client renders campaign and battle surfaces.
- Client sends intent; authority services resolve final state transitions.

## Data and Eventing Model
### Persistence
- PostgreSQL is canonical source of truth for durable entities/events.
- Schema versioning remains migration-driven and source-controlled.

### Eventing (PoC phase)
- Transactional outbox table for service events.
- LISTEN/NOTIFY for low-volume wakeup/fanout signaling.
- Replay-safe processors for idempotent side effects.

### Eventing (scale phase)
- Introduce Redis and/or Pub/Sub for high-frequency hot-path fanout once PoC metrics justify it.

## Security and Authority Model
- Server authoritative for gameplay outcomes, progression values, and persistent state transitions.
- Clients are authoritative only for input intent and presentation.
- Existing auth/session policy remains in place while gameplay authority shifts to Rust services.

## Build, Packaging, and Distribution
- Windows distribution remains launcher-based with Velopack feed in GCS.
- Release workflow continues to package launcher/runtime payloads and upload to GCS feed/archive.
- Installer/updater logging contract remains under `<install_root>/logs`.

## Validation and Quality Gates
Current baseline checks retained during transition:
- `python3 -m compileall backend/app`
- `./gradlew :launcher:test`

Migration-era additions (to be introduced with Rust modules):
- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo test --workspace`
- simulation determinism replay checks
- API contract compatibility tests (FastAPI <-> Rust world service)

## Cost-Control Baseline (PoC)
- Keep Cloud Run minimum instances at zero unless a warm instance is operationally required.
- Keep GCS artifact retention at 3 builds.
- Defer Redis/Memorystore until objective performance triggers occur.
- Reassess monthly cost envelope after first fully playable province vertical slice.

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
