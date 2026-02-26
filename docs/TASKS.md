# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Active Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-2D-006 | ⬜ | 5 | Build 512x512 modular spritesheet pipeline for preset archetypes with visible equipment layers (base body + armor/weapon overlays), plus runtime compositing contract. |
| COI-2D-007 | ⬜ | 5 | Add in-world Character Sheet + Inventory systems for ARPG progression (equipment slots, inventory grid, stats summary, and equip/unequip propagation to sprite layers). |
| COI-2D-009 | ⬜ | 3 | Extend runtime gameplay config domains for skill-tree progression semantics and modular-gear mappings (node effects, prerequisites, slot visual maps). |

## Completed
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-2D-054 | ✅ | 3 | Retired deprecated graph-concept references from canonical docs and rebooted UI concept iteration from `ui_concept_*` only by adding `tools/generate_ui_concept_radial_reboot.py`, generating a clean new `pass_01` under `concept_art/option_radial_reboot_blackwhite/pass_01` (boot/gateway/register/play empty/play selected/create/system/update + contact sheet + process notes). |
| COI-2D-044 | ✅ | 2 | Updated concept direction to keep skill-graph context in both selection and creation screens and reflect pre-launch build-save intent in the selection UX exploration (future economy-gated commit path). |
| COI-2D-043 | ✅ | 2 | Added a separate exploratory UI concept set under `concept_art/v2/` (without overwriting existing baseline concepts), emphasizing minimal launch-oriented account flows and optional build-planner placement outside default lobby critical path. |
| COI-2D-042 | ✅ | 2 | Reworked release trigger policy from broad ignore-rules to a strict runtime/package path allowlist so concept/docs/tool-only commits cannot generate new build versions. |
| COI-2D-041 | ✅ | 2 | Produced a third-pass concept-art pack with a single-color background, corrected panel bounds (no sidebar overlap), safer long-text wrapping, and auth-screen simplification (removed login/register subheadline while keeping login footer hints). |
| COI-2D-040 | ✅ | 2 | Expanded release-trigger exclusions from specific concept tooling to all `tools/**` so documentation/concept/tool churn does not auto-run deployment workflows. |
| COI-2D-039 | ✅ | 2 | Added `issues_png/` as a tracked repository folder scaffold (`.gitkeep` + folder-local ignore) so issue screenshots can be staged locally without polluting commits or triggering release flow. |
| COI-2D-038 | ✅ | 3 | Updated GCS release-retention pruning from latest-only to latest-5-version policy (feed `.nupkg` and archive prefixes) to preserve short delta chains while controlling bucket costs. |
| COI-2D-037 | ✅ | 1 | Updated release workflow trigger filters to ignore `concept_art/**` and `issues_png/**` changes so visual-reference image churn no longer triggers deployment builds. |
| COI-2D-036 | ✅ | 2 | Completed a second-pass refinement of UI concept renders by fixing text/button clipping, panel alignment drift, title overlap, and background layering artifacts across all concept screens. |
| COI-2D-035 | ✅ | 3 | Added release-pipeline artifact-retention pruning in GCS so each publish removes feed/archive versions older than the current build and keeps latest-only storage by default. |
| COI-2D-034 | ✅ | 2 | Produced a full UI polish concept pack (`concept_art/`) with one screen per major menu (auth, update, play empty/selected, create, settings tabs) to validate a non-incremental minimal UX direction before implementation. |
| COI-2D-033 | ✅ | 2 | Reworked auth form composition into a tighter shell with narrower login/register cards, shorter input/button controls, and contextual-only status messaging to remove oversized/empty form space. |
| COI-2D-032 | ✅ | 2 | Compacted login/register form presentation by reducing auth panel width, input heights, and control typography to avoid oversized fields. |
| COI-2D-031 | ✅ | 2 | Pinned update-screen build metadata above the notes scroller and reset notes scroll position to the first row on refresh so users can read from the top immediately. |
| COI-2D-030 | ✅ | 3 | Fixed account create-view bounce by preserving `create` mode during deferred character-list refreshes instead of force-returning to `Play` list mode. |
| COI-2D-029 | ✅ | 3 | Prevented unintended menu redirects during update checks by preserving the current screen context for no-update/unavailable/failure update outcomes. |
| COI-2D-028 | ✅ | 2 | Ensured release notes are refreshed from backend summary on startup/auth entry (not only when opening/checking Update). |
| COI-2D-027 | ✅ | 2 | Raised footer build visibility (font size/contrast) so installed client version is easier to sanity check at a glance. |
| COI-2D-026 | ✅ | 4 | Added release-pipeline to backend policy sync step and monotonic activation guard (`allow_version_regression` override only for explicit rollback) to prevent silent `latest_version` drift/regressions. |
| COI-2D-025 | ✅ | 3 | Corrected release-note header policy to show only installed client build metadata in player UI; removed `Latest` build surfacing from runtime update/login screens. |
| COI-2D-024 | ✅ | 2 | Improved release-note readability by wrapping long bullet lines in a compact width for cleaner update-panel scanning. |
| COI-2D-023 | ✅ | 2 | Reduced header vertical footprint (title scale, spacing, margins) to prioritize interactive content area. |
| COI-2D-022 | ✅ | 3 | Rebalanced auth/update shell sizing and panel widths to reduce sparse unused area while preserving compact UX. |
| COI-2D-021 | ✅ | 3 | Standardized selected-state rendering for sidebar buttons and removed disabled-looking active-item visuals. |
| COI-2D-020 | ✅ | 2 | Fixed sidebar selection consistency across auth/register/update/account contexts via explicit visual-state styling. |
| COI-2D-019 | ✅ | 2 | Tightened auth/create/update card heights and removed dead lower space in compact panels. |
| COI-2D-018 | ✅ | 2 | Re-centered auth form content in compact shells to eliminate top-heavy composition. |
| COI-2D-017 | ✅ | 2 | Kept left navigation rail compact and vertically centered with centered button stack alignment. |
| COI-2D-016 | ✅ | 2 | Replaced icon set with a new light-themed initials icon and wired it across launcher, game client, installer wrapper, and packaging assets. |
| COI-2D-015 | ✅ | 4 | Updated installer payload to include separate game + designer executables and added Velopack hook handling to provision/remove both desktop shortcuts. |
| COI-2D-014 | ✅ | 5 | Added backend-managed designer publish endpoint (`/designer/publish`) to commit file changes to GitHub and dispatch release/backend workflows from backend-controlled credentials. |
| COI-2D-013 | ✅ | 4 | Enforced strict latest-build auth gating for all users (register/login/refresh + authenticated context checks), removing outdated-build access regardless of role. |
| COI-2D-012 | ✅ | 4 | Implemented themed updater UX in game auth screen with status persistence (`update_status.json`), percent/speed/size display, and explicit up-to-date dialog flow. |
| COI-2D-011 | ✅ | 3 | Simplified account/create UI by removing small preview cards, top-aligning creation controls, and enforcing empty list graph state when no character is selected. |
| COI-2D-010 | ✅ | 3 | Rebaselined validation for 2D runtime (`check_2d_runtime_contract.py`) and kept UI regression harness updated for current layout signature. |
| COI-2D-008 | ✅ | 4 | Kept runtime client editor-free while advancing external designer tooling: standalone designer app scaffold + login flow + publish integration. |
| COI-2D-005 | ✅ | 4 | Implemented 2-direction spritesheet baseline (`E/W`) with regenerated Sellsword sheets/catalog at `512x512` frame contract. |
| COI-2D-004 | ✅ | 4 | Replaced large account preview focus with graph-first center surface (`skill_tree_graph.gd`) for list/create flows. |
| COI-2D-003 | ✅ | 4 | Refactored account/create layouts for non-fullscreen preview architecture and safe empty-state behavior. |
| COI-2D-002 | ✅ | 4 | Reworked UI token theme toward lighter direction and continued layout cleanup for improved readability. |
| COI-2D-001 | ✅ | 4 | Rebased runtime execution path to 2D-first world/preview stack; removed active 3D contract gating in release flow. |
| COI-2D-000 | ✅ | 1 | Confirmed 2D pivot scope: online top-down ARPG, lighter UI, skill-tree-centered account surface, and separate designer tooling direction. |
