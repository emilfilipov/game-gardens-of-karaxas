extends SubViewportContainer

signal player_position_changed(position: Vector2)
signal transition_requested(transition: Dictionary)
signal combat_state_changed(state: Dictionary)
signal loot_dropped(item: Dictionary)
signal quest_event(event: Dictionary)
signal npc_interacted(npc: Dictionary)

const SELLSWORD_FACTORY = preload("res://scripts/sellsword_3d_factory.gd")
const GROUND_TILE_SCENE = preload("res://scenes/environment/ground_tile_stone_3d.tscn")
const FOLIAGE_GRASS_SCENE = preload("res://scenes/environment/foliage_grass_a_3d.tscn")
const FOLIAGE_TREE_SCENE = preload("res://scenes/environment/foliage_tree_dead_3d.tscn")

const GRID_UNIT_PIXELS: float = 32.0
const DEFAULT_PLAYER_SPEED_UNITS: float = 4.2

const CAMERA_HEIGHT: float = 18.5
const CAMERA_DISTANCE: float = 17.0
const CAMERA_PITCH_DEG: float = -52.0
const CAMERA_YAW_DEG: float = -45.0
const CAMERA_FOLLOW_SMOOTH: float = 6.0

var world_width_tiles: int = 80
var world_height_tiles: int = 48
var world_name: String = "Default"
var player_speed_units: float = DEFAULT_PLAYER_SPEED_UNITS
var _active: bool = false

var _viewport: SubViewport
var _world_root: Node3D
var _terrain_root: Node3D
var _foliage_root: Node3D
var _camera_rig: Node3D
var _camera_pivot: Node3D
var _camera: Camera3D
var _player_root: Node3D
var _player_model: Node3D

var _player_position: Vector3 = Vector3(2.0, 0.0, 2.0)
var _target_camera_position: Vector3 = Vector3.ZERO
var _player_appearance_key: String = "human_male"

func _ready() -> void:
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_PASS
	_build_scene()
	set_process(false)

func _build_scene() -> void:
	_viewport = SubViewport.new()
	_viewport.disable_3d = false
	_viewport.usage = SubViewport.USAGE_3D
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_viewport)

	_world_root = Node3D.new()
	_world_root.name = "World3D"
	_viewport.add_child(_world_root)

	var env = WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.05, 0.06, 0.08)
	environment.ambient_light_color = Color(0.56, 0.57, 0.58)
	environment.ambient_light_energy = 0.8
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.environment = environment
	_world_root.add_child(env)

	var sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, 30.0, 0.0)
	sun.light_color = Color(1.0, 0.95, 0.83)
	sun.light_energy = 1.6
	sun.shadow_enabled = true
	_world_root.add_child(sun)

	var fill = OmniLight3D.new()
	fill.position = Vector3(-6.0, 4.0, -6.0)
	fill.light_color = Color(0.44, 0.50, 0.62)
	fill.light_energy = 0.35
	fill.omni_range = 18.0
	_world_root.add_child(fill)

	_terrain_root = Node3D.new()
	_terrain_root.name = "Terrain"
	_world_root.add_child(_terrain_root)

	_foliage_root = Node3D.new()
	_foliage_root.name = "Foliage"
	_world_root.add_child(_foliage_root)

	_player_root = Node3D.new()
	_player_root.name = "PlayerRoot"
	_world_root.add_child(_player_root)

	_camera_rig = Node3D.new()
	_camera_rig.name = "CameraRig"
	_world_root.add_child(_camera_rig)

	_camera_pivot = Node3D.new()
	_camera_pivot.name = "CameraPivot"
	_camera_pivot.rotation_degrees = Vector3(CAMERA_PITCH_DEG, CAMERA_YAW_DEG, 0.0)
	_camera_rig.add_child(_camera_pivot)

	_camera = Camera3D.new()
	_camera.current = true
	_camera.fov = 50.0
	_camera.near = 0.05
	_camera.far = 320.0
	_camera.position = Vector3(0.0, CAMERA_HEIGHT, CAMERA_DISTANCE)
	_camera_pivot.add_child(_camera)

	_rebuild_ground_and_foliage()
	_set_player_model(_player_appearance_key)
	_update_player_transform(true)

	resized.connect(_on_resized)
	_on_resized()

func _on_resized() -> void:
	if _viewport == null:
		return
	_viewport.size = Vector2i(maxi(1, int(size.x)), maxi(1, int(size.y)))

func _set_player_model(appearance_key: String) -> void:
	_player_appearance_key = appearance_key.strip_edges().to_lower()
	if _player_appearance_key.is_empty():
		_player_appearance_key = "human_male"
	if _player_model != null:
		_player_model.queue_free()
		_player_model = null
	_player_model = SELLSWORD_FACTORY.create_model(_player_appearance_key)
	_player_root.add_child(_player_model)

func _rebuild_ground_and_foliage() -> void:
	for child in _terrain_root.get_children():
		child.queue_free()
	for child in _foliage_root.get_children():
		child.queue_free()

	var ground = SELLSWORD_FACTORY.build_ground(maxf(8.0, float(max(world_width_tiles, world_height_tiles)) * 0.8))
	_terrain_root.add_child(ground)

	# Starter foliage kit: deterministic sparse tufts for quick 3D level blockout.
	var span_x = max(6, mini(22, world_width_tiles / 4))
	var span_z = max(6, mini(22, world_height_tiles / 4))
	for x in range(-span_x, span_x + 1, 3):
		for z in range(-span_z, span_z + 1, 3):
			if (abs(x) + abs(z)) % 4 != 0:
				continue
			var tuft = SELLSWORD_FACTORY.build_grass_tuft((x + span_x) * 31 + z + span_z)
			tuft.position = Vector3(float(x) * 0.65, 0.0, float(z) * 0.65)
			_foliage_root.add_child(tuft)

func _spawn_level_objects(objects: Array) -> void:
	for object_row in objects:
		if not (object_row is Dictionary):
			continue
		var asset_key = str(object_row.get("asset_key", "")).strip_edges().to_lower()
		if asset_key == "spawn_marker":
			continue
		var source_scene: PackedScene = null
		match asset_key:
			"ground_stone_a":
				source_scene = GROUND_TILE_SCENE
			"foliage_grass_a":
				source_scene = FOLIAGE_GRASS_SCENE
			"foliage_tree_dead_a":
				source_scene = FOLIAGE_TREE_SCENE
			_:
				continue
		var instance = source_scene.instantiate()
		if not (instance is Node3D):
			if instance != null:
				instance.queue_free()
			continue
		var transform = object_row.get("transform", {})
		var target = instance as Node3D
		if transform is Dictionary:
			target.position = Vector3(
				float(transform.get("x", 0.0)),
				float(transform.get("z", 0.0)),
				float(transform.get("y", 0.0))
			)
			target.rotation_degrees = Vector3(0.0, float(transform.get("rotation_deg", 0.0)), 0.0)
			target.scale = Vector3(
				float(transform.get("scale_x", 1.0)),
				1.0,
				float(transform.get("scale_y", 1.0))
			)
		if asset_key.begins_with("ground_"):
			_terrain_root.add_child(target)
		else:
			_foliage_root.add_child(target)

func configure_world(level_name: String, width_tiles: int, height_tiles: int, spawn_world: Vector2, level_payload: Dictionary = {}) -> void:
	world_name = level_name
	world_width_tiles = maxi(width_tiles, 8)
	world_height_tiles = maxi(height_tiles, 8)
	_player_position = Vector3(spawn_world.x / GRID_UNIT_PIXELS, 0.0, spawn_world.y / GRID_UNIT_PIXELS)
	_rebuild_ground_and_foliage()

	if level_payload.has("objects") and level_payload.get("objects") is Array:
		var objects: Array = level_payload.get("objects", [])
		for object_row in objects:
			if not (object_row is Dictionary):
				continue
			if str(object_row.get("object_id", "")) != "spawn_marker_3d":
				continue
			var transform = object_row.get("transform", {})
			if transform is Dictionary:
				_player_position = Vector3(float(transform.get("x", _player_position.x)), float(transform.get("z", 0.0)), float(transform.get("y", _player_position.z)))
				break
		_spawn_level_objects(objects)

	_update_player_transform(true)

func configure_runtime(runtime_cfg: Dictionary) -> void:
	if not (runtime_cfg is Dictionary):
		return
	var movement_cfg: Dictionary = runtime_cfg.get("movement", {}) if runtime_cfg.has("movement") else runtime_cfg
	player_speed_units = maxf(1.0, float(movement_cfg.get("player_speed_tiles", DEFAULT_PLAYER_SPEED_UNITS)))

func set_player_appearance(appearance_key: String) -> void:
	_set_player_model(appearance_key)
	_update_player_transform(true)

func set_world_position(world_position: Vector2) -> void:
	_player_position = Vector3(world_position.x / GRID_UNIT_PIXELS, _player_position.y, world_position.y / GRID_UNIT_PIXELS)
	_update_player_transform(true)

func get_world_position() -> Vector2:
	return Vector2(_player_position.x * GRID_UNIT_PIXELS, _player_position.z * GRID_UNIT_PIXELS)

func set_active(active: bool) -> void:
	_active = active
	set_process(active)
	if active:
		grab_focus()

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

func _axis_to_direction(axis: Vector2) -> String:
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
	return "S"

func _process(delta: float) -> void:
	if not _active:
		return

	var axis = _movement_axis()
	var moved = false
	if axis != Vector2.ZERO:
		moved = true
		var dir = axis.normalized()
		_player_position.x = clampf(_player_position.x + dir.x * player_speed_units * delta, 0.0, float(world_width_tiles))
		_player_position.z = clampf(_player_position.z + dir.y * player_speed_units * delta, 0.0, float(world_height_tiles))
		if _player_model != null:
			_player_model.rotation_degrees.y = SELLSWORD_FACTORY.direction_to_rotation_y(_axis_to_direction(axis))
		_update_player_transform(false)
		emit_signal("player_position_changed", get_world_position())

	# Keep camera anchored behind the player using fixed ARPG cinematic angle.
	_target_camera_position = Vector3(_player_position.x, 0.0, _player_position.z)
	_camera_rig.position = _camera_rig.position.lerp(_target_camera_position, clampf(delta * CAMERA_FOLLOW_SMOOTH, 0.0, 1.0))

	if moved:
		emit_signal("combat_state_changed", {
			"player_position": get_world_position(),
			"mode": "moving",
			"world_name": world_name,
		})

func _update_player_transform(force_camera_snap: bool) -> void:
	_player_root.position = _player_position
	if force_camera_snap:
		_target_camera_position = Vector3(_player_position.x, 0.0, _player_position.z)
		_camera_rig.position = _target_camera_position
