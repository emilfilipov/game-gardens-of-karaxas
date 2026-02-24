from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings


@dataclass
class RuntimeGameplayConfig:
    config_key: str
    content_contract_signature: str
    fetched_at: datetime
    domains: dict[str, dict]
    source_path: str
    schema_version: int
    version: int


class RuntimeConfigValidationError(ValueError):
    pass


class RuntimeMetaModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: int = Field(default=1, ge=1, le=99)
    config_key: str = Field(default="runtime_gameplay_v1", min_length=1, max_length=128)
    version: int = Field(default=1, ge=1, le=1_000_000)
    title: str | None = Field(default=None, max_length=255)


class RuntimeDocumentModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    meta: RuntimeMetaModel
    domains: dict[str, dict] = Field(default_factory=dict)


def _fallback_domains() -> dict[str, dict]:
    return {
        "meta": {
            "schema_version": 1,
            "config_key": "runtime_gameplay_v1",
            "version": 1,
            "title": "Embedded fallback runtime config",
        },
        "character_options": {
            "point_budget": 10,
            "race": [{"value": "human", "label": "Human"}],
            "background": [{"value": "drifter", "label": "Drifter"}],
            "affiliation": [{"value": "unaffiliated", "label": "Unaffiliated"}],
        },
        "character_presets": {
            "entries": [
                {
                    "key": "sellsword",
                    "label": "Sellsword",
                    "description": "Hardened sword-for-hire template.",
                    "appearance_key": "human_male",
                    "race": "Human",
                    "background": "Drifter",
                    "affiliation": "Unaffiliated",
                    "point_budget": 10,
                    "stats": {"strength": 2, "agility": 2, "intellect": 2, "vitality": 2},
                    "skills": {"ember": 1},
                    "starting_inventory": [{"item_key": "traveler_knife", "qty": 1}],
                }
            ]
        },
        "stats": {
            "max_per_stat": 10,
            "entries": [
                {"key": "strength", "label": "Strength", "description": "Physical power."},
                {"key": "agility", "label": "Agility", "description": "Speed and reflexes."},
                {"key": "intellect", "label": "Intellect", "description": "Spell scaling."},
                {"key": "vitality", "label": "Vitality", "description": "Maximum health."},
            ],
        },
        "skills": {
            "entries": [
                {"key": "ember", "label": "Ember", "damage_base": 20, "intelligence_scale": 0.35},
                {"key": "cleave", "label": "Cleave", "damage_base": 14, "strength_scale": 0.50},
                {"key": "quick_strike", "label": "Quick Strike", "damage_base": 16, "agility_scale": 0.45},
                {"key": "bandage", "label": "Bandage", "heal_base": 18, "cooldown": 8.0},
            ],
        },
        "movement": {
            "player_speed_tiles": 4.6,
            "player_radius": 14.0,
        },
        "runtime_client": {
            "world_renderer": "3d",
            "camera_profile_key": "arpg_poe_baseline",
        },
        "world_3d": {
            "camera_profile_key": "arpg_poe_baseline",
        },
        "combat": {
            "resource_pool": "mana",
            "basic_attack": {"damage": 8.0, "range": 1.3, "cooldown": 0.45},
            "abilities": [],
        },
        "progression": {
            "xp_per_level": 100,
            "xp_per_enemy": 12,
        },
        "loot": {
            "tiers": {
                "1": ["scrap_shard", "cracked_rune"],
            }
        },
    }


def _candidate_runtime_paths() -> list[Path]:
    configured = Path(settings.runtime_gameplay_config_path).expanduser()
    repo_default = Path(__file__).resolve().parents[2] / "runtime" / "gameplay_config.json"
    container_default = Path("/app/runtime/gameplay_config.json")
    return [configured, repo_default, container_default]


def _required_domain_keys() -> set[str]:
    return {"character_options", "character_presets", "stats", "skills", "movement", "combat", "progression", "loot"}


def _normalize_document(payload: dict) -> dict:
    if "domains" in payload and isinstance(payload.get("domains"), dict):
        document = dict(payload)
    else:
        # Backward compatibility: treat root object as domains object when `domains` is absent.
        domains = {str(k): v for k, v in payload.items() if isinstance(v, dict)}
        meta = domains.pop("meta", {})
        document = {"meta": meta, "domains": domains}
    return document


def _validate_document(payload: dict) -> RuntimeDocumentModel:
    document = _normalize_document(payload)
    try:
        parsed = RuntimeDocumentModel.model_validate(document)
    except ValidationError as exc:
        raise RuntimeConfigValidationError(f"runtime_config_validation_failed: {exc}") from exc
    missing = sorted(_required_domain_keys() - set(parsed.domains.keys()))
    if missing:
        raise RuntimeConfigValidationError(f"runtime_config_missing_domains: {', '.join(missing)}")
    for key, value in parsed.domains.items():
        if not isinstance(value, dict):
            raise RuntimeConfigValidationError(f"runtime_config_domain_not_object: {key}")
    return parsed


def _canonical_domains(domains: dict[str, dict]) -> dict[str, dict]:
    return {str(k): v for k, v in domains.items() if isinstance(v, dict)}


def _load_document_from_disk(path: Path) -> RuntimeDocumentModel:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeConfigValidationError("runtime_config_payload_not_object")
    return _validate_document(payload)


def _load_document_with_path(channel: str = "active") -> tuple[RuntimeDocumentModel, str]:
    if channel == "staged":
        path = Path(settings.runtime_gameplay_staged_config_path).expanduser()
        if not path.exists():
            raise RuntimeConfigValidationError("staged_runtime_config_not_found")
        try:
            return _load_document_from_disk(path), str(path)
        except Exception as exc:
            raise RuntimeConfigValidationError(f"staged_runtime_config_invalid: {exc}") from exc

    for path in _candidate_runtime_paths():
        if not path.exists():
            continue
        try:
            return _load_document_from_disk(path), str(path)
        except Exception:
            continue
    fallback = _validate_document(_fallback_domains())
    return fallback, "embedded_fallback"


def _contract_signature(domains: dict[str, dict]) -> str:
    encoded = json.dumps(domains, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _enforce_signature_pin(signature: str) -> None:
    pin = (settings.runtime_gameplay_signature_pin or "").strip().lower()
    if pin and pin != signature.lower():
        raise RuntimeConfigValidationError("runtime_config_signature_pin_mismatch")


def load_runtime_gameplay_config(channel: str = "active") -> RuntimeGameplayConfig:
    document, source_path = _load_document_with_path(channel=channel)
    domains = _canonical_domains(document.domains)
    signature = _contract_signature(domains)
    _enforce_signature_pin(signature)
    return RuntimeGameplayConfig(
        config_key=document.meta.config_key,
        content_contract_signature=signature,
        fetched_at=datetime.now(UTC),
        domains=domains,
        source_path=source_path,
        schema_version=int(document.meta.schema_version),
        version=int(document.meta.version),
    )


def _write_runtime_document(path: Path, document: RuntimeDocumentModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = {
        "meta": document.meta.model_dump(mode="json"),
        "domains": _canonical_domains(document.domains),
    }
    path.write_text(json.dumps(serialized, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def stage_runtime_gameplay_config(payload: dict) -> RuntimeGameplayConfig:
    if not isinstance(payload, dict):
        raise RuntimeConfigValidationError("runtime_config_payload_not_object")
    document = _validate_document(payload)
    staged_path = Path(settings.runtime_gameplay_staged_config_path).expanduser()
    _write_runtime_document(staged_path, document)
    return load_runtime_gameplay_config(channel="staged")


def publish_staged_runtime_gameplay_config() -> RuntimeGameplayConfig:
    staged_path = Path(settings.runtime_gameplay_staged_config_path).expanduser()
    if not staged_path.exists():
        raise RuntimeConfigValidationError("staged_runtime_config_not_found")
    active_path = Path(settings.runtime_gameplay_config_path).expanduser()
    backup_path = Path(settings.runtime_gameplay_backup_config_path).expanduser()

    document = _load_document_from_disk(staged_path)
    if active_path.exists():
        active_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(active_path.read_text(encoding="utf-8"), encoding="utf-8")
    _write_runtime_document(active_path, document)
    staged_path.unlink(missing_ok=True)
    return load_runtime_gameplay_config(channel="active")


def rollback_runtime_gameplay_config() -> RuntimeGameplayConfig:
    active_path = Path(settings.runtime_gameplay_config_path).expanduser()
    backup_path = Path(settings.runtime_gameplay_backup_config_path).expanduser()
    if not backup_path.exists():
        raise RuntimeConfigValidationError("runtime_config_backup_not_found")
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
    return load_runtime_gameplay_config(channel="active")


def runtime_gameplay_config_status() -> dict:
    active: RuntimeGameplayConfig | None = None
    staged: RuntimeGameplayConfig | None = None
    active_error: str | None = None
    staged_error: str | None = None
    try:
        active = load_runtime_gameplay_config(channel="active")
    except Exception as exc:
        active_error = str(exc)
    try:
        staged = load_runtime_gameplay_config(channel="staged")
    except Exception as exc:
        staged_error = str(exc)
    return {
        "active": {
            "config_key": active.config_key if active else None,
            "signature": active.content_contract_signature if active else None,
            "schema_version": active.schema_version if active else None,
            "version": active.version if active else None,
            "source_path": active.source_path if active else None,
            "error": active_error,
        },
        "staged": {
            "config_key": staged.config_key if staged else None,
            "signature": staged.content_contract_signature if staged else None,
            "schema_version": staged.schema_version if staged else None,
            "version": staged.version if staged else None,
            "source_path": staged.source_path if staged else None,
            "error": staged_error,
        },
        "signature_pin": (settings.runtime_gameplay_signature_pin or "").strip().lower() or None,
        "timestamp": datetime.now(UTC).isoformat(),
    }
