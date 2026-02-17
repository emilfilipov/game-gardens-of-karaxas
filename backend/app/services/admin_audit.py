from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.admin_audit import AdminActionAudit


def write_admin_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    target_type: str,
    target_id: str | None = None,
    summary: str = "",
) -> None:
    db.add(
        AdminActionAudit(
            actor=(actor or "system").strip() or "system",
            action=(action or "unknown").strip() or "unknown",
            target_type=(target_type or "unknown").strip() or "unknown",
            target_id=(target_id or "").strip() or None,
            summary=(summary or "").strip(),
        )
    )
    db.commit()

