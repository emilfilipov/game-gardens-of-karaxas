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
WORLD_PROMOTION_STATE_DIR = Path("backend/runtime/designer_world_state")
VERSIONS_SCHEMA_VERSION = 1


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


@dataclass(frozen=True)
class DeactivatedWorldPack:
    province_id: str
    version_key: str
    file_changes: list[GitHubFileChange]


@dataclass(frozen=True)
class RolledBackWorldPack:
    province_id: str
    version_key: str
    pack_hash: str
    file_changes: list[GitHubFileChange]


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_pretty(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_province_id(province_id: str) -> str:
    normalized = str(province_id or "").strip().lower()
    if not normalized:
        raise ValueError("province_id is required")
    return normalized


def _repo_pack_paths(province_id: str, version_key: str) -> tuple[str, str]:
    base = f"assets/content/provinces/{province_id}"
    return f"{base}/{version_key}.json", f"{base}/{version_key}.sig.json"


def _repo_latest_path(province_id: str) -> str:
    return f"assets/content/provinces/{province_id}/latest.json"


def _repo_versions_path(province_id: str) -> str:
    return f"assets/content/provinces/{province_id}/versions.json"


def _disk_latest_path(province_id: str) -> Path:
    return Path(_repo_latest_path(province_id))


def _disk_versions_path(province_id: str) -> Path:
    return Path(_repo_versions_path(province_id))


def _runtime_versions_path(province_id: str) -> Path:
    return WORLD_PROMOTION_STATE_DIR / f"{province_id}_versions.json"


def _json_change(path: str, payload: dict[str, Any]) -> GitHubFileChange:
    return GitHubFileChange(path=path, content=_json_pretty(payload))


def _load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON object at {path}")
    return payload


def _synthetic_active_entry(
    *,
    province_id: str,
    version_key: str,
    pack_hash: str,
    activated_at: str,
) -> dict[str, Any]:
    pack_path, signature_path = _repo_pack_paths(province_id, version_key)
    return {
        "version_key": version_key,
        "sha256": pack_hash,
        "pack_path": pack_path,
        "signature_path": signature_path,
        "source": "legacy_latest_pointer",
        "created_at": activated_at,
        "activated_at": activated_at,
        "deactivated_at": None,
        "status": "active",
    }


def _normalize_version_entry(province_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    version_key = str(entry.get("version_key", "")).strip()
    sha256 = str(entry.get("sha256", "")).strip()
    if not version_key or not sha256:
        raise ValueError("versions.json has an entry with missing version_key or sha256")

    pack_path = str(entry.get("pack_path", "")).strip()
    signature_path = str(entry.get("signature_path", "")).strip()
    if not pack_path or not signature_path:
        generated_pack, generated_sig = _repo_pack_paths(province_id, version_key)
        pack_path = pack_path or generated_pack
        signature_path = signature_path or generated_sig

    return {
        "version_key": version_key,
        "sha256": sha256,
        "pack_path": pack_path,
        "signature_path": signature_path,
        "source": str(entry.get("source", "designer_world_stage")).strip() or "designer_world_stage",
        "created_at": str(entry.get("created_at", "")).strip() or _iso_now(),
        "activated_at": _optional_text(entry.get("activated_at")),
        "deactivated_at": _optional_text(entry.get("deactivated_at")),
        "status": str(entry.get("status", "inactive")).strip().lower() or "inactive",
    }


def _find_version_entry(manifest: dict[str, Any], version_key: str) -> dict[str, Any] | None:
    for entry in manifest.get("versions", []):
        if entry.get("version_key") == version_key:
            return entry
    return None


def _sort_versions(manifest: dict[str, Any]) -> None:
    manifest["versions"].sort(
        key=lambda row: (
            str(row.get("created_at") or ""),
            str(row.get("version_key") or ""),
        )
    )


def _persist_runtime_manifest(province_id: str, manifest: dict[str, Any]) -> None:
    runtime_path = _runtime_versions_path(province_id)
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text(_json_pretty(manifest), encoding="utf-8")


def _load_versions_manifest(province_id: str) -> dict[str, Any]:
    normalized_province = _normalize_province_id(province_id)
    runtime_payload = _load_json_file(_runtime_versions_path(normalized_province))
    if runtime_payload is not None:
        versions_payload = runtime_payload
        latest_payload: dict[str, Any] | None = {
            "active_version_key": runtime_payload.get("active_version_key"),
            "active_sha256": runtime_payload.get("active_sha256"),
            "activated_at": runtime_payload.get("updated_at"),
        }
    else:
        versions_payload = _load_json_file(_disk_versions_path(normalized_province))
        latest_payload = _load_json_file(_disk_latest_path(normalized_province))

    if versions_payload is None:
        versions_payload = {
            "schema_version": VERSIONS_SCHEMA_VERSION,
            "province_id": normalized_province,
            "active_version_key": None,
            "active_sha256": None,
            "updated_at": None,
            "versions": [],
        }

    if str(versions_payload.get("province_id", "")).strip().lower() != normalized_province:
        raise ValueError("versions.json province_id mismatch")

    normalized_versions: list[dict[str, Any]] = []
    for row in versions_payload.get("versions", []):
        if not isinstance(row, dict):
            raise ValueError("versions.json versions[] entries must be objects")
        normalized_versions.append(_normalize_version_entry(normalized_province, row))

    active_version_key = _optional_text(versions_payload.get("active_version_key"))
    active_sha256 = _optional_text(versions_payload.get("active_sha256"))

    if latest_payload:
        latest_active_version = str(latest_payload.get("active_version_key", "")).strip() or None
        latest_active_sha = str(latest_payload.get("active_sha256", "")).strip() or None
        latest_activated_at = str(latest_payload.get("activated_at", "")).strip() or _iso_now()

        if latest_active_version and latest_active_sha:
            if not active_version_key:
                active_version_key = latest_active_version
            if not active_sha256:
                active_sha256 = latest_active_sha
            if _find_version_entry({"versions": normalized_versions}, latest_active_version) is None:
                normalized_versions.append(
                    _synthetic_active_entry(
                        province_id=normalized_province,
                        version_key=latest_active_version,
                        pack_hash=latest_active_sha,
                        activated_at=latest_activated_at,
                    )
                )

    manifest = {
        "schema_version": int(versions_payload.get("schema_version", VERSIONS_SCHEMA_VERSION)),
        "province_id": normalized_province,
        "active_version_key": active_version_key,
        "active_sha256": active_sha256,
        "updated_at": _optional_text(versions_payload.get("updated_at")),
        "versions": normalized_versions,
    }

    if manifest["active_version_key"]:
        active_entry = _find_version_entry(manifest, manifest["active_version_key"])
        if active_entry is None:
            manifest["versions"].append(
                _synthetic_active_entry(
                    province_id=normalized_province,
                    version_key=str(manifest["active_version_key"]),
                    pack_hash=str(manifest.get("active_sha256") or ""),
                    activated_at=manifest.get("updated_at") or _iso_now(),
                )
            )
            active_entry = _find_version_entry(manifest, str(manifest["active_version_key"]))
        if active_entry is not None:
            active_entry["status"] = "active"
            if not active_entry.get("activated_at"):
                active_entry["activated_at"] = _iso_now()

    _sort_versions(manifest)
    return manifest


def _write_versions_state_changes(
    *,
    province_id: str,
    manifest: dict[str, Any],
    active_version_key: str | None,
    active_sha256: str | None,
    activated_at: str,
) -> list[GitHubFileChange]:
    manifest["schema_version"] = VERSIONS_SCHEMA_VERSION
    manifest["province_id"] = province_id
    manifest["active_version_key"] = active_version_key
    manifest["active_sha256"] = active_sha256
    manifest["updated_at"] = activated_at
    _sort_versions(manifest)
    _persist_runtime_manifest(province_id, manifest)

    latest_payload = {
        "active_version_key": active_version_key,
        "active_sha256": active_sha256,
        "activated_at": activated_at,
    }

    return [
        _json_change(_repo_latest_path(province_id), latest_payload),
        _json_change(_repo_versions_path(province_id), manifest),
    ]


def _next_version_key(manifest: dict[str, Any], province_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    existing = {str(row.get("version_key", "")) for row in manifest.get("versions", [])}
    candidate = f"{province_id}_world_{stamp}"
    if candidate not in existing:
        return candidate

    suffix = 1
    while True:
        with_suffix = f"{candidate}_{suffix:02d}"
        if with_suffix not in existing:
            return with_suffix
        suffix += 1


def _deactivate_active_entry(manifest: dict[str, Any], deactivated_at: str) -> str | None:
    active_version_key = str(manifest.get("active_version_key") or "").strip() or None
    if not active_version_key:
        return None

    active_entry = _find_version_entry(manifest, active_version_key)
    if active_entry is not None:
        active_entry["status"] = "inactive"
        active_entry["deactivated_at"] = deactivated_at
        if not active_entry.get("activated_at"):
            active_entry["activated_at"] = deactivated_at

    manifest["active_version_key"] = None
    manifest["active_sha256"] = None
    return active_version_key


def normalize_world_pack(pack: dict[str, Any]) -> dict[str, Any]:
    payload = dict(pack)
    payload["manifest_version"] = 1
    payload["province_id"] = _normalize_province_id(str(payload.get("province_id", "")))
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
    staged_at = _iso_now()
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

    province_id = _normalize_province_id(str(staged.pack["province_id"]))
    manifest = _load_versions_manifest(province_id)

    activated_at = _iso_now()
    _deactivate_active_entry(manifest, activated_at)

    version_key = _next_version_key(manifest, province_id)
    pack_path, sig_path = _repo_pack_paths(province_id, version_key)

    manifest["versions"].append(
        {
            "version_key": version_key,
            "sha256": computed_hash,
            "pack_path": pack_path,
            "signature_path": sig_path,
            "source": "designer_world_stage",
            "created_at": activated_at,
            "activated_at": activated_at,
            "deactivated_at": None,
            "status": "active",
        }
    )

    signature = {
        "schema_version": 1,
        "sha256": computed_hash,
        "generated_at": activated_at,
        "source": "designer_world_stage",
    }

    file_changes = [
        _json_change(pack_path, staged.pack),
        _json_change(sig_path, signature),
        *_write_versions_state_changes(
            province_id=province_id,
            manifest=manifest,
            active_version_key=version_key,
            active_sha256=computed_hash,
            activated_at=activated_at,
        ),
    ]

    return ActivatedWorldPack(
        pack_hash=computed_hash,
        version_key=version_key,
        file_changes=file_changes,
    )


def deactivate_active_world_pack(province_id: str) -> DeactivatedWorldPack:
    normalized_province = _normalize_province_id(province_id)
    manifest = _load_versions_manifest(normalized_province)
    deactivated_at = _iso_now()

    version_key = _deactivate_active_entry(manifest, deactivated_at)
    if not version_key:
        raise ValueError(f"No active world pack found for province '{normalized_province}'")

    file_changes = _write_versions_state_changes(
        province_id=normalized_province,
        manifest=manifest,
        active_version_key=None,
        active_sha256=None,
        activated_at=deactivated_at,
    )
    return DeactivatedWorldPack(
        province_id=normalized_province,
        version_key=version_key,
        file_changes=file_changes,
    )


def rollback_world_pack_version(province_id: str, target_version_key: str | None = None) -> RolledBackWorldPack:
    normalized_province = _normalize_province_id(province_id)
    manifest = _load_versions_manifest(normalized_province)
    versions: list[dict[str, Any]] = list(manifest.get("versions", []))
    if not versions:
        raise ValueError(f"No world pack versions found for province '{normalized_province}'")

    active_version_key = str(manifest.get("active_version_key") or "").strip() or None

    normalized_target = str(target_version_key or "").strip()
    target_entry: dict[str, Any] | None = None
    if normalized_target:
        target_entry = _find_version_entry(manifest, normalized_target)
        if target_entry is None:
            raise ValueError(f"Unknown rollback target version '{normalized_target}'")
    else:
        candidates = [row for row in versions if str(row.get("version_key", "")) != (active_version_key or "")]
        if not candidates:
            raise ValueError(f"No rollback target available for province '{normalized_province}'")
        candidates.sort(
            key=lambda row: (
                str(row.get("activated_at") or ""),
                str(row.get("created_at") or ""),
                str(row.get("version_key") or ""),
            )
        )
        target_entry = candidates[-1]

    if target_entry is None:
        raise ValueError("Unable to resolve rollback target")

    target_key = str(target_entry.get("version_key", "")).strip()
    if active_version_key and target_key == active_version_key:
        raise ValueError(f"Version '{target_key}' is already active")

    rolled_back_at = _iso_now()
    _deactivate_active_entry(manifest, rolled_back_at)

    target_entry["status"] = "active"
    target_entry["activated_at"] = rolled_back_at
    target_entry["deactivated_at"] = None

    target_hash = str(target_entry.get("sha256", "")).strip()
    if not target_hash:
        raise ValueError(f"Rollback target '{target_key}' is missing sha256")

    file_changes = _write_versions_state_changes(
        province_id=normalized_province,
        manifest=manifest,
        active_version_key=target_key,
        active_sha256=target_hash,
        activated_at=rolled_back_at,
    )
    return RolledBackWorldPack(
        province_id=normalized_province,
        version_key=target_key,
        pack_hash=target_hash,
        file_changes=file_changes,
    )
