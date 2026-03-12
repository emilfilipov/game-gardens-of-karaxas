import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.api.deps import AuthContext  # noqa: E402
from app.api.routes.characters import bootstrap_character_world  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.character import Character  # noqa: E402
from app.models.level import Level  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.character import CharacterWorldBootstrapRequest  # noqa: E402
from app.schemas.common import VersionStatus  # noqa: E402


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


def test_world_bootstrap_returns_spawn_yaw_z_map_scale_and_camera_profile() -> None:
    db = _db_session()
    user = User(email="bootstrap3d@test.com", display_name="Bootstrap3D", password_hash="hash", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    level = Level(
        name="expedition_floor",
        descriptive_name="Expedition Floor",
        order_index=1,
        schema_version=2,
        width=40,
        height=24,
        spawn_x=3,
        spawn_y=4,
        is_town_hub=False,
        wall_cells=[],
        layer_cells={},
        object_placements=[
            {
                "object_id": "spawn_marker_3d",
                "asset_key": "spawn_marker",
                "layer_id": 0,
                "transform": {"x": 3.0, "y": 4.0, "z": 1.5, "rotation_deg": 130.0},
            }
        ],
        transitions=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(level)
    db.commit()
    db.refresh(level)

    character = Character(
        user_id=user.id,
        level_id=level.id,
        location_x=3,
        location_y=4,
        name="WorldHero",
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
        is_selected=False,
    )
    db.add(character)
    db.commit()
    db.refresh(character)

    session = UserSession(
        id="sess-bootstrap3d",
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

    response = bootstrap_character_world(
        character.id,
        CharacterWorldBootstrapRequest(override_level_id=None),
        context=_auth_context(user, session),
        db=db,
    )
    assert response.spawn.yaw_deg == 130.0
    assert response.spawn.world_z == 1.5
    assert response.runtime.camera_profile_key == "arpg_poe_baseline"
    assert response.level.map_scale["tile_world_size"] == 32.0
    assert response.level.scene_variant_hint == "arena_flat_grass"
    assert response.player_runtime["world_entry_bridge"]["status"] in {"ok", "fallback", "skipped"}


def test_world_bootstrap_scene_variant_defaults_for_town_hub() -> None:
    db = _db_session()
    user = User(email="bootstrap-hub@test.com", display_name="BootstrapHub", password_hash="hash", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    level = Level(
        name="hub_floor",
        descriptive_name="Hub Floor",
        order_index=1,
        schema_version=2,
        width=40,
        height=24,
        spawn_x=2,
        spawn_y=2,
        is_town_hub=True,
        wall_cells=[],
        layer_cells={},
        object_placements=[],
        transitions=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(level)
    db.commit()
    db.refresh(level)

    character = Character(
        user_id=user.id,
        level_id=level.id,
        location_x=2,
        location_y=2,
        name="HubHero",
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
        is_selected=False,
    )
    db.add(character)
    db.commit()
    db.refresh(character)

    session = UserSession(
        id="sess-bootstrap-hub",
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

    response = bootstrap_character_world(
        character.id,
        CharacterWorldBootstrapRequest(override_level_id=None),
        context=_auth_context(user, session),
        db=db,
    )
    assert response.spawn.yaw_deg == 0.0
    assert response.spawn.world_z == 0.0
    assert response.level.scene_variant_hint == "town_hub"


def main() -> int:
    tests = [
        test_world_bootstrap_returns_spawn_yaw_z_map_scale_and_camera_profile,
        test_world_bootstrap_scene_variant_defaults_for_town_hub,
    ]
    for test_fn in tests:
        test_fn()
    print("[bootstrap-3d-contract] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
