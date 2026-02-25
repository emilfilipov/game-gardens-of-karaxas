extends RefCounted
class_name UiTokens

const COLORS: Dictionary = {
	"panel_bg": Color(0.93, 0.95, 0.98, 0.97),
	"panel_bg_alt": Color(0.89, 0.92, 0.97, 0.97),
	"panel_bg_deep": Color(0.83, 0.88, 0.95, 0.98),
	"panel_bg_soft": Color(0.98, 0.95, 0.89, 0.95),
	"panel_bg_highlight": Color(0.96, 0.90, 0.78, 0.95),
	"row_bg": Color(0.92, 0.95, 0.99, 0.97),
	"row_bg_selected": Color(0.85, 0.92, 0.98, 0.98),
	"panel_border": Color(0.47, 0.58, 0.73, 0.86),
	"panel_border_soft": Color(0.59, 0.69, 0.81, 0.68),
	"divider": Color(0.49, 0.59, 0.73, 0.46),
	"text_primary": Color(0.10, 0.16, 0.25),
	"text_secondary": Color(0.18, 0.26, 0.38),
	"text_muted": Color(0.30, 0.39, 0.51),
	"text_inverse": Color(0.97, 0.98, 1.0),
	"button_hover": Color(0.81, 0.89, 0.97, 1.0),
	"button_pressed": Color(0.71, 0.81, 0.92, 1.0),
	"button_primary": Color(0.36, 0.57, 0.84, 1.0),
	"button_primary_hover": Color(0.44, 0.64, 0.90, 1.0),
	"button_primary_pressed": Color(0.30, 0.50, 0.77, 1.0),
	"selection_fill": Color(0.45, 0.64, 0.91, 1.0),
	"selection_text": Color(0.97, 0.98, 1.0),
	"veil": Color(0.88, 0.92, 0.98, 0.17),
	"success": Color(0.39, 0.74, 0.46, 1.0),
	"warning": Color(0.89, 0.69, 0.28, 1.0),
	"danger": Color(0.84, 0.39, 0.35, 1.0),
}

const SIZES: Dictionary = {
	"button_w": 154,
	"button_h": 40,
	"button_h_lg": 46,
	"input_w": 240,
	"input_h": 40,
	"menu_square": 44,
	"shell_wide_w": 1560,
	"shell_wide_h": 860,
	"shell_settings_w": 1320,
	"shell_settings_h": 720,
	"shell_auth_w": 1260,
	"shell_auth_h": 560,
	"radius": 2,
	"radius_lg": 5,
	"radius_xl": 8,
}

const SPACING: Dictionary = {
	"xs": 8,
	"sm": 12,
	"md": 18,
	"lg": 28,
	"xl": 36,
}

static func color(name: String) -> Color:
	if COLORS.has(name):
		return COLORS[name]
	return Color.WHITE

static func size(name: String) -> int:
	if SIZES.has(name):
		return int(SIZES[name])
	return 0

static func spacing(name: String) -> int:
	if SPACING.has(name):
		return int(SPACING[name])
	return 0
