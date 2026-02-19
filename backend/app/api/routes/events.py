from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.character import Character
from app.models.session import UserSession
from app.models.user import User
from app.services.observability import (
    record_transition_fallback,
    record_transition_handoff,
    record_zone_preload_latency_ms,
    record_zone_scope_update,
)
from app.services.realtime import ConnectionMeta, realtime_hub
from app.services.release_policy import ensure_release_policy, evaluate_version
from app.services.session_drain import enforce_session_drain
from app.services.ws_ticket import WsTicketError, consume_ws_ticket

router = APIRouter(prefix="/events", tags=["events"])


@router.websocket("/ws")
async def events_ws(websocket: WebSocket):
    ws_ticket = websocket.query_params.get("ticket")
    client_version = websocket.query_params.get("client_version") or "0.0.0"
    client_content_version_key = websocket.query_params.get("client_content_version_key")
    if ws_ticket is None:
        await websocket.close(code=4401, reason="Missing ticket")
        return

    db: Session = SessionLocal()
    try:
        ticket_result = consume_ws_ticket(db, ws_ticket)
        user_id = ticket_result.user_id
        session_id = ticket_result.session_id
    except WsTicketError:
        await websocket.close(code=4401, reason="Invalid ticket")
        db.close()
        return

    try:
        session = db.get(UserSession, session_id)
        user = db.get(User, user_id)
        if session is None or user is None or session.user_id != user_id:
            await websocket.close(code=4401, reason="Invalid session")
            return
        if session.revoked_at is not None:
            await websocket.close(code=4401, reason="Session revoked")
            return

        policy = ensure_release_policy(db)
        effective_content_key = client_content_version_key or session.client_content_version_key
        version_status = evaluate_version(policy, client_version, effective_content_key)
        if version_status.force_update and not user.is_admin:
            await websocket.accept()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "force_update",
                        "min_supported_version": version_status.min_supported_version,
                        "min_supported_content_version_key": version_status.min_supported_content_version_key,
                        "latest_version": version_status.latest_version,
                        "latest_content_version_key": version_status.latest_content_version_key,
                        "enforce_after": version_status.enforce_after.isoformat() if version_status.enforce_after else None,
                        "update_feed_url": version_status.update_feed_url,
                    }
                )
            )
            await websocket.close(code=4401, reason="Update required")
            return

        drain = enforce_session_drain(db, session, user)
        if drain and drain.force_logout:
            await websocket.accept()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "content_publish_forced_logout",
                        "event_id": drain.event_id,
                        "reason_code": drain.reason_code,
                        "deadline": drain.deadline_at.isoformat() if drain.deadline_at else None,
                    }
                )
            )
            await websocket.close(code=4401, reason="Publish drain cutoff reached")
            return

        await realtime_hub.connect(
            websocket,
            ConnectionMeta(
                user_id=user_id,
                channel_id=None,
                client_version=client_version,
                zone_level_id=(
                    db.execute(
                        select(Character.level_id).where(
                            Character.user_id == user_id,
                            Character.is_selected.is_(True),
                        )
                    ).scalar_one_or_none()
                ),
            ),
        )
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "user_id": user_id,
                }
            )
        )
        if drain and not drain.force_logout:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "content_publish_started",
                        "event_id": drain.event_id,
                        "reason_code": drain.reason_code,
                        "deadline": drain.deadline_at.isoformat() if drain.deadline_at else None,
                        "seconds_remaining": drain.seconds_remaining,
                    }
                )
            )

        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            try:
                payload = json.loads(data)
            except Exception:
                await websocket.send_text(json.dumps({"type": "error", "message": "invalid_json"}))
                continue

            message_type = str(payload.get("type", "")).strip().lower()
            if message_type == "zone_scope":
                raw_level = payload.get("level_id")
                try:
                    level_id = int(raw_level) if raw_level is not None else None
                except (TypeError, ValueError):
                    level_id = None
                raw_adjacent = payload.get("adjacent_level_ids")
                adjacent = raw_adjacent if isinstance(raw_adjacent, list) else []
                allow_adjacent_preview = bool(payload.get("allow_adjacent_preview", True))
                meta = await realtime_hub.update_zone_scope(
                    websocket,
                    zone_level_id=level_id,
                    adjacent_level_ids=adjacent,
                    allow_adjacent_preview=allow_adjacent_preview,
                )
                record_zone_scope_update()
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "zone_scope_ack",
                            "level_id": meta.zone_level_id if meta is not None else None,
                            "adjacent_level_ids": list(meta.adjacent_level_ids) if meta is not None else [],
                            "allow_adjacent_preview": bool(meta.allow_adjacent_preview) if meta is not None else allow_adjacent_preview,
                        }
                    )
                )
                continue

            if message_type == "zone_telemetry":
                event_name = str(payload.get("event", "")).strip().lower()
                if event_name == "preload_latency":
                    duration_ms = payload.get("duration_ms", 0)
                    success = bool(payload.get("success", False))
                    try:
                        duration = float(duration_ms)
                    except (TypeError, ValueError):
                        duration = 0.0
                    record_zone_preload_latency_ms(duration, success=success)
                elif event_name == "transition_handoff":
                    success = bool(payload.get("success", False))
                    record_transition_handoff(success=success)
                    if not success:
                        record_transition_fallback()
                elif event_name == "transition_fallback":
                    record_transition_fallback()
                continue

            if message_type == "zone_presence":
                raw_level = payload.get("level_id")
                try:
                    level_id = int(raw_level) if raw_level is not None else 0
                except (TypeError, ValueError):
                    level_id = 0
                if level_id <= 0:
                    continue
                character_id = payload.get("character_id")
                try:
                    character_id = int(character_id) if character_id is not None else None
                except (TypeError, ValueError):
                    character_id = None
                location_x = payload.get("location_x")
                location_y = payload.get("location_y")
                try:
                    location_x = int(location_x) if location_x is not None else None
                except (TypeError, ValueError):
                    location_x = None
                try:
                    location_y = int(location_y) if location_y is not None else None
                except (TypeError, ValueError):
                    location_y = None
                await realtime_hub.broadcast_zone(
                    zone_level_id=level_id,
                    include_adjacent_preview=True,
                    exclude_user_id=user_id,
                    payload={
                        "type": "zone_presence",
                        "user_id": user_id,
                        "character_id": character_id,
                        "level_id": level_id,
                        "location_x": location_x,
                        "location_y": location_y,
                    },
                )
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_hub.disconnect(websocket)
        db.close()
