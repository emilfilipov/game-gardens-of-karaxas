# Level Schema v3 (Hybrid Placement)

## Purpose
`Level Schema v3` extends the current layered grid model (`v2`) with stable per-object placements so we can mix gameplay-safe grid authoring with freeform visual prop transforms.

## Backward Compatibility
- `v2` levels continue to work unchanged.
- `v3` keeps `layers` for logical tile authoring and adds `objects` for freeform placements.
- Legacy readers can ignore `objects` and still consume `layers`.

## Canonical Payload Shape
```json
{
  "name": "l1_ground",
  "descriptive_name": "Ground Floor",
  "order_index": 1,
  "schema_version": 3,
  "width": 80,
  "height": 48,
  "spawn_x": 3,
  "spawn_y": 3,
  "layers": {
    "0": [{"x": 1, "y": 1, "asset_key": "grass_tile"}],
    "1": [{"x": 3, "y": 3, "asset_key": "wall_block"}],
    "2": [{"x": 5, "y": 5, "asset_key": "cloud_soft"}]
  },
  "objects": [
    {
      "object_id": "tree_001",
      "asset_key": "tree_oak",
      "layer_id": 1,
      "transform": {
        "x": 12.5,
        "y": 7.25,
        "z": 0.0,
        "rotation_deg": 0.0,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "pivot_x": 0.5,
        "pivot_y": 1.0
      }
    }
  ],
  "transitions": []
}
```

## Rules
- `object_id` is required and unique per level payload.
- `asset_key` must match content asset definitions.
- `layer_id` must be `0..32`.
- `transform.x/y` must be within level bounds.
- `pivot_x/pivot_y` must be normalized (`0..1`).
- `v3` objects are optional, but if present payload `schema_version` must be `>=3`.

## Runtime Intent
- Grid layers remain authoritative for deterministic gameplay cells.
- Objects are primarily for presentation and precise placement, with future optional gameplay linkage (for example per-object collision templates).
