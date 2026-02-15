# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-005 | ⬜ | 4 | Implement richer guild-management workflows (invite/promote/kick/permissions UI + API). |
| GOK-MMO-006 | ⬜ | 4 | Add social moderation/reporting tools and chat abuse controls. |
| GOK-MMO-007 | ⬜ | 3 | Add websocket auth refresh/reconnect strategy and horizontal scale strategy for realtime chat broadcast. |
| GOK-MMO-008 | ⬜ | 3 | Add gameplay handoff contract from selected character in lobby to runtime session bootstrap. |
| GOK-MMO-009 | ⬜ | 2 | Add backend integration test suite for auth/session/version policy edge cases. |
| GOK-MMO-010 | ⬜ | 3 | Wire websocket chat client in launcher/game screen for live message streaming (currently REST refresh flow). |

## Finished Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-001 | ✅ | 4 | Scaffold `backend/` FastAPI service with Alembic migrations, Cloud SQL model, auth/session flows, lobby, character, chat, and release ops endpoints. |
| GOK-MMO-002 | ✅ | 4 | Refactor launcher UI into structured card-based account flow (login/register/lobby/character create/select/play/update) with reusable layout tokens. |
| GOK-MMO-003 | ✅ | 3 | Add backend-enforced version policy and release activation endpoint with 5-minute grace window for forced update lockout. |
| GOK-MMO-004 | ✅ | 3 | Split CI behavior so backend-only changes do not trigger launcher releases and backend changes deploy via dedicated backend workflow. |
| GOK-MMO-011 | ✅ | 3 | Move chat/guild surfaces out of account lobby into character-gated in-game screen and enforce selected-character requirement on backend chat APIs. |
| GOK-MMO-012 | ✅ | 3 | Upgrade character create/list/select UI structure with reusable layout blocks and art-preview-ready appearance selector scaffolding. |
| GOK-MMO-013 | ✅ | 3 | Wire male/female character sprite assets (idle + walk/run sheets) into create/select UI previews and persist `appearance_key` on character records. |
| GOK-INIT-001 | ✅ | 2 | Create initial project scaffold with launcher module, build system files, and base documentation. |
| GOK-INIT-002 | ✅ | 2 | Configure GitHub Actions release workflow for launcher-only scaffold mode. |
| GOK-INIT-003 | ✅ | 2 | Enable launcher-only Velopack packaging and publish first installer/release artifacts. |
| GOK-INIT-004 | ✅ | 1 | Replace inherited icon assets with `game_icon.png` and generated `.ico` integration. |
