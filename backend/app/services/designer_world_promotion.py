from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from app.services.github_publish import GitHubFileChange

ALLOWED_SETTLEMENT_KINDS = {"camp", "village", "town", "city", "fortress"}
ALLOWED_SPAWN_TYPES = {"player", "army", "caravan", "encounter"}
WORLD_STAGE_PATH = Path("backend/runtime/designer_world_stage.json")


@dataclass(frozen=True)
class StagedWorldPack:
    pack_hash: str
    staged_at: str
    staged_by: int
    pack: dict[str, Any]


@dataclass(frozen=True)
class ActivatedWorldPack:
    pack_hash: str
    version_key: str
    file_changes: list[GitHubFileChange]


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_world_pack(pack: dict[str, Any]) -> dict[str, Any]:
    payload = dict(pack)
    payload["manifest_version"] = 1
    payload["province_id"] = str(payload.get("province_id", "")).strip().lower()
    payload["display_name"] = " ".join(str(payload.get("display_name", "")).strip().split())

    settlements = [dict(row) for row in payload.get("settlements", [])]
    for row in settlements:
        row["name"] = " ".join(str(row.get("name", "")).strip().split())
        row["kind"] = str(row.get("kind", "town")).strip().lower()
    settlements.sort(key=lambda row: int(row.get("id", 0)))
    payload["settlements"] = settlements

    routes = [dict(row) for row in payload.get("routes", [])]
    routes.sort(key=lambda row: int(row.get("id", 0)))
    payload["routes"] = routes

    spawns = [dict(row) for row in payload.get("spawn_points", [])]
    for row in spawns:
        row["key"] = str(row.get("key", "")).strip().lower()
        row["spawn_type"] = str(row.get("spawn_type", "")).strip().lower()
    spawns.sort(key=lambda row: int(row.get("id", 0)))
    payload["spawn_points"] = spawns
    return payload


def validate_world_pack(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    settlements = payload.get("settlements", [])
    routes = payload.get("routes", [])
    spawns = payload.get("spawn_points", [])

    if not payload.get("province_id"):
        errors.append("province_id is required")
    if not payload.get("display_name"):
        errors.append("display_name is required")
    if not settlements:
        errors.append("At least one settlement is required")
    if not routes:
        errors.append("At least one route is required")
    if not spawns:
        errors.append("At least one spawn point is required")

    settlement_ids: set[int] = set()
    for row in settlements:
        settlement_id = int(row.get("id", 0))
        if settlement_id <= 0:
            errors.append(f"Settlement id must be > 0 (got {settlement_id})")
            continue
        if settlement_id in settlement_ids:
            errors.append(f"Duplicate settlement id {settlement_id}")
            continue
        settlement_ids.add(settlement_id)
        if not str(row.get("name", "")).strip():
            errors.append(f"Settlement {settlement_id} has empty name")
        kind = str(row.get("kind", "")).strip().lower()
        if kind not in ALLOWED_SETTLEMENT_KINDS:
            errors.append(f"Settlement {settlement_id} has invalid kind '{kind}'")

    route_ids: set[int] = set()
    neighbors: dict[int, set[int]] = defaultdict(set)
    for row in routes:
        route_id = int(row.get("id", 0))
        if route_id <= 0:
            errors.append(f"Route id must be > 0 (got {route_id})")
            continue
        if route_id in route_ids:
            errors.append(f"Duplicate route id {route_id}")
            continue
        route_ids.add(route_id)
        origin = int(row.get("origin", 0))
        destination = int(row.get("destination", 0))
        if origin == destination:
            errors.append(f"Route {route_id} origin equals destination")
            continue
        if origin not in settlement_ids:
            errors.append(f"Route {route_id} references missing origin settlement {origin}")
            continue
        if destination not in settlement_ids:
            errors.append(f"Route {route_id} references missing destination settlement {destination}")
            continue
        if int(row.get("travel_hours", 0)) <= 0:
            errors.append(f"Route {route_id} travel_hours must be > 0")
        neighbors[origin].add(destination)
        neighbors[destination].add(origin)

    spawn_ids: set[int] = set()
    spawn_keys: set[str] = set()
    for row in spawns:
        spawn_id = int(row.get("id", 0))
        if spawn_id <= 0:
            errors.append(f"Spawn id must be > 0 (got {spawn_id})")
            continue
        if spawn_id in spawn_ids:
            errors.append(f"Duplicate spawn id {spawn_id}")
            continue
        spawn_ids.add(spawn_id)
        key = str(row.get("key", "")).strip().lower()
        if not key:
            errors.append(f"Spawn {spawn_id} has empty key")
        elif key in spawn_keys:
            errors.append(f"Duplicate spawn key '{key}'")
        else:
            spawn_keys.add(key)

        settlement_id = int(row.get("settlement_id", 0))
        if settlement_id not in settlement_ids:
            errors.append(f"Spawn {spawn_id} references missing settlement {settlement_id}")
        spawn_type = str(row.get("spawn_type", "")).strip().lower()
        if spawn_type not in ALLOWED_SPAWN_TYPES:
            errors.append(f"Spawn {spawn_id} has invalid spawn_type '{spawn_type}'")

    if settlement_ids:
        start = min(settlement_ids)
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for nxt in neighbors.get(current, set()):
                if nxt in visited:
                    continue
                visited.add(nxt)
                queue.append(nxt)
        missing = sorted(settlement_ids - visited)
        if missing:
            errors.append(f"Route graph is disconnected; unreachable settlement ids: {missing}")

    return errors


def stage_world_pack(pack: dict[str, Any], *, actor_user_id: int) -> StagedWorldPack:
    normalized = normalize_world_pack(pack)
    errors = validate_world_pack(normalized)
    if errors:
        raise ValueError("\n".join(errors))

    canonical = _canonical_json(normalized)
    pack_hash = _sha256_text(canonical)
    staged_at = datetime.now(UTC).isoformat()
    record = {
        "pack_hash": pack_hash,
        "staged_at": staged_at,
        "staged_by": actor_user_id,
        "pack": normalized,
    }
    WORLD_STAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORLD_STAGE_PATH.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return StagedWorldPack(pack_hash=pack_hash, staged_at=staged_at, staged_by=actor_user_id, pack=normalized)


def load_staged_world_pack() -> StagedWorldPack | None:
    if not WORLD_STAGE_PATH.exists():
        return None
    payload = json.loads(WORLD_STAGE_PATH.read_text(encoding="utf-8"))
    return StagedWorldPack(
        pack_hash=str(payload["pack_hash"]),
        staged_at=str(payload["staged_at"]),
        staged_by=int(payload["staged_by"]),
        pack=dict(payload["pack"]),
    )


def clear_staged_world_pack() -> None:
    if WORLD_STAGE_PATH.exists():
        WORLD_STAGE_PATH.unlink()


def activate_staged_world_pack(expected_pack_hash: str | None = None) -> ActivatedWorldPack:
    staged = load_staged_world_pack()
    if staged is None:
        raise ValueError("No staged world pack found")

    canonical = _canonical_json(staged.pack)
    computed_hash = _sha256_text(canonical)
    if computed_hash != staged.pack_hash:
        raise ValueError("Staged world pack hash mismatch")
    if expected_pack_hash and expected_pack_hash.strip() and expected_pack_hash.strip() != computed_hash:
        raise ValueError("Staged world pack hash does not match expected hash")

    province_id = str(staged.pack["province_id"])
    version_key = f"{province_id}_world_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    pack_path = f"assets/content/provinces/{province_id}/{version_key}.json"
    sig_path = f"assets/content/provinces/{province_id}/{version_key}.sig.json"
    latest_path = f"assets/content/provinces/{province_id}/latest.json"

    signature = {
        "schema_version": 1,
        "sha256": computed_hash,
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "designer_world_stage",
    }
    latest = {
        "active_version_key": version_key,
        "active_sha256": computed_hash,
        "activated_at": datetime.now(UTC).isoformat(),
    }

    return ActivatedWorldPack(
        pack_hash=computed_hash,
        version_key=version_key,
        file_changes=[
            GitHubFileChange(path=pack_path, content=json.dumps(staged.pack, indent=2, sort_keys=True) + "\n"),
            GitHubFileChange(path=sig_path, content=json.dumps(signature, indent=2, sort_keys=True) + "\n"),
            GitHubFileChange(path=latest_path, content=json.dumps(latest, indent=2, sort_keys=True) + "\n"),
        ],
    )
