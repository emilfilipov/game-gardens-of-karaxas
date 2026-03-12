import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.api.routes.ops import _outbox_lag_metrics, _release_feed_health  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models.event_pipeline import WorldOutbox  # noqa: E402
from app.models.release_record import ReleaseRecord  # noqa: E402


def _db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return session_local()


def test_outbox_lag_metrics_reports_pending_count_and_lag() -> None:
    db = _db_session()
    row = WorldOutbox(
        id=1,
        topic="world.tick",
        payload_json={"event": "tick"},
        created_at=datetime.now(UTC) - timedelta(seconds=12),
        next_attempt_at=datetime.now(UTC),
        processed_at=None,
        last_error="",
    )
    db.add(row)
    db.commit()

    metrics = _outbox_lag_metrics(db)
    assert metrics["pending_count"] == 1
    assert float(metrics["oldest_lag_seconds"]) >= 0.0


def test_release_feed_health_reports_latest_release_record() -> None:
    db = _db_session()
    release = ReleaseRecord(
        build_version="v0.1.2",
        min_supported_version="v0.1.0",
        content_version_key="runtime_gameplay_v1",
        min_supported_content_version_key="runtime_gameplay_v1",
        update_feed_url="https://example.com/feed",
        build_release_notes="notes",
        user_facing_notes="notes",
        activated_by="test",
        enforce_after=None,
        activated_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    db.add(release)
    db.commit()

    health = _release_feed_health(db)
    assert health["has_release_record"] is True
    assert health["latest_build_version"] == "v0.1.2"
    assert health["update_feed_url_present"] is True
    assert float(health["minutes_since_latest_activation"]) >= 0.0
