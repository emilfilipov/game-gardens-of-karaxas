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
    zone_level_id: int | None = None
    instance_id: str | None = None
    party_id: str | None = None
    is_hub_zone: bool = False
    adjacent_level_ids: tuple[int, ...] = ()
    allow_adjacent_preview: bool = True


class RealtimeHub:
    def __init__(self) -> None:
        self._channels: dict[int, set[WebSocket]] = defaultdict(set)
        self._users: dict[int, set[WebSocket]] = defaultdict(set)
        self._zones: dict[int, set[WebSocket]] = defaultdict(set)
        self._meta: dict[WebSocket, ConnectionMeta] = {}
        self._hub_presence: dict[int, int] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, meta: ConnectionMeta) -> None:
        await websocket.accept()
        join_event: tuple[int, int] | None = None
        async with self._lock:
            if meta.channel_id is not None:
                self._channels[meta.channel_id].add(websocket)
            if meta.zone_level_id is not None:
                self._zones[meta.zone_level_id].add(websocket)
            self._users[meta.user_id].add(websocket)
            self._meta[websocket] = meta
            if meta.is_hub_zone and meta.zone_level_id is not None:
                current_hub = self._hub_presence.get(meta.user_id)
                if current_hub != meta.zone_level_id:
                    self._hub_presence[meta.user_id] = meta.zone_level_id
                    join_event = (meta.user_id, meta.zone_level_id)
        if join_event is not None:
            await self.broadcast_zone(
                zone_level_id=join_event[1],
                include_adjacent_preview=False,
                exclude_user_id=join_event[0],
                payload={"type": "hub_presence_join", "user_id": join_event[0], "level_id": join_event[1]},
            )

    async def disconnect(self, websocket: WebSocket) -> None:
        leave_event: tuple[int, int] | None = None
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
            if meta.zone_level_id is not None:
                zone_sockets = self._zones.get(meta.zone_level_id)
                if zone_sockets is not None:
                    zone_sockets.discard(websocket)
                    if not zone_sockets:
                        self._zones.pop(meta.zone_level_id, None)
            user_sockets = self._users.get(meta.user_id)
            if user_sockets is not None:
                user_sockets.discard(websocket)
                if not user_sockets:
                    self._users.pop(meta.user_id, None)
                    hub_id = self._hub_presence.pop(meta.user_id, None)
                    if hub_id is not None:
                        leave_event = (meta.user_id, hub_id)
        if leave_event is not None:
            await self.broadcast_zone(
                zone_level_id=leave_event[1],
                include_adjacent_preview=False,
                exclude_user_id=leave_event[0],
                payload={"type": "hub_presence_leave", "user_id": leave_event[0], "level_id": leave_event[1]},
            )

    async def broadcast(self, channel_id: int, payload: dict) -> None:
        message = json.dumps(payload)
        async with self._lock:
            sockets = list(self._channels.get(channel_id, set()))
        for socket in sockets:
            try:
                await socket.send_text(message)
            except Exception:
                await self.disconnect(socket)

    async def update_zone_scope(
        self,
        websocket: WebSocket,
        *,
        zone_level_id: int | None,
        adjacent_level_ids: list[int] | tuple[int, ...] | None,
        is_hub_zone: bool = False,
        allow_adjacent_preview: bool = True,
    ) -> ConnectionMeta | None:
        sanitized_adjacent: list[int] = []
        if adjacent_level_ids:
            seen: set[int] = set()
            for raw in adjacent_level_ids:
                try:
                    value = int(raw)
                except (TypeError, ValueError):
                    continue
                if value <= 0 or value in seen:
                    continue
                seen.add(value)
                sanitized_adjacent.append(value)

        join_event: tuple[int, int] | None = None
        leave_event: tuple[int, int] | None = None
        async with self._lock:
            existing = self._meta.get(websocket)
            if existing is None:
                return None
            previous_zone = existing.zone_level_id
            if previous_zone is not None:
                zone_sockets = self._zones.get(previous_zone)
                if zone_sockets is not None:
                    zone_sockets.discard(websocket)
                    if not zone_sockets:
                        self._zones.pop(previous_zone, None)

            normalized_zone = zone_level_id if isinstance(zone_level_id, int) and zone_level_id > 0 else None
            normalized_is_hub = bool(is_hub_zone) and normalized_zone is not None
            updated = ConnectionMeta(
                user_id=existing.user_id,
                channel_id=existing.channel_id,
                client_version=existing.client_version,
                zone_level_id=normalized_zone,
                instance_id=existing.instance_id,
                party_id=existing.party_id,
                is_hub_zone=normalized_is_hub,
                adjacent_level_ids=tuple(sanitized_adjacent),
                allow_adjacent_preview=bool(allow_adjacent_preview),
            )
            self._meta[websocket] = updated
            if normalized_zone is not None:
                self._zones[normalized_zone].add(websocket)
            previous_hub = self._hub_presence.get(existing.user_id)
            if existing.is_hub_zone and previous_hub is not None and previous_hub != normalized_zone:
                leave_event = (existing.user_id, previous_hub)
                self._hub_presence.pop(existing.user_id, None)
            if updated.is_hub_zone and normalized_zone is not None:
                if self._hub_presence.get(existing.user_id) != normalized_zone:
                    self._hub_presence[existing.user_id] = normalized_zone
                    join_event = (existing.user_id, normalized_zone)
            elif not updated.is_hub_zone:
                current_hub = self._hub_presence.pop(existing.user_id, None)
                if current_hub is not None:
                    leave_event = (existing.user_id, current_hub)
        if leave_event is not None:
            await self.broadcast_zone(
                zone_level_id=leave_event[1],
                include_adjacent_preview=False,
                exclude_user_id=leave_event[0],
                payload={"type": "hub_presence_leave", "user_id": leave_event[0], "level_id": leave_event[1]},
            )
        if join_event is not None:
            await self.broadcast_zone(
                zone_level_id=join_event[1],
                include_adjacent_preview=False,
                exclude_user_id=join_event[0],
                payload={"type": "hub_presence_join", "user_id": join_event[0], "level_id": join_event[1]},
            )
        return updated

    async def sockets_for_zone(
        self,
        zone_level_id: int,
        *,
        include_adjacent_preview: bool,
        exclude_user_id: int | None = None,
    ) -> list[WebSocket]:
        if zone_level_id <= 0:
            return []
        async with self._lock:
            if include_adjacent_preview:
                sockets = []
                for socket, meta in self._meta.items():
                    if exclude_user_id is not None and meta.user_id == exclude_user_id:
                        continue
                    if meta.zone_level_id == zone_level_id:
                        sockets.append(socket)
                        continue
                    if not meta.allow_adjacent_preview:
                        continue
                    if zone_level_id in meta.adjacent_level_ids:
                        sockets.append(socket)
                return sockets
            direct = list(self._zones.get(zone_level_id, set()))
            if exclude_user_id is None:
                return direct
            filtered: list[WebSocket] = []
            for socket in direct:
                meta = self._meta.get(socket)
                if meta is None or meta.user_id == exclude_user_id:
                    continue
                filtered.append(socket)
            return filtered

    async def broadcast_zone(
        self,
        *,
        zone_level_id: int,
        payload: dict,
        include_adjacent_preview: bool = False,
        exclude_user_id: int | None = None,
    ) -> int:
        recipients = await self.sockets_for_zone(
            zone_level_id,
            include_adjacent_preview=include_adjacent_preview,
            exclude_user_id=exclude_user_id,
        )
        encoded = json.dumps(payload)
        delivered = 0
        for socket in recipients:
            try:
                await socket.send_text(encoded)
                delivered += 1
            except Exception:
                await self.disconnect(socket)
        from app.services.observability import record_zone_broadcast

        record_zone_broadcast(delivered)
        return delivered

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
