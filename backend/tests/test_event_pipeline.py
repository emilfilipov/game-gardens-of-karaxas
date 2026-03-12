import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.db.base import Base  # noqa: E402
from app.models.event_pipeline import WorldCommandIdempotency  # noqa: E402
from app.services.event_pipeline import (  # noqa: E402
    IdempotencyConflictError,
    advance_processor_cursor,
    append_world_event,
    claim_outbox_batch,
    enqueue_outbox_message,
    finalize_idempotency_key,
    get_or_create_processor_cursor,
    mark_outbox_processed,
    mark_outbox_retry,
    reserve_idempotency_key,
)


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def test_duplicate_idempotency_key_with_same_payload_is_safe() -> None:
    db = _db_session()
    payload = {"command": "move_army", "army_id": 10, "destination": 2}

    first = reserve_idempotency_key(
        db,
        scope="world.command",
        idempotency_key="cmd-1",
        request_payload=payload,
    )
    assert first.created is True

    second = reserve_idempotency_key(
        db,
        scope="world.command",
        idempotency_key="cmd-1",
        request_payload=payload,
    )
    assert second.created is False
    assert second.record.id == first.record.id


def test_duplicate_idempotency_key_with_changed_payload_is_rejected() -> None:
    db = _db_session()
    reserve_idempotency_key(
        db,
        scope="world.command",
        idempotency_key="cmd-2",
        request_payload={"command": "move_army", "army_id": 10},
    )

    try:
        reserve_idempotency_key(
            db,
            scope="world.command",
            idempotency_key="cmd-2",
            request_payload={"command": "move_army", "army_id": 99},
        )
    except IdempotencyConflictError:
        pass
    else:
        assert False, "Expected IdempotencyConflictError"


def test_outbox_retry_and_resume_flow() -> None:
    db = _db_session()
    now = datetime.now(UTC)

    event = append_world_event(
        db,
        stream_key="campaign:acre",
        aggregate_type="army",
        aggregate_id="army:7",
        event_type="army_moved",
        schema_version=1,
        trace_id="trace-1",
        payload_json={"army_id": 7, "destination": 11},
        metadata_json={},
        tick=5,
        idempotency_key="cmd-3",
    )
    outbox = enqueue_outbox_message(
        db,
        topic="campaign.army",
        payload_json={"event_id": event.id},
        event_id=event.id,
        partition_key="army:7",
        next_attempt_at=now,
    )

    claimed = claim_outbox_batch(db, worker_id="worker-a", limit=10, now=now)
    assert len(claimed) == 1
    assert claimed[0].id == outbox.id

    mark_outbox_retry(
        db,
        outbox_id=outbox.id,
        delay_seconds=30,
        last_error="temporary transport failure",
        now=now,
    )

    blocked = claim_outbox_batch(db, worker_id="worker-b", limit=10, now=now + timedelta(seconds=10))
    assert blocked == []

    resumed = claim_outbox_batch(db, worker_id="worker-b", limit=10, now=now + timedelta(seconds=31))
    assert len(resumed) == 1
    assert resumed[0].id == outbox.id

    mark_outbox_processed(db, outbox_id=outbox.id, processed_at=now + timedelta(seconds=32))
    post_processed = claim_outbox_batch(db, worker_id="worker-c", limit=10, now=now + timedelta(seconds=33))
    assert post_processed == []


def test_cursor_advances_monotonically_for_resume_support() -> None:
    db = _db_session()

    cursor = get_or_create_processor_cursor(db, processor_name="notifier")
    assert cursor.last_event_id == 0

    advanced = advance_processor_cursor(
        db,
        processor_name="notifier",
        last_event_id=18,
        last_event_at=datetime.now(UTC),
        metadata_json={"partition": "campaign:acre"},
    )
    assert advanced.last_event_id == 18

    unchanged = advance_processor_cursor(
        db,
        processor_name="notifier",
        last_event_id=17,
        last_event_at=datetime.now(UTC),
        metadata_json={"partition": "older"},
    )
    assert unchanged.last_event_id == 18


def test_finalize_idempotency_links_response_and_event() -> None:
    db = _db_session()

    reservation = reserve_idempotency_key(
        db,
        scope="world.command",
        idempotency_key="cmd-4",
        request_payload={"command": "set_stance"},
    )
    event = append_world_event(
        db,
        stream_key="campaign:acre",
        aggregate_type="faction",
        aggregate_id="faction:1",
        event_type="stance_updated",
        schema_version=1,
        trace_id="trace-2",
        payload_json={"actor": 1, "target": 2, "delta": -3},
        metadata_json={},
        tick=8,
        idempotency_key="cmd-4",
    )

    completed = finalize_idempotency_key(
        db,
        record=reservation.record,
        status="applied",
        response_payload={"accepted": True},
        event_id=event.id,
    )
    assert completed.status == "applied"
    assert completed.event_id == event.id

    fetched = db.get(WorldCommandIdempotency, completed.id)
    assert fetched is not None
    assert fetched.response_json == {"accepted": True}
