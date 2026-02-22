from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    level_id: Mapped[int | None] = mapped_column(ForeignKey("levels.id", ondelete="SET NULL"), nullable=True, index=True)
    location_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    appearance_key: Mapped[str] = mapped_column(String(64), nullable=False, default="human_male")
    race: Mapped[str] = mapped_column(String(64), nullable=False, default="Human")
    background: Mapped[str] = mapped_column(String(64), nullable=False, default="Drifter")
    affiliation: Mapped[str] = mapped_column(String(64), nullable=False, default="Unaffiliated")
    stat_points_total: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    stat_points_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    equipment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    appearance_profile: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    stats: Mapped[dict] = mapped_column(JSON, nullable=False)
    skills: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_selected: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
