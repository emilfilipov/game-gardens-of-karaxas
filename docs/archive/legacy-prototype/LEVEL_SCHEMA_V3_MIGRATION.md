# Level Schema v3 Migration Plan

## Objective
Adopt hybrid level payloads (`v3`) without breaking existing `v2` level data or clients.

## Database Migration
- Alembic revision `0017_level_schema_v3_objects` adds:
  - `levels.object_placements` (`JSON`, default `[]`).
- Downgrade removes `object_placements`.

## API Compatibility Strategy
1. Read path:
   - Existing rows without object data return `objects: []`.
   - `schema_version` remains at least `2` and can be `3` for hybrid payloads.
2. Write path:
   - Existing `v2` payloads remain valid.
   - `objects` are accepted only when `schema_version >= 3`.
   - Duplicate `object_id` values are rejected.
3. Legacy adapter behavior:
   - `wall_cells` is still derived from layered collision tiles for compatibility.
   - No change required in legacy clients that only read layered grid data.

## Rollout Sequence
1. Deploy migration + API with `objects` support.
2. Keep editor in `v2` mode initially.
3. Enable `v3` authoring in admin tooling behind explicit save schema version.
4. Observe payload validation errors and DB metrics.
5. Promote `v3` to default schema for new authored levels.

## Rollback
- Disable `v3` authoring in editor/UI.
- Existing `v3` levels still readable because `layers` remain present.
- If required, Alembic downgrade removes `object_placements` after data export.
