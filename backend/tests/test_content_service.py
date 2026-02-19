from copy import deepcopy

from app.services.content import (
    CONTENT_DOMAIN_ASSETS,
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


def test_assets_validation_rejects_invalid_layer_and_collidable_type() -> None:
    payload = {
        "entries": [
            {
                "key": "tree_oak",
                "label": "Oak Tree",
                "text_key": "asset.tree_oak",
                "description": "Tree",
                "default_layer": -1,
                "collidable": "yes",
            }
        ]
    }
    issues = validate_domain_payload(CONTENT_DOMAIN_ASSETS, payload)
    assert any(".default_layer" in issue.message for issue in issues)
    assert any(".collidable" in issue.message for issue in issues)


def test_assets_validation_rejects_unknown_equipment_slot_reference() -> None:
    payload = {
        "entries": [
            {
                "key": "grass_tile",
                "label": "Grass Tile",
                "text_key": "asset.grass_tile",
                "description": "Ground tile",
                "default_layer": 0,
                "collidable": False,
            }
        ],
        "equipment_slots": [
            {"slot": "weapon_main", "label": "Main Hand", "draw_layer": 60},
        ],
        "equipment_visuals": [
            {
                "item_key": "weapon_training_saber",
                "label": "Training Saber",
                "slot": "weapon_off",
                "text_key": "item.weapon_training_saber",
                "description": "Starter weapon",
                "asset_key": "weapon_training_saber",
                "default_for_slot": True,
                "draw_layer": 60,
                "pivot_x": 16,
                "pivot_y": 24,
                "directions": 8,
                "frames_per_direction": 6,
            }
        ],
    }
    issues = validate_domain_payload(CONTENT_DOMAIN_ASSETS, payload)
    assert any(".slot' is unknown" in issue.message for issue in issues)


def test_assets_validation_rejects_duplicate_default_per_slot() -> None:
    payload = {
        "entries": [
            {
                "key": "grass_tile",
                "label": "Grass Tile",
                "text_key": "asset.grass_tile",
                "description": "Ground tile",
                "default_layer": 0,
                "collidable": False,
            }
        ],
        "equipment_slots": [
            {"slot": "weapon_main", "label": "Main Hand", "draw_layer": 60},
        ],
        "equipment_visuals": [
            {
                "item_key": "weapon_training_saber",
                "label": "Training Saber",
                "slot": "weapon_main",
                "text_key": "item.weapon_training_saber",
                "description": "Starter weapon",
                "asset_key": "weapon_training_saber",
                "default_for_slot": True,
                "draw_layer": 60,
                "pivot_x": 16,
                "pivot_y": 24,
                "directions": 8,
                "frames_per_direction": 6,
            },
            {
                "item_key": "weapon_training_longsword",
                "label": "Training Longsword",
                "slot": "weapon_main",
                "text_key": "item.weapon_training_longsword",
                "description": "Starter weapon variant",
                "asset_key": "weapon_training_longsword",
                "default_for_slot": True,
                "draw_layer": 60,
                "pivot_x": 16,
                "pivot_y": 24,
                "directions": 8,
                "frames_per_direction": 6,
            },
        ],
    }
    issues = validate_domain_payload(CONTENT_DOMAIN_ASSETS, payload)
    assert any("Only one default visual is allowed per slot" in issue.message for issue in issues)
