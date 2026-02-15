from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.models.character import Character
from app.schemas.character import CharacterCreateRequest, CharacterResponse

router = APIRouter(prefix="/characters", tags=["characters"])


def _to_response(character: Character) -> CharacterResponse:
    return CharacterResponse(
        id=character.id,
        name=character.name,
        appearance_key=character.appearance_key,
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
        name=payload.name.strip(),
        appearance_key=payload.appearance_key.strip(),
        stat_points_total=payload.stat_points_total,
        stat_points_used=stat_points_used,
        stats=payload.stats,
        skills=payload.skills,
        is_selected=False,
    )
    db.add(character)
    db.commit()
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
