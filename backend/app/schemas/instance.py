from datetime import datetime

from pydantic import BaseModel


class InstanceSummaryResponse(BaseModel):
    id: str
    kind: str
    status: str
    level_id: int | None = None
    party_id: str | None = None
    last_active_at: datetime | None = None
    expires_at: datetime | None = None
    restored_from_session: bool = False
