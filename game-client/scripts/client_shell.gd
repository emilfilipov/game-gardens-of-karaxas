extends Control

const WORLD_CANVAS_SCENE = preload("res://scripts/world_canvas.gd")

const DEFAULT_API_BASE_URL = "https://karaxas-backend-rss3xj2ixq-ew.a.run.app"
const DEFAULT_CLIENT_VERSION = "0.0.0"
const DEFAULT_CONTENT_VERSION = "unknown"

const MENU_UPDATE = 1
const MENU_LOG_VIEWER = 2
const MENU_LOGOUT = 3
const MENU_EXIT = 4
const MENU_SETTINGS = 6
const MENU_LOGOUT_CHARACTER = 7
const MENU_LEVEL_EDITOR = 8
const MENU_ASSET_EDITOR = 9
const MENU_CONTENT_VERSIONS = 10
const MENU_LEVEL_ORDER = 11

var api_base_url = DEFAULT_API_BASE_URL
var client_version = DEFAULT_CLIENT_VERSION
var client_content_version_key = DEFAULT_CONTENT_VERSION
var client_content_contract = ""
var release_summary: Dictionary = {}
var content_domains: Dictionary = {}

var access_token = ""
var refresh_token = ""
var session_email = ""
var session_display_name = ""
var session_is_admin = false

var characters: Array = []
var selected_character_index = -1
var active_level_id: int = -1
var active_level_name = "Default"
var active_world_ready = false
var active_character_id: int = -1
var ui_theme: Theme

var install_root_path = ""
var logs_root_path = ""
var prefs_path = ""
var level_draft_path = ""
var asset_draft_path = ""
var settings_dirty = false
var suppress_settings_events = false
var character_texture_cache: Dictionary = {}
var admin_levels_cache: Array = []
var character_row_level_overrides: Dictionary = {}

var register_mode = false
var current_screen_name = "auth"
var screen_nodes: Dictionary = {}

var header_title: Label
var menu_button: Button
var menu_popup: PopupMenu
var footer_status: Label
var main_stack: Control
var background_art: TextureRect
var background_veil: ColorRect

var auth_container: VBoxContainer
var auth_email_input: LineEdit
var auth_password_input: LineEdit
var auth_otp_input: LineEdit
var auth_display_name_input: LineEdit
var auth_submit_button: Button
var auth_toggle_button: Button
var auth_status_label: Label
var auth_release_notes: RichTextLabel
var auth_update_button: Button

var account_container: VBoxContainer
var account_status_label: Label
var character_tabs: TabContainer
var character_rows_scroll: ScrollContainer
var character_rows_container: VBoxContainer
var character_details_label: RichTextLabel
var character_preview_texture: TextureRect
var character_list_title_label: Label

var create_name_input: LineEdit
var create_sex_option: OptionButton
var create_race_option: OptionButton
var create_background_option: OptionButton
var create_affiliation_option: OptionButton
var create_preview_texture: TextureRect
var create_points_left_label: Label
var create_stats_grid: GridContainer
var create_skills_grid: GridContainer
var create_status_label: Label
var create_submit_button: Button
var create_stat_keys: Array[String] = []
var create_skill_keys: Array[String] = []
var create_stat_values: Dictionary = {}
var create_skill_values: Dictionary = {}
var create_skill_buttons: Dictionary = {}
var create_point_budget: int = 10
var create_stat_max_per_entry: int = 10

var world_container: VBoxContainer
var world_status_label: Label
var world_canvas: Control

var log_container: VBoxContainer
var log_file_option: OptionButton
var log_text_view: TextEdit
var log_status_label: Label
var log_back_button: Button

var settings_container: VBoxContainer
var settings_status_label: Label
var settings_screen_mode: OptionButton
var settings_audio_mute: Button
var settings_audio_volume: HSlider
var settings_mfa_status_label: Label
var settings_mfa_otp_input: LineEdit
var settings_mfa_toggle: Button
var settings_mfa_secret_output: TextEdit
var settings_mfa_generate_button: Button
var settings_save_button: Button
var settings_cancel_button: Button
var settings_mfa_last_secret = ""
var settings_mfa_last_uri = ""
var settings_mfa_last_qr_svg = ""

var level_editor_container: VBoxContainer
var level_editor_status: Label
var level_editor_level_option: OptionButton
var level_editor_name_input: LineEdit
var level_editor_descriptive_input: LineEdit
var level_editor_order_input: LineEdit
var level_editor_width_input: LineEdit
var level_editor_height_input: LineEdit
var level_editor_spawn_x_input: LineEdit
var level_editor_spawn_y_input: LineEdit
var level_editor_asset_option: OptionButton
var level_editor_layer_option: OptionButton
var level_editor_show_layer_checks: Dictionary = {}
var level_editor_canvas_scroll: ScrollContainer
var level_editor_canvas: Control
var level_editor_layers_input: TextEdit
var level_editor_transitions_input: TextEdit
var level_editor_pending_list: ItemList
var level_editor_local_drafts: Array = []
var level_editor_levels_cache: Array = []

var level_order_container: VBoxContainer
var level_order_status: Label
var level_order_list: ItemList
var level_order_levels: Array = []

var asset_editor_container: VBoxContainer
var asset_editor_status: Label
var asset_editor_version_option: OptionButton
var asset_editor_domain_option: OptionButton
var asset_editor_search_input: LineEdit
var asset_editor_card_list: ItemList
var asset_editor_payload_input: TextEdit
var asset_editor_pending_list: ItemList
var asset_editor_local_drafts: Array = []
var asset_editor_versions_cache: Array = []
var asset_editor_active_domains: Dictionary = {}
var asset_editor_cards: Array = []
var asset_editor_selected_card_index: int = -1

var versions_container: VBoxContainer
var versions_status: Label
var versions_list: ItemList
var versions_details: TextEdit
var versions_compare_a: OptionButton
var versions_compare_b: OptionButton
var versions_compare_output: TextEdit
var versions_compare_left: TextEdit
var versions_compare_right: TextEdit

func _ready() -> void:
	_resolve_paths()
	_append_log("Godot shell startup.")
	_apply_window_icon()
	_apply_default_window_mode()
	_load_client_version()
	_build_theme()
	_build_ui()
	_load_last_email_pref()
	_load_level_editor_drafts()
	_load_asset_editor_drafts()
	call_deferred("_async_bootstrap")

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		call_deferred("_handle_exit_request")

func _handle_exit_request() -> void:
	await _persist_active_character_location()
	get_tree().quit()

func _async_bootstrap() -> void:
	_set_footer_status("Loading client bootstrap...")
	await _refresh_content_bootstrap()
	await _refresh_release_summary()
	_set_footer_status("Ready.")
	_show_screen("auth")

func _build_theme() -> void:
	ui_theme = Theme.new()

	var panel_box = StyleBoxFlat.new()
	panel_box.bg_color = Color(0.14, 0.10, 0.08, 0.96)
	panel_box.border_width_left = 1
	panel_box.border_width_top = 1
	panel_box.border_width_right = 1
	panel_box.border_width_bottom = 1
	panel_box.border_color = Color(0.68, 0.52, 0.34, 1.0)
	panel_box.corner_radius_top_left = 2
	panel_box.corner_radius_top_right = 2
	panel_box.corner_radius_bottom_left = 2
	panel_box.corner_radius_bottom_right = 2

	var panel_box_alt = panel_box.duplicate()
	panel_box_alt.bg_color = Color(0.18, 0.13, 0.10, 0.98)

	var button_normal = panel_box_alt.duplicate()
	var button_hover = panel_box_alt.duplicate()
	button_hover.bg_color = Color(0.24, 0.18, 0.13, 1.0)
	var button_pressed = panel_box_alt.duplicate()
	button_pressed.bg_color = Color(0.29, 0.21, 0.15, 1.0)

	var input_box = panel_box.duplicate()
	input_box.bg_color = Color(0.13, 0.10, 0.08, 0.98)
	var input_focus = input_box.duplicate()
	input_focus.border_color = Color(0.88, 0.72, 0.47, 1.0)
	input_focus.border_width_left = 2
	input_focus.border_width_top = 2
	input_focus.border_width_right = 2
	input_focus.border_width_bottom = 2

	ui_theme.set_stylebox("panel", "PanelContainer", panel_box)
	ui_theme.set_stylebox("normal", "Button", button_normal)
	ui_theme.set_stylebox("hover", "Button", button_hover)
	ui_theme.set_stylebox("pressed", "Button", button_pressed)
	ui_theme.set_stylebox("focus", "Button", button_hover)
	ui_theme.set_color("font_color", "Button", Color(0.95, 0.89, 0.77))
	ui_theme.set_color("font_focus_color", "Button", Color(0.98, 0.92, 0.80))
	ui_theme.set_color("font_hover_color", "Button", Color(0.98, 0.92, 0.80))
	ui_theme.set_color("font_pressed_color", "Button", Color(0.98, 0.92, 0.80))

	ui_theme.set_stylebox("normal", "LineEdit", input_box)
	ui_theme.set_stylebox("focus", "LineEdit", input_focus)
	ui_theme.set_stylebox("read_only", "LineEdit", input_box)
	ui_theme.set_color("font_color", "LineEdit", Color(0.95, 0.89, 0.77))
	ui_theme.set_color("font_placeholder_color", "LineEdit", Color(0.72, 0.62, 0.49))

	ui_theme.set_stylebox("normal", "TextEdit", input_box)
	ui_theme.set_stylebox("focus", "TextEdit", input_focus)
	ui_theme.set_color("font_color", "TextEdit", Color(0.95, 0.89, 0.77))

	ui_theme.set_stylebox("normal", "ItemList", input_box)
	ui_theme.set_stylebox("focus", "ItemList", input_focus)
	ui_theme.set_color("font_color", "ItemList", Color(0.95, 0.89, 0.77))
	ui_theme.set_color("font_selected_color", "ItemList", Color(0.15, 0.10, 0.07))
	ui_theme.set_color("background", "ItemList", Color(0.13, 0.10, 0.08))
	ui_theme.set_color("guide_color", "ItemList", Color(0.33, 0.25, 0.17))
	ui_theme.set_color("selection_fill", "ItemList", Color(0.84, 0.68, 0.44))

	ui_theme.set_stylebox("panel", "TabContainer", panel_box)
	ui_theme.set_stylebox("tab_unselected", "TabBar", button_normal)
	ui_theme.set_stylebox("tab_selected", "TabBar", button_pressed)
	ui_theme.set_color("font_selected_color", "TabBar", Color(0.97, 0.91, 0.79))
	ui_theme.set_color("font_unselected_color", "TabBar", Color(0.82, 0.72, 0.58))

	ui_theme.set_stylebox("normal", "OptionButton", button_normal)
	ui_theme.set_stylebox("hover", "OptionButton", button_hover)
	ui_theme.set_stylebox("pressed", "OptionButton", button_pressed)
	ui_theme.set_stylebox("focus", "OptionButton", button_hover)
	ui_theme.set_color("font_color", "OptionButton", Color(0.95, 0.89, 0.77))
	ui_theme.set_color("font_hover_color", "OptionButton", Color(0.98, 0.92, 0.80))
	ui_theme.set_color("font_pressed_color", "OptionButton", Color(0.98, 0.92, 0.80))

	ui_theme.set_stylebox("panel", "PopupMenu", panel_box_alt)
	ui_theme.set_stylebox("hover", "PopupMenu", button_pressed)
	ui_theme.set_stylebox("separator", "PopupMenu", button_normal)
	ui_theme.set_color("font_color", "PopupMenu", Color(0.95, 0.89, 0.77))
	ui_theme.set_color("font_hover_color", "PopupMenu", Color(0.15, 0.10, 0.07))
	ui_theme.set_color("font_disabled_color", "PopupMenu", Color(0.55, 0.45, 0.35))
	ui_theme.set_stylebox("normal", "CheckBox", button_normal)
	ui_theme.set_stylebox("hover", "CheckBox", button_hover)
	ui_theme.set_stylebox("pressed", "CheckBox", button_pressed)
	ui_theme.set_stylebox("focus", "CheckBox", button_hover)
	ui_theme.set_color("font_color", "CheckBox", Color(0.95, 0.89, 0.77))
	ui_theme.set_stylebox("slider", "HSlider", button_normal)
	ui_theme.set_stylebox("grabber_area", "HSlider", input_box)
	ui_theme.set_stylebox("grabber_area_highlight", "HSlider", input_focus)
	ui_theme.set_color("font_color", "Label", Color(0.95, 0.89, 0.77))

	theme = ui_theme

func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS

	background_art = TextureRect.new()
	background_art.set_anchors_preset(Control.PRESET_FULL_RECT)
	background_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	background_art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	background_art.texture = _load_texture_from_path("res://assets/main_menu_background.png")
	if background_art.texture == null:
		var fallback_bg = _load_texture_from_path(_path_join(install_root_path, "game-client/assets/main_menu_background.png"))
		if fallback_bg == null:
			fallback_bg = _load_texture_from_path(_path_join(install_root_path, "assets/main_menu_background.png"))
		if fallback_bg != null:
			background_art.texture = fallback_bg
		else:
			_append_log("Background art could not be loaded from bundled or install paths.")
	add_child(background_art)

	background_veil = ColorRect.new()
	background_veil.set_anchors_preset(Control.PRESET_FULL_RECT)
	background_veil.color = Color(0.03, 0.02, 0.02, 0.30)
	add_child(background_veil)

	var root = MarginContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("margin_left", 18)
	root.add_theme_constant_override("margin_top", 14)
	root.add_theme_constant_override("margin_right", 18)
	root.add_theme_constant_override("margin_bottom", 14)
	add_child(root)

	var layout = VBoxContainer.new()
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", 10)
	root.add_child(layout)

	var header = HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	layout.add_child(header)

	header_title = Label.new()
	header_title.text = "Gardens of Karaxas"
	header_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	header_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_title.add_theme_font_size_override("font_size", 36)
	header_title.add_theme_color_override("font_color", Color(0.95, 0.90, 0.79))
	header.add_child(header_title)

	menu_button = Button.new()
	menu_button.text = "..."
	menu_button.custom_minimum_size = Vector2(44, 44)
	menu_button.pressed.connect(_on_menu_button_pressed)
	header.add_child(menu_button)

	menu_popup = PopupMenu.new()
	add_child(menu_popup)
	menu_popup.id_pressed.connect(_on_menu_item_pressed)

	main_stack = Control.new()
	main_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	main_stack.set_anchors_preset(Control.PRESET_FULL_RECT)
	layout.add_child(main_stack)

	auth_container = _build_auth_screen()
	_register_screen("auth", auth_container)

	account_container = _build_account_screen()
	_register_screen("account", account_container)

	world_container = _build_world_screen()
	_register_screen("world", world_container)

	log_container = _build_log_screen()
	_register_screen("logs", log_container)

	settings_container = _build_settings_screen()
	_register_screen("settings", settings_container)

	level_editor_container = _build_level_editor_screen()
	_register_screen("level_editor", level_editor_container)

	level_order_container = _build_level_order_screen()
	_register_screen("level_order", level_order_container)

	asset_editor_container = _build_asset_editor_screen()
	_register_screen("asset_editor", asset_editor_container)

	versions_container = _build_content_versions_screen()
	_register_screen("content_versions", versions_container)

	footer_status = Label.new()
	footer_status.text = " "
	footer_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	footer_status.add_theme_font_size_override("font_size", 14)
	footer_status.add_theme_color_override("font_color", Color(0.94, 0.84, 0.69))
	layout.add_child(footer_status)

	_show_screen("auth")

func _build_auth_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 10)

	var body = HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 12)
	wrap.add_child(body)

	var auth_panel = PanelContainer.new()
	auth_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	auth_panel.size_flags_stretch_ratio = 0.5
	body.add_child(auth_panel)

	var auth_inner = VBoxContainer.new()
	auth_inner.add_theme_constant_override("separation", 8)
	auth_inner.size_flags_vertical = Control.SIZE_EXPAND_FILL
	auth_panel.add_child(auth_inner)

	var auth_title = Label.new()
	auth_title.text = "Account"
	auth_title.add_theme_font_size_override("font_size", 24)
	auth_title.add_theme_color_override("font_color", Color(0.95, 0.89, 0.77))
	auth_inner.add_child(auth_title)

	auth_display_name_input = _line_edit("Display Name")
	auth_display_name_input.text_submitted.connect(func(_text: String) -> void:
		_on_auth_submit()
	)
	auth_inner.add_child(auth_display_name_input)
	auth_email_input = _line_edit("Email")
	auth_email_input.text_submitted.connect(func(_text: String) -> void:
		_on_auth_submit()
	)
	auth_inner.add_child(auth_email_input)
	auth_password_input = _line_edit("Password", true)
	auth_password_input.text_submitted.connect(func(_text: String) -> void:
		_on_auth_submit()
	)
	auth_inner.add_child(auth_password_input)
	auth_otp_input = _line_edit("MFA Code (if enabled)")
	auth_otp_input.text_submitted.connect(func(_text: String) -> void:
		_on_auth_submit()
	)
	auth_inner.add_child(auth_otp_input)

	var auth_button_row = HBoxContainer.new()
	auth_button_row.add_theme_constant_override("separation", 8)
	auth_inner.add_child(auth_button_row)
	auth_submit_button = _button("Login")
	auth_submit_button.pressed.connect(_on_auth_submit)
	auth_button_row.add_child(auth_submit_button)
	auth_toggle_button = _button("Create Account")
	auth_toggle_button.pressed.connect(_on_auth_toggle_mode)
	auth_button_row.add_child(auth_toggle_button)
	var auth_exit_button = _button("Exit")
	auth_exit_button.pressed.connect(_handle_exit_request)
	auth_button_row.add_child(auth_exit_button)

	auth_status_label = Label.new()
	auth_status_label.text = " "
	auth_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	auth_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	auth_inner.add_child(auth_status_label)

	var update_panel = PanelContainer.new()
	update_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	update_panel.size_flags_stretch_ratio = 0.5
	body.add_child(update_panel)
	var update_inner = VBoxContainer.new()
	update_inner.size_flags_vertical = Control.SIZE_EXPAND_FILL
	update_inner.add_theme_constant_override("separation", 8)
	update_panel.add_child(update_inner)
	var update_title = Label.new()
	update_title.text = "Release Notes"
	update_title.add_theme_font_size_override("font_size", 24)
	update_title.add_theme_color_override("font_color", Color(0.95, 0.89, 0.77))
	update_inner.add_child(update_title)
	auth_release_notes = RichTextLabel.new()
	auth_release_notes.fit_content = false
	auth_release_notes.scroll_active = true
	auth_release_notes.bbcode_enabled = false
	auth_release_notes.size_flags_vertical = Control.SIZE_EXPAND_FILL
	auth_release_notes.custom_minimum_size = Vector2(420, 360)
	auth_release_notes.add_theme_color_override("default_color", Color(0.94, 0.85, 0.71))
	update_inner.add_child(auth_release_notes)
	auth_update_button = _button("Update & Restart")
	auth_update_button.pressed.connect(_on_update_and_restart_pressed)
	update_inner.add_child(auth_update_button)

	_apply_auth_mode()
	return wrap

func _build_account_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)

	account_status_label = Label.new()
	account_status_label.text = " "
	account_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	wrap.add_child(account_status_label)

	character_tabs = TabContainer.new()
	character_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(character_tabs)

	var list_tab = VBoxContainer.new()
	list_tab.name = "Character List"
	list_tab.add_theme_constant_override("separation", 8)
	character_tabs.add_child(list_tab)

	var list_split = HSplitContainer.new()
	list_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list_tab.add_child(list_split)

	var list_left = PanelContainer.new()
	list_left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list_left.size_flags_stretch_ratio = 0.73
	list_split.add_child(list_left)
	var list_left_inner = VBoxContainer.new()
	list_left_inner.add_theme_constant_override("separation", 8)
	list_left_inner.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list_left.add_child(list_left_inner)
	character_list_title_label = _label("Character List")
	character_list_title_label.add_theme_font_size_override("font_size", 22)
	list_left_inner.add_child(character_list_title_label)
	character_rows_scroll = ScrollContainer.new()
	character_rows_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	character_rows_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	list_left_inner.add_child(character_rows_scroll)
	character_rows_container = VBoxContainer.new()
	character_rows_container.add_theme_constant_override("separation", 6)
	character_rows_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	character_rows_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	character_rows_scroll.add_child(character_rows_container)

	var list_right = PanelContainer.new()
	list_right.custom_minimum_size = Vector2(340, 420)
	list_right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list_split.add_child(list_right)
	var list_right_inner = VBoxContainer.new()
	list_right_inner.add_theme_constant_override("separation", 8)
	list_right.add_child(list_right_inner)
	var preview_panel = PanelContainer.new()
	preview_panel.custom_minimum_size = Vector2(320, 220)
	list_right_inner.add_child(preview_panel)
	character_preview_texture = TextureRect.new()
	character_preview_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	character_preview_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	character_preview_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	preview_panel.add_child(character_preview_texture)
	character_details_label = RichTextLabel.new()
	character_details_label.fit_content = false
	character_details_label.bbcode_enabled = false
	character_details_label.custom_minimum_size = Vector2(320, 220)
	character_details_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	character_details_label.add_theme_color_override("default_color", Color(0.94, 0.84, 0.69))
	list_right_inner.add_child(character_details_label)

	var create_tab = VBoxContainer.new()
	create_tab.name = "Create Character"
	create_tab.add_theme_constant_override("separation", 8)
	character_tabs.add_child(create_tab)

	var create_shell = PanelContainer.new()
	create_shell.size_flags_vertical = Control.SIZE_EXPAND_FILL
	create_tab.add_child(create_shell)
	var create_root = VBoxContainer.new()
	create_root.add_theme_constant_override("separation", 10)
	create_root.size_flags_vertical = Control.SIZE_EXPAND_FILL
	create_shell.add_child(create_root)

	var create_body = HBoxContainer.new()
	create_body.add_theme_constant_override("separation", 10)
	create_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	create_root.add_child(create_body)

	var create_preview_panel = PanelContainer.new()
	create_preview_panel.custom_minimum_size = Vector2(230, 420)
	create_body.add_child(create_preview_panel)
	create_preview_texture = TextureRect.new()
	create_preview_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	create_preview_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	create_preview_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	create_preview_panel.add_child(create_preview_texture)

	var create_right = VBoxContainer.new()
	create_right.add_theme_constant_override("separation", 10)
	create_right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	create_body.add_child(create_right)

	var identity_row = HBoxContainer.new()
	identity_row.add_theme_constant_override("separation", 8)
	create_right.add_child(identity_row)
	create_name_input = _line_edit("Character Name")
	create_name_input.custom_minimum_size = Vector2(190, 36)
	identity_row.add_child(_labeled_control("Name", create_name_input))
	create_sex_option = _option(["Male", "Female"])
	create_sex_option.custom_minimum_size = Vector2(190, 36)
	create_sex_option.item_selected.connect(func(_index: int) -> void:
		_refresh_create_character_preview()
	)
	identity_row.add_child(_labeled_control("Sex", create_sex_option))
	create_race_option = _option(["Human"])
	create_race_option.custom_minimum_size = Vector2(190, 36)
	identity_row.add_child(_labeled_control("Race", create_race_option))
	create_background_option = _option(["Drifter"])
	create_background_option.custom_minimum_size = Vector2(190, 36)
	identity_row.add_child(_labeled_control("Background", create_background_option))
	create_affiliation_option = _option(["Unaffiliated"])
	create_affiliation_option.custom_minimum_size = Vector2(190, 36)
	identity_row.add_child(_labeled_control("Affiliation", create_affiliation_option))

	var create_tables = HSplitContainer.new()
	create_tables.size_flags_vertical = Control.SIZE_EXPAND_FILL
	create_right.add_child(create_tables)

	var stats_panel = PanelContainer.new()
	stats_panel.custom_minimum_size = Vector2(570, 320)
	create_tables.add_child(stats_panel)
	var stats_inner = VBoxContainer.new()
	stats_inner.add_theme_constant_override("separation", 8)
	stats_panel.add_child(stats_inner)
	var stats_title = _label("Stats")
	stats_title.add_theme_font_size_override("font_size", 18)
	stats_inner.add_child(stats_title)
	create_stats_grid = GridContainer.new()
	create_stats_grid.columns = 5
	create_stats_grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	create_stats_grid.add_theme_constant_override("h_separation", 6)
	create_stats_grid.add_theme_constant_override("v_separation", 6)
	stats_inner.add_child(create_stats_grid)

	var skills_panel = PanelContainer.new()
	skills_panel.custom_minimum_size = Vector2(570, 320)
	create_tables.add_child(skills_panel)
	var skills_inner = VBoxContainer.new()
	skills_inner.add_theme_constant_override("separation", 8)
	skills_panel.add_child(skills_inner)
	var skills_title = _label("Skills")
	skills_title.add_theme_font_size_override("font_size", 18)
	skills_inner.add_child(skills_title)
	create_skills_grid = GridContainer.new()
	create_skills_grid.columns = 6
	create_skills_grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	create_skills_grid.add_theme_constant_override("h_separation", 6)
	create_skills_grid.add_theme_constant_override("v_separation", 6)
	skills_inner.add_child(create_skills_grid)

	var footer_row = HBoxContainer.new()
	footer_row.add_theme_constant_override("separation", 10)
	create_right.add_child(footer_row)
	create_points_left_label = _label("10/10 points left")
	footer_row.add_child(create_points_left_label)
	footer_row.add_spacer(false)
	create_submit_button = _button("Create Character")
	create_submit_button.custom_minimum_size = Vector2(220, 42)
	create_submit_button.pressed.connect(_on_create_character_pressed)
	footer_row.add_child(create_submit_button)

	create_status_label = Label.new()
	create_status_label.text = " "
	create_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	create_root.add_child(create_status_label)
	_populate_character_creation_tables(content_domains.get("character_options", {}))
	_refresh_create_character_preview()

	return wrap

func _build_world_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)

	world_status_label = Label.new()
	world_status_label.text = "WASD to move."
	world_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	wrap.add_child(world_status_label)

	world_canvas = Control.new()
	world_canvas.set_script(WORLD_CANVAS_SCENE)
	world_canvas.size_flags_vertical = Control.SIZE_EXPAND_FILL
	world_canvas.custom_minimum_size = Vector2(800, 460)
	world_canvas.connect("player_position_changed", _on_world_position_changed)
	wrap.add_child(world_canvas)
	return wrap

func _build_log_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)

	var row = HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	wrap.add_child(row)

	log_file_option = _option(["launcher.log", "game.log", "velopack.log", "godot.log"])
	row.add_child(log_file_option)
	var refresh = _button("Reload")
	refresh.pressed.connect(_reload_log_view)
	row.add_child(refresh)
	log_back_button = _button("Back")
	log_back_button.pressed.connect(func() -> void:
		_show_screen("account")
	)
	row.add_child(log_back_button)

	log_status_label = Label.new()
	log_status_label.text = " "
	log_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	wrap.add_child(log_status_label)

	log_text_view = TextEdit.new()
	log_text_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log_text_view.editable = false
	wrap.add_child(log_text_view)

	return wrap

func _register_screen(name: String, screen: Control) -> void:
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.offset_left = 0
	screen.offset_top = 0
	screen.offset_right = 0
	screen.offset_bottom = 0
	main_stack.add_child(screen)
	screen_nodes[name] = screen

func _build_settings_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)
	var title = Label.new()
	title.text = "Settings"
	title.add_theme_font_size_override("font_size", 24)
	title.add_theme_color_override("font_color", Color(0.95, 0.89, 0.77))
	wrap.add_child(title)

	var tabs = TabContainer.new()
	tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(tabs)

	var video_tab = VBoxContainer.new()
	video_tab.name = "Video"
	video_tab.add_theme_constant_override("separation", 8)
	tabs.add_child(video_tab)
	video_tab.add_child(_label("Screen Mode"))
	settings_screen_mode = _option(["Borderless Fullscreen", "Windowed"])
	settings_screen_mode.item_selected.connect(func(_index: int) -> void:
		_mark_settings_dirty()
	)
	video_tab.add_child(settings_screen_mode)

	var audio_tab = VBoxContainer.new()
	audio_tab.name = "Audio"
	audio_tab.add_theme_constant_override("separation", 8)
	tabs.add_child(audio_tab)
	settings_audio_mute = _button("Muted: OFF")
	settings_audio_mute.toggle_mode = true
	settings_audio_mute.toggled.connect(func(_checked: bool) -> void:
		settings_audio_mute.text = "Muted: ON" if settings_audio_mute.button_pressed else "Muted: OFF"
		_mark_settings_dirty()
	)
	audio_tab.add_child(settings_audio_mute)
	settings_audio_volume = HSlider.new()
	settings_audio_volume.min_value = 0
	settings_audio_volume.max_value = 100
	settings_audio_volume.step = 1
	settings_audio_volume.value_changed.connect(func(_value: float) -> void:
		_mark_settings_dirty()
	)
	audio_tab.add_child(settings_audio_volume)

	var security_tab = VBoxContainer.new()
	security_tab.name = "Security"
	security_tab.add_theme_constant_override("separation", 8)
	tabs.add_child(security_tab)
	settings_mfa_status_label = _label("MFA: Loading...")
	security_tab.add_child(settings_mfa_status_label)

	var mfa_toggle_row = HBoxContainer.new()
	mfa_toggle_row.add_theme_constant_override("separation", 8)
	security_tab.add_child(mfa_toggle_row)
	settings_mfa_toggle = _button("MFA: OFF")
	settings_mfa_toggle.toggle_mode = true
	settings_mfa_toggle.custom_minimum_size = Vector2(160, 36)
	settings_mfa_toggle.toggled.connect(func(pressed: bool) -> void:
		settings_mfa_toggle.text = "MFA: ON" if pressed else "MFA: OFF"
	)
	mfa_toggle_row.add_child(settings_mfa_toggle)
	settings_mfa_otp_input = _line_edit("Authenticator code")
	settings_mfa_otp_input.custom_minimum_size = Vector2(280, 36)
	mfa_toggle_row.add_child(settings_mfa_otp_input)

	var mfa_button_row = HBoxContainer.new()
	mfa_button_row.add_theme_constant_override("separation", 8)
	security_tab.add_child(mfa_button_row)
	settings_mfa_generate_button = _button("Generate/Rotate Secret")
	settings_mfa_generate_button.pressed.connect(_generate_settings_mfa_secret)
	mfa_button_row.add_child(settings_mfa_generate_button)
	var mfa_show_qr = _button("Show QR")
	mfa_show_qr.pressed.connect(_show_settings_mfa_qr)
	mfa_button_row.add_child(mfa_show_qr)
	var mfa_apply = _button("Apply MFA")
	mfa_apply.pressed.connect(_apply_settings_mfa_toggle)
	mfa_button_row.add_child(mfa_apply)
	settings_mfa_secret_output = TextEdit.new()
	settings_mfa_secret_output.editable = false
	settings_mfa_secret_output.custom_minimum_size = Vector2(640, 150)
	settings_mfa_secret_output.text = "MFA setup details will appear here."
	security_tab.add_child(settings_mfa_secret_output)

	var action_row = HBoxContainer.new()
	action_row.add_theme_constant_override("separation", 8)
	wrap.add_child(action_row)
	settings_save_button = _button("Save")
	settings_save_button.pressed.connect(_on_settings_save_pressed)
	action_row.add_child(settings_save_button)
	settings_cancel_button = _button("Cancel")
	settings_cancel_button.pressed.connect(_on_settings_cancel_pressed)
	action_row.add_child(settings_cancel_button)
	var back_button = _button("Back to Account")
	back_button.pressed.connect(func() -> void:
		_show_screen("account")
	)
	action_row.add_child(back_button)

	settings_status_label = _label(" ")
	wrap.add_child(settings_status_label)
	return wrap

func _build_level_editor_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)
	var title = _label("Level Editor (Admin)")
	title.add_theme_font_size_override("font_size", 24)
	wrap.add_child(title)

	var top_row_1 = HBoxContainer.new()
	top_row_1.add_theme_constant_override("separation", 8)
	wrap.add_child(top_row_1)
	top_row_1.add_child(_label("Load Existing"))
	level_editor_level_option = _option(["No levels"])
	level_editor_level_option.custom_minimum_size = Vector2(220, 34)
	top_row_1.add_child(level_editor_level_option)
	var load_level = _button("Load")
	load_level.custom_minimum_size = Vector2(100, 34)
	load_level.pressed.connect(_load_selected_level_into_editor)
	top_row_1.add_child(load_level)
	var refresh_levels = _button("Reload")
	refresh_levels.custom_minimum_size = Vector2(100, 34)
	refresh_levels.pressed.connect(_refresh_level_editor_levels)
	top_row_1.add_child(refresh_levels)
	top_row_1.add_child(_label("Name"))
	level_editor_name_input = _line_edit("level_name")
	level_editor_name_input.custom_minimum_size = Vector2(150, 34)
	top_row_1.add_child(level_editor_name_input)
	top_row_1.add_child(_label("Descriptive"))
	level_editor_descriptive_input = _line_edit("Display Name")
	level_editor_descriptive_input.custom_minimum_size = Vector2(170, 34)
	top_row_1.add_child(level_editor_descriptive_input)
	top_row_1.add_child(_label("Order"))
	level_editor_order_input = _line_edit("1")
	level_editor_order_input.custom_minimum_size = Vector2(72, 34)
	level_editor_order_input.tooltip_text = "Tower floor order index. Lower values appear earlier in progression."
	top_row_1.add_child(level_editor_order_input)
	var save_local = _button("Save Local")
	save_local.custom_minimum_size = Vector2(110, 34)
	save_local.pressed.connect(_save_level_editor_local_draft)
	top_row_1.add_child(save_local)
	var publish = _button("Publish Changes")
	publish.custom_minimum_size = Vector2(135, 34)
	publish.pressed.connect(_publish_level_editor_drafts)
	top_row_1.add_child(publish)
	var back = _button("Back")
	back.custom_minimum_size = Vector2(90, 34)
	back.pressed.connect(func() -> void:
		_show_screen("account")
	)
	top_row_1.add_child(back)

	var top_row_2 = HBoxContainer.new()
	top_row_2.add_theme_constant_override("separation", 8)
	wrap.add_child(top_row_2)
	top_row_2.add_child(_label("Width"))
	level_editor_width_input = _line_edit("80")
	level_editor_width_input.custom_minimum_size = Vector2(82, 34)
	top_row_2.add_child(level_editor_width_input)
	top_row_2.add_child(_label("Height"))
	level_editor_height_input = _line_edit("48")
	level_editor_height_input.custom_minimum_size = Vector2(82, 34)
	top_row_2.add_child(level_editor_height_input)
	top_row_2.add_child(_label("Spawn X"))
	level_editor_spawn_x_input = _line_edit("3")
	level_editor_spawn_x_input.custom_minimum_size = Vector2(82, 34)
	top_row_2.add_child(level_editor_spawn_x_input)
	top_row_2.add_child(_label("Spawn Y"))
	level_editor_spawn_y_input = _line_edit("3")
	level_editor_spawn_y_input.custom_minimum_size = Vector2(82, 34)
	top_row_2.add_child(level_editor_spawn_y_input)

	var split = HSplitContainer.new()
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(split)
	var left = VBoxContainer.new()
	left.add_theme_constant_override("separation", 8)
	split.add_child(left)
	left.add_child(_label("Layers JSON"))
	level_editor_layers_input = TextEdit.new()
	level_editor_layers_input.size_flags_vertical = Control.SIZE_EXPAND_FILL
	level_editor_layers_input.custom_minimum_size = Vector2(520, 320)
	level_editor_layers_input.text = "{\n  \"0\": [],\n  \"1\": [],\n  \"2\": []\n}"
	left.add_child(level_editor_layers_input)
	left.add_child(_label("Transitions JSON"))
	level_editor_transitions_input = TextEdit.new()
	level_editor_transitions_input.custom_minimum_size = Vector2(520, 140)
	level_editor_transitions_input.text = "[]"
	left.add_child(level_editor_transitions_input)

	var right = VBoxContainer.new()
	right.add_theme_constant_override("separation", 8)
	split.add_child(right)
	right.add_child(_label("Local Draft Queue"))
	level_editor_pending_list = ItemList.new()
	level_editor_pending_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(level_editor_pending_list)

	level_editor_status = _label(" ")
	wrap.add_child(level_editor_status)
	return wrap

func _build_level_order_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)
	var title = _label("Level Order (Admin)")
	title.add_theme_font_size_override("font_size", 24)
	wrap.add_child(title)

	level_order_list = ItemList.new()
	level_order_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	level_order_list.custom_minimum_size = Vector2(520, 520)
	wrap.add_child(level_order_list)

	var actions = HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	wrap.add_child(actions)
	var move_up = _button("Move Up")
	move_up.pressed.connect(func() -> void:
		_move_level_order(-1)
	)
	actions.add_child(move_up)
	var move_down = _button("Move Down")
	move_down.pressed.connect(func() -> void:
		_move_level_order(1)
	)
	actions.add_child(move_down)
	var reload = _button("Reload")
	reload.pressed.connect(_refresh_level_order_list)
	actions.add_child(reload)
	var publish = _button("Publish Order")
	publish.pressed.connect(_publish_level_order)
	actions.add_child(publish)
	var back = _button("Back")
	back.pressed.connect(func() -> void:
		_show_screen("account")
	)
	actions.add_child(back)

	level_order_status = _label(" ")
	wrap.add_child(level_order_status)
	return wrap

func _build_asset_editor_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)
	var title = _label("Asset Editor (Admin)")
	title.add_theme_font_size_override("font_size", 24)
	wrap.add_child(title)

	var top = HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	wrap.add_child(top)
	asset_editor_version_option = _option(["No versions"])
	asset_editor_version_option.custom_minimum_size = Vector2(260, 34)
	asset_editor_version_option.item_selected.connect(func(_index: int) -> void:
		_load_asset_editor_selected_version()
	)
	top.add_child(asset_editor_version_option)
	asset_editor_domain_option = _option(["No domains"])
	asset_editor_domain_option.custom_minimum_size = Vector2(220, 34)
	asset_editor_domain_option.item_selected.connect(func(_index: int) -> void:
		_load_asset_editor_selected_domain_payload()
	)
	top.add_child(asset_editor_domain_option)
	var refresh_versions = _button("Refresh")
	refresh_versions.pressed.connect(_refresh_asset_editor_versions)
	top.add_child(refresh_versions)
	var back = _button("Back")
	back.pressed.connect(func() -> void:
		_show_screen("account")
	)
	top.add_child(back)

	var split = HSplitContainer.new()
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(split)
	asset_editor_payload_input = TextEdit.new()
	asset_editor_payload_input.size_flags_vertical = Control.SIZE_EXPAND_FILL
	asset_editor_payload_input.custom_minimum_size = Vector2(860, 520)
	split.add_child(asset_editor_payload_input)
	var pending_wrap = VBoxContainer.new()
	pending_wrap.add_theme_constant_override("separation", 8)
	pending_wrap.custom_minimum_size = Vector2(280, 520)
	split.add_child(pending_wrap)
	pending_wrap.add_child(_label("Pending Local Changes"))
	asset_editor_pending_list = ItemList.new()
	asset_editor_pending_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	pending_wrap.add_child(asset_editor_pending_list)

	var actions = HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	wrap.add_child(actions)
	var save_local = _button("Save Local")
	save_local.pressed.connect(_save_asset_editor_local_draft)
	actions.add_child(save_local)
	var publish = _button("Publish Changes")
	publish.pressed.connect(_publish_asset_editor_drafts)
	actions.add_child(publish)
	asset_editor_status = _label(" ")
	wrap.add_child(asset_editor_status)
	return wrap

func _build_content_versions_screen() -> VBoxContainer:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)
	var title = _label("Content Versions (Admin)")
	title.add_theme_font_size_override("font_size", 24)
	wrap.add_child(title)

	var split = HSplitContainer.new()
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(split)
	versions_list = ItemList.new()
	versions_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	versions_list.custom_minimum_size = Vector2(360, 420)
	versions_list.item_selected.connect(_on_versions_item_selected)
	split.add_child(versions_list)
	versions_details = TextEdit.new()
	versions_details.editable = false
	versions_details.size_flags_vertical = Control.SIZE_EXPAND_FILL
	split.add_child(versions_details)

	var compare_row = HBoxContainer.new()
	compare_row.add_theme_constant_override("separation", 8)
	wrap.add_child(compare_row)
	versions_compare_a = _option(["A"])
	compare_row.add_child(versions_compare_a)
	versions_compare_b = _option(["B"])
	compare_row.add_child(versions_compare_b)
	var run_compare = _button("Compare")
	run_compare.pressed.connect(_compare_content_versions)
	compare_row.add_child(run_compare)
	var refresh = _button("Refresh")
	refresh.pressed.connect(_refresh_content_versions)
	compare_row.add_child(refresh)
	var create_draft = _button("Create Draft")
	create_draft.pressed.connect(_create_content_draft)
	compare_row.add_child(create_draft)
	var validate = _button("Validate")
	validate.pressed.connect(_validate_selected_content_version)
	compare_row.add_child(validate)
	var activate = _button("Activate")
	activate.pressed.connect(_activate_selected_content_version)
	compare_row.add_child(activate)
	var rollback = _button("Rollback Prev")
	rollback.pressed.connect(_rollback_content_version)
	compare_row.add_child(rollback)
	var back = _button("Back")
	back.pressed.connect(func() -> void:
		_show_screen("account")
	)
	compare_row.add_child(back)

	versions_compare_output = TextEdit.new()
	versions_compare_output.editable = false
	versions_compare_output.custom_minimum_size = Vector2(960, 180)
	wrap.add_child(versions_compare_output)

	versions_status = _label(" ")
	wrap.add_child(versions_status)
	return wrap

func _line_edit(placeholder: String, secret = false) -> LineEdit:
	var input = LineEdit.new()
	input.placeholder_text = placeholder
	input.secret = secret
	input.custom_minimum_size = Vector2(200, 34)
	return input

func _label(text_value: String) -> Label:
	var label = Label.new()
	label.text = text_value
	label.add_theme_color_override("font_color", Color(0.95, 0.89, 0.77))
	return label

func _button(text_value: String) -> Button:
	var b = Button.new()
	b.text = text_value
	b.custom_minimum_size = Vector2(140, 36)
	return b

func _option(items: Array) -> OptionButton:
	var option = OptionButton.new()
	option.custom_minimum_size = Vector2(220, 34)
	for item in items:
		option.add_item(str(item))
	return option

func _labeled_control(label_text: String, control: Control) -> Control:
	var wrap = VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 4)
	wrap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var label = _label(label_text)
	wrap.add_child(label)
	wrap.add_child(control)
	return wrap

func _clear_children(node: Node) -> void:
	if node == null:
		return
	for child in node.get_children():
		child.queue_free()

func _refresh_create_character_preview() -> void:
	if create_preview_texture == null:
		return
	var appearance_key = "human_male"
	if create_sex_option != null and create_sex_option.selected == 1:
		appearance_key = "human_female"
	create_preview_texture.texture = _resolve_character_texture(appearance_key)

func _refresh_selected_character_preview() -> void:
	if character_preview_texture == null:
		return
	if selected_character_index < 0 or selected_character_index >= characters.size():
		character_preview_texture.texture = null
		return
	var row: Dictionary = characters[selected_character_index]
	var appearance_key = str(row.get("appearance_key", "human_male"))
	character_preview_texture.texture = _resolve_character_texture(appearance_key)

func _resolve_character_texture(appearance_key: String):
	var key = appearance_key.strip_edges().to_lower()
	if key.is_empty():
		key = "human_male"
	if character_texture_cache.has(key):
		var cached = character_texture_cache.get(key)
		if cached is Texture2D:
			return cached

	var file_name = "karaxas_human_female_idle_32.png" if key == "human_female" else "karaxas_human_male_idle_32.png"
	var candidates: Array[String] = []
	candidates.append("res://assets/characters/" + file_name)
	candidates.append(_path_join(install_root_path, "assets/characters/" + file_name))
	candidates.append(_path_join(install_root_path, "game-client/assets/characters/" + file_name))
	candidates.append(_path_join(OS.get_executable_path().get_base_dir(), "assets/characters/" + file_name))

	for path in candidates:
		var texture = _load_texture_from_path(path)
		if texture != null:
			character_texture_cache[key] = texture
			return texture
	return null

func _load_texture_from_path(path: String):
	if path.is_empty():
		return null
	var image = Image.new()
	if path.begins_with("res://"):
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

func _character_location_text(row: Dictionary) -> String:
	var level_name = "Default"
	if row.get("level_name", null) != null:
		level_name = str(row.get("level_name"))
	elif row.get("level_id", null) != null:
		level_name = "Level #" + str(row.get("level_id"))
	var x = row.get("location_x", null)
	var y = row.get("location_y", null)
	if x != null and y != null:
		return "%s (%s, %s)" % [level_name, str(x), str(y)]
	return level_name

func _set_selected_character(index: int) -> void:
	if index < 0 or index >= characters.size():
		selected_character_index = -1
		_render_character_details(-1)
		_render_character_rows()
		return
	selected_character_index = index
	_render_character_details(index)
	_render_character_rows()

func _render_character_rows() -> void:
	if character_rows_container == null:
		return
	_clear_children(character_rows_container)
	if characters.is_empty():
		var empty_label = _label("No characters yet. Create your first character.")
		empty_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		character_rows_container.add_child(empty_label)
		return
	for index in range(characters.size()):
		var row: Dictionary = characters[index]
		var row_index = index
		var row_character_id = int(row.get("id", -1))
		var card = PanelContainer.new()
		card.custom_minimum_size = Vector2(0, 84)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if index == selected_character_index:
			card.self_modulate = Color(1.08, 1.08, 1.08, 1.0)
		var card_inner = HBoxContainer.new()
		card_inner.add_theme_constant_override("separation", 8)
		card.add_child(card_inner)

		var summary_button = _button(
			"%s | Level %s | XP %s (next %s) | Location: %s"
			% [
				str(row.get("name", "Unnamed")),
				str(row.get("level", 1)),
				str(row.get("experience", 0)),
				str(row.get("experience_to_next_level", 100)),
				_character_location_text(row),
			]
		)
		summary_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		summary_button.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		summary_button.clip_text = true
		summary_button.pressed.connect(func() -> void:
			_set_selected_character(row_index)
		)
		card_inner.add_child(summary_button)

		if session_is_admin:
			var level_option = OptionButton.new()
			level_option.custom_minimum_size = Vector2(200, 36)
			level_option.add_item("Current location", -1)
			for level in admin_levels_cache:
				var level_label = str(level.get("descriptive_name", level.get("name", "Level")))
				var level_id = int(level.get("id", -1))
				level_option.add_item(level_label, level_id)
			var override_level = int(character_row_level_overrides.get(row_character_id, -1))
			for item_index in range(level_option.get_item_count()):
				if level_option.get_item_id(item_index) == override_level:
					level_option.selected = item_index
					break
			level_option.item_selected.connect(func(item_index: int) -> void:
				var selected_level_id = level_option.get_item_id(item_index)
				if selected_level_id <= 0:
					character_row_level_overrides.erase(row_character_id)
				else:
					character_row_level_overrides[row_character_id] = selected_level_id
			)
			card_inner.add_child(level_option)

		var play_button = _button("Play")
		play_button.custom_minimum_size = Vector2(110, 36)
		play_button.pressed.connect(func() -> void:
			_set_selected_character(row_index)
			_on_character_play_pressed()
		)
		card_inner.add_child(play_button)

		var delete_button = _button("Delete")
		delete_button.custom_minimum_size = Vector2(110, 36)
		delete_button.pressed.connect(func() -> void:
			_set_selected_character(row_index)
			_on_character_delete_pressed()
		)
		card_inner.add_child(delete_button)

		character_rows_container.add_child(card)

func _remaining_create_points() -> int:
	var used = 0
	for value in create_stat_values.values():
		used += int(value)
	for value in create_skill_values.values():
		if int(value) > 0:
			used += 1
	return max(0, create_point_budget - used)

func _refresh_create_points_label() -> void:
	if create_points_left_label == null:
		return
	create_points_left_label.text = "%d/%d points left" % [_remaining_create_points(), create_point_budget]

func _adjust_create_stat(stat_key: String, delta: int, value_label: Label) -> void:
	var current = int(create_stat_values.get(stat_key, 0))
	if delta > 0 and _remaining_create_points() <= 0:
		return
	var next_value = clampi(current + delta, 0, create_stat_max_per_entry)
	if next_value == current:
		return
	create_stat_values[stat_key] = next_value
	value_label.text = str(next_value)
	_refresh_create_points_label()

func _toggle_create_skill(skill_key: String, enabled: bool) -> void:
	var current = int(create_skill_values.get(skill_key, 0))
	if enabled and current == 0 and _remaining_create_points() <= 0:
		var button = create_skill_buttons.get(skill_key)
		if button is Button:
			button.button_pressed = false
		return
	create_skill_values[skill_key] = 1 if enabled else 0
	_refresh_create_points_label()

func _skill_tooltip(entry: Dictionary) -> String:
	return (
		"Name: %s\nType: %s\nMana: %s  Energy: %s  Life: %s\nEffects: %s\nDamage: %s\nCooldown: %ss\nDescription: %s"
		% [
			str(entry.get("label", entry.get("key", "Skill"))),
			str(entry.get("skill_type", "Unknown")),
			str(entry.get("mana_cost", 0)),
			str(entry.get("energy_cost", 0)),
			str(entry.get("life_cost", 0)),
			str(entry.get("effects", "Placeholder effect.")),
			str(entry.get("damage_text", "Placeholder damage.")),
			str(entry.get("cooldown_seconds", 0)),
			str(entry.get("description", "Placeholder description.")),
		]
	)

func _populate_character_creation_tables(options: Dictionary) -> void:
	if create_stats_grid == null or create_skills_grid == null:
		return
	create_point_budget = max(1, int(options.get("point_budget", 10)))
	create_stat_max_per_entry = max(1, int(content_domains.get("stats", {}).get("max_per_stat", 10)))
	create_stat_values.clear()
	create_skill_values.clear()
	create_skill_buttons.clear()
	create_stat_keys.clear()
	create_skill_keys.clear()
	_clear_children(create_stats_grid)
	_clear_children(create_skills_grid)

	var stat_entries: Array = content_domains.get("stats", {}).get("entries", [])
	if stat_entries.is_empty():
		stat_entries = [
			{"key": "strength", "label": "Strength", "description": "Power for heavy melee attacks."},
			{"key": "agility", "label": "Agility", "description": "Speed for movement and recovery."},
			{"key": "intellect", "label": "Intellect", "description": "Arcane output and spell control."},
			{"key": "vitality", "label": "Vitality", "description": "Base health and toughness."},
			{"key": "resolve", "label": "Resolve", "description": "Resistance against control effects."},
			{"key": "endurance", "label": "Endurance", "description": "Stamina and sustained effort."},
			{"key": "dexterity", "label": "Dexterity", "description": "Precision for weapons and tools."},
			{"key": "willpower", "label": "Willpower", "description": "Mental focus and channeling."},
		]

	for entry in stat_entries:
		if not (entry is Dictionary):
			continue
		var key = str(entry.get("key", "")).strip_edges().to_lower()
		if key.is_empty():
			continue
		var stat_key = key
		create_stat_keys.append(stat_key)
		create_stat_values[stat_key] = 0

		var stat_label = _label(str(entry.get("label", key.capitalize())))
		stat_label.custom_minimum_size = Vector2(130, 40)
		create_stats_grid.add_child(stat_label)

		var minus = _button("-")
		minus.custom_minimum_size = Vector2(38, 38)
		create_stats_grid.add_child(minus)

		var value_label = _label("0")
		value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		value_label.custom_minimum_size = Vector2(44, 38)
		create_stats_grid.add_child(value_label)

		var plus = _button("+")
		plus.custom_minimum_size = Vector2(38, 38)
		create_stats_grid.add_child(plus)

		var description = _label(str(entry.get("description", "Placeholder description.")))
		description.custom_minimum_size = Vector2(220, 40)
		description.clip_text = true
		description.tooltip_text = str(entry.get("tooltip", entry.get("description", "Placeholder tooltip.")))
		create_stats_grid.add_child(description)

		minus.pressed.connect(func() -> void:
			_adjust_create_stat(stat_key, -1, value_label)
		)
		plus.pressed.connect(func() -> void:
			_adjust_create_stat(stat_key, 1, value_label)
		)

	var skill_entries: Array = content_domains.get("skills", {}).get("entries", [])
	if skill_entries.is_empty():
		skill_entries = [
			{"key": "ember", "label": "Ember"},
			{"key": "cleave", "label": "Cleave"},
			{"key": "quick_strike", "label": "Quick Strike"},
			{"key": "bandage", "label": "Bandage"},
		]

	for entry in skill_entries:
		if not (entry is Dictionary):
			continue
		var key = str(entry.get("key", "")).strip_edges().to_lower()
		if key.is_empty():
			continue
		var skill_key = key
		create_skill_keys.append(skill_key)
		create_skill_values[skill_key] = 0
		var skill_button = _button(str(entry.get("label", skill_key)))
		skill_button.toggle_mode = true
		skill_button.custom_minimum_size = Vector2(74, 74)
		skill_button.tooltip_text = _skill_tooltip(entry)
		skill_button.toggled.connect(func(pressed: bool) -> void:
			_toggle_create_skill(skill_key, pressed)
		)
		create_skill_buttons[skill_key] = skill_button
		create_skills_grid.add_child(skill_button)

	while create_skills_grid.get_child_count() < 24:
		var placeholder = PanelContainer.new()
		placeholder.custom_minimum_size = Vector2(74, 74)
		create_skills_grid.add_child(placeholder)

	_refresh_create_points_label()
	_refresh_create_character_preview()

func _on_menu_button_pressed() -> void:
	_populate_menu()
	menu_popup.position = Vector2i(
		int(menu_button.global_position.x + menu_button.size.x - 220),
		int(menu_button.global_position.y + menu_button.size.y + 2)
	)
	menu_popup.reset_size()
	menu_popup.popup()

func _populate_menu() -> void:
	menu_popup.clear()
	if access_token != "":
		menu_popup.add_item("Welcome " + session_display_name, -1)
		menu_popup.set_item_disabled(menu_popup.get_item_count() - 1, true)
		menu_popup.add_separator()
		if _current_screen() == "world":
			menu_popup.add_item("Settings", MENU_SETTINGS)
			menu_popup.add_item("Logout Character", MENU_LOGOUT_CHARACTER)
			menu_popup.add_item("Logout Account", MENU_LOGOUT)
		else:
			menu_popup.add_item("Settings", MENU_SETTINGS)
			if session_is_admin:
				menu_popup.add_item("Level Editor", MENU_LEVEL_EDITOR)
				menu_popup.add_item("Level Order", MENU_LEVEL_ORDER)
				menu_popup.add_item("Asset Editor", MENU_ASSET_EDITOR)
				menu_popup.add_item("Content Versions", MENU_CONTENT_VERSIONS)
				menu_popup.add_item("Log Viewer", MENU_LOG_VIEWER)
			menu_popup.add_item("Update & Restart", MENU_UPDATE)
			menu_popup.add_item("Logout Account", MENU_LOGOUT)
	else:
		menu_popup.add_item("Update & Restart", MENU_UPDATE)
	menu_popup.add_item("Exit Game", MENU_EXIT)

func _on_menu_item_pressed(item_id: int) -> void:
	match item_id:
		MENU_SETTINGS:
			_open_settings_screen()
		MENU_UPDATE:
			_on_update_and_restart_pressed()
		MENU_LOG_VIEWER:
			if session_is_admin:
				_show_screen("logs")
				_reload_log_view()
		MENU_LEVEL_EDITOR:
			if session_is_admin:
				_show_screen("level_editor")
				_refresh_level_editor_levels()
		MENU_LEVEL_ORDER:
			if session_is_admin:
				_show_screen("level_order")
				_refresh_level_order_list()
		MENU_ASSET_EDITOR:
			if session_is_admin:
				_show_screen("asset_editor")
				_refresh_asset_editor_versions()
		MENU_CONTENT_VERSIONS:
			if session_is_admin:
				_show_screen("content_versions")
				_refresh_content_versions()
		MENU_LOGOUT:
			await _logout_account()
		MENU_LOGOUT_CHARACTER:
			await _persist_active_character_location()
			active_world_ready = false
			_show_screen("account")
		MENU_EXIT:
			await _persist_active_character_location()
			get_tree().quit()

func _show_screen(name: String) -> void:
	current_screen_name = name
	var in_world = name == "world"
	if background_art != null:
		background_art.visible = not in_world
	if background_veil != null:
		background_veil.visible = not in_world
	for key in screen_nodes.keys():
		var node = screen_nodes.get(key)
		if node is Control:
			node.visible = str(key) == name
	if world_canvas != null and world_canvas.has_method("set_active"):
		world_canvas.call("set_active", name == "world")
	menu_button.visible = name != "auth"
	footer_status.visible = not in_world
	if name == "auth":
		header_title.text = "Gardens of Karaxas"
	elif name == "world":
		header_title.text = ""
	elif name == "settings":
		header_title.text = "Settings"
	elif name == "level_editor":
		header_title.text = "Level Editor"
	elif name == "level_order":
		header_title.text = "Level Order"
	elif name == "asset_editor":
		header_title.text = "Asset Editor"
	elif name == "content_versions":
		header_title.text = "Content Versions"
	elif name == "logs":
		header_title.text = "Log Viewer"
	else:
		header_title.text = "Account"

func _current_screen() -> String:
	return current_screen_name

func _apply_auth_mode() -> void:
	auth_display_name_input.visible = register_mode
	auth_otp_input.visible = not register_mode
	auth_submit_button.text = "Register" if register_mode else "Login"
	auth_toggle_button.text = "Back" if register_mode else "Create Account"
	auth_status_label.text = " "
	if register_mode:
		auth_email_input.clear()
		auth_password_input.clear()
		auth_display_name_input.clear()
		auth_otp_input.clear()
	else:
		auth_display_name_input.clear()
		auth_password_input.clear()
		auth_otp_input.clear()
		if auth_email_input.text.strip_edges().is_empty():
			_load_last_email_pref()

func _set_auth_status(message: String) -> void:
	auth_status_label.text = message

func _set_footer_status(message: String) -> void:
	footer_status.text = message

func _on_auth_toggle_mode() -> void:
	register_mode = not register_mode
	_apply_auth_mode()

func _on_auth_submit() -> void:
	var email = auth_email_input.text.strip_edges()
	var password = auth_password_input.text
	if email.is_empty() or password.is_empty():
		_set_auth_status("Email and password are required.")
		return

	var response: Dictionary
	if register_mode:
		var display_name = auth_display_name_input.text.strip_edges()
		if display_name.length() < 2:
			_set_auth_status("Display name must be at least 2 characters.")
			return
		_set_auth_status("Creating account...")
		response = await _api_request(
			HTTPClient.METHOD_POST,
			"/auth/register",
			{
				"email": email,
				"password": password,
				"display_name": display_name,
			},
			false
		)
	else:
		_set_auth_status("Logging in...")
		response = await _api_request(
			HTTPClient.METHOD_POST,
			"/auth/login",
			{
				"email": email,
				"password": password,
				"otp_code": auth_otp_input.text.strip_edges(),
				"client_version": client_version,
				"client_content_version_key": client_content_version_key,
			},
			false
		)

	if not response.get("ok", false):
		_append_log("Auth failed for " + email + " status=" + str(response.get("status", 0)))
		_set_auth_status(_friendly_error(response))
		return

	var payload: Dictionary = response.get("json", {})
	_append_log("Auth success for " + email)
	_apply_session(payload)
	_set_auth_status(" ")
	register_mode = false
	_apply_auth_mode()
	await _load_characters()
	_show_screen("account")
	character_tabs.current_tab = 0

func _apply_session(payload: Dictionary) -> void:
	access_token = str(payload.get("access_token", ""))
	refresh_token = str(payload.get("refresh_token", ""))
	session_email = str(payload.get("email", ""))
	session_display_name = str(payload.get("display_name", session_email))
	session_is_admin = bool(payload.get("is_admin", false))
	auth_email_input.text = session_email
	_save_last_email_pref(session_email)
	_set_footer_status("Welcome " + session_display_name)

func _logout_session_local() -> void:
	access_token = ""
	refresh_token = ""
	session_email = ""
	session_display_name = ""
	session_is_admin = false
	characters.clear()
	selected_character_index = -1
	active_character_id = -1
	active_level_id = -1
	active_level_name = "Default"
	active_world_ready = false
	character_row_level_overrides.clear()
	_clear_children(character_rows_container)
	character_details_label.text = "Choose a character from the list."
	character_preview_texture.texture = null
	auth_password_input.clear()
	auth_otp_input.clear()
	settings_mfa_last_secret = ""
	settings_mfa_last_uri = ""
	settings_mfa_last_qr_svg = ""

func _logout_account() -> void:
	await _persist_active_character_location()
	if access_token != "":
		await _api_request(HTTPClient.METHOD_POST, "/auth/logout", {}, true)
	_logout_session_local()
	_show_screen("auth")
	_set_footer_status("Logged out.")

func _load_characters() -> void:
	if access_token == "":
		return
	account_status_label.text = "Loading characters..."
	if session_is_admin:
		await _refresh_admin_levels_cache()
	var response = await _api_request(HTTPClient.METHOD_GET, "/characters", null, true)
	if not response.get("ok", false):
		account_status_label.text = _friendly_error(response)
		return
	var payload = response.get("json", [])
	characters = payload if payload is Array else []
	if characters.is_empty():
		selected_character_index = -1
		character_details_label.text = "No characters yet. Create your first character."
		character_preview_texture.texture = null
	else:
		var selected_index = 0
		for idx in range(characters.size()):
			if bool(characters[idx].get("is_selected", false)):
				selected_index = idx
				break
		selected_character_index = selected_index
		_render_character_details(selected_index)
	_refresh_create_character_preview()
	_render_character_rows()
	account_status_label.text = " "

func _refresh_admin_levels_cache() -> void:
	admin_levels_cache.clear()
	if access_token.is_empty() or not session_is_admin:
		return
	var response = await _api_request(HTTPClient.METHOD_GET, "/levels", null, true)
	if not response.get("ok", false):
		return
	var payload = response.get("json", [])
	admin_levels_cache = payload if payload is Array else []

func _on_character_selected(index: int) -> void:
	_set_selected_character(index)

func _render_character_details(index: int) -> void:
	if index < 0 or index >= characters.size():
		character_details_label.text = "Choose a character from the list."
		character_preview_texture.texture = null
		return
	var row: Dictionary = characters[index]
	var location_text = _character_location_text(row)
	character_details_label.text = (
		"Name: %s\nLevel: %s\nXP: %s (next %s)\nAppearance: %s\nRace: %s\nBackground: %s\nAffiliation: %s\nLocation: %s"
		% [
			str(row.get("name", "")),
			str(row.get("level", 1)),
			str(row.get("experience", 0)),
			str(row.get("experience_to_next_level", 100)),
			str(row.get("appearance_key", "human_male")),
			str(row.get("race", "Human")),
			str(row.get("background", "Drifter")),
			str(row.get("affiliation", "Unaffiliated")),
			location_text,
		]
	)
	_refresh_selected_character_preview()

func _on_create_character_pressed() -> void:
	if access_token == "":
		create_status_label.text = "Please login first."
		return
	var name = create_name_input.text.strip_edges()
	if name.length() < 2:
		create_status_label.text = "Character name must be at least 2 characters."
		return
	create_status_label.text = "Creating character..."
	var appearance_key = "human_male" if create_sex_option.selected == 0 else "human_female"
	var stats_payload: Dictionary = {}
	for key in create_stat_keys:
		stats_payload[key] = int(create_stat_values.get(key, 0))
	var skills_payload: Dictionary = {}
	for key in create_skill_keys:
		skills_payload[key] = int(create_skill_values.get(key, 0))
	var payload = {
		"name": name,
		"appearance_key": appearance_key,
		"race": create_race_option.get_item_text(create_race_option.selected),
		"background": create_background_option.get_item_text(create_background_option.selected),
		"affiliation": create_affiliation_option.get_item_text(create_affiliation_option.selected),
		"stat_points_total": create_point_budget,
		"stats": stats_payload,
		"skills": skills_payload,
		"equipment": {},
	}
	var response = await _api_request(HTTPClient.METHOD_POST, "/characters", payload, true)
	if not response.get("ok", false):
		create_status_label.text = _friendly_error(response)
		return
	create_name_input.clear()
	for key in create_stat_keys:
		create_stat_values[key] = 0
	for key in create_skill_keys:
		create_skill_values[key] = 0
	for key in create_skill_buttons.keys():
		var button = create_skill_buttons.get(key)
		if button is Button:
			button.button_pressed = false
	_populate_character_creation_tables(content_domains.get("character_options", {}))
	create_status_label.text = "Character created."
	await _load_characters()
	character_tabs.current_tab = 0

func _on_character_delete_pressed() -> void:
	if selected_character_index < 0 or selected_character_index >= characters.size():
		account_status_label.text = "Select a character first."
		return
	var row: Dictionary = characters[selected_character_index]
	account_status_label.text = "Deleting " + str(row.get("name", "character")) + "..."
	var response = await _api_request(
		HTTPClient.METHOD_DELETE,
		"/characters/%s" % str(row.get("id")),
		null,
		true
	)
	if not response.get("ok", false):
		account_status_label.text = _friendly_error(response)
		return
	await _load_characters()
	account_status_label.text = "Character deleted."

func _on_character_play_pressed() -> void:
	if selected_character_index < 0 or selected_character_index >= characters.size():
		account_status_label.text = "Select a character first."
		return
	var row: Dictionary = characters[selected_character_index]
	var character_id = int(row.get("id", -1))
	if character_id <= 0:
		account_status_label.text = "Invalid character selection."
		return
	account_status_label.text = "Starting session..."
	active_character_id = character_id
	var select_response = await _api_request(
		HTTPClient.METHOD_POST,
		"/characters/%s/select" % str(character_id),
		{},
		true
	)
	if not select_response.get("ok", false):
		account_status_label.text = _friendly_error(select_response)
		return

	var level_data: Dictionary = {}
	var override_level_id = int(character_row_level_overrides.get(character_id, -1))
	var override_applied = session_is_admin and override_level_id > 0
	if override_applied:
		var assign_response = await _api_request(
			HTTPClient.METHOD_POST,
			"/characters/%s/level" % str(character_id),
			{"level_id": override_level_id},
			true
		)
		if not assign_response.get("ok", false):
			account_status_label.text = _friendly_error(assign_response)
			return
		row["level_id"] = override_level_id
		row["location_x"] = null
		row["location_y"] = null

	var level_id = row.get("level_id", null)
	if level_id != null:
		var level_response = await _api_request(HTTPClient.METHOD_GET, "/levels/%s" % str(level_id), null, true)
		if level_response.get("ok", false):
			level_data = level_response.get("json", {})
	if level_data.is_empty():
		var first_level = await _api_request(HTTPClient.METHOD_GET, "/levels/first", null, true)
		if first_level.get("ok", false):
			level_data = first_level.get("json", {})
	if level_data.is_empty():
		level_data = {
			"id": -1,
			"name": "Default",
			"descriptive_name": "Default",
			"width": 80,
			"height": 48,
			"spawn_x": 3,
			"spawn_y": 3,
		}
		account_status_label.text = "Loaded fallback world."

	active_level_id = int(level_data.get("id", -1))
	active_level_name = str(level_data.get("descriptive_name", level_data.get("name", "Default")))
	var width_tiles = int(level_data.get("width", 64))
	var height_tiles = int(level_data.get("height", 48))
	var spawn_tile_x = int(level_data.get("spawn_x", 3))
	var spawn_tile_y = int(level_data.get("spawn_y", 3))
	var spawn_world = Vector2(
		float(spawn_tile_x) * 32.0 + 16.0,
		float(spawn_tile_y) * 32.0 + 16.0
	)
	if not override_applied and row.get("location_x", null) != null and row.get("location_y", null) != null:
		spawn_world = Vector2(float(row.get("location_x")), float(row.get("location_y")))

	world_canvas.call("configure_world", active_level_name, width_tiles, height_tiles, spawn_world)
	world_status_label.text = "WASD to move. Level: %s" % active_level_name
	_append_log("Character " + str(active_character_id) + " entered world level=" + active_level_name)
	active_world_ready = true
	account_status_label.text = " "
	_show_screen("world")

func _on_world_position_changed(position: Vector2) -> void:
	world_status_label.text = "WASD to move. Level: %s (%d, %d)" % [active_level_name, int(position.x), int(position.y)]

func _persist_active_character_location() -> void:
	if not active_world_ready:
		return
	if selected_character_index < 0 or selected_character_index >= characters.size():
		return
	if access_token == "":
		return
	var row: Dictionary = characters[selected_character_index]
	if active_character_id > 0 and int(row.get("id", -1)) != active_character_id:
		return
	var world_position: Vector2 = world_canvas.call("get_world_position")
	await _api_request(
		HTTPClient.METHOD_POST,
		"/characters/%s/location" % str(row.get("id")),
		{
			"level_id": active_level_id if active_level_id > 0 else null,
			"location_x": int(round(world_position.x)),
			"location_y": int(round(world_position.y)),
		},
		true
	)
	_append_log("Persisted character location id=%s level=%s x=%s y=%s" % [
		str(row.get("id", -1)),
		str(active_level_id),
		str(int(round(world_position.x))),
		str(int(round(world_position.y))),
	])
	active_world_ready = false

func _on_update_and_restart_pressed() -> void:
	await _refresh_release_summary()
	var update_needed = bool(release_summary.get("force_update", false)) or bool(release_summary.get("update_available", false)) or bool(release_summary.get("content_update_available", false))
	if not update_needed:
		_set_footer_status("Game is up to date.")
		_append_log("Update check result: up to date.")
		return
	var feed_url = str(release_summary.get("update_feed_url", "")).strip_edges()
	if feed_url.is_empty():
		_set_footer_status("Update feed URL is missing.")
		return
	var helper_path = _resolve_update_helper_path()
	if helper_path.is_empty():
		_set_footer_status("Update helper not found.")
		_append_log("Update helper missing at install root.")
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
	var process_id = OS.create_process(helper_path, args)
	if process_id <= 0:
		_set_footer_status("Failed to start update helper.")
		_append_log("Update helper failed to launch.")
		return
	_set_footer_status("Update helper started. Restarting...")
	_append_log("Update helper launched successfully. pid=" + str(process_id))
	await _persist_active_character_location()
	get_tree().quit()

func _reload_log_view() -> void:
	var file_name = log_file_option.get_item_text(log_file_option.selected)
	var path = _path_join(logs_root_path, file_name)
	if file_name == "godot.log":
		var user_log = _path_join(ProjectSettings.globalize_path("user://"), "logs/godot.log")
		if FileAccess.file_exists(user_log):
			path = user_log
		else:
			path = _path_join(logs_root_path, "godot.log")
	if not FileAccess.file_exists(path):
		log_text_view.text = ""
		log_status_label.text = "Log not found: " + file_name
		return
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		log_status_label.text = "Unable to open: " + file_name
		return
	log_text_view.text = file.get_as_text()
	log_status_label.text = "Showing " + file_name
	file.close()

func _open_settings_screen() -> void:
	_load_settings_preferences()
	await _refresh_settings_mfa_status()
	_show_screen("settings")

func _load_settings_preferences() -> void:
	suppress_settings_events = true
	var prefs = _read_preferences()
	var screen_mode = str(prefs.get("screen_mode", "borderless_fullscreen")).strip_edges().to_lower()
	if screen_mode == "windowed":
		settings_screen_mode.selected = 1
	else:
		settings_screen_mode.selected = 0
	settings_audio_mute.button_pressed = str(prefs.get("audio_muted", "false")).strip_edges().to_lower() == "true"
	settings_audio_mute.text = "Muted: ON" if settings_audio_mute.button_pressed else "Muted: OFF"
	settings_audio_volume.value = float(str(prefs.get("audio_volume", "80")).to_int())
	settings_dirty = false
	suppress_settings_events = false
	settings_status_label.text = " "

func _mark_settings_dirty() -> void:
	if suppress_settings_events:
		return
	settings_dirty = true

func _on_settings_save_pressed() -> void:
	if not settings_dirty:
		settings_status_label.text = "No changes to save."
		return
	var confirmed = await _show_confirm_dialog("Save Settings", "Save your settings changes?")
	if not confirmed:
		settings_status_label.text = "Save canceled."
		return
	var prefs = _read_preferences()
	prefs["screen_mode"] = "windowed" if settings_screen_mode.selected == 1 else "borderless_fullscreen"
	prefs["audio_muted"] = "true" if settings_audio_mute.button_pressed else "false"
	prefs["audio_volume"] = str(int(round(settings_audio_volume.value)))
	_write_preferences(prefs)
	settings_dirty = false
	_apply_default_window_mode()
	if settings_screen_mode.selected == 1:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, false)
	settings_status_label.text = "Settings saved."

func _on_settings_cancel_pressed() -> void:
	if settings_dirty:
		var confirmed = await _show_confirm_dialog("Discard Changes", "You have unsaved changes. Exit settings?")
		if not confirmed:
			settings_status_label.text = "Cancel aborted."
			return
	_load_settings_preferences()
	_show_screen("account")

func _show_confirm_dialog(title: String, text_value: String) -> bool:
	var dialog = ConfirmationDialog.new()
	dialog.title = title
	dialog.dialog_text = text_value
	dialog.theme = ui_theme
	add_child(dialog)
	var done = false
	var accepted = false
	dialog.confirmed.connect(func() -> void:
		accepted = true
		done = true
	)
	dialog.canceled.connect(func() -> void:
		accepted = false
		done = true
	)
	dialog.close_requested.connect(func() -> void:
		accepted = false
		done = true
	)
	dialog.popup_centered(Vector2i(520, 180))
	while not done:
		await get_tree().process_frame
	dialog.queue_free()
	return accepted

func _refresh_settings_mfa_status() -> void:
	if access_token.is_empty():
		return
	settings_mfa_status_label.text = "MFA: Loading..."
	var response = await _api_request(HTTPClient.METHOD_GET, "/auth/mfa/status", null, true)
	if not response.get("ok", false):
		settings_mfa_status_label.text = "MFA: unavailable"
		settings_status_label.text = _friendly_error(response)
		return
	var body = response.get("json", {})
	var enabled = bool(body.get("enabled", false))
	var configured = bool(body.get("configured", false))
	settings_mfa_status_label.text = "MFA: " + ("Enabled" if enabled else ("Configured (off)" if configured else "Not configured"))
	suppress_settings_events = true
	settings_mfa_toggle.button_pressed = enabled
	settings_mfa_toggle.text = "MFA: ON" if enabled else "MFA: OFF"
	suppress_settings_events = false

func _generate_settings_mfa_secret() -> void:
	if access_token.is_empty():
		return
	settings_status_label.text = "Generating MFA secret..."
	var response = await _api_request(HTTPClient.METHOD_POST, "/auth/mfa/setup", {}, true)
	if not response.get("ok", false):
		settings_status_label.text = _friendly_error(response)
		return
	var body = response.get("json", {})
	var secret = str(body.get("secret", ""))
	var uri = str(body.get("provisioning_uri", ""))
	var qr_svg = str(body.get("qr_svg", ""))
	settings_mfa_last_secret = secret
	settings_mfa_last_uri = uri
	settings_mfa_last_qr_svg = qr_svg
	settings_mfa_secret_output.text = "Secret:\n%s\n\nProvisioning URI:\n%s" % [secret, uri]
	settings_status_label.text = "MFA secret generated."
	_show_settings_mfa_qr()
	await _refresh_settings_mfa_status()

func _show_settings_mfa_qr() -> void:
	if settings_mfa_last_uri.strip_edges().is_empty():
		settings_status_label.text = "Generate MFA secret first."
		return
	var dialog = AcceptDialog.new()
	dialog.title = "MFA Setup"
	dialog.theme = ui_theme
	add_child(dialog)

	var panel = PanelContainer.new()
	panel.custom_minimum_size = Vector2(700, 560)
	dialog.add_child(panel)

	var root = VBoxContainer.new()
	root.add_theme_constant_override("separation", 10)
	panel.add_child(root)

	var title = _label("Scan this QR code with your authenticator app")
	title.add_theme_font_size_override("font_size", 18)
	root.add_child(title)

	var qr_box = PanelContainer.new()
	qr_box.custom_minimum_size = Vector2(300, 300)
	root.add_child(qr_box)
	var qr_texture = TextureRect.new()
	qr_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	qr_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	qr_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	qr_box.add_child(qr_texture)

	var image = Image.new()
	var svg_error = ERR_INVALID_DATA
	if not settings_mfa_last_qr_svg.strip_edges().is_empty():
		svg_error = image.load_svg_from_string(settings_mfa_last_qr_svg)
	if svg_error == OK:
		var texture = ImageTexture.create_from_image(image)
		qr_texture.texture = texture
	else:
		var fallback = _label("QR unavailable")
		fallback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		fallback.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		fallback.set_anchors_preset(Control.PRESET_FULL_RECT)
		qr_box.add_child(fallback)

	var secret_label = _label("Secret: " + settings_mfa_last_secret)
	secret_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(secret_label)
	var uri_view = TextEdit.new()
	uri_view.editable = false
	uri_view.custom_minimum_size = Vector2(640, 90)
	uri_view.text = settings_mfa_last_uri
	root.add_child(uri_view)

	var actions = HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	root.add_child(actions)
	var copy_secret = _button("Copy Secret")
	copy_secret.pressed.connect(func() -> void:
		DisplayServer.clipboard_set(settings_mfa_last_secret)
	)
	actions.add_child(copy_secret)
	var copy_uri = _button("Copy URI")
	copy_uri.pressed.connect(func() -> void:
		DisplayServer.clipboard_set(settings_mfa_last_uri)
	)
	actions.add_child(copy_uri)
	var close_btn = _button("Close")
	close_btn.pressed.connect(func() -> void:
		dialog.queue_free()
	)
	actions.add_child(close_btn)

	dialog.confirmed.connect(func() -> void:
		dialog.queue_free()
	)
	dialog.canceled.connect(func() -> void:
		dialog.queue_free()
	)
	dialog.close_requested.connect(func() -> void:
		dialog.queue_free()
	)
	dialog.popup_centered(Vector2i(760, 620))

func _apply_settings_mfa_toggle() -> void:
	if access_token.is_empty():
		return
	settings_mfa_toggle.text = "MFA: ON" if settings_mfa_toggle.button_pressed else "MFA: OFF"
	var otp = settings_mfa_otp_input.text.strip_edges()
	if otp.length() < 6:
		settings_status_label.text = "Enter a valid MFA code."
		return
	var endpoint = "/auth/mfa/enable" if settings_mfa_toggle.button_pressed else "/auth/mfa/disable"
	settings_status_label.text = "Updating MFA..."
	var response = await _api_request(
		HTTPClient.METHOD_POST,
		endpoint,
		{"otp_code": otp},
		true
	)
	if not response.get("ok", false):
		settings_status_label.text = _friendly_error(response)
		return
	settings_mfa_otp_input.clear()
	settings_status_label.text = "MFA updated."
	await _refresh_settings_mfa_status()

func _refresh_level_editor_levels() -> void:
	if access_token.is_empty() or not session_is_admin:
		return
	level_editor_status.text = "Loading levels..."
	var response = await _api_request(HTTPClient.METHOD_GET, "/levels", null, true)
	if not response.get("ok", false):
		level_editor_status.text = _friendly_error(response)
		return
	var rows = response.get("json", [])
	level_editor_levels_cache = rows if rows is Array else []
	level_editor_level_option.clear()
	for row in level_editor_levels_cache:
		level_editor_level_option.add_item("%s (#%s)" % [str(row.get("descriptive_name", row.get("name", ""))), str(row.get("id", ""))])
	if level_editor_level_option.get_item_count() == 0:
		level_editor_level_option.add_item("No levels")
	level_editor_status.text = " "
	_refresh_level_editor_pending_view()

func _load_selected_level_into_editor() -> void:
	if level_editor_level_option.get_item_count() == 0 or level_editor_levels_cache.is_empty():
		return
	var index = level_editor_level_option.selected
	if index < 0 or index >= level_editor_levels_cache.size():
		return
	var summary = level_editor_levels_cache[index]
	var level_id = int(summary.get("id", -1))
	level_editor_status.text = "Loading level #%s..." % str(level_id)
	var response = await _api_request(HTTPClient.METHOD_GET, "/levels/%s" % str(level_id), null, true)
	if not response.get("ok", false):
		level_editor_status.text = _friendly_error(response)
		return
	var level = response.get("json", {})
	level_editor_name_input.text = str(level.get("name", ""))
	level_editor_descriptive_input.text = str(level.get("descriptive_name", ""))
	level_editor_order_input.text = str(level.get("order_index", 1))
	level_editor_width_input.text = str(level.get("width", 80))
	level_editor_height_input.text = str(level.get("height", 48))
	level_editor_spawn_x_input.text = str(level.get("spawn_x", 3))
	level_editor_spawn_y_input.text = str(level.get("spawn_y", 3))
	level_editor_layers_input.text = JSON.stringify(level.get("layers", {}), "\t")
	level_editor_transitions_input.text = JSON.stringify(level.get("transitions", []), "\t")
	level_editor_status.text = "Level loaded."

func _save_level_editor_local_draft() -> void:
	var level_name = level_editor_name_input.text.strip_edges()
	if level_name.is_empty():
		level_editor_status.text = "Level name is required."
		return
	var layers_variant = JSON.parse_string(level_editor_layers_input.text.strip_edges())
	if not (layers_variant is Dictionary):
		level_editor_status.text = "Layers JSON must be an object."
		return
	var transitions_variant = JSON.parse_string(level_editor_transitions_input.text.strip_edges())
	if not (transitions_variant is Array):
		level_editor_status.text = "Transitions JSON must be an array."
		return
	var payload = {
		"name": level_name,
		"descriptive_name": level_editor_descriptive_input.text.strip_edges(),
		"order_index": int(level_editor_order_input.text.to_int()),
		"schema_version": 2,
		"width": max(8, int(level_editor_width_input.text.to_int())),
		"height": max(8, int(level_editor_height_input.text.to_int())),
		"spawn_x": max(0, int(level_editor_spawn_x_input.text.to_int())),
		"spawn_y": max(0, int(level_editor_spawn_y_input.text.to_int())),
		"layers": layers_variant,
		"transitions": transitions_variant,
	}
	var replaced = false
	for idx in range(level_editor_local_drafts.size()):
		if str(level_editor_local_drafts[idx].get("name", "")) == level_name:
			level_editor_local_drafts[idx] = payload
			replaced = true
			break
	if not replaced:
		level_editor_local_drafts.append(payload)
	_save_level_editor_drafts()
	_refresh_level_editor_pending_view()
	level_editor_status.text = "Saved local draft."

func _publish_level_editor_drafts() -> void:
	if level_editor_local_drafts.is_empty():
		level_editor_status.text = "No level drafts to publish."
		return
	level_editor_status.text = "Publishing %d level draft(s)..." % level_editor_local_drafts.size()
	for draft in level_editor_local_drafts:
		var response = await _api_request(HTTPClient.METHOD_POST, "/levels", draft, true)
		if not response.get("ok", false):
			level_editor_status.text = _friendly_error(response)
			return
	level_editor_local_drafts.clear()
	_save_level_editor_drafts()
	_refresh_level_editor_pending_view()
	await _refresh_level_editor_levels()
	level_editor_status.text = "Published level drafts."

func _refresh_level_editor_pending_view() -> void:
	level_editor_pending_list.clear()
	for draft in level_editor_local_drafts:
		level_editor_pending_list.add_item("%s | %sx%s" % [str(draft.get("name", "")), str(draft.get("width", "")), str(draft.get("height", ""))])

func _refresh_level_order_list() -> void:
	if access_token.is_empty() or not session_is_admin:
		return
	level_order_status.text = "Loading levels..."
	var response = await _api_request(HTTPClient.METHOD_GET, "/levels", null, true)
	if not response.get("ok", false):
		level_order_status.text = _friendly_error(response)
		return
	var rows = response.get("json", [])
	level_order_levels = rows if rows is Array else []
	level_order_levels.sort_custom(func(a, b) -> bool:
		return int(a.get("order_index", 0)) < int(b.get("order_index", 0))
	)
	level_order_list.clear()
	for row in level_order_levels:
		level_order_list.add_item(
			"%s | order %s | #%s" % [
				str(row.get("descriptive_name", row.get("name", ""))),
				str(row.get("order_index", 0)),
				str(row.get("id", -1)),
			]
		)
	if level_order_list.get_item_count() > 0:
		level_order_list.select(0)
	level_order_status.text = " "

func _move_level_order(direction: int) -> void:
	if level_order_levels.is_empty():
		return
	var selected = level_order_list.get_selected_items()
	if selected.is_empty():
		return
	var from_idx = int(selected[0])
	var to_idx = int(clamp(from_idx + direction, 0, level_order_levels.size() - 1))
	if to_idx == from_idx:
		return
	var row = level_order_levels[from_idx]
	level_order_levels.remove_at(from_idx)
	level_order_levels.insert(to_idx, row)
	for i in range(level_order_levels.size()):
		level_order_levels[i]["order_index"] = i + 1
	level_order_list.clear()
	for entry in level_order_levels:
		level_order_list.add_item(
			"%s | order %s | #%s" % [
				str(entry.get("descriptive_name", entry.get("name", ""))),
				str(entry.get("order_index", 0)),
				str(entry.get("id", -1)),
			]
		)
	level_order_list.select(to_idx)

func _publish_level_order() -> void:
	if level_order_levels.is_empty():
		level_order_status.text = "No levels to publish."
		return
	var payload: Array = []
	for row in level_order_levels:
		payload.append(
			{
				"id": int(row.get("id", -1)),
				"order_index": int(row.get("order_index", 0)),
			}
		)
	level_order_status.text = "Publishing level order..."
	var response = await _api_request(HTTPClient.METHOD_POST, "/levels/order", payload, true)
	if not response.get("ok", false):
		level_order_status.text = _friendly_error(response)
		return
	level_order_status.text = "Level order published."

func _refresh_asset_editor_versions() -> void:
	if access_token.is_empty() or not session_is_admin:
		return
	asset_editor_status.text = "Loading content versions..."
	var response = await _api_request(HTTPClient.METHOD_GET, "/content/versions", null, true)
	if not response.get("ok", false):
		asset_editor_status.text = _friendly_error(response)
		return
	var rows = response.get("json", [])
	asset_editor_versions_cache = rows if rows is Array else []
	asset_editor_version_option.clear()
	for row in asset_editor_versions_cache:
		asset_editor_version_option.add_item("%s [%s]" % [str(row.get("version_key", "")), str(row.get("state", ""))])
	if asset_editor_version_option.get_item_count() == 0:
		asset_editor_version_option.add_item("No versions")
	_refresh_asset_editor_pending_view()
	asset_editor_status.text = " "
	_load_asset_editor_selected_version()

func _load_asset_editor_selected_version() -> void:
	asset_editor_active_domains = {}
	asset_editor_domain_option.clear()
	if asset_editor_versions_cache.is_empty():
		asset_editor_domain_option.add_item("No domains")
		asset_editor_payload_input.text = ""
		return
	var idx = asset_editor_version_option.selected
	if idx < 0 or idx >= asset_editor_versions_cache.size():
		idx = 0
	var version = asset_editor_versions_cache[idx]
	var version_id = int(version.get("id", -1))
	if version_id <= 0:
		return
	var response = await _api_request(HTTPClient.METHOD_GET, "/content/versions/%s" % str(version_id), null, true)
	if not response.get("ok", false):
		asset_editor_status.text = _friendly_error(response)
		return
	var detail = response.get("json", {})
	asset_editor_active_domains = detail.get("domains", {})
	for key in asset_editor_active_domains.keys():
		asset_editor_domain_option.add_item(str(key))
	if asset_editor_domain_option.get_item_count() == 0:
		asset_editor_domain_option.add_item("No domains")
		asset_editor_payload_input.text = ""
	else:
		asset_editor_domain_option.selected = 0
		_load_asset_editor_selected_domain_payload()

func _load_asset_editor_selected_domain_payload() -> void:
	if asset_editor_domain_option.get_item_count() == 0:
		return
	var domain = asset_editor_domain_option.get_item_text(asset_editor_domain_option.selected)
	var payload = asset_editor_active_domains.get(domain, {})
	asset_editor_payload_input.text = JSON.stringify(payload, "\t")

func _save_asset_editor_local_draft() -> void:
	if asset_editor_versions_cache.is_empty():
		asset_editor_status.text = "No content versions available."
		return
	var idx = asset_editor_version_option.selected
	if idx < 0 or idx >= asset_editor_versions_cache.size():
		asset_editor_status.text = "Select a content version."
		return
	var domain = asset_editor_domain_option.get_item_text(asset_editor_domain_option.selected)
	if domain == "No domains":
		asset_editor_status.text = "Select a domain."
		return
	var payload = JSON.parse_string(asset_editor_payload_input.text.strip_edges())
	if not (payload is Dictionary):
		asset_editor_status.text = "Domain payload must be a JSON object."
		return
	var version = asset_editor_versions_cache[idx]
	var entry = {
		"version_id": int(version.get("id", -1)),
		"version_key": str(version.get("version_key", "")),
		"domain": domain,
		"payload": payload,
	}
	var replaced = false
	for i in range(asset_editor_local_drafts.size()):
		var row = asset_editor_local_drafts[i]
		if int(row.get("version_id", -1)) == int(entry.get("version_id", -1)) and str(row.get("domain", "")) == domain:
			asset_editor_local_drafts[i] = entry
			replaced = true
			break
	if not replaced:
		asset_editor_local_drafts.append(entry)
	_save_asset_editor_drafts()
	_refresh_asset_editor_pending_view()
	asset_editor_status.text = "Saved local change."

func _publish_asset_editor_drafts() -> void:
	if asset_editor_local_drafts.is_empty():
		asset_editor_status.text = "No local changes queued."
		return
	asset_editor_status.text = "Publishing %d change(s)..." % asset_editor_local_drafts.size()
	for entry in asset_editor_local_drafts:
		var response = await _api_request(
			HTTPClient.METHOD_PUT,
			"/content/versions/%s/bundles/%s" % [str(entry.get("version_id", -1)), str(entry.get("domain", ""))],
			{"payload": entry.get("payload", {})},
			true
		)
		if not response.get("ok", false):
			asset_editor_status.text = _friendly_error(response)
			return
	asset_editor_local_drafts.clear()
	_save_asset_editor_drafts()
	_refresh_asset_editor_pending_view()
	await _refresh_asset_editor_versions()
	asset_editor_status.text = "Published changes."

func _refresh_asset_editor_pending_view() -> void:
	asset_editor_pending_list.clear()
	for entry in asset_editor_local_drafts:
		asset_editor_pending_list.add_item("%s | %s" % [str(entry.get("version_key", "")), str(entry.get("domain", ""))])

func _refresh_content_versions() -> void:
	if access_token.is_empty() or not session_is_admin:
		return
	versions_status.text = "Loading versions..."
	var response = await _api_request(HTTPClient.METHOD_GET, "/content/versions", null, true)
	if not response.get("ok", false):
		versions_status.text = _friendly_error(response)
		return
	var rows = response.get("json", [])
	asset_editor_versions_cache = rows if rows is Array else []
	versions_list.clear()
	versions_compare_a.clear()
	versions_compare_b.clear()
	for row in asset_editor_versions_cache:
		var label = "%s [%s]" % [str(row.get("version_key", "")), str(row.get("state", ""))]
		versions_list.add_item(label)
		versions_compare_a.add_item(label)
		versions_compare_b.add_item(label)
	if versions_list.get_item_count() > 0:
		versions_list.select(0)
		await _on_versions_item_selected(0)
	versions_status.text = " "

func _on_versions_item_selected(index: int) -> void:
	if index < 0 or index >= asset_editor_versions_cache.size():
		return
	var row = asset_editor_versions_cache[index]
	var response = await _api_request(HTTPClient.METHOD_GET, "/content/versions/%s" % str(row.get("id", -1)), null, true)
	if not response.get("ok", false):
		versions_details.text = _friendly_error(response)
		return
	var detail = response.get("json", {})
	versions_details.text = JSON.stringify(detail, "\t")

func _create_content_draft() -> void:
	var response = await _api_request(HTTPClient.METHOD_POST, "/content/versions", {"note": "Godot draft"}, true)
	if not response.get("ok", false):
		versions_status.text = _friendly_error(response)
		return
	versions_status.text = "Draft created."
	await _refresh_content_versions()

func _validate_selected_content_version() -> void:
	var version_id = _selected_content_version_id()
	if version_id <= 0:
		versions_status.text = "Select a content version first."
		return
	var response = await _api_request(HTTPClient.METHOD_POST, "/content/versions/%s/validate" % str(version_id), {}, true)
	if not response.get("ok", false):
		versions_status.text = _friendly_error(response)
		return
	versions_status.text = "Validation complete."
	await _refresh_content_versions()

func _activate_selected_content_version() -> void:
	var version_id = _selected_content_version_id()
	if version_id <= 0:
		versions_status.text = "Select a content version first."
		return
	var confirmed = await _show_confirm_dialog("Activate Version", "Activate selected content version?")
	if not confirmed:
		return
	var response = await _api_request(HTTPClient.METHOD_POST, "/content/versions/%s/activate" % str(version_id), {}, true)
	if not response.get("ok", false):
		versions_status.text = _friendly_error(response)
		return
	versions_status.text = "Version activated."
	await _refresh_content_versions()
	await _refresh_release_summary()

func _rollback_content_version() -> void:
	var confirmed = await _show_confirm_dialog("Rollback Content", "Rollback to previous content version?")
	if not confirmed:
		return
	var response = await _api_request(HTTPClient.METHOD_POST, "/content/versions/rollback/previous", {}, true)
	if not response.get("ok", false):
		versions_status.text = _friendly_error(response)
		return
	versions_status.text = "Rollback completed."
	await _refresh_content_versions()
	await _refresh_release_summary()

func _compare_content_versions() -> void:
	if asset_editor_versions_cache.is_empty():
		versions_compare_output.text = "No versions available."
		return
	var idx_a = versions_compare_a.selected
	var idx_b = versions_compare_b.selected
	if idx_a < 0 or idx_b < 0 or idx_a >= asset_editor_versions_cache.size() or idx_b >= asset_editor_versions_cache.size():
		versions_compare_output.text = "Select two versions."
		return
	var id_a = int(asset_editor_versions_cache[idx_a].get("id", -1))
	var id_b = int(asset_editor_versions_cache[idx_b].get("id", -1))
	var a_resp = await _api_request(HTTPClient.METHOD_GET, "/content/versions/%s" % str(id_a), null, true)
	var b_resp = await _api_request(HTTPClient.METHOD_GET, "/content/versions/%s" % str(id_b), null, true)
	if not a_resp.get("ok", false) or not b_resp.get("ok", false):
		versions_compare_output.text = "Failed to load compare versions."
		return
	var a_domains = a_resp.get("json", {}).get("domains", {})
	var b_domains = b_resp.get("json", {}).get("domains", {})
	var lines: Array = []
	for key in a_domains.keys():
		if not b_domains.has(key):
			lines.append("- Domain removed in B: " + str(key))
			continue
		var a_text = JSON.stringify(a_domains.get(key, {}))
		var b_text = JSON.stringify(b_domains.get(key, {}))
		if a_text != b_text:
			lines.append("- Domain changed: " + str(key))
	for key in b_domains.keys():
		if not a_domains.has(key):
			lines.append("- Domain added in B: " + str(key))
	if lines.is_empty():
		lines.append("No domain-level differences detected.")
	versions_compare_output.text = "\n".join(lines)

func _selected_content_version_id() -> int:
	var idx = versions_list.get_selected_items()
	if idx.is_empty():
		return -1
	var row_index = int(idx[0])
	if row_index < 0 or row_index >= asset_editor_versions_cache.size():
		return -1
	return int(asset_editor_versions_cache[row_index].get("id", -1))

func _save_level_editor_drafts() -> void:
	_write_json_file(level_draft_path, {"drafts": level_editor_local_drafts})

func _load_level_editor_drafts() -> void:
	var payload = _read_json_file(level_draft_path)
	if payload is Dictionary:
		var rows = payload.get("drafts", [])
		level_editor_local_drafts = rows if rows is Array else []
	_refresh_level_editor_pending_view()

func _save_asset_editor_drafts() -> void:
	_write_json_file(asset_draft_path, {"drafts": asset_editor_local_drafts})

func _load_asset_editor_drafts() -> void:
	var payload = _read_json_file(asset_draft_path)
	if payload is Dictionary:
		var rows = payload.get("drafts", [])
		asset_editor_local_drafts = rows if rows is Array else []
	_refresh_asset_editor_pending_view()

func _refresh_release_summary() -> void:
	var response = await _api_request(HTTPClient.METHOD_GET, "/release/summary", null, false)
	if response.get("ok", false):
		release_summary = response.get("json", {})
		var notes = str(release_summary.get("latest_user_facing_notes", "")).strip_edges()
		if notes.is_empty():
			notes = str(release_summary.get("latest_build_release_notes", "")).strip_edges()
		if notes.is_empty():
			notes = "No release notes available."
		auth_release_notes.text = notes
	else:
		release_summary = {}
		auth_release_notes.text = "Unable to load release notes."

func _refresh_content_bootstrap() -> void:
	var response = await _api_request(HTTPClient.METHOD_GET, "/content/bootstrap", null, false)
	if not response.get("ok", false):
		return
	var body: Dictionary = response.get("json", {})
	client_content_contract = str(body.get("content_contract_signature", "")).strip_edges()
	client_content_version_key = str(body.get("content_version_key", DEFAULT_CONTENT_VERSION))
	content_domains = body.get("domains", {})
	_populate_character_options_from_content()

func _populate_character_options_from_content() -> void:
	var options: Dictionary = content_domains.get("character_options", {})
	if create_race_option == null:
		return
	_fill_option(create_race_option, _content_labels(options.get("race", options.get("races", [])), ["Human"]))
	_fill_option(create_background_option, _content_labels(options.get("background", options.get("backgrounds", [])), ["Drifter"]))
	_fill_option(create_affiliation_option, _content_labels(options.get("affiliation", options.get("affiliations", [])), ["Unaffiliated"]))
	_populate_character_creation_tables(options)

func _content_labels(source: Variant, fallback: Array) -> Array:
	if source is Array and not source.is_empty():
		var labels: Array = []
		for entry in source:
			if entry is Dictionary:
				var label = str(entry.get("label", entry.get("value", ""))).strip_edges()
				if not label.is_empty():
					labels.append(label)
		if not labels.is_empty():
			return labels
	return fallback

func _fill_option(option: OptionButton, values: Array) -> void:
	option.clear()
	for value in values:
		option.add_item(str(value))
	option.selected = 0 if option.get_item_count() > 0 else -1

func _api_request(method: int, path: String, payload: Variant, requires_auth: bool) -> Dictionary:
	var request = HTTPRequest.new()
	add_child(request)
	request.timeout = 20.0
	var headers = PackedStringArray()
	headers.append("Content-Type: application/json")
	headers.append("X-Client-Version: %s" % client_version)
	headers.append("X-Client-Content-Version: %s" % client_content_version_key)
	if not client_content_contract.is_empty():
		headers.append("X-Client-Content-Contract: %s" % client_content_contract)
	if requires_auth and not access_token.is_empty():
		headers.append("Authorization: Bearer %s" % access_token)
	var body_text = ""
	if payload != null and method != HTTPClient.METHOD_GET and method != HTTPClient.METHOD_DELETE:
		body_text = JSON.stringify(payload)
	var url = api_base_url.trim_suffix("/") + path
	var error = request.request(url, headers, method, body_text)
	if error != OK:
		request.queue_free()
		return {
			"ok": false,
			"status": 0,
			"message": "Request start failed: %s" % error,
		}
	var completed: Array = await request.request_completed
	request.queue_free()
	var status_code: int = completed[1]
	var raw_body: PackedByteArray = completed[3]
	var text = raw_body.get_string_from_utf8()
	var parsed = {}
	if not text.is_empty():
		var parsed_variant = JSON.parse_string(text)
		if parsed_variant is Dictionary:
			parsed = parsed_variant
		elif parsed_variant is Array:
			parsed = {"_array": parsed_variant}
	var ok = status_code >= 200 and status_code < 300
	return {
		"ok": ok,
		"status": status_code,
		"text": text,
		"json": parsed if not parsed.has("_array") else parsed["_array"],
	}

func _friendly_error(response: Dictionary) -> String:
	var code = int(response.get("status", 0))
	var payload: Variant = response.get("json", {})
	var detail: Variant = null
	if payload is Dictionary:
		detail = payload.get("detail", null)
	var message = ""
	if detail is Dictionary:
		message = str(detail.get("message", "")).strip_edges()
	elif detail is String:
		message = str(detail).strip_edges()
	if message.is_empty():
		message = str(response.get("text", "")).strip_edges()
	if message.is_empty():
		message = str(response.get("message", "")).strip_edges()
	if code == 401 and message.to_lower().contains("invalid mfa"):
		return "Invalid MFA code."
	if code == 401:
		return "This account doesn't exist."
	if code == 409 and register_mode:
		return "This account already exists."
	if code == 426:
		return "A new version is required. Click Update & Restart when ready."
	if code == 0:
		var lower = message.to_lower()
		if lower.contains("cant resolve") or lower.contains("dns"):
			return "No internet connection (DNS lookup failed)."
		if lower.contains("timeout"):
			return "Connection timed out. Servers may be unavailable."
		if lower.contains("ssl"):
			return "Secure connection failed. Please retry in a moment."
		return "Servers are currently unavailable."
	return message if not message.is_empty() else "Request failed (%s)." % str(code)

func _append_log(message: String) -> void:
	var line = "[%s] %s" % [Time.get_datetime_string_from_system(true, true), message]
	print(line)
	if logs_root_path.is_empty():
		return
	var log_path = _path_join(logs_root_path, "game.log")
	var file = FileAccess.open(log_path, FileAccess.READ_WRITE)
	if file == null:
		file = FileAccess.open(log_path, FileAccess.WRITE)
	if file == null:
		return
	file.seek_end()
	file.store_line(line)
	file.close()

func _resolve_paths() -> void:
	var payload_root = OS.get_environment("VELOPACK_APPROOT").strip_edges()
	if payload_root.is_empty():
		payload_root = OS.get_executable_path().get_base_dir()
	var cleaned_payload = payload_root.replace("\\", "/")
	var runtime_marker = "/game-client/runtime/windows"
	if cleaned_payload.contains(runtime_marker):
		install_root_path = cleaned_payload.split(runtime_marker)[0]
	elif cleaned_payload.ends_with("/game-client"):
		install_root_path = cleaned_payload.get_base_dir()
	elif cleaned_payload.get_file().to_lower() == "current":
		install_root_path = cleaned_payload.get_base_dir()
	else:
		install_root_path = cleaned_payload
	if install_root_path.is_empty():
		install_root_path = ProjectSettings.globalize_path("user://")
	logs_root_path = _path_join(install_root_path, "logs")
	prefs_path = _path_join(install_root_path, "launcher_prefs.properties")
	level_draft_path = _path_join(install_root_path, "level_editor_local_draft.json")
	asset_draft_path = _path_join(install_root_path, "asset_editor_local_draft.json")
	DirAccess.make_dir_recursive_absolute(logs_root_path)

func _apply_window_icon() -> void:
	var candidates: Array[String] = []
	candidates.append("res://assets/game_icon.png")
	candidates.append(_path_join(install_root_path, "assets/icons/game_icon.png"))
	candidates.append(_path_join(install_root_path, "game-client/assets/game_icon.png"))
	candidates.append(_path_join(OS.get_executable_path().get_base_dir(), "assets/game_icon.png"))
	for path in candidates:
		if path.is_empty():
			continue
		var image = Image.new()
		var error = image.load(path)
		if error != OK:
			continue
		if DisplayServer.has_method("set_icon"):
			DisplayServer.call("set_icon", image)
		return

func _resolve_update_helper_path() -> String:
	var helper = _path_join(install_root_path, "UpdateHelper.exe")
	if FileAccess.file_exists(helper):
		return helper
	return ""

func _load_client_version() -> void:
	var meta_path = _path_join(install_root_path, "patch_notes_meta.txt")
	if not FileAccess.file_exists(meta_path):
		return
	var file = FileAccess.open(meta_path, FileAccess.READ)
	if file == null:
		return
	while not file.eof_reached():
		var line = file.get_line().strip_edges()
		if line.begins_with("version="):
			client_version = line.trim_prefix("version=").strip_edges()
			break
	file.close()

func _path_join(a: String, b: String) -> String:
	if a.is_empty():
		return b
	if a.ends_with("/") or a.ends_with("\\"):
		return a + b
	return a + "/" + b

func _apply_default_window_mode() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)

func _load_last_email_pref() -> void:
	var prefs = _read_preferences()
	var value = str(prefs.get("last_email", "")).strip_edges()
	if not value.is_empty():
		auth_email_input.text = value

func _save_last_email_pref(email: String) -> void:
	var trimmed = email.strip_edges()
	if trimmed.is_empty():
		return
	var prefs = _read_preferences()
	prefs["last_email"] = trimmed
	_write_preferences(prefs)

func _read_preferences() -> Dictionary:
	var prefs: Dictionary = {}
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
		prefs[str(parts[0]).strip_edges()] = str(parts[1]).strip_edges()
	file.close()
	return prefs

func _write_preferences(prefs: Dictionary) -> void:
	if prefs_path.is_empty():
		return
	var file = FileAccess.open(prefs_path, FileAccess.WRITE)
	if file == null:
		return
	var keys = prefs.keys()
	keys.sort()
	for key in keys:
		file.store_line("%s=%s" % [str(key), str(prefs.get(key, ""))])
	file.close()

func _read_json_file(path: String) -> Variant:
	if path.is_empty() or not FileAccess.file_exists(path):
		return {}
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var text = file.get_as_text()
	file.close()
	if text.strip_edges().is_empty():
		return {}
	var parsed = JSON.parse_string(text)
	if parsed == null:
		return {}
	return parsed

func _write_json_file(path: String, payload: Variant) -> void:
	if path.is_empty():
		return
	var file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return
	file.store_string(JSON.stringify(payload, "\t"))
	file.close()
