from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    appearance_key: Mapped[str] = mapped_column(String(64), nullable=False, default="human_male")
    stat_points_total: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    stat_points_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stats: Mapped[dict] = mapped_column(JSON, nullable=False)
    skills: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_selected: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
