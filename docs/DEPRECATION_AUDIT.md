# Deprecation Audit

Last updated: 2026-03-13

## Objective
Remove prototype-era modules, assets, and documentation that are no longer required for the Rust-first Ambitions of Peace runtime and tooling track.

## Classification Rules
- `removed`: deleted from active repository tracking.
- `active`: retained and aligned with canonical docs and current delivery path.

## Removed Legacy Modules and Toolchains
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
- Concept-art bundle and concept-art helper scripts.

## Removed Legacy Documentation and Assets
- Superseded prototype/product docs:
  - `docs/ART_PIPELINE_CONTRACT.md`
  - `docs/archive/legacy-prototype/ART_DIRECTION_BOARD.md`
  - `docs/archive/legacy-prototype/CHARACTER_FLOW_QA.md`
  - `docs/archive/legacy-prototype/CONFIG_FIELDS.md`
  - `docs/archive/legacy-prototype/ENGINE_SPIKE_GOK_MMO_176.md`
  - `docs/archive/legacy-prototype/ISOMETRIC_COORDINATE_SPEC.md`
  - `docs/archive/legacy-prototype/ISOMETRIC_VERTICAL_SLICE_GATES.md`
  - `docs/archive/legacy-prototype/LEVEL_SCHEMA_V3.md`
  - `docs/archive/legacy-prototype/LEVEL_SCHEMA_V3_MIGRATION.md`
  - `docs/archive/legacy-prototype/LORE.md`
  - `docs/archive/legacy-prototype/TOWER_ADMIN_CHECKLIST.md`
- Prototype art/asset pipeline artifacts:
  - `assets/README.md`
  - `assets/iso_asset_manifest.json`
  - `assets/icons/game_icon.ico`
  - `assets/icons/game_icon.png`
  - `assets/tiles/*`
  - `assets/characters/sellsword_v1/*`
  - `assets/characters/karaxas_human_*`
  - `tools/generate_sellsword_sprite_pack.py`
  - `tools/validate_asset_ingest.py`

## Active Runtime Scope After Cleanup
- `backend/`
- `world-service/`
- `sim-core/`
- `tooling-core/`
- `client-app/`
- `designer-client/`
- `assets/content/` province-pack content

## Result
The repository is stripped to the current Rust-first game/runtime/tooling path with legacy prototype-era stacks and asset pipelines removed from tracked history.
