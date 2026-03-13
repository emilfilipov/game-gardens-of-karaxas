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
from app.api.routes.gameplay import world_sync  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.character import Character  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.common import VersionStatus  # noqa: E402
from app.schemas.gameplay import WorldSyncRequest  # noqa: E402
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


def _seed_user_character(db: Session, *, suffix: str) -> tuple[User, UserSession, Character]:
    user = User(email=f"sync-{suffix}@test.com", display_name=f"User{suffix}", password_hash="hash", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    character = Character(
        user_id=user.id,
        level_id=None,
        location_x=10,
        location_y=11,
        name=f"SyncHero{suffix}",
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
        id=f"sess-sync-{suffix}",
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


def test_world_sync_returns_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db, suffix="a")

    def _fake_snapshot(*, now_ms: int, include_travel_map: bool) -> dict:
        assert now_ms >= 0
        assert include_travel_map is True
        return {
            "tick": {"current_tick": 9},
            "travel_map": {"settlements": [{"id": 101, "name": "Acre"}], "routes": [], "choke_points": []},
            "logistics": {"status": "ok", "current_tick": 9, "state": {"armies": [], "pending_transfers": []}},
            "trade": {"status": "ok", "current_tick": 9, "state": {"markets": [], "routes": [], "pending_shipments": []}},
            "espionage": {"status": "ok", "current_tick": 9, "state": {"informants": [], "pending_orders": [], "recent_reports": []}},
            "politics": {"status": "ok", "current_tick": 9, "state": {"factions": [], "standings": [], "offices": [], "treaties": [], "pending_orders": []}},
            "battle": {"status": "ok", "current_tick": 9, "state": {"instances": [], "recent_results": [], "pending_orders": []}},
            "metrics": {"status": "ok", "tick_interval_ms": 200, "queue_depth": 0, "tick_metrics": {"total_ticks": 9}},
        }

    monkeypatch.setattr(gameplay_routes, "fetch_world_sync_snapshot", _fake_snapshot)

    response = world_sync(
        WorldSyncRequest(character_id=character.id, last_applied_tick=0, include_map=True),
        context=_auth_context(user, session),
        db=db,
    )

    assert response.accepted is True
    assert response.reason_code == "world_sync_snapshot"
    assert response.character_id == character.id
    assert response.campaign_tick == 9
    assert response.tick_interval_ms == 200
    assert response.stale_after_ms >= 800
    assert response.world["travel_map"]["settlements"][0]["id"] == 101


def test_world_sync_returns_404_for_foreign_character() -> None:
    db = _db_session()
    owner, owner_session, owner_character = _seed_user_character(db, suffix="owner")
    intruder, intruder_session, _intruder_character = _seed_user_character(db, suffix="intruder")

    with pytest.raises(HTTPException) as exc:
        world_sync(
            WorldSyncRequest(character_id=owner_character.id),
            context=_auth_context(intruder, intruder_session),
            db=db,
        )

    assert owner.id != intruder.id
    assert owner_session.id != intruder_session.id
    assert exc.value.status_code == 404


def test_world_sync_returns_502_when_world_service_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    user, session, character = _seed_user_character(db, suffix="b")

    def _failing_snapshot(*, now_ms: int, include_travel_map: bool) -> dict:  # noqa: ARG001
        raise WorldServiceControlError("world down")

    monkeypatch.setattr(gameplay_routes, "fetch_world_sync_snapshot", _failing_snapshot)

    with pytest.raises(HTTPException) as exc:
        world_sync(
            WorldSyncRequest(character_id=character.id),
            context=_auth_context(user, session),
            db=db,
        )

    assert exc.value.status_code == 502
    assert exc.value.detail["code"] == "world_sync_unavailable"
