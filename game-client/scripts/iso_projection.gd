extends RefCounted
class_name IsoProjection

const TILE_WIDTH: float = 64.0
const TILE_HEIGHT: float = 32.0
const HALF_TILE_WIDTH: float = TILE_WIDTH * 0.5
const HALF_TILE_HEIGHT: float = TILE_HEIGHT * 0.5

static func world_to_screen(world_position: Vector2) -> Vector2:
	var sx: float = (world_position.x - world_position.y) * HALF_TILE_WIDTH
	var sy: float = (world_position.x + world_position.y) * HALF_TILE_HEIGHT
	return Vector2(sx, sy)

static func screen_to_world(screen_position: Vector2) -> Vector2:
	var wx: float = (screen_position.y / HALF_TILE_HEIGHT + screen_position.x / HALF_TILE_WIDTH) * 0.5
	var wy: float = (screen_position.y / HALF_TILE_HEIGHT - screen_position.x / HALF_TILE_WIDTH) * 0.5
	return Vector2(wx, wy)

static func world_to_tile(world_position: Vector2) -> Vector2i:
	return Vector2i(int(floor(world_position.x)), int(floor(world_position.y)))

static func tile_center_world(tile: Vector2i) -> Vector2:
	return Vector2(float(tile.x) + 0.5, float(tile.y) + 0.5)

static func tile_center_screen(tile: Vector2i) -> Vector2:
	return world_to_screen(tile_center_world(tile))

static func depth_key(floor_order: int, render_layer: int, sort_y: int, sort_x: int, stable_id: int) -> Array:
	return [floor_order, render_layer, sort_y, sort_x, stable_id]

static func run_fixtures() -> Dictionary:
	var fixture_world_points: Array = [
		Vector2(0.0, 0.0),
		Vector2(1.0, 1.0),
		Vector2(12.5, 4.25),
		Vector2(80.0, 48.0),
	]
	var max_error: float = 0.0
	for point in fixture_world_points:
		var screen: Vector2 = world_to_screen(point)
		var roundtrip: Vector2 = screen_to_world(screen)
		max_error = maxf(max_error, point.distance_to(roundtrip))

	var k1: Array = depth_key(1, 0, 10, 4, 100)
	var k2: Array = depth_key(1, 1, 0, 1, 1)
	var k3: Array = depth_key(1, 1, 0, 1, 2)
	var depth_monotonic: bool = k1 < k2 and k2 < k3

	return {
		"max_roundtrip_error": max_error,
		"depth_monotonic": depth_monotonic,
		"ok": max_error <= 0.0001 and depth_monotonic,
	}
