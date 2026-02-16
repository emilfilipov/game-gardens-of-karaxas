from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_admin_context
from app.models.character import Character
from app.models.level import Level
from app.schemas.character import CharacterCreateRequest, CharacterLevelAssignRequest, CharacterResponse

router = APIRouter(prefix="/characters", tags=["characters"])
XP_PER_LEVEL = 100


def _to_response(character: Character) -> CharacterResponse:
    current_band_progress = character.experience % XP_PER_LEVEL
    return CharacterResponse(
        id=character.id,
        name=character.name,
        level_id=character.level_id,
        appearance_key=character.appearance_key,
        level=character.level,
        experience=character.experience,
        experience_to_next_level=XP_PER_LEVEL - current_band_progress if current_band_progress > 0 else XP_PER_LEVEL,
        stat_points_total=character.stat_points_total,
        stat_points_used=character.stat_points_used,
        stats=character.stats,
        skills=character.skills,
        is_selected=character.is_selected,
        created_at=character.created_at,
        updated_at=character.updated_at,
    )


@router.get("", response_model=list[CharacterResponse])
def list_characters(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Character).where(Character.user_id == context.user.id).order_by(Character.created_at.asc())
    ).scalars()
    return [_to_response(row) for row in rows]


@router.post("", response_model=CharacterResponse)
def create_character(
    payload: CharacterCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    normalized_name = payload.name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Character name is required", "code": "invalid_character_name"},
        )
    existing = db.execute(select(Character.id).where(func.lower(Character.name) == normalized_name.lower())).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Character name already exists", "code": "character_name_taken"},
        )

    stat_points_used = sum(v for v in payload.stats.values() if isinstance(v, int) and v > 0) + sum(
        v for v in payload.skills.values() if isinstance(v, int) and v > 0
    )
    if stat_points_used > payload.stat_points_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Allocated points exceed total", "code": "invalid_point_budget"},
        )

    character = Character(
        user_id=context.user.id,
        name=normalized_name,
        appearance_key=payload.appearance_key.strip(),
        stat_points_total=payload.stat_points_total,
        stat_points_used=stat_points_used,
        level=1,
        experience=0,
        stats=payload.stats,
        skills=payload.skills,
        is_selected=False,
    )
    db.add(character)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Character name already exists", "code": "character_name_taken"},
        ) from None
    db.refresh(character)
    return _to_response(character)


@router.post("/{character_id}/select")
def select_character(character_id: int, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    rows = db.execute(select(Character).where(Character.user_id == context.user.id)).scalars().all()
    for row in rows:
        row.is_selected = row.id == character_id
        db.add(row)
    db.commit()
    return {"ok": True, "character_id": character_id}


@router.delete("/{character_id}")
def delete_character(character_id: int, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )
    was_selected = character.is_selected
    db.delete(character)
    db.commit()
    return {"ok": True, "character_id": character_id, "selection_cleared": was_selected}


@router.post("/{character_id}/level")
def assign_character_level(
    character_id: int,
    payload: CharacterLevelAssignRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    level_id = payload.level_id
    if level_id is not None:
        level = db.get(Level, level_id)
        if level is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Level not found", "code": "level_not_found"},
            )

    character.level_id = level_id
    db.add(character)
    db.commit()
    return {"ok": True, "character_id": character.id, "level_id": character.level_id}
