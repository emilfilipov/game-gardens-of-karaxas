from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_admin_context
from app.models.character import Character
from app.models.level import Level
from app.schemas.character import (
    CharacterCreateRequest,
    CharacterLevelAssignRequest,
    CharacterLocationUpdateRequest,
    CharacterResponse,
)
from app.services.content import (
    CONTENT_DOMAIN_CHARACTER_OPTIONS,
    CONTENT_DOMAIN_PROGRESSION,
    CONTENT_DOMAIN_SKILLS,
    CONTENT_DOMAIN_STATS,
    get_active_snapshot,
)

router = APIRouter(prefix="/characters", tags=["characters"])


def _xp_per_level(db: Session) -> int:
    snapshot = get_active_snapshot(db)
    progression = snapshot.domain(CONTENT_DOMAIN_PROGRESSION)
    value = progression.get("xp_per_level")
    if isinstance(value, int) and value > 0:
        return value
    return 100


def _point_budget(db: Session) -> int:
    snapshot = get_active_snapshot(db)
    options = snapshot.domain(CONTENT_DOMAIN_CHARACTER_OPTIONS)
    value = options.get("point_budget")
    if isinstance(value, int) and value > 0:
        return value
    return 10


def _allowed_stat_keys(db: Session) -> set[str]:
    snapshot = get_active_snapshot(db)
    stats = snapshot.domain(CONTENT_DOMAIN_STATS)
    entries = stats.get("entries")
    if not isinstance(entries, list):
        return set()
    return {
        str(entry.get("key", "")).strip().lower()
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("key", "")).strip()
    }


def _allowed_skill_keys(db: Session) -> set[str]:
    snapshot = get_active_snapshot(db)
    skills = snapshot.domain(CONTENT_DOMAIN_SKILLS)
    entries = skills.get("entries")
    if not isinstance(entries, list):
        return set()
    return {
        str(entry.get("key", "")).strip().lower()
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("key", "")).strip()
    }


def _stat_max_value(db: Session) -> int:
    snapshot = get_active_snapshot(db)
    stats = snapshot.domain(CONTENT_DOMAIN_STATS)
    value = stats.get("max_per_stat")
    if isinstance(value, int) and value >= 0:
        return value
    return 10


def _normalize_catalog_choice(db: Session, catalog_key: str, raw_value: str, fallback: str) -> str:
    snapshot = get_active_snapshot(db)
    options = snapshot.domain(CONTENT_DOMAIN_CHARACTER_OPTIONS).get(catalog_key)
    if not isinstance(options, list):
        return fallback
    normalized = raw_value.strip()
    if not normalized:
        normalized = fallback
    for entry in options:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("value", "")).strip()
        label = str(entry.get("label", "")).strip()
        if normalized.lower() in {value.lower(), label.lower()}:
            return label or value or fallback
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"message": f"Invalid {catalog_key} option '{raw_value}'", "code": "invalid_option_choice"},
    )


def _to_response(character: Character, xp_per_level: int) -> CharacterResponse:
    band = xp_per_level if xp_per_level > 0 else 100
    current_band_progress = character.experience % band
    return CharacterResponse(
        id=character.id,
        name=character.name,
        level_id=character.level_id,
        location_x=character.location_x,
        location_y=character.location_y,
        appearance_key=character.appearance_key,
        race=character.race,
        background=character.background,
        affiliation=character.affiliation,
        level=character.level,
        experience=character.experience,
        experience_to_next_level=band - current_band_progress if current_band_progress > 0 else band,
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
    xp_per_level = _xp_per_level(db)
    rows = db.execute(
        select(Character).where(Character.user_id == context.user.id).order_by(Character.created_at.asc())
    ).scalars()
    return [_to_response(row, xp_per_level=xp_per_level) for row in rows]


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

    configured_budget = _point_budget(db)
    allowed_stats = _allowed_stat_keys(db)
    allowed_skills = _allowed_skill_keys(db)
    max_per_stat = _stat_max_value(db)

    normalized_stats: dict[str, int] = {}
    for key, value in payload.stats.items():
        normalized_key = key.strip().lower()
        if normalized_key not in allowed_stats:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Unknown stat key '{key}'", "code": "invalid_stat_key"},
            )
        if not isinstance(value, int) or value < 0 or value > max_per_stat:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Stat '{key}' must be between 0 and {max_per_stat}", "code": "invalid_stat_value"},
            )
        normalized_stats[normalized_key] = value

    normalized_skills: dict[str, int] = {}
    for key, value in payload.skills.items():
        normalized_key = key.strip().lower()
        if normalized_key not in allowed_skills:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Unknown skill key '{key}'", "code": "invalid_skill_key"},
            )
        if not isinstance(value, int) or value < 0 or value > 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Skill '{key}' must be 0 or 1", "code": "invalid_skill_value"},
            )
        normalized_skills[normalized_key] = value

    stat_points_used = sum(v for v in normalized_stats.values() if v > 0) + sum(v for v in normalized_skills.values() if v > 0)
    if stat_points_used > configured_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Allocated points exceed total", "code": "invalid_point_budget"},
        )

    character = Character(
        user_id=context.user.id,
        name=normalized_name,
        appearance_key=payload.appearance_key.strip(),
        race=_normalize_catalog_choice(db, "race", payload.race, "Human"),
        background=_normalize_catalog_choice(db, "background", payload.background, "Drifter"),
        affiliation=_normalize_catalog_choice(db, "affiliation", payload.affiliation, "Unaffiliated"),
        stat_points_total=configured_budget,
        stat_points_used=stat_points_used,
        level=1,
        experience=0,
        stats=normalized_stats,
        skills=normalized_skills,
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
    return _to_response(character, xp_per_level=_xp_per_level(db))


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
    character.location_x = None
    character.location_y = None
    db.add(character)
    db.commit()
    return {"ok": True, "character_id": character.id, "level_id": character.level_id}


@router.post("/{character_id}/location")
def update_character_location(
    character_id: int,
    payload: CharacterLocationUpdateRequest,
    context: AuthContext = Depends(get_auth_context),
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
    character.location_x = payload.location_x
    character.location_y = payload.location_y
    db.add(character)
    db.commit()
    return {
        "ok": True,
        "character_id": character.id,
        "level_id": character.level_id,
        "location_x": character.location_x,
        "location_y": character.location_y,
    }
