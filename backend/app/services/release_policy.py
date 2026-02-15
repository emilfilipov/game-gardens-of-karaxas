from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from packaging.version import InvalidVersion, Version
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.release_policy import ReleasePolicy


@dataclass
class VersionDecision:
    client_version: str
    latest_version: str
    min_supported_version: str
    enforce_after: datetime | None
    update_available: bool
    force_update: bool


def _safe_version(raw: str | None) -> Version:
    value = raw or "0.0.0"
    try:
        return Version(value)
    except InvalidVersion:
        return Version("0.0.0")


def ensure_release_policy(db: Session) -> ReleasePolicy:
    policy = db.get(ReleasePolicy, 1)
    if policy is None:
        policy = ReleasePolicy(
            id=1,
            latest_version="0.0.0",
            min_supported_version="0.0.0",
            updated_by="bootstrap",
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


def evaluate_version(policy: ReleasePolicy, client_version: str | None) -> VersionDecision:
    now = datetime.now(UTC)
    normalized_client_version = client_version or "0.0.0"
    latest = _safe_version(policy.latest_version)
    minimum = _safe_version(policy.min_supported_version)
    client = _safe_version(normalized_client_version)
    update_available = client < latest
    force_update = client < minimum and policy.enforce_after is not None and now >= policy.enforce_after
    return VersionDecision(
        client_version=normalized_client_version,
        latest_version=policy.latest_version,
        min_supported_version=policy.min_supported_version,
        enforce_after=policy.enforce_after,
        update_available=update_available,
        force_update=force_update,
    )


def activate_release(
    db: Session,
    latest_version: str,
    min_supported_version: str | None,
    grace_minutes: int | None,
    updated_by: str,
) -> ReleasePolicy:
    policy = ensure_release_policy(db)
    policy.latest_version = latest_version
    policy.min_supported_version = min_supported_version or latest_version
    minutes = grace_minutes if grace_minutes is not None else settings.version_grace_minutes_default
    policy.enforce_after = datetime.now(UTC) + timedelta(minutes=minutes)
    policy.updated_by = updated_by
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy
