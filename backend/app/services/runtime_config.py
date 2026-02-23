from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from app.core.config import settings


@dataclass
class RuntimeGameplayConfig:
    config_key: str
    content_contract_signature: str
    fetched_at: datetime
    domains: dict[str, dict]
    source_path: str


def _fallback_domains() -> dict[str, dict]:
    return {
        "character_options": {
            "point_budget": 10,
            "race": [{"value": "human", "label": "Human"}],
            "background": [{"value": "drifter", "label": "Drifter"}],
            "affiliation": [{"value": "unaffiliated", "label": "Unaffiliated"}],
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
    }


def _candidate_runtime_paths() -> list[Path]:
    configured = Path(settings.runtime_gameplay_config_path).expanduser()
    repo_default = Path(__file__).resolve().parents[2] / "runtime" / "gameplay_config.json"
    container_default = Path("/app/runtime/gameplay_config.json")
    return [configured, repo_default, container_default]


def _load_domains_from_disk() -> tuple[dict[str, dict], str]:
    for path in _candidate_runtime_paths():
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                domains = payload.get("domains", payload)
                if isinstance(domains, dict):
                    normalized = {str(k): v for k, v in domains.items() if isinstance(v, dict)}
                    if normalized:
                        return normalized, str(path)
        except Exception:
            continue
    return _fallback_domains(), "embedded_fallback"


def _contract_signature(domains: dict[str, dict]) -> str:
    encoded = json.dumps(domains, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_runtime_gameplay_config() -> RuntimeGameplayConfig:
    domains, source_path = _load_domains_from_disk()
    meta = domains.get("meta", {})
    config_key = str(meta.get("config_key", "runtime_gameplay_v1")).strip() or "runtime_gameplay_v1"
    return RuntimeGameplayConfig(
        config_key=config_key,
        content_contract_signature=_contract_signature(domains),
        fetched_at=datetime.now(UTC),
        domains=domains,
        source_path=source_path,
    )
