from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_ops_token
from app.schemas.ops import ActivateReleaseRequest, ReleasePolicyResponse
from app.services.realtime import realtime_hub
from app.services.release_policy import activate_release, ensure_release_policy

router = APIRouter(prefix="/ops/release", tags=["ops"])


@router.get("/status", response_model=ReleasePolicyResponse, dependencies=[Depends(require_ops_token)])
def status(db: Session = Depends(get_db)):
    policy = ensure_release_policy(db)
    return ReleasePolicyResponse(
        latest_version=policy.latest_version,
        min_supported_version=policy.min_supported_version,
        enforce_after=policy.enforce_after,
        updated_by=policy.updated_by,
        updated_at=policy.updated_at,
    )


@router.post("/activate", response_model=ReleasePolicyResponse, dependencies=[Depends(require_ops_token)])
async def activate(payload: ActivateReleaseRequest, db: Session = Depends(get_db)):
    policy = activate_release(
        db=db,
        latest_version=payload.latest_version,
        min_supported_version=payload.min_supported_version,
        grace_minutes=payload.grace_minutes,
        updated_by="github-actions",
    )
    await realtime_hub.notify_force_update(
        min_supported_version=policy.min_supported_version,
        enforce_after_iso=policy.enforce_after.isoformat() if policy.enforce_after else None,
    )
    return ReleasePolicyResponse(
        latest_version=policy.latest_version,
        min_supported_version=policy.min_supported_version,
        enforce_after=policy.enforce_after,
        updated_by=policy.updated_by,
        updated_at=policy.updated_at,
    )
