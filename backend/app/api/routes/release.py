from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_client_content_version, get_client_version, get_db
from app.models.content import ContentVersion
from app.schemas.release import ReleaseSummaryResponse
from app.services.release_policy import (
    ensure_release_policy,
    evaluate_version,
    get_latest_release_record,
    get_release_record_for_build,
)

router = APIRouter(prefix="/release", tags=["release"])


def _content_note_by_version_key(db: Session, version_key: str | None) -> str:
    normalized = (version_key or "").strip()
    if not normalized:
        return ""
    row = db.execute(select(ContentVersion.note).where(ContentVersion.version_key == normalized)).scalar_one_or_none()
    return (row or "").strip()


@router.get("/summary", response_model=ReleaseSummaryResponse)
def release_summary(
    db: Session = Depends(get_db),
    client_version: str | None = Depends(get_client_version),
    client_content_version_key: str | None = Depends(get_client_content_version),
):
    policy = ensure_release_policy(db)
    decision = evaluate_version(policy, client_version, client_content_version_key)
    latest_record = get_latest_release_record(db)
    client_record = get_release_record_for_build(db, decision.client_version)

    return ReleaseSummaryResponse(
        client_version=decision.client_version,
        latest_version=decision.latest_version,
        min_supported_version=decision.min_supported_version,
        client_content_version_key=decision.client_content_version_key,
        latest_content_version_key=decision.latest_content_version_key,
        min_supported_content_version_key=decision.min_supported_content_version_key,
        enforce_after=decision.enforce_after,
        update_available=decision.update_available,
        content_update_available=decision.content_update_available,
        force_update=decision.force_update,
        update_feed_url=decision.update_feed_url,
        latest_build_release_notes=(latest_record.build_release_notes if latest_record else ""),
        latest_user_facing_notes=(latest_record.user_facing_notes if latest_record else ""),
        client_build_release_notes=(client_record.build_release_notes if client_record else ""),
        latest_content_note=_content_note_by_version_key(db, decision.latest_content_version_key),
        client_content_note=_content_note_by_version_key(db, decision.client_content_version_key),
        latest_published_at=(latest_record.activated_at if latest_record else None),
    )
