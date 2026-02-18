from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.release_policy import ensure_release_policy

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.get("/health/deep")
def deep_health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    policy = ensure_release_policy(db)
    return {
        "ok": True,
        "checked_at": datetime.now(UTC).isoformat(),
        "latest_version": policy.latest_version,
        "latest_content_version_key": policy.latest_content_version_key,
    }
