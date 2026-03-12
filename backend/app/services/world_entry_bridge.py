from __future__ import annotations

import json
from urllib import error, request

from app.core.config import settings
from app.services.world_service_auth import build_signed_headers

WORLD_ENTRY_PATH = "/internal/world-entry/bootstrap"


class WorldEntryBridgeError(RuntimeError):
    pass


def fetch_world_entry_bootstrap(payload: dict) -> dict:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = build_signed_headers(
        method="POST",
        path_and_query=WORLD_ENTRY_PATH,
        body=body,
    )

    base_url = settings.world_service_base_url.strip().rstrip("/")
    if not base_url:
        raise WorldEntryBridgeError("world_service_base_url is empty")
    req = request.Request(
        f"{base_url}{WORLD_ENTRY_PATH}",
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
                raise WorldEntryBridgeError("world-service world entry payload is not an object")
            return parsed
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        raise WorldEntryBridgeError(f"world-service world entry HTTP {exc.code}: {raw}") from exc
    except error.URLError as exc:
        raise WorldEntryBridgeError(f"world-service world entry network error: {exc.reason}") from exc
