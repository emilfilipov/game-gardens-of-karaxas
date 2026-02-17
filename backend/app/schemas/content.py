from datetime import datetime

from pydantic import BaseModel, Field


class ContentValidationIssueResponse(BaseModel):
    domain: str
    message: str


class ContentBootstrapResponse(BaseModel):
    content_schema_version: int
    content_version_id: int
    content_version_key: str
    fetched_at: datetime
    domains: dict[str, dict]


class ContentVersionSummaryResponse(BaseModel):
    id: int
    version_key: str
    state: str
    note: str
    created_by_user_id: int | None
    created_at: datetime
    validated_at: datetime | None
    activated_at: datetime | None
    updated_at: datetime


class ContentVersionDetailResponse(ContentVersionSummaryResponse):
    domains: dict[str, dict]


class ContentVersionCreateRequest(BaseModel):
    note: str = Field(default="", max_length=255)


class ContentBundleUpsertRequest(BaseModel):
    payload: dict = Field(default_factory=dict)


class ContentValidationResponse(BaseModel):
    ok: bool
    issues: list[ContentValidationIssueResponse] = Field(default_factory=list)
    state: str


class ContentPublishDrainSummaryResponse(BaseModel):
    id: int
    trigger_type: str
    reason_code: str
    initiated_by: str
    content_version_id: int | None
    content_version_key: str
    build_version: str | None
    grace_seconds: int
    started_at: datetime
    deadline_at: datetime
    cutoff_at: datetime | None
    status: str
    sessions_targeted: int
    sessions_persisted: int
    sessions_persist_failed: int
    sessions_revoked: int
