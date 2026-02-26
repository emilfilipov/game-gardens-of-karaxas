# Plompers Arena Inc. - Technical

## Purpose
Canonical technical source of truth for runtime architecture, backend boundaries, updater pipeline, and CI/CD behavior for the Plompers Arena Inc. refactor.

## Refactor Status
This document defines the target architecture and migration constraints for the 3D pivot.
Unless explicitly noted as "already implemented," items here are implementation targets.

## Active Architecture (Unchanged Platform Stack)

### Runtime Stack
- Bootstrap/orchestrator: Kotlin launcher (`launcher/`)
- Game runtime client: Godot 4.x (`game-client/`)
- Online backend API: FastAPI + PostgreSQL (`backend/`)
- Distribution/update: Velopack + GCS feed
- External content tooling: standalone designer program (`designer-client/`)

### Directional Model
- Online arena battle royale with instance-aware gameplay.
- Server-authoritative gameplay values and progression.
- Client handles rendering/input/UI and sends gameplay intent.

## Product Rename Contract
- Product name: `Plompers Arena Inc.`
- All player-facing labels, launcher text, and release-note headers must migrate to new naming.
- Legacy internal paths/binary identifiers may temporarily coexist during migration if required for updater compatibility.
- Migration tasks must explicitly track any remaining `Children of Ikphelion` labels.

## Runtime Entry and 3D Migration Contract
- Existing Godot bootstrap entrypoint remains: `game-client/scenes/bootstrap.tscn`.
- Existing shell script remains: `game-client/scripts/client_shell.gd`.
- World runtime is migrating from 2D baseline toward a 3D arena scene.
- Top-down / PoE-like camera readability is mandatory after 3D conversion.
- Skill graph viewer must remain accessible in account list/create flows during and after migration.

## Functional Parity Requirements (Must Keep)
- Auth (`login/register`, optional MFA)
- Account hub (character list/create/select/play)
- Skill graph viewer surface and interactions in account shell
- Settings and update flows
- Backend bootstrap contract from selected character to runtime instance entry

## 3D Arena Runtime Target
- World presentation: 3D scene with high-angle top-down camera.
- Avatar presentation: bouncy-ball player model with physics-based movement/impulse interactions.
- Arena baseline map: flat surface with grass foliage.
- Camera behavior:
  - stable high-angle top-down framing,
  - enough zoom for tactical readability,
  - no disorienting cinematic drift by default.

## Black/White Visual System Contract
- Baseline state for world assets is monochrome (black/white/gray).
- Color reveal occurs only on interaction events.
- Interaction-driven colorization examples:
  - ground/grass touched by player gains color,
  - wall/object collision points gain color.
- Colorization implementation must be deterministic enough for gameplay readability and QA replay checks.

## UI Contract
- Black/white UI direction is canonical.
- Reference pack: `concept_art/ui_concept_blackwhite/ui_concept_bw_*.png`.
- Migration must preserve existing feature coverage (not remove flows to simplify styling).
- Skill graph viewer remains first-class in account flows.

## Backend Responsibilities (Unchanged)
- Auth/session lifecycle (register/login/refresh/logout + MFA)
- Character lifecycle (list/create/select/delete/location/bootstrap)
- Content/config delivery (`/content/runtime-config`, `/content/bootstrap`)
- Level authoring APIs (`/levels`) for external designer tooling
- Runtime publish/version operations under `/content/*`
- Designer publish orchestration under `/designer/publish` (backend-mediated GitHub commit + workflow dispatch)
- Gameplay authority (`/gameplay/resolve-action`)
- Release notes authority for builds via `release_records` (served through `/release/summary`)

## Packaging Contract (Migration Target)
- Installer payload includes game launcher/runtime entry plus designer executable.
- Player-facing names and shortcuts migrate to Plompers Arena Inc. naming.
- Update status persistence contract remains `<install_root>/logs/update_status.json`.
- Release notes remain visible in dedicated `Update` menu.

## Test and Validation Direction
Current checks remain in use while migration proceeds:
- Backend syntax sanity:
  - `python3 -m compileall backend/app`
- Launcher tests:
  - `./gradlew :launcher:test`

Migration check additions required by tasks:
- 3D runtime contract harness (top-down camera + arena scene load + movement spawn checks)
- Graph viewer parity regression checks
- Visual colorization-rule validation checks (interaction creates localized color changes)

## CI/CD Scope
- Release workflow: `.github/workflows/release.yml`
- Backend deploy workflow: `.github/workflows/deploy-backend.yml`
- Security scan workflow: `.github/workflows/security-scan.yml`
- Release workflow push triggers continue using strict runtime/package allowlist.

## Distribution Channels
- Standalone launcher remains primary (`Velopack + GCS`).
- Dual-distribution Steam strategy remains documented in:
  - `docs/STEAM_DUAL_DISTRIBUTION.md`

## Documentation Rule
`docs/TECHNICAL.md` is canonical for technical decisions.
Any architecture/infra/runtime change is incomplete until reflected here in the same change.
