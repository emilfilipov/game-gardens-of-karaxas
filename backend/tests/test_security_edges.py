import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi import HTTPException

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.db.base import Base  # noqa: E402
from app.api.deps import AuthContext  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.api.routes.auth import _assert_user_mfa, mfa_disable, mfa_enable  # noqa: E402
from app.services.ws_ticket import WsTicketError, consume_ws_ticket, issue_ws_ticket  # noqa: E402


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def test_ws_ticket_is_one_time_use() -> None:
    db = _db_session()
    user = User(email="ticket@test.com", display_name="Ticket", password_hash="x", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    session = UserSession(
        id="ticket-session",
        user_id=user.id,
        refresh_token_hash="hash",
        client_version="1.0.0",
        client_content_version_key="cv_1",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    db.commit()

    raw_ticket, _expiry = issue_ws_ticket(db, user_id=user.id, session_id=session.id, ttl_seconds=30)
    consumed = consume_ws_ticket(db, raw_ticket)
    assert consumed.user_id == user.id
    assert consumed.session_id == session.id

    try:
        consume_ws_ticket(db, raw_ticket)
    except WsTicketError:
        pass
    else:
        assert False, "Expected WsTicketError for replayed ticket"


def test_mfa_disabled_does_not_require_otp_even_if_secret_exists() -> None:
    user = User(
        email="mfa@test.com",
        display_name="MFA",
        password_hash="x",
        is_admin=False,
        mfa_enabled=False,
        mfa_totp_secret="ABCDEF123456",
    )
    _assert_user_mfa(user, None)


def test_mfa_enabled_requires_valid_otp() -> None:
    user = User(
        email="mfa_enabled@test.com",
        display_name="MFA Enabled",
        password_hash="x",
        is_admin=False,
        mfa_enabled=True,
        mfa_totp_secret="ABCDEF123456",
    )
    try:
        _assert_user_mfa(user, None)
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail["code"] == "invalid_mfa_code"
    else:
        assert False, "Expected HTTPException for missing OTP when MFA is enabled"


def test_mfa_toggle_endpoints_accept_empty_payload() -> None:
    db = _db_session()
    user = User(
        email="toggle@test.com",
        display_name="Toggle",
        password_hash="x",
        is_admin=False,
        mfa_enabled=False,
        mfa_totp_secret=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    session = UserSession(
        id="toggle-session",
        user_id=user.id,
        refresh_token_hash="hash",
        client_version="1.0.0",
        client_content_version_key="cv_1",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    db.commit()

    context = AuthContext(user=user, session=session, version_status=None)
    enabled = mfa_enable(None, context=context, db=db)
    assert enabled.enabled is True
    assert enabled.configured is True
    db.refresh(user)
    assert user.mfa_enabled is True
    assert bool((user.mfa_totp_secret or "").strip()) is True

    disabled = mfa_disable(None, context=context, db=db)
    assert disabled.enabled is False
    assert disabled.configured is True
    db.refresh(user)
    assert user.mfa_enabled is False
