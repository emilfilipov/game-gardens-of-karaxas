from __future__ import annotations

import json
from urllib import error, request

from app.core.config import settings
from app.services.world_service_auth import build_signed_headers

CONTROL_COMMAND_PATH = "/internal/control/commands"
CONTROL_TICK_PATH = "/internal/control/tick"
TRAVEL_MAP_PATH = "/travel/map"
LOGISTICS_STATE_PATH = "/logistics/state"
TRADE_STATE_PATH = "/trade/state"
ESPIONAGE_STATE_PATH = "/espionage/state"
POLITICS_STATE_PATH = "/politics/state"
BATTLE_STATE_PATH = "/battle/state"
METRICS_SUMMARY_PATH = "/metrics/summary"


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
    return _json_get(BATTLE_STATE_PATH)


def fetch_world_sync_snapshot(*, now_ms: int, include_travel_map: bool = True) -> dict:
    tick_payload = advance_ticks(now_ms=now_ms)
    logistics_payload = _json_get(LOGISTICS_STATE_PATH)
    trade_payload = _json_get(TRADE_STATE_PATH)
    espionage_payload = _json_get(ESPIONAGE_STATE_PATH)
    politics_payload = _json_get(POLITICS_STATE_PATH)
    battle_payload = _json_get(BATTLE_STATE_PATH)
    metrics_payload = _json_get(METRICS_SUMMARY_PATH)

    payload = {
        "tick": tick_payload,
        "logistics": logistics_payload,
        "trade": trade_payload,
        "espionage": espionage_payload,
        "politics": politics_payload,
        "battle": battle_payload,
        "metrics": metrics_payload,
    }
    if include_travel_map:
        payload["travel_map"] = _json_get(TRAVEL_MAP_PATH)
    return payload


def _json_get(path: str) -> dict:
    base_url = settings.world_service_base_url.strip().rstrip("/")
    if not base_url:
        raise WorldServiceControlError("world_service_base_url is empty")

    req = request.Request(f"{base_url}{path}", method="GET")
    try:
        with request.urlopen(req, timeout=settings.world_service_request_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            if not isinstance(parsed, dict):
                raise WorldServiceControlError(f"{path} payload is not a JSON object")
            return parsed
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        raise WorldServiceControlError(f"{path} HTTP {exc.code}: {raw}") from exc
    except error.URLError as exc:
        raise WorldServiceControlError(f"{path} network error: {exc.reason}") from exc


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
