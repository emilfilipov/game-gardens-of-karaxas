from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db
from app.core.security import TokenPayloadError, decode_access_token
from app.db.session import SessionLocal
from app.models.chat import ChatChannel, ChatMember, ChatMessage
from app.models.session import UserSession
from app.models.user import User
from app.schemas.chat import ChannelResponse, ChatMessageCreateRequest, ChatMessageResponse, DirectChannelRequest
from app.services.realtime import ConnectionMeta, realtime_hub
from app.services.release_policy import ensure_release_policy, evaluate_version

router = APIRouter(prefix="/chat", tags=["chat"])


def _can_access_channel(db: Session, user_id: int, channel: ChatChannel) -> bool:
    if channel.kind == "GLOBAL":
        return True
    member = db.execute(
        select(ChatMember).where(and_(ChatMember.channel_id == channel.id, ChatMember.user_id == user_id))
    ).scalar_one_or_none()
    return member is not None


def _to_channel_response(channel: ChatChannel) -> ChannelResponse:
    return ChannelResponse(id=channel.id, name=channel.name, kind=channel.kind, guild_id=channel.guild_id)


@router.get("/channels", response_model=list[ChannelResponse])
def list_channels(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    rows = db.execute(
        select(ChatChannel)
        .outerjoin(ChatMember, ChatMember.channel_id == ChatChannel.id)
        .where(or_(ChatChannel.kind == "GLOBAL", ChatMember.user_id == context.user.id))
        .order_by(ChatChannel.kind.asc(), ChatChannel.name.asc())
        .distinct()
    ).scalars()
    return [_to_channel_response(row) for row in rows]


@router.post("/channels/direct", response_model=ChannelResponse)
def create_or_get_direct_channel(
    payload: DirectChannelRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    if payload.target_user_id == context.user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Cannot create direct channel to self", "code": "invalid_target"},
        )

    target_user = db.get(User, payload.target_user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Target user not found", "code": "target_not_found"},
        )

    rows = db.execute(
        select(ChatChannel)
        .join(ChatMember, ChatMember.channel_id == ChatChannel.id)
        .where(ChatChannel.kind == "DIRECT")
    ).scalars().all()

    for channel in rows:
        members = db.execute(select(ChatMember.user_id).where(ChatMember.channel_id == channel.id)).scalars().all()
        if sorted(members) == sorted([context.user.id, payload.target_user_id]):
            return _to_channel_response(channel)

    ordered = sorted([context.user.display_name, target_user.display_name])
    channel = ChatChannel(name=f"DM: {ordered[0]} / {ordered[1]}", kind="DIRECT")
    db.add(channel)
    db.commit()
    db.refresh(channel)

    db.add(ChatMember(channel_id=channel.id, user_id=context.user.id))
    db.add(ChatMember(channel_id=channel.id, user_id=target_user.id))
    db.commit()

    return _to_channel_response(channel)


@router.get("/messages", response_model=list[ChatMessageResponse])
def list_messages(
    channel_id: int = Query(..., ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    channel = db.get(ChatChannel, channel_id)
    if channel is None or not _can_access_channel(db, context.user.id, channel):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Channel not found", "code": "channel_not_found"},
        )

    rows = db.execute(
        select(ChatMessage, User)
        .join(User, User.id == ChatMessage.sender_user_id)
        .where(ChatMessage.channel_id == channel_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    ).all()
    rows.reverse()
    return [
        ChatMessageResponse(
            id=message.id,
            channel_id=message.channel_id,
            sender_user_id=message.sender_user_id,
            sender_display_name=user.display_name,
            content=message.content,
            created_at=message.created_at,
        )
        for message, user in rows
    ]


@router.post("/messages", response_model=ChatMessageResponse)
async def create_message(
    payload: ChatMessageCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    channel = db.get(ChatChannel, payload.channel_id)
    if channel is None or not _can_access_channel(db, context.user.id, channel):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Channel not found", "code": "channel_not_found"},
        )

    message = ChatMessage(
        channel_id=payload.channel_id,
        sender_user_id=context.user.id,
        content=payload.content.strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    response = ChatMessageResponse(
        id=message.id,
        channel_id=message.channel_id,
        sender_user_id=message.sender_user_id,
        sender_display_name=context.user.display_name,
        content=message.content,
        created_at=message.created_at,
    )

    await realtime_hub.broadcast(
        payload.channel_id,
        {
            "type": "chat_message",
            "message": response.model_dump(mode="json"),
        },
    )
    return response


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    channel_id_raw = websocket.query_params.get("channel_id", "1")
    client_version = websocket.query_params.get("client_version") or "0.0.0"

    if token is None:
        await websocket.close(code=4401, reason="Missing token")
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        session_id = str(payload["sid"])
        channel_id = int(channel_id_raw)
    except (TokenPayloadError, ValueError):
        await websocket.close(code=4401, reason="Invalid token")
        return

    db = SessionLocal()
    try:
        session = db.get(UserSession, session_id)
        user = db.get(User, user_id)
        channel = db.get(ChatChannel, channel_id)
        if session is None or user is None or channel is None:
            await websocket.close(code=4401, reason="Invalid session")
            return
        if session.revoked_at is not None:
            await websocket.close(code=4401, reason="Session revoked")
            return
        if not _can_access_channel(db, user_id, channel):
            await websocket.close(code=4403, reason="Channel access denied")
            return

        policy = ensure_release_policy(db)
        version_status = evaluate_version(policy, client_version)
        if version_status.force_update:
            await websocket.accept()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "force_update",
                        "min_supported_version": version_status.min_supported_version,
                        "latest_version": version_status.latest_version,
                        "enforce_after": version_status.enforce_after.isoformat() if version_status.enforce_after else None,
                    }
                )
            )
            await websocket.close(code=4401, reason="Update required")
            return

        await realtime_hub.connect(
            websocket,
            ConnectionMeta(user_id=user_id, channel_id=channel_id, client_version=client_version),
        )

        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "channel_id": channel_id,
                    "user_id": user_id,
                }
            )
        )

        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            try:
                parsed = json.loads(data)
            except Exception:
                await websocket.send_text(json.dumps({"type": "error", "message": "invalid_json"}))
                continue

            content = str(parsed.get("content", "")).strip()
            if not content:
                continue

            msg = ChatMessage(channel_id=channel_id, sender_user_id=user_id, content=content)
            db.add(msg)
            db.commit()
            db.refresh(msg)

            await realtime_hub.broadcast(
                channel_id,
                {
                    "type": "chat_message",
                    "message": {
                        "id": msg.id,
                        "channel_id": msg.channel_id,
                        "sender_user_id": msg.sender_user_id,
                        "sender_display_name": user.display_name,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                    },
                },
            )
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_hub.disconnect(websocket)
        db.close()
