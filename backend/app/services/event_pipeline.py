from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event_pipeline import (
    WorldCommandIdempotency,
    WorldEvent,
    WorldOutbox,
    WorldProcessorCursor,
)

OUTBOX_NOTIFY_CHANNEL = "world_outbox_new"


class IdempotencyConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class IdempotencyReservation:
    record: WorldCommandIdempotency
    created: bool


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _stable_json_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_outbox_notify_payload(*, outbox_id: int, topic: str, event_id: int | None) -> str:
    payload = {
        "outbox_id": int(outbox_id),
        "topic": (topic or "").strip() or "default",
    }
    if event_id is not None:
        payload["event_id"] = int(event_id)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def reserve_idempotency_key(db: Session, *, scope: str, idempotency_key: str, request_payload: dict) -> IdempotencyReservation:
    normalized_scope = (scope or "").strip()
    normalized_key = (idempotency_key or "").strip()
    if not normalized_scope:
        raise ValueError("scope must not be empty")
    if not normalized_key:
        raise ValueError("idempotency_key must not be empty")

    request_hash = _stable_json_hash(request_payload)
    existing = db.execute(
        select(WorldCommandIdempotency).where(
            WorldCommandIdempotency.scope == normalized_scope,
            WorldCommandIdempotency.idempotency_key == normalized_key,
        )
    ).scalar_one_or_none()

    if existing is not None:
        if existing.request_hash != request_hash:
            raise IdempotencyConflictError("idempotency key reused with different request payload")
        return IdempotencyReservation(record=existing, created=False)

    row = WorldCommandIdempotency(
        scope=normalized_scope,
        idempotency_key=normalized_key,
        request_hash=request_hash,
        status="pending",
    )
    db.add(row)
    db.flush()
    return IdempotencyReservation(record=row, created=True)


def finalize_idempotency_key(
    db: Session,
    *,
    record: WorldCommandIdempotency,
    status: str,
    response_payload: dict | None,
    event_id: int | None,
) -> WorldCommandIdempotency:
    normalized_status = (status or "").strip()
    if not normalized_status:
        raise ValueError("status must not be empty")

    record.status = normalized_status
    record.response_json = response_payload
    record.event_id = event_id
    db.add(record)
    db.flush()
    return record


def append_world_event(
    db: Session,
    *,
    stream_key: str,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    schema_version: int,
    trace_id: str,
    payload_json: dict,
    metadata_json: dict | None = None,
    tick: int | None = None,
    idempotency_key: str | None = None,
) -> WorldEvent:
    row = WorldEvent(
        stream_key=(stream_key or "").strip() or "default",
        aggregate_type=(aggregate_type or "").strip() or "unknown",
        aggregate_id=(aggregate_id or "").strip() or "unknown",
        event_type=(event_type or "").strip() or "unknown",
        schema_version=max(1, int(schema_version)),
        trace_id=(trace_id or "").strip() or "unknown",
        payload_json=payload_json or {},
        metadata_json=metadata_json or {},
        tick=tick,
        idempotency_key=(idempotency_key or "").strip() or None,
    )
    db.add(row)
    db.flush()
    return row


def enqueue_outbox_message(
    db: Session,
    *,
    topic: str,
    payload_json: dict,
    event_id: int | None = None,
    partition_key: str | None = None,
    next_attempt_at: datetime | None = None,
) -> WorldOutbox:
    row = WorldOutbox(
        topic=(topic or "").strip() or "default",
        payload_json=payload_json or {},
        event_id=event_id,
        partition_key=(partition_key or "").strip() or None,
        next_attempt_at=next_attempt_at or _now_utc(),
        attempt_count=0,
        last_error="",
    )
    db.add(row)
    db.flush()
    return row


def claim_outbox_batch(db: Session, *, worker_id: str, limit: int, now: datetime | None = None) -> list[WorldOutbox]:
    at = now or _now_utc()
    safe_limit = max(1, min(limit, 500))

    rows = (
        db.execute(
            select(WorldOutbox)
            .where(
                WorldOutbox.processed_at.is_(None),
                WorldOutbox.locked_at.is_(None),
                WorldOutbox.next_attempt_at <= at,
            )
            .order_by(WorldOutbox.id.asc())
            .limit(safe_limit)
        )
        .scalars()
        .all()
    )

    normalized_worker = (worker_id or "").strip() or "worker"
    for row in rows:
        row.locked_by = normalized_worker
        row.locked_at = at
        row.attempt_count += 1
        db.add(row)
    db.flush()
    return rows


def mark_outbox_processed(db: Session, *, outbox_id: int, processed_at: datetime | None = None) -> WorldOutbox | None:
    row = db.get(WorldOutbox, outbox_id)
    if row is None:
        return None

    row.processed_at = processed_at or _now_utc()
    row.locked_at = None
    row.locked_by = None
    row.last_error = ""
    db.add(row)
    db.flush()
    return row


def mark_outbox_retry(
    db: Session,
    *,
    outbox_id: int,
    delay_seconds: int,
    last_error: str,
    now: datetime | None = None,
) -> WorldOutbox | None:
    row = db.get(WorldOutbox, outbox_id)
    if row is None:
        return None

    at = now or _now_utc()
    row.next_attempt_at = at + timedelta(seconds=max(0, delay_seconds))
    row.locked_at = None
    row.locked_by = None
    row.last_error = (last_error or "").strip()
    db.add(row)
    db.flush()
    return row


def get_or_create_processor_cursor(db: Session, *, processor_name: str) -> WorldProcessorCursor:
    normalized_name = (processor_name or "").strip()
    if not normalized_name:
        raise ValueError("processor_name must not be empty")

    row = db.get(WorldProcessorCursor, normalized_name)
    if row is not None:
        return row

    row = WorldProcessorCursor(
        processor_name=normalized_name,
        last_event_id=0,
        metadata_json={},
    )
    db.add(row)
    db.flush()
    return row


def advance_processor_cursor(
    db: Session,
    *,
    processor_name: str,
    last_event_id: int,
    last_event_at: datetime | None,
    metadata_json: dict | None = None,
) -> WorldProcessorCursor:
    row = get_or_create_processor_cursor(db, processor_name=processor_name)
    if last_event_id >= row.last_event_id:
        row.last_event_id = last_event_id
        row.last_event_at = last_event_at
        row.metadata_json = metadata_json or row.metadata_json
        db.add(row)
        db.flush()
    return row
