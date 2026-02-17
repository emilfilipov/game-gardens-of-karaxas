from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_admin_context
from app.models.level import Level
from app.schemas.level import LevelGridPoint, LevelLayerCell, LevelResponse, LevelSaveRequest, LevelSummaryResponse

router = APIRouter(prefix="/levels", tags=["levels"])

SCHEMA_VERSION_LAYERED = 2
LAYER_ID_MIN = 0
LAYER_ID_MAX = 32
DEFAULT_LAYER_BY_ASSET = {
    "grass_tile": 0,
    "wall_block": 1,
    "tree_oak": 1,
    "cloud_soft": 2,
}
COLLISION_LAYER_IDS = {1}
COLLISION_ASSET_KEYS = {"wall_block", "tree_oak"}


def _legacy_layers_from_wall_cells(wall_cells: list[dict] | None) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    if not wall_cells:
        return result
    result[1] = [
        {
            "x": int(cell.get("x", 0)),
            "y": int(cell.get("y", 0)),
            "asset_key": "wall_block",
        }
        for cell in wall_cells
    ]
    return result


def _parse_stored_layers(level: Level) -> dict[int, list[dict]]:
    raw_layers = level.layer_cells if isinstance(level.layer_cells, dict) else {}
    if not raw_layers:
        return _legacy_layers_from_wall_cells(level.wall_cells)
    parsed: dict[int, list[dict]] = {}
    for layer_key, raw_cells in raw_layers.items():
        try:
            layer_id = int(layer_key)
        except (TypeError, ValueError):
            continue
        if layer_id < LAYER_ID_MIN or layer_id > LAYER_ID_MAX:
            continue
        if not isinstance(raw_cells, list):
            continue
        normalized_cells: list[dict] = []
        for raw_cell in raw_cells:
            if not isinstance(raw_cell, dict):
                continue
            x = int(raw_cell.get("x", 0))
            y = int(raw_cell.get("y", 0))
            asset_key = str(raw_cell.get("asset_key", "")).strip().lower()
            if not asset_key:
                asset_key = "wall_block" if layer_id == 1 else "decor"
            normalized_cells.append({"x": x, "y": y, "asset_key": asset_key})
        parsed[layer_id] = normalized_cells
    return parsed


def _derive_wall_cells(
    layer_cells: dict[int, list[dict]],
    width: int,
    height: int,
    spawn_x: int,
    spawn_y: int,
) -> list[dict]:
    seen: set[tuple[int, int]] = set()
    walls: list[dict] = []
    for layer_id in sorted(layer_cells.keys()):
        if layer_id not in COLLISION_LAYER_IDS:
            continue
        for cell in layer_cells[layer_id]:
            asset_key = str(cell.get("asset_key", "")).strip().lower()
            if asset_key not in COLLISION_ASSET_KEYS:
                continue
            x = int(cell.get("x", 0))
            y = int(cell.get("y", 0))
            if x < 0 or y < 0 or x >= width or y >= height:
                continue
            if x == spawn_x and y == spawn_y:
                continue
            key = (x, y)
            if key in seen:
                continue
            seen.add(key)
            walls.append({"x": x, "y": y})
    return walls


def _normalize_layers_from_payload(payload: LevelSaveRequest) -> dict[int, list[dict]]:
    source_layers: dict[int, list[LevelLayerCell]]
    if payload.layers:
        source_layers = payload.layers
    else:
        source_layers = {
            1: [LevelLayerCell(x=cell.x, y=cell.y, asset_key="wall_block") for cell in payload.wall_cells]
        }

    normalized: dict[int, list[dict]] = {}
    seen: dict[int, set[tuple[int, int, str]]] = {}
    for raw_layer_id, cells in source_layers.items():
        layer_id = int(raw_layer_id)
        if layer_id < LAYER_ID_MIN or layer_id > LAYER_ID_MAX:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": f"Layer {layer_id} is outside allowed range {LAYER_ID_MIN}-{LAYER_ID_MAX}",
                    "code": "invalid_layer_id",
                },
            )
        layer_entries: list[dict] = []
        seen.setdefault(layer_id, set())
        for cell in cells:
            x = int(cell.x)
            y = int(cell.y)
            if x >= payload.width or y >= payload.height:
                continue
            asset_key = cell.asset_key.strip().lower()
            if not asset_key:
                asset_key = "wall_block" if layer_id == 1 else "decor"

            expected_collision_layer = DEFAULT_LAYER_BY_ASSET.get(asset_key)
            if asset_key in COLLISION_ASSET_KEYS and expected_collision_layer not in COLLISION_LAYER_IDS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": f"Asset '{asset_key}' is not configured for collision layers",
                        "code": "invalid_collision_asset",
                    },
                )
            if asset_key in COLLISION_ASSET_KEYS and layer_id not in COLLISION_LAYER_IDS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": f"Asset '{asset_key}' must be placed on collision layer 1",
                        "code": "invalid_collision_layer",
                    },
                )

            dedupe_key = (x, y, asset_key)
            if dedupe_key in seen[layer_id]:
                continue
            seen[layer_id].add(dedupe_key)
            layer_entries.append({"x": x, "y": y, "asset_key": asset_key})

        normalized[layer_id] = layer_entries
    return normalized


def _to_summary(level: Level) -> LevelSummaryResponse:
    return LevelSummaryResponse(
        id=level.id,
        name=level.name,
        schema_version=max(int(level.schema_version or 1), SCHEMA_VERSION_LAYERED),
        width=level.width,
        height=level.height,
    )


def _to_response(level: Level) -> LevelResponse:
    layer_cells = _parse_stored_layers(level)
    wall_cells = _derive_wall_cells(
        layer_cells,
        width=level.width,
        height=level.height,
        spawn_x=level.spawn_x,
        spawn_y=level.spawn_y,
    )
    return LevelResponse(
        id=level.id,
        name=level.name,
        schema_version=max(int(level.schema_version or 1), SCHEMA_VERSION_LAYERED),
        width=level.width,
        height=level.height,
        spawn_x=level.spawn_x,
        spawn_y=level.spawn_y,
        layers={
            layer_id: [
                LevelLayerCell(
                    x=int(cell.get("x", 0)),
                    y=int(cell.get("y", 0)),
                    asset_key=str(cell.get("asset_key", "")).strip().lower() or "decor",
                )
                for cell in layer_cells[layer_id]
            ]
            for layer_id in sorted(layer_cells.keys())
        },
        wall_cells=[LevelGridPoint(x=int(cell.get("x", 0)), y=int(cell.get("y", 0))) for cell in wall_cells],
        created_by_user_id=level.created_by_user_id,
        created_at=level.created_at,
        updated_at=level.updated_at,
    )


@router.get("", response_model=list[LevelSummaryResponse])
def list_levels(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    rows = db.execute(select(Level).order_by(Level.name.asc(), Level.id.asc())).scalars()
    return [_to_summary(row) for row in rows]


@router.get("/{level_id}", response_model=LevelResponse)
def get_level(level_id: int, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    level = db.get(Level, level_id)
    if level is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Level not found", "code": "level_not_found"},
        )
    return _to_response(level)


@router.post("", response_model=LevelResponse)
def save_level(
    payload: LevelSaveRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    normalized_name = payload.name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Level name is required", "code": "invalid_level_name"},
        )
    if payload.spawn_x >= payload.width or payload.spawn_y >= payload.height:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Spawn point must be inside the level bounds", "code": "invalid_spawn"},
        )

    layer_cells = _normalize_layers_from_payload(payload)
    wall_cells = _derive_wall_cells(
        layer_cells,
        width=payload.width,
        height=payload.height,
        spawn_x=payload.spawn_x,
        spawn_y=payload.spawn_y,
    )
    layer_cells_for_storage = {str(layer_id): cells for layer_id, cells in layer_cells.items()}
    existing = db.execute(select(Level).where(func.lower(Level.name) == normalized_name.lower())).scalar_one_or_none()
    if existing is None:
        level = Level(
            name=normalized_name,
            schema_version=SCHEMA_VERSION_LAYERED,
            width=payload.width,
            height=payload.height,
            spawn_x=payload.spawn_x,
            spawn_y=payload.spawn_y,
            wall_cells=wall_cells,
            layer_cells=layer_cells_for_storage,
            created_by_user_id=context.user.id,
        )
        db.add(level)
    else:
        existing.name = normalized_name
        existing.schema_version = SCHEMA_VERSION_LAYERED
        existing.width = payload.width
        existing.height = payload.height
        existing.spawn_x = payload.spawn_x
        existing.spawn_y = payload.spawn_y
        existing.wall_cells = wall_cells
        existing.layer_cells = layer_cells_for_storage
        existing.created_by_user_id = context.user.id
        db.add(existing)
        level = existing
    db.commit()
    db.refresh(level)
    return _to_response(level)
