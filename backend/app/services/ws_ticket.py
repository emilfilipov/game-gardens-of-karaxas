from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_refresh_token, hash_token
from app.models.ws_ticket import WsConnectionTicket

WS_TICKET_TTL_SECONDS = 45


class WsTicketError(ValueError):
    pass


@dataclass(frozen=True)
class WsTicketResult:
    user_id: int
    session_id: str


def _now_utc() -> datetime:
    return datetime.now(UTC)


def issue_ws_ticket(db: Session, *, user_id: int, session_id: str, ttl_seconds: int = WS_TICKET_TTL_SECONDS) -> tuple[str, datetime]:
    secret = create_refresh_token()
    ticket_id = uuid4().hex
    expiry = _now_utc() + timedelta(seconds=max(10, ttl_seconds))
    db.add(
        WsConnectionTicket(
            id=ticket_id,
            user_id=user_id,
            session_id=session_id,
            secret_hash=hash_token(secret),
            expires_at=expiry,
        )
    )
    db.commit()
    return f"{ticket_id}.{secret}", expiry


def consume_ws_ticket(db: Session, raw_ticket: str) -> WsTicketResult:
    token = (raw_ticket or "").strip()
    if "." not in token:
        raise WsTicketError("invalid_ticket")
    ticket_id, secret = token.split(".", 1)
    if not ticket_id or not secret:
        raise WsTicketError("invalid_ticket")

    row = db.execute(select(WsConnectionTicket).where(WsConnectionTicket.id == ticket_id)).scalar_one_or_none()
    if row is None:
        raise WsTicketError("invalid_ticket")
    if row.consumed_at is not None:
        raise WsTicketError("ticket_consumed")
    if row.expires_at <= _now_utc():
        raise WsTicketError("ticket_expired")
    if row.secret_hash != hash_token(secret):
        raise WsTicketError("invalid_ticket")

    row.consumed_at = _now_utc()
    db.add(row)
    db.commit()
    return WsTicketResult(user_id=row.user_id, session_id=row.session_id)


def purge_expired_ws_tickets(db: Session) -> int:
    now = _now_utc()
    rows = db.execute(
        select(WsConnectionTicket).where(
            (WsConnectionTicket.expires_at < now) | (WsConnectionTicket.consumed_at.is_not(None))
        )
    ).scalars()
    count = 0
    for row in rows:
        db.delete(row)
        count += 1
    if count:
        db.commit()
    return count
