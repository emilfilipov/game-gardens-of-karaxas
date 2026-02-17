from datetime import datetime

from pydantic import BaseModel


class ReleaseSummaryResponse(BaseModel):
    client_version: str
    latest_version: str
    min_supported_version: str
    client_content_version_key: str
    latest_content_version_key: str
    min_supported_content_version_key: str
    enforce_after: datetime | None
    update_available: bool
    content_update_available: bool
    force_update: bool
    update_feed_url: str | None
    latest_build_release_notes: str
    latest_user_facing_notes: str
    client_build_release_notes: str
    latest_content_note: str
    client_content_note: str
    latest_published_at: datetime | None
