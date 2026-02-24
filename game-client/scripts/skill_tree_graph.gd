extends Control
class_name SkillTreeGraph

signal node_selected(node_id: String)

const NODE_TYPE_COLORS := {
	"stat": Color(0.47, 0.66, 0.90, 1.0),
	"passive": Color(0.50, 0.76, 0.54, 1.0),
	"active": Color(0.96, 0.69, 0.38, 1.0),
}

var _nodes: Array[Dictionary] = []
var _edges: Array[Dictionary] = []
var _node_lookup: Dictionary = {}
var _allocated_ids: Dictionary = {}
var _hovered_node_id: String = ""
var _selected_node_id: String = ""


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP


func configure_graph(nodes: Array, edges: Array, allocated_ids: Array = []) -> void:
	_nodes.clear()
	_edges.clear()
	_node_lookup.clear()
	_allocated_ids.clear()
	_hovered_node_id = ""
	_selected_node_id = ""
	for raw in nodes:
		if not (raw is Dictionary):
			continue
		var entry: Dictionary = raw
		var node_id = str(entry.get("id", "")).strip_edges().to_lower()
		if node_id.is_empty():
			continue
		var normalized: Dictionary = {
			"id": node_id,
			"label": str(entry.get("label", node_id.capitalize())),
			"type": str(entry.get("type", "passive")).strip_edges().to_lower(),
			"x": clampf(float(entry.get("x", 0.5)), 0.0, 1.0),
			"y": clampf(float(entry.get("y", 0.5)), 0.0, 1.0),
		}
		_nodes.append(normalized)
		_node_lookup[node_id] = normalized
	for raw_edge in edges:
		if not (raw_edge is Dictionary):
			continue
		var edge: Dictionary = raw_edge
		var from_id = str(edge.get("from", "")).strip_edges().to_lower()
		var to_id = str(edge.get("to", "")).strip_edges().to_lower()
		if from_id.is_empty() or to_id.is_empty():
			continue
		if not _node_lookup.has(from_id) or not _node_lookup.has(to_id):
			continue
		_edges.append({"from": from_id, "to": to_id})
	for raw_allocated in allocated_ids:
		var node_id = str(raw_allocated).strip_edges().to_lower()
		if node_id.is_empty():
			continue
		_allocated_ids[node_id] = true
	queue_redraw()


func clear_graph() -> void:
	_nodes.clear()
	_edges.clear()
	_node_lookup.clear()
	_allocated_ids.clear()
	_hovered_node_id = ""
	_selected_node_id = ""
	queue_redraw()


func set_allocated_nodes(allocated_ids: Array) -> void:
	_allocated_ids.clear()
	for raw_allocated in allocated_ids:
		var node_id = str(raw_allocated).strip_edges().to_lower()
		if node_id.is_empty():
			continue
		_allocated_ids[node_id] = true
	queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if _nodes.is_empty():
		return
	if event is InputEventMouseMotion:
		var motion: InputEventMouseMotion = event
		_hovered_node_id = _find_node_at_point(motion.position)
		queue_redraw()
	elif event is InputEventMouseButton:
		var mouse_button: InputEventMouseButton = event
		if mouse_button.button_index != MOUSE_BUTTON_LEFT or not mouse_button.pressed:
			return
		var clicked_id = _find_node_at_point(mouse_button.position)
		if clicked_id.is_empty():
			return
		_selected_node_id = clicked_id
		emit_signal("node_selected", clicked_id)
		queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.96, 0.97, 0.99, 0.86), true)
	_draw_grid()
	for edge in _edges:
		var from_id = str(edge.get("from", ""))
		var to_id = str(edge.get("to", ""))
		if not _node_lookup.has(from_id) or not _node_lookup.has(to_id):
			continue
		var from_node: Dictionary = _node_lookup[from_id]
		var to_node: Dictionary = _node_lookup[to_id]
		var line_color = Color(0.62, 0.69, 0.79, 0.74)
		if _allocated_ids.has(from_id) and _allocated_ids.has(to_id):
			line_color = Color(0.42, 0.74, 0.49, 0.94)
		draw_line(_node_position(from_node), _node_position(to_node), line_color, 2.0, true)
	for node in _nodes:
		_draw_node(node)


func _draw_grid() -> void:
	var columns = 12
	var rows = 8
	var grid_color = Color(0.78, 0.83, 0.90, 0.20)
	for x in range(columns + 1):
		var px = size.x * (float(x) / float(columns))
		draw_line(Vector2(px, 0.0), Vector2(px, size.y), grid_color, 1.0, true)
	for y in range(rows + 1):
		var py = size.y * (float(y) / float(rows))
		draw_line(Vector2(0.0, py), Vector2(size.x, py), grid_color, 1.0, true)


func _draw_node(node: Dictionary) -> void:
	var center = _node_position(node)
	var node_type = str(node.get("type", "passive"))
	var node_id = str(node.get("id", ""))
	var base_color = NODE_TYPE_COLORS.get(node_type, NODE_TYPE_COLORS["passive"])
	var radius = 13.0
	if _allocated_ids.has(node_id):
		radius = 15.0
	if node_id == _hovered_node_id:
		radius += 2.0
	if node_id == _selected_node_id:
		radius += 2.0
	var fill = base_color
	if _allocated_ids.has(node_id):
		fill = fill.lerp(Color(1.0, 1.0, 1.0, 1.0), 0.18)
	draw_circle(center, radius, fill)
	draw_circle(center, radius + 1.5, Color(0.24, 0.28, 0.35, 0.78), false, 2.0)
	var label = str(node.get("label", "")).strip_edges()
	if not label.is_empty():
		draw_string(
			get_theme_default_font(),
			center + Vector2(-34.0, 28.0),
			label,
			HORIZONTAL_ALIGNMENT_LEFT,
			90.0,
			11,
			Color(0.20, 0.24, 0.32, 0.95)
		)


func _node_position(node: Dictionary) -> Vector2:
	var pad_x = maxf(24.0, size.x * 0.05)
	var pad_y = maxf(24.0, size.y * 0.07)
	var px = pad_x + (size.x - pad_x * 2.0) * float(node.get("x", 0.5))
	var py = pad_y + (size.y - pad_y * 2.0) * float(node.get("y", 0.5))
	return Vector2(px, py)


func _find_node_at_point(point: Vector2) -> String:
	for node in _nodes:
		var center = _node_position(node)
		if point.distance_to(center) <= 20.0:
			return str(node.get("id", ""))
	return ""
