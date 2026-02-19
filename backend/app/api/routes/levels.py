from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_admin_context
from app.models.level import Level
from app.schemas.level import (
    LevelGridPoint,
    LevelLayerCell,
    LevelOrderSaveRequest,
    LevelResponse,
    LevelSaveRequest,
    LevelSummaryResponse,
    LevelTransition,
)

router = APIRouter(prefix="/levels", tags=["levels"])

SCHEMA_VERSION_LAYERED = 2
LAYER_ID_MIN = 0
LAYER_ID_MAX = 32
DEFAULT_LAYER_BY_ASSET = {
    "grass_tile": 0,
    "wall_block": 1,
    "tree_oak": 1,
    "stairs_passage": 1,
    "ladder_passage": 1,
    "elevator_platform": 1,
    "cloud_soft": 2,
}
COLLISION_LAYER_IDS = {1}
COLLISION_ASSET_KEYS = {"wall_block", "tree_oak"}
TRANSITION_ASSET_KEYS = {
    "stairs_passage": "stairs",
    "ladder_passage": "ladder",
    "elevator_platform": "elevator",
}
SUPPORTED_TRANSITION_TYPES = {"stairs", "ladder", "elevator"}


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


def _parse_stored_transitions(level: Level) -> list[dict]:
    raw = level.transitions if isinstance(level.transitions, list) else []
    parsed: list[dict] = []
    seen: set[tuple[int, int, str, int]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            x = int(item.get("x", 0))
            y = int(item.get("y", 0))
            destination_level_id = int(item.get("destination_level_id", 0))
        except (TypeError, ValueError):
            continue
        transition_type = str(item.get("transition_type", "")).strip().lower()
        if (
            transition_type not in SUPPORTED_TRANSITION_TYPES
            or destination_level_id <= 0
            or x < 0
            or y < 0
            or x >= level.width
            or y >= level.height
        ):
            continue
        dedupe_key = (x, y, transition_type, destination_level_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        parsed.append(
            {
                "x": x,
                "y": y,
                "transition_type": transition_type,
                "destination_level_id": destination_level_id,
            }
        )
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
            if asset_key in TRANSITION_ASSET_KEYS and layer_id != 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": f"Asset '{asset_key}' must be placed on layer 1",
                        "code": "invalid_transition_layer",
                    },
                )

            dedupe_key = (x, y, asset_key)
            if dedupe_key in seen[layer_id]:
                continue
            seen[layer_id].add(dedupe_key)
            layer_entries.append({"x": x, "y": y, "asset_key": asset_key})

        normalized[layer_id] = layer_entries
    return normalized


def _normalize_transitions_from_payload(payload: LevelSaveRequest, db: Session) -> list[dict]:
    normalized: list[dict] = []
    seen: set[tuple[int, int, str, int]] = set()
    for transition in payload.transitions:
        x = int(transition.x)
        y = int(transition.y)
        if x >= payload.width or y >= payload.height:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Transition cell must be inside level bounds", "code": "invalid_transition_cell"},
            )
        transition_type = transition.transition_type.strip().lower()
        if transition_type not in SUPPORTED_TRANSITION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Unsupported transition type '{transition.transition_type}'", "code": "invalid_transition_type"},
            )
        destination_level_id = int(transition.destination_level_id)
        if db.get(Level, destination_level_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": f"Destination level {destination_level_id} was not found",
                    "code": "transition_destination_not_found",
                },
            )
        dedupe_key = (x, y, transition_type, destination_level_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(
            {
                "x": x,
                "y": y,
                "transition_type": transition_type,
                "destination_level_id": destination_level_id,
            }
        )
    return normalized


def _assign_transition_assets(layer_cells: dict[int, list[dict]], transitions: list[dict]) -> dict[int, list[dict]]:
    updated: dict[int, list[dict]] = {
        layer_id: [dict(cell) for cell in cells]
        for layer_id, cells in layer_cells.items()
    }
    layer = updated.setdefault(1, [])
    by_cell = {(int(cell.get("x", 0)), int(cell.get("y", 0))): idx for idx, cell in enumerate(layer)}
    for transition in transitions:
        x = int(transition["x"])
        y = int(transition["y"])
        transition_type = str(transition["transition_type"]).lower()
        asset_key = next((key for key, value in TRANSITION_ASSET_KEYS.items() if value == transition_type), None)
        if asset_key is None:
            continue
        existing_index = by_cell.get((x, y))
        if existing_index is not None:
            layer[existing_index]["asset_key"] = asset_key
        else:
            by_cell[(x, y)] = len(layer)
            layer.append({"x": x, "y": y, "asset_key": asset_key})
    return updated


def _to_summary(level: Level) -> LevelSummaryResponse:
    return LevelSummaryResponse(
        id=level.id,
        name=level.name,
        descriptive_name=level.descriptive_name or level.name,
        order_index=level.order_index,
        schema_version=max(int(level.schema_version or 1), SCHEMA_VERSION_LAYERED),
        width=level.width,
        height=level.height,
    )


def _to_response(level: Level) -> LevelResponse:
    transitions = _parse_stored_transitions(level)
    layer_cells = _assign_transition_assets(_parse_stored_layers(level), transitions)
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
        descriptive_name=level.descriptive_name or level.name,
        order_index=level.order_index,
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
        transitions=[
            LevelTransition(
                x=int(item["x"]),
                y=int(item["y"]),
                transition_type=str(item["transition_type"]),
                destination_level_id=int(item["destination_level_id"]),
            )
            for item in transitions
        ],
        wall_cells=[LevelGridPoint(x=int(cell.get("x", 0)), y=int(cell.get("y", 0))) for cell in wall_cells],
        created_by_user_id=level.created_by_user_id,
        created_at=level.created_at,
        updated_at=level.updated_at,
    )


@router.get("", response_model=list[LevelSummaryResponse])
def list_levels(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    rows = db.execute(select(Level).order_by(Level.order_index.asc(), Level.id.asc())).scalars()
    return [_to_summary(row) for row in rows]


@router.get("/first", response_model=LevelResponse)
def get_first_level(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    first_level = db.execute(select(Level).order_by(Level.order_index.asc(), Level.id.asc()).limit(1)).scalar_one_or_none()
    if first_level is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No levels found", "code": "level_not_found"},
        )
    return _to_response(first_level)


@router.post("/order")
def save_level_order(
    payload: LevelOrderSaveRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    levels = db.execute(select(Level).order_by(Level.order_index.asc(), Level.id.asc())).scalars().all()
    by_id = {level.id: level for level in levels}

    seen_ids: set[int] = set()
    ordered_ids: list[int] = []
    for entry in payload.levels:
        if entry.level_id in seen_ids:
            continue
        level = by_id.get(entry.level_id)
        if level is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Level {entry.level_id} not found", "code": "level_not_found"},
            )
        seen_ids.add(entry.level_id)
        ordered_ids.append(entry.level_id)

    for level in levels:
        if level.id not in seen_ids:
            ordered_ids.append(level.id)

    for index, level_id in enumerate(ordered_ids, start=1):
        level = by_id[level_id]
        level.order_index = index
        db.add(level)

    db.commit()
    return {"ok": True, "updated": len(ordered_ids)}


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
    normalized_descriptive_name = payload.descriptive_name.strip() or normalized_name
    if payload.spawn_x >= payload.width or payload.spawn_y >= payload.height:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Spawn point must be inside the level bounds", "code": "invalid_spawn"},
        )

    layer_cells = _normalize_layers_from_payload(payload)
    transitions = _normalize_transitions_from_payload(payload, db)
    layer_cells = _assign_transition_assets(layer_cells, transitions)
    wall_cells = _derive_wall_cells(
        layer_cells,
        width=payload.width,
        height=payload.height,
        spawn_x=payload.spawn_x,
        spawn_y=payload.spawn_y,
    )
    layer_cells_for_storage = {str(layer_id): cells for layer_id, cells in layer_cells.items()}
    existing = db.execute(select(Level).where(func.lower(Level.name) == normalized_name.lower())).scalar_one_or_none()
    requested_order = payload.order_index
    max_order = db.execute(select(func.max(Level.order_index))).scalar_one_or_none() or 0
    if existing is None:
        order_index = requested_order if requested_order is not None else max_order + 1
        level = Level(
            name=normalized_name,
            descriptive_name=normalized_descriptive_name,
            order_index=order_index,
            schema_version=SCHEMA_VERSION_LAYERED,
            width=payload.width,
            height=payload.height,
            spawn_x=payload.spawn_x,
            spawn_y=payload.spawn_y,
            wall_cells=wall_cells,
            layer_cells=layer_cells_for_storage,
            transitions=transitions,
            created_by_user_id=context.user.id,
        )
        db.add(level)
    else:
        existing.name = normalized_name
        existing.descriptive_name = normalized_descriptive_name
        if requested_order is not None:
            existing.order_index = requested_order
        existing.schema_version = SCHEMA_VERSION_LAYERED
        existing.width = payload.width
        existing.height = payload.height
        existing.spawn_x = payload.spawn_x
        existing.spawn_y = payload.spawn_y
        existing.wall_cells = wall_cells
        existing.layer_cells = layer_cells_for_storage
        existing.transitions = transitions
        existing.created_by_user_id = context.user.id
        db.add(existing)
        level = existing
    db.commit()
    db.refresh(level)
    return _to_response(level)
