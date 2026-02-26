# Art Pipeline Contract (Production)

## Source of Truth
- Raw source files: layered authoring files (`.blend`, `.psd`, `.kra`, `.aseprite`) in artist workspace.
- Runtime exports: engine-ingestable assets (`.glb`, `.png`) only.
- Asset registry: `assets/iso_asset_manifest.json` (to be renamed in implementation if schema changes).

## Naming and Packaging
- Asset keys: lowercase snake-case (`^[a-z0-9_\\-]+$`).
- Runtime filenames should keep stable category prefixes until dedicated migration task updates naming conventions.
- Asset categories include characters, environment, foliage, and FX overlays.

## Visual Baseline
- Default asset presentation is monochrome (black/white/gray).
- Gameplay interaction drives color reveal overlays.
- Readability first: silhouettes and interactables remain clear from top-down camera.

## Export Profiles
- Environment/character meshes: `.glb` with documented scale/pivot conventions.
- Texture exports: PNG RGBA8.
- Preserve non-destructive grayscale master textures for interaction-colorization pipeline.

## Validation Gate
- `tools/validate_asset_ingest.py` (or successor task output) validates:
  - naming policy,
  - file existence,
  - manifest schema,
  - dimensions/metadata,
  - category and pivot rules.
- Release pipeline fails if ingest validation fails.
