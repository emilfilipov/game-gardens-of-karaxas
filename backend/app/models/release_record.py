from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReleaseRecord(Base):
    __tablename__ = "release_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    build_version: Mapped[str] = mapped_column(String(64), nullable=False)
    min_supported_version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_version_key: Mapped[str] = mapped_column(String(64), nullable=False)
    min_supported_content_version_key: Mapped[str] = mapped_column(String(64), nullable=False)
    update_feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    build_release_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_facing_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    activated_by: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    enforce_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
