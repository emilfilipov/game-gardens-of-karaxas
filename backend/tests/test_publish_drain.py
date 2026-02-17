import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.db.base import Base  # noqa: E402
from app.models.character import Character  # noqa: E402
from app.models.publish_drain import PublishDrainEvent  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.session_drain import (  # noqa: E402
    DRAIN_STATUS_DRAINING,
    PublishDrainConflictError,
    enforce_session_drain,
    ensure_publish_drain_capacity,
    start_publish_drain,
)


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def test_start_publish_drain_marks_non_admin_sessions_and_despawns_selected_character() -> None:
    db = _db_session()
    now = datetime.now(UTC)
    user = User(email="player@test.com", display_name="Player", password_hash="x", is_admin=False)
    admin = User(email="admin@test.com", display_name="Admin", password_hash="x", is_admin=True)
    db.add_all([user, admin])
    db.commit()
    db.refresh(user)
    db.refresh(admin)

    db.add(
        Character(
            user_id=user.id,
            name="Hero",
            stats={},
            skills={},
            is_selected=True,
            stat_points_total=10,
            stat_points_used=0,
        )
    )
    db.add(
        UserSession(
            id="sess-player",
            user_id=user.id,
            refresh_token_hash="hash",
            client_version="1.0.0",
            client_content_version_key="cv_1",
            expires_at=now + timedelta(hours=1),
            last_seen_at=now,
        )
    )
    db.add(
        UserSession(
            id="sess-admin",
            user_id=admin.id,
            refresh_token_hash="hash2",
            client_version="1.0.0",
            client_content_version_key="cv_1",
            expires_at=now + timedelta(hours=1),
            last_seen_at=now,
        )
    )
    db.commit()

    event = start_publish_drain(
        db,
        trigger_type="content_publish",
        reason_code="content_publish",
        initiated_by="user:1",
        content_version_id=None,
        content_version_key="cv_2",
        build_version="1.0.1",
        grace_minutes=5,
    )
    assert event is not None
    assert event.status == DRAIN_STATUS_DRAINING
    assert event.sessions_targeted == 1
    assert event.sessions_persisted == 1
    assert event.sessions_persist_failed == 0

    player_session = db.get(UserSession, "sess-player")
    admin_session = db.get(UserSession, "sess-admin")
    assert player_session is not None
    assert admin_session is not None
    assert player_session.drain_state == "draining"
    assert player_session.drain_event_id == event.id
    assert admin_session.drain_state == "active"
    assert admin_session.drain_event_id is None

    character = db.query(Character).filter(Character.user_id == user.id).one()
    assert character.is_selected is False


def test_enforce_session_drain_revokes_after_deadline() -> None:
    db = _db_session()
    user = User(email="player2@test.com", display_name="Player2", password_hash="x", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    event = PublishDrainEvent(
        trigger_type="content_publish",
        reason_code="content_publish",
        initiated_by="user:1",
        content_version_key="cv_2",
        grace_seconds=0,
        deadline_at=datetime.now(UTC) - timedelta(seconds=2),
        status=DRAIN_STATUS_DRAINING,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    session = UserSession(
        id="sess-drain",
        user_id=user.id,
        refresh_token_hash="h",
        client_version="1.0.0",
        client_content_version_key="cv_1",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        last_seen_at=datetime.now(UTC),
        drain_state="draining",
        drain_event_id=event.id,
        drain_deadline_at=event.deadline_at,
        drain_reason_code="content_publish",
    )
    db.add(session)
    db.commit()

    decision = enforce_session_drain(db, session, user)
    assert decision is not None
    assert decision.force_logout is True
    updated = db.get(UserSession, "sess-drain")
    assert updated is not None
    assert updated.revoked_at is not None
    assert updated.drain_state == "completed"


def test_publish_drain_lock_prevents_overlap() -> None:
    db = _db_session()
    db.add(
        PublishDrainEvent(
            trigger_type="content_publish",
            reason_code="content_publish",
            initiated_by="user:1",
            content_version_key="cv_2",
            grace_seconds=300,
            deadline_at=datetime.now(UTC) + timedelta(minutes=5),
            status=DRAIN_STATUS_DRAINING,
        )
    )
    db.commit()
    try:
        ensure_publish_drain_capacity(db)
    except PublishDrainConflictError:
        pass
    else:
        assert False, "Expected PublishDrainConflictError"

