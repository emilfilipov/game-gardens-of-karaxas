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
from app.api.routes.gameplay import issue_battle_command, start_battle_instance  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.character import Character  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.common import VersionStatus  # noqa: E402
from app.schemas.gameplay import BattleCommandRequest, BattleStartRequest  # noqa: E402
from app.services.world_service_control import WorldServiceControlError  # noqa: E402


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
    user = User(email="battle@test.com", display_name="Battle", password_hash="hash", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    character = Character(
        user_id=user.id,
        level_id=None,
        location_x=10,
        location_y=11,
        name="BattleHero",
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
        id="sess-battle",
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


def test_start_battle_instance_dispatches_encounter_command(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db)
    commands: list[dict] = []

    def _dispatch(*, trace_id: str, command: dict) -> dict:
        commands.append({"trace_id": trace_id, "command": command})
        return {"accepted": True}

    monkeypatch.setattr(gameplay_routes, "dispatch_control_command", _dispatch)
    monkeypatch.setattr(gameplay_routes, "advance_ticks", lambda *, now_ms: {"current_tick": 27})
    monkeypatch.setattr(
        gameplay_routes,
        "fetch_battle_state",
        lambda: {"state": {"instances": [{"instance_id": commands[0]["command"]["instance_id"], "status": "active"}], "recent_results": []}},
    )

    response = start_battle_instance(
        BattleStartRequest(character_id=character.id, location_settlement_id=222),
        context=_auth_context(user, session),
        db=db,
    )

    assert response.accepted is True
    assert response.reason_code == "battle_instance_started"
    assert response.campaign_tick == 27
    assert len(commands) == 1
    assert commands[0]["command"]["type"] == "start_battle_encounter"


def test_issue_battle_command_dispatches_formation(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db)
    commands: list[dict] = []

    def _dispatch(*, trace_id: str, command: dict) -> dict:
        commands.append({"trace_id": trace_id, "command": command})
        return {"accepted": True}

    monkeypatch.setattr(gameplay_routes, "dispatch_control_command", _dispatch)
    monkeypatch.setattr(gameplay_routes, "advance_ticks", lambda *, now_ms: {"current_tick": 31})
    monkeypatch.setattr(
        gameplay_routes,
        "fetch_battle_state",
        lambda: {"state": {"instances": [{"instance_id": 9001, "status": "active"}], "recent_results": []}},
    )

    response = issue_battle_command(
        BattleCommandRequest(
            character_id=character.id,
            battle_instance_id=9001,
            action_type="set_formation",
            side="attacker",
            formation="wedge",
        ),
        context=_auth_context(user, session),
        db=db,
    )

    assert response.accepted is True
    assert response.campaign_tick == 31
    assert commands[0]["command"]["type"] == "set_battle_formation"
    assert commands[0]["command"]["formation"] == "wedge"


def test_issue_battle_command_rejects_invalid_action() -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db)

    with pytest.raises(HTTPException) as exc:
        issue_battle_command(
            BattleCommandRequest(
                character_id=character.id,
                battle_instance_id=9001,
                action_type="teleport",
            ),
            context=_auth_context(user, session),
            db=db,
        )

    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "invalid_battle_action_type"


def test_start_battle_instance_returns_502_when_world_service_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db)

    def _failing_dispatch(*, trace_id: str, command: dict) -> dict:  # noqa: ARG001
        raise WorldServiceControlError("bridge down")

    monkeypatch.setattr(gameplay_routes, "dispatch_control_command", _failing_dispatch)

    with pytest.raises(HTTPException) as exc:
        start_battle_instance(
            BattleStartRequest(character_id=character.id),
            context=_auth_context(user, session),
            db=db,
        )

    assert exc.value.status_code == 502
    assert exc.value.detail["code"] == "world_service_unavailable"
