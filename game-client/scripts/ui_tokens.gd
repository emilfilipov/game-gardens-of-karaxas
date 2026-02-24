extends RefCounted
class_name UiTokens

const COLORS: Dictionary = {
	"panel_bg": Color(0.09, 0.09, 0.10, 0.94),
	"panel_bg_alt": Color(0.13, 0.11, 0.10, 0.94),
	"panel_bg_deep": Color(0.06, 0.06, 0.07, 0.96),
	"panel_bg_soft": Color(0.18, 0.14, 0.11, 0.93),
	"panel_bg_highlight": Color(0.24, 0.18, 0.13, 0.93),
	"row_bg": Color(0.12, 0.11, 0.11, 0.93),
	"row_bg_selected": Color(0.26, 0.19, 0.14, 0.96),
	"panel_border": Color(0.62, 0.55, 0.45, 0.82),
	"panel_border_soft": Color(0.39, 0.34, 0.29, 0.56),
	"divider": Color(0.55, 0.47, 0.38, 0.34),
	"text_primary": Color(0.93, 0.90, 0.84),
	"text_secondary": Color(0.81, 0.74, 0.64),
	"text_muted": Color(0.58, 0.53, 0.47),
	"text_inverse": Color(0.12, 0.10, 0.08),
	"button_hover": Color(0.29, 0.20, 0.15, 1.0),
	"button_pressed": Color(0.21, 0.15, 0.11, 1.0),
	"button_primary": Color(0.48, 0.28, 0.20, 1.0),
	"button_primary_hover": Color(0.59, 0.35, 0.24, 1.0),
	"button_primary_pressed": Color(0.37, 0.22, 0.17, 1.0),
	"selection_fill": Color(0.58, 0.40, 0.30, 1.0),
	"selection_text": Color(0.97, 0.93, 0.86),
	"veil": Color(0.01, 0.01, 0.01, 0.08),
	"success": Color(0.58, 0.83, 0.58, 1.0),
	"warning": Color(0.94, 0.78, 0.43, 1.0),
	"danger": Color(0.92, 0.52, 0.46, 1.0),
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
	"shell_auth_w": 1180,
	"shell_auth_h": 500,
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
