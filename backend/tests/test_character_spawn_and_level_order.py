import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.api.deps import AuthContext  # noqa: E402
from app.api.routes.characters import assign_character_level, create_character  # noqa: E402
from app.api.routes.levels import save_level_order  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.character import Character  # noqa: E402
from app.models.level import Level  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.character import CharacterCreateRequest, CharacterLevelAssignRequest  # noqa: E402
from app.schemas.level import LevelOrderItem, LevelOrderSaveRequest  # noqa: E402


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def _auth_context(user: User) -> AuthContext:
    return AuthContext(user=user, session=None, version_status=None)


def _make_level(
    *,
    name: str,
    order_index: int,
    spawn_x: int,
    spawn_y: int,
) -> Level:
    return Level(
        name=name,
        descriptive_name=name,
        order_index=order_index,
        schema_version=2,
        width=40,
        height=24,
        spawn_x=spawn_x,
        spawn_y=spawn_y,
        wall_cells=[],
        layer_cells={},
        transitions=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC) + timedelta(seconds=1),
    )


def test_new_character_spawns_at_first_ordered_floor() -> None:
    db = _db_session()
    user = User(email="spawn@test.com", display_name="Spawner", password_hash="hash", is_admin=False)
    db.add(user)
    db.add_all(
        [
            _make_level(name="Floor-B", order_index=2, spawn_x=7, spawn_y=8),
            _make_level(name="Floor-A", order_index=1, spawn_x=3, spawn_y=4),
        ]
    )
    db.commit()
    db.refresh(user)

    response = create_character(
        CharacterCreateRequest(
            name="SpawnTester",
            appearance_key="human_male",
            race="Human",
            background="Drifter",
            affiliation="Unaffiliated",
            stats={},
            skills={},
        ),
        context=_auth_context(user),
        db=db,
    )
    assert response.level_id is not None
    assert response.location_x == 3
    assert response.location_y == 4


def test_assign_character_level_resets_spawn_to_target_floor_spawn() -> None:
    db = _db_session()
    admin = User(email="admin-level@test.com", display_name="Admin", password_hash="hash", is_admin=True)
    target_level = _make_level(name="Floor-Target", order_index=1, spawn_x=11, spawn_y=13)
    db.add_all([admin, target_level])
    db.commit()
    db.refresh(admin)
    db.refresh(target_level)

    character = Character(
        user_id=admin.id,
        level_id=None,
        location_x=None,
        location_y=None,
        name="AdminHero",
        appearance_key="human_female",
        race="Human",
        background="Drifter",
        affiliation="Unaffiliated",
        stat_points_total=10,
        stat_points_used=0,
        level=1,
        experience=0,
        stats={},
        skills={},
        is_selected=False,
    )
    db.add(character)
    db.commit()
    db.refresh(character)

    result = assign_character_level(
        character.id,
        CharacterLevelAssignRequest(level_id=target_level.id),
        context=_auth_context(admin),
        db=db,
    )
    assert result["level_id"] == target_level.id
    assert result["location_x"] == 11
    assert result["location_y"] == 13


def test_level_order_save_persists_drag_drop_order_atomically() -> None:
    db = _db_session()
    admin = User(email="order-admin@test.com", display_name="OrderAdmin", password_hash="hash", is_admin=True)
    levels = [
        _make_level(name="L1", order_index=1, spawn_x=1, spawn_y=1),
        _make_level(name="L2", order_index=2, spawn_x=2, spawn_y=2),
        _make_level(name="L3", order_index=3, spawn_x=3, spawn_y=3),
    ]
    db.add(admin)
    db.add_all(levels)
    db.commit()
    db.refresh(admin)
    for level in levels:
        db.refresh(level)

    payload = LevelOrderSaveRequest(
        levels=[
            LevelOrderItem(level_id=levels[2].id, order_index=1),
            LevelOrderItem(level_id=levels[0].id, order_index=2),
            LevelOrderItem(level_id=levels[1].id, order_index=3),
        ]
    )
    response = save_level_order(payload, context=_auth_context(admin), db=db)
    assert response["ok"] is True
    assert response["updated"] == 3

    ordered = db.execute(select(Level).order_by(Level.order_index.asc(), Level.id.asc())).scalars().all()
    assert [row.id for row in ordered] == [levels[2].id, levels[0].id, levels[1].id]
