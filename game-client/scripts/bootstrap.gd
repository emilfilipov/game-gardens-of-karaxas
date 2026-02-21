extends Node2D

const BOOTSTRAP_ARG_PREFIX := "--bootstrap="

var _title_label: Label
var _status_label: Label
var _details_label: RichTextLabel

func _ready() -> void:
    _build_shell()
    var bootstrap_path := _find_bootstrap_arg(OS.get_cmdline_user_args())
    if bootstrap_path.is_empty():
        _set_status("No launcher bootstrap payload was provided.")
        _set_details("Run via launcher Play flow to receive runtime bootstrap data.")
        print("GOK game-client bootstrap: no launcher bootstrap path provided")
        return

    var file := FileAccess.open(bootstrap_path, FileAccess.READ)
    if file == null:
        _set_status("Failed to open launcher bootstrap payload.")
        _set_details("Path: " + bootstrap_path)
        push_error("GOK game-client bootstrap: failed to open bootstrap file: " + bootstrap_path)
        return

    var payload_text := file.get_as_text()
    file.close()
    print("GOK game-client bootstrap loaded from: " + bootstrap_path)
    var payload_json := JSON.parse_string(payload_text)
    if typeof(payload_json) != TYPE_DICTIONARY:
        _set_status("Launcher bootstrap payload is invalid JSON.")
        _set_details(payload_text.left(1200))
        return

    var payload: Dictionary = payload_json
    _render_payload_summary(payload, bootstrap_path)

func _build_shell() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)

    var bg := ColorRect.new()
    bg.color = Color(0.09, 0.08, 0.07, 1.0)
    bg.set_anchors_preset(Control.PRESET_FULL_RECT)
    layer.add_child(bg)

    var panel := PanelContainer.new()
    panel.set_anchors_preset(Control.PRESET_CENTER)
    panel.custom_minimum_size = Vector2(860, 520)
    panel.position = Vector2(530, 280)
    layer.add_child(panel)

    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.15, 0.11, 0.09, 0.97)
    style.border_width_left = 2
    style.border_width_top = 2
    style.border_width_right = 2
    style.border_width_bottom = 2
    style.border_color = Color(0.67, 0.51, 0.34, 1.0)
    panel.add_theme_stylebox_override("panel", style)

    var margin := MarginContainer.new()
    margin.add_theme_constant_override("margin_left", 18)
    margin.add_theme_constant_override("margin_top", 14)
    margin.add_theme_constant_override("margin_right", 18)
    margin.add_theme_constant_override("margin_bottom", 14)
    panel.add_child(margin)

    var column := VBoxContainer.new()
    column.add_theme_constant_override("separation", 10)
    margin.add_child(column)

    _title_label = Label.new()
    _title_label.text = "Gardens of Karaxas - Godot Runtime"
    _title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
    _title_label.add_theme_color_override("font_color", Color(0.95, 0.90, 0.78))
    _title_label.add_theme_font_size_override("font_size", 28)
    column.add_child(_title_label)

    _status_label = Label.new()
    _status_label.text = "Waiting for launcher handoff..."
    _status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    _status_label.add_theme_color_override("font_color", Color(0.94, 0.85, 0.70))
    _status_label.add_theme_font_size_override("font_size", 18)
    column.add_child(_status_label)

    _details_label = RichTextLabel.new()
    _details_label.fit_content = false
    _details_label.scroll_active = true
    _details_label.bbcode_enabled = true
    _details_label.custom_minimum_size = Vector2(820, 410)
    _details_label.add_theme_color_override("default_color", Color(0.93, 0.86, 0.74))
    _details_label.add_theme_font_size_override("normal_font_size", 16)
    column.add_child(_details_label)

func _set_status(text: String) -> void:
    if _status_label != null:
        _status_label.text = text

func _set_details(text: String) -> void:
    if _details_label != null:
        _details_label.text = text

func _render_payload_summary(payload: Dictionary, bootstrap_path: String) -> void:
    var character := payload.get("character", {})
    var spawn := payload.get("spawn", {})
    var content := payload.get("content", {})
    var release := payload.get("release", {})
    var runtime := payload.get("runtime", {})

    _set_status("Launcher handoff successful. Runtime payload loaded.")
    var lines := PackedStringArray()
    lines.append("[b]Bootstrap file:[/b] " + bootstrap_path)
    lines.append("[b]Schema:[/b] " + str(payload.get("schema_version", "unknown")))
    lines.append("")
    lines.append("[b]Character[/b]")
    lines.append("Name: " + str(character.get("name", "unknown")))
    lines.append("Appearance: " + str(character.get("appearance_key", "unknown")))
    lines.append("Race/Background/Affiliation: " + str(character.get("race", "?")) + " / " + str(character.get("background", "?")) + " / " + str(character.get("affiliation", "?")))
    lines.append("")
    lines.append("[b]Spawn[/b]")
    lines.append("Floor: " + str(spawn.get("descriptive_name", spawn.get("level_name", "unknown"))))
    lines.append("World position: (" + str(spawn.get("world_x", "?")) + ", " + str(spawn.get("world_y", "?")) + ")")
    lines.append("Source: " + str(spawn.get("source", "unknown")))
    lines.append("")
    lines.append("[b]Versions[/b]")
    lines.append("Client build: " + str(release.get("client_version", "unknown")))
    lines.append("Latest build: " + str(release.get("latest_version", "unknown")))
    lines.append("Content key: " + str(content.get("version_key", "unknown")))
    lines.append("Runtime host: " + str(runtime.get("runtime_host", "unknown")))
    lines.append("")
    lines.append("Gameplay world migration is in progress.")
    lines.append("This panel confirms launcher-to-Godot handoff while runtime systems are being integrated.")
    _set_details("\n".join(lines))

func _find_bootstrap_arg(args: PackedStringArray) -> String:
    for raw_arg in args:
        if raw_arg.begins_with(BOOTSTRAP_ARG_PREFIX):
            return raw_arg.substr(BOOTSTRAP_ARG_PREFIX.length())
    return ""
