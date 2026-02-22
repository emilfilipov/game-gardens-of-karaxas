extends Control

const WORLD_CANVAS_SCENE = preload("res://scripts/world_canvas.gd")
const UI_TOKENS = preload("res://scripts/ui_tokens.gd")
const UI_COMPONENTS = preload("res://scripts/ui_components.gd")
const PODIUM_PREVIEW_SCENE = preload("res://scripts/character_podium_preview.gd")

const MENU_NEW_GAME = "new_game"
const MENU_LOAD_GAME = "load_game"
const MENU_SETTINGS = "settings"
const MENU_UPDATE = "update"
const MENU_ADMIN = "admin"
const MENU_EXIT = "exit"

const DEFAULT_CONFIG = "res://assets/config/game_config.json"

var ui_theme = null
var current_screen = "main_menu"
var screen_nodes = {}

var install_root_path = ""
var logs_root_path = ""
var prefs_path = ""
var user_config_path = ""
var saves_index_path = ""
var saves_root_path = ""
var levels_root_path = ""

var game_config = {}
var game_settings = {}
var client_version = "0.0.0"
var footer_version_text = ""

var active_save = {}
var active_slot_id = -1
var world_active = false

var background_art = null
var background_veil = null
var header_title = null
var footer_status = null
var main_stack = null

var main_menu_container = null
var menu_status_label = null

var create_container = null
var create_name_input = null
var create_sex_option = null
var create_race_option = null
var create_background_option = null
var create_affiliation_option = null
var create_preview_widget = null
var create_points_label = null
var create_stats_grid = null
var create_skills_grid = null
var create_status_label = null
var create_budget = 10
var create_stat_values = {}
var create_skill_values = {}
var create_skill_buttons = {}
var create_stat_keys = []
var create_skill_keys = []

var load_container = null
var load_list = null
var load_status_label = null
var load_preview_label = null

var settings_container = null
var settings_status_label = null
var settings_screen_mode = null
var settings_audio_mute = null
var settings_audio_volume = null
var settings_autosave_interval = null
var settings_reduced_motion = null
var settings_difficulty_option = null

var admin_container = null
var admin_status_label = null
var admin_tabs = null

var admin_level_option = null
var admin_level_id_input = null
var admin_level_name_input = null
var admin_level_width_input = null
var admin_level_height_input = null
var admin_level_spawn_x_input = null
var admin_level_spawn_y_input = null
var admin_level_layers_input = null
var admin_level_objects_input = null
var admin_level_transitions_input = null

var admin_asset_list = null
var admin_asset_payload = null
var admin_asset_status = null
var admin_asset_selected_index = -1

var admin_config_text = null
var admin_config_status = null

var admin_diag_text = null

var world_container = null
var world_canvas = null
var world_status_label = null

var character_texture_cache = {}

func _ready() -> void:
	_resolve_paths()
	_append_log("Single-player shell startup.")
	_apply_default_window_mode()
	_load_client_version()
	_build_theme()
	_build_ui()
	_ensure_default_config_exists()
	_load_game_config()
	_load_settings()
	_refresh_create_from_config()
	_refresh_load_game_list()
	_refresh_admin_panels()
	_show_screen("main_menu")
	_set_status("Ready.")

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if world_active:
			_save_active_slot(false)
		get_tree().quit()

func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey):
		return
	var key_event = event
	if not key_event.pressed or key_event.echo:
		return
	if key_event.keycode == KEY_ESCAPE:
		if current_screen == "world":
			_save_active_slot(false)
			_exit_world_to_main_menu()
			accept_event()
		elif current_screen != "main_menu":
			_show_screen("main_menu")
			accept_event()
	elif key_event.keycode == KEY_ENTER or key_event.keycode == KEY_KP_ENTER:
		if current_screen == "create":
			_on_create_character_pressed()
			accept_event()

func _build_theme() -> void:
	ui_theme = Theme.new()

	var panel_box = StyleBoxFlat.new()
	panel_box.bg_color = UI_TOKENS.color("panel_bg")
	panel_box.border_width_left = 1
	panel_box.border_width_top = 1
	panel_box.border_width_right = 1
	panel_box.border_width_bottom = 1
	panel_box.border_color = UI_TOKENS.color("panel_border")
	panel_box.corner_radius_top_left = UI_TOKENS.size("radius_xl")
	panel_box.corner_radius_top_right = UI_TOKENS.size("radius_xl")
	panel_box.corner_radius_bottom_left = UI_TOKENS.size("radius_xl")
	panel_box.corner_radius_bottom_right = UI_TOKENS.size("radius_xl")

	var panel_box_alt = panel_box.duplicate()
	panel_box_alt.bg_color = UI_TOKENS.color("panel_bg_alt")

	var button_normal = panel_box_alt.duplicate()
	button_normal.corner_radius_top_left = UI_TOKENS.size("radius")
	button_normal.corner_radius_top_right = UI_TOKENS.size("radius")
	button_normal.corner_radius_bottom_left = UI_TOKENS.size("radius")
	button_normal.corner_radius_bottom_right = UI_TOKENS.size("radius")
	var button_hover = button_normal.duplicate()
	button_hover.bg_color = UI_TOKENS.color("button_hover")
	var button_pressed = button_normal.duplicate()
	button_pressed.bg_color = UI_TOKENS.color("button_pressed")

	var input_box = panel_box.duplicate()
	input_box.bg_color = UI_TOKENS.color("panel_bg_deep")
	input_box.border_color = UI_TOKENS.color("panel_border_soft")
	input_box.corner_radius_top_left = UI_TOKENS.size("radius")
	input_box.corner_radius_top_right = UI_TOKENS.size("radius")
	input_box.corner_radius_bottom_left = UI_TOKENS.size("radius")
	input_box.corner_radius_bottom_right = UI_TOKENS.size("radius")
	var input_focus = input_box.duplicate()
	input_focus.border_color = UI_TOKENS.color("panel_border")

	ui_theme.set_stylebox("panel", "PanelContainer", panel_box)
	ui_theme.set_stylebox("panel", "PopupPanel", panel_box_alt)
	ui_theme.set_stylebox("normal", "Button", button_normal)
	ui_theme.set_stylebox("hover", "Button", button_hover)
	ui_theme.set_stylebox("pressed", "Button", button_pressed)
	ui_theme.set_stylebox("focus", "Button", button_normal)
	ui_theme.set_color("font_color", "Button", UI_TOKENS.color("text_primary"))
	ui_theme.set_color("font_hover_color", "Button", UI_TOKENS.color("text_primary"))
	ui_theme.set_color("font_pressed_color", "Button", UI_TOKENS.color("text_primary"))
	ui_theme.set_constant("outline_size", "Button", 0)

	ui_theme.set_stylebox("normal", "LineEdit", input_box)
	ui_theme.set_stylebox("focus", "LineEdit", input_focus)
	ui_theme.set_stylebox("read_only", "LineEdit", input_box)
	ui_theme.set_color("font_color", "LineEdit", UI_TOKENS.color("text_primary"))
	ui_theme.set_color("font_placeholder_color", "LineEdit", UI_TOKENS.color("text_muted"))
	ui_theme.set_constant("outline_size", "LineEdit", 0)

	ui_theme.set_stylebox("normal", "TextEdit", input_box)
	ui_theme.set_stylebox("focus", "TextEdit", input_focus)
	ui_theme.set_color("font_color", "TextEdit", UI_TOKENS.color("text_primary"))
	ui_theme.set_constant("outline_size", "TextEdit", 0)

	ui_theme.set_stylebox("normal", "ItemList", input_box)
	ui_theme.set_stylebox("focus", "ItemList", input_focus)
	ui_theme.set_color("font_color", "ItemList", UI_TOKENS.color("text_primary"))
	ui_theme.set_color("font_selected_color", "ItemList", UI_TOKENS.color("selection_text"))
	ui_theme.set_color("selection_fill", "ItemList", UI_TOKENS.color("selection_fill"))

	ui_theme.set_stylebox("normal", "OptionButton", button_normal)
	ui_theme.set_stylebox("hover", "OptionButton", button_hover)
	ui_theme.set_stylebox("pressed", "OptionButton", button_pressed)
	ui_theme.set_stylebox("focus", "OptionButton", button_pressed)
	ui_theme.set_color("font_color", "OptionButton", UI_TOKENS.color("text_primary"))
	ui_theme.set_constant("outline_size", "OptionButton", 0)

	ui_theme.set_stylebox("panel", "TabContainer", panel_box)
	ui_theme.set_stylebox("tab_unselected", "TabBar", button_normal)
	ui_theme.set_stylebox("tab_hovered", "TabBar", button_hover)
	ui_theme.set_stylebox("tab_selected", "TabBar", button_pressed)
	ui_theme.set_color("font_selected_color", "TabBar", UI_TOKENS.color("text_primary"))
	ui_theme.set_color("font_unselected_color", "TabBar", UI_TOKENS.color("text_muted"))
	ui_theme.set_constant("outline_size", "TabBar", 0)

	ui_theme.set_color("font_color", "Label", UI_TOKENS.color("text_primary"))
	ui_theme.set_color("font_color", "RichTextLabel", UI_TOKENS.color("text_primary"))

	theme = ui_theme

func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS

	background_art = TextureRect.new()
	background_art.set_anchors_preset(Control.PRESET_FULL_RECT)
	background_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	background_art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	background_art.texture = _load_texture("res://assets/main_menu_background.png")
	if background_art.texture == null:
		background_art.texture = _load_texture(_path_join(install_root_path, "game-client/assets/main_menu_background.png"))
	add_child(background_art)

	background_veil = ColorRect.new()
	background_veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	background_veil.color = UI_TOKENS.color("veil")
	add_child(background_veil)

	var root = MarginContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("margin_left", 20)
	root.add_theme_constant_override("margin_top", 12)
	root.add_theme_constant_override("margin_right", 20)
	root.add_theme_constant_override("margin_bottom", 14)
	add_child(root)

	var layout = VBoxContainer.new()
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	root.add_child(layout)

	var header = HBoxContainer.new()
	layout.add_child(header)

	var left_pad = Control.new()
	left_pad.custom_minimum_size = Vector2(44, 44)
	header.add_child(left_pad)

	header_title = Label.new()
	header_title.text = "Gardens of Karaxas"
	header_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	header_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_title.add_theme_font_size_override("font_size", 46)
	header.add_child(header_title)

	var right_pad = Control.new()
	right_pad.custom_minimum_size = Vector2(44, 44)
	header.add_child(right_pad)

	main_stack = Control.new()
	main_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_stack.set_anchors_preset(Control.PRESET_FULL_RECT)
	layout.add_child(main_stack)

	_register_screen("main_menu", _build_main_menu_screen())
	_register_screen("create", _build_create_screen())
	_register_screen("load", _build_load_screen())
	_register_screen("settings", _build_settings_screen())
	_register_screen("admin", _build_admin_screen())
	_register_screen("world", _build_world_screen())

	footer_status = Label.new()
	footer_status.text = footer_version_text
	footer_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	footer_status.add_theme_font_size_override("font_size", 12)
	footer_status.add_theme_color_override("font_color", UI_TOKENS.color("text_muted"))
	layout.add_child(footer_status)

func _register_screen(name: String, node: Control) -> void:
	node.set_anchors_preset(Control.PRESET_FULL_RECT)
	node.offset_left = 0
	node.offset_top = 0
	node.offset_right = 0
	node.offset_bottom = 0
	main_stack.add_child(node)
	screen_nodes[name] = node

func _show_screen(name: String) -> void:
	current_screen = name
	for key in screen_nodes.keys():
		var node = screen_nodes.get(key)
		if node is Control:
			node.visible = str(key) == name
	if world_canvas != null and world_canvas.has_method("set_active"):
		world_canvas.call("set_active", name == "world")
	if background_art != null:
		background_art.visible = name != "world"
	if background_veil != null:
		background_veil.visible = name != "world"
	if header_title != null:
		header_title.text = "" if name == "world" else "Gardens of Karaxas"
	if name == "load":
		_refresh_load_game_list()
	if name == "admin":
		_refresh_admin_panels()

func _build_main_menu_screen() -> Control:
	var shell = UI_COMPONENTS.centered_shell(Vector2(560, 620), UI_TOKENS.spacing("lg"))
	var wrap = shell["wrap"]
	var content = shell["content"]

	var title = _label("Main Menu", 34)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	content.add_child(title)
	content.add_child(_label("Single-player isometric ARPG", -1, "text_secondary"))

	var button_col = VBoxContainer.new()
	button_col.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	button_col.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(button_col)

	button_col.add_child(_main_menu_button("New Game", MENU_NEW_GAME))
	button_col.add_child(_main_menu_button("Load Game", MENU_LOAD_GAME))
	button_col.add_child(_main_menu_button("Settings", MENU_SETTINGS))
	button_col.add_child(_main_menu_button("Update", MENU_UPDATE))
	button_col.add_child(_main_menu_button("Admin", MENU_ADMIN))
	button_col.add_child(_main_menu_button("Exit", MENU_EXIT))
	button_col.add_spacer(false)

	menu_status_label = _label(" ", -1, "text_secondary")
	menu_status_label.text = " "
	menu_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(menu_status_label)

	main_menu_container = wrap
	return wrap

func _main_menu_button(label_text: String, action: String) -> Button:
	var button = UI_COMPONENTS.button_primary(label_text, Vector2(0, 52))
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(func() -> void:
		_on_main_menu_action(action)
	)
	return button

func _on_main_menu_action(action: String) -> void:
	match action:
		MENU_NEW_GAME:
			_show_screen("create")
		MENU_LOAD_GAME:
			_show_screen("load")
		MENU_SETTINGS:
			_show_screen("settings")
		MENU_UPDATE:
			_on_update_pressed()
		MENU_ADMIN:
			_show_screen("admin")
		MENU_EXIT:
			if world_active:
				_save_active_slot(false)
			get_tree().quit()

func _build_create_screen() -> Control:
	var shell = UI_COMPONENTS.centered_shell(Vector2(1540, 860), UI_TOKENS.spacing("md"))
	var wrap = shell["wrap"]
	var content = shell["content"]

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	content.add_child(top)
	var back = _button("Back to Main Menu")
	back.custom_minimum_size = Vector2(190, 36)
	back.pressed.connect(func() -> void:
		_show_screen("main_menu")
	)
	top.add_child(back)
	top.add_spacer(false)

	var body = HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", UI_TOKENS.spacing("md"))
	content.add_child(body)

	var left = UI_COMPONENTS.panel_card(Vector2(260, 0), false)
	left.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(left)
	var left_col = VBoxContainer.new()
	left_col.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left_col.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	left.add_child(left_col)
	left_col.add_child(_label("Character Setup", 22, "text_secondary"))

	create_name_input = _line_edit("Character Name")
	create_name_input.custom_minimum_size = Vector2(0, 38)
	left_col.add_child(_labeled_control("Name", create_name_input))
	create_sex_option = _option([])
	create_sex_option.item_selected.connect(func(_idx: int) -> void:
		_refresh_create_preview()
	)
	left_col.add_child(_labeled_control("Sex", create_sex_option))
	create_race_option = _option([])
	left_col.add_child(_labeled_control("Race", create_race_option))
	create_background_option = _option([])
	left_col.add_child(_labeled_control("Background", create_background_option))
	create_affiliation_option = _option([])
	left_col.add_child(_labeled_control("Affiliation", create_affiliation_option))
	left_col.add_spacer(false)

	var center = UI_COMPONENTS.panel_card(Vector2(0, 0), true)
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(center)
	create_preview_widget = PODIUM_PREVIEW_SCENE.new()
	create_preview_widget.call("configure", Callable(self, "_resolve_character_texture_directional"), bool(game_settings.get("reduced_motion", false)))
	create_preview_widget.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(create_preview_widget)

	var right = UI_COMPONENTS.panel_card(Vector2(380, 0), false)
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(right)
	var right_col = VBoxContainer.new()
	right_col.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_col.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	right.add_child(right_col)
	var stats_label = _label("Stats", 20, "text_secondary")
	right_col.add_child(stats_label)
	create_stats_grid = GridContainer.new()
	create_stats_grid.columns = 4
	create_stats_grid.add_theme_constant_override("h_separation", UI_TOKENS.spacing("xs"))
	create_stats_grid.add_theme_constant_override("v_separation", UI_TOKENS.spacing("xs"))
	right_col.add_child(create_stats_grid)
	var skill_label = _label("Skills", 20, "text_secondary")
	right_col.add_child(skill_label)
	create_skills_grid = GridContainer.new()
	create_skills_grid.columns = 4
	create_skills_grid.add_theme_constant_override("h_separation", UI_TOKENS.spacing("xs"))
	create_skills_grid.add_theme_constant_override("v_separation", UI_TOKENS.spacing("xs"))
	right_col.add_child(create_skills_grid)
	right_col.add_spacer(false)
	var action_row = HBoxContainer.new()
	action_row.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	right_col.add_child(action_row)
	create_points_label = _label("0/0 points left", 16, "text_secondary")
	action_row.add_child(create_points_label)
	action_row.add_spacer(false)
	var create_button = UI_COMPONENTS.button_primary("Create Save", Vector2(220, 42))
	create_button.pressed.connect(_on_create_character_pressed)
	action_row.add_child(create_button)
	create_status_label = _label(" ", -1, "text_secondary")
	create_status_label.text = " "
	right_col.add_child(create_status_label)

	create_container = wrap
	return wrap

func _build_load_screen() -> Control:
	var shell = UI_COMPONENTS.centered_shell(Vector2(1180, 760), UI_TOKENS.spacing("md"))
	var wrap = shell["wrap"]
	var content = shell["content"]

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	content.add_child(top)
	top.add_child(_label("Load Game", 32))
	top.add_spacer(false)
	var back = _button("Back")
	back.pressed.connect(func() -> void:
		_show_screen("main_menu")
	)
	top.add_child(back)

	var body = HSplitContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(body)

	load_list = ItemList.new()
	load_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	load_list.custom_minimum_size = Vector2(520, 420)
	load_list.item_selected.connect(_on_load_slot_selected)
	body.add_child(load_list)

	var right = VBoxContainer.new()
	right.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	body.add_child(right)
	load_preview_label = RichTextLabel.new()
	load_preview_label.fit_content = false
	load_preview_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	load_preview_label.bbcode_enabled = false
	right.add_child(load_preview_label)
	var actions = HBoxContainer.new()
	actions.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	right.add_child(actions)
	var load_btn = UI_COMPONENTS.button_primary("Load Selected", Vector2(170, 40))
	load_btn.pressed.connect(_on_load_selected_pressed)
	actions.add_child(load_btn)
	var delete_btn = _button("Delete")
	delete_btn.custom_minimum_size = Vector2(140, 40)
	delete_btn.pressed.connect(_on_delete_selected_pressed)
	actions.add_child(delete_btn)
	var refresh_btn = _button("Refresh")
	refresh_btn.custom_minimum_size = Vector2(120, 40)
	refresh_btn.pressed.connect(_refresh_load_game_list)
	actions.add_child(refresh_btn)

	load_status_label = _label(" ", -1, "text_secondary")
	load_status_label.text = " "
	content.add_child(load_status_label)

	load_container = wrap
	return wrap

func _build_settings_screen() -> Control:
	var shell = UI_COMPONENTS.centered_shell(Vector2(UI_TOKENS.size("shell_settings_w"), UI_TOKENS.size("shell_settings_h")), UI_TOKENS.spacing("md"))
	var wrap = shell["wrap"]
	var content = shell["content"]

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	content.add_child(top)
	top.add_child(_label("Settings", 30))
	top.add_spacer(false)
	var back = _button("Back")
	back.pressed.connect(func() -> void:
		_show_screen("main_menu")
	)
	top.add_child(back)

	var tabs = TabContainer.new()
	tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(tabs)

	var video_tab = _settings_tab(tabs, "Video")
	settings_screen_mode = _option(["Borderless Fullscreen", "Windowed"])
	settings_screen_mode.item_selected.connect(func(_index: int) -> void:
		_apply_settings()
	)
	video_tab.add_child(_labeled_control("Screen Mode", settings_screen_mode))

	var audio_tab = _settings_tab(tabs, "Audio")
	settings_audio_mute = _button("Muted: OFF")
	settings_audio_mute.toggle_mode = true
	settings_audio_mute.toggled.connect(func(_checked: bool) -> void:
		settings_audio_mute.text = "Muted: ON" if settings_audio_mute.button_pressed else "Muted: OFF"
		_apply_settings()
	)
	audio_tab.add_child(settings_audio_mute)
	settings_audio_volume = HSlider.new()
	settings_audio_volume.min_value = 0
	settings_audio_volume.max_value = 100
	settings_audio_volume.step = 1
	settings_audio_volume.value_changed.connect(func(_value: float) -> void:
		_apply_settings()
	)
	audio_tab.add_child(_labeled_control("Master Volume", settings_audio_volume))

	var input_tab = _settings_tab(tabs, "Input")
	input_tab.add_child(_label("Input rebinding scaffold lives in central config (`input.bindings`).", -1, "text_secondary"))

	var gameplay_tab = _settings_tab(tabs, "Gameplay")
	settings_difficulty_option = _option(["Story", "Normal", "Hard", "Nightmare"])
	settings_difficulty_option.item_selected.connect(func(_index: int) -> void:
		_apply_settings()
	)
	gameplay_tab.add_child(_labeled_control("Difficulty", settings_difficulty_option))
	settings_autosave_interval = HSlider.new()
	settings_autosave_interval.min_value = 30
	settings_autosave_interval.max_value = 600
	settings_autosave_interval.step = 15
	settings_autosave_interval.value_changed.connect(func(_value: float) -> void:
		_apply_settings()
	)
	gameplay_tab.add_child(_labeled_control("Autosave (sec)", settings_autosave_interval))

	var access_tab = _settings_tab(tabs, "Accessibility")
	settings_reduced_motion = _button("Reduced Motion: OFF")
	settings_reduced_motion.toggle_mode = true
	settings_reduced_motion.toggled.connect(func(_checked: bool) -> void:
		settings_reduced_motion.text = "Reduced Motion: ON" if settings_reduced_motion.button_pressed else "Reduced Motion: OFF"
		_apply_settings()
	)
	access_tab.add_child(settings_reduced_motion)

	settings_status_label = _label("Settings auto-apply and save locally.", -1, "text_secondary")
	content.add_child(settings_status_label)

	settings_container = wrap
	return wrap

func _settings_tab(tabs: TabContainer, name: String) -> VBoxContainer:
	var tab = VBoxContainer.new()
	tab.name = name
	tab.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	tabs.add_child(tab)
	return tab

func _build_admin_screen() -> Control:
	var shell = UI_COMPONENTS.centered_shell(Vector2(1700, 900), UI_TOKENS.spacing("md"))
	var wrap = shell["wrap"]
	var content = shell["content"]

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	content.add_child(top)
	top.add_child(_label("Admin Workspace", 30))
	top.add_spacer(false)
	var back = _button("Back")
	back.pressed.connect(func() -> void:
		_show_screen("main_menu")
	)
	top.add_child(back)

	admin_tabs = TabContainer.new()
	admin_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(admin_tabs)

	_build_admin_levels_tab()
	_build_admin_assets_tab()
	_build_admin_config_tab()
	_build_admin_diagnostics_tab()

	admin_status_label = _label("Designer tools operate on local data/config files.", -1, "text_secondary")
	content.add_child(admin_status_label)

	admin_container = wrap
	return wrap

func _build_admin_levels_tab() -> void:
	var tab = VBoxContainer.new()
	tab.name = "Level Editor"
	tab.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	admin_tabs.add_child(tab)

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	tab.add_child(top)
	admin_level_option = _option(["No levels"])
	admin_level_option.custom_minimum_size = Vector2(280, 34)
	top.add_child(admin_level_option)
	var load_btn = _button("Load")
	load_btn.pressed.connect(_admin_load_selected_level)
	top.add_child(load_btn)
	var new_btn = _button("New")
	new_btn.pressed.connect(_admin_new_level)
	top.add_child(new_btn)
	var save_btn = UI_COMPONENTS.button_primary("Save Level")
	save_btn.pressed.connect(_admin_save_level)
	top.add_child(save_btn)
	var play_btn = _button("Play This Level")
	play_btn.pressed.connect(_admin_play_current_level)
	top.add_child(play_btn)
	var set_default_btn = _button("Set As Default")
	set_default_btn.pressed.connect(_admin_set_default_level)
	top.add_child(set_default_btn)

	var meta = GridContainer.new()
	meta.columns = 8
	meta.add_theme_constant_override("h_separation", UI_TOKENS.spacing("xs"))
	meta.add_theme_constant_override("v_separation", UI_TOKENS.spacing("xs"))
	tab.add_child(meta)
	admin_level_id_input = _line_edit("level_id")
	admin_level_name_input = _line_edit("Display Name")
	admin_level_width_input = _line_edit("80")
	admin_level_height_input = _line_edit("48")
	admin_level_spawn_x_input = _line_edit("3")
	admin_level_spawn_y_input = _line_edit("3")
	meta.add_child(_label("ID", -1, "text_secondary"))
	meta.add_child(admin_level_id_input)
	meta.add_child(_label("Name", -1, "text_secondary"))
	meta.add_child(admin_level_name_input)
	meta.add_child(_label("Width", -1, "text_secondary"))
	meta.add_child(admin_level_width_input)
	meta.add_child(_label("Height", -1, "text_secondary"))
	meta.add_child(admin_level_height_input)
	meta.add_child(_label("Spawn X", -1, "text_secondary"))
	meta.add_child(admin_level_spawn_x_input)
	meta.add_child(_label("Spawn Y", -1, "text_secondary"))
	meta.add_child(admin_level_spawn_y_input)

	var split = HSplitContainer.new()
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tab.add_child(split)

	admin_level_layers_input = TextEdit.new()
	admin_level_layers_input.size_flags_vertical = Control.SIZE_EXPAND_FILL
	admin_level_layers_input.placeholder_text = "Layers JSON"
	split.add_child(admin_level_layers_input)

	var right = VBoxContainer.new()
	right.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	split.add_child(right)
	admin_level_objects_input = TextEdit.new()
	admin_level_objects_input.size_flags_vertical = Control.SIZE_EXPAND_FILL
	admin_level_objects_input.placeholder_text = "Objects JSON"
	right.add_child(admin_level_objects_input)
	admin_level_transitions_input = TextEdit.new()
	admin_level_transitions_input.custom_minimum_size = Vector2(0, 180)
	admin_level_transitions_input.placeholder_text = "Transitions JSON"
	right.add_child(admin_level_transitions_input)

func _build_admin_assets_tab() -> void:
	var tab = VBoxContainer.new()
	tab.name = "Asset Editor"
	tab.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	admin_tabs.add_child(tab)

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	tab.add_child(top)
	var refresh = _button("Refresh Assets")
	refresh.pressed.connect(_refresh_admin_asset_list)
	top.add_child(refresh)
	var save = UI_COMPONENTS.button_primary("Save Asset")
	save.pressed.connect(_admin_save_asset_entry)
	top.add_child(save)
	var add = _button("Add Asset")
	add.pressed.connect(_admin_add_asset_entry)
	top.add_child(add)

	var split = HSplitContainer.new()
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tab.add_child(split)

	admin_asset_list = ItemList.new()
	admin_asset_list.custom_minimum_size = Vector2(320, 480)
	admin_asset_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	admin_asset_list.item_selected.connect(_on_admin_asset_selected)
	split.add_child(admin_asset_list)

	admin_asset_payload = TextEdit.new()
	admin_asset_payload.size_flags_vertical = Control.SIZE_EXPAND_FILL
	split.add_child(admin_asset_payload)

	admin_asset_status = _label(" ", -1, "text_secondary")
	admin_asset_status.text = " "
	tab.add_child(admin_asset_status)

func _build_admin_config_tab() -> void:
	var tab = VBoxContainer.new()
	tab.name = "Config Editor"
	tab.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	admin_tabs.add_child(tab)

	var row = HBoxContainer.new()
	row.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	tab.add_child(row)
	var reload = _button("Reload")
	reload.pressed.connect(func() -> void:
		_load_game_config()
		_refresh_admin_config_text()
	)
	row.add_child(reload)
	var validate = _button("Validate")
	validate.pressed.connect(func() -> void:
		var errors = _validate_config(game_config)
		if errors.is_empty():
			admin_config_status.text = "Configuration valid."
		else:
			admin_config_status.text = "Validation failed: " + " | ".join(errors)
	)
	row.add_child(validate)
	var save = UI_COMPONENTS.button_primary("Save Config")
	save.pressed.connect(_admin_save_config_text)
	row.add_child(save)

	admin_config_text = TextEdit.new()
	admin_config_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tab.add_child(admin_config_text)

	admin_config_status = _label(" ", -1, "text_secondary")
	admin_config_status.text = " "
	tab.add_child(admin_config_status)

func _build_admin_diagnostics_tab() -> void:
	var tab = VBoxContainer.new()
	tab.name = "Diagnostics"
	tab.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	admin_tabs.add_child(tab)

	var row = HBoxContainer.new()
	row.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	tab.add_child(row)
	var reload_logs = _button("Reload Logs")
	reload_logs.pressed.connect(_refresh_admin_diagnostics)
	row.add_child(reload_logs)
	var paths = _button("Show Paths")
	paths.pressed.connect(_show_admin_paths)
	row.add_child(paths)

	admin_diag_text = TextEdit.new()
	admin_diag_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	admin_diag_text.editable = false
	tab.add_child(admin_diag_text)

func _build_world_screen() -> Control:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	wrap.add_child(top)
	var save_btn = UI_COMPONENTS.button_primary("Save Game", Vector2(140, 38))
	save_btn.pressed.connect(func() -> void:
		_save_active_slot(true)
	)
	top.add_child(save_btn)
	var settings_btn = _button("Settings")
	settings_btn.custom_minimum_size = Vector2(120, 38)
	settings_btn.pressed.connect(func() -> void:
		_show_screen("settings")
	)
	top.add_child(settings_btn)
	var main_btn = _button("Main Menu")
	main_btn.custom_minimum_size = Vector2(140, 38)
	main_btn.pressed.connect(func() -> void:
		_save_active_slot(false)
		_exit_world_to_main_menu()
	)
	top.add_child(main_btn)
	var exit_btn = _button("Exit")
	exit_btn.custom_minimum_size = Vector2(110, 38)
	exit_btn.pressed.connect(func() -> void:
		_save_active_slot(false)
		get_tree().quit()
	)
	top.add_child(exit_btn)
	top.add_spacer(false)

	world_status_label = _label("WASD to move. ESC returns to menu.", -1, "text_secondary")
	wrap.add_child(world_status_label)

	var panel = UI_COMPONENTS.panel_card(Vector2(0, 0), false)
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(panel)
	world_canvas = Control.new()
	world_canvas.set_script(WORLD_CANVAS_SCENE)
	world_canvas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	world_canvas.connect("player_position_changed", _on_world_position_changed)
	world_canvas.connect("transition_requested", _on_world_transition_requested)
	panel.add_child(world_canvas)

	world_container = wrap
	return wrap

func _refresh_create_from_config() -> void:
	var creator = game_config.get("character_creation", {})
	if not (creator is Dictionary):
		creator = {}
	create_budget = int(creator.get("point_budget", 10))
	create_stat_values.clear()
	create_skill_values.clear()
	create_skill_buttons.clear()
	create_stat_keys.clear()
	create_skill_keys.clear()

	_fill_option(create_sex_option, creator.get("sex_options", ["Male", "Female"]))
	_fill_option(create_race_option, creator.get("race_options", ["Human"]))
	_fill_option(create_background_option, creator.get("background_options", ["Drifter"]))
	_fill_option(create_affiliation_option, creator.get("affiliation_options", ["Unaffiliated"]))

	_clear_children(create_stats_grid)
	var stats = creator.get("stats", [])
	if not (stats is Array):
		stats = []
	for raw in stats:
		if not (raw is Dictionary):
			continue
		var key = str(raw.get("key", "")).strip_edges()
		if key.is_empty():
			continue
		create_stat_keys.append(key)
		create_stat_values[key] = int(raw.get("default", 0))
		var name = str(raw.get("label", key))
		var desc = str(raw.get("description", ""))
		create_stats_grid.add_child(_label(name, -1, "text_secondary"))
		var minus = _button("-")
		minus.custom_minimum_size = Vector2(30, 30)
		var value_label = _label(str(create_stat_values[key]))
		value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var plus = _button("+")
		plus.custom_minimum_size = Vector2(30, 30)
		minus.pressed.connect(func() -> void:
			_adjust_stat(key, -1, value_label)
		)
		plus.pressed.connect(func() -> void:
			_adjust_stat(key, 1, value_label)
		)
		create_stats_grid.add_child(minus)
		create_stats_grid.add_child(value_label)
		create_stats_grid.add_child(plus)
		create_stats_grid.add_child(_label(desc, -1, "text_muted"))

	_clear_children(create_skills_grid)
	var skills = creator.get("skills", [])
	if not (skills is Array):
		skills = []
	for raw_skill in skills:
		if not (raw_skill is Dictionary):
			continue
		var skill_key = str(raw_skill.get("key", "")).strip_edges()
		if skill_key.is_empty():
			continue
		create_skill_keys.append(skill_key)
		create_skill_values[skill_key] = int(raw_skill.get("selected", 0))
		var button = _button(str(raw_skill.get("label", skill_key)))
		button.custom_minimum_size = Vector2(84, 84)
		button.toggle_mode = true
		button.button_pressed = int(create_skill_values[skill_key]) > 0
		button.toggled.connect(func(enabled: bool) -> void:
			_toggle_skill(skill_key, enabled)
		)
		create_skill_buttons[skill_key] = button
		create_skills_grid.add_child(button)

	_refresh_points_label()
	_refresh_create_preview()

func _fill_option(option: OptionButton, values) -> void:
	if option == null:
		return
	option.clear()
	var list = values
	if not (list is Array):
		list = []
	if list.is_empty():
		list = ["Default"]
	for value in list:
		if value is Dictionary:
			option.add_item(str(value.get("label", value.get("key", "Option"))))
			option.set_item_metadata(option.get_item_count() - 1, str(value.get("key", "")))
		else:
			option.add_item(str(value))
			option.set_item_metadata(option.get_item_count() - 1, str(value).strip_edges().to_lower().replace(" ", "_"))
	option.selected = 0
	UI_COMPONENTS.sanitize_option_popup(option)

func _remaining_points() -> int:
	var spent = 0
	for v in create_stat_values.values():
		spent += int(v)
	for v2 in create_skill_values.values():
		if int(v2) > 0:
			spent += 1
	return max(0, create_budget - spent)

func _refresh_points_label() -> void:
	if create_points_label != null:
		create_points_label.text = "%d/%d points left" % [_remaining_points(), create_budget]

func _adjust_stat(key: String, delta: int, value_label: Label) -> void:
	var current = int(create_stat_values.get(key, 0))
	if delta > 0 and _remaining_points() <= 0:
		return
	var next = clampi(current + delta, 0, 10)
	if next == current:
		return
	create_stat_values[key] = next
	value_label.text = str(next)
	_refresh_points_label()

func _toggle_skill(key: String, enabled: bool) -> void:
	if enabled and int(create_skill_values.get(key, 0)) == 0 and _remaining_points() <= 0:
		var button = create_skill_buttons.get(key)
		if button is Button:
			button.button_pressed = false
		return
	create_skill_values[key] = 1 if enabled else 0
	_refresh_points_label()

func _refresh_create_preview() -> void:
	if create_preview_widget == null:
		return
	var appearance = "human_male"
	if create_sex_option != null and create_sex_option.selected >= 0:
		var text = create_sex_option.get_item_text(create_sex_option.selected).to_lower()
		appearance = "human_female" if text.contains("female") else "human_male"
	create_preview_widget.call("set_character", appearance, "")

func _on_create_character_pressed() -> void:
	if create_name_input == null:
		return
	var name = create_name_input.text.strip_edges()
	if name.length() < 2:
		create_status_label.text = "Character name must be at least 2 characters."
		return
	var creator = game_config.get("character_creation", {})
	var world_cfg = game_config.get("world", {})
	var default_level = str(world_cfg.get("default_level_id", "open_world_01"))
	var save_payload = {
		"character": {
			"name": name,
			"sex": _option_value(create_sex_option),
			"race": _option_value(create_race_option),
			"background": _option_value(create_background_option),
			"affiliation": _option_value(create_affiliation_option),
			"appearance_key": "human_female" if _option_value(create_sex_option).contains("female") else "human_male",
			"level": 1,
			"experience": 0,
			"stats": create_stat_values.duplicate(true),
			"skills": create_skill_values.duplicate(true),
		},
		"world": {
			"level_id": default_level,
			"world_x": float(world_cfg.get("default_spawn_x", 96.0)),
			"world_y": float(world_cfg.get("default_spawn_y", 96.0)),
		},
		"inventory": [],
		"quests": [],
		"dialog_state": {},
		"playtime_seconds": 0,
		"created_at": Time.get_datetime_string_from_system(true, true),
		"updated_at": Time.get_datetime_string_from_system(true, true),
		"config_revision": int(game_config.get("meta", {}).get("revision", 1)),
		"character_creation_rules": creator,
	}
	var slot_id = _create_save_slot(save_payload)
	if slot_id < 0:
		create_status_label.text = "Failed to create save slot."
		return
	create_status_label.text = "Save created in slot %d." % slot_id
	_refresh_load_game_list()
	_start_game_from_slot(slot_id)

func _option_value(option: OptionButton) -> String:
	if option == null or option.selected < 0:
		return ""
	var metadata = option.get_item_metadata(option.selected)
	if metadata is String:
		var value = str(metadata).strip_edges()
		if not value.is_empty():
			return value
	return option.get_item_text(option.selected)

func _refresh_load_game_list() -> void:
	if load_list == null:
		return
	load_list.clear()
	var index_data = _read_save_index()
	var slots = index_data.get("slots", [])
	if not (slots is Array):
		slots = []
	for slot in slots:
		if not (slot is Dictionary):
			continue
		var line = "Slot %s | %s | Lv.%s | %s | %s" % [
			str(slot.get("id", "?")),
			str(slot.get("character_name", "Unknown")),
			str(slot.get("character_level", 1)),
			str(slot.get("level_id", "unknown")),
			str(slot.get("updated_at", "")),
		]
		load_list.add_item(line)
		load_list.set_item_metadata(load_list.get_item_count() - 1, int(slot.get("id", -1)))
	if load_list.get_item_count() <= 0:
		load_preview_label.text = "No saves found. Start a New Game to create one."
		load_status_label.text = " "
	else:
		load_list.select(0)
		_on_load_slot_selected(0)

func _on_load_slot_selected(index: int) -> void:
	if load_list == null or index < 0 or index >= load_list.get_item_count():
		return
	var slot_id = int(load_list.get_item_metadata(index))
	var payload = _read_save_slot(slot_id)
	if payload.is_empty():
		load_preview_label.text = "Unable to read save slot."
		return
	var character = payload.get("character", {})
	var world = payload.get("world", {})
	load_preview_label.text = "Name: %s\nLevel: %s\nRace: %s\nBackground: %s\nAffiliation: %s\nLocation: %s (%s,%s)\nUpdated: %s" % [
		str(character.get("name", "Unknown")),
		str(character.get("level", 1)),
		str(character.get("race", "")),
		str(character.get("background", "")),
		str(character.get("affiliation", "")),
		str(world.get("level_id", "unknown")),
		str(int(world.get("world_x", 0))),
		str(int(world.get("world_y", 0))),
		str(payload.get("updated_at", "")),
	]

func _on_load_selected_pressed() -> void:
	if load_list == null or load_list.get_selected_items().is_empty():
		load_status_label.text = "Select a save slot first."
		return
	var item = int(load_list.get_selected_items()[0])
	var slot_id = int(load_list.get_item_metadata(item))
	_start_game_from_slot(slot_id)

func _on_delete_selected_pressed() -> void:
	if load_list == null or load_list.get_selected_items().is_empty():
		load_status_label.text = "Select a save slot first."
		return
	var item = int(load_list.get_selected_items()[0])
	var slot_id = int(load_list.get_item_metadata(item))
	_delete_save_slot(slot_id)
	load_status_label.text = "Deleted slot %d." % slot_id
	_refresh_load_game_list()

func _start_game_from_slot(slot_id: int) -> void:
	var payload = _read_save_slot(slot_id)
	if payload.is_empty():
		_set_status("Failed to load save slot %d." % slot_id)
		return
	active_slot_id = slot_id
	active_save = payload
	_start_world_from_active_save()

func _start_world_from_active_save() -> void:
	if world_canvas == null:
		return
	var world = active_save.get("world", {})
	var level_id = str(world.get("level_id", game_config.get("world", {}).get("default_level_id", "open_world_01")))
	var level = _load_level(level_id)
	if level.is_empty():
		level = _default_level(level_id)
	var width = int(level.get("width", 80))
	var height = int(level.get("height", 48))
	var spawn_x = float(world.get("world_x", float(level.get("spawn_x", 3)) * 32.0))
	var spawn_y = float(world.get("world_y", float(level.get("spawn_y", 3)) * 32.0))
	var level_name = str(level.get("display_name", level.get("id", "Open World")))
	var runtime_cfg = game_config.get("gameplay", {}).get("movement", {})
	if world_canvas.has_method("configure_runtime"):
		world_canvas.call("configure_runtime", runtime_cfg)
	world_canvas.call("configure_world", level_name, width, height, Vector2(spawn_x, spawn_y), level)
	world_status_label.text = "WASD to move. Level: %s" % level_name
	world_active = true
	_show_screen("world")

func _exit_world_to_main_menu() -> void:
	world_active = false
	_show_screen("main_menu")

func _on_world_position_changed(position: Vector2) -> void:
	if active_save.is_empty():
		return
	var world = active_save.get("world", {})
	if not (world is Dictionary):
		world = {}
	world["world_x"] = int(round(position.x))
	world["world_y"] = int(round(position.y))
	active_save["world"] = world

func _on_world_transition_requested(transition: Dictionary) -> void:
	if active_save.is_empty():
		return
	var destination = str(transition.get("destination_level_id", "")).strip_edges()
	if destination.is_empty():
		return
	var world = active_save.get("world", {})
	if not (world is Dictionary):
		world = {}
	world["level_id"] = destination
	world["world_x"] = int(transition.get("destination_x", 96))
	world["world_y"] = int(transition.get("destination_y", 96))
	active_save["world"] = world
	_start_world_from_active_save()

func _save_active_slot(show_status: bool) -> void:
	if active_slot_id < 0 or active_save.is_empty():
		return
	var now = Time.get_datetime_string_from_system(true, true)
	active_save["updated_at"] = now
	var stats = active_save.get("character", {})
	if stats is Dictionary:
		stats["updated_at"] = now
		active_save["character"] = stats
	_write_save_slot(active_slot_id, active_save)
	_update_save_index_entry(active_slot_id, active_save)
	if show_status:
		_set_status("Saved slot %d." % active_slot_id)

func _apply_settings() -> void:
	if settings_screen_mode != null:
		game_settings["screen_mode"] = "windowed" if settings_screen_mode.selected == 1 else "borderless_fullscreen"
	if settings_audio_mute != null:
		game_settings["audio_muted"] = settings_audio_mute.button_pressed
	if settings_audio_volume != null:
		game_settings["audio_volume"] = int(round(settings_audio_volume.value))
	if settings_autosave_interval != null:
		game_settings["autosave_interval"] = int(round(settings_autosave_interval.value))
	if settings_reduced_motion != null:
		game_settings["reduced_motion"] = settings_reduced_motion.button_pressed
	if settings_difficulty_option != null and settings_difficulty_option.selected >= 0:
		game_settings["difficulty"] = settings_difficulty_option.get_item_text(settings_difficulty_option.selected)

	_write_preferences(game_settings)
	_apply_window_mode_from_settings()
	if create_preview_widget != null:
		create_preview_widget.call("set_reduced_motion", bool(game_settings.get("reduced_motion", false)))
	settings_status_label.text = "Settings applied."

func _load_settings() -> void:
	game_settings = _read_preferences()
	if settings_screen_mode != null:
		settings_screen_mode.selected = 1 if str(game_settings.get("screen_mode", "borderless_fullscreen")).to_lower() == "windowed" else 0
	if settings_audio_mute != null:
		settings_audio_mute.button_pressed = bool(game_settings.get("audio_muted", false))
		settings_audio_mute.text = "Muted: ON" if settings_audio_mute.button_pressed else "Muted: OFF"
	if settings_audio_volume != null:
		settings_audio_volume.value = float(game_settings.get("audio_volume", 75))
	if settings_autosave_interval != null:
		settings_autosave_interval.value = float(game_settings.get("autosave_interval", 120))
	if settings_reduced_motion != null:
		settings_reduced_motion.button_pressed = bool(game_settings.get("reduced_motion", false))
		settings_reduced_motion.text = "Reduced Motion: ON" if settings_reduced_motion.button_pressed else "Reduced Motion: OFF"
	if settings_difficulty_option != null:
		var difficulty = str(game_settings.get("difficulty", "Normal"))
		for i in range(settings_difficulty_option.get_item_count()):
			if settings_difficulty_option.get_item_text(i) == difficulty:
				settings_difficulty_option.selected = i
				break
	_apply_window_mode_from_settings()

func _apply_window_mode_from_settings() -> void:
	var mode = str(game_settings.get("screen_mode", "borderless_fullscreen")).to_lower()
	if mode == "windowed":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, false)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)

func _on_update_pressed() -> void:
	var feed_url = str(game_config.get("update", {}).get("feed_url", "")).strip_edges()
	if feed_url.is_empty():
		feed_url = str(OS.get_environment("GOK_UPDATE_REPO")).strip_edges()
	if feed_url.is_empty():
		_set_status("Update feed URL missing in config.")
		return
	var helper = _resolve_update_helper_path()
	if helper.is_empty():
		_set_status("Update helper not found.")
		return
	var args = PackedStringArray([
		"--repo",
		feed_url,
		"--log-file",
		_path_join(logs_root_path, "velopack.log"),
		"--waitpid",
		str(OS.get_process_id()),
		"--restart-args",
		"--autoplay",
	])
	var pid = OS.create_process(helper, args)
	if pid <= 0:
		_set_status("Failed to start update helper.")
		return
	_append_log("Update helper launched. pid=" + str(pid))
	if world_active:
		_save_active_slot(false)
	_set_status("Updater started. Restarting...")
	get_tree().quit()

func _refresh_admin_panels() -> void:
	_refresh_admin_level_list()
	_refresh_admin_asset_list()
	_refresh_admin_config_text()
	_refresh_admin_diagnostics()

func _refresh_admin_level_list() -> void:
	if admin_level_option == null:
		return
	admin_level_option.clear()
	var files = _list_level_files()
	if files.is_empty():
		admin_level_option.add_item("No levels")
		admin_level_option.selected = 0
		_admin_new_level()
		return
	for file_name in files:
		admin_level_option.add_item(file_name)
	admin_level_option.selected = 0
	UI_COMPONENTS.sanitize_option_popup(admin_level_option)
	_admin_load_selected_level()

func _admin_new_level() -> void:
	admin_level_id_input.text = "open_world_%d" % int(Time.get_unix_time_from_system() % 100000)
	admin_level_name_input.text = "Open World"
	admin_level_width_input.text = "80"
	admin_level_height_input.text = "48"
	admin_level_spawn_x_input.text = "3"
	admin_level_spawn_y_input.text = "3"
	admin_level_layers_input.text = JSON.stringify({"0": [], "1": [], "2": []}, "\t")
	admin_level_objects_input.text = JSON.stringify([], "\t")
	admin_level_transitions_input.text = JSON.stringify([], "\t")
	admin_status_label.text = "New level draft created."

func _admin_load_selected_level() -> void:
	if admin_level_option == null or admin_level_option.get_item_count() <= 0:
		return
	var selected = admin_level_option.get_item_text(admin_level_option.selected)
	if selected == "No levels":
		_admin_new_level()
		return
	var level_id = selected.trim_suffix(".json")
	var level = _load_level(level_id)
	if level.is_empty():
		admin_status_label.text = "Failed to load level " + level_id
		return
	admin_level_id_input.text = str(level.get("id", level_id))
	admin_level_name_input.text = str(level.get("display_name", level_id))
	admin_level_width_input.text = str(level.get("width", 80))
	admin_level_height_input.text = str(level.get("height", 48))
	admin_level_spawn_x_input.text = str(level.get("spawn_x", 3))
	admin_level_spawn_y_input.text = str(level.get("spawn_y", 3))
	admin_level_layers_input.text = JSON.stringify(level.get("layers", {"0": [], "1": [], "2": []}), "\t")
	admin_level_objects_input.text = JSON.stringify(level.get("objects", []), "\t")
	admin_level_transitions_input.text = JSON.stringify(level.get("transitions", []), "\t")
	admin_status_label.text = "Loaded level " + level_id

func _admin_save_level() -> void:
	var level_id = admin_level_id_input.text.strip_edges().to_lower()
	if level_id.is_empty():
		admin_status_label.text = "Level ID is required."
		return
	var layers = JSON.parse_string(admin_level_layers_input.text)
	if not (layers is Dictionary):
		admin_status_label.text = "Layers JSON must be an object."
		return
	var objects = JSON.parse_string(admin_level_objects_input.text)
	if not (objects is Array):
		admin_status_label.text = "Objects JSON must be an array."
		return
	var transitions = JSON.parse_string(admin_level_transitions_input.text)
	if not (transitions is Array):
		admin_status_label.text = "Transitions JSON must be an array."
		return
	var level = {
		"schema_version": 3,
		"id": level_id,
		"display_name": admin_level_name_input.text.strip_edges(),
		"width": int(admin_level_width_input.text.to_int()),
		"height": int(admin_level_height_input.text.to_int()),
		"spawn_x": int(admin_level_spawn_x_input.text.to_int()),
		"spawn_y": int(admin_level_spawn_y_input.text.to_int()),
		"layers": layers,
		"objects": objects,
		"transitions": transitions,
		"asset_templates": _asset_templates_map(),
	}
	if _write_level(level_id, level):
		admin_status_label.text = "Saved level " + level_id
		_refresh_admin_level_list()
	else:
		admin_status_label.text = "Failed to save level."

func _admin_play_current_level() -> void:
	var level_id = admin_level_id_input.text.strip_edges().to_lower()
	if level_id.is_empty():
		admin_status_label.text = "Save level first."
		return
	var payload = _read_save_slot(active_slot_id)
	if payload.is_empty():
		payload = _new_ephemeral_save_payload()
	payload["world"] = {
		"level_id": level_id,
		"world_x": int(admin_level_spawn_x_input.text.to_int()) * 32,
		"world_y": int(admin_level_spawn_y_input.text.to_int()) * 32,
	}
	if active_slot_id < 0:
		active_slot_id = _create_save_slot(payload)
	active_save = payload
	_start_world_from_active_save()

func _admin_set_default_level() -> void:
	var level_id = admin_level_id_input.text.strip_edges().to_lower()
	if level_id.is_empty():
		admin_status_label.text = "Level ID is required."
		return
	var world_cfg = game_config.get("world", {})
	if not (world_cfg is Dictionary):
		world_cfg = {}
	world_cfg["default_level_id"] = level_id
	world_cfg["default_spawn_x"] = int(admin_level_spawn_x_input.text.to_int()) * 32
	world_cfg["default_spawn_y"] = int(admin_level_spawn_y_input.text.to_int()) * 32
	game_config["world"] = world_cfg
	_save_game_config(game_config)
	admin_status_label.text = "Default level set to " + level_id
	_refresh_admin_config_text()

func _refresh_admin_asset_list() -> void:
	if admin_asset_list == null:
		return
	admin_asset_list.clear()
	var catalog = _assets_catalog()
	for entry in catalog:
		if not (entry is Dictionary):
			continue
		var key = str(entry.get("key", "asset"))
		var label = str(entry.get("label", key))
		admin_asset_list.add_item("%s | %s" % [key, label])
		admin_asset_list.set_item_metadata(admin_asset_list.get_item_count() - 1, key)
	if admin_asset_list.get_item_count() > 0:
		admin_asset_list.select(0)
		_on_admin_asset_selected(0)
	else:
		admin_asset_payload.text = "{}"
		admin_asset_status.text = "No asset entries in config."

func _assets_catalog() -> Array:
	var assets = game_config.get("assets", {})
	if not (assets is Dictionary):
		return []
	var catalog = assets.get("catalog", [])
	if catalog is Array:
		return catalog
	return []

func _asset_templates_map() -> Dictionary:
	var templates = {}
	for entry in _assets_catalog():
		if not (entry is Dictionary):
			continue
		var key = str(entry.get("key", "")).strip_edges().to_lower()
		if key.is_empty():
			continue
		templates[key] = entry
	return templates

func _on_admin_asset_selected(index: int) -> void:
	admin_asset_selected_index = index
	var catalog = _assets_catalog()
	if index < 0 or index >= catalog.size():
		admin_asset_payload.text = "{}"
		return
	admin_asset_payload.text = JSON.stringify(catalog[index], "\t")

func _admin_add_asset_entry() -> void:
	var assets = game_config.get("assets", {})
	if not (assets is Dictionary):
		assets = {}
	var catalog = assets.get("catalog", [])
	if not (catalog is Array):
		catalog = []
	var new_entry = {
		"key": "new_asset_%d" % int(Time.get_unix_time_from_system() % 100000),
		"label": "New Asset",
		"default_layer": 1,
		"collidable": false,
		"description": "Describe this asset.",
		"collision_template": {
			"shape": "none",
			"layers": ["ground"],
		},
	}
	catalog.append(new_entry)
	assets["catalog"] = catalog
	game_config["assets"] = assets
	_save_game_config(game_config)
	_refresh_admin_asset_list()
	admin_asset_status.text = "Added new asset entry."

func _admin_save_asset_entry() -> void:
	if admin_asset_selected_index < 0:
		admin_asset_status.text = "Select an asset first."
		return
	var parsed = JSON.parse_string(admin_asset_payload.text)
	if not (parsed is Dictionary):
		admin_asset_status.text = "Asset payload must be valid JSON object."
		return
	var assets = game_config.get("assets", {})
	if not (assets is Dictionary):
		assets = {}
	var catalog = assets.get("catalog", [])
	if not (catalog is Array):
		catalog = []
	if admin_asset_selected_index < 0 or admin_asset_selected_index >= catalog.size():
		admin_asset_status.text = "Selected asset index is out of range."
		return
	catalog[admin_asset_selected_index] = parsed
	assets["catalog"] = catalog
	game_config["assets"] = assets
	_save_game_config(game_config)
	_refresh_admin_asset_list()
	admin_asset_status.text = "Asset saved."

func _refresh_admin_config_text() -> void:
	if admin_config_text != null:
		admin_config_text.text = JSON.stringify(game_config, "\t")

func _admin_save_config_text() -> void:
	var parsed = JSON.parse_string(admin_config_text.text)
	if not (parsed is Dictionary):
		admin_config_status.text = "Config must be valid JSON object."
		return
	var errors = _validate_config(parsed)
	if not errors.is_empty():
		admin_config_status.text = "Validation failed: " + " | ".join(errors)
		return
	game_config = parsed
	_save_game_config(game_config)
	admin_config_status.text = "Config saved."
	_refresh_create_from_config()
	_refresh_admin_asset_list()

func _refresh_admin_diagnostics() -> void:
	if admin_diag_text == null:
		return
	var game_log = _path_join(logs_root_path, "game.log")
	var text = ""
	if FileAccess.file_exists(game_log):
		var file = FileAccess.open(game_log, FileAccess.READ)
		if file != null:
			text = file.get_as_text()
			file.close()
	admin_diag_text.text = text if not text.is_empty() else "No log entries yet."

func _show_admin_paths() -> void:
	if admin_diag_text == null:
		return
	admin_diag_text.text = "install_root=%s\nlogs_root=%s\nconfig=%s\nsaves_index=%s\nlevels_root=%s\n" % [
		install_root_path,
		logs_root_path,
		user_config_path,
		saves_index_path,
		levels_root_path,
	]

func _validate_config(config: Dictionary) -> Array:
	var errors = []
	if not config.has("meta"):
		errors.append("meta is missing")
	if not config.has("update"):
		errors.append("update is missing")
	if not config.has("character_creation"):
		errors.append("character_creation is missing")
	if not config.has("gameplay"):
		errors.append("gameplay is missing")
	if not config.has("assets"):
		errors.append("assets is missing")
	var creator = config.get("character_creation", {})
	if creator is Dictionary:
		if int(creator.get("point_budget", 0)) <= 0:
			errors.append("character_creation.point_budget must be > 0")
	else:
		errors.append("character_creation must be an object")
	return errors

func _new_ephemeral_save_payload() -> Dictionary:
	return {
		"character": {
			"name": "Adventurer",
			"sex": "male",
			"race": "human",
			"background": "drifter",
			"affiliation": "unaffiliated",
			"appearance_key": "human_male",
			"level": 1,
			"experience": 0,
			"stats": {},
			"skills": {},
		},
		"world": {
			"level_id": str(game_config.get("world", {}).get("default_level_id", "open_world_01")),
			"world_x": int(game_config.get("world", {}).get("default_spawn_x", 96)),
			"world_y": int(game_config.get("world", {}).get("default_spawn_y", 96)),
		},
		"inventory": [],
		"quests": [],
		"dialog_state": {},
		"playtime_seconds": 0,
		"created_at": Time.get_datetime_string_from_system(true, true),
		"updated_at": Time.get_datetime_string_from_system(true, true),
	}

func _create_save_slot(payload: Dictionary) -> int:
	var index_data = _read_save_index()
	var next_id = int(index_data.get("next_slot_id", 1))
	_write_save_slot(next_id, payload)
	var slots = index_data.get("slots", [])
	if not (slots is Array):
		slots = []
	slots.append(_save_summary(next_id, payload))
	index_data["slots"] = slots
	index_data["next_slot_id"] = next_id + 1
	_write_json_file(saves_index_path, index_data)
	return next_id

func _update_save_index_entry(slot_id: int, payload: Dictionary) -> void:
	var index_data = _read_save_index()
	var slots = index_data.get("slots", [])
	if not (slots is Array):
		slots = []
	var found = false
	for i in range(slots.size()):
		if not (slots[i] is Dictionary):
			continue
		if int(slots[i].get("id", -1)) == slot_id:
			slots[i] = _save_summary(slot_id, payload)
			found = true
			break
	if not found:
		slots.append(_save_summary(slot_id, payload))
	index_data["slots"] = slots
	_write_json_file(saves_index_path, index_data)

func _delete_save_slot(slot_id: int) -> void:
	var path = _path_join(saves_root_path, "slot_%d.json" % slot_id)
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
	var index_data = _read_save_index()
	var slots = index_data.get("slots", [])
	if slots is Array:
		var updated = []
		for slot in slots:
			if slot is Dictionary and int(slot.get("id", -1)) == slot_id:
				continue
			updated.append(slot)
		index_data["slots"] = updated
	_write_json_file(saves_index_path, index_data)

func _save_summary(slot_id: int, payload: Dictionary) -> Dictionary:
	var character = payload.get("character", {})
	var world = payload.get("world", {})
	return {
		"id": slot_id,
		"character_name": str(character.get("name", "Unknown")),
		"character_level": int(character.get("level", 1)),
		"level_id": str(world.get("level_id", "unknown")),
		"updated_at": str(payload.get("updated_at", Time.get_datetime_string_from_system(true, true))),
	}

func _read_save_index() -> Dictionary:
	var fallback = {"next_slot_id": 1, "slots": []}
	if not FileAccess.file_exists(saves_index_path):
		_write_json_file(saves_index_path, fallback)
		return fallback
	var parsed = _read_json_file(saves_index_path)
	if parsed is Dictionary:
		return parsed
	return fallback

func _read_save_slot(slot_id: int) -> Dictionary:
	var path = _path_join(saves_root_path, "slot_%d.json" % slot_id)
	var parsed = _read_json_file(path)
	if parsed is Dictionary:
		return parsed
	return {}

func _write_save_slot(slot_id: int, payload: Dictionary) -> void:
	var path = _path_join(saves_root_path, "slot_%d.json" % slot_id)
	_write_json_file(path, payload)

func _load_level(level_id: String) -> Dictionary:
	var path = _path_join(levels_root_path, level_id + ".json")
	var parsed = _read_json_file(path)
	if parsed is Dictionary:
		return parsed
	return {}

func _write_level(level_id: String, level: Dictionary) -> bool:
	var path = _path_join(levels_root_path, level_id + ".json")
	return _write_json_file(path, level)

func _list_level_files() -> Array:
	var files = []
	var dir = DirAccess.open(levels_root_path)
	if dir == null:
		return files
	dir.list_dir_begin()
	while true:
		var file_name = dir.get_next()
		if file_name.is_empty():
			break
		if dir.current_is_dir():
			continue
		if file_name.to_lower().ends_with(".json"):
			files.append(file_name)
	dir.list_dir_end()
	files.sort()
	return files

func _default_level(level_id: String) -> Dictionary:
	return {
		"schema_version": 3,
		"id": level_id,
		"display_name": "Open World",
		"width": 80,
		"height": 48,
		"spawn_x": 3,
		"spawn_y": 3,
		"layers": {"0": [], "1": [], "2": []},
		"objects": [],
		"transitions": [],
		"asset_templates": _asset_templates_map(),
	}

func _ensure_default_config_exists() -> void:
	if FileAccess.file_exists(user_config_path):
		return
	var fallback = _read_json_file(DEFAULT_CONFIG)
	if not (fallback is Dictionary):
		fallback = {
			"meta": {"revision": 1},
			"update": {"feed_url": ""},
			"character_creation": {"point_budget": 10, "sex_options": ["Male", "Female"], "race_options": ["Human"], "background_options": ["Drifter"], "affiliation_options": ["Unaffiliated"], "stats": [], "skills": []},
			"gameplay": {"movement": {"player_speed_tiles": 4.6, "player_radius": 14.0}},
			"assets": {"catalog": []},
			"world": {"default_level_id": "open_world_01", "default_spawn_x": 96, "default_spawn_y": 96},
		}
	_write_json_file(user_config_path, fallback)

func _load_game_config() -> void:
	var parsed = _read_json_file(user_config_path)
	if parsed is Dictionary:
		game_config = parsed
	else:
		game_config = {}
	var errors = _validate_config(game_config)
	if not errors.is_empty():
		_set_status("Config issues: " + " | ".join(errors))
	_ensure_default_level_exists()

func _save_game_config(data: Dictionary) -> void:
	_write_json_file(user_config_path, data)
	_append_log("Saved game configuration.")

func _ensure_default_level_exists() -> void:
	var world_cfg = game_config.get("world", {})
	if not (world_cfg is Dictionary):
		world_cfg = {}
	var default_level_id = str(world_cfg.get("default_level_id", "open_world_01"))
	if _load_level(default_level_id).is_empty():
		_write_level(default_level_id, _default_level(default_level_id))

func _set_status(message: String) -> void:
	if menu_status_label != null:
		menu_status_label.text = message
	if footer_status != null:
		footer_status.text = footer_version_text if message.strip_edges().is_empty() else "%s | %s" % [footer_version_text, message]
	_append_log(message)

func _resolve_character_texture_directional(appearance_key: String, direction: String):
	var key = appearance_key.strip_edges().to_lower()
	if key.is_empty():
		key = "human_male"
	var direction_key = direction.strip_edges().to_lower()
	var cache_key = "%s|%s" % [key, direction_key]
	if character_texture_cache.has(cache_key):
		var cached_directional = character_texture_cache.get(cache_key)
		if cached_directional is Texture2D:
			return cached_directional
	if character_texture_cache.has(key):
		var cached = character_texture_cache.get(key)
		if cached is Texture2D:
			return cached

	var base = "karaxas_human_female" if key == "human_female" else "karaxas_human_male"
	var candidates = []
	candidates.append("res://assets/characters/%s_idle_%s_32.png" % [base, direction_key])
	candidates.append("res://assets/characters/%s_idle_32.png" % base)
	candidates.append(_path_join(install_root_path, "assets/characters/%s_idle_%s_32.png" % [base, direction_key]))
	candidates.append(_path_join(install_root_path, "assets/characters/%s_idle_32.png" % base))
	candidates.append(_path_join(install_root_path, "game-client/assets/characters/%s_idle_32.png" % base))
	for path in candidates:
		var texture = _load_texture(path)
		if texture != null:
			character_texture_cache[cache_key] = texture
			character_texture_cache[key] = texture
			return texture
	return null

func _load_texture(path: String):
	if path.is_empty():
		return null
	var image = Image.new()
	if path.begins_with("res://"):
		if not ResourceLoader.exists(path) and not FileAccess.file_exists(path):
			return null
		if image.load(path) == OK:
			return ImageTexture.create_from_image(image)
		var resource = load(path)
		if resource is Texture2D:
			return resource
		return null
	if not FileAccess.file_exists(path):
		return null
	if image.load(path) != OK:
		return null
	return ImageTexture.create_from_image(image)

func _resolve_paths() -> void:
	var payload_root = OS.get_environment("VELOPACK_APPROOT").strip_edges()
	if payload_root.is_empty():
		payload_root = OS.get_executable_path().get_base_dir()
	var cleaned = payload_root.replace("\\", "/")
	var runtime_marker = "/game-client/runtime/windows"
	if cleaned.contains(runtime_marker):
		install_root_path = cleaned.split(runtime_marker)[0]
	elif cleaned.ends_with("/game-client"):
		install_root_path = cleaned.get_base_dir()
	elif cleaned.get_file().to_lower() == "current":
		install_root_path = cleaned.get_base_dir()
	else:
		install_root_path = cleaned
	if install_root_path.is_empty():
		install_root_path = ProjectSettings.globalize_path("user://")
	logs_root_path = _path_join(install_root_path, "logs")
	prefs_path = _path_join(install_root_path, "single_player_prefs.properties")
	var user_root = ProjectSettings.globalize_path("user://")
	user_config_path = _path_join(user_root, "config/game_config.json")
	saves_root_path = _path_join(user_root, "saves")
	saves_index_path = _path_join(saves_root_path, "index.json")
	levels_root_path = _path_join(user_root, "designer/levels")
	DirAccess.make_dir_recursive_absolute(logs_root_path)
	DirAccess.make_dir_recursive_absolute(_path_join(user_root, "config"))
	DirAccess.make_dir_recursive_absolute(saves_root_path)
	DirAccess.make_dir_recursive_absolute(levels_root_path)

func _append_log(message: String) -> void:
	if message.strip_edges().is_empty():
		return
	var line = "[%s] %s" % [Time.get_datetime_string_from_system(true, true), message]
	print(line)
	if logs_root_path.is_empty():
		return
	var path = _path_join(logs_root_path, "game.log")
	var file = FileAccess.open(path, FileAccess.READ_WRITE)
	if file == null:
		file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return
	file.seek_end()
	file.store_line(line)
	file.close()

func _resolve_update_helper_path() -> String:
	var helper = _path_join(install_root_path, "UpdateHelper.exe")
	if FileAccess.file_exists(helper):
		return helper
	var exe_helper = _path_join(OS.get_executable_path().get_base_dir(), "UpdateHelper.exe")
	if FileAccess.file_exists(exe_helper):
		return exe_helper
	return ""

func _load_client_version() -> void:
	var meta_path = _path_join(install_root_path, "patch_notes_meta.txt")
	if FileAccess.file_exists(meta_path):
		var file = FileAccess.open(meta_path, FileAccess.READ)
		if file != null:
			while not file.eof_reached():
				var line = file.get_line().strip_edges()
				if line.begins_with("version="):
					client_version = line.trim_prefix("version=").strip_edges()
					break
			file.close()
	footer_version_text = "v" + client_version

func _apply_default_window_mode() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)

func _read_preferences() -> Dictionary:
	var prefs = {}
	if prefs_path.is_empty() or not FileAccess.file_exists(prefs_path):
		return prefs
	var file = FileAccess.open(prefs_path, FileAccess.READ)
	if file == null:
		return prefs
	while not file.eof_reached():
		var line = file.get_line().strip_edges()
		if line.is_empty() or line.begins_with("#"):
			continue
		var parts = line.split("=", false, 2)
		if parts.size() != 2:
			continue
		var key = str(parts[0]).strip_edges()
		var value = str(parts[1]).strip_edges()
		if value == "true":
			prefs[key] = true
		elif value == "false":
			prefs[key] = false
		elif value.is_valid_int():
			prefs[key] = int(value)
		elif value.is_valid_float():
			prefs[key] = float(value)
		else:
			prefs[key] = value
	file.close()
	return prefs

func _write_preferences(prefs: Dictionary) -> void:
	if prefs_path.is_empty():
		return
	var file = FileAccess.open(prefs_path, FileAccess.WRITE)
	if file == null:
		return
	for key in prefs.keys():
		file.store_line("%s=%s" % [str(key), str(prefs[key])])
	file.close()

func _read_json_file(path: String):
	if path.is_empty() or not FileAccess.file_exists(path):
		return null
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return null
	var text = file.get_as_text()
	file.close()
	return JSON.parse_string(text)

func _write_json_file(path: String, payload) -> bool:
	if path.is_empty():
		return false
	var parent = path.get_base_dir()
	if not parent.is_empty():
		DirAccess.make_dir_recursive_absolute(parent)
	var file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(payload, "\t"))
	file.close()
	return true

func _path_join(a: String, b: String) -> String:
	if a.is_empty():
		return b
	if a.ends_with("/") or a.ends_with("\\"):
		return a + b
	return a + "/" + b

func _label(text_value: String, font_size: int = -1, color_name: String = "text_primary") -> Label:
	return UI_COMPONENTS.label(text_value, font_size, color_name)

func _button(text_value: String) -> Button:
	return UI_COMPONENTS.button_secondary(text_value)

func _option(items: Array) -> OptionButton:
	return UI_COMPONENTS.option(items)

func _line_edit(placeholder: String, secret: bool = false) -> LineEdit:
	return UI_COMPONENTS.line_edit(placeholder, secret)

func _labeled_control(label_text: String, control: Control) -> Control:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 4)
	wrap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	wrap.add_child(_label(label_text, -1, "text_secondary"))
	wrap.add_child(control)
	return wrap

func _clear_children(node: Node) -> void:
	if node == null:
		return
	for child in node.get_children():
		node.remove_child(child)
		child.queue_free()
