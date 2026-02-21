extends Control

signal player_position_changed(position: Vector2)

const TILE_SIZE := 32.0
const PLAYER_RADIUS := 14.0
const PLAYER_SPEED := 220.0

var world_width_px: float = 1600.0
var world_height_px: float = 1000.0
var player_position_world: Vector2 = Vector2(96.0, 96.0)
var world_name: String = "Default"
var _active: bool = false

func configure_world(level_name: String, width_tiles: int, height_tiles: int, spawn_world: Vector2) -> void:
	world_name = level_name
	world_width_px = max(float(width_tiles) * TILE_SIZE, 320.0)
	world_height_px = max(float(height_tiles) * TILE_SIZE, 320.0)
	player_position_world = _clamp_world_position(spawn_world)
	queue_redraw()

func set_world_position(world_position: Vector2) -> void:
	player_position_world = _clamp_world_position(world_position)
	queue_redraw()

func get_world_position() -> Vector2:
	return player_position_world

func set_active(active: bool) -> void:
	_active = active
	set_process(active)
	if active:
		grab_focus()

func _ready() -> void:
	focus_mode = Control.FOCUS_ALL
	set_process(false)

func _process(delta: float) -> void:
	if not _active:
		return
	var axis: Vector2 = Vector2.ZERO
	if Input.is_key_pressed(KEY_A):
		axis.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		axis.x += 1.0
	if Input.is_key_pressed(KEY_W):
		axis.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		axis.y += 1.0
	if axis == Vector2.ZERO:
		return
	var next_pos: Vector2 = player_position_world + axis.normalized() * PLAYER_SPEED * delta
	var clamped_position: Vector2 = _clamp_world_position(next_pos)
	if clamped_position != player_position_world:
		player_position_world = clamped_position
		emit_signal("player_position_changed", player_position_world)
		queue_redraw()

func _draw() -> void:
	var viewport_rect: Rect2 = Rect2(Vector2.ZERO, size)
	draw_rect(viewport_rect, Color(0.11, 0.15, 0.12, 1.0), true)

	var camera: Vector2 = _camera_origin()
	var world_rect: Rect2 = Rect2(-camera, Vector2(world_width_px, world_height_px))
	draw_rect(world_rect, Color(0.20, 0.27, 0.22, 1.0), true)

	var step: int = int(TILE_SIZE)
	var x: int = 0
	while x <= int(world_width_px):
		var sx: float = float(x) - camera.x
		draw_line(Vector2(sx, -camera.y), Vector2(sx, world_height_px - camera.y), Color(0.26, 0.33, 0.28, 0.55), 1.0)
		x += step
	var y: int = 0
	while y <= int(world_height_px):
		var sy: float = float(y) - camera.y
		draw_line(Vector2(-camera.x, sy), Vector2(world_width_px - camera.x, sy), Color(0.26, 0.33, 0.28, 0.55), 1.0)
		y += step
	draw_rect(world_rect, Color(0.72, 0.58, 0.39, 1.0), false, 2.0)

	var player_screen: Vector2 = player_position_world - camera
	draw_circle(player_screen, PLAYER_RADIUS, Color(0.94, 0.83, 0.63, 1.0))
	draw_circle(player_screen + Vector2(0.0, PLAYER_RADIUS + 4.0), 3.0, Color(0.81, 0.63, 0.42, 1.0))

func _camera_origin() -> Vector2:
	var camera: Vector2 = player_position_world - size / 2.0
	camera.x = clampf(camera.x, 0.0, maxf(0.0, world_width_px - size.x))
	camera.y = clampf(camera.y, 0.0, maxf(0.0, world_height_px - size.y))
	return camera

func _clamp_world_position(value: Vector2) -> Vector2:
	var min_x: float = PLAYER_RADIUS
	var min_y: float = PLAYER_RADIUS
	var max_x: float = maxf(min_x, world_width_px - PLAYER_RADIUS)
	var max_y: float = maxf(min_y, world_height_px - PLAYER_RADIUS)
	return Vector2(
		clampf(value.x, min_x, max_x),
		clampf(value.y, min_y, max_y)
	)
