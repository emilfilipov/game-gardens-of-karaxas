import io
import json
import os
from urllib import error

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPS_API_TOKEN", "test-ops")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("WORLD_SERVICE_BASE_URL", "http://127.0.0.1:8088")
os.environ.setdefault("WORLD_SERVICE_AUTH_SECRET", "integration-secret")
os.environ.setdefault("WORLD_SERVICE_CALLER_ID", "fastapi-control-plane")
os.environ.setdefault("WORLD_SERVICE_SCOPE", "world.control.mutate")
os.environ.setdefault("WORLD_SERVICE_REQUEST_TIMEOUT_SECONDS", "5")

from app.services.world_entry_bridge import WORLD_ENTRY_PATH, WorldEntryBridgeError, fetch_world_entry_bootstrap  # noqa: E402


class _DummyResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


def test_fetch_world_entry_bootstrap_signs_and_decodes_response(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def _fake_urlopen(req, timeout):  # type: ignore[no-untyped-def]
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["timeout"] = str(timeout)
        captured["signature"] = req.headers.get("x-aop-signature", "") or req.headers.get("X-aop-signature", "")
        captured["service_id"] = req.headers.get("x-aop-service-id", "") or req.headers.get("X-aop-service-id", "")
        return _DummyResponse(
            {
                "status": "ok",
                "character_id": 7,
                "anchor_settlement_id": 101,
                "campaign_tick": 12,
            }
        )

    monkeypatch.setattr("app.services.world_entry_bridge.request.urlopen", _fake_urlopen)

    payload = {
        "character_id": 7,
        "character_name": "BridgeHero",
        "instance_id": "inst-7",
        "instance_kind": "campaign_shard",
        "spawn_world_x": -120,
        "spawn_world_y": 40,
        "spawn_world_z": 0.0,
        "yaw_deg": 90.0,
    }
    response = fetch_world_entry_bootstrap(payload)

    assert response["status"] == "ok"
    assert response["anchor_settlement_id"] == 101
    assert captured["url"].endswith(WORLD_ENTRY_PATH)
    assert captured["method"] == "POST"
    assert captured["signature"]
    assert captured["service_id"] == "fastapi-control-plane"


def test_fetch_world_entry_bootstrap_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_urlopen(_req, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise error.HTTPError(
            url="http://127.0.0.1:8088/internal/world-entry/bootstrap",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"unavailable"}'),
        )

    monkeypatch.setattr("app.services.world_entry_bridge.request.urlopen", _fake_urlopen)

    with pytest.raises(WorldEntryBridgeError) as exc:
        fetch_world_entry_bootstrap(
            {
                "character_id": 7,
                "character_name": "BridgeHero",
                "instance_id": "inst-7",
                "instance_kind": "campaign_shard",
                "spawn_world_x": -120,
                "spawn_world_y": 40,
                "spawn_world_z": 0.0,
                "yaw_deg": 90.0,
            }
        )

    assert "HTTP 503" in str(exc.value)
