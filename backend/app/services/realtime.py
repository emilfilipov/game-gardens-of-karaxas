from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import WebSocket


@dataclass
class ConnectionMeta:
    user_id: int
    channel_id: int | None
    client_version: str


class RealtimeHub:
    def __init__(self) -> None:
        self._channels: dict[int, set[WebSocket]] = defaultdict(set)
        self._users: dict[int, set[WebSocket]] = defaultdict(set)
        self._meta: dict[WebSocket, ConnectionMeta] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, meta: ConnectionMeta) -> None:
        await websocket.accept()
        async with self._lock:
            if meta.channel_id is not None:
                self._channels[meta.channel_id].add(websocket)
            self._users[meta.user_id].add(websocket)
            self._meta[websocket] = meta

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            meta = self._meta.pop(websocket, None)
            if meta is None:
                return
            if meta.channel_id is not None:
                sockets = self._channels.get(meta.channel_id)
                if sockets is not None:
                    sockets.discard(websocket)
                    if not sockets:
                        self._channels.pop(meta.channel_id, None)
            user_sockets = self._users.get(meta.user_id)
            if user_sockets is not None:
                user_sockets.discard(websocket)
                if not user_sockets:
                    self._users.pop(meta.user_id, None)

    async def broadcast(self, channel_id: int, payload: dict) -> None:
        message = json.dumps(payload)
        async with self._lock:
            sockets = list(self._channels.get(channel_id, set()))
        for socket in sockets:
            try:
                await socket.send_text(message)
            except Exception:
                await self.disconnect(socket)

    async def notify_force_update(
        self,
        min_supported_version: str,
        min_supported_content_version_key: str,
        enforce_after_iso: str | None,
        update_feed_url: str | None = None,
    ) -> None:
        payload = {
            "type": "force_update",
            "min_supported_version": min_supported_version,
            "min_supported_content_version_key": min_supported_content_version_key,
            "enforce_after": enforce_after_iso,
            "update_feed_url": update_feed_url,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        async with self._lock:
            sockets = list(self._meta.keys())
        for socket in sockets:
            try:
                await socket.send_text(json.dumps(payload))
            except Exception:
                await self.disconnect(socket)

    async def _broadcast_all(self, payload: dict) -> None:
        encoded = json.dumps(payload)
        async with self._lock:
            sockets = list(self._meta.keys())
        for socket in sockets:
            try:
                await socket.send_text(encoded)
            except Exception:
                await self.disconnect(socket)

    async def notify_content_publish_started(
        self,
        *,
        event_id: int | None,
        content_version_key: str,
        reason_code: str,
        deadline_iso: str | None,
        grace_seconds: int,
    ) -> None:
        await self._broadcast_all(
            {
                "type": "content_publish_started",
                "event_id": event_id,
                "content_version_key": content_version_key,
                "reason_code": reason_code,
                "deadline": deadline_iso,
                "grace_seconds": grace_seconds,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    async def notify_content_publish_warning(
        self,
        *,
        event_id: int | None,
        content_version_key: str,
        reason_code: str,
        deadline_iso: str | None,
        seconds_remaining: int,
    ) -> None:
        await self._broadcast_all(
            {
                "type": "content_publish_warning",
                "event_id": event_id,
                "content_version_key": content_version_key,
                "reason_code": reason_code,
                "deadline": deadline_iso,
                "seconds_remaining": max(0, seconds_remaining),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    async def notify_content_publish_forced_logout(
        self,
        *,
        event_id: int | None,
        content_version_key: str,
        reason_code: str,
        cutoff_iso: str | None,
    ) -> None:
        await self._broadcast_all(
            {
                "type": "content_publish_forced_logout",
                "event_id": event_id,
                "content_version_key": content_version_key,
                "reason_code": reason_code,
                "cutoff_at": cutoff_iso,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


realtime_hub = RealtimeHub()
