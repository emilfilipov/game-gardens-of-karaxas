from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from packaging.version import InvalidVersion, Version
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import ContentVersion
from app.models.release_policy import ReleasePolicy
from app.models.release_record import ReleaseRecord


@dataclass
class VersionDecision:
    client_version: str
    latest_version: str
    min_supported_version: str
    client_content_version_key: str
    latest_content_version_key: str
    min_supported_content_version_key: str
    update_feed_url: str | None
    enforce_after: datetime | None
    update_available: bool
    content_update_available: bool
    force_update: bool


def _safe_version(raw: str | None) -> Version:
    value = raw or "0.0.0"
    try:
        return Version(value)
    except InvalidVersion:
        return Version("0.0.0")


def _normalize_content_key(raw: str | None) -> str:
    return (raw or "").strip() or "unknown"


def resolve_active_content_version_key(db: Session) -> str:
    row = db.execute(
        select(ContentVersion.version_key)
        .where(ContentVersion.state == "active")
        .order_by(ContentVersion.activated_at.desc().nullslast(), ContentVersion.id.desc())
    ).scalar_one_or_none()
    return _normalize_content_key(row) if row else "cv_bootstrap_v1"


def ensure_release_policy(db: Session) -> ReleasePolicy:
    policy = db.get(ReleasePolicy, 1)
    active_content_key = resolve_active_content_version_key(db)
    if policy is None:
        policy = ReleasePolicy(
            id=1,
            latest_version="0.0.0",
            min_supported_version="0.0.0",
            latest_content_version_key=active_content_key,
            min_supported_content_version_key=active_content_key,
            updated_by="bootstrap",
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    changed = False
    if _normalize_content_key(policy.latest_content_version_key) == "unknown":
        policy.latest_content_version_key = active_content_key
        changed = True
    if _normalize_content_key(policy.min_supported_content_version_key) == "unknown":
        policy.min_supported_content_version_key = active_content_key
        changed = True
    if changed:
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


def evaluate_version(
    policy: ReleasePolicy,
    client_version: str | None,
    client_content_version_key: str | None,
) -> VersionDecision:
    now = datetime.now(UTC)
    normalized_client_version = client_version or "0.0.0"
    normalized_client_content_key = _normalize_content_key(client_content_version_key)
    latest = _safe_version(policy.latest_version)
    minimum = _safe_version(policy.min_supported_version)
    client = _safe_version(normalized_client_version)
    latest_content_key = _normalize_content_key(policy.latest_content_version_key)
    min_content_key = _normalize_content_key(policy.min_supported_content_version_key)

    build_update_available = client < latest
    content_update_available = normalized_client_content_key != latest_content_key
    update_available = build_update_available or content_update_available

    build_force_candidate = client < minimum
    content_force_candidate = normalized_client_content_key != min_content_key
    force_update = (
        (build_force_candidate or content_force_candidate)
        and policy.enforce_after is not None
        and now >= policy.enforce_after
    )

    return VersionDecision(
        client_version=normalized_client_version,
        latest_version=policy.latest_version,
        min_supported_version=policy.min_supported_version,
        client_content_version_key=normalized_client_content_key,
        latest_content_version_key=latest_content_key,
        min_supported_content_version_key=min_content_key,
        update_feed_url=(policy.update_feed_url or "").strip() or None,
        enforce_after=policy.enforce_after,
        update_available=update_available,
        content_update_available=content_update_available,
        force_update=force_update,
    )


def activate_release(
    db: Session,
    latest_version: str,
    min_supported_version: str | None,
    latest_content_version_key: str | None,
    min_supported_content_version_key: str | None,
    update_feed_url: str | None,
    build_release_notes: str,
    user_facing_notes: str,
    grace_minutes: int | None,
    updated_by: str,
) -> ReleasePolicy:
    policy = ensure_release_policy(db)
    resolved_latest_content_key = _normalize_content_key(latest_content_version_key)
    if resolved_latest_content_key == "unknown":
        resolved_latest_content_key = resolve_active_content_version_key(db)
    resolved_min_content_key = _normalize_content_key(min_supported_content_version_key)
    if resolved_min_content_key == "unknown":
        resolved_min_content_key = resolved_latest_content_key

    policy.latest_version = latest_version
    policy.min_supported_version = min_supported_version or latest_version
    policy.latest_content_version_key = resolved_latest_content_key
    policy.min_supported_content_version_key = resolved_min_content_key
    policy.update_feed_url = (update_feed_url or "").strip() or None
    minutes = grace_minutes if grace_minutes is not None else settings.version_grace_minutes_default
    policy.enforce_after = datetime.now(UTC) + timedelta(minutes=minutes)
    policy.updated_by = updated_by
    db.add(policy)

    db.add(
        ReleaseRecord(
            build_version=policy.latest_version,
            min_supported_version=policy.min_supported_version,
            content_version_key=policy.latest_content_version_key,
            min_supported_content_version_key=policy.min_supported_content_version_key,
            update_feed_url=policy.update_feed_url,
            build_release_notes=(build_release_notes or "").strip(),
            user_facing_notes=(user_facing_notes or "").strip(),
            activated_by=updated_by,
            enforce_after=policy.enforce_after,
        )
    )

    db.commit()
    db.refresh(policy)
    return policy


def get_latest_release_record(db: Session) -> ReleaseRecord | None:
    return db.execute(select(ReleaseRecord).order_by(ReleaseRecord.activated_at.desc(), ReleaseRecord.id.desc())).scalars().first()


def get_release_record_for_build(db: Session, build_version: str | None) -> ReleaseRecord | None:
    normalized = (build_version or "").strip()
    if not normalized:
        return None
    return db.execute(
        select(ReleaseRecord)
        .where(ReleaseRecord.build_version == normalized)
        .order_by(ReleaseRecord.activated_at.desc(), ReleaseRecord.id.desc())
    ).scalars().first()
