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
var _preview_shell: PanelContainer
var _texture: TextureRect
var _ground_strip: ColorRect
var _ground_anchor: ColorRect
var _ground_shadow: PanelContainer
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
	_apply_preview_surface_style()
	_layout_preview_surface(1.0)
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

	_preview_shell = PanelContainer.new()
	_preview_shell.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_preview_shell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root.add_child(_preview_shell)
	_preview_shell.resized.connect(func() -> void:
		_layout_preview_surface(1.0)
	)

	_ground_strip = ColorRect.new()
	_ground_strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_preview_shell.add_child(_ground_strip)

	_ground_shadow = PanelContainer.new()
	var shadow_style = StyleBoxFlat.new()
	shadow_style.bg_color = Color(0.0, 0.0, 0.0, 0.36)
	shadow_style.corner_radius_top_left = 128
	shadow_style.corner_radius_top_right = 128
	shadow_style.corner_radius_bottom_left = 128
	shadow_style.corner_radius_bottom_right = 128
	_ground_shadow.add_theme_stylebox_override("panel", shadow_style)
	_ground_shadow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_preview_shell.add_child(_ground_shadow)

	_ground_anchor = ColorRect.new()
	_ground_anchor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_preview_shell.add_child(_ground_anchor)

	_texture = TextureRect.new()
	_texture.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_texture.stretch_mode = TextureRect.STRETCH_SCALE
	_texture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_preview_shell.add_child(_texture)
	_apply_preview_surface_style()

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
	var pulse: float = 1.0
	if _reduced_motion:
		_layout_preview_surface(1.0)
		return
	_idle_phase += delta
	pulse = 1.0 + sin(_idle_phase * 1.35) * 0.015
	_layout_preview_surface(pulse)

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
	_layout_preview_surface(1.0)
	_apply_lighting_profile()

func _apply_preview_surface_style() -> void:
	if _preview_shell == null:
		return
	var style = StyleBoxFlat.new()
	if _world_scale_mode:
		style.bg_color = Color(0.03, 0.03, 0.04, 0.78)
		style.border_color = Color(0.75, 0.59, 0.37, 0.75)
		style.border_width_left = 1
		style.border_width_top = 1
		style.border_width_right = 1
		style.border_width_bottom = 1
		style.corner_radius_top_left = 8
		style.corner_radius_top_right = 8
		style.corner_radius_bottom_left = 8
		style.corner_radius_bottom_right = 8
	else:
		style.bg_color = Color(0.01, 0.01, 0.01, 0.18)
		style.corner_radius_top_left = 6
		style.corner_radius_top_right = 6
		style.corner_radius_bottom_left = 6
		style.corner_radius_bottom_right = 6
	_preview_shell.add_theme_stylebox_override("panel", style)

func _layout_preview_surface(animation_scale: float) -> void:
	if _preview_shell == null or _texture == null:
		return
	var shell_size = _preview_shell.size
	if shell_size.x <= 1.0 or shell_size.y <= 1.0:
		return

	var strip_height = maxf(28.0, shell_size.y * (0.16 if _world_scale_mode else 0.13))
	if _ground_strip != null:
		_ground_strip.color = Color(0.02, 0.02, 0.03, 0.56) if _world_scale_mode else Color(0.04, 0.03, 0.03, 0.34)
		_ground_strip.position = Vector2(8.0, shell_size.y - strip_height - 8.0)
		_ground_strip.size = Vector2(maxf(1.0, shell_size.x - 16.0), strip_height)

	var texture = _texture.texture
	if texture == null:
		if _ground_shadow != null:
			_ground_shadow.visible = false
		if _ground_anchor != null:
			_ground_anchor.visible = false
		_texture.visible = false
		return
	_texture.visible = true

	var margin_x = 12.0
	var top_pad = 8.0
	var bottom_pad = 12.0
	var avail_w = maxf(8.0, shell_size.x - margin_x * 2.0)
	var avail_h = maxf(8.0, shell_size.y - top_pad - bottom_pad)
	var tex_w = float(texture.get_width())
	var tex_h = float(texture.get_height())
	if tex_w <= 0.0 or tex_h <= 0.0:
		return
	var fit = minf(avail_w / tex_w, avail_h / tex_h)
	var draw_w = maxf(1.0, tex_w * fit * _display_scale * animation_scale)
	var draw_h = maxf(1.0, tex_h * fit * _display_scale * animation_scale)
	var baseline_y = shell_size.y - 18.0
	var foot_ratio = 0.86
	var draw_x = (shell_size.x - draw_w) * 0.5
	var draw_y = baseline_y - draw_h * foot_ratio
	if draw_y < top_pad:
		draw_y = top_pad

	_texture.position = Vector2(draw_x, draw_y)
	_texture.size = Vector2(draw_w, draw_h)

	var anchor_width = maxf(56.0, draw_w * 0.54)
	if _ground_anchor != null:
		_ground_anchor.visible = true
		_ground_anchor.color = Color(0.86, 0.72, 0.48, 0.52) if _world_scale_mode else Color(0.85, 0.69, 0.45, 0.32)
		_ground_anchor.position = Vector2((shell_size.x - anchor_width) * 0.5, baseline_y)
		_ground_anchor.size = Vector2(anchor_width, 1.0)

	if _ground_shadow != null:
		_ground_shadow.visible = true
		var shadow_w = maxf(32.0, draw_w * (0.58 if _world_scale_mode else 0.5))
		var shadow_h = maxf(10.0, draw_h * 0.08)
		_ground_shadow.position = Vector2((shell_size.x - shadow_w) * 0.5, baseline_y + 2.0)
		_ground_shadow.size = Vector2(shadow_w, shadow_h)

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
