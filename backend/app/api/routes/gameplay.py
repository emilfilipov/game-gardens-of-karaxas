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
    BattleCommandRequest,
    BattleCommandResponse,
    BattleStartRequest,
    BattleStartResponse,
    DomainActionRequest,
    DomainActionResponse,
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


def _battle_action_command(payload: BattleCommandRequest) -> dict:
    action = payload.action_type.strip().lower()
    if action == "set_formation":
        side = (payload.side or "").strip().lower()
        formation = (payload.formation or "").strip().lower()
        if side not in {"attacker", "defender"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"message": "side must be attacker or defender", "code": "invalid_battle_side"},
            )
        if formation not in {"line", "wedge", "defensive"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"message": "formation must be line, wedge, or defensive", "code": "invalid_formation"},
            )
        return {
            "type": "set_battle_formation",
            "instance_id": payload.battle_instance_id,
            "side": side,
            "formation": formation,
        }
    if action == "deploy_reserve":
        side = (payload.side or "").strip().lower()
        if side not in {"attacker", "defender"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"message": "side must be attacker or defender", "code": "invalid_battle_side"},
            )
        if payload.reserve_strength is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"message": "reserve_strength is required", "code": "missing_reserve_strength"},
            )
        return {
            "type": "deploy_battle_reserve",
            "instance_id": payload.battle_instance_id,
            "side": side,
            "reserve_strength": int(payload.reserve_strength),
        }
    if action == "force_resolve":
        return {
            "type": "force_resolve_battle_instance",
            "instance_id": payload.battle_instance_id,
        }
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "message": "action_type must be set_formation, deploy_reserve, or force_resolve",
            "code": "invalid_battle_action_type",
        },
    )


def _payload_int(payload: dict, key: str, *, minimum: int = 0, maximum: int = 2_147_483_647) -> int:
    try:
        value = int(payload.get(key))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": f"{key} must be an integer", "code": "invalid_domain_action_payload"},
        ) from None
    if value < minimum or value > maximum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": f"{key} must be between {minimum} and {maximum}",
                "code": "invalid_domain_action_payload",
            },
        )
    return value


def _payload_bool(payload: dict, key: str) -> bool:
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"message": f"{key} must be a boolean", "code": "invalid_domain_action_payload"},
    )


def _domain_action_command(payload: DomainActionRequest) -> dict:
    action_type = payload.action_type.strip().lower()
    raw = payload.payload if isinstance(payload.payload, dict) else {}
    if action_type == "queue_supply_transfer":
        return {
            "type": "queue_supply_transfer",
            "from_army": _payload_int(raw, "from_army", minimum=1),
            "to_army": _payload_int(raw, "to_army", minimum=1),
            "food": _payload_int(raw, "food", minimum=0, maximum=100_000),
            "horses": _payload_int(raw, "horses", minimum=0, maximum=100_000),
            "materiel": _payload_int(raw, "materiel", minimum=0, maximum=100_000),
        }
    if action_type == "queue_trade_shipment":
        return {
            "type": "queue_trade_shipment",
            "origin_settlement": _payload_int(raw, "origin_settlement", minimum=1),
            "destination_settlement": _payload_int(raw, "destination_settlement", minimum=1),
            "food": _payload_int(raw, "food", minimum=0, maximum=100_000),
            "horses": _payload_int(raw, "horses", minimum=0, maximum=100_000),
            "materiel": _payload_int(raw, "materiel", minimum=0, maximum=100_000),
        }
    if action_type == "request_intel_report":
        return {
            "type": "request_intel_report",
            "informant_id": _payload_int(raw, "informant_id", minimum=1),
            "subject_settlement": _payload_int(raw, "subject_settlement", minimum=1),
        }
    if action_type == "set_treaty_status":
        treaty_kind = str(raw.get("treaty_kind", "")).strip().lower()
        if treaty_kind not in {"trade_pact", "non_aggression", "military_access"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "message": "treaty_kind must be trade_pact, non_aggression, or military_access",
                    "code": "invalid_domain_action_payload",
                },
            )
        return {
            "type": "set_treaty_status",
            "treaty_id": _payload_int(raw, "treaty_id", minimum=1),
            "faction_a": _payload_int(raw, "faction_a", minimum=1),
            "faction_b": _payload_int(raw, "faction_b", minimum=1),
            "treaty_kind": treaty_kind,
            "active": _payload_bool(raw, "active"),
            "trust_bp": _payload_int(raw, "trust_bp", minimum=0, maximum=10_000),
        }
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "message": "Unsupported action_type for domain action",
            "code": "invalid_domain_action_type",
        },
    )


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

    logistics_state = snapshot.get("logistics", {}).get("state", {}) if isinstance(snapshot.get("logistics"), dict) else {}
    trade_state = snapshot.get("trade", {}).get("state", {}) if isinstance(snapshot.get("trade"), dict) else {}
    espionage_state = snapshot.get("espionage", {}).get("state", {}) if isinstance(snapshot.get("espionage"), dict) else {}
    politics_state = snapshot.get("politics", {}).get("state", {}) if isinstance(snapshot.get("politics"), dict) else {}
    household_summary = {
        "active_armies": len(logistics_state.get("armies", [])) if isinstance(logistics_state, dict) else 0,
        "market_count": len(trade_state.get("markets", [])) if isinstance(trade_state, dict) else 0,
        "informant_count": len(espionage_state.get("informants", [])) if isinstance(espionage_state, dict) else 0,
        "treaty_count": len(politics_state.get("treaties", [])) if isinstance(politics_state, dict) else 0,
    }

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
            "character": {
                "id": character.id,
                "name": character.name,
                "level": character.level,
                "experience": character.experience,
                "location_x": int(character.location_x or 0),
                "location_y": int(character.location_y or 0),
            },
            "household": household_summary,
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


@router.post("/battle/start", response_model=BattleStartResponse)
def start_battle_instance(
    payload: BattleStartRequest,
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
    instance_id = int(f"{character.id}{now_ms % 1_000_000}") % 2_147_000_000
    encounter_id = instance_id + 17
    trace_id = f"battle-start-{context.session.id}-{character.id}-{now_ms}"
    command = {
        "type": "start_battle_encounter",
        "instance_id": instance_id,
        "encounter_id": encounter_id,
        "location": payload.location_settlement_id,
        "attacker_army": payload.attacker_army_id,
        "defender_army": payload.defender_army_id,
        "attacker_strength": payload.attacker_strength,
        "defender_strength": payload.defender_strength,
    }

    try:
        dispatch_control_command(trace_id=trace_id, command=command)
        tick_payload = advance_ticks(now_ms=now_ms)
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

    battle_status = _instance_status_from_battle_state(battle_payload, instance_id)
    return BattleStartResponse(
        accepted=True,
        reason_code="battle_instance_started",
        battle_instance_id=instance_id,
        encounter_id=encounter_id,
        battle_status=battle_status,
        campaign_tick=int(tick_payload.get("current_tick", 0)),
    )


@router.post("/battle/command", response_model=BattleCommandResponse)
def issue_battle_command(
    payload: BattleCommandRequest,
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
    command = _battle_action_command(payload)
    action = payload.action_type.strip().lower()
    trace_id = f"battle-action-{action}-{context.session.id}-{payload.battle_instance_id}-{now_ms}"

    try:
        dispatch_control_command(trace_id=trace_id, command=command)
        tick_payload = advance_ticks(now_ms=now_ms)
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

    battle_status = _instance_status_from_battle_state(battle_payload, payload.battle_instance_id)
    return BattleCommandResponse(
        accepted=True,
        reason_code="battle_command_dispatched",
        battle_instance_id=payload.battle_instance_id,
        battle_status=battle_status,
        campaign_tick=int(tick_payload.get("current_tick", 0)),
    )


@router.post("/domain-action", response_model=DomainActionResponse)
def issue_domain_action(
    payload: DomainActionRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, payload.character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    command = _domain_action_command(payload)
    now_ms = _world_sync_now_ms()
    trace_id = f"domain-action-{payload.action_type.strip().lower()}-{context.session.id}-{now_ms}"
    try:
        dispatch_control_command(trace_id=trace_id, command=command)
        tick_payload = advance_ticks(now_ms=now_ms)
    except WorldServiceControlError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "world-service control call failed",
                "code": "world_service_unavailable",
                "reason": str(exc),
            },
        ) from exc

    return DomainActionResponse(
        accepted=True,
        reason_code="domain_action_dispatched",
        action_type=payload.action_type.strip().lower(),
        campaign_tick=int(tick_payload.get("current_tick", 0)),
    )
