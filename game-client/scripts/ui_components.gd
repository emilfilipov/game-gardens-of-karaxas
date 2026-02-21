extends RefCounted
class_name UiComponents

const UI_TOKENS = preload("res://scripts/ui_tokens.gd")


static func _style_box(bg: Color, border: Color, radius_name: String = "radius_lg") -> StyleBoxFlat:
	var style = StyleBoxFlat.new()
	style.bg_color = bg
	style.border_width_left = 1
	style.border_width_top = 1
	style.border_width_right = 1
	style.border_width_bottom = 1
	style.border_color = border
	style.corner_radius_top_left = UI_TOKENS.size(radius_name)
	style.corner_radius_top_right = UI_TOKENS.size(radius_name)
	style.corner_radius_bottom_left = UI_TOKENS.size(radius_name)
	style.corner_radius_bottom_right = UI_TOKENS.size(radius_name)
	return style


static func label(text_value: String, font_size: int = -1, color_name: String = "text_primary") -> Label:
	var node = Label.new()
	node.text = text_value
	node.add_theme_color_override("font_color", UI_TOKENS.color(color_name))
	if font_size > 0:
		node.add_theme_font_size_override("font_size", font_size)
	return node


static func line_edit(placeholder: String, secret: bool = false, min_size: Vector2 = Vector2(0, 0)) -> LineEdit:
	var input = LineEdit.new()
	input.placeholder_text = placeholder
	input.secret = secret
	input.clear_button_enabled = true
	if min_size == Vector2.ZERO:
		input.custom_minimum_size = Vector2(UI_TOKENS.size("input_w"), UI_TOKENS.size("input_h"))
	else:
		input.custom_minimum_size = min_size
	input.focus_mode = Control.FOCUS_CLICK
	return input


static func button(text_value: String, min_size: Vector2 = Vector2(0, 0), focus_mode: int = Control.FOCUS_NONE) -> Button:
	var node = Button.new()
	node.text = text_value
	node.focus_mode = focus_mode
	if min_size == Vector2.ZERO:
		node.custom_minimum_size = Vector2(UI_TOKENS.size("button_w"), UI_TOKENS.size("button_h"))
	else:
		node.custom_minimum_size = min_size
	return node


static func _apply_button_style(node: Button, normal: StyleBoxFlat, hover: StyleBoxFlat, pressed: StyleBoxFlat) -> void:
	node.add_theme_stylebox_override("normal", normal)
	node.add_theme_stylebox_override("hover", hover)
	node.add_theme_stylebox_override("pressed", pressed)
	node.add_theme_stylebox_override("focus", normal)
	node.add_theme_color_override("font_color", UI_TOKENS.color("text_primary"))
	node.add_theme_color_override("font_hover_color", UI_TOKENS.color("text_primary"))
	node.add_theme_color_override("font_pressed_color", UI_TOKENS.color("text_primary"))


static func button_secondary(text_value: String, min_size: Vector2 = Vector2(0, 0)) -> Button:
	var node = button(text_value, min_size)
	var normal = _style_box(UI_TOKENS.color("panel_bg_soft"), UI_TOKENS.color("panel_border_soft"), "radius")
	var hover = normal.duplicate()
	hover.bg_color = UI_TOKENS.color("button_hover")
	var pressed = normal.duplicate()
	pressed.bg_color = UI_TOKENS.color("button_pressed")
	_apply_button_style(node, normal, hover, pressed)
	return node


static func button_primary(text_value: String, min_size: Vector2 = Vector2(0, 0)) -> Button:
	var node = button(text_value, min_size, Control.FOCUS_CLICK)
	var normal = _style_box(UI_TOKENS.color("button_primary"), UI_TOKENS.color("panel_border"), "radius")
	var hover = normal.duplicate()
	hover.bg_color = UI_TOKENS.color("button_primary_hover")
	var pressed = normal.duplicate()
	pressed.bg_color = UI_TOKENS.color("button_primary_pressed")
	_apply_button_style(node, normal, hover, pressed)
	return node


static func panel_card(min_size: Vector2 = Vector2(0, 0), selected: bool = false) -> PanelContainer:
	var card = PanelContainer.new()
	if min_size != Vector2.ZERO:
		card.custom_minimum_size = min_size
	var style = _style_box(
		UI_TOKENS.color("row_bg_selected") if selected else UI_TOKENS.color("row_bg"),
		UI_TOKENS.color("panel_border") if selected else UI_TOKENS.color("panel_border_soft"),
		"radius_lg"
	)
	card.add_theme_stylebox_override("panel", style)
	return card


static func option(items: Array, min_size: Vector2 = Vector2(0, 0)) -> OptionButton:
	var node = OptionButton.new()
	if min_size == Vector2.ZERO:
		node.custom_minimum_size = Vector2(UI_TOKENS.size("input_w"), UI_TOKENS.size("input_h"))
	else:
		node.custom_minimum_size = min_size
	node.focus_mode = Control.FOCUS_NONE
	for item in items:
		node.add_item(str(item))
	sanitize_option_popup(node)
	return node


static func status_banner(text_value: String, tone: String = "muted") -> PanelContainer:
	var color_name = "text_secondary"
	if tone == "success":
		color_name = "success"
	elif tone == "warning":
		color_name = "warning"
	elif tone == "danger":
		color_name = "danger"
	var panel = panel_card(Vector2.ZERO, false)
	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", UI_TOKENS.spacing("sm"))
	margin.add_theme_constant_override("margin_top", UI_TOKENS.spacing("xs"))
	margin.add_theme_constant_override("margin_right", UI_TOKENS.spacing("sm"))
	margin.add_theme_constant_override("margin_bottom", UI_TOKENS.spacing("xs"))
	panel.add_child(margin)
	var label_node = label(text_value, -1, color_name)
	margin.add_child(label_node)
	return panel


static func section_card(title_text: String, min_size: Vector2 = Vector2(0, 0)) -> Dictionary:
	var panel = panel_card(min_size, false)
	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", UI_TOKENS.spacing("sm"))
	margin.add_theme_constant_override("margin_top", UI_TOKENS.spacing("sm"))
	margin.add_theme_constant_override("margin_right", UI_TOKENS.spacing("sm"))
	margin.add_theme_constant_override("margin_bottom", UI_TOKENS.spacing("sm"))
	panel.add_child(margin)
	var content = VBoxContainer.new()
	content.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	margin.add_child(content)
	if not title_text.is_empty():
		content.add_child(label(title_text, 18, "text_secondary"))
	return {"panel": panel, "content": content}


static func sanitize_option_popup(option: OptionButton) -> void:
	if option == null:
		return
	var popup = option.get_popup()
	if popup == null:
		return
	for idx in range(popup.get_item_count()):
		popup.set_item_as_radio_checkable(idx, false)
		popup.set_item_as_checkable(idx, false)


static func centered_shell(min_size: Vector2, padding: int = 10) -> Dictionary:
	var wrap = VBoxContainer.new()
	wrap.size_flags_vertical = Control.SIZE_EXPAND_FILL

	var center = CenterContainer.new()
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wrap.add_child(center)

	var shell = PanelContainer.new()
	shell.custom_minimum_size = min_size
	center.add_child(shell)

	var shell_pad = MarginContainer.new()
	shell_pad.add_theme_constant_override("margin_left", padding)
	shell_pad.add_theme_constant_override("margin_top", padding)
	shell_pad.add_theme_constant_override("margin_right", padding)
	shell_pad.add_theme_constant_override("margin_bottom", padding)
	shell.add_child(shell_pad)

	var content = VBoxContainer.new()
	content.add_theme_constant_override("separation", UI_TOKENS.spacing("sm"))
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	shell_pad.add_child(content)

	return {
		"wrap": wrap,
		"content": content,
	}
