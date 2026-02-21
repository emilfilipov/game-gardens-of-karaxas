extends RefCounted
class_name UiTokens

const COLORS: Dictionary = {
	"panel_bg": Color(0.12, 0.09, 0.07, 0.95),
	"panel_bg_alt": Color(0.17, 0.12, 0.09, 0.95),
	"panel_bg_deep": Color(0.10, 0.07, 0.06, 0.96),
	"panel_bg_soft": Color(0.20, 0.14, 0.10, 0.93),
	"panel_bg_highlight": Color(0.25, 0.18, 0.13, 0.95),
	"row_bg": Color(0.17, 0.12, 0.09, 0.96),
	"row_bg_selected": Color(0.30, 0.21, 0.15, 0.98),
	"panel_border": Color(0.78, 0.63, 0.42, 1.0),
	"panel_border_soft": Color(0.48, 0.36, 0.24, 1.0),
	"text_primary": Color(0.98, 0.93, 0.82),
	"text_secondary": Color(0.94, 0.84, 0.69),
	"text_muted": Color(0.70, 0.60, 0.48),
	"text_inverse": Color(0.12, 0.08, 0.06),
	"button_hover": Color(0.25, 0.17, 0.12, 1.0),
	"button_pressed": Color(0.33, 0.23, 0.15, 1.0),
	"button_primary": Color(0.56, 0.40, 0.25, 1.0),
	"button_primary_hover": Color(0.64, 0.46, 0.28, 1.0),
	"button_primary_pressed": Color(0.45, 0.32, 0.20, 1.0),
	"selection_fill": Color(0.66, 0.50, 0.31, 1.0),
	"selection_text": Color(1.0, 0.95, 0.85),
	"veil": Color(0.02, 0.02, 0.02, 0.36),
	"success": Color(0.58, 0.83, 0.58, 1.0),
	"warning": Color(0.94, 0.78, 0.43, 1.0),
	"danger": Color(0.92, 0.52, 0.46, 1.0),
}

const SIZES: Dictionary = {
	"button_w": 154,
	"button_h": 38,
	"button_h_lg": 46,
	"input_w": 240,
	"input_h": 38,
	"menu_square": 44,
	"shell_wide_w": 1560,
	"shell_wide_h": 860,
	"shell_auth_w": 1180,
	"shell_auth_h": 680,
	"radius": 4,
	"radius_lg": 8,
	"radius_xl": 12,
}

const SPACING: Dictionary = {
	"xs": 6,
	"sm": 10,
	"md": 14,
	"lg": 18,
	"xl": 24,
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
