from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.character import Character
from app.models.publish_drain import PublishDrainEvent, PublishDrainSessionAudit
from app.models.session import UserSession
from app.models.user import User
from app.services.observability import record_forced_logout_event

DRAIN_STATUS_DRAINING = "draining"
DRAIN_STATUS_COMPLETED = "completed"
DRAIN_STATUS_FAILED = "failed"

SESSION_DRAIN_STATE_ACTIVE = "active"
SESSION_DRAIN_STATE_DRAINING = "draining"
SESSION_DRAIN_STATE_COMPLETED = "completed"


class PublishDrainConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class SessionDrainDecision:
    force_logout: bool
    event_id: int | None
    reason_code: str | None
    deadline_at: datetime | None
    seconds_remaining: int | None


def _now_utc() -> datetime:
    return datetime.now(UTC)


def list_recent_publish_drains(db: Session, limit: int = 30) -> list[PublishDrainEvent]:
    safe_limit = max(1, min(limit, 200))
    return (
        db.execute(select(PublishDrainEvent).order_by(PublishDrainEvent.id.desc()).limit(safe_limit))
        .scalars()
        .all()
    )


def finalize_due_publish_drains(db: Session) -> list[PublishDrainEvent]:
    now = _now_utc()
    events = (
        db.execute(
            select(PublishDrainEvent)
            .where(
                PublishDrainEvent.status == DRAIN_STATUS_DRAINING,
                PublishDrainEvent.deadline_at <= now,
            )
            .order_by(PublishDrainEvent.deadline_at.asc(), PublishDrainEvent.id.asc())
        )
        .scalars()
        .all()
    )
    finalized: list[PublishDrainEvent] = []
    for row in events:
        finished = finalize_publish_drain(db, row.id, cutoff=now)
        if finished is not None:
            finalized.append(finished)
    return finalized


def _active_drain_count(db: Session) -> int:
    return (
        db.execute(
            select(func.count(PublishDrainEvent.id)).where(PublishDrainEvent.status == DRAIN_STATUS_DRAINING)
        ).scalar_one()
        or 0
    )


def ensure_publish_drain_capacity(db: Session) -> None:
    if not settings.publish_drain_enabled:
        return
    if _active_drain_count(db) >= max(1, settings.publish_drain_max_concurrent):
        raise PublishDrainConflictError("A publish drain is already active.")


def _flush_user_presence(db: Session, user_id: int) -> tuple[bool, str]:
    try:
        rows = (
            db.execute(
                select(Character).where(
                    Character.user_id == user_id,
                    Character.is_selected.is_(True),
                )
            )
            .scalars()
            .all()
        )
        for row in rows:
            row.is_selected = False
            db.add(row)
        return True, ""
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"flush_failed:{type(exc).__name__}"


def start_publish_drain(
    db: Session,
    *,
    trigger_type: str,
    reason_code: str,
    initiated_by: str,
    content_version_id: int | None,
    content_version_key: str,
    build_version: str | None,
    grace_minutes: int,
    notes: str = "",
) -> PublishDrainEvent | None:
    if not settings.publish_drain_enabled:
        return None

    ensure_publish_drain_capacity(db)

    now = _now_utc()
    grace_seconds = max(0, grace_minutes) * 60
    deadline = now + timedelta(seconds=grace_seconds)
    normalized_content_key = (content_version_key or "").strip() or "unknown"

    event = PublishDrainEvent(
        trigger_type=(trigger_type or "publish").strip() or "publish",
        reason_code=(reason_code or "publish").strip() or "publish",
        initiated_by=(initiated_by or "system").strip() or "system",
        content_version_id=content_version_id,
        content_version_key=normalized_content_key,
        build_version=(build_version or "").strip() or None,
        grace_seconds=grace_seconds,
        deadline_at=deadline,
        status=DRAIN_STATUS_DRAINING,
        notes=(notes or "").strip(),
    )
    db.add(event)
    db.flush()

    session_rows = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(
            User.is_admin.is_(False),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    ).all()
    user_flush_result: dict[int, tuple[bool, str]] = {}
    targeted = 0
    persisted_ok = 0
    persisted_failed = 0

    for session, user in session_rows:
        targeted += 1
        flush_ok, flush_detail = user_flush_result.get(user.id, (True, ""))
        if user.id not in user_flush_result:
            flush_ok, flush_detail = _flush_user_presence(db, user.id)
            user_flush_result[user.id] = (flush_ok, flush_detail)

        session.drain_state = SESSION_DRAIN_STATE_DRAINING
        session.drain_event_id = event.id
        session.drain_deadline_at = deadline
        session.drain_reason_code = event.reason_code
        db.add(session)

        if flush_ok:
            persisted_ok += 1
        else:
            persisted_failed += 1
        db.add(
            PublishDrainSessionAudit(
                event_id=event.id,
                session_id=session.id,
                user_id=session.user_id,
                persisted_ok=flush_ok,
                despawned_ok=flush_ok,
                revoked_ok=False,
                detail=flush_detail,
            )
        )

    event.sessions_targeted = targeted
    event.sessions_persisted = persisted_ok
    event.sessions_persist_failed = persisted_failed
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def finalize_publish_drain(db: Session, event_id: int, *, cutoff: datetime | None = None) -> PublishDrainEvent | None:
    event = db.get(PublishDrainEvent, event_id)
    if event is None:
        return None
    if event.status != DRAIN_STATUS_DRAINING:
        return event

    cutoff_at = cutoff or _now_utc()
    rows = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(
            User.is_admin.is_(False),
            UserSession.drain_event_id == event.id,
            UserSession.revoked_at.is_(None),
        )
    ).all()

    revoked_count = 0
    for session, _user in rows:
        session.revoked_at = cutoff_at
        session.drain_state = SESSION_DRAIN_STATE_COMPLETED
        db.add(session)
        revoked_count += 1
        audit = db.execute(
            select(PublishDrainSessionAudit).where(
                PublishDrainSessionAudit.event_id == event.id,
                PublishDrainSessionAudit.session_id == session.id,
            )
        ).scalar_one_or_none()
        if audit is not None:
            audit.revoked_ok = True
            db.add(audit)

    event.sessions_revoked += revoked_count
    event.status = DRAIN_STATUS_COMPLETED
    event.cutoff_at = cutoff_at
    db.add(event)
    db.commit()
    if revoked_count > 0:
        for _ in range(revoked_count):
            record_forced_logout_event()
    db.refresh(event)
    return event


def enforce_session_drain(db: Session, session: UserSession, user: User) -> SessionDrainDecision | None:
    if user.is_admin:
        return None
    if session.drain_state != SESSION_DRAIN_STATE_DRAINING:
        return None
    now = _now_utc()
    deadline = session.drain_deadline_at
    if deadline is None:
        return SessionDrainDecision(
            force_logout=False,
            event_id=session.drain_event_id,
            reason_code=session.drain_reason_code,
            deadline_at=None,
            seconds_remaining=None,
        )
    if now < deadline:
        return SessionDrainDecision(
            force_logout=False,
            event_id=session.drain_event_id,
            reason_code=session.drain_reason_code,
            deadline_at=deadline,
            seconds_remaining=max(0, int((deadline - now).total_seconds())),
        )

    newly_revoked = session.revoked_at is None
    session.revoked_at = now
    session.drain_state = SESSION_DRAIN_STATE_COMPLETED
    db.add(session)

    if session.drain_event_id:
        event = db.get(PublishDrainEvent, session.drain_event_id)
        if event is not None:
            if newly_revoked:
                event.sessions_revoked += 1
            if event.status == DRAIN_STATUS_DRAINING and event.deadline_at <= now:
                event.status = DRAIN_STATUS_COMPLETED
                event.cutoff_at = now
            db.add(event)
        audit = db.execute(
            select(PublishDrainSessionAudit).where(
                PublishDrainSessionAudit.event_id == session.drain_event_id,
                PublishDrainSessionAudit.session_id == session.id,
            )
        ).scalar_one_or_none()
        if audit is not None:
            audit.revoked_ok = True
            db.add(audit)

    db.commit()
    if newly_revoked:
        record_forced_logout_event()
    return SessionDrainDecision(
        force_logout=True,
        event_id=session.drain_event_id,
        reason_code=session.drain_reason_code,
        deadline_at=deadline,
        seconds_remaining=0,
    )


async def run_publish_drain_countdown(event_id: int) -> None:
    from app.db.session import SessionLocal
    from app.services.realtime import realtime_hub

    db = SessionLocal()
    try:
        event = db.get(PublishDrainEvent, event_id)
        if event is None or event.status != DRAIN_STATUS_DRAINING:
            return
        now = _now_utc()
        seconds_until_deadline = max(0, int((event.deadline_at - now).total_seconds()))
        await realtime_hub.notify_content_publish_started(
            event_id=event.id,
            content_version_key=event.content_version_key,
            reason_code=event.reason_code,
            deadline_iso=event.deadline_at.isoformat(),
            grace_seconds=event.grace_seconds,
        )
    finally:
        db.close()

    warning_thresholds = [300, 120, 60, 30, 10]
    remaining = seconds_until_deadline
    for threshold in warning_thresholds:
        if remaining <= threshold:
            continue
        await asyncio.sleep(max(0, remaining - threshold))
        remaining = threshold
        await realtime_hub.notify_content_publish_warning(
            event_id=event_id,
            content_version_key=event.content_version_key,
            reason_code=event.reason_code,
            deadline_iso=event.deadline_at.isoformat(),
            seconds_remaining=threshold,
        )

    if remaining > 0:
        await asyncio.sleep(remaining)

    db = SessionLocal()
    try:
        finalized = finalize_publish_drain(db, event_id)
        if finalized is None:
            return
        await realtime_hub.notify_content_publish_forced_logout(
            event_id=finalized.id,
            content_version_key=finalized.content_version_key,
            reason_code=finalized.reason_code,
            cutoff_iso=finalized.cutoff_at.isoformat() if finalized.cutoff_at else None,
        )
    finally:
        db.close()
