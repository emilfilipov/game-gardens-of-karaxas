extends PanelContainer
class_name CharacterPodiumPreview3D

signal direction_changed(direction: String)

const DIRECTIONS: Array[String] = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
const SELLSWORD_FACTORY = preload("res://scripts/sellsword_3d_factory.gd")

var _loader: Callable
var _appearance_key: String = ""
var _direction_index: int = 0
var _drag_active: bool = false
var _drag_anchor_x: float = 0.0
var _drag_threshold: float = 18.0
var _reduced_motion: bool = false
var _lighting_profile: String = "warm_torchlight"
var _show_controls: bool = true
var _show_title: bool = true
var _interactive: bool = true
var _world_scale_mode: bool = false

var _title_label: Label
var _viewport_shell: PanelContainer
var _viewport: SubViewport
var _world_root: Node3D
var _camera: Camera3D
var _key_light: DirectionalLight3D
var _fill_light: OmniLight3D
var _ground: MeshInstance3D
var _character_root: Node3D
var _character_model: Node3D
var _direction_label: Label
var _rotate_left: Button
var _rotate_right: Button
var _controls_row: HBoxContainer

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build_ui()
	_set_character_internal("")
	set_process(false)

func configure(
	loader: Callable,
	reduced_motion: bool,
	show_controls: bool = true,
	show_title: bool = true,
	interactive: bool = true,
	world_scale_mode: bool = false
) -> void:
	_loader = loader
	_reduced_motion = reduced_motion
	_show_controls = show_controls
	_show_title = show_title
	_interactive = interactive
	_world_scale_mode = world_scale_mode
	mouse_filter = Control.MOUSE_FILTER_STOP if _interactive else Control.MOUSE_FILTER_IGNORE
	if _controls_row != null:
		_controls_row.visible = _show_controls
	if _title_label != null:
		_title_label.visible = _show_title and not _title_label.text.is_empty()
	_apply_shell_style()
	_update_camera_pose()
	_apply_lighting_profile()

func set_reduced_motion(enabled: bool) -> void:
	_reduced_motion = enabled

func set_character(appearance_key: String, title: String = "") -> void:
	if _title_label != null:
		_title_label.text = title
		_title_label.visible = _show_title and not title.is_empty()
	_set_character_internal(appearance_key)

func clear_character() -> void:
	_set_character_internal("")
	if _title_label != null:
		_title_label.visible = false
		_title_label.text = ""

func set_direction(direction: String) -> void:
	var normalized = direction.strip_edges().to_upper()
	var index = DIRECTIONS.find(normalized)
	if index < 0:
		return
	_direction_index = index
	_apply_direction()
	emit_signal("direction_changed", DIRECTIONS[_direction_index])

func set_lighting_profile(profile: String) -> void:
	_lighting_profile = profile.strip_edges().to_lower()
	if _lighting_profile.is_empty():
		_lighting_profile = "warm_torchlight"
	_apply_lighting_profile()

func current_direction() -> String:
	return DIRECTIONS[_direction_index]

func rotate_by(delta: int) -> void:
	if DIRECTIONS.is_empty():
		return
	_direction_index = int(posmod(_direction_index + delta, DIRECTIONS.size()))
	_apply_direction()
	emit_signal("direction_changed", DIRECTIONS[_direction_index])

func _build_ui() -> void:
	add_theme_stylebox_override("panel", StyleBoxEmpty.new())

	var root = VBoxContainer.new()
	root.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_theme_constant_override("separation", 8)
	add_child(root)

	_title_label = Label.new()
	_title_label.text = ""
	_title_label.visible = false
	_title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_label.add_theme_font_size_override("font_size", 18)
	root.add_child(_title_label)

	_viewport_shell = PanelContainer.new()
	_viewport_shell.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_viewport_shell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root.add_child(_viewport_shell)

	var viewport_container = SubViewportContainer.new()
	viewport_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	viewport_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	viewport_container.stretch = true
	viewport_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_viewport_shell.add_child(viewport_container)

	_viewport = SubViewport.new()
	_viewport.disable_3d = false
	_viewport.usage = SubViewport.USAGE_3D
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
	_viewport.transparent_bg = true
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport_container.add_child(_viewport)

	_world_root = Node3D.new()
	_world_root.name = "PreviewWorld"
	_viewport.add_child(_world_root)

	var env = WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.03, 0.03, 0.04, 1.0)
	environment.ambient_light_color = Color(0.55, 0.54, 0.50)
	environment.ambient_light_energy = 0.75
	environment.ssr_enabled = false
	environment.ssil_enabled = false
	env.environment = environment
	_world_root.add_child(env)

	_ground = SELLSWORD_FACTORY.build_ground(7.2)
	_world_root.add_child(_ground)

	var shadow_mesh := CylinderMesh.new()
	shadow_mesh.top_radius = 0.52
	shadow_mesh.bottom_radius = 0.52
	shadow_mesh.height = 0.02
	shadow_mesh.radial_segments = 24
	var shadow_mat := StandardMaterial3D.new()
	shadow_mat.albedo_color = Color(0.0, 0.0, 0.0, 0.26)
	shadow_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var shadow = MeshInstance3D.new()
	shadow.mesh = shadow_mesh
	shadow.material_override = shadow_mat
	shadow.position = Vector3(0.0, 0.03, 0.0)
	_world_root.add_child(shadow)

	_key_light = DirectionalLight3D.new()
	_key_light.light_color = Color(1.0, 0.90, 0.78)
	_key_light.light_energy = 1.45
	_key_light.shadow_enabled = true
	_key_light.rotation_degrees = Vector3(-55.0, 35.0, 0.0)
	_world_root.add_child(_key_light)

	_fill_light = OmniLight3D.new()
	_fill_light.light_color = Color(0.48, 0.56, 0.78)
	_fill_light.light_energy = 0.35
	_fill_light.omni_range = 6.0
	_fill_light.position = Vector3(-1.4, 1.1, -1.1)
	_world_root.add_child(_fill_light)

	_character_root = Node3D.new()
	_character_root.name = "CharacterRoot"
	_world_root.add_child(_character_root)

	_camera = Camera3D.new()
	_camera.current = true
	_camera.near = 0.05
	_camera.far = 80.0
	_camera.fov = 34.0
	_world_root.add_child(_camera)

	_controls_row = HBoxContainer.new()
	_controls_row.add_theme_constant_override("separation", 8)
	_controls_row.visible = _show_controls
	root.add_child(_controls_row)
	_controls_row.add_spacer(false)

	_rotate_left = Button.new()
	_rotate_left.text = "<"
	_rotate_left.custom_minimum_size = Vector2(56, 36)
	_rotate_left.pressed.connect(func() -> void:
		rotate_by(-1)
	)
	_controls_row.add_child(_rotate_left)

	_direction_label = Label.new()
	_direction_label.text = "Facing: S"
	_direction_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_direction_label.custom_minimum_size = Vector2(130, 32)
	_controls_row.add_child(_direction_label)

	_rotate_right = Button.new()
	_rotate_right.text = ">"
	_rotate_right.custom_minimum_size = Vector2(56, 36)
	_rotate_right.pressed.connect(func() -> void:
		rotate_by(1)
	)
	_controls_row.add_child(_rotate_right)
	_controls_row.add_spacer(false)

	_viewport_shell.resized.connect(_on_shell_resized)
	_apply_shell_style()
	_update_camera_pose()

func _on_shell_resized() -> void:
	if _viewport == null or _viewport_shell == null:
		return
	var size = _viewport_shell.size
	_viewport.size = Vector2i(maxi(1, int(size.x)), maxi(1, int(size.y)))

func _apply_shell_style() -> void:
	if _viewport_shell == null:
		return
	var style := StyleBoxFlat.new()
	if _world_scale_mode:
		style.bg_color = Color(0.03, 0.03, 0.04, 0.85)
		style.border_color = Color(0.75, 0.59, 0.37, 0.78)
		style.border_width_left = 1
		style.border_width_top = 1
		style.border_width_right = 1
		style.border_width_bottom = 1
		style.corner_radius_top_left = 8
		style.corner_radius_top_right = 8
		style.corner_radius_bottom_left = 8
		style.corner_radius_bottom_right = 8
	else:
		style.bg_color = Color(0.01, 0.01, 0.01, 0.20)
		style.corner_radius_top_left = 6
		style.corner_radius_top_right = 6
		style.corner_radius_bottom_left = 6
		style.corner_radius_bottom_right = 6
	_viewport_shell.add_theme_stylebox_override("panel", style)

func _update_camera_pose() -> void:
	if _camera == null:
		return
	if _world_scale_mode:
		_camera.position = Vector3(0.0, 1.75, 2.6)
		_camera.fov = 40.0
	else:
		_camera.position = Vector3(0.0, 1.95, 2.95)
		_camera.fov = 34.0
	_camera.look_at(Vector3(0.0, 0.95, 0.0), Vector3.UP)

func _set_character_internal(appearance_key: String) -> void:
	_appearance_key = appearance_key.strip_edges().to_lower()
	if _character_model != null:
		_character_model.queue_free()
		_character_model = null
	if _appearance_key.is_empty():
		return
	_character_model = SELLSWORD_FACTORY.create_model(_appearance_key)
	_character_root.add_child(_character_model)
	if _world_scale_mode:
		_character_model.scale = Vector3.ONE * 0.36
	SELSWORD_FACTORY.play_animation(_character_model, "idle", 0.0)
	_apply_direction()

func _apply_direction() -> void:
	if _direction_label != null:
		_direction_label.text = "Facing: " + DIRECTIONS[_direction_index]
	if _character_model == null:
		return
	_character_model.rotation_degrees = Vector3(0.0, SELLSWORD_FACTORY.direction_to_rotation_y(DIRECTIONS[_direction_index]), 0.0)

func _apply_lighting_profile() -> void:
	if _key_light == null:
		return
	match _lighting_profile:
		"neutral_daylight":
			_key_light.light_color = Color(0.96, 0.98, 1.0)
			_key_light.light_energy = 1.3
		"grim_dusk":
			_key_light.light_color = Color(0.72, 0.76, 0.92)
			_key_light.light_energy = 1.1
		_:
			_key_light.light_color = Color(1.0, 0.90, 0.78)
			_key_light.light_energy = 1.45

func _gui_input(event: InputEvent) -> void:
	if not _interactive:
		return
	if event is InputEventMouseButton:
		var button_event: InputEventMouseButton = event
		if button_event.button_index == MOUSE_BUTTON_LEFT:
			_drag_active = button_event.pressed
			_drag_anchor_x = button_event.position.x
	if event is InputEventMouseMotion and _drag_active:
		var motion: InputEventMouseMotion = event
		var delta_x: float = motion.position.x - _drag_anchor_x
		if absf(delta_x) >= _drag_threshold:
			rotate_by(1 if delta_x > 0.0 else -1)
			_drag_anchor_x = motion.position.x
