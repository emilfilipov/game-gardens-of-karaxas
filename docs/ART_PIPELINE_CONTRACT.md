# Art Pipeline Contract (Production)

## Source of Truth
- Raw source files: layered authoring files (`.psd`, `.kra`, `.aseprite`) in artist workspace.
- Runtime exports: `.png` only for game ingestion.
- Asset registry: `assets/iso_asset_manifest.json`.

## Naming and Packaging
- Asset keys: lowercase snake-case (`^[a-z0-9_\\-]+$`).
- Runtime filenames: `karaxas_<asset_key>_<variant>_<size>.png`.
- Characters and tiles are grouped by category folders:
  - `assets/characters/`
  - `assets/tiles/`
- Manifest entries must include:
  - `key`, `path`, `category`, `width`, `height`, `pivot_x`, `pivot_y`, `frame_count`.

## Visual Baseline
- Warm/vibrant palette as baseline.
- Soft global lighting baseline; grim-dark mood done by effect layers, not destructive recoloring of base assets.
- Readability first: silhouettes must remain legible at gameplay zoom.

## Export Profiles
- PNG RGBA8.
- Premultiplied alpha disabled for source exports.
- Pixel boundaries aligned for gameplay-critical sprites.
- Stable pivot conventions:
  - characters/props default `(0.5, 1.0)`.

## Validation Gate
- `tools/validate_asset_ingest.py` validates:
  - naming policy,
  - file existence,
  - PNG format,
  - manifest dimension match,
  - pivot normalization,
  - frame-count validity.
- Release pipeline fails if ingest validation fails.
