extends RefCounted
class_name UiTokens

const COLORS: Dictionary = {
	"panel_bg": Color(0.08, 0.08, 0.08, 0.97),
	"panel_bg_alt": Color(0.12, 0.12, 0.12, 0.97),
	"panel_bg_deep": Color(0.04, 0.04, 0.04, 0.98),
	"panel_bg_soft": Color(0.17, 0.17, 0.17, 0.95),
	"panel_bg_highlight": Color(0.22, 0.22, 0.22, 0.95),
	"row_bg": Color(0.10, 0.10, 0.10, 0.97),
	"row_bg_selected": Color(0.20, 0.20, 0.20, 0.98),
	"panel_border": Color(0.88, 0.88, 0.88, 0.86),
	"panel_border_soft": Color(0.66, 0.66, 0.66, 0.68),
	"divider": Color(0.78, 0.78, 0.78, 0.46),
	"text_primary": Color(0.95, 0.95, 0.95),
	"text_secondary": Color(0.84, 0.84, 0.84),
	"text_muted": Color(0.69, 0.69, 0.69),
	"text_inverse": Color(0.05, 0.05, 0.05),
	"button_hover": Color(0.28, 0.28, 0.28, 1.0),
	"button_pressed": Color(0.36, 0.36, 0.36, 1.0),
	"button_primary": Color(0.93, 0.93, 0.93, 1.0),
	"button_primary_hover": Color(1.0, 1.0, 1.0, 1.0),
	"button_primary_pressed": Color(0.80, 0.80, 0.80, 1.0),
	"selection_fill": Color(0.95, 0.95, 0.95, 1.0),
	"selection_text": Color(0.05, 0.05, 0.05),
	"veil": Color(0.0, 0.0, 0.0, 0.26),
	"success": Color(0.80, 0.80, 0.80, 1.0),
	"warning": Color(0.65, 0.65, 0.65, 1.0),
	"danger": Color(0.52, 0.52, 0.52, 1.0),
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
