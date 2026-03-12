import os
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


def test_stage_and_activate_world_pack_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage_path = tmp_path / "designer_world_stage.json"
    monkeypatch.setattr(promotion, "WORLD_STAGE_PATH", stage_path)

    staged = promotion.stage_world_pack(_valid_world_pack(), actor_user_id=42)
    assert len(staged.pack_hash) == 64
    assert staged.staged_by == 42
    assert stage_path.exists() is True

    loaded = promotion.load_staged_world_pack()
    assert loaded is not None
    assert loaded.pack_hash == staged.pack_hash
    assert loaded.pack["province_id"] == "acre"

    activated = promotion.activate_staged_world_pack(expected_pack_hash=staged.pack_hash)
    assert activated.pack_hash == staged.pack_hash
    assert activated.version_key.startswith("acre_world_")
    assert len(activated.file_changes) == 3
    assert activated.file_changes[0].path.startswith("assets/content/provinces/acre/")

    promotion.clear_staged_world_pack()
    assert stage_path.exists() is False


def test_activate_fails_when_expected_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage_path = tmp_path / "designer_world_stage.json"
    monkeypatch.setattr(promotion, "WORLD_STAGE_PATH", stage_path)
    staged = promotion.stage_world_pack(_valid_world_pack(), actor_user_id=7)

    with pytest.raises(ValueError, match="does not match expected hash"):
        promotion.activate_staged_world_pack(expected_pack_hash=f"{staged.pack_hash[:-1]}0")


def test_stage_rejects_invalid_settlement_kind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage_path = tmp_path / "designer_world_stage.json"
    monkeypatch.setattr(promotion, "WORLD_STAGE_PATH", stage_path)
    payload = _valid_world_pack()
    payload["settlements"][0]["kind"] = "metropolis"

    with pytest.raises(ValueError, match="invalid kind"):
        promotion.stage_world_pack(payload, actor_user_id=3)
