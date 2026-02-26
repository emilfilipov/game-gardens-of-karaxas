from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_db, require_admin_context
from app.models.character import Character
from app.models.level import Level
from app.models.session import UserSession
from app.schemas.character import (
    CharacterCreateRequest,
    CharacterWorldBootstrapRequest,
    CharacterWorldBootstrapResponse,
    CharacterWorldLevelResponse,
    CharacterWorldRuntimeDescriptor,
    CharacterWorldSpawnResponse,
    CharacterLevelAssignRequest,
    CharacterLocationUpdateRequest,
    CharacterResponse,
)
from app.schemas.common import VersionStatus
from app.services.content import (
    CONTENT_DOMAIN_ASSETS,
    CONTENT_DOMAIN_CHARACTER_OPTIONS,
    CONTENT_DOMAIN_PROGRESSION,
    CONTENT_DOMAIN_SKILLS,
    CONTENT_DOMAIN_STATS,
    get_active_snapshot,
)
from app.services.instance_manager import assign_session_world_instance
from app.services.party_manager import get_active_party_for_user
from app.services.runtime_config import load_runtime_gameplay_config

router = APIRouter(prefix="/characters", tags=["characters"])

APPEARANCE_OPTION_KEYS = (
    "sex",
    "body_preset",
    "skin_tone",
    "hair_style",
    "hair_color",
    "face",
    "stance",
    "lighting_profile",
)
WORLD_TILE_SIZE = 32
WORLD_TILE_OFFSET = 16
DEFAULT_CAMERA_PROFILE_KEY = "arpg_poe_baseline"
DEFAULT_SCENE_VARIANT_HINT = "arena_flat_grass"


def _xp_per_level(db: Session) -> int:
    snapshot = get_active_snapshot(db)
    progression = snapshot.domain(CONTENT_DOMAIN_PROGRESSION)
    value = progression.get("xp_per_level")
    if isinstance(value, int) and value > 0:
        return value
    return 100


def _point_budget(db: Session) -> int:
    snapshot = get_active_snapshot(db)
    options = snapshot.domain(CONTENT_DOMAIN_CHARACTER_OPTIONS)
    value = options.get("point_budget")
    if isinstance(value, int) and value > 0:
        return value
    return 10


def _allowed_stat_keys(db: Session) -> set[str]:
    snapshot = get_active_snapshot(db)
    stats = snapshot.domain(CONTENT_DOMAIN_STATS)
    entries = stats.get("entries")
    if not isinstance(entries, list):
        return set()
    return {
        str(entry.get("key", "")).strip().lower()
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("key", "")).strip()
    }


def _allowed_skill_keys(db: Session) -> set[str]:
    snapshot = get_active_snapshot(db)
    skills = snapshot.domain(CONTENT_DOMAIN_SKILLS)
    entries = skills.get("entries")
    if not isinstance(entries, list):
        return set()
    return {
        str(entry.get("key", "")).strip().lower()
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("key", "")).strip()
    }


def _stat_max_value(db: Session) -> int:
    snapshot = get_active_snapshot(db)
    stats = snapshot.domain(CONTENT_DOMAIN_STATS)
    value = stats.get("max_per_stat")
    if isinstance(value, int) and value >= 0:
        return value
    return 10


def _equipment_slots(db: Session) -> set[str]:
    snapshot = get_active_snapshot(db)
    assets = snapshot.domain(CONTENT_DOMAIN_ASSETS)
    raw_slots = assets.get("equipment_slots")
    if not isinstance(raw_slots, list):
        return set()
    allowed: set[str] = set()
    for raw in raw_slots:
        if not isinstance(raw, dict):
            continue
        slot = str(raw.get("slot", "")).strip().lower()
        if slot:
            allowed.add(slot)
    return allowed


def _default_equipment(db: Session) -> dict[str, str]:
    snapshot = get_active_snapshot(db)
    assets = snapshot.domain(CONTENT_DOMAIN_ASSETS)
    visuals = assets.get("equipment_visuals")
    if not isinstance(visuals, list):
        return {}
    defaults: dict[str, str] = {}
    for raw in visuals:
        if not isinstance(raw, dict):
            continue
        if not isinstance(raw.get("default_for_slot"), bool) or not raw.get("default_for_slot"):
            continue
        slot = str(raw.get("slot", "")).strip().lower()
        item_key = str(raw.get("item_key", "")).strip().lower()
        if slot and item_key and slot not in defaults:
            defaults[slot] = item_key
    return defaults


def _preset_catalog() -> dict[str, dict]:
    runtime = load_runtime_gameplay_config()
    presets = runtime.domains.get("character_presets", {})
    entries = presets.get("entries", [])
    if not isinstance(entries, list):
        return {}
    catalog: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key", "")).strip().lower()
        if not key:
            continue
        catalog[key] = entry
    return catalog


def _preset_entry(preset_key: str) -> dict:
    catalog = _preset_catalog()
    normalized = preset_key.strip().lower()
    if normalized and normalized in catalog:
        return catalog[normalized]
    return catalog.get("sellsword", {})


def _normalize_equipment_selection(db: Session, raw_equipment: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    allowed_slots = _equipment_slots(db)
    for raw_slot, raw_item in raw_equipment.items():
        slot = str(raw_slot).strip().lower()
        item = str(raw_item).strip().lower()
        if not slot:
            continue
        if allowed_slots and slot not in allowed_slots:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Unknown equipment slot '{raw_slot}'", "code": "invalid_equipment_slot"},
            )
        if not item:
            continue
        normalized[slot] = item
    return normalized


def _normalize_catalog_choice(db: Session, catalog_key: str, raw_value: str, fallback: str) -> str:
    snapshot = get_active_snapshot(db)
    options = snapshot.domain(CONTENT_DOMAIN_CHARACTER_OPTIONS).get(catalog_key)
    if not isinstance(options, list):
        return fallback
    normalized = raw_value.strip()
    if not normalized:
        normalized = fallback
    for entry in options:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("value", "")).strip()
        label = str(entry.get("label", "")).strip()
        if normalized.lower() in {value.lower(), label.lower()}:
            return label or value or fallback
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"message": f"Invalid {catalog_key} option '{raw_value}'", "code": "invalid_option_choice"},
    )


def _appearance_catalog(db: Session) -> dict[str, set[str]]:
    snapshot = get_active_snapshot(db)
    options = snapshot.domain(CONTENT_DOMAIN_CHARACTER_OPTIONS)
    raw_appearance = options.get("appearance", {})
    if not isinstance(raw_appearance, dict):
        return {}
    catalog: dict[str, set[str]] = {}
    for field in APPEARANCE_OPTION_KEYS:
        values: set[str] = set()
        entries = raw_appearance.get(field, [])
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                value = str(entry.get("value", entry.get("label", ""))).strip().lower()
                if value:
                    values.add(value)
        if values:
            catalog[field] = values
    return catalog


def _normalize_appearance_profile(db: Session, raw_profile: dict, appearance_key: str) -> dict:
    if not isinstance(raw_profile, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "appearance_profile must be an object", "code": "invalid_appearance_profile"},
        )

    normalized_key = appearance_key.strip().lower() or "human_male"
    catalog = _appearance_catalog(db)
    defaults = {
        "sex": normalized_key,
        "body_preset": "adventurer",
        "skin_tone": "warm_bronze",
        "hair_style": "short",
        "hair_color": "umber",
        "face": "calm",
        "stance": "neutral",
        "lighting_profile": "warm_torchlight",
    }
    for key, values in catalog.items():
        if values and defaults.get(key, "") not in values:
            defaults[key] = sorted(values)[0]
    defaults["sex"] = normalized_key if "sex" not in catalog or normalized_key in catalog["sex"] else defaults["sex"]

    result: dict[str, str | int] = {"version": 1}
    for key in APPEARANCE_OPTION_KEYS:
        value = raw_profile.get(key, defaults.get(key, ""))
        normalized_value = str(value).strip().lower()
        if not normalized_value:
            normalized_value = str(defaults.get(key, "")).strip().lower()
        allowed = catalog.get(key)
        if allowed and normalized_value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": f"Invalid appearance option '{key}={value}'",
                    "code": "invalid_appearance_profile_choice",
                },
            )
        result[key] = normalized_value
    return result


def _to_response(character: Character, xp_per_level: int) -> CharacterResponse:
    band = xp_per_level if xp_per_level > 0 else 100
    current_band_progress = character.experience % band
    return CharacterResponse(
        id=character.id,
        name=character.name,
        preset_key=character.preset_key,
        level_id=character.level_id,
        location_x=character.location_x,
        location_y=character.location_y,
        appearance_key=character.appearance_key,
        appearance_profile=character.appearance_profile if isinstance(character.appearance_profile, dict) else {},
        race=character.race,
        background=character.background,
        affiliation=character.affiliation,
        level=character.level,
        experience=character.experience,
        experience_to_next_level=band - current_band_progress if current_band_progress > 0 else band,
        stat_points_total=character.stat_points_total,
        stat_points_used=character.stat_points_used,
        equipment=character.equipment,
        inventory=character.inventory if isinstance(character.inventory, list) else [],
        stats=character.stats,
        skills=character.skills,
        is_selected=character.is_selected,
        created_at=character.created_at,
        updated_at=character.updated_at,
    )


def _first_level_spawn(db: Session) -> tuple[int, int, int] | None:
    level = db.execute(select(Level).order_by(Level.order_index.asc(), Level.id.asc()).limit(1)).scalar_one_or_none()
    if level is None:
        return None
    return level.id, level.spawn_x, level.spawn_y


def _tile_to_world(tile_value: int) -> int:
    return tile_value * WORLD_TILE_SIZE + WORLD_TILE_OFFSET


def _world_to_tile(world_value: int) -> int:
    return max(0, int(round((world_value - WORLD_TILE_OFFSET) / float(WORLD_TILE_SIZE))))


def _parse_level_layers(level: Level) -> dict[int, list[dict]]:
    raw_layers = level.layer_cells if isinstance(level.layer_cells, dict) else {}
    if not raw_layers:
        fallback_walls = level.wall_cells if isinstance(level.wall_cells, list) else []
        return {
            1: [
                {"x": int(cell.get("x", 0)), "y": int(cell.get("y", 0)), "asset_key": "wall_block"}
                for cell in fallback_walls
                if isinstance(cell, dict)
            ]
        }
    parsed: dict[int, list[dict]] = {}
    for raw_key, raw_cells in raw_layers.items():
        try:
            layer_id = int(raw_key)
        except (TypeError, ValueError):
            continue
        if not isinstance(raw_cells, list):
            continue
        parsed_cells: list[dict] = []
        for cell in raw_cells:
            if not isinstance(cell, dict):
                continue
            parsed_cells.append(
                {
                    "x": int(cell.get("x", 0)),
                    "y": int(cell.get("y", 0)),
                    "asset_key": str(cell.get("asset_key", "decor")).strip().lower() or "decor",
                }
            )
        parsed[layer_id] = parsed_cells
    return parsed


def _parse_level_objects(level: Level) -> list[dict]:
    raw_objects = level.object_placements if isinstance(level.object_placements, list) else []
    parsed: list[dict] = []
    for raw in raw_objects:
        if not isinstance(raw, dict):
            continue
        transform = raw.get("transform", {}) if isinstance(raw.get("transform", {}), dict) else {}
        parsed.append(
            {
                "object_id": str(raw.get("object_id", "")).strip().lower(),
                "asset_key": str(raw.get("asset_key", "")).strip().lower(),
                "layer_id": int(raw.get("layer_id", 0)),
                "transform": {
                    "x": float(transform.get("x", 0.0)),
                    "y": float(transform.get("y", 0.0)),
                    "z": float(transform.get("z", 0.0)),
                    "rotation_deg": float(transform.get("rotation_deg", 0.0)),
                    "scale_x": float(transform.get("scale_x", 1.0)),
                    "scale_y": float(transform.get("scale_y", 1.0)),
                    "pivot_x": float(transform.get("pivot_x", 0.5)),
                    "pivot_y": float(transform.get("pivot_y", 1.0)),
                },
            }
        )
    return parsed


def _resolve_spawn_marker_3d_metadata(level: Level) -> tuple[float, float]:
    raw_objects = level.object_placements if isinstance(level.object_placements, list) else []
    for raw in raw_objects:
        if not isinstance(raw, dict):
            continue
        object_id = str(raw.get("object_id", "")).strip().lower()
        asset_key = str(raw.get("asset_key", "")).strip().lower()
        if object_id != "spawn_marker_3d" and asset_key not in {"spawn_marker", "spawn_marker_3d"}:
            continue
        transform = raw.get("transform", {})
        if not isinstance(transform, dict):
            transform = {}
        return float(transform.get("z", 0.0)), float(transform.get("rotation_deg", 0.0))
    return 0.0, 0.0


def _parse_level_transitions(level: Level) -> list[dict]:
    raw_transitions = level.transitions if isinstance(level.transitions, list) else []
    parsed: list[dict] = []
    for raw in raw_transitions:
        if not isinstance(raw, dict):
            continue
        parsed.append(
            {
                "x": int(raw.get("x", 0)),
                "y": int(raw.get("y", 0)),
                "transition_type": str(raw.get("transition_type", "")).strip().lower(),
                "destination_level_id": int(raw.get("destination_level_id", 0)),
            }
        )
    return parsed


def _resolve_camera_profile_key(runtime_domains: dict[str, dict]) -> str:
    runtime_client = runtime_domains.get("runtime_client", {})
    if isinstance(runtime_client, dict):
        profile_key = str(runtime_client.get("camera_profile_key", "")).strip().lower()
        if profile_key:
            return profile_key
    world_3d = runtime_domains.get("world_3d", {})
    if isinstance(world_3d, dict):
        profile_key = str(world_3d.get("camera_profile_key", "")).strip().lower()
        if profile_key:
            return profile_key
    return DEFAULT_CAMERA_PROFILE_KEY


def _level_map_scale_metadata() -> dict[str, float]:
    return {
        "tile_world_size": float(WORLD_TILE_SIZE),
        "tile_world_offset": float(WORLD_TILE_OFFSET),
        "world_units_per_tile": 1.0,
    }


def _resolve_scene_variant_hint(level: Level) -> str:
    if bool(level.is_town_hub):
        return "town_hub"
    return DEFAULT_SCENE_VARIANT_HINT


def _resolve_world_spawn(character: Character, level: Level, override_applied: bool) -> tuple[int, int, int, int, str]:
    if not override_applied and character.location_x is not None and character.location_y is not None:
        stored_x = int(character.location_x)
        stored_y = int(character.location_y)
        # Existing data can contain tile coordinates (legacy/new character defaults) or world coordinates.
        if 0 <= stored_x < int(level.width) and 0 <= stored_y < int(level.height):
            world_x = _tile_to_world(stored_x)
            world_y = _tile_to_world(stored_y)
            return stored_x, stored_y, world_x, world_y, "saved_tile_location"
        tile_x = _world_to_tile(stored_x)
        tile_y = _world_to_tile(stored_y)
        return tile_x, tile_y, stored_x, stored_y, "saved_world_location"

    spawn_tile_x = int(level.spawn_x)
    spawn_tile_y = int(level.spawn_y)
    return (
        spawn_tile_x,
        spawn_tile_y,
        _tile_to_world(spawn_tile_x),
        _tile_to_world(spawn_tile_y),
        "level_spawn",
    )


def _apply_selected_character(db: Session, user_id: int, character_id: int) -> None:
    rows = db.execute(select(Character).where(Character.user_id == user_id)).scalars().all()
    for row in rows:
        row.is_selected = row.id == character_id
        db.add(row)


def _version_status_model(context: AuthContext) -> VersionStatus:
    evaluated = context.version_status
    return VersionStatus(
        client_version=evaluated.client_version,
        latest_version=evaluated.latest_version,
        min_supported_version=evaluated.min_supported_version,
        client_content_version_key=evaluated.client_content_version_key,
        latest_content_version_key=evaluated.latest_content_version_key,
        min_supported_content_version_key=evaluated.min_supported_content_version_key,
        enforce_after=evaluated.enforce_after,
        update_available=evaluated.update_available,
        content_update_available=evaluated.content_update_available,
        force_update=evaluated.force_update,
        update_feed_url=evaluated.update_feed_url,
    )


@router.get("", response_model=list[CharacterResponse])
def list_characters(context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    xp_per_level = _xp_per_level(db)
    rows = db.execute(
        select(Character).where(Character.user_id == context.user.id).order_by(Character.created_at.asc())
    ).scalars()
    return [_to_response(row, xp_per_level=xp_per_level) for row in rows]


@router.post("", response_model=CharacterResponse)
def create_character(
    payload: CharacterCreateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    normalized_name = payload.name.strip()
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Character name is required", "code": "invalid_character_name"},
        )
    existing = db.execute(select(Character.id).where(func.lower(Character.name) == normalized_name.lower())).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Character name already exists", "code": "character_name_taken"},
        )

    preset = _preset_entry(payload.preset_key)
    configured_budget = int(preset.get("point_budget", _point_budget(db)))
    allowed_stats = _allowed_stat_keys(db)
    allowed_skills = _allowed_skill_keys(db)
    max_per_stat = _stat_max_value(db)
    default_equipment = _default_equipment(db)
    preset_stats = preset.get("stats", {}) if isinstance(preset.get("stats", {}), dict) else {}
    preset_skills = preset.get("skills", {}) if isinstance(preset.get("skills", {}), dict) else {}

    normalized_stats: dict[str, int] = {}
    merged_stats = dict(preset_stats)
    merged_stats.update(payload.stats)
    for key, value in merged_stats.items():
        normalized_key = key.strip().lower()
        if normalized_key not in allowed_stats:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Unknown stat key '{key}'", "code": "invalid_stat_key"},
            )
        if not isinstance(value, int) or value < 0 or value > max_per_stat:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Stat '{key}' must be between 0 and {max_per_stat}", "code": "invalid_stat_value"},
            )
        normalized_stats[normalized_key] = value

    normalized_skills: dict[str, int] = {}
    merged_skills = dict(preset_skills)
    merged_skills.update(payload.skills)
    for key, value in merged_skills.items():
        normalized_key = key.strip().lower()
        if normalized_key not in allowed_skills:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Unknown skill key '{key}'", "code": "invalid_skill_key"},
            )
        if not isinstance(value, int) or value < 0 or value > 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": f"Skill '{key}' must be 0 or 1", "code": "invalid_skill_value"},
            )
        normalized_skills[normalized_key] = value
    normalized_equipment = _normalize_equipment_selection(db, payload.equipment)
    merged_equipment = dict(default_equipment)
    merged_equipment.update(normalized_equipment)

    stat_points_used = sum(v for v in normalized_stats.values() if v > 0) + sum(v for v in normalized_skills.values() if v > 0)
    if stat_points_used > configured_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Allocated points exceed total", "code": "invalid_point_budget"},
        )

    default_spawn = _first_level_spawn(db)
    requested_appearance_key = str(payload.appearance_key).strip()
    resolved_appearance_key = requested_appearance_key or str(preset.get("appearance_key", "human_male")).strip()

    character = Character(
        user_id=context.user.id,
        name=normalized_name,
        preset_key=str(payload.preset_key).strip().lower() or "sellsword",
        level_id=default_spawn[0] if default_spawn is not None else None,
        location_x=default_spawn[1] if default_spawn is not None else None,
        location_y=default_spawn[2] if default_spawn is not None else None,
        appearance_key=resolved_appearance_key,
        appearance_profile=_normalize_appearance_profile(
            db,
            payload.appearance_profile,
            resolved_appearance_key,
        ),
        race=_normalize_catalog_choice(db, "race", str(preset.get("race", payload.race)), "Human"),
        background=_normalize_catalog_choice(db, "background", str(preset.get("background", payload.background)), "Drifter"),
        affiliation=_normalize_catalog_choice(db, "affiliation", str(preset.get("affiliation", payload.affiliation)), "Unaffiliated"),
        stat_points_total=configured_budget,
        stat_points_used=stat_points_used,
        level=1,
        experience=0,
        equipment=merged_equipment,
        inventory=list(preset.get("starting_inventory", [])) if isinstance(preset.get("starting_inventory", []), list) else [],
        stats=normalized_stats,
        skills=normalized_skills,
        is_selected=False,
    )
    db.add(character)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Character name already exists", "code": "character_name_taken"},
        ) from None
    db.refresh(character)
    return _to_response(character, xp_per_level=_xp_per_level(db))


@router.post("/{character_id}/select")
def select_character(character_id: int, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    _apply_selected_character(db, context.user.id, character_id)
    db.commit()
    return {"ok": True, "character_id": character_id}


@router.post("/{character_id}/world-bootstrap", response_model=CharacterWorldBootstrapResponse)
def bootstrap_character_world(
    character_id: int,
    payload: CharacterWorldBootstrapRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    override_level_id = payload.override_level_id
    override_applied = False
    if override_level_id is not None:
        if not context.user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Admin access required for override level", "code": "admin_required"},
            )
        override_applied = True

    target_level: Level | None = None
    if override_level_id is not None:
        target_level = db.get(Level, override_level_id)
    elif character.level_id is not None:
        target_level = db.get(Level, character.level_id)

    if target_level is None:
        target_level = db.execute(select(Level).order_by(Level.order_index.asc(), Level.id.asc()).limit(1)).scalar_one_or_none()
        if target_level is not None and not override_applied:
            character.level_id = target_level.id
            character.location_x = target_level.spawn_x
            character.location_y = target_level.spawn_y
            db.add(character)

    if target_level is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "No playable level is available", "code": "no_playable_level"},
        )

    _apply_selected_character(db, context.user.id, character_id)
    db.commit()
    db.refresh(character)

    tile_x, tile_y, world_x, world_y, spawn_source = _resolve_world_spawn(character, target_level, override_applied)
    runtime_cfg = load_runtime_gameplay_config()
    spawn_world_z, spawn_yaw_deg = _resolve_spawn_marker_3d_metadata(target_level)
    camera_profile_key = _resolve_camera_profile_key(runtime_cfg.domains)

    level_payload = CharacterWorldLevelResponse(
        id=target_level.id,
        name=target_level.name,
        descriptive_name=target_level.descriptive_name,
        width=target_level.width,
        height=target_level.height,
        spawn_x=target_level.spawn_x,
        spawn_y=target_level.spawn_y,
        is_town_hub=bool(target_level.is_town_hub),
        map_scale=_level_map_scale_metadata(),
        scene_variant_hint=_resolve_scene_variant_hint(target_level),
        layers=_parse_level_layers(target_level),
        objects=_parse_level_objects(target_level),
        transitions=_parse_level_transitions(target_level),
    )
    active_party = get_active_party_for_user(db, context.user.id)
    assignment = assign_session_world_instance(
        db,
        session=context.session,
        user_id=context.user.id,
        character_id=character.id,
        level_id=target_level.id,
        party_id=active_party.id if active_party is not None else None,
        is_hub_level=bool(target_level.is_town_hub),
    )
    context.session.current_location_x = world_x
    context.session.current_location_y = world_y
    db.add(context.session)
    db.commit()
    db.refresh(character)
    return CharacterWorldBootstrapResponse(
        character=_to_response(character, xp_per_level=_xp_per_level(db)),
        level=level_payload,
        spawn=CharacterWorldSpawnResponse(
            tile_x=tile_x,
            tile_y=tile_y,
            world_x=world_x,
            world_y=world_y,
            world_z=spawn_world_z,
            yaw_deg=spawn_yaw_deg,
            source=spawn_source,
        ),
        instance={
            "id": assignment.instance_id,
            "kind": assignment.instance_kind,
            "level_id": assignment.level_id,
            "party_id": assignment.party_id,
            "restored": assignment.restored,
            "expires_at": assignment.expires_at,
        },
        runtime=CharacterWorldRuntimeDescriptor(
            config_key=runtime_cfg.config_key,
            content_contract_signature=runtime_cfg.content_contract_signature,
            camera_profile_key=camera_profile_key,
        ),
        runtime_domains=runtime_cfg.domains,
        player_runtime={
            "player_level": character.level,
            "player_stats": character.stats if isinstance(character.stats, dict) else {},
            "equipment_bonus_stats": {},
        },
        version_status=_version_status_model(context),
    )


@router.delete("/{character_id}")
def delete_character(character_id: int, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )
    was_selected = character.is_selected
    db.delete(character)
    db.commit()
    return {"ok": True, "character_id": character_id, "selection_cleared": was_selected}


@router.post("/{character_id}/level")
def assign_character_level(
    character_id: int,
    payload: CharacterLevelAssignRequest,
    context: AuthContext = Depends(require_admin_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    level_id = payload.level_id
    spawn_x: int | None = None
    spawn_y: int | None = None
    if level_id is not None:
        level = db.get(Level, level_id)
        if level is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Level not found", "code": "level_not_found"},
            )
        spawn_x = level.spawn_x
        spawn_y = level.spawn_y

    character.level_id = level_id
    character.location_x = spawn_x
    character.location_y = spawn_y
    db.add(character)
    db.commit()
    return {
        "ok": True,
        "character_id": character.id,
        "level_id": character.level_id,
        "location_x": character.location_x,
        "location_y": character.location_y,
    }


@router.post("/{character_id}/location")
def update_character_location(
    character_id: int,
    payload: CharacterLocationUpdateRequest,
    context: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    character = db.get(Character, character_id)
    if character is None or character.user_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Character not found", "code": "character_not_found"},
        )

    level_id = payload.level_id
    if level_id is not None:
        level = db.get(Level, level_id)
        if level is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Level not found", "code": "level_not_found"},
            )

    character.level_id = level_id
    character.location_x = payload.location_x
    character.location_y = payload.location_y
    db.add(character)
    session = db.get(UserSession, context.session.id)
    if session is not None:
        session.current_level_id = level_id
        session.current_location_x = payload.location_x
        session.current_location_y = payload.location_y
        session.current_character_id = character.id
        db.add(session)
    db.commit()
    return {
        "ok": True,
        "character_id": character.id,
        "level_id": character.level_id,
        "location_x": character.location_x,
        "location_y": character.location_y,
    }
