from datetime import datetime

from pydantic import BaseModel, Field


class ActivateReleaseRequest(BaseModel):
    latest_version: str = Field(min_length=1, max_length=64)
    min_supported_version: str | None = Field(default=None, min_length=1, max_length=64)
    latest_content_version_key: str | None = Field(default=None, min_length=1, max_length=64)
    min_supported_content_version_key: str | None = Field(default=None, min_length=1, max_length=64)
    update_feed_url: str | None = Field(default=None, max_length=2048)
    build_release_notes: str = Field(default="", max_length=20000)
    user_facing_notes: str = Field(default="", max_length=20000)
    grace_minutes: int = Field(default=5, ge=0, le=120)


class ReleasePolicyResponse(BaseModel):
    latest_version: str
    min_supported_version: str
    latest_content_version_key: str
    min_supported_content_version_key: str
    update_feed_url: str | None
    enforce_after: datetime | None
    updated_by: str
    updated_at: datetime
