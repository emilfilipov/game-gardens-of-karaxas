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
