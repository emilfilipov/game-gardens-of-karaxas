from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    previous_refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    refresh_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_version: Mapped[str] = mapped_column(String(64), nullable=False, default="0.0.0")
    client_content_version_key: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    drain_state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    drain_event_id: Mapped[int | None] = mapped_column(ForeignKey("publish_drain_events.id", ondelete="SET NULL"), nullable=True, index=True)
    drain_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    drain_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
