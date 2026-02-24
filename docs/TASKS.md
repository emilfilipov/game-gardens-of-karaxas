# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-2D-002 | ⏳ | 4 | Redesign game-client UI from the ground up for a lighter, more pleasant visual direction (new color tokens, panel styles, typography hierarchy, and spacing rhythm) while preserving usability and theming consistency. |
| COI-2D-004 | ⏳ | 4 | Replace large account preview area with a Path of Exile-style passive/active skill tree graph surface (node network with edges, hover details, and allocation interaction model). Baseline graph scaffold is live; gameplay allocation semantics remain pending. |
| COI-2D-006 | ⬜ | 5 | Build 512x512 modular spritesheet pipeline for preset archetypes with visible equipment layers (base body + armor/weapon overlays), plus data contract for runtime compositing. |
| COI-2D-007 | ⬜ | 5 | Add in-world Character Sheet + Inventory systems needed for ARPG gear progression (equipment slots, inventory grid, stats summary, and runtime equip/unequip updates reflected in sprites). |
| COI-2D-008 | ⏳ | 5 | Move level/asset/content editor tooling into a separate designer application, remove editor screens from the runtime client, and keep admin publish workflows available through the external tool. External `designer-client` scaffold is added; full parity migration of all previous editor UX remains pending. |
| COI-2D-009 | ⬜ | 3 | Update backend/runtime gameplay config domains for the new skill-tree and modular-gear authoring model (preset metadata, node graph payloads, item visual layer mappings). |
| COI-2D-010 | ⏳ | 3 | Rebaseline validation pipeline for 2D pivot: replace 3D contract checks with 2D runtime contract checks and keep UI regression + online smoke coverage passing in CI. Workflow/check migration is implemented; full pipeline stability confirmation is in progress through CI runs. |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-2D-005 | ✅ | 4 | Implemented 2-direction spritesheet baseline (`E/W`) with runtime fallback mapping for legacy facing requests, and regenerated Sellsword runtime sheets/catalog to `512x512` + `2dir` naming contract. |
| COI-2D-003 | ✅ | 4 | Rebuilt account list/create layouts for compact preview flow: removed fullscreen podium usage, kept in-game scale inset previews, and preserved selection/no-character safety behavior with explicit preview clearing. |
| COI-2D-001 | ✅ | 4 | Rebased client runtime to 2D-first execution path: 2D world canvas is now the active world renderer path, 2D podium preview is the active account preview component, and 3D runtime contract checks are removed from release gating. |
| COI-2D-000 | ✅ | 1 | Confirmed final pivot scope with product direction locked: online top-down ARPG remains, production returns to 2D spritesheets, light-hearted UI style, skill-tree-first account surface, and separate external designer tool requirement. |
