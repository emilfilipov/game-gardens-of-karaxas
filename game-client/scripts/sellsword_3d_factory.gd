extends RefCounted
class_name Sellsword3DFactory

const DIRECTIONS: Array[String] = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
const TARGET_MODEL_HEIGHT: float = 1.92

const GENERATED_ASSET_PATHS := {
	"human_male": "res://../assets/3d/generated/sellsword_male.glb",
	"human_female": "res://../assets/3d/generated/sellsword_female.glb",
	"ground_stone_a": "res://../assets/3d/generated/ground_tile_stone.glb",
	"foliage_grass_a": "res://../assets/3d/generated/foliage_grass_a.glb",
	"foliage_tree_dead_a": "res://../assets/3d/generated/foliage_tree_dead_a.glb",
}

static var _generated_scene_cache: Dictionary = {}

static func _mat(color: Color, roughness: float = 0.86, metallic: float = 0.0) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = clampf(roughness, 0.0, 1.0)
	material.metallic = clampf(metallic, 0.0, 1.0)
	material.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	return material

static func _mesh_instance(mesh: Mesh, material: Material, position: Vector3, rotation_deg: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = material
	node.position = position
	node.rotation_degrees = rotation_deg
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	return node

static func _load_generated_scene(asset_key: String) -> Node3D:
	var path = str(GENERATED_ASSET_PATHS.get(asset_key, "")).strip_edges()
	if path.is_empty():
		return null
	var absolute_path = ProjectSettings.globalize_path(path)
	if not FileAccess.file_exists(absolute_path):
		return null

	if _generated_scene_cache.has(absolute_path):
		var cached = _generated_scene_cache.get(absolute_path)
		if cached is PackedScene:
			var cached_instance = (cached as PackedScene).instantiate()
			if cached_instance is Node3D:
				return cached_instance as Node3D
			if cached_instance != null:
				cached_instance.queue_free()

	var resource = ResourceLoader.load(path)
	if resource is PackedScene:
		_generated_scene_cache[absolute_path] = resource
		var scene_instance = (resource as PackedScene).instantiate()
		if scene_instance is Node3D:
			return scene_instance as Node3D
		if scene_instance != null:
			scene_instance.queue_free()

	if not ClassDB.class_exists("GLTFDocument") or not ClassDB.class_exists("GLTFState"):
		return null
	var gltf_document = ClassDB.instantiate("GLTFDocument")
	var gltf_state = ClassDB.instantiate("GLTFState")
	if gltf_document == null or gltf_state == null:
		return null

	var append_error = int(gltf_document.call("append_from_file", absolute_path, gltf_state))
	if append_error != OK:
		return null
	var generated_scene = gltf_document.call("generate_scene", gltf_state)
	if not (generated_scene is Node3D):
		if generated_scene is Node:
			(generated_scene as Node).queue_free()
		return null

	var packed := PackedScene.new()
	if packed.pack(generated_scene) == OK:
		_generated_scene_cache[absolute_path] = packed
	return generated_scene as Node3D

static func _collect_mesh_instances(root: Node, output: Array[MeshInstance3D]) -> void:
	if root is MeshInstance3D:
		output.append(root as MeshInstance3D)
	for child in root.get_children():
		_collect_mesh_instances(child, output)

static func _combined_aabb(root: Node3D) -> AABB:
	var meshes: Array[MeshInstance3D] = []
	_collect_mesh_instances(root, meshes)
	if meshes.is_empty():
		return AABB(Vector3.ZERO, Vector3.ZERO)
	var has_box = false
	var combined := AABB(Vector3.ZERO, Vector3.ZERO)
	for mesh_instance in meshes:
		if mesh_instance.mesh == null:
			continue
		var local_box: AABB = mesh_instance.mesh.get_aabb()
		var global_box := mesh_instance.global_transform * local_box
		if not has_box:
			combined = global_box
			has_box = true
		else:
			combined = combined.merge(global_box)
	if not has_box:
		return AABB(Vector3.ZERO, Vector3.ZERO)
	return combined

static func _normalize_and_ground_model(model: Node3D) -> void:
	if model == null:
		return
	var raw_box = _combined_aabb(model)
	if raw_box.size.y > 0.001:
		var scale_ratio = clampf(TARGET_MODEL_HEIGHT / raw_box.size.y, 0.08, 6.0)
		model.scale *= Vector3.ONE * scale_ratio
	var scaled_box = _combined_aabb(model)
	if scaled_box.size.y > 0.001:
		model.position.y -= scaled_box.position.y

static func _set_cast_shadows(root: Node) -> void:
	if root is MeshInstance3D:
		(root as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for child in root.get_children():
		_set_cast_shadows(child)

static func _find_first_node3d_with_tokens(root: Node, tokens: Array[String]) -> Node3D:
	var queue: Array[Node] = [root]
	while not queue.is_empty():
		var current = queue.pop_front()
		if current is Node3D:
			var node_name = current.name.to_lower()
			for token in tokens:
				if node_name.find(token) >= 0:
					return current as Node3D
		for child in current.get_children():
			if child is Node:
				queue.append(child)
	return null

static func _find_or_create_animation_player(root: Node3D) -> AnimationPlayer:
	var queue: Array[Node] = [root]
	while not queue.is_empty():
		var current = queue.pop_front()
		if current is AnimationPlayer:
			return current as AnimationPlayer
		for child in current.get_children():
			if child is Node:
				queue.append(child)
	var created := AnimationPlayer.new()
	created.name = "AnimationPlayer"
	root.add_child(created)
	return created

static func _animation_library(player: AnimationPlayer) -> AnimationLibrary:
	if player == null:
		return null
	var existing = player.get_animation_library("")
	if existing is AnimationLibrary:
		return existing as AnimationLibrary
	var created := AnimationLibrary.new()
	player.add_animation_library("", created)
	return created

static func _has_animation(player: AnimationPlayer, key: String) -> bool:
	var library = _animation_library(player)
	return library != null and library.has_animation(key)

static func _track_value(anim: Animation, player: AnimationPlayer, node: Node, property: String, keys: Array[Array]) -> void:
	if anim == null or player == null or node == null:
		return
	if not (node is Node):
		return
	var rel_path = player.get_path_to(node)
	if rel_path.is_empty():
		return
	var track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(track, NodePath(str(rel_path) + ":" + property))
	for entry in keys:
		if entry.size() < 2:
			continue
		anim.track_insert_key(track, float(entry[0]), entry[1])

static func _ensure_animation(player: AnimationPlayer, key: String, model_root: Node3D, limbs: Dictionary, length: float, looping: bool, mode: String) -> void:
	if player == null or model_root == null:
		return
	if _has_animation(player, key):
		return
	var anim := Animation.new()
	anim.length = length
	anim.loop_mode = Animation.LOOP_LINEAR if looping else Animation.LOOP_NONE
	
	var arm_l = limbs.get("arm_l")
	var arm_r = limbs.get("arm_r")
	var leg_l = limbs.get("leg_l")
	var leg_r = limbs.get("leg_r")
	var head = limbs.get("head")

	match mode:
		"idle":
			_track_value(anim, player, model_root, "position:y", [[0.0, 0.0], [length * 0.5, 0.018], [length, 0.0]])
			if head is Node3D:
				_track_value(anim, player, head, "rotation_degrees:x", [[0.0, 0.0], [length * 0.5, 1.5], [length, 0.0]])
		"walk":
			_track_value(anim, player, model_root, "position:y", [[0.0, 0.0], [length * 0.5, 0.034], [length, 0.0]])
			if arm_l is Node3D and arm_r is Node3D:
				_track_value(anim, player, arm_l, "rotation_degrees:x", [[0.0, -18.0], [length * 0.5, 18.0], [length, -18.0]])
				_track_value(anim, player, arm_r, "rotation_degrees:x", [[0.0, 18.0], [length * 0.5, -18.0], [length, 18.0]])
			if leg_l is Node3D and leg_r is Node3D:
				_track_value(anim, player, leg_l, "rotation_degrees:x", [[0.0, 14.0], [length * 0.5, -14.0], [length, 14.0]])
				_track_value(anim, player, leg_r, "rotation_degrees:x", [[0.0, -14.0], [length * 0.5, 14.0], [length, -14.0]])
		"run":
			_track_value(anim, player, model_root, "position:y", [[0.0, 0.0], [length * 0.5, 0.052], [length, 0.0]])
			if arm_l is Node3D and arm_r is Node3D:
				_track_value(anim, player, arm_l, "rotation_degrees:x", [[0.0, -34.0], [length * 0.5, 34.0], [length, -34.0]])
				_track_value(anim, player, arm_r, "rotation_degrees:x", [[0.0, 34.0], [length * 0.5, -34.0], [length, 34.0]])
			if leg_l is Node3D and leg_r is Node3D:
				_track_value(anim, player, leg_l, "rotation_degrees:x", [[0.0, 24.0], [length * 0.5, -24.0], [length, 24.0]])
				_track_value(anim, player, leg_r, "rotation_degrees:x", [[0.0, -24.0], [length * 0.5, 24.0], [length, -24.0]])
		"attack":
			if arm_r is Node3D:
				_track_value(anim, player, arm_r, "rotation_degrees:x", [[0.0, 8.0], [length * 0.35, -72.0], [length * 0.65, 46.0], [length, 6.0]])
			if arm_l is Node3D:
				_track_value(anim, player, arm_l, "rotation_degrees:x", [[0.0, -6.0], [length * 0.35, 22.0], [length, -6.0]])
			_track_value(anim, player, model_root, "rotation_degrees:y", [[0.0, 0.0], [length * 0.35, -8.0], [length, 0.0]])
		"cast":
			if arm_l is Node3D and arm_r is Node3D:
				_track_value(anim, player, arm_l, "rotation_degrees:x", [[0.0, -10.0], [length * 0.4, -58.0], [length, -10.0]])
				_track_value(anim, player, arm_r, "rotation_degrees:x", [[0.0, -10.0], [length * 0.4, -58.0], [length, -10.0]])
			_track_value(anim, player, model_root, "position:y", [[0.0, 0.0], [length * 0.5, 0.028], [length, 0.0]])
		"hurt":
			_track_value(anim, player, model_root, "rotation_degrees:x", [[0.0, 0.0], [length * 0.35, -14.0], [length, 0.0]])
		"death":
			_track_value(anim, player, model_root, "rotation_degrees:z", [[0.0, 0.0], [length, 88.0]])
			_track_value(anim, player, model_root, "position:y", [[0.0, 0.0], [length, -0.34]])

	var library = _animation_library(player)
	if library != null:
		library.add_animation(key, anim)

static func _ensure_animation_set(model_root: Node3D) -> void:
	if model_root == null:
		return
	var animation_player = _find_or_create_animation_player(model_root)
	if animation_player == null:
		return

	var limbs = {
		"head": _find_first_node3d_with_tokens(model_root, ["head"]),
		"arm_l": _find_first_node3d_with_tokens(model_root, ["arm_l", "arml", "upperarm_l", "leftarm", "arm.l"]),
		"arm_r": _find_first_node3d_with_tokens(model_root, ["arm_r", "armr", "upperarm_r", "rightarm", "arm.r"]),
		"leg_l": _find_first_node3d_with_tokens(model_root, ["leg_l", "legl", "thigh_l", "leftleg", "leg.l"]),
		"leg_r": _find_first_node3d_with_tokens(model_root, ["leg_r", "legr", "thigh_r", "rightleg", "leg.r"]),
	}

	_ensure_animation(animation_player, "idle", model_root, limbs, 1.15, true, "idle")
	_ensure_animation(animation_player, "walk", model_root, limbs, 0.72, true, "walk")
	_ensure_animation(animation_player, "run", model_root, limbs, 0.52, true, "run")
	_ensure_animation(animation_player, "attack", model_root, limbs, 0.56, false, "attack")
	_ensure_animation(animation_player, "cast", model_root, limbs, 0.62, false, "cast")
	_ensure_animation(animation_player, "hurt", model_root, limbs, 0.36, false, "hurt")
	_ensure_animation(animation_player, "death", model_root, limbs, 1.05, false, "death")

static func play_animation(model_root: Node3D, animation_name: String, blend: float = 0.08) -> void:
	if model_root == null:
		return
	var player = _find_or_create_animation_player(model_root)
	if player == null:
		return
	var key = animation_name.strip_edges().to_lower()
	if key.is_empty():
		key = "idle"
	if not _has_animation(player, key):
		if _has_animation(player, "idle"):
			key = "idle"
		else:
			return
	player.play(key, blend)

static func _build_head(appearance_key: String) -> Node3D:
	var is_female = appearance_key.strip_edges().to_lower() == "human_female"
	var root := Node3D.new()
	root.name = "Head"

	var skin = _mat(Color(0.92, 0.79, 0.68), 0.72)
	var hair = _mat(Color(0.26, 0.17, 0.11), 0.78)
	if is_female:
		skin = _mat(Color(0.95, 0.82, 0.74), 0.72)
		hair = _mat(Color(0.30, 0.18, 0.12), 0.78)

	var skull_mesh := SphereMesh.new()
	skull_mesh.radius = 0.18
	skull_mesh.height = 0.34
	skull_mesh.radial_segments = 28
	skull_mesh.rings = 14
	root.add_child(_mesh_instance(skull_mesh, skin, Vector3(0.0, 1.45, 0.0)))

	var hair_mesh := SphereMesh.new()
	hair_mesh.radius = 0.19
	hair_mesh.height = 0.22 if is_female else 0.20
	hair_mesh.radial_segments = 22
	hair_mesh.rings = 10
	root.add_child(_mesh_instance(hair_mesh, hair, Vector3(0.0, 1.53, 0.01)))

	if is_female:
		var ponytail_mesh := CapsuleMesh.new()
		ponytail_mesh.radius = 0.045
		ponytail_mesh.height = 0.28
		ponytail_mesh.radial_segments = 12
		root.add_child(_mesh_instance(ponytail_mesh, hair, Vector3(0.0, 1.38, 0.19), Vector3(28.0, 0.0, 0.0)))

	var nose_mesh := SphereMesh.new()
	nose_mesh.radius = 0.022
	nose_mesh.height = 0.035
	root.add_child(_mesh_instance(nose_mesh, _mat(Color(0.84, 0.67, 0.58), 0.72), Vector3(0.0, 1.42, 0.18)))

	return root

static func _build_torso(is_female: bool) -> Node3D:
	var root := Node3D.new()
	root.name = "Torso"

	var tunic = _mat(Color(0.30, 0.46, 0.36), 0.88)
	var leather = _mat(Color(0.46, 0.30, 0.18), 0.82)
	var metal = _mat(Color(0.69, 0.67, 0.63), 0.42, 0.18)
	var cloak = _mat(Color(0.16, 0.19, 0.24), 0.88)

	var cloak_mesh := CapsuleMesh.new()
	cloak_mesh.radius = 0.31
	cloak_mesh.height = 0.86
	cloak_mesh.radial_segments = 20
	root.add_child(_mesh_instance(cloak_mesh, cloak, Vector3(0.0, 1.02, -0.08), Vector3(0.0, 0.0, 0.0)))

	var torso_mesh := CapsuleMesh.new()
	torso_mesh.radius = 0.25 if is_female else 0.27
	torso_mesh.height = 0.78 if is_female else 0.82
	torso_mesh.radial_segments = 22
	root.add_child(_mesh_instance(torso_mesh, tunic, Vector3(0.0, 1.06, 0.0)))

	var armor_mesh := BoxMesh.new()
	armor_mesh.size = Vector3(0.58 if is_female else 0.62, 0.55, 0.35)
	root.add_child(_mesh_instance(armor_mesh, leather, Vector3(0.0, 1.06, 0.05)))

	var belt_mesh := BoxMesh.new()
	belt_mesh.size = Vector3(0.64, 0.08, 0.18)
	root.add_child(_mesh_instance(belt_mesh, _mat(Color(0.28, 0.18, 0.12), 0.84), Vector3(0.0, 0.86, 0.12)))

	var buckle_mesh := BoxMesh.new()
	buckle_mesh.size = Vector3(0.08, 0.06, 0.02)
	root.add_child(_mesh_instance(buckle_mesh, metal, Vector3(0.0, 0.86, 0.21)))

	var pauldron_mesh := SphereMesh.new()
	pauldron_mesh.radius = 0.12
	pauldron_mesh.height = 0.18
	pauldron_mesh.radial_segments = 12
	pauldron_mesh.rings = 6
	root.add_child(_mesh_instance(pauldron_mesh, metal, Vector3(-0.33, 1.17, 0.02), Vector3(0.0, 0.0, -20.0)))
	root.add_child(_mesh_instance(pauldron_mesh, metal, Vector3(0.33, 1.17, 0.02), Vector3(0.0, 0.0, 20.0)))

	return root

static func _build_limb(name: String, material: Material, radius: float, length: float, position: Vector3) -> MeshInstance3D:
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = length
	mesh.radial_segments = 16
	var limb = _mesh_instance(mesh, material, position)
	limb.name = name
	return limb

static func _build_procedural_model(appearance_key: String) -> Node3D:
	var key = appearance_key.strip_edges().to_lower()
	var is_female = key == "human_female"
	if key.is_empty():
		key = "human_male"

	var root := Node3D.new()
	root.name = "Sellsword_%s" % ("Female" if is_female else "Male")
	root.set_meta("appearance_key", key)

	var skin = _mat(Color(0.92, 0.79, 0.68), 0.74)
	if is_female:
		skin = _mat(Color(0.95, 0.82, 0.74), 0.74)
	var cloth = _mat(Color(0.30, 0.46, 0.36), 0.88)
	var boot = _mat(Color(0.12, 0.11, 0.13), 0.90)

	root.add_child(_build_torso(is_female))
	root.add_child(_build_head(key))

	root.add_child(_build_limb("Arm_L", cloth, 0.075, 0.48, Vector3(-0.36, 1.01, 0.02)))
	root.add_child(_build_limb("Arm_R", cloth, 0.075, 0.48, Vector3(0.36, 1.01, 0.02)))
	root.add_child(_build_limb("Forearm_L", skin, 0.066, 0.32, Vector3(-0.36, 0.79, 0.06)))
	root.add_child(_build_limb("Forearm_R", skin, 0.066, 0.32, Vector3(0.36, 0.79, 0.06)))

	root.add_child(_build_limb("Leg_L", cloth, 0.090 if is_female else 0.095, 0.56, Vector3(-0.15, 0.46, 0.02)))
	root.add_child(_build_limb("Leg_R", cloth, 0.090 if is_female else 0.095, 0.56, Vector3(0.15, 0.46, 0.02)))
	root.add_child(_build_limb("Boot_L", boot, 0.095, 0.24, Vector3(-0.15, 0.16, 0.10)))
	root.add_child(_build_limb("Boot_R", boot, 0.095, 0.24, Vector3(0.15, 0.16, 0.10)))

	var sword_mesh := BoxMesh.new()
	sword_mesh.size = Vector3(0.04, 0.58, 0.05)
	var sword = _mesh_instance(sword_mesh, _mat(Color(0.67, 0.65, 0.62), 0.34, 0.25), Vector3(0.46, 0.78, -0.02), Vector3(0.0, 0.0, -35.0))
	sword.name = "Sword"
	root.add_child(sword)

	return root

static func create_model(appearance_key: String) -> Node3D:
	var normalized = appearance_key.strip_edges().to_lower()
	if normalized.is_empty():
		normalized = "human_male"

	var model = _load_generated_scene(normalized)
	if model == null:
		model = _build_procedural_model(normalized)
	_set_cast_shadows(model)
	_normalize_and_ground_model(model)
	_ensure_animation_set(model)
	play_animation(model, "idle", 0.0)
	return model

static func create_environment_asset(asset_key: String) -> Node3D:
	var normalized = asset_key.strip_edges().to_lower()
	var generated = _load_generated_scene(normalized)
	if generated != null:
		_set_cast_shadows(generated)
		return generated
	match normalized:
		"ground_stone_a":
			return build_ground(2.0)
		"foliage_grass_a":
			return build_grass_tuft(0)
		"foliage_tree_dead_a":
			var tree := Node3D.new()
			var trunk_mesh := CylinderMesh.new()
			trunk_mesh.height = 2.9
			trunk_mesh.bottom_radius = 0.25
			trunk_mesh.top_radius = 0.11
			var trunk = _mesh_instance(trunk_mesh, _mat(Color(0.30, 0.23, 0.16), 0.9), Vector3(0.0, 1.45, 0.0))
			trunk.name = "Trunk"
			tree.add_child(trunk)
			return tree
		_:
			return null

static func direction_to_rotation_y(direction: String) -> float:
	var normalized = direction.strip_edges().to_upper()
	var index = DIRECTIONS.find(normalized)
	if index < 0:
		index = 0
	# S=0, SW=45, W=90, NW=135, N=180, NE=225, E=270, SE=315
	return float(index) * 45.0

static func build_ground(size: float = 8.0) -> MeshInstance3D:
	var plane_mesh := PlaneMesh.new()
	plane_mesh.size = Vector2(size, size)
	var mat = _mat(Color(0.14, 0.16, 0.14), 0.96)
	var ground = _mesh_instance(plane_mesh, mat, Vector3(0.0, 0.0, 0.0), Vector3(-90.0, 0.0, 0.0))
	ground.name = "Ground"
	return ground

static func build_grass_tuft(seed: int = 0) -> Node3D:
	var tuft := Node3D.new()
	tuft.name = "GrassTuft_%d" % seed
	var blade_mat = _mat(Color(0.18, 0.34, 0.19), 0.86)
	var blade_mesh := BoxMesh.new()
	blade_mesh.size = Vector3(0.04, 0.20, 0.01)
	for idx in range(3):
		var blade = _mesh_instance(blade_mesh, blade_mat, Vector3(0.0, 0.10, 0.0), Vector3(0.0, float(seed * 13 + idx * 62), float(-8 + idx * 8)))
		blade.position.x = (float(idx) - 1.0) * 0.03
		tuft.add_child(blade)
	return tuft
