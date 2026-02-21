# Gardens of Karaxas

Gardens of Karaxas is an account-based online RPG project with a Godot-first desktop client and Velopack distribution model.

## Canonical Documentation
- `docs/GAME.md` - all game/product information.
- `docs/TECHNICAL.md` - all technical architecture and stack decisions.

Read both before implementing changes.

## Project Structure
- `launcher/` - Kotlin bootstrap/orchestration module for updater + runtime handoff.
- `game-client/` - Godot 4.x unified client shell (auth/account/game/editor) and runtime bootstrap contract files.
- `backend/` - FastAPI backend services (auth, lobby/social, characters, chat, release ops).
- `assets/` - shared visual/icon assets.
- `docs/` - canonical and supporting documentation.
- `scripts/` - packaging and release scripts.
- `tools/` - setup wrapper and update helper tooling.
- `.github/workflows/` - CI/CD automation.

## Build and Run
- Launcher build:
  - `./gradlew :launcher:build`
- Launcher tests:
  - `./gradlew :launcher:test`
- Backend local run (after configuring `backend/.env`):
  - `backend/scripts/run_local.sh`

## Distribution and Deploy
- Launcher packaging/release: `docs/INSTALLER.md` and `.github/workflows/release.yml`
- Backend deployment: `backend/scripts/deploy_cloud_run.sh` and `.github/workflows/deploy-backend.yml`

## Operations and Security
- Operations runbook and rollout checklist: `docs/OPERATIONS.md`
- Security hardening, incident runbooks, and readiness checklist: `docs/SECURITY.md`

## Isometric and Content Authoring References
- Level schema v3 contract: `docs/LEVEL_SCHEMA_V3.md`
- Level schema v3 migration path: `docs/LEVEL_SCHEMA_V3_MIGRATION.md`
- Art pipeline/export contract: `docs/ART_PIPELINE_CONTRACT.md`
- Isometric vertical-slice quality gates: `docs/ISOMETRIC_VERTICAL_SLICE_GATES.md`
