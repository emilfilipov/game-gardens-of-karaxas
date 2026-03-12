import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.api.deps import AuthContext  # noqa: E402
from app.api.routes import designer_publish as designer_routes  # noqa: E402
from app.db.base import Base  # noqa: E402
import app.models  # noqa: F401,E402
from app.models.admin_audit import AdminActionAudit  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.session import UserSession  # noqa: E402
from app.schemas.designer_publish import (  # noqa: E402
    DesignerWorldPackActivateRequest,
    DesignerWorldPackStageRequest,
)
from app.services.github_publish import GitHubPublishResult  # noqa: E402


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return session_local()


def _admin_context(db: Session) -> AuthContext:
    admin = User(email="admin@test.com", display_name="Admin", password_hash="x", is_admin=True)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    session = UserSession(
        id="designer-test-session",
        user_id=admin.id,
        refresh_token_hash="hash",
        client_version="1.0.0",
        client_content_version_key="cv_1",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    db.commit()
    return AuthContext(user=admin, session=session, version_status=None)


def _stage_payload() -> DesignerWorldPackStageRequest:
    return DesignerWorldPackStageRequest(
        pack={
            "manifest_version": 1,
            "province_id": "acre",
            "display_name": "Acre Draft",
            "settlements": [
                {"id": 1, "name": "Acre Port", "map_x": -280, "map_y": 60, "kind": "city"},
                {"id": 2, "name": "Montmusard Camp", "map_x": -250, "map_y": 120, "kind": "camp"},
            ],
            "routes": [
                {"id": 10, "origin": 1, "destination": 2, "travel_hours": 2, "base_risk": 10, "is_sea_route": False},
            ],
            "spawn_points": [
                {"id": 1, "key": "player_spawn", "settlement_id": 1, "spawn_type": "player"},
            ],
        }
    )


def test_world_pack_stage_and_activate_routes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db_session()
    context = _admin_context(db)
    stage_path = tmp_path / "designer_world_stage.json"
    monkeypatch.setattr(designer_routes, "publish_changes_and_dispatch", _fake_publish)
    monkeypatch.setattr("app.services.designer_world_promotion.WORLD_STAGE_PATH", stage_path)

    staged = designer_routes.stage_designer_world_pack(_stage_payload(), context=context, db=db)
    assert staged.settlement_count == 2
    assert staged.route_count == 1
    assert staged.spawn_count == 1
    assert stage_path.exists() is True

    activated = designer_routes.activate_designer_world_pack(
        DesignerWorldPackActivateRequest(
            expected_pack_hash=staged.pack_hash,
            commit_message="Promote acre world pack",
            trigger_release_workflow=True,
            trigger_backend_workflow=False,
        ),
        context=context,
        db=db,
    )
    assert activated.pack_hash == staged.pack_hash
    assert activated.version_key.startswith("acre_world_")
    assert activated.commit_sha == "deadbeefcafebabe"
    assert activated.release_workflow_triggered is True
    assert activated.backend_workflow_triggered is False
    assert stage_path.exists() is False

    audit_rows = db.execute(select(AdminActionAudit).order_by(AdminActionAudit.id.asc())).scalars().all()
    assert len(audit_rows) == 2
    assert audit_rows[0].action == "designer_world_stage"
    assert audit_rows[1].action == "designer_world_activate"


def _fake_publish(**kwargs) -> GitHubPublishResult:
    file_changes = kwargs.get("file_changes", [])
    assert len(file_changes) == 3
    return GitHubPublishResult(
        repo="example/repo",
        branch="main",
        commit_sha="deadbeefcafebabe",
        release_workflow_triggered=bool(kwargs.get("trigger_release_workflow", False)),
        backend_workflow_triggered=bool(kwargs.get("trigger_backend_workflow", False)),
    )
