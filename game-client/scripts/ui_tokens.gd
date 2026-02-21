extends RefCounted
class_name UiTokens

const COLORS: Dictionary = {
	"panel_bg": Color(0.14, 0.10, 0.08, 0.96),
	"panel_bg_alt": Color(0.18, 0.13, 0.10, 0.98),
	"panel_bg_deep": Color(0.13, 0.10, 0.08, 0.98),
	"panel_border": Color(0.68, 0.52, 0.34, 1.0),
	"text_primary": Color(0.95, 0.89, 0.77),
	"text_secondary": Color(0.94, 0.83, 0.68),
	"text_muted": Color(0.72, 0.62, 0.49),
	"button_hover": Color(0.24, 0.18, 0.13, 1.0),
	"button_pressed": Color(0.29, 0.21, 0.15, 1.0),
	"selection_fill": Color(0.56, 0.43, 0.27, 1.0),
	"selection_text": Color(0.96, 0.90, 0.80),
	"veil": Color(0.03, 0.02, 0.02, 0.30),
}

const SIZES: Dictionary = {
	"button_w": 140,
	"button_h": 36,
	"input_w": 220,
	"input_h": 34,
	"menu_square": 44,
	"shell_wide_w": 1360,
	"shell_wide_h": 760,
	"shell_auth_w": 930,
	"shell_auth_h": 560,
	"radius": 2,
}

const SPACING: Dictionary = {
	"xs": 4,
	"sm": 8,
	"md": 10,
	"lg": 12,
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
