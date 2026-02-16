from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_admin_context
from app.models.level import Level
from app.schemas.level import LevelGridPoint, LevelResponse, LevelSaveRequest, LevelSummaryResponse

router = APIRouter(prefix="/levels", tags=["levels"])


def _to_summary(level: Level) -> LevelSummaryResponse:
    return LevelSummaryResponse(
        id=level.id,
        name=level.name,
        width=level.width,
        height=level.height,
    )


def _to_response(level: Level) -> LevelResponse:
    return LevelResponse(
        id=level.id,
        name=level.name,
        width=level.width,
        height=level.height,
        spawn_x=level.spawn_x,
        spawn_y=level.spawn_y,
        wall_cells=[LevelGridPoint(x=int(cell.get("x", 0)), y=int(cell.get("y", 0))) for cell in level.wall_cells or []],
        created_by_user_id=level.created_by_user_id,
        created_at=level.created_at,
        updated_at=level.updated_at,
    )


def _normalize_wall_cells(payload: LevelSaveRequest) -> list[dict]:
    seen: set[tuple[int, int]] = set()
    normalized: list[dict] = []
    for cell in payload.wall_cells:
        x = int(cell.x)
        y = int(cell.y)
        if x >= payload.width or y >= payload.height:
            continue
        key = (x, y)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"x": x, "y": y})
    return normalized


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

    wall_cells = _normalize_wall_cells(payload)
    existing = db.execute(select(Level).where(func.lower(Level.name) == normalized_name.lower())).scalar_one_or_none()
    if existing is None:
        level = Level(
            name=normalized_name,
            width=payload.width,
            height=payload.height,
            spawn_x=payload.spawn_x,
            spawn_y=payload.spawn_y,
            wall_cells=wall_cells,
            created_by_user_id=context.user.id,
        )
        db.add(level)
    else:
        existing.name = normalized_name
        existing.width = payload.width
        existing.height = payload.height
        existing.spawn_x = payload.spawn_x
        existing.spawn_y = payload.spawn_y
        existing.wall_cells = wall_cells
        existing.created_by_user_id = context.user.id
        db.add(existing)
        level = existing
    db.commit()
    db.refresh(level)
    return _to_response(level)
