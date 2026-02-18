# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| - | - | - | Standalone backlog is currently empty. |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-INIT-001 | ✅ | 2 | Created initial project scaffold with launcher module, build system files, and base documentation. |
| GOK-INIT-002 | ✅ | 2 | Configured GitHub Actions release workflow for launcher-only scaffold mode. |
| GOK-INIT-003 | ✅ | 2 | Enabled launcher-only Velopack packaging and published first installer/release artifacts. |
| GOK-INIT-004 | ✅ | 1 | Replaced inherited icon assets with `game_icon.png` and generated `.ico` integration. |
| GOK-MMO-001 | ✅ | 4 | Scaffolded `backend/` FastAPI service with Alembic migrations, Cloud SQL model, auth/session flows, lobby, character, chat, and release ops endpoints. |
| GOK-MMO-002 | ✅ | 4 | Refactored launcher UI into structured card-based account flow with reusable layout tokens. |
| GOK-MMO-003 | ✅ | 3 | Added backend-enforced version policy and release activation endpoint with 5-minute grace window. |
| GOK-MMO-004 | ✅ | 3 | Split CI behavior so backend-only changes do not trigger launcher releases and backend changes deploy independently. |
| GOK-MMO-008 | ✅ | 3 | Implemented gameplay handoff from selected character to in-launcher world session bootstrap. |
| GOK-MMO-009 | ✅ | 2 | Expanded security edge tests with websocket ticket replay protection and publish-drain/session coverage. |
| GOK-MMO-011 | ✅ | 3 | Moved chat/guild surfaces out of lobby into character-gated in-game flow and enforced selected-character requirement. |
| GOK-MMO-012 | ✅ | 3 | Upgraded character create/list/select UI structure with reusable layout blocks and art-preview scaffolding. |
| GOK-MMO-013 | ✅ | 3 | Wired male/female character sprite assets into create/select previews and persisted `appearance_key`. |
| GOK-MMO-014 | ✅ | 4 | Refactored launcher shell UX (combined auth card, cog menu, borderless fullscreen, 10-point allocation, WASD prototype). |
| GOK-MMO-015 | ✅ | 2 | Polished auth interactions: Enter-to-submit, hint text, and explicit credential/network error messaging. |
| GOK-MMO-016 | ✅ | 2 | Added remembered last-login email prefill and logged-in-only settings-controlled automatic login. |
| GOK-MMO-017 | ✅ | 3 | Refactored authenticated shell UX into persistent tabs with character-count-based post-login routing. |
| GOK-MMO-018 | ✅ | 4 | Added character deletion, global duplicate-name prevention, level/XP scaffold, and row-based character play flow. |
| GOK-MMO-019 | ✅ | 3 | Hardened authenticated scene switching to prevent UI overlap artifacts and moved gameplay to dedicated scene entry. |
| GOK-MMO-020 | ✅ | 3 | Redesigned launcher UI chrome to shape-based themed controls while preserving full-screen background image. |
| GOK-MMO-021 | ✅ | 2 | Enforced consistent theme rendering on all launcher buttons to remove platform-default white artifacts. |
| GOK-MMO-022 | ✅ | 2 | Hardened release workflow backend activation notification with retries and non-blocking failure handling. |
| GOK-MMO-023 | ✅ | 3 | Consolidated authenticated navigation to Create/Select with centered auth fields and fixed-size character cards. |
| GOK-MMO-024 | ✅ | 2 | Normalized launcher text/font theming and refined updater/control styling including square cog rendering. |
| GOK-MMO-025 | ✅ | 4 | Added admin-only level builder flow, per-character level assignment, and level-based gameplay handoff. |
| GOK-MMO-026 | ✅ | 2 | Replaced hardcoded admin email checks with database-backed `users.is_admin` authority. |
| GOK-MMO-027 | ✅ | 2 | Simplified updater UX to status text and reduced extra Velopack windows via silent helper mode. |
| GOK-MMO-028 | ✅ | 3 | Refined authenticated UI structure and standardized dropdown/scroll styling through shared themed classes. |
| GOK-MMO-029 | ✅ | 3 | Hardened character art preview asset discovery and expanded level-editor viewport behavior. |
| GOK-MMO-030 | ✅ | 4 | Persisted character runtime location in DB and resumed from saved location on subsequent play sessions. |
| GOK-MMO-031 | ✅ | 3 | Polished updater/level-tool theming, reliability, and removed redundant obsolete UI PNG assets. |
| GOK-MMO-032 | ✅ | 2 | Fixed character preview reliability and sex mapping collisions; preserved sprite aspect ratio. |
| GOK-MMO-033 | ✅ | 3 | Completed create/select UI polish and enabled admin level dropdown play-time spawn override flow. |
| GOK-MMO-034 | ✅ | 4 | Implemented character/lobby/editor upgrades including large virtual level-grid support and UI footprint improvements. |
| GOK-MMO-035 | ✅ | 2 | Persisted full character-creation scaffold selections (`race`, `background`, `affiliation`) in backend and UI. |
| GOK-MMO-036 | ✅ | 1 | Removed platform-default blue highlight from cogwheel dropdown via themed menu-item UI. |
| GOK-MMO-037 | ✅ | 2 | Reworked create-character identity row and fixed-size controls; fit level-editor scene within screen bounds. |
| GOK-MMO-038 | ✅ | 2 | Stabilized create-character preview/controls, fixed-size stat cards, and restored live point-budget indicator. |
| GOK-MMO-039 | ✅ | 2 | Converted skill slots to fixed square buttons and added standardized hover tooltip templates. |
| GOK-MMO-040 | ✅ | 2 | Fixed tooltip theme behavior; moved level-builder load/save/back to top strip; improved invalid-token UX. |
| GOK-MMO-041 | ✅ | 1 | Moved level-builder load dropdown and save name input into top strip near load/save actions. |
| GOK-MMO-042 | ✅ | 4 | Implemented Epic A baseline: layered schema, adapters, APIs, editor tools, rendering order, and collision extraction. |
| GOK-MMO-043 | ✅ | 2 | Added launcher layered payload codec fixtures with legacy wall fallback coverage. |
| GOK-MMO-044 | ✅ | 4 | Implemented Epic B baseline: content version model, snapshot cache/validation, content-driven create UI/tooltips and gating. |
| GOK-MMO-045 | ✅ | 2 | Refactored level-builder asset UX to fixed 3-column layer palette with previews/tooltips and spawn radar marker. |
| GOK-MMO-046 | ✅ | 4 | Implemented admin content-authoring workflow with local staging queue, batch publish, history, and compare view. |
| GOK-MMO-047 | ✅ | 2 | Reworked pre-login updater UX into split auth/update layout with embedded release notes/update action. |
| GOK-MMO-048 | ✅ | 4 | Migrated release/update control plane toward GCS with DB-backed release registry and launcher release summary wiring. |
| GOK-MMO-049 | ✅ | 2 | Stabilized Epic D/E rollout by fixing observability init crash, migrating JWT to `PyJWT`, and enforcing non-root container runtime. |
| GOK-MMO-100 | ✅ | 2 | Defined level-layer schema/constraints with reserved layers `0` (ground), `1` (collision/gameplay), `2` (ambient). |
| GOK-MMO-101 | ✅ | 3 | Added Alembic migration `0008_level_layers` with legacy wall-cell backfill to layered model. |
| GOK-MMO-102 | ✅ | 3 | Enforced collision asset placement/derivation rules in backend save validation. |
| GOK-MMO-103 | ✅ | 3 | Updated level APIs to return layered payloads + schema version while preserving legacy derived wall compatibility. |
| GOK-MMO-104 | ✅ | 2 | Added launcher level-builder active-layer selector and per-layer visibility toggles. |
| GOK-MMO-105 | ✅ | 3 | Scoped placement/erase logic to active layer and protected spawn cells from collision-tile placement. |
| GOK-MMO-106 | ✅ | 3 | Implemented deterministic gameplay renderer layer order and layer-filtered collision extraction. |
| GOK-MMO-107 | ✅ | 2 | Implemented legacy level adapter for backend read/save and launcher load paths. |
| GOK-MMO-108 | ✅ | 2 | Added layered payload serialization/deserialization golden fixtures with legacy fallback coverage. |
| GOK-MMO-110 | ✅ | 3 | Implemented canonical DB-driven content domains (`progression`, `character_options`, `stats`, `skills`, `tuning`, `ui_text`). |
| GOK-MMO-111 | ✅ | 4 | Added content-versioned schema (`content_versions`, `content_bundles`) with publish states. |
| GOK-MMO-112 | ✅ | 3 | Implemented active content snapshot loader/cache with atomic swap and startup seed/repair. |
| GOK-MMO-113 | ✅ | 4 | Replaced constant-based progression with snapshot reads and added content-driven combat coefficient service. |
| GOK-MMO-114 | ✅ | 3 | Added content validation pipeline with structural/uniqueness/bounds/required-text checks and admin validate/activate flow. |
| GOK-MMO-115 | ✅ | 2 | Added launcher bootstrap fetch and local cache stamp for active content snapshots. |
| GOK-MMO-116 | ✅ | 3 | Refactored launcher character-create options to load from content payloads instead of hardcoded lists. |
| GOK-MMO-117 | ✅ | 2 | Externalized stat/skill tooltip and description text into content domains consumed by launcher UI. |
| GOK-MMO-118 | ✅ | 3 | Added launcher fallback to cached snapshot and gameplay/create gating when no valid snapshot exists. |
| GOK-MMO-119 | ✅ | 3 | Added deterministic content-driven combat and content service tests. |
| GOK-MMO-120 | ✅ | 3 | Defined publish transaction semantics with persisted `publish_drain_events` and publish-start metadata broadcast. |
| GOK-MMO-121 | ✅ | 4 | Implemented backend session-drain orchestrator with admin exemption and per-session cutoff deadlines. |
| GOK-MMO-122 | ✅ | 4 | Implemented drain flush/despawn path with persistence/despawn audit outcomes. |
| GOK-MMO-123 | ✅ | 3 | Added websocket publish events for start/warning/forced-logout via realtime hub. |
| GOK-MMO-124 | ✅ | 3 | Wired launcher realtime stream to force non-admin logout UX and return to auth after state save. |
| GOK-MMO-125 | ✅ | 3 | Enforced drain cutoffs in auth/websocket paths with deterministic post-deadline session revocation. |
| GOK-MMO-126 | ✅ | 3 | Added publish-drain audit schema for actor/version/counter/cutoff tracking. |
| GOK-MMO-127 | ✅ | 2 | Added drain safety controls: max concurrent drain lock and rollback endpoint. |
| GOK-MMO-128 | ✅ | 3 | Added integration tests for drain tagging, exemptions, despawn persistence, cutoff revocation, overlap lock behavior. |
| GOK-MMO-130 | ✅ | 2 | Added rollout gating flags and feature-flag visibility endpoint (`/ops/release/feature-flags`). |
| GOK-MMO-131 | ✅ | 2 | Added ops metrics endpoint (`/ops/release/metrics`) including release/content/drain/limiter telemetry. |
| GOK-MMO-132 | ✅ | 2 | Added publish/rollback operational runbooks with verification flows in `docs/OPERATIONS.md`. |
| GOK-MMO-133 | ✅ | 3 | Added concurrent publish-drain stress probe tooling and operations guidance. |
| GOK-MMO-134 | ✅ | 2 | Implemented signed content-contract bootstrap flow and launcher contract-header propagation. |
| GOK-MMO-135 | ✅ | 2 | Added go/no-go production checklist for publish-drain enablement and operational verification points. |
| GOK-MMO-140 | ✅ | 3 | Standardized sanitized error envelopes and removed raw exception leakage from API responses. |
| GOK-MMO-141 | ✅ | 3 | Added in-memory auth/chat write rate limiting with lockout/backoff controls. |
| GOK-MMO-142 | ✅ | 3 | Replaced websocket bearer-token query auth with one-time ws connection tickets. |
| GOK-MMO-143 | ✅ | 2 | Enforced DB TLS defaults (`DB_SSLMODE=require`) with validated config handling. |
| GOK-MMO-144 | ✅ | 3 | Added deploy support for Secret Manager references (`*_SECRET_REF`) and documented least-privilege patterns. |
| GOK-MMO-145 | ✅ | 3 | Added perimeter hardening controls (request size guard + abuse throttles) and Cloud Armor baseline guidance. |
| GOK-MMO-146 | ✅ | 2 | Added security-relevant ops telemetry for rate limiter and forced logout/drain counters. |
| GOK-MMO-147 | ✅ | 2 | Added incident response runbooks for compromise/token leak/abuse/rotation scenarios. |
| GOK-MMO-148 | ✅ | 2 | Added CI vulnerability gates (`pip-audit` + Trivy fail thresholds). |
| GOK-MMO-149 | ✅ | 2 | Added immutable privileged-action audit model and admin audit retrieval endpoint. |
| GOK-MMO-150 | ✅ | 2 | Enforced secure response headers and configurable CORS allowlist in backend middleware. |
| GOK-MMO-151 | ✅ | 2 | Added security readiness checklist and pentest preflight criteria in `docs/SECURITY.md`. |
| GOK-MMO-152 | ✅ | 3 | Migrated CI cloud auth to WIF-only flow and removed service-account JSON key path from release/deploy workflows. |
| GOK-MMO-153 | ✅ | 3 | Added Cloud SQL backup policy automation script and restore-drill script to operationalize backup/restore practice. |
| GOK-MMO-154 | ✅ | 3 | Added monitoring alert bootstrap script for backend reliability signals (5xx and latency baselines) and integrated observability guidance updates. |
| GOK-MMO-155 | ✅ | 3 | Added deep health endpoint (`/health/deep`) and backend deploy smoke gate in CI to fail post-deploy regressions before completion. |
| GOK-MMO-156 | ✅ | 4 | Implemented refresh-token replay/reuse detection with bulk session revocation and immutable security-event logging on compromise signals. |
| GOK-MMO-157 | ✅ | 4 | Added admin MFA/TOTP management APIs and shorter admin refresh-session TTL policy wiring. |
| GOK-MMO-158 | ✅ | 3 | Added Cloud Armor baseline automation script and documented attach/default-rule workflow for MMO perimeter hardening. |
| GOK-MMO-159 | ✅ | 3 | Enforced Secret Manager-first runtime secret injection in deploy flow (plain env fallback now explicit opt-in for local use only). |
| GOK-MMO-160 | ✅ | 2 | Added executable rollback helper scripts for content and release policy rollback actions and expanded runbook coverage. |
| GOK-MMO-161 | ✅ | 3 | Added immutable `security_event_audit` model, auth/session security event capture, ops query endpoint, and metrics aggregation wiring. |
| GOK-MMO-162 | ✅ | 4 | Expanded account security and UX: MFA is now user-configurable (not admin-only) and launcher now ships a full in-session Settings screen with themed Video/Audio/Security tabs, immediate mode apply, and save/cancel unsaved-change confirmations. |
