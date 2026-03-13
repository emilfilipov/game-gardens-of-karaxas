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
from app.models.session import UserSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.designer_publish import (  # noqa: E402
    DesignerWorldPackActivateRequest,
    DesignerWorldPackDeactivateRequest,
    DesignerWorldPackRollbackRequest,
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


def _stage_payload(display_name: str = "Acre Draft") -> DesignerWorldPackStageRequest:
    return DesignerWorldPackStageRequest(
        pack={
            "manifest_version": 1,
            "province_id": "acre",
            "display_name": display_name,
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


def test_world_pack_stage_activate_rollback_and_deactivate_routes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = _db_session()
    context = _admin_context(db)
    stage_path = tmp_path / "runtime" / "designer_world_stage.json"
    state_dir = tmp_path / "runtime" / "designer_world_state"

    publish_calls: list[dict] = []

    def _fake_publish(**kwargs) -> GitHubPublishResult:
        publish_calls.append(kwargs)
        return GitHubPublishResult(
            repo="example/repo",
            branch="main",
            commit_sha="deadbeefcafebabe",
            release_workflow_triggered=bool(kwargs.get("trigger_release_workflow", False)),
            backend_workflow_triggered=bool(kwargs.get("trigger_backend_workflow", False)),
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(designer_routes, "publish_changes_and_dispatch", _fake_publish)
    monkeypatch.setattr("app.services.designer_world_promotion.WORLD_STAGE_PATH", stage_path)
    monkeypatch.setattr("app.services.designer_world_promotion.WORLD_PROMOTION_STATE_DIR", state_dir)

    staged_v1 = designer_routes.stage_designer_world_pack(_stage_payload("Acre Draft v1"), context=context, db=db)
    activated_v1 = designer_routes.activate_designer_world_pack(
        DesignerWorldPackActivateRequest(
            expected_pack_hash=staged_v1.pack_hash,
            commit_message="Promote acre world pack v1",
            trigger_release_workflow=True,
            trigger_backend_workflow=False,
        ),
        context=context,
        db=db,
    )

    staged_v2 = designer_routes.stage_designer_world_pack(_stage_payload("Acre Draft v2"), context=context, db=db)
    activated_v2 = designer_routes.activate_designer_world_pack(
        DesignerWorldPackActivateRequest(
            expected_pack_hash=staged_v2.pack_hash,
            commit_message="Promote acre world pack v2",
            trigger_release_workflow=True,
            trigger_backend_workflow=False,
        ),
        context=context,
        db=db,
    )

    rollback = designer_routes.rollback_designer_world_pack(
        DesignerWorldPackRollbackRequest(
            province_id="acre",
            target_version_key=activated_v1.version_key,
            commit_message="Rollback to v1",
            trigger_release_workflow=False,
            trigger_backend_workflow=True,
        ),
        context=context,
        db=db,
    )

    deactivated = designer_routes.deactivate_designer_world_pack(
        DesignerWorldPackDeactivateRequest(
            province_id="acre",
            commit_message="Deactivate active world pack",
            trigger_release_workflow=False,
            trigger_backend_workflow=True,
        ),
        context=context,
        db=db,
    )

    assert activated_v1.version_key.startswith("acre_world_")
    assert activated_v2.version_key.startswith("acre_world_")
    assert activated_v2.version_key != activated_v1.version_key

    assert rollback.version_key == activated_v1.version_key
    assert rollback.commit_sha == "deadbeefcafebabe"
    assert rollback.release_workflow_triggered is False
    assert rollback.backend_workflow_triggered is True

    assert deactivated.province_id == "acre"
    assert deactivated.deactivated_version_key == activated_v1.version_key
    assert deactivated.release_workflow_triggered is False
    assert deactivated.backend_workflow_triggered is True

    assert stage_path.exists() is False
    assert len(publish_calls) == 4
    assert len(publish_calls[0]["file_changes"]) == 4
    assert len(publish_calls[1]["file_changes"]) == 4
    assert len(publish_calls[2]["file_changes"]) == 2
    assert len(publish_calls[3]["file_changes"]) == 2

    audit_rows = db.execute(select(AdminActionAudit).order_by(AdminActionAudit.id.asc())).scalars().all()
    actions = [row.action for row in audit_rows]
    assert actions == [
        "designer_world_stage",
        "designer_world_activate",
        "designer_world_stage",
        "designer_world_activate",
        "designer_world_rollback",
        "designer_world_deactivate",
    ]
