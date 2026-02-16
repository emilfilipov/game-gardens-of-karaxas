# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-009 | ⬜ | 2 | Add backend integration test suite for auth/session/version policy edge cases. |

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
| GOK-MMO-008 | ✅ | 3 | Implement gameplay handoff from selected character to in-launcher world session bootstrap (character identity + appearance transfer). |
| GOK-MMO-014 | ✅ | 4 | Refactor launcher shell UX: combined auth toggle card, borderless fullscreen + cog menu, 10-point character allocation UI, and WASD world movement with edge borders. |
| GOK-MMO-015 | ✅ | 2 | Polish auth interactions: Enter-to-submit, full input hint coverage, explicit credential/network error messages, and auth-screen-only small box layout. |
| GOK-MMO-016 | ✅ | 2 | Add remembered last-login email prefill and logged-in-only settings-controlled automatic login with startup refresh-session flow. |
| GOK-MMO-017 | ✅ | 3 | Refactor authenticated shell UX into persistent themed tabs, character-count-based post-login routing, dropdown logout/welcome identity, and immediate character list refresh after create/select actions. |
| GOK-MMO-018 | ✅ | 4 | Add character deletion, global duplicate-name prevention, level/XP scaffold, row-based character play flow, art-loading root fixes, and tab card rendering fixes. |
| GOK-MMO-019 | ✅ | 3 | Harden authenticated scene switching by despawning inactive cards, reduce overlap artifacts with opaque themed surfaces, remove manual refresh controls, and move gameplay to a dedicated scene entered only from character-row play actions. |
| GOK-MMO-020 | ✅ | 3 | Redesign launcher UI chrome to shape-based themed controls (buttons/panels/inputs) while preserving the existing full-screen background image, improving layout stability and reducing PNG-surface rendering artifacts. |
| GOK-MMO-021 | ✅ | 2 | Enforce consistent theme rendering on all launcher buttons (including auth submit/toggle, settings cog, and stat +/- controls) to eliminate platform-default white button artifacts. |
| GOK-MMO-022 | ✅ | 2 | Harden release workflow backend activation notification with retries and non-blocking failure handling so transient backend outages do not fail launcher releases. |
| GOK-MMO-023 | ✅ | 3 | Consolidate authenticated navigation to Create/Select, center auth fields, harden opaque surface rendering, and normalize fixed-size character card layout without horizontal list overflow. |
| GOK-MMO-024 | ✅ | 2 | Normalize launcher text/font theme coverage (including update menu text), style update progress bars for both determinate/indeterminate states, switch register toggle label to `Back`, and hard-pin cog control to a true square render. |
| GOK-MMO-025 | ✅ | 4 | Add admin-only level builder flow (backend `levels` APIs + launcher level editor UI), per-character level assignment controls, and gameplay handoff that loads assigned level spawn/wall collision data. |
| GOK-MMO-026 | ✅ | 2 | Replace hardcoded admin email checks with database-backed `users.is_admin` authority and propagate admin state through auth session payloads to gate launcher admin menus. |
| GOK-MMO-027 | ✅ | 2 | Simplify updater UX to status-text-only feedback (remove progress bars) and reduce update pop-up windows by running Velopack apply in silent mode with a windowless helper binary target. |
| GOK-MMO-028 | ✅ | 3 | Refine authenticated UI structure: remove create-preview animation controls, reorder tabs to Character List/Create/Levels, remove redundant create-screen back navigation, and standardize dropdown/scroll styling through shared themed UI classes. |
| GOK-INIT-001 | ✅ | 2 | Create initial project scaffold with launcher module, build system files, and base documentation. |
| GOK-INIT-002 | ✅ | 2 | Configure GitHub Actions release workflow for launcher-only scaffold mode. |
| GOK-INIT-003 | ✅ | 2 | Enable launcher-only Velopack packaging and publish first installer/release artifacts. |
| GOK-INIT-004 | ✅ | 1 | Replace inherited icon assets with `game_icon.png` and generated `.ico` integration. |
