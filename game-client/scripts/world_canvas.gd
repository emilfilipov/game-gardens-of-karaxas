extends Control

signal player_position_changed(position: Vector2)

const ISO = preload("res://scripts/iso_projection.gd")
const UI_TOKENS = preload("res://scripts/ui_tokens.gd")

const GRID_UNIT_PIXELS: float = 32.0
const PLAYER_SPEED_TILES: float = 4.6
const PLAYER_RADIUS: float = 14.0

var world_width_tiles: int = 80
var world_height_tiles: int = 48
var player_tile_position: Vector2 = Vector2(3.0, 3.0)
var player_facing: String = "S"
var world_name: String = "Default"
var _active: bool = false

var floor_tiles: Array[Vector2i] = []
var prop_tiles: Array[Dictionary] = []
var foreground_tiles: Array[Dictionary] = []
var blocked_tiles: Dictionary = {}
var show_sort_diagnostics: bool = false

func configure_world(level_name: String, width_tiles: int, height_tiles: int, spawn_world: Vector2, level_payload: Dictionary = {}) -> void:
	world_name = level_name
	world_width_tiles = maxi(width_tiles, 6)
	world_height_tiles = maxi(height_tiles, 6)
	player_tile_position = _clamp_tile_position(_world_pixels_to_tile(spawn_world))
	_build_default_floor()
	_ingest_level_layers(level_payload)
	queue_redraw()

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
	var axis: Vector2 = _movement_axis()
	if axis == Vector2.ZERO:
		return
	var next_pos: Vector2 = _clamp_tile_position(player_tile_position + axis.normalized() * PLAYER_SPEED_TILES * delta)
	if _is_blocked(next_pos):
		return
	player_tile_position = next_pos
	player_facing = _axis_to_facing(axis)
	emit_signal("player_position_changed", _tile_to_world_pixels(player_tile_position))
	queue_redraw()

func _movement_axis() -> Vector2:
	var axis = Vector2.ZERO
	if Input.is_key_pressed(KEY_W):
		axis += Vector2(-1.0, -1.0)
	if Input.is_key_pressed(KEY_S):
		axis += Vector2(1.0, 1.0)
	if Input.is_key_pressed(KEY_A):
		axis += Vector2(-1.0, 1.0)
	if Input.is_key_pressed(KEY_D):
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
		var tile = prop.get("tile", Vector2i.ZERO)
		var render_layer = int(prop.get("layer", 1))
		drawables.append({
			"pass": "prop",
			"tile": tile,
			"asset_key": prop.get("asset_key", "prop"),
			"key": ISO.depth_key(0, render_layer, tile.y, tile.x, 100000 + tile.y * 10000 + tile.x),
		})

	var actor_tile = Vector2i(int(round(player_tile_position.x)), int(round(player_tile_position.y)))
	drawables.append({
		"pass": "actor",
		"tile": actor_tile,
		"facing": player_facing,
		"key": ISO.depth_key(0, 5, actor_tile.y, actor_tile.x, 500000),
	})

	for fg in foreground_tiles:
		var tile = fg.get("tile", Vector2i.ZERO)
		var render_layer = int(fg.get("layer", 2))
		drawables.append({
			"pass": "foreground",
			"tile": tile,
			"asset_key": fg.get("asset_key", "ambient"),
			"key": ISO.depth_key(0, render_layer, tile.y, tile.x, 900000 + tile.y * 10000 + tile.x),
		})

	drawables.sort_custom(_sort_drawables)

	var previous_key: Array = []
	var duplicate_depth_keys: int = 0
	for drawable in drawables:
		var key: Array = drawable.get("key", [])
		if not previous_key.is_empty() and key == previous_key:
			duplicate_depth_keys += 1
		previous_key = key
		var tile: Vector2i = drawable.get("tile", Vector2i.ZERO)
		var center = ISO.tile_center_screen(tile) - camera + world_center
		var pass_name = str(drawable.get("pass", "floor"))
		match pass_name:
			"floor":
				_draw_iso_diamond(center, UI_TOKENS.color("panel_bg_alt"), UI_TOKENS.color("panel_border_soft"), 1.0)
			"prop":
				_draw_prop(center, str(drawable.get("asset_key", "prop")))
			"actor":
				_draw_actor(center, str(drawable.get("facing", "S")))
			"foreground":
				_draw_foreground(center, str(drawable.get("asset_key", "ambient")))

	if show_sort_diagnostics:
		var debug_text = "Iso Sort | drawables=%d | duplicateDepthKeys=%d | facing=%s" % [drawables.size(), duplicate_depth_keys, player_facing]
		draw_string(get_theme_default_font(), Vector2(16, 26), debug_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, UI_TOKENS.color("text_secondary"))

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

func _draw_actor(center: Vector2, facing: String) -> void:
	var body_rect = Rect2(center + Vector2(-8.0, -30.0), Vector2(16.0, 26.0))
	draw_rect(body_rect, UI_TOKENS.color("button_primary"), true)
	draw_rect(body_rect, UI_TOKENS.color("panel_bg_deep"), false, 1.0)
	draw_circle(center + Vector2(0.0, -36.0), 7.0, UI_TOKENS.color("panel_border"))
	var facing_label = facing
	draw_string(
		get_theme_default_font(),
		center + Vector2(-10.0, 14.0),
		facing_label,
		HORIZONTAL_ALIGNMENT_LEFT,
		24.0,
		12,
		UI_TOKENS.color("text_primary")
	)

func _draw_foreground(center: Vector2, asset_key: String) -> void:
	var alpha = 0.26
	if asset_key.contains("cloud"):
		alpha = 0.34
	var rect = Rect2(center + Vector2(-28.0, -84.0), Vector2(56.0, 20.0))
	draw_rect(rect, Color(0.82, 0.86, 0.90, alpha), true)

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
	return blocked_tiles.has(key)

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
				if asset_key.contains("wall") or asset_key.contains("tree") or bool(entry.get("collidable", false)):
					blocked_tiles["%d:%d" % [tx, ty]] = true
			else:
				foreground_tiles.append({"tile": tile, "layer": layer_index, "asset_key": asset_key})
