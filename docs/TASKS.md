# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-SPRPG-023 | ⬜ | 4 | Isometric gameplay vertical slice: implement player combat loop (`basic attack`, `Ember`, `Cleave`, `Quick Strike`, `Bandage`) using values from central config (`gameplay.combat`), with cooldown/resource UI and deterministic hit resolution in world scene. |
| GOK-SPRPG-024 | ⬜ | 4 | Inventory/equipment foundation: add local inventory model, pickup/drop flow, paperdoll slots, and visual equipment mapping scaffold in character preview/world actor rendering. |
| GOK-SPRPG-025 | ⬜ | 3 | Quest/dialog runtime v1: load quest/dialog definitions from config, implement NPC interaction panel, objective tracking, and save/load persistence for quest progression state. |
| GOK-SPRPG-026 | ⬜ | 3 | Level editor UX modernization: convert raw JSON-heavy panel into structured tool widgets (brushes, palette, placement modes, transform handles, collision overlays) while preserving file compatibility. |
| GOK-SPRPG-027 | ⬜ | 3 | Asset editor UX modernization: searchable asset cards with icon thumbnails, structured field forms, collision-shape editor, and inline validation feedback before save/publish. |
| GOK-SPRPG-028 | ⬜ | 3 | Full UI art-direction pass for single-player shell v2: tighten spacing rhythm, animation/motion polish, responsive breakpoints, and standardized control hierarchy across main/load/create/settings/admin/world menus. |
| GOK-SPRPG-029 | ⬜ | 2 | Accessibility pass: keyboard/gamepad navigation parity for all core screens, scalable UI text preset, contrast verification, and reduced-motion coverage for any new transitions. |
| GOK-SPRPG-030 | ⬜ | 3 | Save safety hardening: transactional save writes with timestamped backup snapshots, restore UI for corrupted slots, and startup recovery diagnostics surfaced in admin diagnostics tab. |
| GOK-SPRPG-031 | ⬜ | 2 | Config schema hardening v2: move validation rules to explicit schema files and generate user-facing config reference docs from schema definitions. |
| GOK-SPRPG-032 | ⬜ | 2 | Release/patchnote UX iteration: enrich in-game update panel with latest release summary and local changelog rendering tuned for non-technical players. |

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

## Archived / Superseded
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-* | ✅ | 0 | Entire MMO task stream is superseded by the single-player ARPG direction and retained only as historical reference. |
