from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.models.character import Character
from app.models.gameplay import GameplayActionAudit
from app.models.session import UserSession
from app.schemas.gameplay import ResolveActionRequest, ResolveActionResponse
from app.services.gameplay_authority import movement_sanity_ok, resolve_combat_and_rewards
from app.services.security_events import write_security_event

router = APIRouter(prefix="/gameplay", tags=["gameplay"])


def _xp_to_levelup() -> int:
    return 100


def _apply_progression(character: Character, xp_granted: int) -> tuple[int, int]:
    if xp_granted <= 0:
        return 0, character.experience
    xp_to_level = _xp_to_levelup()
    levels_gained = 0
    character.experience += xp_granted
    while character.experience >= xp_to_level:
        character.experience -= xp_to_level
        character.level += 1
        levels_gained += 1
    return levels_gained, character.experience


def _audit_action(
    db: Session,
    *,
    context: AuthContext,
    character_id: int,
    nonce: str,
    action_type: str,
    accepted: bool,
    reason_code: str,
) -> None:
    db.add(
        GameplayActionAudit(
            session_id=context.session.id,
            user_id=context.user.id,
            character_id=character_id,
            action_nonce=nonce,
            action_type=action_type,
            accepted=accepted,
            reason_code=reason_code,
        )
    )


@router.post("/resolve-action", response_model=ResolveActionResponse)
def resolve_action(
    payload: ResolveActionRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, payload.character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    movement_ok = movement_sanity_ok(
        previous_x=context.session.current_location_x,
        previous_y=context.session.current_location_y,
        reported_x=payload.reported_x,
        reported_y=payload.reported_y,
        delta_seconds=payload.delta_seconds,
    )
    if not movement_ok:
        _audit_action(
            db,
            context=context,
            character_id=character.id,
            nonce=payload.action_nonce,
            action_type=payload.action_type,
            accepted=False,
            reason_code="movement_sanity_failed",
        )
        write_security_event(
            db,
            event_type="gameplay_movement_sanity_failed",
            severity="warning",
            actor_user_id=context.user.id,
            session_id=context.session.id,
            detail={
                "character_id": character.id,
                "reported_x": payload.reported_x,
                "reported_y": payload.reported_y,
                "previous_x": context.session.current_location_x,
                "previous_y": context.session.current_location_y,
            },
        )
        db.commit()
        return ResolveActionResponse(
            accepted=False,
            reason_code="movement_sanity_failed",
            server_damage=0.0,
            xp_granted=0,
            levels_gained=0,
            loot_granted=[],
            server_position_x=int(context.session.current_location_x or payload.reported_x),
            server_position_y=int(context.session.current_location_y or payload.reported_y),
            character_level=character.level,
            character_experience=character.experience,
        )

    latest = db.execute(
        select(GameplayActionAudit)
        .where(GameplayActionAudit.session_id == context.session.id)
        .order_by(desc(GameplayActionAudit.id))
        .limit(1)
    ).scalar_one_or_none()
    if latest is not None:
        elapsed = (datetime.now(UTC) - latest.created_at).total_seconds()
        if elapsed < 0.05:
            _audit_action(
                db,
                context=context,
                character_id=character.id,
                nonce=payload.action_nonce,
                action_type=payload.action_type,
                accepted=False,
                reason_code="action_rate_limited",
            )
            write_security_event(
                db,
                event_type="gameplay_action_rate_limited",
                severity="warning",
                actor_user_id=context.user.id,
                session_id=context.session.id,
                detail={"character_id": character.id, "elapsed_seconds": elapsed},
            )
            db.commit()
            return ResolveActionResponse(
                accepted=False,
                reason_code="action_rate_limited",
                server_damage=0.0,
                xp_granted=0,
                levels_gained=0,
                loot_granted=[],
                server_position_x=int(context.session.current_location_x or payload.reported_x),
                server_position_y=int(context.session.current_location_y or payload.reported_y),
                character_level=character.level,
                character_experience=character.experience,
            )

    resolution = resolve_combat_and_rewards(
        action_type=payload.action_type.strip().lower(),
        skill_key=payload.skill_key.strip().lower() if payload.skill_key else None,
        character_stats=character.stats if isinstance(character.stats, dict) else {},
        enemies_defeated=payload.enemies_defeated,
        requested_loot_tier=payload.requested_loot_tier,
    )
    levels_gained, _remaining_xp = _apply_progression(character, resolution.xp_granted)
    inventory = character.inventory if isinstance(character.inventory, list) else []
    if resolution.loot_granted:
        inventory.extend(resolution.loot_granted)
        character.inventory = inventory
    character.location_x = payload.reported_x
    character.location_y = payload.reported_y
    db.add(character)
    context.session.current_location_x = payload.reported_x
    context.session.current_location_y = payload.reported_y
    context.session.current_character_id = character.id
    db.add(context.session)
    _audit_action(
        db,
        context=context,
        character_id=character.id,
        nonce=payload.action_nonce,
        action_type=payload.action_type,
        accepted=resolution.accepted,
        reason_code=resolution.reason_code,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "uq_gameplay_action_session_nonce" not in str(exc):
            raise
        return ResolveActionResponse(
            accepted=False,
            reason_code="action_nonce_reused",
            server_damage=0.0,
            xp_granted=0,
            levels_gained=0,
            loot_granted=[],
            server_position_x=int(context.session.current_location_x or payload.reported_x),
            server_position_y=int(context.session.current_location_y or payload.reported_y),
            character_level=character.level,
            character_experience=character.experience,
        )
    db.refresh(character)
    return ResolveActionResponse(
        accepted=resolution.accepted,
        reason_code=resolution.reason_code,
        server_damage=resolution.server_damage,
        xp_granted=resolution.xp_granted,
        levels_gained=levels_gained,
        loot_granted=resolution.loot_granted,
        server_position_x=payload.reported_x,
        server_position_y=payload.reported_y,
        character_level=character.level,
        character_experience=character.experience,
    )
