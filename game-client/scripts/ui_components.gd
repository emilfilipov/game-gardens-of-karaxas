extends RefCounted
class_name UiComponents


static func label(text_value: String, font_size: int = -1) -> Label:
	var node = Label.new()
	node.text = text_value
	node.add_theme_color_override("font_color", UiTokens.color("text_primary"))
	if font_size > 0:
		node.add_theme_font_size_override("font_size", font_size)
	return node


static func line_edit(placeholder: String, secret: bool = false, min_size: Vector2 = Vector2(0, 0)) -> LineEdit:
	var input = LineEdit.new()
	input.placeholder_text = placeholder
	input.secret = secret
	if min_size == Vector2.ZERO:
		input.custom_minimum_size = Vector2(UiTokens.size("input_w"), UiTokens.size("input_h"))
	else:
		input.custom_minimum_size = min_size
	input.focus_mode = Control.FOCUS_CLICK
	return input


static func button(text_value: String, min_size: Vector2 = Vector2(0, 0), focus_mode: int = Control.FOCUS_NONE) -> Button:
	var node = Button.new()
	node.text = text_value
	node.focus_mode = focus_mode
	if min_size == Vector2.ZERO:
		node.custom_minimum_size = Vector2(UiTokens.size("button_w"), UiTokens.size("button_h"))
	else:
		node.custom_minimum_size = min_size
	return node


static func option(items: Array, min_size: Vector2 = Vector2(0, 0)) -> OptionButton:
	var node = OptionButton.new()
	if min_size == Vector2.ZERO:
		node.custom_minimum_size = Vector2(UiTokens.size("input_w"), UiTokens.size("input_h"))
	else:
		node.custom_minimum_size = min_size
	node.focus_mode = Control.FOCUS_NONE
	for item in items:
		node.add_item(str(item))
	sanitize_option_popup(node)
	return node


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
	content.add_theme_constant_override("separation", UiTokens.spacing("sm"))
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	shell_pad.add_child(content)

	return {
		"wrap": wrap,
		"content": content,
	}
