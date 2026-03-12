from __future__ import annotations

import json
from urllib import error, request

from app.core.config import settings
from app.services.world_service_auth import build_signed_headers

CONTROL_COMMAND_PATH = "/internal/control/commands"
CONTROL_TICK_PATH = "/internal/control/tick"
BATTLE_STATE_PATH = "/battle/state"


class WorldServiceControlError(RuntimeError):
    pass


def dispatch_control_command(*, trace_id: str, command: dict) -> dict:
    payload = {
        "trace_id": trace_id,
        "command": command,
    }
    return _signed_json_post(CONTROL_COMMAND_PATH, payload)


def advance_ticks(*, now_ms: int) -> dict:
    return _signed_json_post(CONTROL_TICK_PATH, {"now_ms": int(now_ms)})


def fetch_battle_state() -> dict:
    base_url = settings.world_service_base_url.strip().rstrip("/")
    if not base_url:
        raise WorldServiceControlError("world_service_base_url is empty")

    req = request.Request(f"{base_url}{BATTLE_STATE_PATH}", method="GET")
    try:
        with request.urlopen(req, timeout=settings.world_service_request_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            if not isinstance(parsed, dict):
                raise WorldServiceControlError("battle state payload is not a JSON object")
            return parsed
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        raise WorldServiceControlError(f"battle state HTTP {exc.code}: {raw}") from exc
    except error.URLError as exc:
        raise WorldServiceControlError(f"battle state network error: {exc.reason}") from exc


def _signed_json_post(path: str, payload: dict) -> dict:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = build_signed_headers(method="POST", path_and_query=path, body=body)
    base_url = settings.world_service_base_url.strip().rstrip("/")
    if not base_url:
        raise WorldServiceControlError("world_service_base_url is empty")

    req = request.Request(
        f"{base_url}{path}",
        method="POST",
        data=body,
        headers={
            "Content-Type": "application/json",
            **headers,
        },
    )

    try:
        with request.urlopen(req, timeout=settings.world_service_request_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            if not isinstance(parsed, dict):
                raise WorldServiceControlError(f"response from {path} is not a JSON object")
            return parsed
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        raise WorldServiceControlError(f"{path} HTTP {exc.code}: {raw}") from exc
    except error.URLError as exc:
        raise WorldServiceControlError(f"{path} network error: {exc.reason}") from exc
