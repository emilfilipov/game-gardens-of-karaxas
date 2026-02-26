# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Active Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| PAI-3D-001 | ⬜ | 3 | Rename all player-facing game identity surfaces to `Plompers Arena Inc.` (launcher text, runtime title text, update/release strings, docs references) while preserving updater compatibility for legacy install paths during transition. |
| PAI-3D-002 | ⏳ | 4 | Convert runtime UI theme to black/white using `concept_art/ui_concept_blackwhite/` as layout/style target without removing any existing auth/account/update/settings functionality. |
| PAI-3D-003 | ⬜ | 4 | Preserve and harden account/character/skill-graph parity through the pivot so graph viewer interactions remain available in character list/create and are not regressed by shell/theme refactors. |
| PAI-3D-004 | ⬜ | 5 | Define and implement arena battle-royale gameplay rules for bouncy-ball players (spawn, elimination/placement, ranking objective, and match-end conditions) with server-authoritative values. |
| PAI-3D-005 | ⏳ | 5 | Migrate active runtime world from 2D baseline to a 3D top-down arena scene while keeping login/bootstrap flow intact and preserving backend contracts. |
| PAI-3D-006 | ⏳ | 4 | Implement top-down / Path-of-Exile-like camera rig in 3D with fixed readability constraints (angle, zoom bounds, no disorienting drift). |
| PAI-3D-007 | ⏳ | 5 | Build monochrome-to-color interaction system: all assets default black/white and gain localized color only after player interaction/collision, with reproducible behavior for QA. |
| PAI-3D-008 | ✅ | 3 | Author first 3D playable level as flat arena ground with grass foliage only, optimized for movement/combat readability and colorization validation. |
| PAI-3D-009 | ⏳ | 5 | Create first playable 3D character model (bouncy ball combat avatar), movement controller, collision profile, and animation/VFX hooks required for arena testing. |
| PAI-3D-010 | ⏳ | 5 | Wire end-to-end playable loop: login/register -> character create/select -> play -> spawn in flat grass arena -> controlled movement and interaction colorization. |
| PAI-3D-011 | ⏳ | 4 | Add automated and manual regression gates for new 3D runtime (scene boot, camera contract, movement, graph parity, colorization events) and keep launcher/backend checks green. |

## Detailed Task Specs

### PAI-3D-001 - Product Rename Migration
- Objective: complete rename from legacy `Children of Ikphelion` branding to `Plompers Arena Inc.` for player-facing surfaces.
- Implementation checklist:
  - update launcher/game/designer visible title strings,
  - update release-note title templates and update-screen labels,
  - update installer shortcut display names,
  - audit docs for stale legacy naming and keep only intentional compatibility notes.
- Acceptance criteria:
  - no player-visible legacy name in active runtime flows,
  - explicit technical note exists for any temporary legacy binary/path identifier.
- Validation:
  - `grep -Rsn "Children of Ikphelion\|ChildrenOfIkphelion" docs launcher game-client designer-client`

### PAI-3D-002 - UI Black/White Conversion
- Objective: enforce black/white UI direction aligned to `concept_art/ui_concept_blackwhite/`.
- Implementation checklist:
  - define/update UI tokens for monochrome palette,
  - align shell, cards, controls, and typography to concept composition,
  - apply theme to auth/account/settings/update,
  - preserve menu discoverability and selected-state clarity.
- Acceptance criteria:
  - all core screens render in black/white theme,
  - no fallback/default system-looking surfaces remain in core flow.
- Validation:
  - `python3 game-client/tests/check_ui_regression.py`

### PAI-3D-003 - Graph Viewer and Account Parity
- Objective: preserve current account functionality, especially graph viewer.
- Implementation checklist:
  - keep list/create graph panel mounted and interactive,
  - preserve selection gating behavior for character actions,
  - verify graph state behavior for empty/non-empty character selections,
  - ensure UI/theme changes do not drop graph events.
- Acceptance criteria:
  - graph viewer visible and functional in account list/create,
  - no loss of existing character/account actions.
- Validation:
  - extend and run UI/runtime regression checks for graph surface parity.

### PAI-3D-004 - Arena Ruleset
- Objective: codify battle-royale style gameplay for bouncy-ball players.
- Implementation checklist:
  - define match lifecycle states,
  - define ranking/elimination conditions,
  - define spawn rules and safe start behavior,
  - define scoring/placement payload for progression hooks,
  - integrate with server-authoritative gameplay value resolution.
- Acceptance criteria:
  - reproducible match start -> play -> finish lifecycle,
  - clear top-rank outcome emitted at match end.
- Validation:
  - targeted gameplay integration tests in backend + runtime smoke run.

### PAI-3D-005 - 3D Runtime Migration
- Objective: replace active 2D world path with 3D arena runtime path.
- Implementation checklist:
  - create/activate 3D arena scene and controller scripts,
  - port movement/input glue from shell bootstrap into 3D world entry,
  - preserve world bootstrap contract usage,
  - ensure runtime still enters world only after valid auth/character selection.
- Acceptance criteria:
  - authenticated player can load into 3D arena from account flow,
  - no bootstrap contract regressions.
- Validation:
  - new 3D runtime contract test + manual login-to-world verification.

### PAI-3D-006 - Camera Contract
- Objective: maintain top-down/PoE-like camera in 3D runtime.
- Implementation checklist:
  - implement fixed high-angle camera rig,
  - set zoom bounds and default zoom,
  - ensure player remains readable near arena bounds,
  - avoid abrupt camera jitter/drift.
- Acceptance criteria:
  - camera angle/zoom contract documented and enforced in scene config,
  - movement/combat remains readable in default window sizes.
- Validation:
  - runtime contract check for camera transform constraints.

### PAI-3D-007 - Interaction-Driven Colorization
- Objective: implement monochrome default with localized interaction color reveal.
- Implementation checklist:
  - create shader/material contract for grayscale baseline,
  - add gameplay event hooks for contact/overlap color triggers,
  - apply grass-to-green and wall-impact color prototypes,
  - define persistence/decay policy for revealed color regions,
  - ensure performance stays acceptable with repeated interactions.
- Acceptance criteria:
  - untouched scene remains monochrome,
  - interaction areas gain expected color response,
  - colorization is localized and visible from gameplay camera.
- Validation:
  - visual regression captures + runtime interaction smoke checks.

### PAI-3D-008 - Flat Grass Arena Level
- Objective: author first playable map requested for vertical slice.
- Implementation checklist:
  - create flat arena terrain,
  - place grass foliage at readable density,
  - define spawn points and boundary collisions,
  - tune lighting for black/white baseline readability.
- Acceptance criteria:
  - level loads reliably as first playable arena,
  - grass density supports clear movement and interaction testing.
- Validation:
  - runtime load smoke test + FPS sanity check on target dev hardware.

### PAI-3D-009 - Playable Character Model
- Objective: create first 3D player model and movement-ready controller stack.
- Implementation checklist:
  - produce bouncy-ball character model and material setup,
  - configure collision/physics parameters for bounce behavior,
  - bind input to movement/impulse actions,
  - expose hooks for future ability/skill effects.
- Acceptance criteria:
  - player avatar is controllable and behaves as intended bouncy-ball fighter,
  - collisions with level geometry are stable.
- Validation:
  - runtime movement/collision smoke tests in flat grass arena.

### PAI-3D-010 - End-to-End Playable Wiring
- Objective: deliver testable vertical slice from auth to in-level control.
- Implementation checklist:
  - preserve login/register + character create/select,
  - route play action into 3D arena spawn,
  - verify graph viewer remains available in account hub,
  - confirm movement and colorization are active after spawn.
- Acceptance criteria:
  - user can create account/character and play in arena without debug shortcuts,
  - all required steps work in one normal player flow.
- Validation:
  - scripted/manual end-to-end smoke checklist executed and recorded.

### PAI-3D-011 - Regression Gates
- Objective: keep quality gates in sync with 3D pivot.
- Implementation checklist:
  - add 3D runtime contract check script,
  - add graph parity and colorization-event assertions,
  - maintain launcher/backend check coverage,
  - document expected local validation sequence.
- Acceptance criteria:
  - CI/local checks catch camera/spawn/graph/colorization regressions,
  - release gating references 3D contract instead of legacy 2D-only assumptions.
- Validation:
  - `python3 -m compileall backend/app`
  - `./gradlew :launcher:test`
  - `python3 game-client/tests/check_ui_regression.py`
  - `python3 game-client/tests/check_3d_runtime_contract.py`

## Superseded Backlog (Kept for Traceability)
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-2D-006 | ⏳ | 5 | Superseded by 3D pivot; original 2D modular spritesheet pipeline task retained only for history. |
| COI-2D-007 | ⏳ | 5 | Superseded by 3D pivot; inventory/character sheet goals migrate to 3D runtime presentation tasks. |
| COI-2D-009 | ⏳ | 3 | Superseded scope; progression config work continues under 3D task IDs where applicable. |

## Completed (Current Cycle)
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| PAI-3D-000 | ✅ | 2 | Updated canonical/product-support documentation for Plompers Arena Inc. refactor mandate and produced detailed implementation-ready task breakdown for 3D black/white arena pivot. |
| PAI-3D-012 | ✅ | 4 | Activated 3D runtime path in `client_shell.gd`, added flat grass arena generation with wall boundaries and interaction-driven color reveal in `world_canvas_3d.gd`, introduced plomper ball avatar generation in `sellsword_3d_factory.gd`, and added `check_3d_runtime_contract.py` with release workflow gate migration. |

## Legacy Completed (Pre-Pivot)
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-2D-056 | ✅ | 1 | Refined `tools/generate_ui_concept_blackwhite.py` to preserve title/header contrast and prevent background over-darkening by switching to selective accent darkening; regenerated `concept_art/ui_concept_blackwhite/ui_concept_bw_*.png`. |
| COI-2D-055 | ✅ | 2 | Replaced further graph/blob concept iteration with a direct black/white theme remap of baseline `ui_concept_*.png` screens by adding `tools/generate_ui_concept_blackwhite.py` and generating `concept_art/ui_concept_blackwhite/ui_concept_bw_*.png` plus a contact sheet. |
| COI-2D-054 | ✅ | 3 | Retired deprecated graph-concept references from canonical docs and rebooted UI concept iteration from `ui_concept_*` only by adding `tools/generate_ui_concept_radial_reboot.py`, generating a clean new `pass_01` under `concept_art/option_radial_reboot_blackwhite/pass_01` (boot/gateway/register/play empty/play selected/create/system/update + contact sheet + process notes). |
