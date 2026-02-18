from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.security_event import SecurityEventAudit


def write_security_event(
    db: Session,
    *,
    event_type: str,
    severity: str = "info",
    actor_user_id: int | None = None,
    session_id: str | None = None,
    ip_address: str | None = None,
    detail: dict[str, Any] | str | None = None,
    commit: bool = False,
) -> None:
    if isinstance(detail, dict):
        detail_text = json.dumps(detail, sort_keys=True, separators=(",", ":"))
    else:
        detail_text = (detail or "").strip()
    db.add(
        SecurityEventAudit(
            actor_user_id=actor_user_id,
            session_id=(session_id or "").strip() or None,
            event_type=(event_type or "unknown").strip() or "unknown",
            severity=(severity or "info").strip().lower() or "info",
            ip_address=(ip_address or "").strip() or None,
            detail=detail_text,
        )
    )
    if commit:
        db.commit()


def list_security_events(
    db: Session,
    *,
    limit: int = 100,
    event_type: str | None = None,
) -> list[SecurityEventAudit]:
    safe_limit = max(1, min(limit, 1000))
    query = select(SecurityEventAudit)
    normalized = (event_type or "").strip()
    if normalized:
        query = query.where(SecurityEventAudit.event_type == normalized)
    return db.execute(query.order_by(SecurityEventAudit.id.desc()).limit(safe_limit)).scalars().all()


def security_event_stats(db: Session) -> dict[str, int]:
    total = db.execute(select(func.count(SecurityEventAudit.id))).scalar_one() or 0
    critical = (
        db.execute(select(func.count(SecurityEventAudit.id)).where(SecurityEventAudit.severity == "critical")).scalar_one()
        or 0
    )
    warning = (
        db.execute(select(func.count(SecurityEventAudit.id)).where(SecurityEventAudit.severity == "warning")).scalar_one()
        or 0
    )
    return {
        "total": int(total),
        "critical": int(critical),
        "warning": int(warning),
    }
