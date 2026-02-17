from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_ops_token
from app.schemas.ops import ActivateReleaseRequest, ReleasePolicyResponse
from app.services.realtime import realtime_hub
from app.services.release_policy import activate_release, ensure_release_policy
from app.services.session_drain import (
    PublishDrainConflictError,
    ensure_publish_drain_capacity,
    run_publish_drain_countdown,
    start_publish_drain,
)

router = APIRouter(prefix="/ops/release", tags=["ops"])


@router.get("/status", response_model=ReleasePolicyResponse, dependencies=[Depends(require_ops_token)])
def status(db: Session = Depends(get_db)):
    policy = ensure_release_policy(db)
    return ReleasePolicyResponse(
        latest_version=policy.latest_version,
        min_supported_version=policy.min_supported_version,
        latest_content_version_key=policy.latest_content_version_key,
        min_supported_content_version_key=policy.min_supported_content_version_key,
        update_feed_url=policy.update_feed_url,
        enforce_after=policy.enforce_after,
        updated_by=policy.updated_by,
        updated_at=policy.updated_at,
    )


@router.post("/activate", response_model=ReleasePolicyResponse, dependencies=[Depends(require_ops_token)])
async def activate(payload: ActivateReleaseRequest, db: Session = Depends(get_db)):
    try:
        ensure_publish_drain_capacity(db)
    except PublishDrainConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "publish_drain_locked"},
        ) from exc
    policy = activate_release(
        db=db,
        latest_version=payload.latest_version,
        min_supported_version=payload.min_supported_version,
        latest_content_version_key=payload.latest_content_version_key,
        min_supported_content_version_key=payload.min_supported_content_version_key,
        update_feed_url=payload.update_feed_url,
        build_release_notes=payload.build_release_notes,
        user_facing_notes=payload.user_facing_notes,
        grace_minutes=payload.grace_minutes,
        updated_by="release-pipeline",
    )
    try:
        drain_event = start_publish_drain(
            db,
            trigger_type="release_activate",
            reason_code="release_activate",
            initiated_by="release-pipeline",
            content_version_id=None,
            content_version_key=policy.latest_content_version_key,
            build_version=policy.latest_version,
            grace_minutes=payload.grace_minutes,
            notes=payload.user_facing_notes,
        )
    except PublishDrainConflictError:
        # Capacity is checked above and this path is defensive-only.
        drain_event = None

    if drain_event is not None:
        asyncio.create_task(run_publish_drain_countdown(drain_event.id))
    await realtime_hub.notify_force_update(
        min_supported_version=policy.min_supported_version,
        min_supported_content_version_key=policy.min_supported_content_version_key,
        enforce_after_iso=policy.enforce_after.isoformat() if policy.enforce_after else None,
        update_feed_url=policy.update_feed_url,
    )
    return ReleasePolicyResponse(
        latest_version=policy.latest_version,
        min_supported_version=policy.min_supported_version,
        latest_content_version_key=policy.latest_content_version_key,
        min_supported_content_version_key=policy.min_supported_content_version_key,
        update_feed_url=policy.update_feed_url,
        enforce_after=policy.enforce_after,
        updated_by=policy.updated_by,
        updated_at=policy.updated_at,
    )
