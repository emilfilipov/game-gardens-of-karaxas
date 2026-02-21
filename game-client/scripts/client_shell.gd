extends Control

const WORLD_CANVAS_SCENE := preload("res://scripts/world_canvas.gd")

const DEFAULT_API_BASE_URL := "https://karaxas-backend-rss3xj2ixq-ew.a.run.app"
const DEFAULT_CLIENT_VERSION := "0.0.0"
const DEFAULT_CONTENT_VERSION := "unknown"

const MENU_UPDATE := 1
const MENU_LOG_VIEWER := 2
const MENU_LOGOUT := 3
const MENU_EXIT := 4
const MENU_BACK_TO_ACCOUNT := 5

var api_base_url := DEFAULT_API_BASE_URL
var client_version := DEFAULT_CLIENT_VERSION
var client_content_version_key := DEFAULT_CONTENT_VERSION
var client_content_contract := ""
var release_summary: Dictionary = {}
var content_domains: Dictionary = {}

var access_token := ""
var refresh_token := ""
var session_email := ""
var session_display_name := ""
var session_is_admin := false

var characters: Array = []
var selected_character_index := -1
var active_level_id: int = -1
var active_level_name := "Default"
var active_world_ready := false

var install_root_path := ""
var logs_root_path := ""
var prefs_path := ""

var register_mode := false
var current_screen_name := "auth"

var header_title: Label
var menu_button: Button
var menu_popup: PopupMenu
var footer_status: Label
var main_stack: StackContainer

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
var character_list_widget: ItemList
var character_details_label: RichTextLabel
var character_play_button: Button
var character_delete_button: Button
var character_refresh_button: Button

var create_name_input: LineEdit
var create_sex_option: OptionButton
var create_race_option: OptionButton
var create_background_option: OptionButton
var create_affiliation_option: OptionButton
var create_status_label: Label
var create_submit_button: Button

var world_container: VBoxContainer
var world_status_label: Label
var world_canvas: Control
var world_back_button: Button

var log_container: VBoxContainer
var log_file_option: OptionButton
var log_text_view: TextEdit
var log_status_label: Label
var log_back_button: Button

func _ready() -> void:
	_apply_default_window_mode()
	_resolve_paths()
	_load_client_version()
	_build_theme()
	_build_ui()
	_load_last_email_pref()
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
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.16, 0.12, 0.10, 0.97)
	style.border_width_left = 1
	style.border_width_top = 1
	style.border_width_right = 1
	style.border_width_bottom = 1
	style.border_color = Color(0.68, 0.52, 0.34, 1.0)
	add_theme_stylebox_override("panel", style)

func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS

	var root := MarginContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("margin_left", 18)
	root.add_theme_constant_override("margin_top", 14)
	root.add_theme_constant_override("margin_right", 18)
	root.add_theme_constant_override("margin_bottom", 14)
	add_child(root)

	var layout := VBoxContainer.new()
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", 10)
	root.add_child(layout)

	var header := HBoxContainer.new()
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
	menu_button.custom_minimum_size = Vector2(56, 42)
	menu_button.pressed.connect(_on_menu_button_pressed)
	header.add_child(menu_button)

	menu_popup = PopupMenu.new()
	add_child(menu_popup)
	menu_popup.id_pressed.connect(_on_menu_item_pressed)

	main_stack = StackContainer.new()
	main_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(main_stack)

	auth_container = _build_auth_screen()
	main_stack.add_child(auth_container)

	account_container = _build_account_screen()
	main_stack.add_child(account_container)

	world_container = _build_world_screen()
	main_stack.add_child(world_container)

	log_container = _build_log_screen()
	main_stack.add_child(log_container)

	footer_status = Label.new()
	footer_status.text = " "
	footer_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	footer_status.add_theme_font_size_override("font_size", 14)
	footer_status.add_theme_color_override("font_color", Color(0.94, 0.84, 0.69))
	layout.add_child(footer_status)

	_show_screen("auth")

func _build_auth_screen() -> VBoxContainer:
	var wrap := VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 10)

	var body := HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 12)
	wrap.add_child(body)

	var auth_panel := PanelContainer.new()
	auth_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	auth_panel.size_flags_stretch_ratio = 0.5
	body.add_child(auth_panel)

	var auth_inner := VBoxContainer.new()
	auth_inner.add_theme_constant_override("separation", 8)
	auth_inner.size_flags_vertical = Control.SIZE_EXPAND_FILL
	auth_panel.add_child(auth_inner)

	var auth_title := Label.new()
	auth_title.text = "Account"
	auth_title.add_theme_font_size_override("font_size", 24)
	auth_title.add_theme_color_override("font_color", Color(0.95, 0.89, 0.77))
	auth_inner.add_child(auth_title)

	auth_display_name_input = _line_edit("Display Name")
	auth_inner.add_child(auth_display_name_input)
	auth_email_input = _line_edit("Email")
	auth_inner.add_child(auth_email_input)
	auth_password_input = _line_edit("Password", true)
	auth_inner.add_child(auth_password_input)
	auth_otp_input = _line_edit("MFA Code (if enabled)")
	auth_inner.add_child(auth_otp_input)

	var auth_button_row := HBoxContainer.new()
	auth_button_row.add_theme_constant_override("separation", 8)
	auth_inner.add_child(auth_button_row)
	auth_submit_button = _button("Login")
	auth_submit_button.pressed.connect(_on_auth_submit)
	auth_button_row.add_child(auth_submit_button)
	auth_toggle_button = _button("Create Account")
	auth_toggle_button.pressed.connect(_on_auth_toggle_mode)
	auth_button_row.add_child(auth_toggle_button)
	var auth_exit_button := _button("Exit")
	auth_exit_button.pressed.connect(_handle_exit_request)
	auth_button_row.add_child(auth_exit_button)

	auth_status_label = Label.new()
	auth_status_label.text = " "
	auth_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	auth_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	auth_inner.add_child(auth_status_label)

	var update_panel := PanelContainer.new()
	update_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	update_panel.size_flags_stretch_ratio = 0.5
	body.add_child(update_panel)
	var update_inner := VBoxContainer.new()
	update_inner.size_flags_vertical = Control.SIZE_EXPAND_FILL
	update_inner.add_theme_constant_override("separation", 8)
	update_panel.add_child(update_inner)
	var update_title := Label.new()
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
	var wrap := VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)

	account_status_label = Label.new()
	account_status_label.text = " "
	account_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	wrap.add_child(account_status_label)

	character_tabs = TabContainer.new()
	character_tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(character_tabs)

	var list_tab := VBoxContainer.new()
	list_tab.name = "Character List"
	list_tab.add_theme_constant_override("separation", 8)
	character_tabs.add_child(list_tab)

	var list_split := HSplitContainer.new()
	list_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list_tab.add_child(list_split)

	character_list_widget = ItemList.new()
	character_list_widget.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	character_list_widget.size_flags_vertical = Control.SIZE_EXPAND_FILL
	character_list_widget.select_mode = ItemList.SELECT_SINGLE
	character_list_widget.item_selected.connect(_on_character_selected)
	list_split.add_child(character_list_widget)

	character_details_label = RichTextLabel.new()
	character_details_label.fit_content = false
	character_details_label.bbcode_enabled = false
	character_details_label.custom_minimum_size = Vector2(320, 260)
	character_details_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	character_details_label.add_theme_color_override("default_color", Color(0.94, 0.84, 0.69))
	list_split.add_child(character_details_label)

	var list_buttons := HBoxContainer.new()
	list_buttons.add_theme_constant_override("separation", 8)
	list_tab.add_child(list_buttons)
	character_play_button = _button("Play")
	character_play_button.pressed.connect(_on_character_play_pressed)
	list_buttons.add_child(character_play_button)
	character_delete_button = _button("Delete")
	character_delete_button.pressed.connect(_on_character_delete_pressed)
	list_buttons.add_child(character_delete_button)
	character_refresh_button = _button("Refresh")
	character_refresh_button.pressed.connect(_load_characters)
	list_buttons.add_child(character_refresh_button)

	var create_tab := VBoxContainer.new()
	create_tab.name = "Create Character"
	create_tab.add_theme_constant_override("separation", 8)
	character_tabs.add_child(create_tab)

	create_name_input = _line_edit("Character Name")
	create_tab.add_child(create_name_input)
	create_sex_option = _option(["Male", "Female"])
	create_tab.add_child(create_sex_option)
	create_race_option = _option(["Human"])
	create_tab.add_child(create_race_option)
	create_background_option = _option(["Drifter"])
	create_tab.add_child(create_background_option)
	create_affiliation_option = _option(["Unaffiliated"])
	create_tab.add_child(create_affiliation_option)
	create_submit_button = _button("Create Character")
	create_submit_button.pressed.connect(_on_create_character_pressed)
	create_tab.add_child(create_submit_button)
	create_status_label = Label.new()
	create_status_label.text = " "
	create_status_label.add_theme_color_override("font_color", Color(0.94, 0.83, 0.68))
	create_tab.add_child(create_status_label)

	return wrap

func _build_world_screen() -> VBoxContainer:
	var wrap := VBoxContainer.new()
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

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	wrap.add_child(row)
	world_back_button = _button("Back to Account")
	world_back_button.pressed.connect(_on_world_back_pressed)
	row.add_child(world_back_button)
	return wrap

func _build_log_screen() -> VBoxContainer:
	var wrap := VBoxContainer.new()
	wrap.add_theme_constant_override("separation", 8)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	wrap.add_child(row)

	log_file_option = _option(["launcher.log", "game.log", "velopack.log", "godot.log"])
	row.add_child(log_file_option)
	var refresh := _button("Reload")
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
	log_text_view.readonly = true
	wrap.add_child(log_text_view)

	return wrap

func _line_edit(placeholder: String, secret := false) -> LineEdit:
	var input := LineEdit.new()
	input.placeholder_text = placeholder
	input.secret = secret
	input.custom_minimum_size = Vector2(200, 34)
	return input

func _button(text_value: String) -> Button:
	var b := Button.new()
	b.text = text_value
	b.custom_minimum_size = Vector2(140, 36)
	return b

func _option(items: Array) -> OptionButton:
	var option := OptionButton.new()
	option.custom_minimum_size = Vector2(220, 34)
	for item in items:
		option.add_item(str(item))
	return option

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
	menu_popup.add_item("Update & Restart", MENU_UPDATE)
	if access_token != "":
		if session_is_admin:
			menu_popup.add_item("Log Viewer", MENU_LOG_VIEWER)
		if _current_screen() == "world":
			menu_popup.add_item("Back to Account", MENU_BACK_TO_ACCOUNT)
		menu_popup.add_item("Logout Account", MENU_LOGOUT)
	menu_popup.add_item("Exit Game", MENU_EXIT)

func _on_menu_item_pressed(item_id: int) -> void:
	match item_id:
		MENU_UPDATE:
			_on_update_and_restart_pressed()
		MENU_LOG_VIEWER:
			if session_is_admin:
				_show_screen("logs")
				_reload_log_view()
		MENU_LOGOUT:
			await _logout_account()
		MENU_BACK_TO_ACCOUNT:
			await _on_world_back_pressed()
		MENU_EXIT:
			await _persist_active_character_location()
			get_tree().quit()

func _show_screen(name: String) -> void:
	current_screen_name = name
	var target_index := 0
	match name:
		"auth":
			target_index = 0
		"account":
			target_index = 1
		"world":
			target_index = 2
		"logs":
			target_index = 3
	for idx in range(main_stack.get_child_count()):
		main_stack.get_child(idx).visible = idx == target_index
	world_canvas.call("set_active", name == "world")
	menu_button.visible = name != "auth"
	if name == "auth":
		header_title.text = "Gardens of Karaxas"
	elif name == "world":
		header_title.text = "Game World"
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
	var email := auth_email_input.text.strip_edges()
	var password := auth_password_input.text
	if email.is_empty() or password.is_empty():
		_set_auth_status("Email and password are required.")
		return

	var response: Dictionary
	if register_mode:
		var display_name := auth_display_name_input.text.strip_edges()
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
		_set_auth_status(_friendly_error(response))
		return

	var payload: Dictionary = response.get("json", {})
	_apply_session(payload)
	_set_auth_status(" ")
	register_mode = false
	_apply_auth_mode()
	await _load_characters()
	_show_screen("account")
	if characters.is_empty():
		character_tabs.current_tab = 1
	else:
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
	active_level_id = -1
	active_level_name = "Default"
	active_world_ready = false
	character_list_widget.clear()
	character_details_label.text = "Choose a character from the list."
	auth_password_input.clear()
	auth_otp_input.clear()

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
	var response := await _api_request(HTTPClient.METHOD_GET, "/characters", null, true)
	if not response.get("ok", false):
		account_status_label.text = _friendly_error(response)
		return
	var payload = response.get("json", [])
	characters = payload if payload is Array else []
	character_list_widget.clear()
	for entry in characters:
		var row := str(entry.get("name", "Unnamed")) + " | Level " + str(entry.get("level", 1))
		character_list_widget.add_item(row)
	if characters.is_empty():
		selected_character_index = -1
		character_details_label.text = "No characters yet. Create your first character."
	else:
		selected_character_index = 0
		character_list_widget.select(0)
		_render_character_details(0)
	account_status_label.text = " "

func _on_character_selected(index: int) -> void:
	selected_character_index = index
	_render_character_details(index)

func _render_character_details(index: int) -> void:
	if index < 0 or index >= characters.size():
		character_details_label.text = "Choose a character from the list."
		return
	var row: Dictionary = characters[index]
	var location_text := "Default"
	if row.get("level_id", null) != null:
		location_text = "Level #" + str(row.get("level_id"))
	if row.get("location_x", null) != null and row.get("location_y", null) != null:
		location_text += " (" + str(row.get("location_x")) + ", " + str(row.get("location_y")) + ")"
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

func _on_create_character_pressed() -> void:
	if access_token == "":
		create_status_label.text = "Please login first."
		return
	var name := create_name_input.text.strip_edges()
	if name.length() < 2:
		create_status_label.text = "Character name must be at least 2 characters."
		return
	create_status_label.text = "Creating character..."
	var appearance_key := "human_male" if create_sex_option.selected == 0 else "human_female"
	var payload := {
		"name": name,
		"appearance_key": appearance_key,
		"race": create_race_option.get_item_text(create_race_option.selected),
		"background": create_background_option.get_item_text(create_background_option.selected),
		"affiliation": create_affiliation_option.get_item_text(create_affiliation_option.selected),
		"stat_points_total": int(content_domains.get("character_options", {}).get("point_budget", 10)),
		"stats": {},
		"skills": {},
		"equipment": {},
	}
	var response := await _api_request(HTTPClient.METHOD_POST, "/characters", payload, true)
	if not response.get("ok", false):
		create_status_label.text = _friendly_error(response)
		return
	create_name_input.clear()
	create_status_label.text = "Character created."
	await _load_characters()
	character_tabs.current_tab = 0

func _on_character_delete_pressed() -> void:
	if selected_character_index < 0 or selected_character_index >= characters.size():
		account_status_label.text = "Select a character first."
		return
	var row: Dictionary = characters[selected_character_index]
	account_status_label.text = "Deleting " + str(row.get("name", "character")) + "..."
	var response := await _api_request(
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
	account_status_label.text = "Starting session..."
	var select_response := await _api_request(
		HTTPClient.METHOD_POST,
		"/characters/%s/select" % str(row.get("id")),
		{},
		true
	)
	if not select_response.get("ok", false):
		account_status_label.text = _friendly_error(select_response)
		return

	var level_data: Dictionary = {}
	var level_id = row.get("level_id", null)
	if level_id != null:
		var level_response := await _api_request(HTTPClient.METHOD_GET, "/levels/%s" % str(level_id), null, true)
		if level_response.get("ok", false):
			level_data = level_response.get("json", {})
	if level_data.is_empty():
		var first_level := await _api_request(HTTPClient.METHOD_GET, "/levels/first", null, true)
		if first_level.get("ok", false):
			level_data = first_level.get("json", {})
	if level_data.is_empty():
		account_status_label.text = "Unable to load level data."
		return

	active_level_id = int(level_data.get("id", -1))
	active_level_name = str(level_data.get("descriptive_name", level_data.get("name", "Default")))
	var width_tiles := int(level_data.get("width", 64))
	var height_tiles := int(level_data.get("height", 48))
	var spawn_tile_x := int(level_data.get("spawn_x", 3))
	var spawn_tile_y := int(level_data.get("spawn_y", 3))
	var spawn_world := Vector2(
		float(spawn_tile_x) * 32.0 + 16.0,
		float(spawn_tile_y) * 32.0 + 16.0
	)
	if row.get("location_x", null) != null and row.get("location_y", null) != null:
		spawn_world = Vector2(float(row.get("location_x")), float(row.get("location_y")))

	world_canvas.call("configure_world", active_level_name, width_tiles, height_tiles, spawn_world)
	world_status_label.text = "WASD to move. Level: %s" % active_level_name
	active_world_ready = true
	account_status_label.text = " "
	_show_screen("world")

func _on_world_position_changed(position: Vector2) -> void:
	world_status_label.text = "WASD to move. Level: %s (%d, %d)" % [active_level_name, int(position.x), int(position.y)]

func _on_world_back_pressed() -> void:
	await _persist_active_character_location()
	_show_screen("account")

func _persist_active_character_location() -> void:
	if not active_world_ready:
		return
	if selected_character_index < 0 or selected_character_index >= characters.size():
		return
	if access_token == "":
		return
	var row: Dictionary = characters[selected_character_index]
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
	active_world_ready = false

func _on_update_and_restart_pressed() -> void:
	await _refresh_release_summary()
	var update_needed := bool(release_summary.get("force_update", false)) or bool(release_summary.get("update_available", false)) or bool(release_summary.get("content_update_available", false))
	if not update_needed:
		_set_footer_status("Game is up to date.")
		return
	var feed_url := str(release_summary.get("update_feed_url", "")).strip_edges()
	if feed_url.is_empty():
		_set_footer_status("Update feed URL is missing.")
		return
	var helper_path := _resolve_update_helper_path()
	if helper_path.is_empty():
		_set_footer_status("Update helper not found.")
		return
	var args := PackedStringArray([
		"--repo",
		feed_url,
		"--log-file",
		_path_join(logs_root_path, "velopack.log"),
		"--waitpid",
		str(OS.get_process_id()),
		"--restart-args",
		"--autoplay",
	])
	var process_id := OS.create_process(helper_path, args)
	if process_id <= 0:
		_set_footer_status("Failed to start update helper.")
		return
	_set_footer_status("Update helper started. Restarting...")
	await _persist_active_character_location()
	get_tree().quit()

func _reload_log_view() -> void:
	var file_name := log_file_option.get_item_text(log_file_option.selected)
	var path := _path_join(logs_root_path, file_name)
	if file_name == "godot.log":
		path = _path_join(logs_root_path, "godot.log")
	if not FileAccess.file_exists(path):
		log_text_view.text = ""
		log_status_label.text = "Log not found: " + file_name
		return
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		log_status_label.text = "Unable to open: " + file_name
		return
	log_text_view.text = file.get_as_text()
	log_status_label.text = "Showing " + file_name
	file.close()

func _refresh_release_summary() -> void:
	var response := await _api_request(HTTPClient.METHOD_GET, "/release/summary", null, false)
	if response.get("ok", false):
		release_summary = response.get("json", {})
		var notes := str(release_summary.get("latest_user_facing_notes", "")).strip_edges()
		if notes.is_empty():
			notes = str(release_summary.get("latest_build_release_notes", "")).strip_edges()
		if notes.is_empty():
			notes = "No release notes available."
		auth_release_notes.text = notes
	else:
		auth_release_notes.text = "Unable to load release notes."

func _refresh_content_bootstrap() -> void:
	var response := await _api_request(HTTPClient.METHOD_GET, "/content/bootstrap", null, false)
	if not response.get("ok", false):
		return
	var body: Dictionary = response.get("json", {})
	client_content_contract = str(body.get("content_contract_signature", "")).strip_edges()
	client_content_version_key = str(body.get("content_version_key", DEFAULT_CONTENT_VERSION))
	content_domains = body.get("domains", {})
	_populate_character_options_from_content()

func _populate_character_options_from_content() -> void:
	var options: Dictionary = content_domains.get("character_options", {})
	_fill_option(create_race_option, _content_labels(options.get("races", []), ["Human"]))
	_fill_option(create_background_option, _content_labels(options.get("backgrounds", []), ["Drifter"]))
	_fill_option(create_affiliation_option, _content_labels(options.get("affiliations", []), ["Unaffiliated"]))

func _content_labels(source: Variant, fallback: Array) -> Array:
	if source is Array and not source.is_empty():
		var labels: Array = []
		for entry in source:
			if entry is Dictionary:
				var label := str(entry.get("label", entry.get("value", ""))).strip_edges()
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
	var request := HTTPRequest.new()
	add_child(request)
	request.timeout = 20.0
	var headers := PackedStringArray()
	headers.append("Content-Type: application/json")
	headers.append("X-Client-Version: %s" % client_version)
	headers.append("X-Client-Content-Version: %s" % client_content_version_key)
	if not client_content_contract.is_empty():
		headers.append("X-Client-Content-Contract: %s" % client_content_contract)
	if requires_auth and not access_token.is_empty():
		headers.append("Authorization: Bearer %s" % access_token)
	var body_text := ""
	if payload != null and method != HTTPClient.METHOD_GET and method != HTTPClient.METHOD_DELETE:
		body_text = JSON.stringify(payload)
	var url := api_base_url.trim_suffix("/") + path
	var error := request.request(url, headers, method, body_text)
	if error != OK:
		request.queue_free()
		return {
			"ok": false,
			"status": 0,
			"message": "Request start failed: %s" % error,
		}
	var completed := await request.request_completed
	request.queue_free()
	var status_code: int = completed[1]
	var raw_body: PackedByteArray = completed[3]
	var text := raw_body.get_string_from_utf8()
	var parsed := {}
	if not text.is_empty():
		var parsed_variant = JSON.parse_string(text)
		if parsed_variant is Dictionary:
			parsed = parsed_variant
		elif parsed_variant is Array:
			parsed = {"_array": parsed_variant}
	var ok := status_code >= 200 and status_code < 300
	return {
		"ok": ok,
		"status": status_code,
		"text": text,
		"json": parsed if not parsed.has("_array") else parsed["_array"],
	}

func _friendly_error(response: Dictionary) -> String:
	var code := int(response.get("status", 0))
	var payload := response.get("json", {})
	var detail: Variant = null
	if payload is Dictionary:
		detail = payload.get("detail", null)
	var message := ""
	if detail is Dictionary:
		message = str(detail.get("message", "")).strip_edges()
	elif detail is String:
		message = str(detail).strip_edges()
	if message.is_empty():
		message = str(response.get("text", "")).strip_edges()
	if code == 401 and message.to_lower().contains("invalid mfa"):
		return "Invalid MFA code."
	if code == 401:
		return "This account doesn't exist."
	if code == 409 and register_mode:
		return "This account already exists."
	if code == 426:
		return "A new version is required. Click Update & Restart when ready."
	if code == 0:
		return "Servers are currently unavailable."
	return message if not message.is_empty() else "Request failed (%s)." % str(code)

func _resolve_paths() -> void:
	var payload_root := OS.get_environment("VELOPACK_APPROOT").strip_edges()
	if payload_root.is_empty():
		payload_root = OS.get_executable_path().get_base_dir()
	var cleaned_payload := payload_root.replace("\\", "/")
	var root_file_name := cleaned_payload.get_file().to_lower()
	if root_file_name == "current":
		install_root_path = cleaned_payload.get_base_dir()
	else:
		install_root_path = cleaned_payload
	logs_root_path = _path_join(install_root_path, "logs")
	prefs_path = _path_join(install_root_path, "launcher_prefs.properties")
	DirAccess.make_dir_recursive_absolute(logs_root_path)

func _resolve_update_helper_path() -> String:
	var helper := _path_join(install_root_path, "UpdateHelper.exe")
	if FileAccess.file_exists(helper):
		return helper
	return ""

func _load_client_version() -> void:
	var meta_path := _path_join(install_root_path, "patch_notes_meta.txt")
	if not FileAccess.file_exists(meta_path):
		return
	var file := FileAccess.open(meta_path, FileAccess.READ)
	if file == null:
		return
	while not file.eof_reached():
		var line := file.get_line().strip_edges()
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
	if prefs_path.is_empty() or not FileAccess.file_exists(prefs_path):
		return
	var file := FileAccess.open(prefs_path, FileAccess.READ)
	if file == null:
		return
	while not file.eof_reached():
		var line := file.get_line().strip_edges()
		if line.begins_with("last_email="):
			var value := line.trim_prefix("last_email=").strip_edges()
			if not value.is_empty():
				auth_email_input.text = value
			break
	file.close()

func _save_last_email_pref(email: String) -> void:
	if prefs_path.is_empty():
		return
	var preserved: Array[String] = []
	if FileAccess.file_exists(prefs_path):
		var existing := FileAccess.open(prefs_path, FileAccess.READ)
		if existing != null:
			while not existing.eof_reached():
				var line := existing.get_line()
				if not line.strip_edges().begins_with("last_email="):
					preserved.append(line)
			existing.close()
	var file := FileAccess.open(prefs_path, FileAccess.WRITE)
	if file == null:
		return
	file.store_line("last_email=%s" % email.strip_edges())
	for line in preserved:
		file.store_line(line)
	file.close()
