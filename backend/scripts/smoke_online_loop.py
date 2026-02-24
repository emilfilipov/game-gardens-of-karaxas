#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import string
import sys
import time
import urllib.error
import urllib.request

import pyotp


def _request(method: str, url: str, payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    body = None
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, method=method, data=body, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return resp.getcode(), json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed = {}
        if raw:
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"raw": raw}
        return exc.code, parsed


def _rand_slug(length: int = 10) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run(base_url: str) -> None:
    base = base_url.rstrip("/")
    suffix = _rand_slug(8)
    email = f"smoke_{suffix}@example.com"
    password = "SmokeTestPass123!"
    display_name = f"smoke_{suffix}"

    common_headers = {
        "X-Client-Version": "smoke-1.0.0",
        "X-Client-Content-Version": "runtime_gameplay_v1",
    }

    code, register_body = _request(
        "POST",
        f"{base}/auth/register",
        {"email": email, "password": password, "display_name": display_name},
        headers=common_headers,
    )
    _assert(code == 200, f"register failed: {code} {register_body}")
    access_token = register_body["access_token"]
    refresh_token = register_body["refresh_token"]
    auth_headers = dict(common_headers)
    auth_headers["Authorization"] = f"Bearer {access_token}"

    code, _ = _request("GET", f"{base}/auth/mfa/status", headers=auth_headers)
    _assert(code == 200, f"mfa status failed: {code}")

    code, _ = _request("POST", f"{base}/auth/mfa/enable", {}, headers=auth_headers)
    _assert(code == 200, f"mfa enable failed: {code}")

    code, qr_body = _request("GET", f"{base}/auth/mfa/qr", headers=auth_headers)
    _assert(code == 200 and qr_body.get("secret"), f"mfa qr failed: {code} {qr_body}")
    otp_code = pyotp.TOTP(qr_body["secret"]).now()

    code, _ = _request(
        "POST",
        f"{base}/auth/login",
        {"email": email, "password": password, "client_version": "smoke-1.0.0", "client_content_version_key": "runtime_gameplay_v1"},
        headers=common_headers,
    )
    _assert(code == 401, "login without otp should fail when mfa enabled")

    code, login_body = _request(
        "POST",
        f"{base}/auth/login",
        {
            "email": email,
            "password": password,
            "otp_code": otp_code,
            "client_version": "smoke-1.0.0",
            "client_content_version_key": "runtime_gameplay_v1",
        },
        headers=common_headers,
    )
    _assert(code == 200, f"login with mfa failed: {code} {login_body}")
    access_token = login_body["access_token"]
    refresh_token = login_body["refresh_token"]
    auth_headers["Authorization"] = f"Bearer {access_token}"

    code, _ = _request("POST", f"{base}/auth/mfa/disable", {}, headers=auth_headers)
    _assert(code == 200, f"mfa disable failed: {code}")

    code, refresh_body = _request(
        "POST",
        f"{base}/auth/refresh",
        {
            "refresh_token": refresh_token,
            "client_version": "smoke-1.0.0",
            "client_content_version_key": "runtime_gameplay_v1",
        },
        headers=common_headers,
    )
    _assert(code == 200, f"refresh failed: {code} {refresh_body}")
    access_token = refresh_body["access_token"]
    auth_headers["Authorization"] = f"Bearer {access_token}"

    code, create_char = _request(
        "POST",
        f"{base}/characters",
        {"name": f"smokechar_{suffix}", "preset_key": "sellsword", "stats": {}, "skills": {}, "equipment": {}},
        headers=auth_headers,
    )
    _assert(code == 200, f"character create failed: {code} {create_char}")
    character_id = int(create_char["id"])

    code, bootstrap = _request(
        "POST",
        f"{base}/characters/{character_id}/world-bootstrap",
        {},
        headers=auth_headers,
    )
    _assert(code == 200, f"world bootstrap failed: {code} {bootstrap}")
    _assert("instance" in bootstrap and "level" in bootstrap, "world bootstrap missing instance/level")
    spawn = bootstrap.get("spawn", {})
    runtime_descriptor = bootstrap.get("runtime", {})
    level_payload = bootstrap.get("level", {})
    _assert(isinstance(spawn.get("yaw_deg", 0.0), (int, float)), "world bootstrap missing spawn yaw_deg")
    _assert(isinstance(spawn.get("world_z", 0.0), (int, float)), "world bootstrap missing spawn world_z")
    _assert(str(runtime_descriptor.get("camera_profile_key", "")).strip() != "", "world bootstrap missing runtime camera_profile_key")
    map_scale = level_payload.get("map_scale", {})
    _assert(isinstance(map_scale, dict) and "tile_world_size" in map_scale, "world bootstrap missing level map_scale metadata")
    _assert(str(level_payload.get("scene_variant_hint", "")).strip() != "", "world bootstrap missing scene_variant_hint")

    code, _ = _request(
        "POST",
        f"{base}/characters/{character_id}/location",
        {"level_id": int(bootstrap["level"]["id"]), "location_x": 123, "location_y": 456},
        headers=auth_headers,
    )
    _assert(code == 200, f"location update failed: {code}")

    code, gameplay = _request(
        "POST",
        f"{base}/gameplay/resolve-action",
        {
            "character_id": character_id,
            "action_nonce": f"nonce-{_rand_slug(12)}",
            "action_type": "skill",
            "skill_key": "ember",
            "reported_x": 124,
            "reported_y": 457,
            "delta_seconds": 0.2,
            "enemies_defeated": 2,
            "requested_loot_tier": 1,
        },
        headers=auth_headers,
    )
    _assert(code == 200 and gameplay.get("accepted") is True, f"gameplay resolve failed: {code} {gameplay}")

    code, chars = _request("GET", f"{base}/characters", headers=auth_headers)
    _assert(code == 200 and isinstance(chars, list), f"character list failed: {code} {chars}")
    row = next((c for c in chars if int(c.get("id", -1)) == character_id), None)
    _assert(row is not None, "character missing from list")
    _assert(int(row.get("location_x", -1)) == 124 and int(row.get("location_y", -1)) == 457, "location not persisted")
    _assert(isinstance(row.get("inventory", []), list), "inventory missing in character response")

    print("Smoke online loop passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Children of Ikphelion online loop smoke harness")
    parser.add_argument("--base-url", required=True, help="Backend base URL, e.g. https://...run.app")
    args = parser.parse_args()
    try:
        run(args.base_url)
    except Exception as exc:
        print(f"Smoke online loop failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
