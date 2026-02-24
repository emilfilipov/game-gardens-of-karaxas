extends RefCounted
class_name Sellsword3DFactory

const DIRECTIONS: Array[String] = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]

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
	skull_mesh.radial_segments = 24
	skull_mesh.rings = 12
	root.add_child(_mesh_instance(skull_mesh, skin, Vector3(0.0, 1.45, 0.0)))

	var hair_mesh := SphereMesh.new()
	hair_mesh.radius = 0.19
	hair_mesh.height = 0.22 if is_female else 0.20
	hair_mesh.radial_segments = 18
	hair_mesh.rings = 8
	root.add_child(_mesh_instance(hair_mesh, hair, Vector3(0.0, 1.53, 0.01)))

	if is_female:
		var ponytail_mesh := CapsuleMesh.new()
		ponytail_mesh.radius = 0.045
		ponytail_mesh.height = 0.28
		ponytail_mesh.radial_segments = 10
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
	cloak_mesh.radial_segments = 18
	root.add_child(_mesh_instance(cloak_mesh, cloak, Vector3(0.0, 1.02, -0.08), Vector3(0.0, 0.0, 0.0)))

	var torso_mesh := CapsuleMesh.new()
	torso_mesh.radius = 0.25 if is_female else 0.27
	torso_mesh.height = 0.78 if is_female else 0.82
	torso_mesh.radial_segments = 20
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

static func _build_limb(material: Material, radius: float, length: float, position: Vector3) -> MeshInstance3D:
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = length
	mesh.radial_segments = 14
	return _mesh_instance(mesh, material, position)

static func create_model(appearance_key: String) -> Node3D:
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

	root.add_child(_build_limb(cloth, 0.075, 0.48, Vector3(-0.36, 1.01, 0.02)))
	root.add_child(_build_limb(cloth, 0.075, 0.48, Vector3(0.36, 1.01, 0.02)))
	root.add_child(_build_limb(skin, 0.066, 0.32, Vector3(-0.36, 0.79, 0.06)))
	root.add_child(_build_limb(skin, 0.066, 0.32, Vector3(0.36, 0.79, 0.06)))

	root.add_child(_build_limb(cloth, 0.090 if is_female else 0.095, 0.56, Vector3(-0.15, 0.46, 0.02)))
	root.add_child(_build_limb(cloth, 0.090 if is_female else 0.095, 0.56, Vector3(0.15, 0.46, 0.02)))
	root.add_child(_build_limb(boot, 0.095, 0.24, Vector3(-0.15, 0.16, 0.10)))
	root.add_child(_build_limb(boot, 0.095, 0.24, Vector3(0.15, 0.16, 0.10)))

	var sword_mesh := BoxMesh.new()
	sword_mesh.size = Vector3(0.04, 0.58, 0.05)
	var sword = _mesh_instance(sword_mesh, _mat(Color(0.67, 0.65, 0.62), 0.34, 0.25), Vector3(0.46, 0.78, -0.02), Vector3(0.0, 0.0, -35.0))
	root.add_child(sword)

	return root

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
