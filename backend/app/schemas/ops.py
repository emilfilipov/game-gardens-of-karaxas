from datetime import datetime

from pydantic import BaseModel, Field


class ActivateReleaseRequest(BaseModel):
    latest_version: str = Field(min_length=1, max_length=64)
    min_supported_version: str | None = Field(default=None, min_length=1, max_length=64)
    grace_minutes: int = Field(default=5, ge=0, le=120)


class ReleasePolicyResponse(BaseModel):
    latest_version: str
    min_supported_version: str
    enforce_after: datetime | None
    updated_by: str
    updated_at: datetime
