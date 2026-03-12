import os
from datetime import UTC, datetime, timedelta
from threading import Event

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.db.base import Base  # noqa: E402
from app.models.event_pipeline import WorldEvent, WorldOutbox  # noqa: E402
from app.services.event_pipeline import (  # noqa: E402
    build_outbox_notify_payload,
    claim_outbox_batch,
    mark_outbox_processed,
)
from app.services.outbox_notify_worker import (  # noqa: E402
    OutboxNotifyWorker,
    OutboxWakeSignal,
    parse_outbox_notify_payload,
    psycopg_dsn_from_sqlalchemy_url,
)


class _ScriptedNotifyConnection:
    def __init__(self, actions: list[object]) -> None:
        self._actions = list(actions)
        self.listen_channel: str | None = None
        self.closed = False

    def listen(self, channel: str) -> None:
        self.listen_channel = channel

    def poll(self, timeout_seconds: float) -> list[str]:
        if not self._actions:
            return []
        action = self._actions.pop(0)
        if isinstance(action, Exception):
            raise action
        if isinstance(action, list):
            return [str(item) for item in action]
        return []

    def close(self) -> None:
        self.closed = True


class _ScriptedNotifyConnector:
    def __init__(self, entries: list[object]) -> None:
        self._entries = list(entries)
        self.open_calls = 0

    def open(self) -> _ScriptedNotifyConnection:
        self.open_calls += 1
        if not self._entries:
            raise RuntimeError("no scripted connection available")
        entry = self._entries.pop(0)
        if isinstance(entry, Exception):
            raise entry
        return entry


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def test_worker_reconnects_and_dispatches_notify_payloads() -> None:
    first_payload = '{"outbox_id":101,"topic":"campaign.army"}'
    second_payload = '{"outbox_id":202,"topic":"campaign.trade"}'
    connector = _ScriptedNotifyConnector(
        [
            _ScriptedNotifyConnection(actions=[[first_payload], RuntimeError("connection reset")]),
            _ScriptedNotifyConnection(actions=[[second_payload], RuntimeError("connection reset")]),
        ]
    )

    observed: list[OutboxWakeSignal] = []
    stop_event = Event()

    def _wake_handler(signal: OutboxWakeSignal) -> None:
        observed.append(signal)
        notify_ids = [row.outbox_id for row in observed if row.reason == "notify"]
        if notify_ids == [101, 202]:
            stop_event.set()

    worker = OutboxNotifyWorker(
        connector=connector,
        wake_handler=_wake_handler,
        channel="world_outbox_new",
        listen_timeout_seconds=0.0,
        reconnect_delay_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    )
    worker.run(stop_event)

    notify_ids = [row.outbox_id for row in observed if row.reason == "notify"]
    startup_count = len([row for row in observed if row.reason == "startup"])

    assert notify_ids == [101, 202]
    assert startup_count >= 2
    assert connector.open_calls >= 2
    assert worker.stats.notifications_received == 2


def test_worker_restart_with_duplicate_notify_stays_idempotent_with_outbox_claims() -> None:
    db = _db_session()
    now = datetime.now(UTC)

    event = WorldEvent(
        id=901,
        stream_key="campaign:acre",
        aggregate_type="army",
        aggregate_id="army:44",
        event_type="army_moved",
        schema_version=1,
        trace_id="trace-outbox",
        payload_json={"army_id": 44, "destination": 2},
        metadata_json={},
        tick=9,
        idempotency_key="cmd-dup",
        recorded_at=now,
    )
    db.add(event)

    first = WorldOutbox(
        id=910,
        topic="campaign.army",
        payload_json={"event_id": event.id, "target": "army:44"},
        event_id=event.id,
        partition_key="army:44",
        next_attempt_at=now,
        attempt_count=0,
        last_error="",
        created_at=now,
    )
    second = WorldOutbox(
        id=911,
        topic="campaign.trade",
        payload_json={"event_id": event.id, "target": "market:acre"},
        event_id=event.id,
        partition_key="market:acre",
        next_attempt_at=now,
        attempt_count=0,
        last_error="",
        created_at=now,
    )
    db.add_all([first, second])
    db.commit()

    duplicate_notify_payload = build_outbox_notify_payload(
        outbox_id=first.id,
        topic=first.topic,
        event_id=event.id,
    )
    connector = _ScriptedNotifyConnector(
        [
            _ScriptedNotifyConnection(actions=[[duplicate_notify_payload], RuntimeError("session dropped")]),
            _ScriptedNotifyConnection(actions=[[duplicate_notify_payload], RuntimeError("session dropped")]),
        ]
    )

    processed_ids: list[int] = []
    notify_signals = 0
    stop_event = Event()

    def _wake_handler(signal: OutboxWakeSignal) -> None:
        nonlocal notify_signals
        if signal.reason == "notify":
            notify_signals += 1

        claimed = claim_outbox_batch(
            db,
            worker_id="notify-worker",
            limit=10,
            now=now + timedelta(seconds=2),
        )
        for row in claimed:
            processed_ids.append(row.id)
            mark_outbox_processed(db, outbox_id=row.id, processed_at=now + timedelta(seconds=3))

        if notify_signals >= 2 and len(processed_ids) >= 2:
            stop_event.set()

    worker = OutboxNotifyWorker(
        connector=connector,
        wake_handler=_wake_handler,
        channel="world_outbox_new",
        listen_timeout_seconds=0.0,
        reconnect_delay_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    )
    worker.run(stop_event)

    assert sorted(processed_ids) == sorted([first.id, second.id])
    assert len(processed_ids) == 2

    remaining = claim_outbox_batch(
        db,
        worker_id="notify-worker-check",
        limit=10,
        now=now + timedelta(seconds=4),
    )
    assert remaining == []


def test_parse_outbox_notify_payload_and_dsn_conversion() -> None:
    assert parse_outbox_notify_payload('{"outbox_id": 17, "topic": "campaign.army"}') == (17, "campaign.army")
    assert parse_outbox_notify_payload("18") == (18, None)
    assert parse_outbox_notify_payload("garbage") == (None, None)

    dsn = psycopg_dsn_from_sqlalchemy_url(
        "postgresql+psycopg://alice:secret@db.example.com:5432/karaxas?sslmode=require"
    )
    assert dsn.startswith("postgresql://alice:secret@db.example.com:5432/karaxas")
    assert "sslmode=require" in dsn
