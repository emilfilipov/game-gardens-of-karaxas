# Deprecation Audit (AOP-PIVOT-032)

Date: 2026-03-12

## Objective
Inventory and reduce legacy prototype documentation/runtime artifacts that can cause direction drift during the Ambitions of Peace migration.

## Classification Rules
- `archived`: superseded and moved to archive path.
- `compatibility-only`: retained for transitional implementation support.
- `active`: aligned with current canonical direction.

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

## Retained Compatibility-Only Documents
- `docs/INSTALLER.md` (legacy path naming notes required for updater compatibility)
- `docs/STEAM_DUAL_DISTRIBUTION.md` (future channel model reference)
- `docs/ART_PIPELINE_CONTRACT.md` (asset ingest guidance used by release validation tooling)

## Active Documents Updated In This Task
- `docs/OPERATIONS.md`
- `docs/SECURITY.md`
- `docs/README.md`

## Result
Legacy product-direction docs are removed from active docs root and preserved under archive path for historical traceability.
