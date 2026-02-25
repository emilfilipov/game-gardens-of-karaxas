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
