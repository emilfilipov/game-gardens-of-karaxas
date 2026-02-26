extends SubViewportContainer

signal player_position_changed(position: Vector2)
signal transition_requested(transition: Dictionary)
signal combat_state_changed(state: Dictionary)
signal loot_dropped(item: Dictionary)
signal quest_event(event: Dictionary)
signal npc_interacted(npc: Dictionary)

const SELLSWORD_FACTORY = preload("res://scripts/sellsword_3d_factory.gd")

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

const GRASS_REVEAL_RADIUS: float = 0.90
const GROUND_REVEAL_STEP: float = 0.38
const WALL_REVEAL_INTERVAL: float = 0.08
const MAX_GROUND_REVEALS: int = 180
const MAX_WALL_REVEALS: int = 90
const DEFAULT_SCENE_VARIANT_HINT: String = "arena_flat_grass"

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
var _reveal_root: Node3D
var _ground_reveal_root: Node3D
var _wall_reveal_root: Node3D
var _camera_rig: Node3D
var _camera_pivot: Node3D
var _camera: Camera3D
var _player_root: Node3D
var _player_model: Node3D
var _navigation_region: NavigationRegion3D

var _player_position: Vector3 = Vector3(2.0, 0.0, 2.0)
var _target_camera_position: Vector3 = Vector3.ZERO
var _player_appearance_key: String = "plomper_ball"
var _player_animation_state: String = "idle"
var _camera_profile_key: String = DEFAULT_CAMERA_PROFILE_KEY
var _map_scale: Dictionary = {}
var _scene_variant_hint: String = DEFAULT_SCENE_VARIANT_HINT

var _grass_tufts: Array[Node3D] = []
var _revealed_grass: Dictionary = {}
var _wall_segments: Array[MeshInstance3D] = []
var _ground_reveals: Array[Node3D] = []
var _wall_reveals: Array[Node3D] = []
var _last_ground_reveal_position: Vector3 = Vector3.ZERO
var _has_ground_reveal_position: bool = false
var _wall_reveal_timer: float = 0.0

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
	environment.background_color = Color(0.03, 0.03, 0.03)
	environment.ambient_light_color = Color(0.52, 0.52, 0.52)
	environment.ambient_light_energy = 0.86
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.environment = environment
	_world_root.add_child(env)

	var sun = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, 30.0, 0.0)
	sun.light_color = Color(1.0, 1.0, 1.0)
	sun.light_energy = 1.65
	sun.shadow_enabled = true
	_world_root.add_child(sun)

	var fill = OmniLight3D.new()
	fill.position = Vector3(-6.0, 4.0, -6.0)
	fill.light_color = Color(0.74, 0.74, 0.74)
	fill.light_energy = 0.40
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

	_reveal_root = Node3D.new()
	_reveal_root.name = "RevealRoot"
	_world_root.add_child(_reveal_root)

	_ground_reveal_root = Node3D.new()
	_ground_reveal_root.name = "GroundReveals"
	_reveal_root.add_child(_ground_reveal_root)

	_wall_reveal_root = Node3D.new()
	_wall_reveal_root.name = "WallReveals"
	_reveal_root.add_child(_wall_reveal_root)

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

func _to_grayscale(color_value: Color) -> Color:
	var luma = color_value.r * 0.299 + color_value.g * 0.587 + color_value.b * 0.114
	return Color(luma, luma, luma, color_value.a)

func _collect_mesh_instances(root: Node, output: Array[MeshInstance3D]) -> void:
	if root is MeshInstance3D:
		output.append(root as MeshInstance3D)
	for child in root.get_children():
		_collect_mesh_instances(child, output)

func _monochrome_material_for(source_material: Material) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.roughness = 0.88
	material.metallic = 0.0
	material.albedo_color = Color(0.55, 0.55, 0.55, 1.0)
	if source_material is BaseMaterial3D:
		var base := source_material as BaseMaterial3D
		material.roughness = base.roughness
		material.metallic = base.metallic
		material.albedo_color = _to_grayscale(base.albedo_color)
	return material

func _apply_monochrome_materials(root: Node) -> void:
	var meshes: Array[MeshInstance3D] = []
	_collect_mesh_instances(root, meshes)
	for mesh_instance in meshes:
		var source: Material = mesh_instance.material_override
		if source == null and mesh_instance.mesh != null and mesh_instance.mesh.get_surface_count() > 0:
			source = mesh_instance.mesh.surface_get_material(0)
		mesh_instance.material_override = _monochrome_material_for(source)

func _set_player_model(appearance_key: String) -> void:
	var requested = appearance_key.strip_edges().to_lower()
	if requested.is_empty() or not requested.begins_with("plomper"):
		requested = "plomper_ball"
	_player_appearance_key = requested
	if _player_model != null:
		_player_model.queue_free()
		_player_model = null
	_player_model = SELLSWORD_FACTORY.create_model(_player_appearance_key)
	_apply_monochrome_materials(_player_model)
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

func _wall_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.36, 0.36, 0.36)
	mat.roughness = 0.95
	mat.metallic = 0.0
	return mat

func _wall_revealed_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.95, 0.53, 0.28)
	mat.roughness = 0.78
	mat.metallic = 0.0
	return mat

func _grass_material(revealed: bool) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	if revealed:
		mat.albedo_color = Color(0.18, 0.62, 0.24)
		mat.roughness = 0.84
	else:
		mat.albedo_color = Color(0.50, 0.50, 0.50)
		mat.roughness = 0.88
	mat.metallic = 0.0
	return mat

func _spawn_arena_walls() -> void:
	_wall_segments.clear()
	var wall_root = Node3D.new()
	wall_root.name = "BoundaryWalls"
	_object_root.add_child(wall_root)

	var wall_mesh := BoxMesh.new()
	wall_mesh.size = Vector3(0.45, 0.95, 1.0)
	var wall_mat = _wall_material()

	var max_x = float(world_width_tiles)
	var max_z = float(world_height_tiles)

	for z_idx in range(0, world_height_tiles + 1, 2):
		var z = float(z_idx)
		var west = MeshInstance3D.new()
		west.mesh = wall_mesh
		west.material_override = wall_mat
		west.position = Vector3(0.0, 0.48, z)
		wall_root.add_child(west)
		_wall_segments.append(west)

		var east = MeshInstance3D.new()
		east.mesh = wall_mesh
		east.material_override = wall_mat
		east.position = Vector3(max_x, 0.48, z)
		wall_root.add_child(east)
		_wall_segments.append(east)

	for x_idx in range(0, world_width_tiles + 1, 2):
		var x = float(x_idx)
		var north = MeshInstance3D.new()
		north.mesh = wall_mesh
		north.material_override = wall_mat
		north.rotation_degrees = Vector3(0.0, 90.0, 0.0)
		north.position = Vector3(x, 0.48, 0.0)
		wall_root.add_child(north)
		_wall_segments.append(north)

		var south = MeshInstance3D.new()
		south.mesh = wall_mesh
		south.material_override = wall_mat
		south.rotation_degrees = Vector3(0.0, 90.0, 0.0)
		south.position = Vector3(x, 0.48, max_z)
		wall_root.add_child(south)
		_wall_segments.append(south)

func _register_grass_tuft(tuft: Node3D) -> void:
	_grass_tufts.append(tuft)
	_revealed_grass[tuft.get_instance_id()] = false
	var meshes: Array[MeshInstance3D] = []
	_collect_mesh_instances(tuft, meshes)
	var baseline_material = _grass_material(false)
	for mesh_instance in meshes:
		mesh_instance.material_override = baseline_material

func _reveal_grass_tuft(tuft: Node3D) -> void:
	if tuft == null:
		return
	var tuft_id = tuft.get_instance_id()
	if bool(_revealed_grass.get(tuft_id, false)):
		return
	_revealed_grass[tuft_id] = true
	var meshes: Array[MeshInstance3D] = []
	_collect_mesh_instances(tuft, meshes)
	var revealed_material = _grass_material(true)
	for mesh_instance in meshes:
		mesh_instance.material_override = revealed_material

func _spawn_ground_reveal(position: Vector3) -> void:
	var marker_mesh := CylinderMesh.new()
	marker_mesh.top_radius = 0.28
	marker_mesh.bottom_radius = 0.28
	marker_mesh.height = 0.015
	marker_mesh.radial_segments = 18
	var marker_mat := StandardMaterial3D.new()
	marker_mat.albedo_color = Color(0.20, 0.68, 0.26, 0.92)
	marker_mat.roughness = 0.75
	marker_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	marker_mat.no_depth_test = false
	var marker = MeshInstance3D.new()
	marker.mesh = marker_mesh
	marker.material_override = marker_mat
	marker.position = Vector3(position.x, 0.01, position.z)
	_ground_reveal_root.add_child(marker)
	_ground_reveals.append(marker)
	while _ground_reveals.size() > MAX_GROUND_REVEALS:
		var old_marker = _ground_reveals.pop_front()
		if old_marker != null:
			old_marker.queue_free()

func _spawn_wall_reveal(position: Vector3) -> void:
	var clamped = Vector3(
		clampf(position.x, 0.0, float(world_width_tiles)),
		0.34,
		clampf(position.z, 0.0, float(world_height_tiles))
	)
	var hit_mesh := SphereMesh.new()
	hit_mesh.radius = 0.13
	hit_mesh.height = 0.26
	hit_mesh.radial_segments = 18
	hit_mesh.rings = 9
	var hit_mat := StandardMaterial3D.new()
	hit_mat.albedo_color = Color(0.95, 0.48, 0.20)
	hit_mat.roughness = 0.64
	hit_mat.metallic = 0.0
	var hit = MeshInstance3D.new()
	hit.mesh = hit_mesh
	hit.material_override = hit_mat
	hit.position = clamped
	_wall_reveal_root.add_child(hit)
	_wall_reveals.append(hit)
	while _wall_reveals.size() > MAX_WALL_REVEALS:
		var old_hit = _wall_reveals.pop_front()
		if old_hit != null:
			old_hit.queue_free()

	var nearest_segment: MeshInstance3D = null
	var nearest_distance := INF
	for segment in _wall_segments:
		if segment == null:
			continue
		var dist = Vector2(segment.position.x - clamped.x, segment.position.z - clamped.z).length_squared()
		if dist < nearest_distance:
			nearest_distance = dist
			nearest_segment = segment
	if nearest_segment != null:
		nearest_segment.material_override = _wall_revealed_material()

func _apply_player_reveal_feedback(moved: bool) -> void:
	if not moved:
		return
	for tuft in _grass_tufts:
		if tuft == null:
			continue
		if Vector2(tuft.position.x - _player_position.x, tuft.position.z - _player_position.z).length() <= GRASS_REVEAL_RADIUS:
			_reveal_grass_tuft(tuft)
	if not _has_ground_reveal_position or _last_ground_reveal_position.distance_to(_player_position) >= GROUND_REVEAL_STEP:
		_spawn_ground_reveal(_player_position)
		_last_ground_reveal_position = _player_position
		_has_ground_reveal_position = true

func _spawn_default_environment() -> void:
	_clear_children(_terrain_root)
	_clear_children(_foliage_root)
	_clear_children(_object_root)
	_clear_children(_ground_reveal_root)
	_clear_children(_wall_reveal_root)
	_blocking_spheres.clear()
	_grass_tufts.clear()
	_revealed_grass.clear()
	_wall_segments.clear()
	_ground_reveals.clear()
	_wall_reveals.clear()
	_last_ground_reveal_position = Vector3.ZERO
	_has_ground_reveal_position = false

	var ground_size = maxf(12.0, float(max(world_width_tiles, world_height_tiles)) + 4.0)
	var ground = SELLSWORD_FACTORY.build_ground(ground_size)
	ground.position = Vector3(float(world_width_tiles) * 0.5, 0.0, float(world_height_tiles) * 0.5)
	_apply_monochrome_materials(ground)
	_terrain_root.add_child(ground)

	for x in range(1, world_width_tiles, 2):
		for z in range(1, world_height_tiles, 2):
			if (x + z) % 3 != 0:
				continue
			var seed = x * 4099 + z * 53
			var tuft = SELLSWORD_FACTORY.build_grass_tuft(seed)
			tuft.position = Vector3(float(x), 0.0, float(z))
			_foliage_root.add_child(tuft)
			_register_grass_tuft(tuft)

	_spawn_arena_walls()

func _resolve_scene_path_for_asset(asset_key: String, object_row: Dictionary) -> String:
	var normalized = asset_key.strip_edges().to_lower()
	var explicit_scene_path = str(object_row.get("scene_path", "")).strip_edges()
	if not explicit_scene_path.is_empty():
		return explicit_scene_path
	var runtime_path = str(_asset_scene_map.get(normalized, "")).strip_edges()
	if not runtime_path.is_empty():
		return runtime_path
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
	_clear_children(_ground_reveal_root)
	_clear_children(_wall_reveal_root)
	_blocking_spheres.clear()
	_grass_tufts.clear()
	_revealed_grass.clear()
	_wall_segments.clear()
	_ground_reveals.clear()
	_wall_reveals.clear()
	_last_ground_reveal_position = Vector3.ZERO
	_has_ground_reveal_position = false

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
		_apply_monochrome_materials(instance)
		if asset_key.begins_with("ground_"):
			_terrain_root.add_child(instance)
		elif asset_key.begins_with("foliage_"):
			_foliage_root.add_child(instance)
			if asset_key.find("grass") >= 0:
				_register_grass_tuft(instance)
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
		has_objects = not objects.is_empty()
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

	var scene_variant = _scene_variant_hint
	if scene_variant.is_empty():
		scene_variant = DEFAULT_SCENE_VARIANT_HINT
	var force_flat_arena = scene_variant == "arena_flat_grass"

	if force_flat_arena:
		_spawn_default_environment()
	elif has_objects:
		_spawn_level_objects(level_payload.get("objects", []))
	else:
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
	_scene_variant_hint = str(runtime_cfg.get("scene_variant_hint", DEFAULT_SCENE_VARIANT_HINT)).strip_edges().to_lower()
	if _scene_variant_hint.is_empty():
		_scene_variant_hint = DEFAULT_SCENE_VARIANT_HINT

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
	if _wall_reveal_timer > 0.0:
		_wall_reveal_timer = maxf(0.0, _wall_reveal_timer - delta)

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
		elif _wall_reveal_timer <= 0.0:
			_spawn_wall_reveal(candidate)
			_wall_reveal_timer = WALL_REVEAL_INTERVAL

	if not moved:
		_set_player_animation("idle")

	_apply_player_reveal_feedback(moved)

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
