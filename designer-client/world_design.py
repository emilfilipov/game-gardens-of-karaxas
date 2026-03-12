"""World-design primitives, validation, and deterministic export helpers."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from copy import deepcopy
from datetime import UTC, datetime

ALLOWED_SETTLEMENT_KINDS = {"camp", "village", "town", "city", "fortress"}
ALLOWED_SPAWN_TYPES = {"player", "army", "caravan", "encounter"}
WORLD_MANIFEST_VERSION = 1


def default_world_pack() -> dict:
    return {
        "manifest_version": WORLD_MANIFEST_VERSION,
        "province_id": "acre",
        "display_name": "Acre (Designer Draft)",
        "settlements": [
            {"id": 1, "name": "Acre Port", "map_x": -280, "map_y": 60, "kind": "city"},
            {"id": 2, "name": "Montmusard Camp", "map_x": -250, "map_y": 120, "kind": "camp"},
            {"id": 3, "name": "Tyre Outskirts", "map_x": -140, "map_y": 40, "kind": "village"},
            {"id": 4, "name": "Sidon Market", "map_x": -20, "map_y": 20, "kind": "town"},
            {"id": 5, "name": "Kerak Fortress", "map_x": 280, "map_y": -140, "kind": "fortress"},
        ],
        "routes": [
            {"id": 10, "origin": 1, "destination": 2, "travel_hours": 2, "base_risk": 10, "is_sea_route": False},
            {"id": 11, "origin": 2, "destination": 3, "travel_hours": 3, "base_risk": 18, "is_sea_route": False},
            {"id": 12, "origin": 3, "destination": 4, "travel_hours": 3, "base_risk": 16, "is_sea_route": False},
            {"id": 13, "origin": 4, "destination": 5, "travel_hours": 7, "base_risk": 26, "is_sea_route": False},
        ],
        "spawn_points": [
            {"id": 1, "key": "player_acre_start", "settlement_id": 1, "spawn_type": "player"},
            {"id": 2, "key": "caravan_tyre_lane", "settlement_id": 3, "spawn_type": "caravan"},
            {"id": 3, "key": "encounter_kerak", "settlement_id": 5, "spawn_type": "encounter"},
        ],
    }


def normalize_world_pack(pack: dict) -> dict:
    normalized = deepcopy(pack)
    normalized["manifest_version"] = WORLD_MANIFEST_VERSION
    normalized["province_id"] = str(normalized.get("province_id", "")).strip().lower()
    normalized["display_name"] = " ".join(str(normalized.get("display_name", "")).strip().split())

    settlements = normalized.get("settlements", [])
    for settlement in settlements:
        settlement["name"] = " ".join(str(settlement.get("name", "")).strip().split())
        settlement["kind"] = str(settlement.get("kind", "town")).strip().lower()
    settlements.sort(key=lambda row: int(row.get("id", 0)))

    routes = normalized.get("routes", [])
    routes.sort(key=lambda row: int(row.get("id", 0)))

    spawns = normalized.get("spawn_points", [])
    for spawn in spawns:
        spawn["key"] = str(spawn.get("key", "")).strip().lower()
        spawn["spawn_type"] = str(spawn.get("spawn_type", "encounter")).strip().lower()
    spawns.sort(key=lambda row: int(row.get("id", 0)))

    return normalized


def validate_world_pack(pack: dict) -> list[str]:
    errors: list[str] = []
    settlements = pack.get("settlements", [])
    routes = pack.get("routes", [])
    spawns = pack.get("spawn_points", [])

    if not str(pack.get("province_id", "")).strip():
        errors.append("province_id is required")
    if not str(pack.get("display_name", "")).strip():
        errors.append("display_name is required")

    if not settlements:
        errors.append("At least one settlement is required")
    if not routes:
        errors.append("At least one route is required")
    if not spawns:
        errors.append("At least one spawn point is required")

    settlement_ids: set[int] = set()
    for settlement in settlements:
        settlement_id = int(settlement.get("id", 0))
        if settlement_id <= 0:
            errors.append(f"Settlement id must be > 0 (got {settlement_id})")
            continue
        if settlement_id in settlement_ids:
            errors.append(f"Duplicate settlement id {settlement_id}")
            continue
        settlement_ids.add(settlement_id)
        if not str(settlement.get("name", "")).strip():
            errors.append(f"Settlement {settlement_id} has empty name")
        kind = str(settlement.get("kind", "")).strip().lower()
        if kind not in ALLOWED_SETTLEMENT_KINDS:
            errors.append(f"Settlement {settlement_id} has invalid kind '{kind}'")

    route_ids: set[int] = set()
    neighbors: dict[int, set[int]] = defaultdict(set)
    for route in routes:
        route_id = int(route.get("id", 0))
        if route_id <= 0:
            errors.append(f"Route id must be > 0 (got {route_id})")
            continue
        if route_id in route_ids:
            errors.append(f"Duplicate route id {route_id}")
            continue
        route_ids.add(route_id)
        origin = int(route.get("origin", 0))
        destination = int(route.get("destination", 0))
        if origin == destination:
            errors.append(f"Route {route_id} origin equals destination")
            continue
        if origin not in settlement_ids:
            errors.append(f"Route {route_id} references missing origin settlement {origin}")
            continue
        if destination not in settlement_ids:
            errors.append(f"Route {route_id} references missing destination settlement {destination}")
            continue
        travel_hours = int(route.get("travel_hours", 0))
        if travel_hours <= 0:
            errors.append(f"Route {route_id} travel_hours must be > 0")
        neighbors[origin].add(destination)
        neighbors[destination].add(origin)

    spawn_ids: set[int] = set()
    spawn_keys: set[str] = set()
    for spawn in spawns:
        spawn_id = int(spawn.get("id", 0))
        if spawn_id <= 0:
            errors.append(f"Spawn id must be > 0 (got {spawn_id})")
            continue
        if spawn_id in spawn_ids:
            errors.append(f"Duplicate spawn id {spawn_id}")
            continue
        spawn_ids.add(spawn_id)

        key = str(spawn.get("key", "")).strip().lower()
        if not key:
            errors.append(f"Spawn {spawn_id} has empty key")
        elif key in spawn_keys:
            errors.append(f"Duplicate spawn key '{key}'")
        else:
            spawn_keys.add(key)

        settlement_id = int(spawn.get("settlement_id", 0))
        if settlement_id not in settlement_ids:
            errors.append(f"Spawn {spawn_id} references missing settlement {settlement_id}")
        spawn_type = str(spawn.get("spawn_type", "")).strip().lower()
        if spawn_type not in ALLOWED_SPAWN_TYPES:
            errors.append(f"Spawn {spawn_id} has invalid spawn_type '{spawn_type}'")

    if settlement_ids:
        start = min(settlement_ids)
        visited = set([start])
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


def canonical_pack_json(pack: dict) -> str:
    return json.dumps(normalize_world_pack(pack), separators=(",", ":"), sort_keys=True)


def world_pack_sha256(pack: dict) -> str:
    return hashlib.sha256(canonical_pack_json(pack).encode("utf-8")).hexdigest()


def signature_payload(pack: dict) -> dict:
    return {
        "schema_version": 1,
        "sha256": world_pack_sha256(pack),
        "generated_at": datetime.now(UTC).isoformat(),
    }
