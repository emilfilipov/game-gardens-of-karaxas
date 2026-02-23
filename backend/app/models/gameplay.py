from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GameplayActionAudit(Base):
    __tablename__ = "gameplay_action_audit"
    __table_args__ = (UniqueConstraint("session_id", "action_nonce", name="uq_gameplay_action_session_nonce"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    action_nonce: Mapped[str] = mapped_column(String(96), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
