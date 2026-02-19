import asyncio
import json

from app.services.realtime import ConnectionMeta, RealtimeHub


class FakeSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, payload: str) -> None:
        self.messages.append(json.loads(payload))


def test_zone_broadcast_respects_active_zone_and_adjacent_preview() -> None:
    async def run() -> None:
        hub = RealtimeHub()
        socket_a = FakeSocket()
        socket_b = FakeSocket()
        socket_c = FakeSocket()

        await hub.connect(socket_a, ConnectionMeta(user_id=1, channel_id=None, client_version="1.0.0", zone_level_id=1))
        await hub.connect(
            socket_b,
            ConnectionMeta(
                user_id=2,
                channel_id=None,
                client_version="1.0.0",
                zone_level_id=2,
                adjacent_level_ids=(1,),
                allow_adjacent_preview=True,
            ),
        )
        await hub.connect(socket_c, ConnectionMeta(user_id=3, channel_id=None, client_version="1.0.0", zone_level_id=3))

        delivered_direct = await hub.broadcast_zone(
            zone_level_id=1,
            include_adjacent_preview=False,
            payload={"type": "zone_presence", "level_id": 1},
        )
        assert delivered_direct == 1
        assert len(socket_a.messages) == 1
        assert len(socket_b.messages) == 0
        assert len(socket_c.messages) == 0

        delivered_with_adjacent = await hub.broadcast_zone(
            zone_level_id=1,
            include_adjacent_preview=True,
            payload={"type": "zone_presence", "level_id": 1},
        )
        assert delivered_with_adjacent == 2
        assert len(socket_a.messages) == 2
        assert len(socket_b.messages) == 1
        assert len(socket_c.messages) == 0

        meta = await hub.update_zone_scope(
            socket_c,
            zone_level_id=1,
            adjacent_level_ids=[2],
            allow_adjacent_preview=False,
        )
        assert meta is not None
        assert meta.zone_level_id == 1
        assert meta.adjacent_level_ids == (2,)
        assert meta.allow_adjacent_preview is False

        delivered_after_scope_change = await hub.broadcast_zone(
            zone_level_id=1,
            include_adjacent_preview=False,
            exclude_user_id=1,
            payload={"type": "zone_presence", "level_id": 1},
        )
        assert delivered_after_scope_change == 1
        assert len(socket_a.messages) == 2
        assert len(socket_c.messages) == 1

    asyncio.run(run())
