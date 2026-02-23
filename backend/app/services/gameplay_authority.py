from __future__ import annotations

from dataclasses import dataclass

from app.services.combat import compute_skill_damage
from app.services.runtime_config import load_runtime_gameplay_config

WORLD_TILE_SIZE = 32.0


@dataclass
class ActionResolution:
    accepted: bool
    reason_code: str
    server_damage: float
    xp_granted: int
    levels_gained: int
    loot_granted: list[dict]


def _movement_units_per_second(domains: dict[str, dict]) -> float:
    movement = domains.get("movement", {})
    speed_tiles = float(movement.get("player_speed_tiles", 4.6))
    return max(1.0, speed_tiles * WORLD_TILE_SIZE)


def movement_sanity_ok(
    *,
    previous_x: int | None,
    previous_y: int | None,
    reported_x: int,
    reported_y: int,
    delta_seconds: float,
) -> bool:
    if previous_x is None or previous_y is None:
        return True
    if delta_seconds <= 0:
        return False
    runtime = load_runtime_gameplay_config()
    max_speed = _movement_units_per_second(runtime.domains)
    allowed = max_speed * max(delta_seconds, 0.05) * 1.8
    dx = float(reported_x - previous_x)
    dy = float(reported_y - previous_y)
    return (dx * dx + dy * dy) ** 0.5 <= allowed


def resolve_combat_and_rewards(
    *,
    action_type: str,
    skill_key: str | None,
    character_stats: dict,
    enemies_defeated: int,
    requested_loot_tier: int,
) -> ActionResolution:
    runtime = load_runtime_gameplay_config()
    domains = runtime.domains
    progression = domains.get("progression", {})
    loot_domain = domains.get("loot", {})

    xp_per_enemy = int(progression.get("xp_per_enemy", 12))
    xp_granted = max(0, min(2000, enemies_defeated * xp_per_enemy))
    server_damage = 0.0
    reason_code = "accepted"
    accepted = True

    if action_type == "skill":
        if not skill_key:
            return ActionResolution(False, "missing_skill_key", 0.0, 0, 0, [])
        try:
            intelligence = float(character_stats.get("intellect", 0))
            server_damage = compute_skill_damage(
                runtime_to_content_snapshot(runtime.domains),
                skill_key=skill_key,
                intelligence=intelligence,
            )
        except Exception:
            return ActionResolution(False, "invalid_skill", 0.0, 0, 0, [])
    elif action_type not in {"move", "loot", "basic_attack"}:
        accepted = False
        reason_code = "invalid_action_type"

    loot_granted: list[dict] = []
    if accepted and enemies_defeated > 0:
        loot_table = loot_domain.get("tiers", {})
        tier_key = str(min(max(requested_loot_tier, 1), 10))
        tier_entries = loot_table.get(tier_key, ["scrap_shard"])
        if not isinstance(tier_entries, list) or not tier_entries:
            tier_entries = ["scrap_shard"]
        granted_item = str(tier_entries[enemies_defeated % len(tier_entries)])
        loot_granted.append({"item_key": granted_item, "qty": 1, "tier": int(tier_key)})

    return ActionResolution(
        accepted=accepted,
        reason_code=reason_code,
        server_damage=server_damage,
        xp_granted=xp_granted if accepted else 0,
        levels_gained=0,
        loot_granted=loot_granted if accepted else [],
    )


class _RuntimeSnapshot:
    def __init__(self, domains: dict[str, dict]):
        self._domains = domains

    def domain(self, key: str) -> dict:
        value = self._domains.get(key, {})
        return value if isinstance(value, dict) else {}


def runtime_to_content_snapshot(domains: dict[str, dict]):
    return _RuntimeSnapshot(domains)
