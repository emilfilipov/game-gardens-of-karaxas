extends Control

signal player_position_changed(position: Vector2)
signal transition_requested(transition: Dictionary)
signal combat_state_changed(state: Dictionary)
signal loot_dropped(item: Dictionary)
signal quest_event(event: Dictionary)
signal npc_interacted(npc: Dictionary)

const ISO = preload("res://scripts/iso_projection.gd")
const UI_TOKENS = preload("res://scripts/ui_tokens.gd")

const GRID_UNIT_PIXELS: float = 32.0
const DEFAULT_PLAYER_SPEED_TILES: float = 4.6
const DEFAULT_PLAYER_RADIUS: float = 14.0

var world_width_tiles: int = 80
var world_height_tiles: int = 48
var player_tile_position: Vector2 = Vector2(3.0, 3.0)
var player_facing: String = "S"
var world_name: String = "Default"
var player_speed_tiles: float = DEFAULT_PLAYER_SPEED_TILES
var player_radius: float = DEFAULT_PLAYER_RADIUS
var _active: bool = false

var floor_tiles: Array[Vector2i] = []
var prop_tiles: Array[Dictionary] = []
var foreground_tiles: Array[Dictionary] = []
var blocked_tiles: Dictionary = {}
var show_sort_diagnostics: bool = false
var asset_templates: Dictionary = {}
var transitions: Array[Dictionary] = []
var player_collision_layer: String = "ground"
var _transition_cooldown: float = 0.0

var keybinds: Dictionary = {
	"move_up": KEY_W,
	"move_down": KEY_S,
	"move_left": KEY_A,
	"move_right": KEY_D,
	"basic_attack": KEY_SPACE,
	"ability_1": KEY_1,
	"ability_2": KEY_2,
	"ability_3": KEY_3,
	"ability_4": KEY_4,
	"interact": KEY_E,
	"pickup": KEY_F,
}
var _previous_key_states: Dictionary = {}

var player_base_stats: Dictionary = {}
var player_bonus_stats: Dictionary = {}
var player_max_health: float = 100.0
var player_health: float = 100.0
var player_max_mana: float = 60.0
var player_mana: float = 60.0
var player_regen_health: float = 0.8
var player_regen_mana: float = 2.1
var player_level: int = 1

var basic_attack_cfg: Dictionary = {
	"damage": 8.0,
	"range": 1.3,
	"cooldown": 0.45,
}
var ability_catalog: Dictionary = {}
var ability_cooldowns: Dictionary = {}
var ability_resource_pool: String = "mana"

var enemy_catalog: Dictionary = {}
var enemy_spawn_rules: Array = []
var enemies: Array[Dictionary] = []
var enemy_id_counter: int = 1

var pickups: Array[Dictionary] = []
var pickup_id_counter: int = 1

var npcs: Array[Dictionary] = []

func configure_world(level_name: String, width_tiles: int, height_tiles: int, spawn_world: Vector2, level_payload: Dictionary = {}) -> void:
	world_name = level_name
	world_width_tiles = maxi(width_tiles, 6)
	world_height_tiles = maxi(height_tiles, 6)
	player_tile_position = _clamp_tile_position(_world_pixels_to_tile(spawn_world))
	asset_templates = {}
	transitions = []
	player_collision_layer = str(level_payload.get("player_collision_layer", "ground")).strip_edges().to_lower()
	if player_collision_layer.is_empty():
		player_collision_layer = "ground"
	var raw_templates = level_payload.get("asset_templates", {})
	if raw_templates is Dictionary:
		asset_templates = raw_templates
	var raw_transitions = level_payload.get("transitions", [])
	if raw_transitions is Array:
		for raw in raw_transitions:
			if not (raw is Dictionary):
				continue
			transitions.append(raw)
	_transition_cooldown = 0.0
	_build_default_floor()
	_ingest_level_layers(level_payload)
	_spawn_level_content(level_payload)
	_emit_combat_state()
	queue_redraw()

func configure_runtime(runtime_cfg: Dictionary) -> void:
	if not (runtime_cfg is Dictionary):
		return
	var runtime_keybinds = runtime_cfg.get("keybinds", {})
	if runtime_keybinds is Dictionary:
		for action_name in runtime_keybinds.keys():
			keybinds[action_name] = int(runtime_keybinds.get(action_name, keybinds.get(action_name, 0)))
	var movement_cfg: Dictionary = runtime_cfg.get("movement", {}) if runtime_cfg.has("movement") else runtime_cfg
	player_speed_tiles = maxf(0.5, float(movement_cfg.get("player_speed_tiles", DEFAULT_PLAYER_SPEED_TILES)))
	player_radius = maxf(2.0, float(movement_cfg.get("player_radius", DEFAULT_PLAYER_RADIUS)))

	player_level = int(runtime_cfg.get("player_level", 1))
	player_base_stats = runtime_cfg.get("player_stats", {}) if runtime_cfg.get("player_stats", {}) is Dictionary else {}
	player_bonus_stats = runtime_cfg.get("equipment_bonus_stats", {}) if runtime_cfg.get("equipment_bonus_stats", {}) is Dictionary else {}

	var player_cfg: Dictionary = runtime_cfg.get("player", {}) if runtime_cfg.get("player", {}) is Dictionary else {}
	player_max_health = maxf(1.0, float(player_cfg.get("base_health", 100.0 + _stat_value("vitality") * 8.0)))
	player_max_mana = maxf(1.0, float(player_cfg.get("base_mana", 60.0 + _stat_value("willpower") * 6.0)))
	player_regen_health = maxf(0.0, float(player_cfg.get("health_regen", 0.8)))
	player_regen_mana = maxf(0.0, float(player_cfg.get("mana_regen", 2.1)))
	if player_health <= 0.0:
		player_health = player_max_health
	else:
		player_health = clampf(player_health, 0.0, player_max_health)
	player_mana = clampf(player_mana, 0.0, player_max_mana)

	ability_catalog.clear()
	ability_cooldowns.clear()
	var combat_cfg: Dictionary = runtime_cfg.get("combat", {}) if runtime_cfg.get("combat", {}) is Dictionary else {}
	var basic_cfg: Dictionary = combat_cfg.get("basic_attack", {}) if combat_cfg.get("basic_attack", {}) is Dictionary else {}
	basic_attack_cfg = {
		"damage": float(basic_cfg.get("damage", 8.0)),
		"range": float(basic_cfg.get("range", 1.3)),
		"cooldown": float(basic_cfg.get("cooldown", 0.45)),
	}
	ability_resource_pool = str(combat_cfg.get("resource_pool", "mana")).strip_edges().to_lower()
	if ability_resource_pool.is_empty():
		ability_resource_pool = "mana"
	var abilities: Array = combat_cfg.get("abilities", []) if combat_cfg.get("abilities", []) is Array else []
	for raw_ability in abilities:
		if not (raw_ability is Dictionary):
			continue
		var key = str(raw_ability.get("key", "")).strip_edges().to_lower()
		if key.is_empty():
			continue
		ability_catalog[key] = raw_ability
		ability_cooldowns[key] = 0.0
	ability_cooldowns["basic_attack"] = 0.0

	enemy_catalog.clear()
	var enemies_cfg: Dictionary = runtime_cfg.get("enemies", {}) if runtime_cfg.get("enemies", {}) is Dictionary else {}
	var enemy_entries: Array = enemies_cfg.get("catalog", []) if enemies_cfg.get("catalog", []) is Array else []
	for raw_enemy in enemy_entries:
		if not (raw_enemy is Dictionary):
			continue
		var enemy_key = str(raw_enemy.get("key", "")).strip_edges().to_lower()
		if enemy_key.is_empty():
			continue
		enemy_catalog[enemy_key] = raw_enemy
	enemy_spawn_rules = enemies_cfg.get("spawn", []) if enemies_cfg.get("spawn", []) is Array else []

	npcs.clear()
	var npc_entries: Array = runtime_cfg.get("npcs", []) if runtime_cfg.get("npcs", []) is Array else []
	for raw_npc in npc_entries:
		if raw_npc is Dictionary:
			npcs.append(raw_npc)

	_emit_combat_state()

func set_world_position(world_position: Vector2) -> void:
	player_tile_position = _clamp_tile_position(_world_pixels_to_tile(world_position))
	queue_redraw()

func get_world_position() -> Vector2:
	return _tile_to_world_pixels(player_tile_position)

func set_active(active: bool) -> void:
	_active = active
	set_process(active)
	if active:
		grab_focus()

func _ready() -> void:
	focus_mode = Control.FOCUS_ALL
	set_process(false)
	_build_default_floor()

func _process(delta: float) -> void:
	if not _active:
		return
	if _transition_cooldown > 0.0:
		_transition_cooldown = maxf(0.0, _transition_cooldown - delta)
	_update_cooldowns(delta)
	_update_player_regen(delta)
	_handle_combat_inputs()

	var axis: Vector2 = _movement_axis()
	if axis != Vector2.ZERO:
		var next_pos: Vector2 = _clamp_tile_position(player_tile_position + axis.normalized() * player_speed_tiles * delta)
		if not _is_blocked(next_pos):
			player_tile_position = next_pos
			player_facing = _axis_to_facing(axis)
			emit_signal("player_position_changed", _tile_to_world_pixels(player_tile_position))

	_update_enemies(delta)
	_check_pickup_action()
	_check_npc_interaction_action()
	_check_transition_trigger()
	queue_redraw()

func _movement_axis() -> Vector2:
	var axis = Vector2.ZERO
	if _action_pressed("move_up"):
		axis += Vector2(-1.0, -1.0)
	if _action_pressed("move_down"):
		axis += Vector2(1.0, 1.0)
	if _action_pressed("move_left"):
		axis += Vector2(-1.0, 1.0)
	if _action_pressed("move_right"):
		axis += Vector2(1.0, -1.0)
	return axis

func _axis_to_facing(axis: Vector2) -> String:
	var sx = int(sign(axis.x))
	var sy = int(sign(axis.y))
	if sx == -1 and sy == -1:
		return "N"
	if sx == 0 and sy == -1:
		return "NE"
	if sx == 1 and sy == -1:
		return "E"
	if sx == 1 and sy == 0:
		return "SE"
	if sx == 1 and sy == 1:
		return "S"
	if sx == 0 and sy == 1:
		return "SW"
	if sx == -1 and sy == 1:
		return "W"
	if sx == -1 and sy == 0:
		return "NW"
	return player_facing

func _action_pressed(action_name: String) -> bool:
	var keycode = int(keybinds.get(action_name, 0))
	if keycode <= 0:
		return false
	return Input.is_key_pressed(keycode)

func _action_just_pressed(action_name: String) -> bool:
	var now_pressed = _action_pressed(action_name)
	var prev_pressed = bool(_previous_key_states.get(action_name, false))
	_previous_key_states[action_name] = now_pressed
	return now_pressed and not prev_pressed

func _update_cooldowns(delta: float) -> void:
	for key in ability_cooldowns.keys():
		ability_cooldowns[key] = maxf(0.0, float(ability_cooldowns.get(key, 0.0)) - delta)

func _update_player_regen(delta: float) -> void:
	player_health = minf(player_max_health, player_health + player_regen_health * delta)
	player_mana = minf(player_max_mana, player_mana + player_regen_mana * delta)

func _handle_combat_inputs() -> void:
	if _action_just_pressed("basic_attack"):
		_cast_basic_attack()
	if _action_just_pressed("ability_1"):
		_cast_ability("ember")
	if _action_just_pressed("ability_2"):
		_cast_ability("cleave")
	if _action_just_pressed("ability_3"):
		_cast_ability("quick_strike")
	if _action_just_pressed("ability_4"):
		_cast_ability("bandage")

func _cast_basic_attack() -> void:
	if float(ability_cooldowns.get("basic_attack", 0.0)) > 0.0:
		return
	ability_cooldowns["basic_attack"] = float(basic_attack_cfg.get("cooldown", 0.45))
	var damage = float(basic_attack_cfg.get("damage", 8.0)) + _stat_value("strength") * 0.7
	var range_tiles = float(basic_attack_cfg.get("range", 1.3))
	_apply_damage_to_targets(damage, range_tiles, 1)
	_emit_combat_state()

func _cast_ability(ability_key: String) -> void:
	var key = ability_key.strip_edges().to_lower()
	if not ability_catalog.has(key):
		return
	if float(ability_cooldowns.get(key, 0.0)) > 0.0:
		return
	var ability: Dictionary = ability_catalog.get(key, {})
	var resource_cost = float(ability.get("resource_cost", 0.0))
	if ability_resource_pool == "mana" and player_mana < resource_cost:
		return
	if ability_resource_pool == "mana":
		player_mana = maxf(0.0, player_mana - resource_cost)
	ability_cooldowns[key] = maxf(0.1, float(ability.get("cooldown", 1.0)))

	if key == "bandage":
		var heal_amount = float(ability.get("heal", 15.0)) + _stat_value("willpower") * 0.7
		player_health = minf(player_max_health, player_health + heal_amount)
		_emit_combat_state()
		return

	var base_damage = float(ability.get("damage", 10.0))
	var scaling_stat = str(ability.get("scaling_stat", "strength")).strip_edges().to_lower()
	var scaled_damage = base_damage + _stat_value(scaling_stat) * 0.8
	var max_targets = int(ability.get("max_targets", 1))
	if key == "cleave":
		max_targets = maxi(max_targets, 3)
	var range_tiles = float(ability.get("range", 2.0))
	_apply_damage_to_targets(scaled_damage, range_tiles, max_targets)
	_emit_combat_state()

func _apply_damage_to_targets(damage: float, range_tiles: float, max_targets: int) -> void:
	var indexed_hits: Array = []
	for i in range(enemies.size()):
		var enemy: Dictionary = enemies[i]
		if bool(enemy.get("dead", false)):
			continue
		var enemy_pos = enemy.get("pos", Vector2.ZERO)
		var distance = player_tile_position.distance_to(enemy_pos)
		if distance <= range_tiles:
			indexed_hits.append({"index": i, "distance": distance})
	indexed_hits.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a.get("distance", 9999.0)) < float(b.get("distance", 9999.0))
	)
	var hits = mini(max_targets, indexed_hits.size())
	for h in range(hits):
		var index = int(indexed_hits[h].get("index", -1))
		if index < 0 or index >= enemies.size():
			continue
		var updated: Dictionary = enemies[index]
		updated["health"] = float(updated.get("health", 1.0)) - damage
		if float(updated.get("health", 0.0)) <= 0.0:
			updated["dead"] = true
			_on_enemy_killed(updated)
		enemies[index] = updated

func _update_enemies(delta: float) -> void:
	for i in range(enemies.size()):
		var enemy: Dictionary = enemies[i]
		if bool(enemy.get("dead", false)):
			continue
		var pos = enemy.get("pos", Vector2.ZERO)
		var attack_timer = maxf(0.0, float(enemy.get("attack_timer", 0.0)) - delta)
		enemy["attack_timer"] = attack_timer
		var dist = player_tile_position.distance_to(pos)
		var aggro = float(enemy.get("aggro_range", 5.0))
		var attack_range = float(enemy.get("attack_range", 1.0))
		var move_speed = float(enemy.get("move_speed", 2.0))
		if dist <= aggro and dist > attack_range:
			var direction = (player_tile_position - pos).normalized()
			var next_pos = _clamp_tile_position(pos + direction * move_speed * delta)
			if not _is_blocked(next_pos):
				enemy["pos"] = next_pos
		elif dist <= attack_range and attack_timer <= 0.0:
			var attack_damage = float(enemy.get("attack_damage", 4.0))
			player_health = maxf(0.0, player_health - attack_damage)
			enemy["attack_timer"] = maxf(0.2, float(enemy.get("attack_cooldown", 1.2)))
			_emit_combat_state()
		enemies[i] = enemy

func _on_enemy_killed(enemy: Dictionary) -> void:
	var enemy_type = str(enemy.get("type", "enemy"))
	emit_signal("quest_event", {
		"type": "enemy_killed",
		"enemy_type": enemy_type,
	})
	var loot_table = enemy.get("loot", [])
	if loot_table is Array and not loot_table.is_empty():
		for raw_entry in loot_table:
			if not (raw_entry is Dictionary):
				continue
			var drop_chance = clampf(float(raw_entry.get("chance", 0.0)), 0.0, 1.0)
			if randf() <= drop_chance:
				var item_key = str(raw_entry.get("item_key", "")).strip_edges().to_lower()
				if item_key.is_empty():
					continue
				var pickup = {
					"id": pickup_id_counter,
					"item_key": item_key,
					"count": int(raw_entry.get("count", 1)),
					"pos": enemy.get("pos", player_tile_position),
				}
				pickup_id_counter += 1
				pickups.append(pickup)
				break

func _check_pickup_action() -> void:
	if not _action_just_pressed("pickup"):
		return
	for i in range(pickups.size()):
		var pickup = pickups[i]
		var pickup_pos = pickup.get("pos", Vector2.ZERO)
		if player_tile_position.distance_to(pickup_pos) <= 1.2:
			emit_signal("loot_dropped", {
				"item_key": str(pickup.get("item_key", "")),
				"count": int(pickup.get("count", 1)),
			})
			pickups.remove_at(i)
			return

func _check_npc_interaction_action() -> void:
	if not _action_just_pressed("interact"):
		return
	for npc in npcs:
		if not (npc is Dictionary):
			continue
		var npc_x = float(npc.get("x", npc.get("tile_x", -99)))
		var npc_y = float(npc.get("y", npc.get("tile_y", -99)))
		if npc_x < -1 or npc_y < -1:
			continue
		var npc_pos = Vector2(npc_x, npc_y)
		if player_tile_position.distance_to(npc_pos) <= 1.6:
			emit_signal("npc_interacted", npc)
			return

func apply_player_heal(amount: float) -> void:
	player_health = minf(player_max_health, player_health + maxf(0.0, amount))
	_emit_combat_state()

func apply_player_mana(amount: float) -> void:
	player_mana = minf(player_max_mana, player_mana + maxf(0.0, amount))
	_emit_combat_state()

func apply_equipment_modifiers(stat_bonus: Dictionary) -> void:
	if stat_bonus is Dictionary:
		player_bonus_stats = stat_bonus
	_emit_combat_state()

func get_combat_snapshot() -> Dictionary:
	var cooldowns: Dictionary = {}
	for key in ability_cooldowns.keys():
		cooldowns[key] = snappedf(float(ability_cooldowns.get(key, 0.0)), 0.01)
	return {
		"health": snappedf(player_health, 0.1),
		"max_health": snappedf(player_max_health, 0.1),
		"mana": snappedf(player_mana, 0.1),
		"max_mana": snappedf(player_max_mana, 0.1),
		"cooldowns": cooldowns,
	}

func _stat_value(key: String) -> float:
	var normalized = key.strip_edges().to_lower()
	var base = float(player_base_stats.get(normalized, 0.0))
	var bonus = float(player_bonus_stats.get(normalized, 0.0))
	return base + bonus

func _emit_combat_state() -> void:
	emit_signal("combat_state_changed", get_combat_snapshot())

func _spawn_level_content(level_payload: Dictionary) -> void:
	enemies.clear()
	pickups.clear()
	var rng = RandomNumberGenerator.new()
	rng.randomize()
	for rule in enemy_spawn_rules:
		if not (rule is Dictionary):
			continue
		var enemy_key = str(rule.get("enemy_key", "")).strip_edges().to_lower()
		if enemy_key.is_empty() or not enemy_catalog.has(enemy_key):
			continue
		var enemy_def = enemy_catalog.get(enemy_key, {})
		var count = maxi(0, int(rule.get("count", 0)))
		for _i in range(count):
			var ex = rng.randi_range(1, maxi(1, world_width_tiles - 2))
			var ey = rng.randi_range(1, maxi(1, world_height_tiles - 2))
			var spawn = Vector2(float(ex), float(ey))
			if _is_blocked(spawn):
				continue
			if player_tile_position.distance_to(spawn) < 3.0:
				continue
			enemies.append({
				"id": enemy_id_counter,
				"type": enemy_key,
				"label": str(enemy_def.get("label", enemy_key.capitalize())),
				"pos": spawn,
				"health": float(enemy_def.get("health", 30.0)),
				"max_health": float(enemy_def.get("health", 30.0)),
				"dead": false,
				"aggro_range": float(enemy_def.get("aggro_range", 5.0)),
				"attack_range": float(enemy_def.get("attack_range", 1.0)),
				"attack_damage": float(enemy_def.get("attack_damage", 4.0)),
				"attack_cooldown": float(enemy_def.get("attack_cooldown", 1.2)),
				"attack_timer": 0.0,
				"move_speed": float(enemy_def.get("move_speed", 2.0)),
				"loot": enemy_def.get("loot", []),
			})
			enemy_id_counter += 1

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), UI_TOKENS.color("panel_bg_deep"), true)
	var camera = _camera_screen_origin()
	var world_center = size * 0.5

	var drawables: Array = []
	for tile in floor_tiles:
		drawables.append({
			"pass": "floor",
			"tile": tile,
			"key": ISO.depth_key(0, 0, tile.y, tile.x, tile.y * 10000 + tile.x),
		})
	for prop in prop_tiles:
		var ptile = prop.get("tile", Vector2i.ZERO)
		var render_layer = int(prop.get("layer", 1))
		drawables.append({
			"pass": "prop",
			"tile": ptile,
			"asset_key": prop.get("asset_key", "prop"),
			"key": ISO.depth_key(0, render_layer, ptile.y, ptile.x, 100000 + ptile.y * 10000 + ptile.x),
		})

	for enemy in enemies:
		if bool(enemy.get("dead", false)):
			continue
		var enemy_tile: Vector2 = enemy.get("pos", Vector2.ZERO)
		var et = Vector2i(int(round(enemy_tile.x)), int(round(enemy_tile.y)))
		drawables.append({
			"pass": "enemy",
			"tile": et,
			"enemy": enemy,
			"key": ISO.depth_key(0, 4, et.y, et.x, 450000 + int(enemy.get("id", 0))),
		})

	for pickup in pickups:
		var ppos: Vector2 = pickup.get("pos", Vector2.ZERO)
		var pt = Vector2i(int(round(ppos.x)), int(round(ppos.y)))
		drawables.append({
			"pass": "pickup",
			"tile": pt,
			"pickup": pickup,
			"key": ISO.depth_key(0, 4, pt.y, pt.x, 430000 + int(pickup.get("id", 0))),
		})

	for npc in npcs:
		if not (npc is Dictionary):
			continue
		var nx = int(round(float(npc.get("x", npc.get("tile_x", 0)))))
		var ny = int(round(float(npc.get("y", npc.get("tile_y", 0)))))
		var nt = Vector2i(nx, ny)
		drawables.append({
			"pass": "npc",
			"tile": nt,
			"npc": npc,
			"key": ISO.depth_key(0, 4, nt.y, nt.x, 420000 + nx * 1024 + ny),
		})

	var actor_tile = Vector2i(int(round(player_tile_position.x)), int(round(player_tile_position.y)))
	drawables.append({
		"pass": "actor",
		"tile": actor_tile,
		"facing": player_facing,
		"key": ISO.depth_key(0, 5, actor_tile.y, actor_tile.x, 500000),
	})

	for fg in foreground_tiles:
		var ftile = fg.get("tile", Vector2i.ZERO)
		var frender_layer = int(fg.get("layer", 2))
		drawables.append({
			"pass": "foreground",
			"tile": ftile,
			"asset_key": fg.get("asset_key", "ambient"),
			"key": ISO.depth_key(0, frender_layer, ftile.y, ftile.x, 900000 + ftile.y * 10000 + ftile.x),
		})

	drawables.sort_custom(_sort_drawables)

	for drawable in drawables:
		var tile: Vector2i = drawable.get("tile", Vector2i.ZERO)
		var center = ISO.tile_center_screen(tile) - camera + world_center
		var pass_name = str(drawable.get("pass", "floor"))
		match pass_name:
			"floor":
				_draw_iso_diamond(center, UI_TOKENS.color("panel_bg_alt"), UI_TOKENS.color("panel_border_soft"), 1.0)
			"prop":
				_draw_prop(center, str(drawable.get("asset_key", "prop")))
			"enemy":
				_draw_enemy(center, drawable.get("enemy", {}))
			"pickup":
				_draw_pickup(center, drawable.get("pickup", {}))
			"npc":
				_draw_npc(center, drawable.get("npc", {}))
			"actor":
				_draw_actor(center, str(drawable.get("facing", "S")))
			"foreground":
				_draw_foreground(center, str(drawable.get("asset_key", "ambient")))

	_draw_hud_overlay()

func _sort_drawables(a: Dictionary, b: Dictionary) -> bool:
	var ka: Array = a.get("key", [])
	var kb: Array = b.get("key", [])
	return ka < kb

func _draw_iso_diamond(center: Vector2, fill: Color, outline: Color, line_width: float) -> void:
	var points = PackedVector2Array([
		center + Vector2(0.0, -ISO.HALF_TILE_HEIGHT),
		center + Vector2(ISO.HALF_TILE_WIDTH, 0.0),
		center + Vector2(0.0, ISO.HALF_TILE_HEIGHT),
		center + Vector2(-ISO.HALF_TILE_WIDTH, 0.0),
	])
	draw_colored_polygon(points, fill)
	var closed_points = PackedVector2Array(points)
	closed_points.append(points[0])
	draw_polyline(closed_points, outline, line_width, true)

func _draw_prop(center: Vector2, asset_key: String) -> void:
	var body_color = UI_TOKENS.color("panel_bg_highlight")
	if asset_key.contains("wall"):
		body_color = UI_TOKENS.color("panel_bg_soft")
	elif asset_key.contains("tree"):
		body_color = Color(0.20, 0.35, 0.22, 1.0)
	elif asset_key.contains("stairs") or asset_key.contains("ladder") or asset_key.contains("elevator"):
		body_color = UI_TOKENS.color("button_primary")
	var rect = Rect2(center + Vector2(-10.0, -44.0), Vector2(20.0, 44.0))
	draw_rect(rect, body_color, true)
	draw_rect(rect, UI_TOKENS.color("panel_border"), false, 1.0)

func _draw_enemy(center: Vector2, enemy: Dictionary) -> void:
	draw_circle(center + Vector2(0.0, -20.0), 12.0, Color(0.64, 0.22, 0.20, 1.0))
	var hp = maxf(0.0, float(enemy.get("health", 0.0)))
	var max_hp = maxf(1.0, float(enemy.get("max_health", 1.0)))
	var pct = clampf(hp / max_hp, 0.0, 1.0)
	var bar_rect = Rect2(center + Vector2(-14.0, -42.0), Vector2(28.0, 4.0))
	draw_rect(bar_rect, Color(0.15, 0.08, 0.08, 1.0), true)
	draw_rect(Rect2(bar_rect.position, Vector2(bar_rect.size.x * pct, bar_rect.size.y)), Color(0.90, 0.32, 0.28, 1.0), true)
	draw_rect(bar_rect, UI_TOKENS.color("panel_border_soft"), false, 1.0)

func _draw_pickup(center: Vector2, pickup: Dictionary) -> void:
	var points = PackedVector2Array([
		center + Vector2(0.0, -18.0),
		center + Vector2(8.0, -10.0),
		center + Vector2(0.0, -2.0),
		center + Vector2(-8.0, -10.0),
	])
	draw_colored_polygon(points, Color(0.88, 0.73, 0.34, 0.95))
	var outline = PackedVector2Array(points)
	outline.append(points[0])
	draw_polyline(outline, UI_TOKENS.color("panel_border"), 1.0, true)
	var item_key = str(pickup.get("item_key", ""))
	if not item_key.is_empty():
		draw_string(get_theme_default_font(), center + Vector2(-22.0, 12.0), item_key, HORIZONTAL_ALIGNMENT_LEFT, 64.0, 10, UI_TOKENS.color("text_secondary"))

func _draw_npc(center: Vector2, npc: Dictionary) -> void:
	var rect = Rect2(center + Vector2(-10.0, -30.0), Vector2(20.0, 30.0))
	draw_rect(rect, Color(0.30, 0.42, 0.64, 1.0), true)
	draw_rect(rect, UI_TOKENS.color("panel_border"), false, 1.0)
	var label = str(npc.get("label", npc.get("key", "NPC")))
	draw_string(get_theme_default_font(), center + Vector2(-28.0, -36.0), label, HORIZONTAL_ALIGNMENT_LEFT, 120.0, 11, UI_TOKENS.color("text_secondary"))

func _draw_actor(center: Vector2, facing: String) -> void:
	var body_rect = Rect2(center + Vector2(-8.0, -30.0), Vector2(16.0, 26.0))
	draw_rect(body_rect, UI_TOKENS.color("button_primary"), true)
	draw_rect(body_rect, UI_TOKENS.color("panel_bg_deep"), false, 1.0)
	draw_circle(center + Vector2(0.0, -36.0), 7.0, UI_TOKENS.color("panel_border"))
	draw_string(get_theme_default_font(), center + Vector2(-10.0, 14.0), facing, HORIZONTAL_ALIGNMENT_LEFT, 24.0, 12, UI_TOKENS.color("text_primary"))

func _draw_foreground(center: Vector2, asset_key: String) -> void:
	var alpha = 0.26
	if asset_key.contains("cloud"):
		alpha = 0.34
	var rect = Rect2(center + Vector2(-28.0, -84.0), Vector2(56.0, 20.0))
	draw_rect(rect, Color(0.82, 0.86, 0.90, alpha), true)

func _draw_hud_overlay() -> void:
	var font = get_theme_default_font()
	var hud_line = "HP %d/%d | MP %d/%d | Enemies %d | Pickups %d" % [
		int(round(player_health)),
		int(round(player_max_health)),
		int(round(player_mana)),
		int(round(player_max_mana)),
		_alive_enemy_count(),
		pickups.size(),
	]
	draw_string(font, Vector2(14.0, 24.0), hud_line, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 14, UI_TOKENS.color("text_primary"))
	var ability_line = "Atk[Space] %.1fs | Ember[1] %.1fs | Cleave[2] %.1fs | Quick[3] %.1fs | Bandage[4] %.1fs" % [
		float(ability_cooldowns.get("basic_attack", 0.0)),
		float(ability_cooldowns.get("ember", 0.0)),
		float(ability_cooldowns.get("cleave", 0.0)),
		float(ability_cooldowns.get("quick_strike", 0.0)),
		float(ability_cooldowns.get("bandage", 0.0)),
	]
	draw_string(font, Vector2(14.0, 42.0), ability_line, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 12, UI_TOKENS.color("text_secondary"))

func _alive_enemy_count() -> int:
	var count = 0
	for enemy in enemies:
		if not bool(enemy.get("dead", false)):
			count += 1
	return count

func _camera_screen_origin() -> Vector2:
	var player_screen_world = ISO.world_to_screen(player_tile_position)
	return player_screen_world - size * 0.5

func _clamp_tile_position(value: Vector2) -> Vector2:
	var min_x = 0.5
	var min_y = 0.5
	var max_x = maxf(min_x, float(world_width_tiles) - 0.5)
	var max_y = maxf(min_y, float(world_height_tiles) - 0.5)
	return Vector2(
		clampf(value.x, min_x, max_x),
		clampf(value.y, min_y, max_y)
	)

func _tile_to_world_pixels(tile_pos: Vector2) -> Vector2:
	return tile_pos * GRID_UNIT_PIXELS

func _world_pixels_to_tile(world_pixels: Vector2) -> Vector2:
	return Vector2(world_pixels.x / GRID_UNIT_PIXELS, world_pixels.y / GRID_UNIT_PIXELS)

func _is_blocked(tile_pos: Vector2) -> bool:
	var key = "%d:%d" % [int(floor(tile_pos.x)), int(floor(tile_pos.y))]
	if blocked_tiles.has(key):
		var layers = blocked_tiles.get(key, [])
		if layers is Array:
			for layer in layers:
				if str(layer).strip_edges().to_lower() == player_collision_layer:
					return true
		else:
			return true
	for enemy in enemies:
		if bool(enemy.get("dead", false)):
			continue
		var epos = enemy.get("pos", Vector2.ZERO)
		if tile_pos.distance_to(epos) <= 0.45:
			return true
	return false

func _collision_layers_for_asset(asset_key: String, entry: Dictionary) -> Array[String]:
	var template: Dictionary = {}
	if entry.has("collision_template") and entry.get("collision_template") is Dictionary:
		template = entry.get("collision_template")
	elif asset_templates.has(asset_key) and asset_templates.get(asset_key) is Dictionary:
		template = (asset_templates.get(asset_key) as Dictionary).get("collision_template", {})
	if template is Dictionary:
		var raw_layers = template.get("layers", [])
		if raw_layers is Array and not raw_layers.is_empty():
			var normalized: Array[String] = []
			for value in raw_layers:
				var layer = str(value).strip_edges().to_lower()
				if not layer.is_empty():
					normalized.append(layer)
			if not normalized.is_empty():
				return normalized
	var fallback: Array[String] = []
	fallback.append("ground")
	return fallback

func _check_transition_trigger() -> void:
	if _transition_cooldown > 0.0 or transitions.is_empty():
		return
	var tx = int(round(player_tile_position.x))
	var ty = int(round(player_tile_position.y))
	for transition in transitions:
		if not (transition is Dictionary):
			continue
		if int(transition.get("x", -1)) == tx and int(transition.get("y", -1)) == ty:
			_transition_cooldown = 0.42
			emit_signal("transition_requested", transition)
			return

func _build_default_floor() -> void:
	floor_tiles.clear()
	for y in range(world_height_tiles):
		for x in range(world_width_tiles):
			floor_tiles.append(Vector2i(x, y))

func _ingest_level_layers(level_payload: Dictionary) -> void:
	prop_tiles.clear()
	foreground_tiles.clear()
	blocked_tiles.clear()
	if level_payload.is_empty():
		return
	var layers: Dictionary = {}
	var raw_layers = level_payload.get("layers", level_payload.get("layers_json", {}))
	if raw_layers is Dictionary:
		layers = raw_layers
	elif raw_layers is String:
		var parsed = JSON.parse_string(raw_layers)
		if parsed is Dictionary:
			layers = parsed
	for key in layers.keys():
		var layer_index = int(str(key))
		var entries = layers.get(key, [])
		if not (entries is Array):
			continue
		for entry in entries:
			if not (entry is Dictionary):
				continue
			var tx = int(entry.get("x", entry.get("tile_x", -1)))
			var ty = int(entry.get("y", entry.get("tile_y", -1)))
			if tx < 0 or ty < 0:
				continue
			var tile = Vector2i(tx, ty)
			var asset_key = str(entry.get("asset_key", entry.get("key", "tile"))).strip_edges().to_lower()
			if layer_index <= 0:
				continue
			if layer_index == 1:
				prop_tiles.append({"tile": tile, "layer": layer_index, "asset_key": asset_key})
				var is_collidable = bool(entry.get("collidable", false)) or asset_key.contains("wall") or asset_key.contains("tree")
				if asset_templates.has(asset_key):
					var catalog_entry = asset_templates.get(asset_key)
					if catalog_entry is Dictionary:
						is_collidable = bool(catalog_entry.get("collidable", is_collidable))
				if is_collidable:
					blocked_tiles["%d:%d" % [tx, ty]] = _collision_layers_for_asset(asset_key, entry)
			else:
				foreground_tiles.append({"tile": tile, "layer": layer_index, "asset_key": asset_key})
