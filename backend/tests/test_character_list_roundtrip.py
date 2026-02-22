import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.api.deps import AuthContext  # noqa: E402
from app.api.routes.characters import create_character, list_characters  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.character import CharacterCreateRequest  # noqa: E402


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return session_local()


def _auth_context(user: User) -> AuthContext:
    return AuthContext(user=user, session=None, version_status=None)


def test_character_create_then_list_returns_all_rows() -> None:
    db = _db_session()
    user = User(email="roundtrip@test.com", display_name="Roundtrip", password_hash="hash", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    auth = _auth_context(user)

    create_character(
        CharacterCreateRequest(
            name="FirstHero",
            appearance_key="human_male",
            race="Human",
            background="Drifter",
            affiliation="Unaffiliated",
            stats={},
            skills={},
        ),
        context=auth,
        db=db,
    )
    create_character(
        CharacterCreateRequest(
            name="SecondHero",
            appearance_key="human_female",
            race="Human",
            background="Drifter",
            affiliation="Unaffiliated",
            stats={},
            skills={},
        ),
        context=auth,
        db=db,
    )

    rows = list_characters(context=auth, db=db)
    assert len(rows) == 2
    assert [row.name for row in rows] == ["FirstHero", "SecondHero"]
    assert all(row.level == 1 for row in rows)
