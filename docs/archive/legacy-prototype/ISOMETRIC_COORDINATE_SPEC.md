# Isometric Coordinate Specification

## Scope
This document locks the canonical coordinate, transform, pivot, sorting, and rounding rules for `GOK-MMO-175`.
All gameplay runtime, collision, persistence, and editor picking must use this contract.

## Constants
- Projection: `2:1` dimetric isometric.
- Tile footprint: `TILE_W = 64`, `TILE_H = 32` pixels.
- Half tile: `HALF_W = 32`, `HALF_H = 16`.
- Zoom default/range (from visual lock): `0.80x` default, `0.70x-1.10x`.
- Deterministic epsilon: `EPS = 1e-6`.
- Deterministic fixed precision for sort/persist: `FP = 1024` (1/1024 tile units).

## Coordinate Spaces
- `tile`: integer map address `(tx, ty)` for logical occupancy/collision cells.
- `world`: continuous map position `(wx, wy)` in tile units.
  - `tile(tx, ty)` owns world square `[tx, tx+1) x [ty, ty+1)`.
- `screen_iso`: pre-camera pixel position `(sx, sy)` in projected space.
- `screen_view`: final viewport pixel position after camera/zoom.

## Forward Transform (World -> Screen)
Given world `(wx, wy)`:

```text
sx = (wx - wy) * HALF_W
sy = (wx + wy) * HALF_H
```

Apply camera and zoom:

```text
vx = (sx - cam_x) * zoom + view_center_x
vy = (sy - cam_y) * zoom + view_center_y
```

Reference vectors:
- `(0, 0) -> (0, 0)`
- `(1, 0) -> (32, 16)`
- `(0, 1) -> (-32, 16)`
- `(10, 4) -> (192, 224)`

## Inverse Transform (Screen -> World)
Remove viewport/camera:

```text
sx = ((vx - view_center_x) / zoom) + cam_x
sy = ((vy - view_center_y) / zoom) + cam_y
```

Then:

```text
ix = sx / HALF_W
iy = sy / HALF_H
wx = (ix + iy) / 2
wy = (iy - ix) / 2
```

## Tile Origin and Pivot Rules
- Level origin is logical tile `(0, 0)`.
- Floor tile art (`64x32`) is anchored to the tile center projection point.
- Characters/props use a ground-contact pivot:
  - default normalized pivot `(0.5, 1.0)` in source frame.
  - data-driven pivot offsets may shift this anchor for specific assets.
- Tall objects (for example trees) keep their collision at base pivot region only; canopy is visual-only unless explicitly authored otherwise.

## Deterministic Rounding and Ownership
Use half-open ownership with `floor` semantics (never truncation):

```text
tile_x = floor(wx + EPS)
tile_y = floor(wy + EPS)
```

Rules:
- Lower bound inclusive, upper bound exclusive.
- Negative coordinates must use mathematical `floor`, not cast/truncate.
- Persisted coordinates are quantized to fixed precision:

```text
persist_wx = round(wx * FP) / FP
persist_wy = round(wy * FP) / FP
```

## Draw-Order Tie Breakers (Stable and Deterministic)
Every renderable object is sorted by the following tuple:
1. `floor_order` (tower floor order).
2. `render_layer` (`ground` < `gameplay` < `ambient` < `foreground`).
3. `sort_y_fp = floor((pivot_wy + layer_bias_y) * FP)`.
4. `sort_x_fp = floor((pivot_wx + layer_bias_x) * FP)`.
5. `stable_id` (monotonic object/entity ID).

This tuple is authoritative for both runtime and editor viewport rendering.

## Collision Sampling Rules
- Collision checks sample by world position -> owning tile via the floor rule above.
- Layer filtering is mandatory:
  - ground actor checks collision-enabled assets on gameplay/collision layers.
  - flying actor checks only layers flagged for flying collision.
- Collision templates are authored per asset and reused across levels; runtime uses the resolved asset template, not ad hoc per-instance defaults.

## Editor Picking Rules
Editor picking uses inverse transform to world position, then deterministic ownership:
1. Convert viewport position -> world `(wx, wy)` using inverse transform.
2. Resolve `(tile_x, tile_y)` using floor ownership rule.
3. Apply active-edit-layer filter for place/erase operations.
4. For stacked hits in same tile/layer, pick highest draw-order tuple; if equal, pick lowest `stable_id`.

## Compatibility Requirement
Any subsystem introducing its own transform, rounding, or sort semantics is non-compliant.
All modules must import/use one shared isometric math implementation that matches this spec exactly.
