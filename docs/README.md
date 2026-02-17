# Gardens of Karaxas

Gardens of Karaxas is an account-based online RPG project with a launcher-first desktop distribution model.

## Canonical Documentation
- `docs/GAME.md` - all game/product information.
- `docs/TECHNICAL.md` - all technical architecture and stack decisions.

Read both before implementing changes.

## Project Structure
- `launcher/` - Kotlin launcher UI with login/lobby screens and updater integration.
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
