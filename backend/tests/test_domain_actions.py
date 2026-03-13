import os
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.api.deps import AuthContext  # noqa: E402
import app.api.routes.gameplay as gameplay_routes  # noqa: E402
from app.api.routes.gameplay import issue_domain_action  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.character import Character  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.common import VersionStatus  # noqa: E402
from app.schemas.gameplay import DomainActionRequest  # noqa: E402


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return session_local()


def _version_status() -> VersionStatus:
    return VersionStatus(
        client_version="test-1.0.0",
        latest_version="test-1.0.0",
        min_supported_version="test-1.0.0",
        client_content_version_key="runtime_gameplay_v1",
        latest_content_version_key="runtime_gameplay_v1",
        min_supported_content_version_key="runtime_gameplay_v1",
        enforce_after=None,
        update_available=False,
        content_update_available=False,
        force_update=False,
        update_feed_url=None,
    )


def _auth_context(user: User, session: UserSession) -> AuthContext:
    return AuthContext(user=user, session=session, version_status=_version_status())


def _seed_user_character(db: Session) -> tuple[User, UserSession, Character]:
    user = User(email="domain@test.com", display_name="Domain", password_hash="hash", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    character = Character(
        user_id=user.id,
        level_id=None,
        location_x=10,
        location_y=11,
        name="DomainHero",
        preset_key="sellsword",
        appearance_key="human_male",
        appearance_profile={},
        race="Human",
        background="Drifter",
        affiliation="Unaffiliated",
        stat_points_total=10,
        stat_points_used=0,
        level=1,
        experience=0,
        equipment={},
        inventory=[],
        stats={},
        skills={},
        is_selected=True,
    )
    db.add(character)
    db.commit()
    db.refresh(character)

    session = UserSession(
        id="sess-domain",
        user_id=user.id,
        refresh_token_hash="hash",
        client_version="test-1.0.0",
        client_content_version_key="runtime_gameplay_v1",
        drain_state="active",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return user, session, character


def test_domain_action_dispatches_supply_transfer(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db)
    commands: list[dict] = []

    def _dispatch(*, trace_id: str, command: dict) -> dict:
        commands.append({"trace_id": trace_id, "command": command})
        return {"accepted": True}

    monkeypatch.setattr(gameplay_routes, "dispatch_control_command", _dispatch)
    monkeypatch.setattr(gameplay_routes, "advance_ticks", lambda *, now_ms: {"current_tick": 44})

    response = issue_domain_action(
        DomainActionRequest(
            character_id=character.id,
            action_type="queue_supply_transfer",
            payload={"from_army": 7, "to_army": 8, "food": 12, "horses": 3, "materiel": 5},
        ),
        context=_auth_context(user, session),
        db=db,
    )

    assert response.accepted is True
    assert response.reason_code == "domain_action_dispatched"
    assert response.campaign_tick == 44
    assert commands[0]["command"]["type"] == "queue_supply_transfer"


def test_domain_action_rejects_invalid_action_type() -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db)

    with pytest.raises(HTTPException) as exc:
        issue_domain_action(
            DomainActionRequest(character_id=character.id, action_type="unknown", payload={}),
            context=_auth_context(user, session),
            db=db,
        )

    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "invalid_domain_action_type"
