# Children of Ikphelion

Children of Ikphelion is an online isometric ARPG project with a Godot client runtime, Kotlin launcher/updater, and FastAPI backend services.

## Canonical Documentation
- `docs/GAME.md` - product/game scope and player-facing behavior.
- `docs/TECHNICAL.md` - technical architecture and engineering decisions.

## Project Structure
- `launcher/` - Kotlin bootstrap/updater orchestration.
- `game-client/` - Godot 4.x runtime shell, world scene, and admin tooling.
- `backend/` - FastAPI online services (auth/session/characters/content/runtime config/events).
- `assets/` - shared game assets.
- `docs/` - canonical + supporting documentation.
- `scripts/` - packaging/release scripts.
- `tools/` - setup wrapper and update helper tooling.
- `.github/workflows/` - CI/CD automation.

## Build and Test
- Launcher tests:
  - `./gradlew :launcher:test`
- UI regression harness:
  - `python3 game-client/tests/check_ui_regression.py`

## Packaging and Release
- Windows packaging script: `scripts/pack.ps1`
- Release automation: `.github/workflows/release.yml`
- Installer/updater behavior: `docs/INSTALLER.md`
- Standalone + Steam dual-channel plan: `docs/STEAM_DUAL_DISTRIBUTION.md`
