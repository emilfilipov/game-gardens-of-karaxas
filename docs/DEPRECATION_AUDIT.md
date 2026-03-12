# Deprecation Audit (AOP-PIVOT-032)

Date: 2026-03-12

## Objective
Remove legacy prototype assets/modules that create migration drift and keep only components aligned with the Rust-first Ambitions of Peace architecture.

## Classification Rules
- `archived`: moved under `docs/archive/legacy-prototype/`.
- `removed`: deleted from active repository tracking.
- `active`: retained and aligned with canonical docs.

## Archived Documents
Moved to `docs/archive/legacy-prototype/`:
- `ART_DIRECTION_BOARD.md`
- `LORE.md`
- `ENGINE_SPIKE_GOK_MMO_176.md`
- `ISOMETRIC_COORDINATE_SPEC.md`
- `ISOMETRIC_VERTICAL_SLICE_GATES.md`
- `LEVEL_SCHEMA_V3.md`
- `LEVEL_SCHEMA_V3_MIGRATION.md`
- `CHARACTER_FLOW_QA.md`
- `TOWER_ADMIN_CHECKLIST.md`
- `CONFIG_FIELDS.md`

## Removed Legacy Modules/Artifacts
Removed from active repository tracking:
- Kotlin/Gradle launcher stack:
  - `launcher/`
  - `build.gradle.kts`, `settings.gradle.kts`, `gradlew`, `gradlew.bat`, `gradle/`, `gradle.properties`
- Godot runtime stack:
  - `game-client/`
- Legacy .NET wrapper helpers:
  - `tools/setup-wrapper/`
  - `tools/update-helper/`
- Blender generation/tooling artifacts:
  - `tools/blender/`
  - `assets/3d/`
- Deprecated packaging/tooling leftovers:
  - `scripts/pack.ps1`
  - `tools/generate_config_docs.py`
  - `icon_2.png`
  - `issues_png/`
- Previously removed in earlier cleanup:
  - legacy `concept_art/` bundle and concept-art helper scripts.

## Active Documents Updated In This Cleanup
- `docs/README.md`
- `docs/INSTALLER.md`
- `docs/OPERATIONS.md`
- `docs/GAME.md`
- `docs/TECHNICAL.md`
- `docs/TASKS.md`
- `AGENTS.md`

## Result
The active repository is now aligned to the Rust-first stack (`backend`, `world-service`, `sim-core`, `client-app`, `designer-client`, `tooling-core`) with no retained Kotlin/Godot/Gradle/Blender compatibility modules.
