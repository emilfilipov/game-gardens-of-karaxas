# Engine Migration Spike - GOK-MMO-176

## Objective
Choose the runtime/editor host stack for the isometric MMORPG transition, using project constraints:
- Windows-first launcher/updater flow remains required.
- FastAPI + Cloud SQL backend remains authoritative.
- Data-driven content/version model remains mandatory.
- Long-term portability target remains Windows, then Linux/Steam, then Android.

## Options Evaluated
- `Option A`: Continue building gameplay/editor directly inside current Kotlin Swing launcher runtime.
- `Option B`: Migrate gameplay + level/editor runtime to Godot 4.x.
- `Option C`: Migrate gameplay + level/editor runtime to Unity (LTS).

## Evaluation Criteria and Weighted Scores
Scoring scale: `1` (poor) to `5` (excellent).

| Criterion | Weight | A: Kotlin Swing | B: Godot 4.x | C: Unity LTS |
| --- | --- | --- | --- | --- |
| 2D isometric runtime fit | 0.20 | 2 | 5 | 4 |
| In-game/editor tooling velocity | 0.20 | 1 | 5 | 4 |
| Integration with existing backend model | 0.15 | 3 | 5 | 4 |
| Team/control/licensing risk | 0.15 | 4 | 5 | 3 |
| Portability path (Linux/Steam/Android) | 0.15 | 2 | 5 | 4 |
| Live-ops friendliness (data-driven updates) | 0.10 | 3 | 5 | 4 |
| CI/build complexity impact | 0.05 | 4 | 4 | 3 |

Weighted totals:
- `Option A`: `2.35`
- `Option B`: `4.95`
- `Option C`: `3.85`

## Decision (Locked)
`GOK-MMO-176` decision: adopt `Godot 4.x` as the authoritative game runtime and world/editor host stack.

Locked host-stack split:
- `launcher/` (Kotlin): account/auth shell, update orchestration, release notes, installer/updater UX.
- `game-client/` (new Godot module): gameplay runtime, world rendering, movement/collision, character visuals, editor-grade scene tooling.
- `backend/` (FastAPI): remains authority for auth/session/content/level/state publish/drain/version gates.

Rationale:
- Best fit for 2D isometric game + content tooling velocity.
- Lowest licensing/business-risk profile for live-service MMO growth.
- Clean portability path while preserving existing launcher/update control plane.
- Strong alignment with data-driven model and API-first service architecture.

## Risk Matrix and Mitigations
| Risk | Probability | Impact | Mitigation |
| --- | --- | --- | --- |
| Migration overlap (Swing runtime + Godot runtime coexistence complexity) | Medium | High | Enforce strict seam: launcher owns auth/update/session bootstrap, Godot owns gameplay/editor only; contract via JSON bootstrap payload and stable local handoff file/schema. |
| Feature regression during parity cutover | Medium | High | Phase cutover by capability gates; keep legacy runtime fallback until parity checklist passes; run side-by-side smoke suite per build. |
| Asset pipeline churn while style evolves | High | Medium | Lock import contract early (`GOK-MMO-179`), add automated ingest validation (`GOK-MMO-180`), and version asset metadata schemas. |
| Performance regressions on large maps | Medium | High | Define frame/memory budgets and perf gates (`GOK-MMO-220`, `GOK-MMO-221`) before broad testing; add zone-stream warm-cache and deterministic eviction. |
| Tooling fragmentation between admin editors and runtime | Medium | Medium | Build shared data contracts first (`v3` schema tasks), keep one authoritative serializer/deserializer package used by editor and runtime. |
| Skill availability/ramp-up for engine-specific workflows | Medium | Medium | Start with small vertical slice and internal conventions; enforce documented code standards and review checklist in module README. |

## Cutover Plan
### Phase 0 - Contract and Scaffold
1. Create `game-client/` Godot module scaffold and CI build hooks.
2. Define launcher-to-game bootstrap contract:
   - session token, character id, content version key, selected floor/location.
3. Add process lifecycle control:
   - launcher starts/stops Godot runtime and receives exit/result state.
4. Keep gameplay disabled in Godot until handshake contract tests pass.

Exit criteria:
- Launcher can open/close Godot window deterministically.
- Bootstrap payload schema validated and versioned.

### Phase 1 - Runtime Parity Slice
1. Port world scene bootstrapping and character spawn rules.
2. Port 8-direction movement and boundary/collision baseline.
3. Port floor transition handoff and active-floor-only rendering.
4. Persist location/floor back to backend on logout/exit.

Exit criteria:
- Character play flow works end-to-end from launcher login to gameplay return.
- Spawn/resume behavior matches current documented rules.

### Phase 2 - Editor Host Migration
1. Move Level Editor v2 workstream to Godot tooling surfaces.
2. Implement layered viewport tools, inspect/edit panels, and v3 schema serialization.
3. Preserve existing draft/publish and audit workflow semantics.

Exit criteria:
- Admin level flow works fully in Godot editor runtime.
- Published level payloads are backward-compatible with backend validation.

### Phase 3 - Asset/Visual Systems
1. Implement paperdoll/equipment layering with DB-driven metadata.
2. Implement shader/effect hooks and day/night per-zone controls.
3. Add production asset import validators and runtime fallback policies.

Exit criteria:
- Character visuals, item overlays, and key effects function from data only.
- Missing/invalid asset inputs fail safely with actionable diagnostics.

### Phase 4 - Hardening and Decommission
1. Run parity and performance soak tests.
2. Disable legacy gameplay scene in `launcher/`.
3. Keep launcher as distribution/auth shell; remove redundant in-launcher gameplay code paths.

Exit criteria:
- Stability/performance gates pass.
- Legacy gameplay path is removed without login/update regressions.

## Rollback Strategy
- Maintain dual-path feature flag until Phase 4 complete:
  - `runtime_host=launcher_legacy|godot`.
- If blocking regressions occur, fallback to legacy path in one config change.
- Keep backend contracts backward-compatible across both clients during transition.

## Dependency Mapping to Backlog
- Immediate downstream tasks: `GOK-MMO-177` through `GOK-MMO-205`.
- Visual and content system follow-ups: `GOK-MMO-206` and beyond.
- This spike locks platform direction; implementation tickets remain required.
