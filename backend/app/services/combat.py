from __future__ import annotations

from app.services.content import CONTENT_DOMAIN_SKILLS, ContentSnapshot


def _skill_entries(snapshot: ContentSnapshot) -> list[dict]:
    domain = snapshot.domain(CONTENT_DOMAIN_SKILLS)
    entries = domain.get("entries")
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def get_skill_definition(snapshot: ContentSnapshot, skill_key: str) -> dict:
    normalized = skill_key.strip().lower()
    for entry in _skill_entries(snapshot):
        if str(entry.get("key", "")).strip().lower() == normalized:
            return entry
    raise KeyError(f"Unknown skill '{skill_key}'")


def compute_skill_damage(
    snapshot: ContentSnapshot,
    skill_key: str,
    intelligence: float,
    additive_bonus: float = 0.0,
    multiplier: float = 1.0,
) -> float:
    skill = get_skill_definition(snapshot, skill_key)
    base = float(skill.get("damage_base", 0.0))
    int_scale = float(skill.get("intelligence_scale", 0.0))
    raw = (base + (float(intelligence) * int_scale) + float(additive_bonus)) * float(multiplier)
    return round(raw, 4)
