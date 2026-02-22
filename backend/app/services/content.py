from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from time import perf_counter
from threading import RLock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import ContentBundle, ContentVersion
from app.services.observability import record_snapshot_load_latency_ms

CONTENT_SCHEMA_VERSION = 1
CONTENT_STATE_DRAFT = "draft"
CONTENT_STATE_VALIDATED = "validated"
CONTENT_STATE_ACTIVE = "active"
CONTENT_STATE_RETIRED = "retired"

CONTENT_DOMAIN_PROGRESSION = "progression"
CONTENT_DOMAIN_CHARACTER_OPTIONS = "character_options"
CONTENT_DOMAIN_STATS = "stats"
CONTENT_DOMAIN_SKILLS = "skills"
CONTENT_DOMAIN_ASSETS = "assets"
CONTENT_DOMAIN_TUNING = "tuning"
CONTENT_DOMAIN_UI_TEXT = "ui_text"

REQUIRED_DOMAINS = {
    CONTENT_DOMAIN_PROGRESSION,
    CONTENT_DOMAIN_CHARACTER_OPTIONS,
    CONTENT_DOMAIN_STATS,
    CONTENT_DOMAIN_SKILLS,
    CONTENT_DOMAIN_ASSETS,
    CONTENT_DOMAIN_TUNING,
    CONTENT_DOMAIN_UI_TEXT,
}

CONTENT_CONTRACT_SPEC = {
    "content_schema_version": CONTENT_SCHEMA_VERSION,
    "required_domains": sorted(REQUIRED_DOMAINS),
}
CONTENT_CONTRACT_SIGNATURE = hashlib.sha256(
    json.dumps(CONTENT_CONTRACT_SPEC, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

DEFAULT_CONTENT_DOMAINS: dict[str, dict] = {
    CONTENT_DOMAIN_PROGRESSION: {
        "xp_per_level": 100,
        "max_level": 100,
        "level_up_rewards": {
            "default": {"stat_points": 1, "skill_points": 0},
        },
    },
    CONTENT_DOMAIN_CHARACTER_OPTIONS: {
        "point_budget": 10,
        "appearance": {
            "sex": [
                {"value": "human_male", "label": "Male", "text_key": "option.sex.human_male", "description": "Standard male body preset.", "order": 1},
                {"value": "human_female", "label": "Female", "text_key": "option.sex.human_female", "description": "Standard female body preset.", "order": 2},
            ],
            "body_preset": [
                {"value": "adventurer", "label": "Adventurer", "text_key": "option.body.adventurer", "description": "Default tower climber body silhouette.", "order": 1},
            ],
            "skin_tone": [
                {"value": "warm_bronze", "label": "Warm Bronze", "text_key": "option.skin.warm_bronze", "description": "Balanced warm skin profile.", "order": 1},
                {"value": "olive", "label": "Olive", "text_key": "option.skin.olive", "description": "Muted olive skin profile.", "order": 2},
                {"value": "fair", "label": "Fair", "text_key": "option.skin.fair", "description": "Light skin profile.", "order": 3},
                {"value": "deep_umber", "label": "Deep Umber", "text_key": "option.skin.deep_umber", "description": "Dark warm skin profile.", "order": 4},
            ],
            "hair_style": [
                {"value": "short", "label": "Short", "text_key": "option.hair_style.short", "description": "Short practical haircut.", "order": 1},
                {"value": "braided", "label": "Braided", "text_key": "option.hair_style.braided", "description": "Braided hairstyle variant.", "order": 2},
                {"value": "shaved", "label": "Shaved", "text_key": "option.hair_style.shaved", "description": "Close shaved style.", "order": 3},
                {"value": "ponytail", "label": "Ponytail", "text_key": "option.hair_style.ponytail", "description": "Tied long hair style.", "order": 4},
            ],
            "hair_color": [
                {"value": "umber", "label": "Umber", "text_key": "option.hair_color.umber", "description": "Default warm brown hair.", "order": 1},
                {"value": "black", "label": "Black", "text_key": "option.hair_color.black", "description": "Deep black hair tone.", "order": 2},
                {"value": "copper", "label": "Copper", "text_key": "option.hair_color.copper", "description": "Copper red hair tone.", "order": 3},
                {"value": "ash", "label": "Ash", "text_key": "option.hair_color.ash", "description": "Ash gray hair tone.", "order": 4},
            ],
            "face": [
                {"value": "calm", "label": "Calm", "text_key": "option.face.calm", "description": "Neutral relaxed face.", "order": 1},
                {"value": "scarred", "label": "Scarred", "text_key": "option.face.scarred", "description": "Weathered veteran look.", "order": 2},
                {"value": "focused", "label": "Focused", "text_key": "option.face.focused", "description": "Disciplined focused look.", "order": 3},
                {"value": "stoic", "label": "Stoic", "text_key": "option.face.stoic", "description": "Reserved stoic look.", "order": 4},
            ],
            "stance": [
                {"value": "neutral", "label": "Neutral", "text_key": "option.stance.neutral", "description": "Balanced idle stance.", "order": 1},
                {"value": "guarded", "label": "Guarded", "text_key": "option.stance.guarded", "description": "Defensive guard stance.", "order": 2},
                {"value": "ready", "label": "Ready", "text_key": "option.stance.ready", "description": "Aggressive ready stance.", "order": 3},
            ],
            "lighting_profile": [
                {"value": "warm_torchlight", "label": "Warm Torchlight", "text_key": "option.light.warm_torchlight", "description": "Warm cinematic preview lighting.", "order": 1},
                {"value": "neutral_daylight", "label": "Neutral Daylight", "text_key": "option.light.neutral_daylight", "description": "Balanced daylight lighting.", "order": 2},
                {"value": "grim_dusk", "label": "Grim Dusk", "text_key": "option.light.grim_dusk", "description": "Lower-key dramatic preview lighting.", "order": 3},
            ],
            "defaults": {
                "sex": "human_male",
                "body_preset": "adventurer",
                "skin_tone": "warm_bronze",
                "hair_style": "short",
                "hair_color": "umber",
                "face": "calm",
                "stance": "neutral",
                "lighting_profile": "warm_torchlight",
            },
        },
        "race": [
            {"value": "human", "label": "Human", "text_key": "option.race.human", "description": "Balanced origin."},
            {"value": "elf", "label": "Elf", "text_key": "option.race.elf", "description": "Arcane-leaning origin."},
            {"value": "dwarf", "label": "Dwarf", "text_key": "option.race.dwarf", "description": "Sturdy martial origin."},
        ],
        "background": [
            {"value": "drifter", "label": "Drifter", "text_key": "option.background.drifter", "description": "Survivalist path."},
            {"value": "scholar", "label": "Scholar", "text_key": "option.background.scholar", "description": "Knowledge path."},
            {"value": "soldier", "label": "Soldier", "text_key": "option.background.soldier", "description": "Military path."},
        ],
        "affiliation": [
            {"value": "unaffiliated", "label": "Unaffiliated", "text_key": "option.affiliation.unaffiliated", "description": "Independent."},
            {"value": "order", "label": "Order", "text_key": "option.affiliation.order", "description": "Disciplined faction."},
            {"value": "consortium", "label": "Consortium", "text_key": "option.affiliation.consortium", "description": "Trade faction."},
        ],
    },
    CONTENT_DOMAIN_STATS: {
        "max_per_stat": 10,
        "entries": [
            {
                "key": "strength",
                "label": "Strength",
                "text_key": "stat.strength",
                "description": "Power for heavy melee attacks.",
                "tooltip": "Increases melee power and carrying force.",
            },
            {
                "key": "agility",
                "label": "Agility",
                "text_key": "stat.agility",
                "description": "Speed for movement and recovery.",
                "tooltip": "Improves movement and action speed.",
            },
            {
                "key": "intellect",
                "label": "Intellect",
                "text_key": "stat.intellect",
                "description": "Arcane output and spell control.",
                "tooltip": "Increases spell power and scaling.",
            },
            {
                "key": "vitality",
                "label": "Vitality",
                "text_key": "stat.vitality",
                "description": "Base health and toughness.",
                "tooltip": "Raises health and resilience.",
            },
            {
                "key": "resolve",
                "label": "Resolve",
                "text_key": "stat.resolve",
                "description": "Resistance against control effects.",
                "tooltip": "Improves control resistance.",
            },
            {
                "key": "endurance",
                "label": "Endurance",
                "text_key": "stat.endurance",
                "description": "Stamina and sustained effort.",
                "tooltip": "Improves sustained activity.",
            },
            {
                "key": "dexterity",
                "label": "Dexterity",
                "text_key": "stat.dexterity",
                "description": "Precision for weapons and tools.",
                "tooltip": "Improves precision and handling.",
            },
            {
                "key": "willpower",
                "label": "Willpower",
                "text_key": "stat.willpower",
                "description": "Mental focus and channeling.",
                "tooltip": "Improves focus and control.",
            },
        ],
    },
    CONTENT_DOMAIN_SKILLS: {
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
                "effects": "Applies Burn I for 4s.",
                "damage_text": "20 fire + INT scaling.",
                "description": "Starter fire projectile.",
            },
            {
                "key": "cleave",
                "label": "Cleave",
                "text_key": "skill.cleave",
                "skill_type": "Melee",
                "mana_cost": 0,
                "energy_cost": 18,
                "life_cost": 0,
                "cooldown_seconds": 5.0,
                "damage_base": 30.0,
                "intelligence_scale": 0.0,
                "effects": "Short frontal arc strike.",
                "damage_text": "30 physical.",
                "description": "Starter wide melee swing.",
            },
            {
                "key": "quick_strike",
                "label": "Quick Strike",
                "text_key": "skill.quick_strike",
                "skill_type": "Melee",
                "mana_cost": 0,
                "energy_cost": 10,
                "life_cost": 0,
                "cooldown_seconds": 2.0,
                "damage_base": 18.0,
                "intelligence_scale": 0.0,
                "effects": "Single-target thrust.",
                "damage_text": "18 physical.",
                "description": "Starter fast attack.",
            },
            {
                "key": "bandage",
                "label": "Bandage",
                "text_key": "skill.bandage",
                "skill_type": "Support",
                "mana_cost": 0,
                "energy_cost": 8,
                "life_cost": 0,
                "cooldown_seconds": 8.0,
                "damage_base": 0.0,
                "intelligence_scale": 0.0,
                "effects": "Applies Regeneration I for 6s.",
                "damage_text": "24 healing over time.",
                "description": "Starter sustain skill.",
            },
        ]
    },
    CONTENT_DOMAIN_ASSETS: {
        "entries": [
            {
                "key": "grass_tile",
                "label": "Grass Tile",
                "text_key": "asset.grass_tile",
                "description": "Ground foliage tile for layer 0.",
                "default_layer": 0,
                "collidable": False,
                "icon_asset_key": "grass_tile",
            },
            {
                "key": "wall_block",
                "label": "Wall Block",
                "text_key": "asset.wall_block",
                "description": "Solid collision wall for gameplay layer 1.",
                "default_layer": 1,
                "collidable": True,
                "icon_asset_key": "wall_block",
                "collision_template": {
                    "shape": "box",
                    "offset_x": 0.0,
                    "offset_y": 0.0,
                    "width": 1.0,
                    "height": 1.0,
                    "layers": ["ground", "flying"],
                },
            },
            {
                "key": "tree_oak",
                "label": "Oak Tree",
                "text_key": "asset.tree_oak",
                "description": "Tree obstacle used on gameplay layer 1.",
                "default_layer": 1,
                "collidable": True,
                "icon_asset_key": "tree_oak",
                "collision_template": {
                    "shape": "base_box",
                    "offset_x": 0.15,
                    "offset_y": 0.62,
                    "width": 0.70,
                    "height": 0.34,
                    "layers": ["ground"],
                },
            },
            {
                "key": "cloud_soft",
                "label": "Soft Cloud",
                "text_key": "asset.cloud_soft",
                "description": "Ambient weather overlay for layer 2.",
                "default_layer": 2,
                "collidable": False,
                "icon_asset_key": "cloud_soft",
            },
            {
                "key": "stairs_passage",
                "label": "Stone Stairs",
                "text_key": "asset.stairs_passage",
                "description": "Transition marker for climbing between tower floors.",
                "default_layer": 1,
                "collidable": False,
                "icon_asset_key": "stairs_passage",
            },
            {
                "key": "ladder_passage",
                "label": "Ladder",
                "text_key": "asset.ladder_passage",
                "description": "Transition marker for vertical ladder travel.",
                "default_layer": 1,
                "collidable": False,
                "icon_asset_key": "ladder_passage",
            },
            {
                "key": "elevator_platform",
                "label": "Elevator Platform",
                "text_key": "asset.elevator_platform",
                "description": "Transition marker for elevator travel between floors.",
                "default_layer": 1,
                "collidable": False,
                "icon_asset_key": "elevator_platform",
            },
            {
                "key": "spawn_marker",
                "label": "Spawn Marker",
                "text_key": "asset.spawn_marker",
                "description": "Player spawn marker used by level editor.",
                "default_layer": 1,
                "collidable": False,
                "icon_asset_key": "spawn_marker",
            },
        ],
        "equipment_slots": [
            {
                "slot": "head",
                "label": "Head",
                "description": "Helmets, hats, and head accessories.",
                "draw_layer": 10,
            },
            {
                "slot": "chest",
                "label": "Chest",
                "description": "Torso armor and robes.",
                "draw_layer": 20,
            },
            {
                "slot": "legs",
                "label": "Legs",
                "description": "Leg armor and cloth.",
                "draw_layer": 30,
            },
            {
                "slot": "hands",
                "label": "Hands",
                "description": "Gloves and bracers.",
                "draw_layer": 40,
            },
            {
                "slot": "feet",
                "label": "Feet",
                "description": "Boots and greaves.",
                "draw_layer": 50,
            },
            {
                "slot": "weapon_main",
                "label": "Main Hand",
                "description": "Primary weapon visual overlay.",
                "draw_layer": 60,
            },
            {
                "slot": "weapon_off",
                "label": "Off Hand",
                "description": "Secondary weapon/shield visual overlay.",
                "draw_layer": 55,
            },
        ],
        "equipment_visuals": [
            {
                "item_key": "weapon_training_saber",
                "label": "Training Saber",
                "slot": "weapon_main",
                "text_key": "item.weapon_training_saber",
                "description": "Starter saber visual placeholder.",
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
                "description": "Starter longsword visual placeholder.",
                "asset_key": "weapon_training_longsword",
                "default_for_slot": False,
                "draw_layer": 60,
                "pivot_x": 16,
                "pivot_y": 24,
                "directions": 8,
                "frames_per_direction": 6,
            },
            {
                "item_key": "offhand_training_buckler",
                "label": "Training Buckler",
                "slot": "weapon_off",
                "text_key": "item.offhand_training_buckler",
                "description": "Starter off-hand shield visual placeholder.",
                "asset_key": "offhand_training_buckler",
                "default_for_slot": True,
                "draw_layer": 55,
                "pivot_x": 16,
                "pivot_y": 24,
                "directions": 8,
                "frames_per_direction": 6,
            },
        ],
    },
    CONTENT_DOMAIN_TUNING: {
        "movement_speed": 220.0,
        "attack_speed_base": 1.0,
    },
    CONTENT_DOMAIN_UI_TEXT: {
        "strings": {
            "ui.content.blocked_play": "Content unavailable. Reconnect to sync gameplay data.",
            "ui.content.cached": "Using cached content snapshot.",
        }
    },
}


@dataclass(frozen=True)
class ContentSnapshot:
    schema_version: int
    content_version_id: int
    content_version_key: str
    loaded_at: datetime
    domains: dict[str, dict]

    def domain(self, name: str, fallback: dict | None = None) -> dict:
        value = self.domains.get(name)
        if isinstance(value, dict):
            return value
        return {} if fallback is None else fallback


@dataclass(frozen=True)
class ContentValidationIssue:
    domain: str
    message: str


_snapshot_lock = RLock()
_cached_snapshot: ContentSnapshot | None = None


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _copy_default_domains() -> dict[str, dict]:
    return deepcopy(DEFAULT_CONTENT_DOMAINS)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_option_entries(domain: str, key: str, raw: object) -> list[ContentValidationIssue]:
    issues: list[ContentValidationIssue] = []
    if not isinstance(raw, list) or not raw:
        issues.append(ContentValidationIssue(domain, f"'{key}' must be a non-empty list"))
        return issues

    seen_values: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            issues.append(ContentValidationIssue(domain, f"'{key}[{index}]' must be an object"))
            continue
        value = str(item.get("value", "")).strip()
        label = str(item.get("label", "")).strip()
        text_key = str(item.get("text_key", "")).strip()
        if not value:
            issues.append(ContentValidationIssue(domain, f"'{key}[{index}].value' is required"))
        if not label:
            issues.append(ContentValidationIssue(domain, f"'{key}[{index}].label' is required"))
        if not text_key:
            issues.append(ContentValidationIssue(domain, f"'{key}[{index}].text_key' is required"))
        order = item.get("order", index)
        if not isinstance(order, int):
            issues.append(ContentValidationIssue(domain, f"'{key}[{index}].order' must be an integer"))
        if value in seen_values:
            issues.append(ContentValidationIssue(domain, f"'{key}[{index}].value' is duplicated ('{value}')"))
        seen_values.add(value)
    return issues


def _validate_equipment_slots(domain: str, payload: dict) -> tuple[list[ContentValidationIssue], set[str]]:
    issues: list[ContentValidationIssue] = []
    slots = payload.get("equipment_slots")
    if slots is None:
        return issues, set()
    if not isinstance(slots, list):
        return [ContentValidationIssue(domain, "'equipment_slots' must be a list when provided")], set()

    seen_slots: set[str] = set()
    for index, raw in enumerate(slots):
        if not isinstance(raw, dict):
            issues.append(ContentValidationIssue(domain, f"'equipment_slots[{index}]' must be an object"))
            continue
        slot = str(raw.get("slot", "")).strip().lower()
        label = str(raw.get("label", "")).strip()
        draw_layer = raw.get("draw_layer")
        if not slot:
            issues.append(ContentValidationIssue(domain, f"'equipment_slots[{index}].slot' is required"))
            continue
        if slot in seen_slots:
            issues.append(ContentValidationIssue(domain, f"'equipment_slots[{index}].slot' is duplicated ('{slot}')"))
        seen_slots.add(slot)
        if not label:
            issues.append(ContentValidationIssue(domain, f"'equipment_slots[{index}].label' is required"))
        if not isinstance(draw_layer, int) or draw_layer < 0:
            issues.append(ContentValidationIssue(domain, f"'equipment_slots[{index}].draw_layer' must be an integer >= 0"))
    return issues, seen_slots


def _validate_equipment_visuals(domain: str, payload: dict, allowed_slots: set[str]) -> list[ContentValidationIssue]:
    visuals = payload.get("equipment_visuals")
    if visuals is None:
        return []
    if not isinstance(visuals, list):
        return [ContentValidationIssue(domain, "'equipment_visuals' must be a list when provided")]

    issues: list[ContentValidationIssue] = []
    seen_items: set[str] = set()
    slot_default_counts: dict[str, int] = {}
    for index, raw in enumerate(visuals):
        if not isinstance(raw, dict):
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}]' must be an object"))
            continue
        item_key = str(raw.get("item_key", "")).strip().lower()
        label = str(raw.get("label", "")).strip()
        slot = str(raw.get("slot", "")).strip().lower()
        text_key = str(raw.get("text_key", "")).strip()
        description = str(raw.get("description", "")).strip()
        asset_key = str(raw.get("asset_key", "")).strip()
        default_for_slot = raw.get("default_for_slot")
        draw_layer = raw.get("draw_layer")
        pivot_x = raw.get("pivot_x")
        pivot_y = raw.get("pivot_y")
        directions = raw.get("directions")
        frames_per_direction = raw.get("frames_per_direction")

        if not item_key:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].item_key' is required"))
        if item_key in seen_items:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].item_key' is duplicated ('{item_key}')"))
        seen_items.add(item_key)
        if not label:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].label' is required"))
        if not slot:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].slot' is required"))
        elif allowed_slots and slot not in allowed_slots:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].slot' is unknown ('{slot}')"))
        if not text_key:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].text_key' is required"))
        if not description:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].description' is required"))
        if not asset_key:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].asset_key' is required"))
        if not isinstance(default_for_slot, bool):
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].default_for_slot' must be boolean"))
        if isinstance(default_for_slot, bool) and default_for_slot:
            slot_default_counts[slot] = slot_default_counts.get(slot, 0) + 1
        if not isinstance(draw_layer, int) or draw_layer < 0:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].draw_layer' must be an integer >= 0"))
        if not isinstance(pivot_x, int):
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].pivot_x' must be an integer"))
        if not isinstance(pivot_y, int):
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].pivot_y' must be an integer"))
        if not isinstance(directions, int) or directions not in {4, 8}:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].directions' must be 4 or 8"))
        if not isinstance(frames_per_direction, int) or frames_per_direction <= 0:
            issues.append(ContentValidationIssue(domain, f"'equipment_visuals[{index}].frames_per_direction' must be > 0"))

    for slot, count in slot_default_counts.items():
        if count > 1:
            issues.append(ContentValidationIssue(domain, f"Only one default visual is allowed per slot ('{slot}')"))

    return issues


def validate_domain_payload(domain: str, payload: dict) -> list[ContentValidationIssue]:
    issues: list[ContentValidationIssue] = []
    if not isinstance(payload, dict):
        return [ContentValidationIssue(domain, "payload must be a JSON object")]

    if domain == CONTENT_DOMAIN_PROGRESSION:
        xp_per_level = payload.get("xp_per_level")
        max_level = payload.get("max_level")
        if not isinstance(xp_per_level, int) or xp_per_level <= 0:
            issues.append(ContentValidationIssue(domain, "'xp_per_level' must be a positive integer"))
        if not isinstance(max_level, int) or max_level <= 0:
            issues.append(ContentValidationIssue(domain, "'max_level' must be a positive integer"))

    elif domain == CONTENT_DOMAIN_CHARACTER_OPTIONS:
        budget = payload.get("point_budget")
        if not isinstance(budget, int) or budget <= 0:
            issues.append(ContentValidationIssue(domain, "'point_budget' must be a positive integer"))
        issues.extend(_validate_option_entries(domain, "race", payload.get("race")))
        issues.extend(_validate_option_entries(domain, "background", payload.get("background")))
        issues.extend(_validate_option_entries(domain, "affiliation", payload.get("affiliation")))
        appearance = payload.get("appearance", {})
        if not isinstance(appearance, dict):
            issues.append(ContentValidationIssue(domain, "'appearance' must be an object"))
        else:
            for field in (
                "sex",
                "body_preset",
                "skin_tone",
                "hair_style",
                "hair_color",
                "face",
                "stance",
                "lighting_profile",
            ):
                issues.extend(_validate_option_entries(domain, f"appearance.{field}", appearance.get(field)))
            defaults = appearance.get("defaults", {})
            if not isinstance(defaults, dict):
                issues.append(ContentValidationIssue(domain, "'appearance.defaults' must be an object"))
            else:
                for field in (
                    "sex",
                    "body_preset",
                    "skin_tone",
                    "hair_style",
                    "hair_color",
                    "face",
                    "stance",
                    "lighting_profile",
                ):
                    value = str(defaults.get(field, "")).strip().lower()
                    if not value:
                        issues.append(ContentValidationIssue(domain, f"'appearance.defaults.{field}' is required"))
                        continue
                    entries = appearance.get(field, [])
                    entry_values = {
                        str(entry.get("value", "")).strip().lower()
                        for entry in entries
                        if isinstance(entry, dict)
                    }
                    if entry_values and value not in entry_values:
                        issues.append(
                            ContentValidationIssue(
                                domain,
                                f"'appearance.defaults.{field}' must match one of appearance.{field} values",
                            )
                        )

    elif domain == CONTENT_DOMAIN_STATS:
        max_per_stat = payload.get("max_per_stat")
        if not isinstance(max_per_stat, int) or max_per_stat < 0:
            issues.append(ContentValidationIssue(domain, "'max_per_stat' must be an integer >= 0"))
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            issues.append(ContentValidationIssue(domain, "'entries' must be a non-empty list"))
        else:
            seen: set[str] = set()
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}]' must be an object"))
                    continue
                key = str(entry.get("key", "")).strip()
                label = str(entry.get("label", "")).strip()
                tooltip = str(entry.get("tooltip", "")).strip()
                description = str(entry.get("description", "")).strip()
                text_key = str(entry.get("text_key", "")).strip()
                if not key:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].key' is required"))
                if key in seen:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].key' is duplicated ('{key}')"))
                seen.add(key)
                if not label:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].label' is required"))
                if not tooltip:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].tooltip' is required"))
                if not description:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].description' is required"))
                if not text_key:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].text_key' is required"))

    elif domain == CONTENT_DOMAIN_SKILLS:
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            issues.append(ContentValidationIssue(domain, "'entries' must be a non-empty list"))
        else:
            seen: set[str] = set()
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}]' must be an object"))
                    continue
                key = str(entry.get("key", "")).strip()
                label = str(entry.get("label", "")).strip()
                text_key = str(entry.get("text_key", "")).strip()
                description = str(entry.get("description", "")).strip()
                effects = str(entry.get("effects", "")).strip()
                skill_type = str(entry.get("skill_type", "")).strip()
                if not key:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].key' is required"))
                if key in seen:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].key' is duplicated ('{key}')"))
                seen.add(key)
                if not label:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].label' is required"))
                if not text_key:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].text_key' is required"))
                if not description:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].description' is required"))
                if not effects:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].effects' is required"))
                if not skill_type:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].skill_type' is required"))
                for numeric_key in ("mana_cost", "energy_cost", "life_cost", "cooldown_seconds", "damage_base", "intelligence_scale"):
                    value = entry.get(numeric_key)
                    if not _is_number(value):
                        issues.append(ContentValidationIssue(domain, f"'entries[{index}].{numeric_key}' must be numeric"))
                    elif float(value) < 0:
                        issues.append(ContentValidationIssue(domain, f"'entries[{index}].{numeric_key}' must be >= 0"))

    elif domain == CONTENT_DOMAIN_ASSETS:
        entries = payload.get("entries")
        if not isinstance(entries, list) or not entries:
            issues.append(ContentValidationIssue(domain, "'entries' must be a non-empty list"))
        else:
            seen: set[str] = set()
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}]' must be an object"))
                    continue
                key = str(entry.get("key", "")).strip()
                label = str(entry.get("label", "")).strip()
                text_key = str(entry.get("text_key", "")).strip()
                description = str(entry.get("description", "")).strip()
                icon_asset_key_raw = entry.get("icon_asset_key", "")
                icon_asset_key = str(icon_asset_key_raw).strip() if icon_asset_key_raw is not None else ""
                default_layer = entry.get("default_layer")
                collidable = entry.get("collidable")
                collision_template = entry.get("collision_template", None)
                if not key:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].key' is required"))
                if key in seen:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].key' is duplicated ('{key}')"))
                seen.add(key)
                if not label:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].label' is required"))
                if not text_key:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].text_key' is required"))
                if not description:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].description' is required"))
                if icon_asset_key_raw is not None and not isinstance(icon_asset_key_raw, str):
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].icon_asset_key' must be text"))
                if not isinstance(default_layer, int) or default_layer < 0:
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].default_layer' must be an integer >= 0"))
                if not isinstance(collidable, bool):
                    issues.append(ContentValidationIssue(domain, f"'entries[{index}].collidable' must be a boolean"))
                if collision_template is not None:
                    if not isinstance(collision_template, dict):
                        issues.append(
                            ContentValidationIssue(
                                domain,
                                f"'entries[{index}].collision_template' must be an object when provided",
                            )
                        )
                    else:
                        shape = str(collision_template.get("shape", "")).strip().lower()
                        if shape not in {"box", "polygon", "base_box"}:
                            issues.append(
                                ContentValidationIssue(
                                    domain,
                                    f"'entries[{index}].collision_template.shape' must be box, polygon, or base_box",
                                )
                            )
                        layers = collision_template.get("layers", [])
                        if not isinstance(layers, list) or not layers:
                            issues.append(
                                ContentValidationIssue(
                                    domain,
                                    f"'entries[{index}].collision_template.layers' must be a non-empty list",
                                )
                            )
                        else:
                            for layer_idx, layer_name in enumerate(layers):
                                if not isinstance(layer_name, str) or not layer_name.strip():
                                    issues.append(
                                        ContentValidationIssue(
                                            domain,
                                            f"'entries[{index}].collision_template.layers[{layer_idx}]' must be text",
                                        )
                                    )
                        for number_key in ("offset_x", "offset_y", "width", "height"):
                            if number_key in collision_template and not _is_number(collision_template.get(number_key)):
                                issues.append(
                                    ContentValidationIssue(
                                        domain,
                                        f"'entries[{index}].collision_template.{number_key}' must be numeric",
                                    )
                                )
                        if shape == "polygon":
                            points = collision_template.get("points", [])
                            if not isinstance(points, list) or len(points) < 3:
                                issues.append(
                                    ContentValidationIssue(
                                        domain,
                                        f"'entries[{index}].collision_template.points' must have at least 3 points for polygon shape",
                                    )
                                )
                elif collidable is True:
                    issues.append(
                        ContentValidationIssue(
                            domain,
                            f"'entries[{index}]' is collidable but missing collision_template",
                        )
                    )
        slot_issues, slot_keys = _validate_equipment_slots(domain, payload)
        issues.extend(slot_issues)
        issues.extend(_validate_equipment_visuals(domain, payload, slot_keys))

    elif domain == CONTENT_DOMAIN_TUNING:
        for key in ("movement_speed", "attack_speed_base"):
            value = payload.get(key)
            if not _is_number(value):
                issues.append(ContentValidationIssue(domain, f"'{key}' must be numeric"))
            elif float(value) <= 0:
                issues.append(ContentValidationIssue(domain, f"'{key}' must be > 0"))

    elif domain == CONTENT_DOMAIN_UI_TEXT:
        strings = payload.get("strings")
        if not isinstance(strings, dict):
            issues.append(ContentValidationIssue(domain, "'strings' must be an object"))
        else:
            for key, value in strings.items():
                if not str(key).strip():
                    issues.append(ContentValidationIssue(domain, "string keys must be non-empty"))
                if not isinstance(value, str) or not value.strip():
                    issues.append(ContentValidationIssue(domain, f"string '{key}' must be a non-empty text value"))

    else:
        issues.append(ContentValidationIssue(domain, "unknown domain"))

    return issues


def validate_domains(domains: dict[str, dict]) -> list[ContentValidationIssue]:
    issues: list[ContentValidationIssue] = []
    missing = sorted(REQUIRED_DOMAINS - set(domains.keys()))
    for domain in missing:
        issues.append(ContentValidationIssue(domain, "required domain is missing"))
    for domain, payload in domains.items():
        issues.extend(validate_domain_payload(domain, payload))
    return issues


def _fetch_bundles_for_version(db: Session, version_id: int) -> dict[str, dict]:
    rows = db.execute(
        select(ContentBundle).where(ContentBundle.content_version_id == version_id).order_by(ContentBundle.domain.asc())
    ).scalars()
    result: dict[str, dict] = {}
    for row in rows:
        result[row.domain] = row.payload if isinstance(row.payload, dict) else {}
    return result


def _build_snapshot(version: ContentVersion, domains: dict[str, dict]) -> ContentSnapshot:
    return ContentSnapshot(
        schema_version=CONTENT_SCHEMA_VERSION,
        content_version_id=version.id,
        content_version_key=version.version_key,
        loaded_at=_now_utc(),
        domains=deepcopy(domains),
    )


def _set_cached_snapshot(snapshot: ContentSnapshot) -> None:
    global _cached_snapshot
    with _snapshot_lock:
        _cached_snapshot = snapshot


def _query_active_version(db: Session) -> ContentVersion | None:
    return db.execute(
        select(ContentVersion)
        .where(ContentVersion.state == CONTENT_STATE_ACTIVE)
        .order_by(ContentVersion.activated_at.desc().nullslast(), ContentVersion.id.desc())
    ).scalars().first()


def ensure_content_seed(db: Session) -> ContentSnapshot:
    started = perf_counter()
    active = _query_active_version(db)
    if active is None:
        active = ContentVersion(
            version_key="cv_bootstrap_v1",
            state=CONTENT_STATE_ACTIVE,
            note="Bootstrap content snapshot",
            activated_at=_now_utc(),
        )
        db.add(active)
        db.commit()
        db.refresh(active)

    existing_domains = _fetch_bundles_for_version(db, active.id)
    changed = False
    for domain, payload in _copy_default_domains().items():
        if domain not in existing_domains:
            db.add(
                ContentBundle(
                    content_version_id=active.id,
                    domain=domain,
                    payload=payload,
                )
            )
            changed = True
    if changed:
        db.commit()
        existing_domains = _fetch_bundles_for_version(db, active.id)

    issues = validate_domains(existing_domains)
    if issues:
        # Keep service operable by restoring required defaults for invalid/missing bundles on active snapshot.
        defaults = _copy_default_domains()
        for issue in issues:
            if issue.domain in defaults:
                existing = db.execute(
                    select(ContentBundle).where(
                        ContentBundle.content_version_id == active.id,
                        ContentBundle.domain == issue.domain,
                    )
                ).scalar_one_or_none()
                if existing is None:
                    db.add(
                        ContentBundle(
                            content_version_id=active.id,
                            domain=issue.domain,
                            payload=defaults[issue.domain],
                        )
                    )
                else:
                    existing.payload = defaults[issue.domain]
                    db.add(existing)
                changed = True
        if changed:
            db.commit()
            existing_domains = _fetch_bundles_for_version(db, active.id)

    snapshot = _build_snapshot(active, existing_domains)
    _set_cached_snapshot(snapshot)
    record_snapshot_load_latency_ms((perf_counter() - started) * 1000.0)
    return snapshot


def refresh_active_snapshot(db: Session) -> ContentSnapshot:
    started = perf_counter()
    active = _query_active_version(db)
    if active is None:
        return ensure_content_seed(db)
    domains = _fetch_bundles_for_version(db, active.id)
    issues = validate_domains(domains)
    if issues:
        return ensure_content_seed(db)
    snapshot = _build_snapshot(active, domains)
    _set_cached_snapshot(snapshot)
    record_snapshot_load_latency_ms((perf_counter() - started) * 1000.0)
    return snapshot


def get_active_snapshot(db: Session, force_refresh: bool = False) -> ContentSnapshot:
    if not force_refresh:
        with _snapshot_lock:
            if _cached_snapshot is not None:
                return _cached_snapshot
    return refresh_active_snapshot(db)


def content_contract_signature() -> str:
    return CONTENT_CONTRACT_SIGNATURE


def list_content_versions(db: Session) -> list[ContentVersion]:
    return db.execute(select(ContentVersion).order_by(ContentVersion.id.desc())).scalars().all()


def get_content_version_or_none(db: Session, version_id: int) -> ContentVersion | None:
    return db.get(ContentVersion, version_id)


def get_content_version_domains(db: Session, version_id: int) -> dict[str, dict]:
    return _fetch_bundles_for_version(db, version_id)


def create_draft_from_active(db: Session, created_by_user_id: int | None, note: str = "") -> ContentVersion:
    active = _query_active_version(db)
    if active is None:
        snapshot = ensure_content_seed(db)
        active = db.get(ContentVersion, snapshot.content_version_id)
    assert active is not None

    timestamp = _now_utc().strftime("%Y%m%d%H%M%S")
    draft = ContentVersion(
        version_key=f"cv_{timestamp}_{active.id}",
        state=CONTENT_STATE_DRAFT,
        note=note.strip(),
        created_by_user_id=created_by_user_id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    active_domains = _fetch_bundles_for_version(db, active.id)
    for domain, payload in active_domains.items():
        db.add(
            ContentBundle(
                content_version_id=draft.id,
                domain=domain,
                payload=deepcopy(payload),
            )
        )
    db.commit()
    return draft


def upsert_version_bundle(
    db: Session,
    version: ContentVersion,
    domain: str,
    payload: dict,
) -> list[ContentValidationIssue]:
    issues = validate_domain_payload(domain, payload)
    if issues:
        return issues

    row = db.execute(
        select(ContentBundle).where(
            ContentBundle.content_version_id == version.id,
            ContentBundle.domain == domain,
        )
    ).scalar_one_or_none()
    if row is None:
        row = ContentBundle(
            content_version_id=version.id,
            domain=domain,
            payload=deepcopy(payload),
        )
    else:
        row.payload = deepcopy(payload)
    db.add(row)
    if version.state == CONTENT_STATE_VALIDATED:
        version.state = CONTENT_STATE_DRAFT
        version.validated_at = None
        db.add(version)
    db.commit()
    return []


def validate_version(db: Session, version: ContentVersion) -> list[ContentValidationIssue]:
    domains = _fetch_bundles_for_version(db, version.id)
    issues = validate_domains(domains)
    if issues:
        return issues
    version.state = CONTENT_STATE_VALIDATED
    version.validated_at = _now_utc()
    db.add(version)
    db.commit()
    return []


def activate_version(db: Session, version: ContentVersion) -> list[ContentValidationIssue]:
    domains = _fetch_bundles_for_version(db, version.id)
    issues = validate_domains(domains)
    if issues:
        return issues

    if version.state != CONTENT_STATE_VALIDATED:
        version.state = CONTENT_STATE_VALIDATED
        version.validated_at = version.validated_at or _now_utc()
        db.add(version)

    active_versions = db.execute(
        select(ContentVersion).where(ContentVersion.state == CONTENT_STATE_ACTIVE, ContentVersion.id != version.id)
    ).scalars()
    for row in active_versions:
        row.state = CONTENT_STATE_RETIRED
        db.add(row)

    version.state = CONTENT_STATE_ACTIVE
    version.activated_at = _now_utc()
    db.add(version)
    db.commit()
    db.refresh(version)
    refresh_active_snapshot(db)
    return []


def content_schema_registry() -> dict[str, dict]:
    return {
        "content_schema_version": CONTENT_SCHEMA_VERSION,
        "required_domains": sorted(REQUIRED_DOMAINS),
        "domain_templates": deepcopy(DEFAULT_CONTENT_DOMAINS),
    }


def _entries_by_key(entries: object) -> dict[str, dict]:
    result: dict[str, dict] = {}
    if not isinstance(entries, list):
        return result
    for item in entries:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", item.get("item_key", ""))).strip().lower()
        if key:
            result[key] = item
    return result


def summarize_content_deltas(base_domains: dict[str, dict], target_domains: dict[str, dict]) -> list[str]:
    lines: list[str] = []

    base_skills = _entries_by_key(base_domains.get(CONTENT_DOMAIN_SKILLS, {}).get("entries", []))
    target_skills = _entries_by_key(target_domains.get(CONTENT_DOMAIN_SKILLS, {}).get("entries", []))
    for key, target in sorted(target_skills.items()):
        base = base_skills.get(key)
        if base is None:
            lines.append(f"Added new skill: {target.get('label', key)}")
            continue
        for field, label in (
            ("damage_base", "damage"),
            ("cooldown_seconds", "cooldown"),
            ("mana_cost", "mana cost"),
            ("energy_cost", "energy cost"),
            ("life_cost", "life cost"),
        ):
            before = base.get(field)
            after = target.get(field)
            if before != after:
                lines.append(
                    f"{target.get('label', key)} {label} changed from {before} to {after}"
                )
    for key, base in sorted(base_skills.items()):
        if key not in target_skills:
            lines.append(f"Removed skill: {base.get('label', key)}")

    base_assets = _entries_by_key(base_domains.get(CONTENT_DOMAIN_ASSETS, {}).get("entries", []))
    target_assets = _entries_by_key(target_domains.get(CONTENT_DOMAIN_ASSETS, {}).get("entries", []))
    for key, target in sorted(target_assets.items()):
        base = base_assets.get(key)
        if base is None:
            lines.append(f"Added asset: {target.get('label', key)}")
            continue
        if bool(base.get("collidable", False)) != bool(target.get("collidable", False)):
            state = "enabled" if bool(target.get("collidable", False)) else "disabled"
            lines.append(f"{target.get('label', key)} collision {state}")
        base_collision = base.get("collision_template", {})
        target_collision = target.get("collision_template", {})
        if base_collision != target_collision and target_collision:
            lines.append(f"{target.get('label', key)} collision shape/template updated")
        if base.get("default_layer") != target.get("default_layer"):
            lines.append(
                f"{target.get('label', key)} default layer changed from {base.get('default_layer')} to {target.get('default_layer')}"
            )
    for key, base in sorted(base_assets.items()):
        if key not in target_assets:
            lines.append(f"Removed asset: {base.get('label', key)}")

    base_stats = _entries_by_key(base_domains.get(CONTENT_DOMAIN_STATS, {}).get("entries", []))
    target_stats = _entries_by_key(target_domains.get(CONTENT_DOMAIN_STATS, {}).get("entries", []))
    for key, target in sorted(target_stats.items()):
        base = base_stats.get(key)
        if base is None:
            lines.append(f"Added stat: {target.get('label', key)}")
            continue
        if str(base.get("description", "")).strip() != str(target.get("description", "")).strip():
            lines.append(f"{target.get('label', key)} description updated")
        if str(base.get("tooltip", "")).strip() != str(target.get("tooltip", "")).strip():
            lines.append(f"{target.get('label', key)} tooltip updated")
    for key, base in sorted(base_stats.items()):
        if key not in target_stats:
            lines.append(f"Removed stat: {base.get('label', key)}")

    base_progression = base_domains.get(CONTENT_DOMAIN_PROGRESSION, {})
    target_progression = target_domains.get(CONTENT_DOMAIN_PROGRESSION, {})
    if base_progression.get("xp_per_level") != target_progression.get("xp_per_level"):
        lines.append(
            f"Level-up XP requirement changed from {base_progression.get('xp_per_level')} to {target_progression.get('xp_per_level')}"
        )

    if not lines:
        lines.append("No user-visible content changes were detected.")
    return lines
