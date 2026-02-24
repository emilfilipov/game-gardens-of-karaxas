extends PanelContainer
class_name CharacterPodiumPreview

signal direction_changed(direction: String)

const DIRECTIONS: Array[String] = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]

var _loader: Callable
var _appearance_key: String = "human_male"
var _direction_index: int = 0
var _drag_active: bool = false
var _drag_anchor_x: float = 0.0
var _drag_threshold: float = 18.0
var _reduced_motion: bool = false
var _idle_phase: float = 0.0
var _lighting_profile: String = "warm_torchlight"
var _show_controls: bool = true
var _show_title: bool = true
var _interactive: bool = true
var _world_scale_mode: bool = false
var _display_scale: float = 1.0

var _title_label: Label
var _texture: TextureRect
var _direction_label: Label
var _rotate_left: Button
var _rotate_right: Button
var _controls_row: HBoxContainer

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build_ui()
	_refresh_texture()
	set_process(true)

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
	_display_scale = 0.33 if _world_scale_mode else 1.0
	mouse_filter = Control.MOUSE_FILTER_STOP if _interactive else Control.MOUSE_FILTER_IGNORE
	if _controls_row != null:
		_controls_row.visible = _show_controls
	if _title_label != null and not _show_title:
		_title_label.visible = false
	_refresh_texture()

func set_reduced_motion(enabled: bool) -> void:
	_reduced_motion = enabled

func set_character(appearance_key: String, title: String = "") -> void:
	_appearance_key = appearance_key.strip_edges().to_lower()
	if _appearance_key.is_empty():
		_appearance_key = "human_male"
	if _title_label != null:
		_title_label.visible = _show_title and not title.is_empty()
		_title_label.text = title
	_refresh_texture()

func set_direction(direction: String) -> void:
	var normalized = direction.strip_edges().to_upper()
	var index = DIRECTIONS.find(normalized)
	if index < 0:
		return
	_direction_index = index
	_refresh_texture()
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
	var total = DIRECTIONS.size()
	_direction_index = int(posmod(_direction_index + delta, total))
	_refresh_texture()
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

	var preview_shell = PanelContainer.new()
	preview_shell.size_flags_vertical = Control.SIZE_EXPAND_FILL
	preview_shell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	preview_shell.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	root.add_child(preview_shell)

	_texture = TextureRect.new()
	_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	preview_shell.add_child(_texture)

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

func _process(delta: float) -> void:
	if _texture == null:
		return
	if _reduced_motion:
		_texture.scale = Vector2.ONE * _display_scale
		return
	_idle_phase += delta
	var pulse: float = 1.0 + sin(_idle_phase * 1.35) * 0.015
	_texture.scale = Vector2(pulse, pulse) * _display_scale

func _refresh_texture() -> void:
	if _texture == null:
		return
	var direction = DIRECTIONS[_direction_index]
	if _direction_label != null:
		_direction_label.text = "Facing: " + direction
	var texture: Texture2D = null
	if _loader.is_valid():
		var value = _loader.call(_appearance_key, direction)
		if value is Texture2D:
			texture = value
		if texture == null:
			value = _loader.call(_appearance_key, "S")
			if value is Texture2D:
				texture = value
		if texture == null:
			value = _loader.call("human_male", "S")
			if value is Texture2D:
				texture = value
	_texture.texture = texture
	_apply_lighting_profile()

func _apply_lighting_profile() -> void:
	if _texture == null:
		return
	match _lighting_profile:
		"neutral_daylight":
			_texture.modulate = Color(0.95, 0.97, 1.0, 1.0)
		"grim_dusk":
			_texture.modulate = Color(0.78, 0.72, 0.84, 1.0)
		_:
			_texture.modulate = Color(1.0, 0.95, 0.88, 1.0)
