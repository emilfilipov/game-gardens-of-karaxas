from copy import deepcopy

from app.services.content import (
    CONTENT_DOMAIN_CHARACTER_OPTIONS,
    CONTENT_DOMAIN_SKILLS,
    DEFAULT_CONTENT_DOMAINS,
    validate_domain_payload,
    validate_domains,
)


def test_default_domains_are_valid() -> None:
    domains = deepcopy(DEFAULT_CONTENT_DOMAINS)
    issues = validate_domains(domains)
    assert issues == []


def test_character_options_validation_rejects_missing_lists() -> None:
    payload = {
        "point_budget": 10,
        "race": [],
        "background": [],
        "affiliation": [],
    }
    issues = validate_domain_payload(CONTENT_DOMAIN_CHARACTER_OPTIONS, payload)
    assert any("race" in issue.message for issue in issues)
    assert any("background" in issue.message for issue in issues)
    assert any("affiliation" in issue.message for issue in issues)


def test_skills_validation_requires_tooltip_fields() -> None:
    payload = {
        "entries": [
            {
                "key": "ember",
                "label": "Ember",
                "text_key": "skill.ember",
                "skill_type": "Spell",
                "mana_cost": 12,
                "energy_cost": 0,
                "life_cost": 0,
                "cooldown_seconds": 4.0,
                "damage_base": 20.0,
                "intelligence_scale": 0.6,
                "effects": "",
                "description": "",
            }
        ]
    }
    issues = validate_domain_payload(CONTENT_DOMAIN_SKILLS, payload)
    assert any(".effects" in issue.message for issue in issues)
    assert any(".description" in issue.message for issue in issues)
