from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReleasePolicy(Base):
    __tablename__ = "release_policy"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    latest_version: Mapped[str] = mapped_column(String(64), nullable=False, default="0.0.0")
    min_supported_version: Mapped[str] = mapped_column(String(64), nullable=False, default="0.0.0")
    enforce_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
