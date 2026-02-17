# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| - | - | - | Standalone backlog is currently empty. Planned work is tracked under Strategic Plan epics below. |

## Strategic Plan (Execution Tracking)
This section tracks execution status for:
- layered level rendering/editing,
- fully data-driven runtime content (non-logic values in DB),
- admin-published content changes that safely log out non-admin users.

Epic A, Epic B, and Epic C are now implemented. Epic D+ remain planned.

### Epic A: Layered Level Model and Level-Builder Layer Editing
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-100 | ✅ | 2 | Level-layer schema and constraints are now defined in backend/launcher with reserved layers `0` (ground/foliage), `1` (gameplay/collision), and `2` (ambient/weather), while preserving extensible numeric layer IDs. |
| GOK-MMO-101 | ✅ | 3 | Added Alembic migration `0008_level_layers` introducing schema-versioned layered level storage and backfilling legacy wall-cell payloads into layer `1` objects. |
| GOK-MMO-102 | ✅ | 3 | Backend save validation now enforces collision asset placement on collision layers only and derives collision data from configured collision assets/layers. |
| GOK-MMO-103 | ✅ | 3 | Level APIs now return `schema_version` and layered payloads (`layers`), while still exposing derived `wall_cells` for backward compatibility. |
| GOK-MMO-104 | ✅ | 2 | Launcher level-builder now includes an active-layer selector and per-layer visibility toggles for edit/inspection workflows. |
| GOK-MMO-105 | ✅ | 3 | Level-builder placement/erase logic is now scoped to active layer; spawn placement remains a separate tool and collision tiles are prevented on spawn cells. |
| GOK-MMO-106 | ✅ | 3 | Gameplay renderer now draws deterministic layer order (`0 -> 1 -> player -> 2`) and collision is derived only from configured collision assets on layer `1`. |
| GOK-MMO-107 | ✅ | 2 | Legacy level adapter is implemented on backend read/save and launcher load paths so old wall/spawn data is auto-translated to layered format. |
| GOK-MMO-108 | ✅ | 2 | Added launcher serialization/deserialization golden fixtures for layered level payload codecs, including legacy wall payload fallback coverage. |

### Epic B: Data-Driven Content and Runtime Tuning Model
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-110 | ✅ | 3 | Implemented canonical content domains for DB-driven values (`progression`, `character_options`, `stats`, `skills`, `tuning`, `ui_text`) with bootstrap defaults and domain contracts. |
| GOK-MMO-111 | ✅ | 4 | Added content-versioned schema via Alembic migration `0009_content_model` (`content_versions`, `content_bundles`) with publish states (`draft`, `validated`, `active`, `retired`). |
| GOK-MMO-112 | ✅ | 3 | Implemented backend active content snapshot loader/cache with atomic in-memory swap and startup seeding/repair (`ensure_content_seed`, `get_active_snapshot`). |
| GOK-MMO-113 | ✅ | 4 | Replaced backend progression/creation constants with content snapshot reads and added combat formula service (`compute_skill_damage`) that sources tunable skill coefficients from snapshot data. |
| GOK-MMO-114 | ✅ | 3 | Added content validation pipeline with structural, uniqueness, numeric-bound, and required-text checks, plus admin validate/activate API flow. |
| GOK-MMO-115 | ✅ | 2 | Added launcher bootstrap fetch (`GET /content/bootstrap`) and client-side cache stamp file (`content_bootstrap_cache.json`) for active content snapshots. |
| GOK-MMO-116 | ✅ | 3 | Refactored launcher character-create option sources (race/background/affiliation, stats, skills, point budget) to load from content payloads rather than hardcoded lists. |
| GOK-MMO-117 | ✅ | 2 | Externalized player-facing stat/skill tooltip/description content to content domains and wired launcher rendering from those payload values. |
| GOK-MMO-118 | ✅ | 3 | Added launcher fallback behavior: use cached snapshot when fetch fails, block gameplay/create when no valid snapshot exists, and surface actionable status text. |
| GOK-MMO-119 | ✅ | 3 | Added deterministic content-driven combat tests (`backend/tests/test_combat_content.py`) and domain validation tests (`backend/tests/test_content_service.py`). |

### Epic C: Admin Publish Flow With Non-Admin Session Drain/Logout
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-120 | ✅ | 3 | Defined publish transaction semantics with persisted `publish_drain_events` records and broadcasted publish-start metadata (`event_id`, `content_version_key`, deadline/grace) before cutoff. |
| GOK-MMO-121 | ✅ | 4 | Implemented backend session-drain orchestrator (`session_drain.py`) that marks non-admin sessions as `draining`, leaves admin sessions untouched, and assigns per-session cutoff deadlines. |
| GOK-MMO-122 | ✅ | 4 | Implemented drain flush/despawn path by clearing selected-character world presence (`characters.is_selected=false`) before revocation and recording per-session persistence/despawn outcome in audit rows. |
| GOK-MMO-123 | ✅ | 3 | Added websocket publish events (`content_publish_started`, `content_publish_warning`, `content_publish_forced_logout`) via realtime hub for both chat/event-stream sockets. |
| GOK-MMO-124 | ✅ | 3 | Wired launcher realtime event stream (`/events/ws`) to force non-admin logout UX: save location if in play, clear auth/session state, and return to auth with required update message. |
| GOK-MMO-125 | ✅ | 3 | Enforced drain cutoffs in backend auth/websocket paths: after deadline non-admin sessions are deterministically revoked and receive `publish_drain_logout`/forced-logout errors. |
| GOK-MMO-126 | ✅ | 3 | Added publish-drain audit schema (`publish_drain_events`, `publish_drain_session_audit`) including actor, version keys, targeted/persist/revoked counters, and cutoff timestamps. |
| GOK-MMO-127 | ✅ | 2 | Added safety controls: configurable max-concurrent drain lock (`publish_drain_max_concurrent`) and admin rollback endpoint (`POST /content/versions/rollback/previous`). |
| GOK-MMO-128 | ✅ | 3 | Added publish-drain integration tests (`backend/tests/test_publish_drain.py`) covering non-admin drain tagging, admin exemption, despawn persistence, cutoff revocation, and overlapping-drain lock behavior. |

### Epic D: Rollout Sequence, Observability, and Hardening
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-130 | ⬜ | 2 | Roll out in phases: schema + read-only snapshot API first, then combat/progression migration, then publish-drain enforcement. Gate each phase behind feature flags. |
| GOK-MMO-131 | ⬜ | 2 | Add operational dashboards/metrics for active content version, snapshot load latencies, drain events, forced logout counts, and failed state-save rates. |
| GOK-MMO-132 | ⬜ | 2 | Add runbooks for content publish and emergency rollback, including expected player-facing UX and admin verification checklist. |
| GOK-MMO-133 | ⬜ | 3 | Perform load/stress tests for publish events under concurrent gameplay sessions and verify no data loss on state persistence path. |
| GOK-MMO-134 | ⬜ | 2 | Freeze and sign content contract (`content schema version`) for launcher/backend compatibility checks during startup/login. |
| GOK-MMO-135 | ⬜ | 2 | Final acceptance pass and production readiness review with explicit go/no-go criteria for enabling publish-triggered forced logout globally. |

### Epic E: Security Hardening and Trust Model
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-009 | ⬜ | 2 | Expand backend integration test suite for auth/session/version-policy security edges (token tamper/replay/expiry/revocation, force-update lockouts, and publish-drain auth transitions). |
| GOK-MMO-140 | ⬜ | 3 | Remove sensitive internal error leakage from API responses; standardize sanitized error envelopes and correlate with server-side request IDs/logs. |
| GOK-MMO-141 | ⬜ | 3 | Add rate limiting and brute-force protections for auth and chat write endpoints (per-IP and per-account thresholds with lockout/backoff policy). |
| GOK-MMO-142 | ⬜ | 3 | Harden websocket auth transport by replacing query-string bearer token with safer handshake/session pattern and short-lived connection credentials. |
| GOK-MMO-143 | ⬜ | 2 | Enforce secure database transport configuration (`sslmode` handling in DSN, environment validation, and non-dev defaults) and document deployment expectations. |
| GOK-MMO-144 | ⬜ | 3 | Move runtime secrets to managed secret storage with rotation policy (`JWT_SECRET`, `OPS_API_TOKEN`, DB credentials) and least-privilege service-account access. |
| GOK-MMO-145 | ⬜ | 3 | Add perimeter protections (WAF/Cloud Armor, abuse throttles, and request-size/body limits) and document safe defaults for internet-exposed services. |
| GOK-MMO-146 | ⬜ | 2 | Add security-focused observability dashboards and alerts (auth failure spikes, token-invalid bursts, forced logout anomalies, suspicious IP behavior). |
| GOK-MMO-147 | ⬜ | 2 | Add formal incident response runbooks for account compromise, token leakage, abuse waves, and emergency secret rotation. |
| GOK-MMO-148 | ⬜ | 2 | Introduce dependency and image vulnerability scanning gates in CI/CD with fail thresholds and triage workflow. |
| GOK-MMO-149 | ⬜ | 2 | Add audit logging requirements for privileged actions (ops release/content publish/admin changes) with immutable retention policy. |
| GOK-MMO-150 | ⬜ | 2 | Define and enforce secure HTTP response headers/CORS policy for backend endpoints and launcher-client origins. |
| GOK-MMO-151 | ⬜ | 2 | Conduct a security readiness review and penetration-test checklist before enabling large-scale public onboarding. |

## Finished Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-001 | ✅ | 4 | Scaffold `backend/` FastAPI service with Alembic migrations, Cloud SQL model, auth/session flows, lobby, character, chat, and release ops endpoints. |
| GOK-MMO-002 | ✅ | 4 | Refactor launcher UI into structured card-based account flow (login/register/lobby/character create/select/play/update) with reusable layout tokens. |
| GOK-MMO-003 | ✅ | 3 | Add backend-enforced version policy and release activation endpoint with 5-minute grace window for forced update lockout. |
| GOK-MMO-004 | ✅ | 3 | Split CI behavior so backend-only changes do not trigger launcher releases and backend changes deploy via dedicated backend workflow. |
| GOK-MMO-008 | ✅ | 3 | Implement gameplay handoff from selected character to in-launcher world session bootstrap (character identity + appearance transfer). |
| GOK-MMO-011 | ✅ | 3 | Move chat/guild surfaces out of account lobby into character-gated in-game screen and enforce selected-character requirement on backend chat APIs. |
| GOK-MMO-012 | ✅ | 3 | Upgrade character create/list/select UI structure with reusable layout blocks and art-preview-ready appearance selector scaffolding. |
| GOK-MMO-013 | ✅ | 3 | Wire male/female character sprite assets (idle + walk/run sheets) into create/select UI previews and persist `appearance_key` on character records. |
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
| GOK-MMO-029 | ✅ | 3 | Harden character art preview rendering (recursive/fallback asset discovery + resilient appearance-key resolution) and expand level-editor viewport to a larger zoomed-out grid with sprite-based spawn marker preview. |
| GOK-MMO-030 | ✅ | 4 | Persist character runtime location in DB (`level_id` + coordinates), resume from saved position on play, expose location in character list/details, and add live-editable level-editor grid dimensions. |
| GOK-MMO-031 | ✅ | 3 | Polish updater/level-tool theming and asset reliability: `Game is up to date` status text, hardened themed combo defaults + scrollbar skinning, grid-size controls moved above grid canvas, payload copy of character art assets, and cleanup of obsolete unused launcher UI PNG resources. |
| GOK-MMO-032 | ✅ | 2 | Fix character preview reliability and sex mapping: probe ancestor asset roots when launcher is started from subdirectories, prevent `female`/`male` substring collisions in appearance selection, and preserve sprite aspect ratio in create/select preview rendering. |
| GOK-MMO-033 | ✅ | 3 | Complete pending create/select UI polish: remove duplicate list heading and rename details panel, remove create preview title, split create screen into stat table + rectangular starter-skill choices with tooltips, anchor create action at bottom-right, and make admin level dropdown act as play-time spawn override. |
| GOK-MMO-034 | ✅ | 4 | Implement follow-up character/lobby UI and editor upgrades: stabilize sex-switch preview scale, add race/background/affiliation create scaffolds, expand stat/skill scaffold capacity, enlarge account shell footprint, and move admin level builder into a dedicated compact scene with virtual `100000x100000` panning grid plus backend schema limit expansion. |
| GOK-MMO-035 | ✅ | 2 | Persist full character-creation scaffold selections by adding backend character profile fields (`race`, `background`, `affiliation`), migration support, launcher create payload wiring, and response rendering in character details. |
| GOK-MMO-036 | ✅ | 1 | Remove platform-default blue highlight from cogwheel dropdown by forcing themed menu-item UI selection/hover colors. |
| GOK-MMO-037 | ✅ | 2 | Rework Create Character identity row so `Race/Background/Affiliation` sit horizontally beside `Name/Sex`, lock stats/skills controls to fixed sizes, and make level-editor scene fit within screen bounds by shrinking canvas minimums and splitting top controls into two compact rows. |
| GOK-MMO-038 | ✅ | 2 | Stabilize Create Character UX by fixing preview zoom consistency, expanding stats into fixed-size control/description cards with square +/- controls, resizing skills to a six-slot row layout, and restoring a live `x/10 points left` indicator beside the create action. |
| GOK-MMO-039 | ✅ | 2 | Convert create-screen skill slots to fixed square buttons (6 per row) and add standardized hover tooltip templates (name, costs, effects, damage/cooldown, type tag, description) with placeholder content for starter skills. |
| GOK-MMO-040 | ✅ | 2 | Fix themed skill tooltip behavior (remove white border artifacts and stabilize hover timing), move level-builder `Load/Save/Back` into the top header strip, improve invalid-token messaging, and enforce grid-input sync + named-level validation during level save. |
| GOK-MMO-041 | ✅ | 1 | Move level-builder `Load Existing` dropdown and `Save Level` name input into the top header strip next to `Load`/`Save`, leaving editor-body rows focused on tool/grid editing controls. |
| GOK-MMO-042 | ✅ | 4 | Implement Epic A baseline: layered level schema + migration/backward adapter, layer-aware API payloads/validation, launcher layer-edit tools (active layer + visibility + tile palette), deterministic layered world rendering, and collision extraction from layer-1 collidable assets. |
| GOK-MMO-043 | ✅ | 2 | Close Epic A test gap by adding launcher layer payload codec fixtures (layered parse/serialize + legacy wall fallback) under `launcher/src/test/kotlin/com/gok/launcher/LevelLayerPayloadCodecTest.kt`. |
| GOK-MMO-044 | ✅ | 4 | Implement Epic B content model end-to-end: content version/bundle schema + APIs, backend snapshot cache/validation, content-driven character rules, launcher content bootstrap caching/fallback, and content-driven create-screen/tooltips with gameplay gating when no valid snapshot exists. |
| GOK-MMO-045 | ✅ | 2 | Refactor level-builder asset UX to a fixed 3-column layer palette (Layer 0/1/2) with fixed-size asset cards, visual asset previews + tooltips, and radar-ping spawn marker replacement in both palette and map canvas. |
| GOK-MMO-046 | ✅ | 4 | Implement admin content-authoring workflow v1: asset-editor `Save Local` staging queue persisted across restarts, batch `Publish Changes` to backend draft versions, new admin `Content Versions` screen (version history cards, active badge, publish/revert actions), and side-by-side item-state compare with changed-item highlighting. |
| GOK-MMO-047 | ✅ | 2 | Rework pre-login updater UX by expanding auth screen into split auth/update layout, embedding compact release-notes + `Update & Restart` controls, and hiding the cog menu on auth while keeping it post-login. |
| GOK-MMO-048 | ✅ | 4 | Migrate release/update control plane toward GCS: added DB-backed release registry (`release_records`), build+content version gating fields in release/session flows, public release summary API for launcher feed/notes, launcher auth/update wiring to release summary + content-version headers, Velopack helper generic feed support, and release workflow publishing to GCS only. |
| GOK-INIT-001 | ✅ | 2 | Create initial project scaffold with launcher module, build system files, and base documentation. |
| GOK-INIT-002 | ✅ | 2 | Configure GitHub Actions release workflow for launcher-only scaffold mode. |
| GOK-INIT-003 | ✅ | 2 | Enable launcher-only Velopack packaging and publish first installer/release artifacts. |
| GOK-INIT-004 | ✅ | 1 | Replace inherited icon assets with `game_icon.png` and generated `.ico` integration. |
