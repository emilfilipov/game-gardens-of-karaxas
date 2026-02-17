from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PublishDrainEvent(Base):
    __tablename__ = "publish_drain_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(128), nullable=False)
    content_version_id: Mapped[int | None] = mapped_column(ForeignKey("content_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    content_version_key: Mapped[str] = mapped_column(String(64), nullable=False)
    build_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grace_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cutoff_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draining")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sessions_targeted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_persisted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_persist_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_revoked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PublishDrainSessionAudit(Base):
    __tablename__ = "publish_drain_session_audit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("publish_drain_events.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    persisted_ok: Mapped[bool] = mapped_column(nullable=False, default=False)
    despawned_ok: Mapped[bool] = mapped_column(nullable=False, default=False)
    revoked_ok: Mapped[bool] = mapped_column(nullable=False, default=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

