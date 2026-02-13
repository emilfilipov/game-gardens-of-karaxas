# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-001 | ⬜ | 3 | Scaffold `desktop/` runtime module and wire it into Gradle (`settings.gradle.kts`, root/module build files). |
| GOK-002 | ⬜ | 2 | Add launcher fallback behavior/message when game runtime executable is not present. |
| GOK-003 | ⬜ | 4 | Implement first playable runtime boot path for Gardens of Karaxas (window, render loop, input baseline). |
| GOK-004 | ⬜ | 3 | Define and implement save data v1 schema and storage path conventions. |
| GOK-005 | ⬜ | 2 | Add CI step to build both launcher and runtime once `desktop/` exists. |
| GOK-006 | ⬜ | 3 | Integrate runtime into Velopack packaging flow so installer ships launcher + game executable. |
| GOK-007 | ⬜ | 4 | Define and implement first combat prototype slice (real-time top-down encounter loop). |
| GOK-008 | ⬜ | 3 | Add initial character selection flow with at least one fully wired character kit. |
| GOK-009 | ⬜ | 3 | Define floor progression rules for the endless tower and implement first traversal loop. |
| GOK-010 | ⬜ | 2 | Add release checklist doc for launcher-only mode vs full runtime release mode. |

## Finished Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-INIT-001 | ✅ | 2 | Create initial project scaffold with launcher module, build system files, and base documentation. |
| GOK-INIT-002 | ✅ | 2 | Configure GitHub Actions release workflow for launcher-only scaffold mode. |
| GOK-INIT-003 | ✅ | 2 | Enable launcher-only Velopack packaging and publish first installer/release artifacts. |
| GOK-INIT-004 | ✅ | 1 | Replace inherited icon assets with `game_icon.png` and generated `.ico` integration. |
