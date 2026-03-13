from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.models.character import Character
from app.models.gameplay import GameplayActionAudit
from app.models.session import UserSession
from app.schemas.gameplay import (
    ResolveActionRequest,
    ResolveActionResponse,
    VerticalSliceLoopRequest,
    VerticalSliceLoopResponse,
    WorldSyncRequest,
    WorldSyncResponse,
)
from app.services.gameplay_authority import movement_sanity_ok, resolve_combat_and_rewards
from app.services.observability import record_world_sync_result
from app.services.security_events import write_security_event
from app.services.world_service_control import (
    WorldServiceControlError,
    advance_ticks,
    dispatch_control_command,
    fetch_battle_state,
    fetch_world_sync_snapshot,
)

router = APIRouter(prefix="/gameplay", tags=["gameplay"])
_WORLD_SYNC_START_MONOTONIC = perf_counter()
_WORLD_SYNC_TICK_INTERVAL_MS = 200
_WORLD_SYNC_STALE_AFTER_MS = 5_000


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


def _winner_side_from_battle_state(
    state_payload: dict, instance_id: int, attacker_army_id: int, defender_army_id: int
) -> str | None:
    state = state_payload.get("state", {})
    if not isinstance(state, dict):
        return None
    recent_results = state.get("recent_results", [])
    if not isinstance(recent_results, list):
        return None

    for row in recent_results:
        if not isinstance(row, dict):
            continue
        if int(row.get("instance_id", -1)) != instance_id:
            continue
        winner_army = int(row.get("winner_army", 0))
        if winner_army == attacker_army_id:
            return "attacker"
        if winner_army == defender_army_id:
            return "defender"
        return "unknown"
    return None


def _instance_status_from_battle_state(state_payload: dict, instance_id: int) -> str:
    state = state_payload.get("state", {})
    if not isinstance(state, dict):
        return "unknown"
    instances = state.get("instances", [])
    if not isinstance(instances, list):
        return "unknown"
    for row in instances:
        if not isinstance(row, dict):
            continue
        if int(row.get("instance_id", -1)) != instance_id:
            continue
        return str(row.get("status", "unknown")).strip().lower() or "unknown"
    return "resolved"


def _world_sync_now_ms() -> int:
    return max(0, int((perf_counter() - _WORLD_SYNC_START_MONOTONIC) * 1000.0))


@router.post("/vertical-slice-loop", response_model=VerticalSliceLoopResponse)
def run_vertical_slice_loop(
    payload: VerticalSliceLoopRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, payload.character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    now_ms = int(datetime.now(UTC).timestamp() * 1000)
    instance_id = int(f"{character.id}{now_ms % 1_000_000}") % 2_147_000_000
    encounter_id = instance_id + 11
    command_trace_prefix = f"vs-{context.session.id}-{character.id}-{now_ms}"

    commands = [
        {
            "type": "issue_move_army",
            "army_id": payload.attacker_army_id,
            "origin": payload.campaign_origin_settlement_id,
            "destination": payload.campaign_destination_settlement_id,
        },
        {
            "type": "start_battle_encounter",
            "instance_id": instance_id,
            "encounter_id": encounter_id,
            "location": payload.campaign_destination_settlement_id,
            "attacker_army": payload.attacker_army_id,
            "defender_army": payload.defender_army_id,
            "attacker_strength": payload.attacker_strength,
            "defender_strength": payload.defender_strength,
        },
        {
            "type": "set_battle_formation",
            "instance_id": instance_id,
            "side": "attacker",
            "formation": "wedge",
        },
        {
            "type": "deploy_battle_reserve",
            "instance_id": instance_id,
            "side": "attacker",
            "reserve_strength": max(50, payload.attacker_strength // 5),
        },
        {
            "type": "force_resolve_battle_instance",
            "instance_id": instance_id,
        },
    ]

    try:
        for index, command in enumerate(commands):
            dispatch_control_command(
                trace_id=f"{command_trace_prefix}-{index}",
                command=command,
            )
        tick_payload = advance_ticks(now_ms=payload.tick_now_ms)
        battle_payload = fetch_battle_state()
    except WorldServiceControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "world-service control call failed",
                "code": "world_service_unavailable",
                "reason": str(exc),
            },
        ) from exc

    winner_side = _winner_side_from_battle_state(
        battle_payload,
        instance_id,
        payload.attacker_army_id,
        payload.defender_army_id,
    )
    battle_status = _instance_status_from_battle_state(battle_payload, instance_id)
    xp_granted = payload.reward_xp + (20 if winner_side == "attacker" else 8)
    levels_gained, _remaining = _apply_progression(character, xp_granted)

    character.location_x = payload.campaign_destination_settlement_id
    character.location_y = payload.campaign_destination_settlement_id
    db.add(character)
    context.session.current_location_x = character.location_x
    context.session.current_location_y = character.location_y
    context.session.current_character_id = character.id
    db.add(context.session)
    _audit_action(
        db,
        context=context,
        character_id=character.id,
        nonce=f"vertical-slice-{instance_id}-{now_ms}",
        action_type="vertical_slice_loop",
        accepted=True,
        reason_code="battle_writeback_persisted",
    )
    db.commit()
    db.refresh(character)

    return VerticalSliceLoopResponse(
        accepted=True,
        reason_code="battle_writeback_persisted",
        battle_instance_id=instance_id,
        battle_status=battle_status,
        winner_side=winner_side,
        world_commands_queued=len(commands),
        campaign_tick=int(tick_payload.get("current_tick", 0)),
        xp_granted=xp_granted,
        levels_gained=levels_gained,
        character_level=character.level,
        character_experience=character.experience,
        persisted_location_x=int(character.location_x or 0),
        persisted_location_y=int(character.location_y or 0),
    )


@router.post("/world-sync", response_model=WorldSyncResponse)
def world_sync(
    payload: WorldSyncRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, payload.character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    now_ms = _world_sync_now_ms()
    started = perf_counter()
    include_map = bool(payload.include_map or payload.last_applied_tick <= 0)
    try:
        snapshot = fetch_world_sync_snapshot(now_ms=now_ms, include_travel_map=include_map)
    except WorldServiceControlError as exc:
        record_world_sync_result(success=False)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "world-service sync call failed",
                "code": "world_sync_unavailable",
                "reason": str(exc),
            },
        ) from exc

    latency_ms = (perf_counter() - started) * 1000.0
    record_world_sync_result(success=True, latency_ms=latency_ms)

    tick_payload = snapshot.get("tick", {})
    campaign_tick = int(tick_payload.get("current_tick", payload.last_applied_tick))
    metrics_payload = snapshot.get("metrics", {})
    tick_interval_ms = int(metrics_payload.get("tick_interval_ms", _WORLD_SYNC_TICK_INTERVAL_MS))
    if tick_interval_ms <= 0:
        tick_interval_ms = _WORLD_SYNC_TICK_INTERVAL_MS
    stale_after_ms = max(_WORLD_SYNC_STALE_AFTER_MS, tick_interval_ms * 4)

    warnings: list[str] = []
    if payload.last_applied_tick > campaign_tick:
        warnings.append("campaign_tick_regressed")

    return WorldSyncResponse(
        accepted=True,
        reason_code="world_sync_snapshot",
        character_id=character.id,
        server_unix_ms=int(datetime.now(UTC).timestamp() * 1000),
        campaign_tick=campaign_tick,
        tick_interval_ms=tick_interval_ms,
        stale_after_ms=stale_after_ms,
        sync_cursor=f"{character.id}:{campaign_tick}:{now_ms}",
        world={
            "travel_map": snapshot.get("travel_map", {}),
            "logistics": snapshot.get("logistics", {}),
            "trade": snapshot.get("trade", {}),
            "espionage": snapshot.get("espionage", {}),
            "politics": snapshot.get("politics", {}),
            "battle": snapshot.get("battle", {}),
            "metrics": snapshot.get("metrics", {}),
        },
        warnings=warnings,
    )
