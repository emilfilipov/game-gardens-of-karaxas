# Isometric Vertical Slice Gates

## Gate A: Contract and Data Readiness
- `2:1` isometric coordinate contract is locked and documented.
- `Level Schema v3` contract and migration plan are published.
- Asset ingest validation is enforced in CI.

## Gate B: Runtime Technical Readiness
- Isometric transforms are deterministic for render, picking, and collision.
- 8-direction movement works with normalized diagonals.
- Layered sorting is stable under dense prop scenes.
- Floor transitions remain seamless (no loading card).

## Gate C: Editor Production Readiness
- Editor supports hybrid placement (`grid` + `freeform`).
- Undo/redo and staged publish flow are functional.
- Validation panel blocks invalid publish payloads.

## Gate D: Visual Quality Readiness
- Character and tile sets pass readability checks at target zoom.
- Atmosphere stack (lighting/fog/particles) remains within frame budgets.
- UI visual language is consistent and free of placeholder/system controls.

## Gate E: Performance and Ops Readiness
- Frame-time and memory budgets are met on baseline hardware.
- Zone preload latency is within target thresholds.
- Error telemetry and diagnostics are visible in ops dashboards.

## Go/No-Go Criteria
- All gates A-E must be green.
- Any critical regression in render correctness, collision, transition handoff, or version-gating blocks advancement.
