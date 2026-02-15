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
    channel_id: int
    client_version: str


class RealtimeHub:
    def __init__(self) -> None:
        self._channels: dict[int, set[WebSocket]] = defaultdict(set)
        self._meta: dict[WebSocket, ConnectionMeta] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, meta: ConnectionMeta) -> None:
        await websocket.accept()
        async with self._lock:
            self._channels[meta.channel_id].add(websocket)
            self._meta[websocket] = meta

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            meta = self._meta.pop(websocket, None)
            if meta is None:
                return
            sockets = self._channels.get(meta.channel_id)
            if sockets is not None:
                sockets.discard(websocket)
                if not sockets:
                    self._channels.pop(meta.channel_id, None)

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
        enforce_after_iso: str | None,
    ) -> None:
        payload = {
            "type": "force_update",
            "min_supported_version": min_supported_version,
            "enforce_after": enforce_after_iso,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        async with self._lock:
            sockets = list(self._meta.keys())
        for socket in sockets:
            try:
                await socket.send_text(json.dumps(payload))
            except Exception:
                await self.disconnect(socket)


realtime_hub = RealtimeHub()
