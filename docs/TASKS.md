# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-SPRPG-035 | ⬜ | 4 | Isometric combat/content polish pass: add enemy archetype variety (ranged/caster/elites), status effects, telegraphs, and balancing sweep across ability/resource curves for the first playable chapter. |
| GOK-SPRPG-036 | ⬜ | 3 | Character/equipment visual pass v2: replace placeholder paperdoll text overlays with layered sprite composition and weapon/armor visuals in both world and podium preview. |
| GOK-SPRPG-037 | ⬜ | 3 | Quest pipeline expansion: multi-step objective chains, branching dialogue choices with consequences, and quest rewards wired to item/equipment progression. |
| GOK-SPRPG-038 | ⬜ | 3 | Admin tooling expansion: add undo/redo history stacks for level and asset editors, plus batch apply/rollback snapshots for local draft sessions. |
| GOK-SPRPG-039 | ⬜ | 2 | Save migration/versioning layer: implement save schema version stamps and migration transforms so future config/content updates remain backward compatible. |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-SPRPG-001 | ✅ | 2 | Canonical direction lock: rewrote `docs/GAME.md` and `docs/TECHNICAL.md` for single-player isometric ARPG scope and removed MMO-as-primary assumptions from canonical docs. |
| GOK-SPRPG-002 | ✅ | 3 | Implemented single-player main menu shell in Godot with six actions (`New Game`, `Load Game`, `Settings`, `Update`, `Admin`, `Exit`) and themed controls based on shared UI tokens/components. |
| GOK-SPRPG-003 | ✅ | 3 | Wired `New Game` into character creation and save-slot bootstrap, with world entry gated behind successful character/save creation. |
| GOK-SPRPG-004 | ✅ | 3 | Implemented local save-slot load browser with slot metadata, preview pane, load/delete actions, and refresh behavior. |
| GOK-SPRPG-005 | ✅ | 3 | Refactored settings to single-player local settings domains with auto-apply and local persistence; removed account/MFA dependencies from active runtime flow. |
| GOK-SPRPG-006 | ✅ | 2 | Retained updater as standalone menu action independent of session/account state; uses feed URL from central config/environment fallback and exits only when helper starts successfully. |
| GOK-SPRPG-007 | ✅ | 4 | Implemented admin workspace tab suite (`Level Editor`, `Asset Editor`, `Config Editor`, `Diagnostics`) inside Godot runtime shell. |
| GOK-SPRPG-008 | ✅ | 3 | Removed level-order runtime dependency from active shell flow; level selection/play now targets open-world level files directly. |
| GOK-SPRPG-009 | ✅ | 4 | Implemented local file save architecture (`index + slot payloads`) with slot create/update/delete and world-state persistence callbacks. |
| GOK-SPRPG-010 | ✅ | 4 | Added central local config loading with shipped default template, runtime editable copy, startup validation, and admin config editing path. |
| GOK-SPRPG-011 | ✅ | 4 | Migrated tunable content scaffolds into central config domains (character creation catalogs, movement/combat tunables, tooltips, dialog/quest placeholders, asset metadata). |
| GOK-SPRPG-012 | ✅ | 3 | Added config validation safety rails with startup validation and admin-facing validation feedback. |
| GOK-SPRPG-013 | ✅ | 3 | Added first-pass designer config editor with local JSON edit/save/validate and admin diagnostics integration. |
| GOK-SPRPG-014 | ✅ | 4 | Decommissioned active online Godot runtime path by replacing networked `client_shell.gd` entry flow with local single-player shell and removing auth/session/social runtime dependency. |
| GOK-SPRPG-015 | ✅ | 3 | Backend services moved off active runtime critical path; game client no longer requires backend service availability for core play/create/load flows. |
| GOK-SPRPG-016 | ✅ | 3 | CI/CD cleanup for single-player direction: removed backend deploy/security workflows from active pipeline and kept release packaging/update workflow as primary automation. |
| GOK-SPRPG-017 | ✅ | 2 | Environment/secrets cleanup in docs/workflow: removed backend release-activation callback variables from active release flow and documented active-vs-deprecated variable set. |
| GOK-SPRPG-018 | ✅ | 3 | Replaced account-driven play entry with save-driven world entry and in-game return/save transitions to main menu. |
| GOK-SPRPG-019 | ✅ | 3 | UI consistency pass for single-player shell using shared token/component architecture across main/create/load/settings/admin/world surfaces. |
| GOK-SPRPG-020 | ✅ | 3 | Migrated UI regression harness to single-player shell script and manifest checks for new required builders/snippets. |
| GOK-SPRPG-021 | ✅ | 2 | Standardized local logging/debug model with game log sink and admin diagnostics tab reload/paths views. |
| GOK-SPRPG-022 | ✅ | 2 | Finalized pivot cleanup in canonical docs and workflow behavior so release/update flow is aligned with single-player runtime architecture. |
| GOK-SPRPG-023 | ✅ | 4 | Implemented isometric gameplay combat vertical slice in world runtime with `basic attack`, `Ember`, `Cleave`, `Quick Strike`, and `Bandage` using central config values, ability cooldown/resource tracking, and deterministic enemy hit resolution. |
| GOK-SPRPG-024 | ✅ | 4 | Implemented inventory/equipment foundation: in-world inventory list with use/equip/drop actions, stack handling, equipment slot model, and equipment stat modifiers applied to world combat runtime. |
| GOK-SPRPG-025 | ✅ | 3 | Implemented quest/dialog runtime v1: NPC interaction in world, quest acceptance flow, kill-goal objective progress tracking, and persistence of quest state in local saves. |
| GOK-SPRPG-026 | ✅ | 3 | Modernized Level Editor UX with structured brush workflow: active layer/asset/mode controls, grid/collision overlays, and interactive level canvas (`level_editor_canvas.gd`) while keeping advanced JSON compatibility. |
| GOK-SPRPG-027 | ✅ | 3 | Modernized Asset Editor UX with searchable asset list and structured field forms (key/label/layer/collision/description) plus inline validation and unique-key guard on save. |
| GOK-SPRPG-028 | ✅ | 3 | Completed single-player UI art-direction polish pass: upgraded menu shell composition with release-notes pane, denser spacing rhythm, themed side panels for world systems, and token refinements for cohesive burgundy visual language. |
| GOK-SPRPG-029 | ✅ | 2 | Implemented accessibility/input parity pass: configurable keybindings capture flow, gamepad enable/deadzone settings, UI scale control, high-contrast toggle, and reduced-motion persistence. |
| GOK-SPRPG-030 | ✅ | 3 | Implemented save safety hardening: atomic JSON writes, timestamped backups, automatic backup recovery on read failure, load-screen restore action, and diagnostics visibility of recovered files. |
| GOK-SPRPG-031 | ✅ | 2 | Implemented config schema hardening v2 with explicit schema file (`game_config.schema.json`), schema-backed runtime validation hook, and generated config reference docs (`docs/CONFIG_FIELDS.md`). |
| GOK-SPRPG-032 | ✅ | 2 | Implemented release/patchnote UX iteration by surfacing latest local release notes in both main menu and in-world side panel for player-friendly update visibility. |
| GOK-SPRPG-033 | ✅ | 3 | Added explicit enemy prototype system ticket and implementation: config-driven enemy catalog/spawn rules, AI chase/attack loop, death events, and loot drop spawning integrated into the world runtime. |
| GOK-SPRPG-034 | ✅ | 2 | Added explicit keybinding/gamepad settings ticket and implementation: action-level key rebinding UI capture, persisted keymap settings, runtime keybind propagation, and gamepad tuning controls scaffold. |

## Archived / Superseded
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-* | ✅ | 0 | Entire MMO task stream is superseded by the single-player ARPG direction and retained only as historical reference. |
