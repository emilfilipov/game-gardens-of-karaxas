#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_CLIENT_VERSION = "dev-0.1.0"
DEFAULT_CONTENT_VERSION_KEY = "runtime_gameplay_v1"
DEFAULT_EMAIL = "poc@ambitions.local"
DEFAULT_PASSWORD = "AmbitionsPoc!123"
DEFAULT_DISPLAY_NAME = "Ambitions PoC"
DEFAULT_CHARACTER_NAME = "PocCommander"


@dataclass
class SessionInfo:
    access_token: str
    refresh_token: str
    session_id: str
    user_id: int
    display_name: str


def _headers(*, client_version: str, content_version_key: str, token: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "x-client-version": client_version,
        "x-client-content-version": content_version_key,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(
    method: str,
    url: str,
    *,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 10.0,
) -> tuple[int, dict]:
    body = None
    request_headers = headers or {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, method=method, data=body, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            if isinstance(parsed, dict):
                return response.getcode(), parsed
            return response.getcode(), {"data": parsed}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed: dict = {}
        if raw:
            try:
                maybe = json.loads(raw)
                if isinstance(maybe, dict):
                    parsed = maybe
                else:
                    parsed = {"data": maybe}
            except Exception:
                parsed = {"raw": raw}
        return exc.code, parsed


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _extract_message(payload: dict) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        msg = str(error.get("message", "")).strip()
        if msg:
            return msg
    detail = payload.get("detail")
    if isinstance(detail, dict):
        msg = str(detail.get("message", "")).strip()
        if msg:
            return msg
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return json.dumps(payload, sort_keys=True)


def _register_or_login(
    *,
    base_url: str,
    email: str,
    password: str,
    display_name: str,
    client_version: str,
    content_version_key: str,
) -> SessionInfo:
    common_headers = _headers(client_version=client_version, content_version_key=content_version_key)
    register_payload = {
        "email": email,
        "password": password,
        "display_name": display_name,
    }
    code, register_body = _request(
        "POST",
        f"{base_url}/auth/register",
        payload=register_payload,
        headers=common_headers,
    )

    if code in {200, 201}:
        return SessionInfo(
            access_token=str(register_body.get("access_token", "")),
            refresh_token=str(register_body.get("refresh_token", "")),
            session_id=str(register_body.get("session_id", "")),
            user_id=int(register_body.get("user_id", 0) or 0),
            display_name=str(register_body.get("display_name", "") or display_name),
        )

    _require(code == 409, f"Register failed with HTTP {code}: {_extract_message(register_body)}")

    login_payload = {
        "email": email,
        "password": password,
        "client_version": client_version,
        "client_content_version_key": content_version_key,
    }
    code, login_body = _request(
        "POST",
        f"{base_url}/auth/login",
        payload=login_payload,
        headers=common_headers,
    )
    _require(code == 200, f"Login failed with HTTP {code}: {_extract_message(login_body)}")

    return SessionInfo(
        access_token=str(login_body.get("access_token", "")),
        refresh_token=str(login_body.get("refresh_token", "")),
        session_id=str(login_body.get("session_id", "")),
        user_id=int(login_body.get("user_id", 0) or 0),
        display_name=str(login_body.get("display_name", "") or display_name),
    )


def _ensure_character(
    *,
    base_url: str,
    session: SessionInfo,
    character_name: str,
    client_version: str,
    content_version_key: str,
) -> int:
    auth_headers = _headers(
        client_version=client_version,
        content_version_key=content_version_key,
        token=session.access_token,
    )

    code, characters_payload = _request("GET", f"{base_url}/characters", headers=auth_headers)
    _require(code == 200, f"Character list failed with HTTP {code}: {_extract_message(characters_payload)}")

    characters_data = characters_payload.get("data", characters_payload)
    _require(isinstance(characters_data, list), "Character list payload is not an array")

    for row in characters_data:
        if not isinstance(row, dict):
            continue
        if str(row.get("name", "")).strip().lower() == character_name.strip().lower():
            return int(row.get("id", 0) or 0)

    create_payload = {
        "name": character_name,
        "preset_key": "sellsword",
        "stats": {},
        "skills": {},
        "equipment": {},
    }
    code, created = _request(
        "POST",
        f"{base_url}/characters",
        payload=create_payload,
        headers=auth_headers,
    )

    if code == 409:
        fallback_name = f"{character_name}-{session.user_id or 'local'}"
        create_payload["name"] = fallback_name
        code, created = _request(
            "POST",
            f"{base_url}/characters",
            payload=create_payload,
            headers=auth_headers,
        )

    _require(code == 200, f"Character create failed with HTTP {code}: {_extract_message(created)}")
    return int(created.get("id", 0) or 0)


def _select_and_bootstrap(
    *,
    base_url: str,
    session: SessionInfo,
    character_id: int,
    client_version: str,
    content_version_key: str,
) -> None:
    auth_headers = _headers(
        client_version=client_version,
        content_version_key=content_version_key,
        token=session.access_token,
    )

    code, body = _request("POST", f"{base_url}/characters/{character_id}/select", payload={}, headers=auth_headers)
    _require(code == 200, f"Character select failed with HTTP {code}: {_extract_message(body)}")

    code, body = _request(
        "POST",
        f"{base_url}/characters/{character_id}/world-bootstrap",
        payload={"override_level_id": None},
        headers=auth_headers,
    )
    _require(code == 200, f"World bootstrap failed with HTTP {code}: {_extract_message(body)}")


def _write_handoff(
    *,
    output_path: Path,
    session: SessionInfo,
    character_id: int,
    email: str,
    base_url: str,
    client_version: str,
    content_version_key: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "email": email,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "session_id": session.session_id,
        "user_id": session.user_id,
        "display_name": session.display_name,
        "character_id": character_id,
        "api_base_url": base_url,
        "client_version": client_version,
        "client_content_version_key": content_version_key,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    base_url = args.base_url.rstrip("/")
    session = _register_or_login(
        base_url=base_url,
        email=args.email,
        password=args.password,
        display_name=args.display_name,
        client_version=args.client_version,
        content_version_key=args.content_version_key,
    )
    _require(session.access_token.strip(), "Missing access_token in auth response")
    _require(session.session_id.strip(), "Missing session_id in auth response")

    character_id = _ensure_character(
        base_url=base_url,
        session=session,
        character_name=args.character_name,
        client_version=args.client_version,
        content_version_key=args.content_version_key,
    )
    _require(character_id > 0, "Failed to resolve character id")

    _select_and_bootstrap(
        base_url=base_url,
        session=session,
        character_id=character_id,
        client_version=args.client_version,
        content_version_key=args.content_version_key,
    )

    output_path = Path(args.output_handoff)
    _write_handoff(
        output_path=output_path,
        session=session,
        character_id=character_id,
        email=args.email,
        base_url=base_url,
        client_version=args.client_version,
        content_version_key=args.content_version_key,
    )

    print("Seed completed.")
    print(f"  user_id: {session.user_id}")
    print(f"  email: {args.email}")
    print(f"  character_id: {character_id}")
    print(f"  handoff_file: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed deterministic local PoC account + character for bootstrap shell")
    parser.add_argument("--base-url", default=os.environ.get("AOP_API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--client-version", default=os.environ.get("AOP_CLIENT_VERSION", DEFAULT_CLIENT_VERSION))
    parser.add_argument(
        "--content-version-key",
        default=os.environ.get("AOP_CLIENT_CONTENT_VERSION_KEY", DEFAULT_CONTENT_VERSION_KEY),
    )
    parser.add_argument("--email", default=os.environ.get("AOP_POC_EMAIL", DEFAULT_EMAIL))
    parser.add_argument("--password", default=os.environ.get("AOP_POC_PASSWORD", DEFAULT_PASSWORD))
    parser.add_argument("--display-name", default=os.environ.get("AOP_POC_DISPLAY_NAME", DEFAULT_DISPLAY_NAME))
    parser.add_argument("--character-name", default=os.environ.get("AOP_POC_CHARACTER_NAME", DEFAULT_CHARACTER_NAME))
    parser.add_argument(
        "--output-handoff",
        default=os.environ.get("AOP_POC_HANDOFF_PATH", "client-app/runtime/startup_handoff.local.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run(args)
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
