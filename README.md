# Gardens of Karaxas

Top-down pixel art/stylized fantasy dungeon crawler set in the endless Tower of Karaxas.

## Canonical Documentation
- `GAME.md` - all game/product information.
- `TECHNICAL.md` - all technical architecture and stack decisions.

Read both before implementing changes.

## Project Structure
- Current:
  - `launcher/` - Windows launcher/updater shell.
  - `assets/` - game content and presentation assets.
  - `scripts/` - packaging and release scripts.
  - `tools/` - setup wrapper and update helper tooling.
  - `.github/workflows/` - CI/CD automation.
  - `build.gradle.kts`, `settings.gradle.kts`, `gradlew`, `gradle/` - Gradle build scaffold.
- Planned (not scaffolded yet):
  - `sim/` - pure Kotlin simulation and domain logic.
  - `game/` - presentation and gameplay orchestration.
  - `desktop/` - standalone desktop runtime.

## Build
- Build launcher module:
  - `./gradlew :launcher:build`
- Build launcher fat jar:
  - `./gradlew :launcher:fatJar`

## Distribution
- Windows packaging: `INSTALLER.md`
- Release notes templates: `RELEASE_NOTES_TEMPLATE.md`, `.github/release-body-template.md`
