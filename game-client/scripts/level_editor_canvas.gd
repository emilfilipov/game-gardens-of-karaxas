extends Control

signal layers_changed(layers: Dictionary)
signal status_changed(message: String)

const UI_TOKENS = preload("res://scripts/ui_tokens.gd")

var grid_width: int = 80
var grid_height: int = 48
var cell_size: float = 18.0
var layers_data: Dictionary = {"0": [], "1": [], "2": []}
var active_layer: int = 1
var brush_asset: String = "wall_block"
var brush_mode: String = "place"
var show_grid: bool = true
var show_collision: bool = true

func _ready() -> void:
	focus_mode = Control.FOCUS_ALL
	mouse_filter = Control.MOUSE_FILTER_STOP

func configure_level(width_tiles: int, height_tiles: int, layers: Dictionary) -> void:
	grid_width = maxi(4, width_tiles)
	grid_height = maxi(4, height_tiles)
	if layers is Dictionary:
		layers_data = _normalized_layers(layers)
	else:
		layers_data = {"0": [], "1": [], "2": []}
	queue_redraw()

func set_active_layer(layer_index: int) -> void:
	active_layer = clampi(layer_index, 0, 2)
	queue_redraw()

func set_brush_asset(asset_key: String) -> void:
	brush_asset = asset_key.strip_edges().to_lower()
	if brush_asset.is_empty():
		brush_asset = "wall_block"

func set_brush_mode(mode: String) -> void:
	var normalized = mode.strip_edges().to_lower()
	if normalized in ["place", "erase", "select"]:
		brush_mode = normalized
	else:
		brush_mode = "place"

func set_overlays(grid_enabled: bool, collision_enabled: bool) -> void:
	show_grid = grid_enabled
	show_collision = collision_enabled
	queue_redraw()

func get_layers_data() -> Dictionary:
	return _normalized_layers(layers_data)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mouse_event = event as InputEventMouseButton
		if not mouse_event.pressed:
			return
		if mouse_event.button_index != MOUSE_BUTTON_LEFT and mouse_event.button_index != MOUSE_BUTTON_RIGHT:
			return
		var tile = _mouse_to_tile(mouse_event.position)
		if tile.x < 0 or tile.y < 0:
			return
		if brush_mode == "select":
			emit_signal("status_changed", "Tile %d,%d selected." % [tile.x, tile.y])
			return
		if mouse_event.button_index == MOUSE_BUTTON_RIGHT:
			_erase_tile(tile)
		else:
			if brush_mode == "erase":
				_erase_tile(tile)
			else:
				_place_tile(tile)
		queue_redraw()
		emit_signal("layers_changed", get_layers_data())

func _place_tile(tile: Vector2i) -> void:
	var key = str(active_layer)
	var list = layers_data.get(key, [])
	if not (list is Array):
		list = []
	for i in range(list.size()):
		var entry = list[i]
		if not (entry is Dictionary):
			continue
		if int(entry.get("x", -1)) == tile.x and int(entry.get("y", -1)) == tile.y:
			entry["asset_key"] = brush_asset
			list[i] = entry
			layers_data[key] = list
			return
	list.append({"x": tile.x, "y": tile.y, "asset_key": brush_asset})
	layers_data[key] = list

func _erase_tile(tile: Vector2i) -> void:
	for layer_key in ["0", "1", "2"]:
		if str(layer_key) != str(active_layer) and brush_mode != "erase":
			continue
		var list = layers_data.get(layer_key, [])
		if not (list is Array):
			continue
		var updated: Array = []
		for entry in list:
			if not (entry is Dictionary):
				continue
			if int(entry.get("x", -1)) == tile.x and int(entry.get("y", -1)) == tile.y:
				continue
			updated.append(entry)
		layers_data[layer_key] = updated

func _mouse_to_tile(local_pos: Vector2) -> Vector2i:
	var ox = 10.0
	var oy = 10.0
	var tx = int(floor((local_pos.x - ox) / cell_size))
	var ty = int(floor((local_pos.y - oy) / cell_size))
	if tx < 0 or ty < 0 or tx >= grid_width or ty >= grid_height:
		return Vector2i(-1, -1)
	return Vector2i(tx, ty)

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), UI_TOKENS.color("panel_bg_deep"), true)
	var ox = 10.0
	var oy = 10.0
	var canvas_w = minf(size.x - 20.0, float(grid_width) * cell_size)
	var canvas_h = minf(size.y - 20.0, float(grid_height) * cell_size)
	var canvas_rect = Rect2(Vector2(ox, oy), Vector2(canvas_w, canvas_h))
	draw_rect(canvas_rect, UI_TOKENS.color("panel_bg"), true)
	draw_rect(canvas_rect, UI_TOKENS.color("panel_border"), false, 1.0)

	if show_grid:
		for gx in range(grid_width + 1):
			var x = ox + float(gx) * cell_size
			if x > ox + canvas_w:
				break
			draw_line(Vector2(x, oy), Vector2(x, oy + canvas_h), UI_TOKENS.color("panel_border_soft"), 1.0)
		for gy in range(grid_height + 1):
			var y = oy + float(gy) * cell_size
			if y > oy + canvas_h:
				break
			draw_line(Vector2(ox, y), Vector2(ox + canvas_w, y), UI_TOKENS.color("panel_border_soft"), 1.0)

	for layer_key in ["0", "1", "2"]:
		var list = layers_data.get(layer_key, [])
		if not (list is Array):
			continue
		for entry in list:
			if not (entry is Dictionary):
				continue
			var tx = int(entry.get("x", -1))
			var ty = int(entry.get("y", -1))
			if tx < 0 or ty < 0:
				continue
			var px = ox + float(tx) * cell_size
			var py = oy + float(ty) * cell_size
			var rect = Rect2(Vector2(px + 1.0, py + 1.0), Vector2(cell_size - 2.0, cell_size - 2.0))
			var tint = _layer_tint(int(str(layer_key).to_int()))
			draw_rect(rect, tint, true)
			if show_collision and str(entry.get("asset_key", "")).contains("wall"):
				draw_rect(rect.grow(-4.0), Color(0.90, 0.30, 0.30, 0.85), false, 1.0)

	var status = "Layer %d | Mode %s | Brush %s" % [active_layer, brush_mode.capitalize(), brush_asset]
	draw_string(get_theme_default_font(), Vector2(12.0, size.y - 8.0), status, HORIZONTAL_ALIGNMENT_LEFT, -1.0, 12, UI_TOKENS.color("text_secondary"))

func _layer_tint(layer_index: int) -> Color:
	match layer_index:
		0:
			return Color(0.26, 0.42, 0.25, 0.92)
		1:
			return Color(0.58, 0.36, 0.24, 0.92)
		2:
			return Color(0.45, 0.55, 0.74, 0.92)
		_:
			return Color(0.40, 0.40, 0.40, 0.92)

func _normalized_layers(raw_layers: Dictionary) -> Dictionary:
	var normalized = {"0": [], "1": [], "2": []}
	for layer_key in normalized.keys():
		var raw_list = raw_layers.get(layer_key, [])
		if not (raw_list is Array):
			continue
		for raw_entry in raw_list:
			if not (raw_entry is Dictionary):
				continue
			normalized[layer_key].append({
				"x": int(raw_entry.get("x", -1)),
				"y": int(raw_entry.get("y", -1)),
				"asset_key": str(raw_entry.get("asset_key", "tile")).strip_edges().to_lower(),
			})
	return normalized
