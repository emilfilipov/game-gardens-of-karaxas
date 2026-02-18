from datetime import UTC, datetime, timedelta

from app.models.release_policy import ReleasePolicy
from app.services.release_policy import evaluate_version, next_logical_build_version


def test_update_available_without_force() -> None:
    policy = ReleasePolicy(
        id=1,
        latest_version="1.0.2",
        min_supported_version="1.0.0",
        latest_content_version_key="cv_2",
        min_supported_content_version_key="cv_1",
        enforce_after=datetime.now(UTC) + timedelta(minutes=5),
        updated_by="test",
    )

    decision = evaluate_version(policy, "1.0.1", "cv_1")
    assert decision.update_available is True
    assert decision.content_update_available is True
    assert decision.force_update is False


def test_force_update_after_grace() -> None:
    policy = ReleasePolicy(
        id=1,
        latest_version="1.2.0",
        min_supported_version="1.2.0",
        latest_content_version_key="cv_2",
        min_supported_content_version_key="cv_2",
        enforce_after=datetime.now(UTC) - timedelta(minutes=1),
        updated_by="test",
    )

    decision = evaluate_version(policy, "1.1.9", "cv_1")
    assert decision.update_available is True
    assert decision.content_update_available is True
    assert decision.force_update is True


def test_content_only_publish_does_not_advertise_binary_update() -> None:
    policy = ReleasePolicy(
        id=1,
        latest_version="1.0.11",
        min_supported_version="1.0.10",
        latest_content_version_key="cv_11",
        min_supported_content_version_key="cv_11",
        enforce_after=datetime.now(UTC) + timedelta(minutes=5),
        updated_by="test",
    )
    decision = evaluate_version(policy, "1.0.10", "cv_11")
    assert decision.update_available is False
    assert decision.content_update_available is False
    assert decision.force_update is False


def test_next_logical_build_version_increments_patch() -> None:
    assert next_logical_build_version("1.0.9") == "1.0.10"
    assert next_logical_build_version("2.4") == "2.4.1"
