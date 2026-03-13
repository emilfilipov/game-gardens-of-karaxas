import os
import json
from pathlib import Path

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

from app.services import designer_world_promotion as promotion  # noqa: E402


def _valid_world_pack() -> dict:
    return {
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


def _configure_temp_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(promotion, "WORLD_STAGE_PATH", tmp_path / "runtime" / "designer_world_stage.json")
    monkeypatch.setattr(promotion, "WORLD_PROMOTION_STATE_DIR", tmp_path / "runtime" / "designer_world_state")
    monkeypatch.chdir(tmp_path)


def test_stage_and_activate_world_pack_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_temp_paths(tmp_path, monkeypatch)

    staged = promotion.stage_world_pack(_valid_world_pack(), actor_user_id=42)
    assert len(staged.pack_hash) == 64
    assert staged.staged_by == 42
    assert promotion.WORLD_STAGE_PATH.exists() is True

    loaded = promotion.load_staged_world_pack()
    assert loaded is not None
    assert loaded.pack_hash == staged.pack_hash
    assert loaded.pack["province_id"] == "acre"

    activated = promotion.activate_staged_world_pack(expected_pack_hash=staged.pack_hash)
    assert activated.pack_hash == staged.pack_hash
    assert activated.version_key.startswith("acre_world_")
    assert len(activated.file_changes) == 4
    assert activated.file_changes[0].path.startswith("assets/content/provinces/acre/")
    assert activated.file_changes[-1].path.endswith("/versions.json")

    promotion.clear_staged_world_pack()
    assert promotion.WORLD_STAGE_PATH.exists() is False


def test_activate_fails_when_expected_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_temp_paths(tmp_path, monkeypatch)
    staged = promotion.stage_world_pack(_valid_world_pack(), actor_user_id=7)

    with pytest.raises(ValueError, match="does not match expected hash"):
        promotion.activate_staged_world_pack(expected_pack_hash=f"{staged.pack_hash[:-1]}0")


def test_stage_rejects_invalid_settlement_kind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_temp_paths(tmp_path, monkeypatch)
    payload = _valid_world_pack()
    payload["settlements"][0]["kind"] = "metropolis"

    with pytest.raises(ValueError, match="invalid kind"):
        promotion.stage_world_pack(payload, actor_user_id=3)


def test_deactivate_and_rollback_world_pack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_temp_paths(tmp_path, monkeypatch)

    first = _valid_world_pack()
    staged_first = promotion.stage_world_pack(first, actor_user_id=11)
    activated_first = promotion.activate_staged_world_pack(expected_pack_hash=staged_first.pack_hash)

    second = _valid_world_pack()
    second["display_name"] = "Acre Draft v2"
    second["spawn_points"].append({"id": 2, "key": "army_spawn", "settlement_id": 2, "spawn_type": "army"})
    staged_second = promotion.stage_world_pack(second, actor_user_id=11)
    activated_second = promotion.activate_staged_world_pack(expected_pack_hash=staged_second.pack_hash)

    deactivated = promotion.deactivate_active_world_pack("acre")
    assert deactivated.province_id == "acre"
    assert deactivated.version_key == activated_second.version_key
    assert len(deactivated.file_changes) == 2

    rolled_back = promotion.rollback_world_pack_version("acre", target_version_key=activated_first.version_key)
    assert rolled_back.province_id == "acre"
    assert rolled_back.version_key == activated_first.version_key
    assert rolled_back.pack_hash == activated_first.pack_hash
    assert len(rolled_back.file_changes) == 2


def test_deactivate_uses_latest_pointer_when_versions_file_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_temp_paths(tmp_path, monkeypatch)

    latest_path = tmp_path / "assets" / "content" / "provinces" / "acre" / "latest.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "active_version_key": "acre_world_20260313010101",
                "active_sha256": "ab" * 32,
                "activated_at": "2026-03-13T01:01:01+00:00",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    deactivated = promotion.deactivate_active_world_pack("acre")
    assert deactivated.version_key == "acre_world_20260313010101"


def test_rollback_rejects_unknown_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_temp_paths(tmp_path, monkeypatch)

    staged = promotion.stage_world_pack(_valid_world_pack(), actor_user_id=5)
    promotion.activate_staged_world_pack(expected_pack_hash=staged.pack_hash)

    with pytest.raises(ValueError, match="Unknown rollback target"):
        promotion.rollback_world_pack_version("acre", target_version_key="acre_world_missing")
