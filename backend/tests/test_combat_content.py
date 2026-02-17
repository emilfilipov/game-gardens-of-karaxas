from datetime import UTC, datetime

from app.services.combat import compute_skill_damage
from app.services.content import CONTENT_SCHEMA_VERSION, ContentSnapshot, DEFAULT_CONTENT_DOMAINS


def _snapshot() -> ContentSnapshot:
    return ContentSnapshot(
        schema_version=CONTENT_SCHEMA_VERSION,
        content_version_id=1,
        content_version_key="cv_test",
        loaded_at=datetime.now(UTC),
        domains=DEFAULT_CONTENT_DOMAINS,
    )


def test_ember_damage_scales_with_intelligence_and_modifiers() -> None:
    snapshot = _snapshot()
    damage = compute_skill_damage(
        snapshot,
        "ember",
        intelligence=30,
        additive_bonus=5,
        multiplier=1.1,
    )
    # (base=20 + 30*0.6 + 5) * 1.1 = 47.3
    assert damage == 47.3


def test_skill_damage_is_deterministic_for_same_inputs() -> None:
    snapshot = _snapshot()
    first = compute_skill_damage(snapshot, "ember", intelligence=21, additive_bonus=2.5, multiplier=1.0)
    second = compute_skill_damage(snapshot, "ember", intelligence=21, additive_bonus=2.5, multiplier=1.0)
    assert first == second
