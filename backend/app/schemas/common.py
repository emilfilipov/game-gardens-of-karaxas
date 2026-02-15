from datetime import datetime

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    message: str
    code: str


class VersionStatus(BaseModel):
    client_version: str
    latest_version: str
    min_supported_version: str
    enforce_after: datetime | None
    update_available: bool
    force_update: bool
