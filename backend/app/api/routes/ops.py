from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_ops_token
from app.core.config import settings
from app.models.admin_audit import AdminActionAudit
from app.schemas.ops import ActivateReleaseRequest, ReleasePolicyResponse
from app.services.admin_audit import write_admin_audit
from app.services.content import get_active_snapshot
from app.services.observability import build_publish_drain_metrics, snapshot_latency_stats
from app.services.rate_limit import rate_limiter
from app.services.realtime import realtime_hub
from app.services.release_policy import activate_release, ensure_release_policy
from app.services.security_events import list_security_events, security_event_stats
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


@router.get("/feature-flags", dependencies=[Depends(require_ops_token)])
def feature_flags():
    return {
        "content_feature_phase": settings.content_feature_phase,
        "security_feature_phase": settings.security_feature_phase,
        "publish_drain_enabled": settings.publish_drain_enabled,
        "publish_drain_max_concurrent": settings.publish_drain_max_concurrent,
        "request_rate_limit_enabled": settings.request_rate_limit_enabled,
    }


@router.get("/metrics", dependencies=[Depends(require_ops_token)])
def metrics(db: Session = Depends(get_db)):
    snapshot = get_active_snapshot(db)
    policy = ensure_release_policy(db)
    return {
        "active_content_version_key": snapshot.content_version_key,
        "release_policy": {
            "latest_version": policy.latest_version,
            "min_supported_version": policy.min_supported_version,
            "latest_content_version_key": policy.latest_content_version_key,
            "min_supported_content_version_key": policy.min_supported_content_version_key,
            "enforce_after": policy.enforce_after.isoformat() if policy.enforce_after else None,
        },
        "snapshot_latency_ms": snapshot_latency_stats(),
        "publish_drain": build_publish_drain_metrics(db),
        "rate_limiter": rate_limiter.stats(),
        "security_events": security_event_stats(db),
    }


@router.get("/admin-audit", dependencies=[Depends(require_ops_token)])
def admin_audit_log(db: Session = Depends(get_db), limit: int = 100):
    safe_limit = max(1, min(limit, 500))
    rows = (
        db.execute(select(AdminActionAudit).order_by(AdminActionAudit.id.desc()).limit(safe_limit))
        .scalars()
        .all()
    )
    return [
        {
            "id": row.id,
            "actor": row.actor,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "summary": row.summary,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/security-audit", dependencies=[Depends(require_ops_token)])
def security_audit_log(
    db: Session = Depends(get_db),
    limit: int = 200,
    event_type: str | None = None,
):
    rows = list_security_events(db, limit=limit, event_type=event_type)
    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "session_id": row.session_id,
            "event_type": row.event_type,
            "severity": row.severity,
            "ip_address": row.ip_address,
            "detail": row.detail,
            "created_at": row.created_at,
        }
        for row in rows
    ]


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
    write_admin_audit(
        db,
        actor="release-pipeline",
        action="release_activate",
        target_type="release_policy",
        target_id="1",
        summary=(
            f"latest={policy.latest_version} min={policy.min_supported_version} "
            f"content={policy.latest_content_version_key} grace={payload.grace_minutes}"
        ),
    )
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
