from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorldEvent(Base):
    __tablename__ = "world_events"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True, autoincrement=True)
    stream_key: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    schema_version: Mapped[int] = mapped_column(nullable=False)
    tick: Mapped[int | None] = mapped_column(BigInteger(), nullable=True, index=True)
    trace_id: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class WorldOutbox(Base):
    __tablename__ = "world_outbox"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    partition_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("world_events.id", ondelete="CASCADE"), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    locked_by: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WorldCommandIdempotency(Base):
    __tablename__ = "world_command_idempotency"
    __table_args__ = (UniqueConstraint("scope", "idempotency_key", name="uq_world_command_idempotency_scope_key"),)

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("world_events.id", ondelete="SET NULL"), nullable=True, index=True)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), index=True
    )


class WorldProcessorCursor(Base):
    __tablename__ = "world_processor_cursors"

    processor_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_event_id: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
