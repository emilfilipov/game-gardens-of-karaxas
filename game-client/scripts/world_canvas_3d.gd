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
const DEFAULT_PLAYER_RUN_SPEED_UNITS: float = 6.0

const CAMERA_HEIGHT: float = 18.8
const CAMERA_DISTANCE: float = 17.2
const CAMERA_PITCH_DEG: float = -52.0
const CAMERA_YAW_DEG: float = -45.0
const CAMERA_FOLLOW_SMOOTH: float = 6.0
const CAMERA_LOOK_AHEAD: float = 1.45
const DEFAULT_CAMERA_PROFILE_KEY: String = "arpg_poe_baseline"

var world_width_tiles: int = 80
var world_height_tiles: int = 48
var world_name: String = "Default"
var player_speed_units: float = DEFAULT_PLAYER_SPEED_UNITS
var player_run_speed_units: float = DEFAULT_PLAYER_RUN_SPEED_UNITS
var _active: bool = false

var keybinds: Dictionary = {
	"move_up": KEY_W,
	"move_down": KEY_S,
	"move_left": KEY_A,
	"move_right": KEY_D,
	"run_modifier": KEY_SHIFT,
}

var _asset_scene_map: Dictionary = {}
var _transitions: Array[Dictionary] = []
var _blocking_spheres: Array[Dictionary] = []
var _transition_cooldown: float = 0.0

var _viewport: SubViewport
var _world_root: Node3D
var _terrain_root: Node3D
var _foliage_root: Node3D
var _object_root: Node3D
var _camera_rig: Node3D
var _camera_pivot: Node3D
var _camera: Camera3D
var _player_root: Node3D
var _player_model: Node3D
var _navigation_region: NavigationRegion3D

var _player_position: Vector3 = Vector3(2.0, 0.0, 2.0)
var _target_camera_position: Vector3 = Vector3.ZERO
var _player_appearance_key: String = "human_male"
var _player_animation_state: String = "idle"
var _camera_profile_key: String = DEFAULT_CAMERA_PROFILE_KEY
var _map_scale: Dictionary = {}
var _scene_variant_hint: String = ""

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
	environment.ambient_light_energy = 0.82
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
	fill.light_energy = 0.36
	fill.omni_range = 18.0
	_world_root.add_child(fill)

	_terrain_root = Node3D.new()
	_terrain_root.name = "Terrain"
	_world_root.add_child(_terrain_root)

	_foliage_root = Node3D.new()
	_foliage_root.name = "Foliage"
	_world_root.add_child(_foliage_root)

	_object_root = Node3D.new()
	_object_root.name = "Objects"
	_world_root.add_child(_object_root)

	_navigation_region = NavigationRegion3D.new()
	_navigation_region.name = "NavRegion"
	_world_root.add_child(_navigation_region)

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

	_spawn_default_environment()
	_set_player_model(_player_appearance_key)
	_apply_camera_profile()
	_update_player_transform(true)
	_build_navigation_mesh()

	resized.connect(_on_resized)
	_on_resized()

func _on_resized() -> void:
	if _viewport == null:
		return
	_viewport.size = Vector2i(maxi(1, int(size.x)), maxi(1, int(size.y)))

func _clear_children(node: Node) -> void:
	for child in node.get_children():
		child.queue_free()

func _set_player_model(appearance_key: String) -> void:
	_player_appearance_key = appearance_key.strip_edges().to_lower()
	if _player_appearance_key.is_empty():
		_player_appearance_key = "human_male"
	if _player_model != null:
		_player_model.queue_free()
		_player_model = null
	_player_model = SELLSWORD_FACTORY.create_model(_player_appearance_key)
	_player_root.add_child(_player_model)
	_set_player_animation("idle", true)

func _set_player_animation(state: String, force: bool = false) -> void:
	if _player_model == null:
		return
	var normalized = state.strip_edges().to_lower()
	if normalized.is_empty():
		normalized = "idle"
	if not force and normalized == _player_animation_state:
		return
	_player_animation_state = normalized
	SELSWORD_FACTORY.play_animation(_player_model, _player_animation_state)

func _spawn_default_environment() -> void:
	_clear_children(_terrain_root)
	_clear_children(_foliage_root)
	_clear_children(_object_root)
	_blocking_spheres.clear()

	var ground = SELLSWORD_FACTORY.build_ground(maxf(8.0, float(max(world_width_tiles, world_height_tiles)) * 0.8))
	_terrain_root.add_child(ground)

	# Starter foliage kit for early 3D blockout when no authored objects are available.
	var span_x = max(6, mini(22, world_width_tiles / 4))
	var span_z = max(6, mini(22, world_height_tiles / 4))
	for x in range(-span_x, span_x + 1, 3):
		for z in range(-span_z, span_z + 1, 3):
			if (abs(x) + abs(z)) % 4 != 0:
				continue
			var tuft = SELLSWORD_FACTORY.build_grass_tuft((x + span_x) * 31 + z + span_z)
			tuft.position = Vector3(float(x) * 0.65, 0.0, float(z) * 0.65)
			_foliage_root.add_child(tuft)

func _resolve_scene_path_for_asset(asset_key: String, object_row: Dictionary) -> String:
	var normalized = asset_key.strip_edges().to_lower()
	var explicit_scene_path = str(object_row.get("scene_path", "")).strip_edges()
	if not explicit_scene_path.is_empty():
		return explicit_scene_path
	var runtime_path = str(_asset_scene_map.get(normalized, "")).strip_edges()
	if not runtime_path.is_empty():
		return runtime_path
	match normalized:
		"ground_stone_a":
			return "res://scenes/environment/ground_tile_stone_3d.tscn"
		"foliage_grass_a":
			return "res://scenes/environment/foliage_grass_a_3d.tscn"
		"foliage_tree_dead_a":
			return "res://scenes/environment/foliage_tree_dead_3d.tscn"
		_:
			return ""

func _instantiate_asset(asset_key: String, object_row: Dictionary) -> Node3D:
	var scene_path = _resolve_scene_path_for_asset(asset_key, object_row)
	if not scene_path.is_empty() and ResourceLoader.exists(scene_path):
		var resource = ResourceLoader.load(scene_path)
		if resource is PackedScene:
			var instance = (resource as PackedScene).instantiate()
			if instance is Node3D:
				return instance as Node3D
			if instance != null:
				instance.queue_free()
	var generated = SELLSWORD_FACTORY.create_environment_asset(asset_key)
	if generated != null:
		return generated
	return null

func _apply_object_transform(target: Node3D, transform_payload: Dictionary) -> void:
	target.position = Vector3(
		float(transform_payload.get("x", 0.0)),
		float(transform_payload.get("z", 0.0)),
		float(transform_payload.get("y", 0.0))
	)
	target.rotation_degrees = Vector3(0.0, float(transform_payload.get("rotation_deg", 0.0)), 0.0)
	target.scale = Vector3(
		float(transform_payload.get("scale_x", 1.0)),
		1.0,
		float(transform_payload.get("scale_y", 1.0))
	)

func _register_blocker(asset_key: String, object_row: Dictionary, object_node: Node3D) -> void:
	var collision_payload = object_row.get("collision", {})
	if not (collision_payload is Dictionary):
		collision_payload = {}
	var walkable = bool(collision_payload.get("walkable", false))
	if walkable:
		return
	var radius = maxf(0.25, float(collision_payload.get("radius", 0.0)))
	if radius <= 0.26:
		var box := AABB(Vector3.ZERO, Vector3.ZERO)
		if object_node is Node3D:
			for child in object_node.get_children():
				if child is MeshInstance3D and (child as MeshInstance3D).mesh != null:
					box = box.merge((child as MeshInstance3D).mesh.get_aabb()) if box.size.length() > 0.0 else (child as MeshInstance3D).mesh.get_aabb()
		if box.size.length() > 0.0:
			radius = maxf(radius, maxf(box.size.x, box.size.z) * 0.42)
	if radius <= 0.26 and (asset_key.begins_with("foliage_tree") or asset_key.find("tree") >= 0):
		radius = 0.75
	if radius <= 0.26:
		return
	_blocking_spheres.append({
		"x": object_node.position.x,
		"z": object_node.position.z,
		"radius": radius,
	})

func _spawn_level_objects(objects: Array) -> void:
	_clear_children(_terrain_root)
	_clear_children(_foliage_root)
	_clear_children(_object_root)
	_blocking_spheres.clear()

	for object_row in objects:
		if not (object_row is Dictionary):
			continue
		var asset_key = str(object_row.get("asset_key", object_row.get("object_id", ""))).strip_edges().to_lower()
		if asset_key.is_empty():
			continue
		if asset_key == "spawn_marker" or asset_key == "spawn_marker_3d":
			continue
		var instance = _instantiate_asset(asset_key, object_row)
		if instance == null:
			continue
		var transform_payload = object_row.get("transform", {})
		if transform_payload is Dictionary:
			_apply_object_transform(instance, transform_payload)
		if asset_key.begins_with("ground_"):
			_terrain_root.add_child(instance)
		elif asset_key.begins_with("foliage_"):
			_foliage_root.add_child(instance)
		else:
			_object_root.add_child(instance)
		_register_blocker(asset_key, object_row, instance)

func _build_navigation_mesh() -> void:
	if _navigation_region == null:
		return
	var nav_mesh := NavigationMesh.new()
	nav_mesh.cell_size = 0.4
	nav_mesh.cell_height = 0.2
	nav_mesh.agent_radius = 0.42
	nav_mesh.agent_height = 1.6
	var vertices = PackedVector3Array([
		Vector3(0.0, 0.0, 0.0),
		Vector3(float(world_width_tiles), 0.0, 0.0),
		Vector3(float(world_width_tiles), 0.0, float(world_height_tiles)),
		Vector3(0.0, 0.0, float(world_height_tiles)),
	])
	if nav_mesh.has_method("set_vertices"):
		nav_mesh.call("set_vertices", vertices)
	if nav_mesh.has_method("add_polygon"):
		nav_mesh.call("add_polygon", PackedInt32Array([0, 1, 2, 3]))
	_navigation_region.navigation_mesh = nav_mesh

func _extract_runtime_asset_map(runtime_cfg: Dictionary) -> Dictionary:
	var resolved: Dictionary = {}
	if not (runtime_cfg is Dictionary):
		return resolved
	var stack: Array = [runtime_cfg]
	var discovered_sources: Array = []
	while not stack.is_empty():
		var current = stack.pop_back()
		discovered_sources.append(current)
		if current is Dictionary:
			for key in current.keys():
				var value = current.get(key)
				if value is Dictionary:
					stack.append(value)
		elif current is Array:
			for value in current:
				if value is Dictionary or value is Array:
					stack.append(value)
	var sources: Array = []
	if runtime_cfg.has("environment_assets"):
		sources.append(runtime_cfg.get("environment_assets"))
	if runtime_cfg.has("assets"):
		sources.append(runtime_cfg.get("assets"))
	if runtime_cfg.has("asset_domains"):
		sources.append(runtime_cfg.get("asset_domains"))
	sources.append_array(discovered_sources)
	for source in sources:
		if not (source is Dictionary):
			continue
		var entries = source.get("entries", source.get("objects", []))
		if not (entries is Array):
			continue
		for entry in entries:
			if not (entry is Dictionary):
				continue
			var key = str(entry.get("key", "")).strip_edges().to_lower()
			var scene_path = str(entry.get("scene_path", "")).strip_edges()
			if key.is_empty() or scene_path.is_empty():
				continue
			resolved[key] = scene_path
	return resolved

func configure_world(
	level_name: String,
	width_tiles: int,
	height_tiles: int,
	spawn_world: Vector2,
	level_payload: Dictionary = {},
	spawn_payload: Dictionary = {}
) -> void:
	world_name = level_name
	world_width_tiles = maxi(width_tiles, 8)
	world_height_tiles = maxi(height_tiles, 8)
	var map_scale_tile_world_size = float(_map_scale.get("tile_world_size", GRID_UNIT_PIXELS))
	if map_scale_tile_world_size <= 0.0:
		map_scale_tile_world_size = GRID_UNIT_PIXELS
	var spawn_world_z = float(spawn_payload.get("world_z", 0.0))
	var spawn_yaw_deg = float(spawn_payload.get("yaw_deg", 0.0))
	_player_position = Vector3(spawn_world.x / map_scale_tile_world_size, spawn_world_z, spawn_world.y / map_scale_tile_world_size)
	if _player_model != null:
		_player_model.rotation_degrees.y = spawn_yaw_deg
	_transitions.clear()
	_transition_cooldown = 0.0

	if level_payload.has("transitions") and level_payload.get("transitions") is Array:
		for row in level_payload.get("transitions", []):
			if row is Dictionary:
				_transitions.append(row)

	var has_objects = false
	if level_payload.has("objects") and level_payload.get("objects") is Array:
		var objects: Array = level_payload.get("objects", [])
		if not objects.is_empty():
			has_objects = true
		for object_row in objects:
			if not (object_row is Dictionary):
				continue
			if str(object_row.get("object_id", "")) != "spawn_marker_3d":
				continue
			var transform = object_row.get("transform", {})
			if transform is Dictionary:
				_player_position = Vector3(float(transform.get("x", _player_position.x)), float(transform.get("z", 0.0)), float(transform.get("y", _player_position.z)))
				if _player_model != null:
					_player_model.rotation_degrees.y = float(transform.get("rotation_deg", 0.0))
				break
		_spawn_level_objects(objects)

	if not has_objects:
		_spawn_default_environment()

	_build_navigation_mesh()
	_update_player_transform(true)
	_set_player_animation("idle", true)

func configure_runtime(runtime_cfg: Dictionary) -> void:
	if not (runtime_cfg is Dictionary):
		return
	var movement_cfg: Dictionary = runtime_cfg.get("movement", {}) if runtime_cfg.has("movement") else runtime_cfg
	player_speed_units = maxf(1.0, float(movement_cfg.get("player_speed_tiles", DEFAULT_PLAYER_SPEED_UNITS)))
	player_run_speed_units = maxf(player_speed_units, float(movement_cfg.get("player_run_speed_tiles", DEFAULT_PLAYER_RUN_SPEED_UNITS)))
	var runtime_keybinds = runtime_cfg.get("keybinds", {})
	if runtime_keybinds is Dictionary:
		for action_name in runtime_keybinds.keys():
			keybinds[action_name] = int(runtime_keybinds.get(action_name, keybinds.get(action_name, 0)))
	_asset_scene_map = _extract_runtime_asset_map(runtime_cfg)
	var requested_camera_profile = str(runtime_cfg.get("camera_profile_key", DEFAULT_CAMERA_PROFILE_KEY)).strip_edges().to_lower()
	_camera_profile_key = requested_camera_profile if not requested_camera_profile.is_empty() else DEFAULT_CAMERA_PROFILE_KEY
	_apply_camera_profile()
	var map_scale_payload = runtime_cfg.get("map_scale", {})
	if map_scale_payload is Dictionary:
		_map_scale = map_scale_payload.duplicate(true)
	else:
		_map_scale = {}
	_scene_variant_hint = str(runtime_cfg.get("scene_variant_hint", "")).strip_edges().to_lower()

func _apply_camera_profile() -> void:
	if _camera == null:
		return
	match _camera_profile_key:
		"arpg_poe_close":
			_camera.fov = 48.0
		"arpg_poe_far":
			_camera.fov = 54.0
		_:
			_camera.fov = 50.0

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

func _action_pressed(action_name: String) -> bool:
	var keycode = int(keybinds.get(action_name, 0))
	if keycode <= 0:
		return false
	return Input.is_key_pressed(keycode)

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

func _is_walk_blocked(position: Vector3) -> bool:
	if position.x < 0.0 or position.z < 0.0:
		return true
	if position.x > float(world_width_tiles) or position.z > float(world_height_tiles):
		return true
	for blocker in _blocking_spheres:
		var bx = float(blocker.get("x", 0.0))
		var bz = float(blocker.get("z", 0.0))
		var radius = float(blocker.get("radius", 0.55))
		var delta = Vector2(position.x - bx, position.z - bz)
		if delta.length() <= radius:
			return true
	return false

func _check_transition_trigger() -> void:
	if _transition_cooldown > 0.0:
		return
	for transition in _transitions:
		var tx = float(transition.get("trigger_x", transition.get("x", transition.get("from_x", -9999.0))))
		var ty = float(transition.get("trigger_y", transition.get("y", transition.get("from_y", -9999.0))))
		if tx <= -9000.0 or ty <= -9000.0:
			continue
		var radius = maxf(0.3, float(transition.get("radius", 1.2)))
		if Vector2(_player_position.x - tx, _player_position.z - ty).length() <= radius:
			_transition_cooldown = 0.65
			emit_signal("transition_requested", transition)
			break

func _process(delta: float) -> void:
	if not _active:
		return
	if _transition_cooldown > 0.0:
		_transition_cooldown = maxf(0.0, _transition_cooldown - delta)

	var axis = _movement_axis()
	var moved = false
	if axis != Vector2.ZERO:
		var is_running = _action_pressed("run_modifier")
		var speed = player_run_speed_units if is_running else player_speed_units
		var dir = axis.normalized()
		var candidate = _player_position + Vector3(dir.x * speed * delta, 0.0, dir.y * speed * delta)
		if not _is_walk_blocked(candidate):
			_player_position = candidate
			moved = true
			if _player_model != null:
				_player_model.rotation_degrees.y = SELLSWORD_FACTORY.direction_to_rotation_y(_axis_to_direction(axis))
			emit_signal("player_position_changed", get_world_position())
			_set_player_animation("run" if is_running else "walk")

	if not moved:
		_set_player_animation("idle")

	# Keep camera anchored behind the player using fixed ARPG cinematic angle.
	_target_camera_position = Vector3(_player_position.x + CAMERA_LOOK_AHEAD, 0.0, _player_position.z + CAMERA_LOOK_AHEAD)
	_camera_rig.position = _camera_rig.position.lerp(_target_camera_position, clampf(delta * CAMERA_FOLLOW_SMOOTH, 0.0, 1.0))

	_check_transition_trigger()
	_update_player_transform(false)

	if moved:
		emit_signal("combat_state_changed", {
			"player_position": get_world_position(),
			"mode": "moving",
			"world_name": world_name,
		})

func _update_player_transform(force_camera_snap: bool) -> void:
	_player_root.position = _player_position
	if force_camera_snap:
		_target_camera_position = Vector3(_player_position.x + CAMERA_LOOK_AHEAD, 0.0, _player_position.z + CAMERA_LOOK_AHEAD)
		_camera_rig.position = _target_camera_position
