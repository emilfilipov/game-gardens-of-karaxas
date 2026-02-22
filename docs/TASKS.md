# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-284 | ⬜ | 2 | Character flow regression checklist + screenshots: capture login -> list -> create -> play happy path and assert empty-account + one-character + multi-character behavior. |
| GOK-MMO-254 | ⬜ | 4 | Implement isometric runtime foundation in Godot and make it the authoritative render/movement math path: build shared projection helpers (`world<->iso screen`, tile picking, depth key), integrate into gameplay scene, and add deterministic fixture tests for transform round-trip and depth sorting stability. |
| GOK-MMO-255 | ⬜ | 4 | Replace top-down world renderer with isometric draw pipeline: floor tile pass, prop pass, actor pass, and foreground/occluder pass with stable ordering (`floor_order`, `render_layer`, `sort_y`, `sort_x`, `stable_id`), plus fallback diagnostics overlay for sorting conflicts. |
| GOK-MMO-256 | ⬜ | 3 | Upgrade player locomotion to isometric 8-direction behavior: remap WASD to iso vectors, normalize diagonal speed, choose facing buckets (`N`,`NE`,`E`,`SE`,`S`,`SW`,`W`,`NW`), and preserve existing position persistence + transition triggers. |
| GOK-MMO-257 | ⬜ | 4 | Build reusable `CharacterPodiumPreview` component for both Character List and Character Creator: art-directed pedestal scene, configurable backdrop, idle loop playback, direction controls, drag-to-rotate support, and graceful fallback when a direction-specific frame is missing. |
| GOK-MMO-258 | ⬜ | 4 | Implement Character List 2.0 (WoW-inspired structure): left roster rail with search/filter/sort, central podium preview, right detail/action panel, and row actions (`Play`, `Delete`) with selected-character highlight + quick metadata chips (level, zone, last location). |
| GOK-MMO-259 | ⬜ | 4 | Implement Character Creator 2.0 as a multi-step flow: `Appearance` -> `Identity` -> `Stats & Skills` -> `Review`; include step validation, back/next navigation, unsaved-change prompts, and data persistence between steps before final create submission. |
| GOK-MMO-260 | ⬜ | 3 | Build deep appearance customization scaffold in creator step 1: sex/body preset, skin tone, hair style/color, facial options, base stance, and preview lighting profile; wire all selectors to live podium preview updates and persist resulting appearance payload. |
| GOK-MMO-261 | ⬜ | 3 | Integrate existing deep gameplay customization into creator step 3: stats allocation matrix, starter skill selection grid, tooltip templates, remaining-point enforcement, and clear summary visualization before final create. |
| GOK-MMO-262 | ⬜ | 3 | Add creator review/commit pipeline: final summary card, validation errors grouped by step, one-click “jump to invalid step”, and successful creation redirect back to Character List with auto-selection of the new character. |
| GOK-MMO-263 | ⬜ | 3 | Extend backend + DB schema for appearance profile persistence: store creator appearance payload (`appearance_profile` JSON), version it, validate allowed keys/options, and expose in character list APIs so podium preview can reconstruct exact look. |
| GOK-MMO-264 | ⬜ | 3 | Extend content bootstrap to be data-driven for creator options: deliver appearance option catalogs, labels, tooltips, ordering, defaults, and localization keys; client must render from content payload rather than hardcoded option arrays. |
| GOK-MMO-265 | ⬜ | 3 | Art-direct the shell theme for MMO identity refresh (burgundy-forward option included): define palette tiers, typography hierarchy, spacing rhythm, icon rules, panel treatments, and interaction states; apply uniformly to auth, account hub, creator, settings, and admin screens. |
| GOK-MMO-266 | ⬜ | 2 | Add fluid interaction/motion layer: screen transition timing, card hover emphasis, focus ring behavior, menu open/close motion, and reduced-motion fallback toggle for accessibility/performance safety. |
| GOK-MMO-267 | ⬜ | 2 | Implement strict keyboard/focus contract across auth + account flows: Tab/Shift+Tab order in forms, Enter submit behavior, Escape close/cancel behavior, and explicit default button focus; include the login/register textbox tabbing fix as acceptance gate. |
| GOK-MMO-268 | ⬜ | 3 | Build UI regression harness for Godot shell: golden screenshots for major states (auth, list, creator steps, settings, admin), layout overflow assertions, and CI visual-diff checks to prevent future style regressions. |
| GOK-MMO-269 | ⬜ | 4 | Implement Level Editor v2 isometric workspace: docked panels (asset browser, layers, inspector, validation, pending changes), transform gizmos, snap controls, and authoring modes for gameplay-grid assets vs freeform decoration assets. |
| GOK-MMO-270 | ⬜ | 4 | Implement collision/hitbox authoring in editor: per-asset collision template editing, polygon/base-only collision for tall props, layer-mask collision rules, and runtime propagation so edited templates affect gameplay immediately after publish. |
| GOK-MMO-271 | ⬜ | 3 | Complete level transition + floor-order runtime/editor loop in iso mode: transition graph editing, bidirectional link helpers, transition validation, adjacent floor warm-streaming, and seamless handoff without loading cards. |
| GOK-MMO-272 | ⬜ | 3 | Finalize data-driven content governance for gameplay tuning: schema registry, validation diagnostics, version diff UI, and user-facing release-note generation from content deltas (damage/cost/collision/stat text changes). |
| GOK-MMO-273 | ⬜ | 3 | Remove obsolete/redundant shell paths once Character Hub + Creator 2.0 are live: delete superseded list/create panels, remove dead bindings, update docs/screenshots/tests, and keep only the new character UX path. |

## Archived / Superseded Tasks (Direction Cleanup)
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-182..223 | ✅ | 0 | Closed as superseded/consolidated into `GOK-MMO-254..273` during the pivot to a direct isometric + Character Hub/Creator 2.0 roadmap with stricter execution sequencing. |
| GOK-MMO-224..227 | ✅ | 0 | Closed as superseded/consolidated into `GOK-MMO-256`, `GOK-MMO-260..264`, and `GOK-MMO-272` so animation, modular visuals, and content schema work track the new creator/hub implementation path. |
| GOK-MMO-228 | ✅ | 0 | Closed: prior input block resolved by approved visual direction and equipment requirements; follow-up implementation is now explicitly tracked in `GOK-MMO-260..264` and `GOK-MMO-272`. |
| GOK-MMO-231..233 | ✅ | 0 | Closed as superseded/consolidated into `GOK-MMO-260`, `GOK-MMO-264`, `GOK-MMO-269`, and `GOK-MMO-272` to keep item visuals/day-night/content governance aligned with the new execution order. |
| GOK-MMO-242..243 | ✅ | 0 | Closed as superseded/consolidated into `GOK-MMO-273` and `GOK-MMO-268` as part of post-parity cleanup + regression-gate strategy. |
| GOK-MMO-252 | ✅ | 0 | Closed as superseded/consolidated into `GOK-MMO-268` (expanded UI regression harness scope with goldens + overflow + visual diffs). |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-282 | ✅ | 3 | Character Creator ergonomics pass: grouped identity controls into a dedicated panel, tightened control widths, and improved layout consistency without introducing multi-scene flow complexity. |
| GOK-MMO-280 | ✅ | 3 | Character List v2 polish pass: added roster search/filter and denser metadata presentation while preserving fixed-size row cards and stable scroll behavior. |
| GOK-MMO-283 | ✅ | 2 | Character flow QA pass: deterministic refresh hooks remain in place after create/delete/play transitions and stale non-error account status flashes were removed from the account shell. |
| GOK-MMO-281 | ✅ | 3 | Character Creator v1 baseline hardened with discovered-art appearance options and guaranteed single-preset fallback (`human_male`) when optional variants are missing. |
| GOK-MMO-279 | ✅ | 2 | Updated canonical docs for the new account-shell behavior: auth focus-chain contract, compact auth shell sizing, simplified MFA settings structure, and selected-character panel action model. |
| GOK-MMO-278 | ✅ | 3 | Refactored Character List into a 3-column flow (roster rail, center podium preview, right detail/actions) with selected-character bound `Play`/`Delete` controls and admin spawn-override selector on the detail panel. |
| GOK-MMO-277 | ✅ | 2 | Simplified settings MFA UI: removed redundant hint/status layers, converted to compact toggle row, and switched to inline two-column QR/info enrollment layout with refresh/copy controls. |
| GOK-MMO-276 | ✅ | 2 | Hardened MFA disable semantics end-to-end: disabling MFA now clears stored TOTP secret and timestamp server-side, and auth login payload now sends `otp_code=null` when blank to avoid malformed optional OTP handling. |
| GOK-MMO-275 | ✅ | 2 | Fixed auth keyboard flow and compacted login shell: explicit Tab/Shift+Tab focus chain for login/register modes plus reduced auth panel vertical footprint for improved layout density. |
| GOK-MMO-274 | ✅ | 2 | Fixed MFA disable/login bug: backend login MFA enforcement now checks only `mfa_enabled` (not merely secret presence), so accounts with MFA toggled OFF can log in without OTP; added regression tests for disabled-vs-enabled MFA behavior. |
| GOK-MMO-253 | ✅ | 3 | Executed Godot shell modernization pass v2: upgraded global UI tokens, expanded shared component variants, refactored auth/account/settings/admin screens onto consistent card scaffolds, improved character-list row visibility/selection hierarchy, and added subtle screen transition fades for smoother UX flow. |
| GOK-MMO-177 | ✅ | 3 | Defined `Level Schema v3` for hybrid placement with freeform prop transforms (`x/y/z`, rotation, scale, pivot) and stable IDs for per-object editing/versioning. |
| GOK-MMO-178 | ✅ | 3 | Designed backward-compatible migration path from layered legacy payloads to `v3` hybrid payloads with validation/fallback adapters and reversible migration strategy. |
| GOK-MMO-179 | ✅ | 3 | Established production art pipeline contract (source formats, export profiles, naming standards, atlas grouping, compression policy, color-space, and per-asset metadata requirements). |
| GOK-MMO-180 | ✅ | 2 | Built automated asset ingest checks (naming/dimensions/pivot/frame-count consistency) to reject invalid art imports before runtime/editor consumption. |
| GOK-MMO-181 | ✅ | 2 | Defined isometric vertical-slice milestone gates with explicit technical, visual, and performance go/no-go checkpoints. |
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
| GOK-MMO-163 | ✅ | 4 | Implemented tower-zone partitioning baseline with level `order_index`, `descriptive_name`, and transition graph links (`stairs`, `ladder`, `elevator`) persisted through backend APIs and migrations. |
| GOK-MMO-164 | ✅ | 4 | Added seamless floor-to-floor runtime handoff: client preloads adjacent linked floors near transition cells and swaps active floor in-scene without loading cards. |
| GOK-MMO-165 | ✅ | 3 | Implemented spawn routing rules: new characters start at first ordered floor spawn; returning characters resume persisted floor + coordinates with first-floor fallback when missing assignment. |
| GOK-MMO-166 | ✅ | 3 | Extended Level Editor metadata with technical name + `descriptive_name` + optional `order_index`, and wired these fields through local draft/publish payloads. |
| GOK-MMO-167 | ✅ | 4 | Added transition-link authoring in Level Editor with transition palette tools and per-cell destination-level binding persisted through save/publish flows. |
| GOK-MMO-168 | ✅ | 3 | Built admin `Level Order` management scene with drag/drop floor cards and backend publish (`POST /levels/order`) for atomic tower-order updates. |
| GOK-MMO-169 | ✅ | 3 | Added transition asset palette/runtime support for stairs, ladder, and elevator placeholders with themed editor rendering and marker overlays. |
| GOK-MMO-170 | ✅ | 3 | Refactored in-game cog menu scope to gameplay-only controls (`Settings`, `Logout Character`, `Logout Account`, `Exit`) and ensured gameplay-exit actions persist location/session state. |
| GOK-MMO-171 | ✅ | 4 | Implemented zone-scoped realtime presence infrastructure: websocket clients now publish active/adjacent floor scope, backend fanout filters zone events by active floor plus optional adjacent-preview subscriptions, and launcher keeps rendering bound to the active floor scene only. |
| GOK-MMO-172 | ✅ | 3 | Added zone-stream observability and tests: preload-latency + transition-handoff/fallback telemetry now feeds ops metrics, with new backend/launcher tests covering spawn routing, zone filtering hooks, transition/preload helper behavior, and level-order persistence. |
| GOK-MMO-173 | ✅ | 2 | Completed UX validation pass for tower navigation flow by hard-gating gameplay loop updates to gameplay scene visibility, clearing gameplay scope on character logout, and documenting an admin two-level linking validation checklist for repeatable QA. |
| GOK-MMO-174 | ✅ | 3 | Locked isometric visual direction and produced approved art/tech reference board in `docs/ART_DIRECTION_BOARD.md`; fixed projection choice (`2:1`), scale targets (`64x32` tiles, `128x128` character frames), camera defaults (`0.80x`, range `0.70x-1.10x`), warm/soft lighting baseline, readability constraints, and UI-over-world composition rules. |
| GOK-MMO-175 | ✅ | 3 | Produced and locked formal isometric coordinate contract in `docs/ISOMETRIC_COORDINATE_SPEC.md` covering world<->screen transforms, tile ownership/origin conventions, pivot rules, stable draw-order tie breakers, and deterministic rounding for movement/collision/editor picking. |
| GOK-MMO-176 | ✅ | 4 | Completed engine migration spike in `docs/ENGINE_SPIKE_GOK_MMO_176.md` with Godot-vs-Unity evaluation matrix, risk matrix, locked runtime/editor host decision (Godot 4.x), phased cutover plan, and reversible rollback strategy. |
| GOK-MMO-234 | ✅ | 3 | Implemented Godot migration Phase 0 scaffold: added `game-client/` Godot project shell, versioned launcher-to-runtime bootstrap contract schema (`gok_runtime_bootstrap_v1`), and launcher bootstrap payload codec/tests for deterministic handoff serialization. |
| GOK-MMO-235 | ✅ | 4 | Implemented launcher-to-Godot runtime handoff behind `GOK_RUNTIME_HOST` with per-character bootstrap file emission, external Godot process launch/monitoring, and explicit startup diagnostics. |
| GOK-MMO-236 | ✅ | 3 | Added deployable runtime-host defaults: release packaging now copies `game-client/` into payload, emits `runtime_host.properties`, release workflow passes `KARAXAS_RUNTIME_HOST`/`KARAXAS_GODOT_EXECUTABLE`/`KARAXAS_GODOT_PROJECT_PATH` into pack step, and launcher resolves runtime host settings from env > packaged config > defaults. |
| GOK-MMO-237 | ✅ | 2 | Fixed in-launcher gameplay presentation sizing: scene cards now fill full client bounds, gameplay panel chrome/title was removed, and launcher background/title/footer are hidden while `play` scene is active so the game world is not rendered in a small boxed viewport. |
| GOK-MMO-238 | ✅ | 3 | Implemented bundled Godot runtime delivery for Windows releases: CI now downloads and optionally SHA-verifies Godot runtime when `runtime_host=godot`, pack step embeds executable at `game-client/runtime/windows/godot4.exe`, and launcher executable resolution now prefers bundled runtime paths before PATH-based command fallback. |
| GOK-MMO-239 | ✅ | 2 | Decoupled updater and log-viewer menu actions: `Update & Restart` remains available to all authenticated users, while a new admin-only `Log Viewer` dropdown action opens logs without triggering update checks. |
| GOK-MMO-240 | ✅ | 2 | Improved Godot handoff diagnostics/UX: launcher now streams external runtime output into launcher logs and no longer auto-minimizes on launch; Godot bootstrap scene now renders a visible handoff summary panel (character/spawn/version data) instead of a blank scaffold view. |
| GOK-MMO-241 | ✅ | 4 | Migrated to a Godot-first unified client shell: auth/register/account/world/log-viewer/update UX now runs in `game-client` with default fullscreen startup, hidden auth cog, and packaged runtime defaults set to `godot`; launcher now acts as thin bootstrap/orchestrator and aborts startup if configured Godot host cannot launch. |
| GOK-MMO-244 | ✅ | 2 | Hotfixed Godot startup gray-screen parse failures by replacing unsupported `StackContainer` usage with a `Control` screen stack and fixing strict GDScript type declarations in async HTTP/error-handling paths. |
| GOK-MMO-245 | ✅ | 3 | Completed Godot parity hardening pass: themed login/account/admin shells now use shared styled controls with background art, gameplay screen suppresses non-essential shell chrome, admin `Level Order` flow is available in Godot, local draft persistence helpers were restored, and runtime icon/logging/path resolution were hardened for packaged installs. |
| GOK-MMO-246 | ✅ | 2 | Added full MFA QR parity in Godot: backend `/auth/mfa/setup` now returns QR SVG payload and settings screen now shows a themed QR enrollment popup with copy-secret/copy-URI fallback actions. |
| GOK-MMO-229 | ✅ | 3 | Implemented 8-direction sprite runtime scaffolding in launcher: character art discovery now supports 4-dir and 8-dir sheet metadata, and movement-facing now resolves to 8-way directions when available with automatic 4-way fallback. |
| GOK-MMO-230 | ✅ | 3 | Implemented modular equipment data foundations: assets content domain now supports equipment slots/visual definitions with validation, character records persist equipment loadout JSON, and launcher content bootstrap parsing now ingests equipment slot/visual metadata. |
