from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_db, require_admin_context
from app.core.config import settings
from app.models.content import ContentVersion
from app.schemas.content import (
    ContentBootstrapResponse,
    ContentBundleUpsertRequest,
    ContentPublishDrainSummaryResponse,
    ContentValidationIssueResponse,
    ContentValidationResponse,
    ContentVersionCreateRequest,
    ContentVersionDetailResponse,
    ContentVersionSummaryResponse,
)
from app.services.content import (
    CONTENT_SCHEMA_VERSION,
    CONTENT_STATE_ACTIVE,
    CONTENT_STATE_RETIRED,
    activate_version,
    content_contract_signature,
    create_draft_from_active,
    get_active_snapshot,
    get_content_version_domains,
    get_content_version_or_none,
    list_content_versions,
    upsert_version_bundle,
    validate_version,
)
from app.services.admin_audit import write_admin_audit
from app.services.realtime import realtime_hub
from app.services.release_policy import ensure_release_policy
from app.services.session_drain import (
    PublishDrainConflictError,
    ensure_publish_drain_capacity,
    list_recent_publish_drains,
    run_publish_drain_countdown,
    start_publish_drain,
)

router = APIRouter(prefix="/content", tags=["content"])


def _to_summary(version) -> ContentVersionSummaryResponse:
    return ContentVersionSummaryResponse(
        id=version.id,
        version_key=version.version_key,
        state=version.state,
        note=version.note or "",
        created_by_user_id=version.created_by_user_id,
        created_at=version.created_at,
        validated_at=version.validated_at,
        activated_at=version.activated_at,
        updated_at=version.updated_at,
    )


def _to_detail(version, domains: dict[str, dict]) -> ContentVersionDetailResponse:
    summary = _to_summary(version)
    return ContentVersionDetailResponse(**summary.model_dump(), domains=domains)


def _to_publish_drain_summary(row) -> ContentPublishDrainSummaryResponse:
    return ContentPublishDrainSummaryResponse(
        id=row.id,
        trigger_type=row.trigger_type,
        reason_code=row.reason_code,
        initiated_by=row.initiated_by,
        content_version_id=row.content_version_id,
        content_version_key=row.content_version_key,
        build_version=row.build_version,
        grace_seconds=row.grace_seconds,
        started_at=row.started_at,
        deadline_at=row.deadline_at,
        cutoff_at=row.cutoff_at,
        status=row.status,
        sessions_targeted=row.sessions_targeted,
        sessions_persisted=row.sessions_persisted,
        sessions_persist_failed=row.sessions_persist_failed,
        sessions_revoked=row.sessions_revoked,
    )


def _ensure_content_phase_for_write(*, requires_drain: bool = False) -> None:
    phase = (settings.content_feature_phase or "").strip().lower()
    if phase in {"", "drain_enforced"}:
        return
    if phase == "snapshot_readonly":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Content writes are disabled in current rollout phase.", "code": "content_phase_readonly"},
        )
    if phase == "snapshot_runtime" and requires_drain:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Content activation is disabled until drain-enforced phase.",
                "code": "content_phase_activation_disabled",
            },
        )


async def _apply_publish_policy_and_drain(
    *,
    db: Session,
    user_id: int,
    content_version_id: int,
    content_version_key: str,
    content_note: str,
    reason_code: str,
) -> None:
    policy = ensure_release_policy(db)
    policy.latest_content_version_key = content_version_key
    policy.min_supported_content_version_key = content_version_key
    policy.enforce_after = datetime.now(UTC) + timedelta(minutes=settings.version_grace_minutes_default)
    policy.updated_by = f"user:{user_id}"
    db.add(policy)

    try:
        drain_event = start_publish_drain(
            db,
            trigger_type=reason_code,
            reason_code=reason_code,
            initiated_by=f"user:{user_id}",
            content_version_id=content_version_id,
            content_version_key=content_version_key,
            build_version=policy.latest_version,
            grace_minutes=settings.version_grace_minutes_default,
            notes=content_note or "",
        )
    except PublishDrainConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "publish_drain_locked"},
        ) from exc
    if drain_event is not None:
        asyncio.create_task(run_publish_drain_countdown(drain_event.id))

    await realtime_hub.notify_force_update(
        min_supported_version=policy.min_supported_version,
        min_supported_content_version_key=policy.min_supported_content_version_key,
        enforce_after_iso=policy.enforce_after.isoformat() if policy.enforce_after else None,
        update_feed_url=policy.update_feed_url,
    )


@router.get("/bootstrap", response_model=ContentBootstrapResponse)
def bootstrap_content(db: Session = Depends(get_db)):
    snapshot = get_active_snapshot(db)
    return ContentBootstrapResponse(
        content_schema_version=CONTENT_SCHEMA_VERSION,
        content_contract_signature=content_contract_signature(),
        content_version_id=snapshot.content_version_id,
        content_version_key=snapshot.content_version_key,
        fetched_at=snapshot.loaded_at,
        domains=snapshot.domains,
    )


@router.get("/versions", response_model=list[ContentVersionSummaryResponse])
def admin_list_content_versions(context: AuthContext = Depends(require_admin_context), db: Session = Depends(get_db)):
    rows = list_content_versions(db)
    return [_to_summary(row) for row in rows]


@router.get("/publish-drains", response_model=list[ContentPublishDrainSummaryResponse])
def admin_list_publish_drains(
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    rows = list_recent_publish_drains(db)
    return [_to_publish_drain_summary(row) for row in rows]


@router.get("/versions/{version_id}", response_model=ContentVersionDetailResponse)
def admin_get_content_version(
    version_id: int,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    domains = get_content_version_domains(db, version.id)
    return _to_detail(version, domains)


@router.post("/versions", response_model=ContentVersionDetailResponse)
def admin_create_content_version(
    payload: ContentVersionCreateRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    _ensure_content_phase_for_write()
    version = create_draft_from_active(
        db,
        created_by_user_id=context.user.id,
        note=payload.note,
    )
    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="content_version_create",
        target_type="content_version",
        target_id=str(version.id),
        summary=f"Created draft {version.version_key}",
    )
    domains = get_content_version_domains(db, version.id)
    return _to_detail(version, domains)


@router.put("/versions/{version_id}/bundles/{domain}", response_model=ContentValidationResponse)
def admin_upsert_content_bundle(
    version_id: int,
    domain: str,
    payload: ContentBundleUpsertRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    _ensure_content_phase_for_write()
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    if version.state == CONTENT_STATE_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Active content versions are immutable", "code": "content_active_immutable"},
        )
    if version.state == CONTENT_STATE_RETIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Retired content versions are immutable", "code": "content_retired_immutable"},
        )

    issues = upsert_version_bundle(db, version=version, domain=domain.strip(), payload=payload.payload)
    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="content_bundle_upsert",
        target_type="content_version",
        target_id=str(version.id),
        summary=f"Domain={domain.strip()} issues={len(issues)}",
    )
    refreshed = get_content_version_or_none(db, version_id)
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state if refreshed else version.state,
    )


@router.post("/versions/{version_id}/validate", response_model=ContentValidationResponse)
def admin_validate_content_version(
    version_id: int,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    _ensure_content_phase_for_write()
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    issues = validate_version(db, version)
    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="content_version_validate",
        target_type="content_version",
        target_id=str(version.id),
        summary=f"Issues={len(issues)}",
    )
    refreshed = get_content_version_or_none(db, version_id) or version
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state,
    )


@router.post("/versions/{version_id}/activate", response_model=ContentValidationResponse)
async def admin_activate_content_version(
    version_id: int,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    _ensure_content_phase_for_write(requires_drain=True)
    try:
        ensure_publish_drain_capacity(db)
    except PublishDrainConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "publish_drain_locked"},
        ) from exc
    version = get_content_version_or_none(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Content version not found", "code": "content_version_not_found"},
        )
    issues = activate_version(db, version)
    refreshed = get_content_version_or_none(db, version_id) or version
    if not issues and refreshed.state == CONTENT_STATE_ACTIVE:
        await _apply_publish_policy_and_drain(
            db=db,
            user_id=context.user.id,
            content_version_id=refreshed.id,
            content_version_key=refreshed.version_key,
            content_note=refreshed.note or "",
            reason_code="content_publish",
        )
    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="content_version_activate",
        target_type="content_version",
        target_id=str(version_id),
        summary=f"Issues={len(issues)} state={refreshed.state}",
    )
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state,
    )


@router.post("/versions/rollback/previous", response_model=ContentValidationResponse)
async def admin_rollback_previous_version(
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    _ensure_content_phase_for_write(requires_drain=True)
    try:
        ensure_publish_drain_capacity(db)
    except PublishDrainConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "code": "publish_drain_locked"},
        ) from exc
    active = db.execute(
        select(ContentVersion)
        .where(ContentVersion.state == CONTENT_STATE_ACTIVE)
        .order_by(ContentVersion.activated_at.desc().nullslast(), ContentVersion.id.desc())
    ).scalars().first()
    if active is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No active content version found", "code": "content_active_not_found"},
        )
    previous = db.execute(
        select(ContentVersion)
        .where(ContentVersion.id != active.id)
        .order_by(ContentVersion.activated_at.desc().nullslast(), ContentVersion.id.desc())
    ).scalars().first()
    if previous is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No previous content version found", "code": "content_previous_not_found"},
        )

    issues = activate_version(db, previous)
    refreshed = get_content_version_or_none(db, previous.id) or previous
    if not issues and refreshed.state == CONTENT_STATE_ACTIVE:
        await _apply_publish_policy_and_drain(
            db=db,
            user_id=context.user.id,
            content_version_id=refreshed.id,
            content_version_key=refreshed.version_key,
            content_note=f"Rollback to {refreshed.version_key}",
            reason_code="content_rollback",
        )
    write_admin_audit(
        db,
        actor=f"user:{context.user.id}",
        action="content_version_rollback",
        target_type="content_version",
        target_id=str(previous.id),
        summary=f"Issues={len(issues)} state={refreshed.state}",
    )
    return ContentValidationResponse(
        ok=len(issues) == 0,
        issues=[ContentValidationIssueResponse(domain=issue.domain, message=issue.message) for issue in issues],
        state=refreshed.state,
    )
