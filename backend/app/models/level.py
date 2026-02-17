from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    spawn_x: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    spawn_y: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    wall_cells: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    layer_cells: Mapped[dict[str, list[dict]]] = mapped_column(JSON, nullable=False, default=dict)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
