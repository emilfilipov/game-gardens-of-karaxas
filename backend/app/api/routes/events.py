from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import TokenPayloadError, decode_access_token
from app.db.session import SessionLocal
from app.models.session import UserSession
from app.models.user import User
from app.services.realtime import ConnectionMeta, realtime_hub
from app.services.release_policy import ensure_release_policy, evaluate_version
from app.services.session_drain import enforce_session_drain

router = APIRouter(prefix="/events", tags=["events"])


@router.websocket("/ws")
async def events_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    client_version = websocket.query_params.get("client_version") or "0.0.0"
    client_content_version_key = websocket.query_params.get("client_content_version_key")
    if token is None:
        await websocket.close(code=4401, reason="Missing token")
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        session_id = str(payload["sid"])
    except (TokenPayloadError, ValueError):
        await websocket.close(code=4401, reason="Invalid token")
        return

    db: Session = SessionLocal()
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
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_hub.disconnect(websocket)
        db.close()

