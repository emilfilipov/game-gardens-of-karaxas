# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-MMO-177 | ⬜ | 3 | Define `Level Schema v3` for hybrid placement: preserve logical grid data while adding freeform prop transforms (`x/y/z`, rotation, scale, pivot) and stable IDs for per-object editing/versioning. |
| GOK-MMO-178 | ⬜ | 3 | Design backward-compatible migration path from current layered level payloads to `v3` hybrid payloads, including validation/fallback adapters and reversible migration scripts for staged rollout. |
| GOK-MMO-179 | ⬜ | 3 | Establish production art pipeline contract (source formats, export profiles, naming standards, atlas grouping, compression policy, color-space, outline/contrast guidelines, and per-asset metadata requirements). |
| GOK-MMO-180 | ⬜ | 2 | Build automated asset ingest checks (naming/dimensions/pivot/frame-count consistency) to reject invalid art imports before runtime/editor consumption. |
| GOK-MMO-181 | ⬜ | 2 | Define milestone gates for isometric vertical slice: technical completion criteria, visual quality criteria, performance budgets, and explicit go/no-go checkpoints per phase. |
| GOK-MMO-182 | ⬜ | 4 | Implement shared isometric math runtime module with unit tests for coordinate transforms, tile picking, camera offsets, and depth-sort keys; wire it as authoritative math layer for game + editor. |
| GOK-MMO-183 | ⬜ | 4 | Refactor gameplay renderer from top-down layering to isometric draw pipeline with stable Y-sort buckets, object pivot-aware depth ordering, and deterministic layer overrides for effects/foreground occluders. |
| GOK-MMO-184 | ⬜ | 3 | Upgrade movement to 8-direction isometric locomotion (input remap, normalized diagonals, animation direction selection) while preserving authoritative location persistence and transition triggers. |
| GOK-MMO-185 | ⬜ | 4 | Rework collision/walkability for iso space: hybrid tile+shape colliders, layer masks (ground/player/flying/projectile), and precise base-only collision for tall props (for example trees). |
| GOK-MMO-186 | ⬜ | 3 | Add occlusion/visibility rules so tall world props can partially hide entities while preserving gameplay readability (silhouette/outline fallback for obscured player/targets). |
| GOK-MMO-187 | ⬜ | 3 | Port transition-link runtime to iso world coordinates and ensure floor handoff remains seamless (no loading card), including spawn correction and cooldown/debounce safeguards in iso movement flow. |
| GOK-MMO-188 | ⬜ | 4 | Implement zone-stream cache policy for iso runtime: active zone + warm adjacent zones with memory budgets, preload priority near transitions, and deterministic eviction strategy under pressure. |
| GOK-MMO-189 | ⬜ | 3 | Extend zone interest/fanout to entity-state channels (not only presence pings) so multiplayer replication is floor-scoped with optional adjacent preview channels guarded by explicit policy flags. |
| GOK-MMO-190 | ⬜ | 4 | Build `Level Editor v2` shell with modern docked layout (asset browser, hierarchy/layers panel, inspector, viewport, validation panel, change queue) sized for full-screen production workflows. |
| GOK-MMO-191 | ⬜ | 4 | Implement editor command bus with undo/redo stacks, atomic transactions, and deterministic serialization for all authoring actions (placement, transform, collision edits, links, metadata changes). |
| GOK-MMO-192 | ⬜ | 3 | Build searchable asset browser with tags/categories/favorites/recent sets and visual thumbnails/icons; include hover metadata and quick filters for gameplay-critical vs decorative assets. |
| GOK-MMO-193 | ⬜ | 3 | Implement modern placement toolset: single-place, brush paint, erase, box paint, lasso fill, stamp tool, and scatter tool with tunable density/randomization controls. |
| GOK-MMO-194 | ⬜ | 4 | Implement hybrid placement modes: strict grid for gameplay logic assets and freeform transforms for visual props; support mode switching per tool with clear viewport indicators. |
| GOK-MMO-195 | ⬜ | 2 | Add snap system with toggle + steps (`off`, `0.25`, `0.5`, `1 tile`) and per-axis snapping so designers can keep precision where needed without grid-only clunkiness. |
| GOK-MMO-196 | ⬜ | 3 | Add transform gizmos (move/rotate/scale), numeric transform inputs, and pivot editing for selected objects, including multi-select transform operations and alignment/distribution helpers. |
| GOK-MMO-197 | ⬜ | 3 | Implement multi-select editing workflow (marquee, additive/subtractive selection, copy/paste/duplicate, group/ungroup, prefab instance placement) with stable object references. |
| GOK-MMO-198 | ⬜ | 3 | Build robust layer manager (`ground/gameplay/ambient/foreground/custom`) with lock/hide/solo states and batch reassignment tools for selected objects. |
| GOK-MMO-199 | ⬜ | 4 | Implement per-asset collision/hitbox editor with shape primitives and polygon editing; persist collision templates to DB-driven asset definitions and reuse across levels automatically. |
| GOK-MMO-200 | ⬜ | 3 | Add navigation/walkability paint tools and debug overlays to separate walkable logic from visual placement; include exporter that compiles nav/collision artifacts for runtime consumption. |
| GOK-MMO-201 | ⬜ | 3 | Build transition graph editor UX (link creation, destination validation, bidirectional helpers, orphan detection) with graph integrity checks before publish. |
| GOK-MMO-202 | ⬜ | 3 | Add live validation panel for editor drafts (missing assets, invalid links, collision conflicts, out-of-bounds objects, duplicate keys, schema violations) with clickable fix navigation. |
| GOK-MMO-203 | ⬜ | 3 | Add in-editor playtest mode that spawns selected character profile and simulates runtime movement/collision/transition behavior without full relaunch, including quick return to edit mode. |
| GOK-MMO-204 | ⬜ | 4 | Extend local-draft workflow to full level editor v2 object graph with diff previews; publish should create auditable content/version entries and preserve rollback compatibility. |
| GOK-MMO-205 | ⬜ | 3 | Build level version history panel with searchable cards, active marker, revert flow, and side-by-side object-state diff view highlighting added/removed/modified entities. |
| GOK-MMO-206 | ⬜ | 4 | Execute character art upgrade pipeline for iso style: unified skeleton/pose sheets, direction sets, combat states, and consistent silhouette/readability at target zoom levels. |
| GOK-MMO-224 | ⬜ | 4 | Formalize and implement 8-direction character animation contract (`N`,`NE`,`E`,`SE`,`S`,`SW`,`W`,`NW`) for core actions with approved baseline timing: `idle(6f@6fps, loop)`, `walk(8f@10fps, loop)`, `run(8f@12fps, loop)`, `attack(6f@10fps, one-shot, hit@frame4)`, `cast(8f@10fps, one-shot, commit@frame3 spawn@frame5)`, `hit(4f@12fps, one-shot)`, `death(8f@8fps, one-shot hold-last)`; include importer validation + missing-direction CI checks. |
| GOK-MMO-225 | ⬜ | 4 | Implement modular character visual stack (paperdoll layering) using V1 slots: `head`, `shoulder_left`, `shoulder_right`, `chest`, `pants`, `hands`, `feet`, `blood_runes`, `neck`, `ear_left`, `ear_right`, `finger_left`, `finger_right`, `belt`, `consumable_1`, `consumable_2`, `consumable_3`, `weapon_main`, `weapon_off`; empty slots render base body; include future-facing support for per-character base appearance presets and cosmetic visual-overrides/transmog layer. |
| GOK-MMO-226 | ⬜ | 3 | Extend DB-driven item/content schemas to include per-slot visual definitions (atlas key, draw layer, pivot offsets, tint channels, optional effect hooks, style tags) and enforce V1 equip conflicts/handedness: two-handed weapons disable `weapon_off`, `full_body` armor disables `pants`, shields are off-hand only, one-handed weapons default main hand but may be assigned to either hand when no conflict; tag system must be dual-use (`visual` + `functional`) so item tags can bind to gameplay systems (for example poison/bleed/burn status infliction hooks). |
| GOK-MMO-227 | ⬜ | 3 | Add editor + validation workflow for equipment visuals: slot compatibility checks, per-direction sprite completeness, fallback/default visuals, and preview rules for suggested draw behavior (base-layer stack + direction-aware hand layering so weapon/shield can render behind/in-front based on facing); validate main hand=right/off hand=left semantics at equip time. |
| GOK-MMO-228 | ⏳ | 1 | Blocked input ticket for production art pass: provide (1) style reference set (2-4 examples), (2) target sprite resolution + zoom, (3) v1 equipment slot list, (4) v1 weapon/item visual list (at least saber + longsword variants), and (5) v1 per-action frame-count contract; point-1 fallback approved when references are unavailable: proceed with vibrant/warm palette + soft global lighting baseline and rely on per-item/per-character/per-zone effect layers to push selective areas toward grim-dark mood; point-2 guidance to evaluate: recommended MMO baseline is high-detail character frames (`128x128`) + tighter logical iso footprint (`64x32`) + slightly zoomed-out default camera (`~0.80x`, suggested range `0.70x-1.10x`) so more world is visible while keeping placement precision; future change-cost matrix: camera zoom/view distance/fog-of-war are low-cost, sprite on-screen size/render-scale policy are medium-cost, core tile footprint and pivot conventions are high-cost migration items. |
| GOK-MMO-231 | ⬜ | 3 | Seed V1 equipable item visuals across all slots for integration tests (armor/jewelry/runes/consumables/weapons) and place representative pickups in test levels to validate pickup flow, inventory, and character-sheet rendering. Initial list includes: leather cap, leather spaulders (L/R), leather chest, leather pants/breeches, leather gloves, leather boots, chest blood-rune wound, copper necklace (slight glint), copper earrings (slight glint), copper rings (slight glint), leather belt, weapons `{short_sword, knife, brass_knuckles, longsword_2h, spear_1h, spear_2h, wooden_plank_shield, short_bow_2h, long_bow_2h, crossbow_1h, crossbow_2h, spear_of_the_red_mists}` with `spear_of_the_red_mists` red-fog VFX scaffold. |
| GOK-MMO-232 | ⬜ | 4 | Design and implement unified tag registry/contracts used by both content authoring and runtime systems: namespaced tags (`visual.*`, `fx.*`, `status.*`, `combat.*`, etc.), validation rules, conflict/priority resolution, and runtime resolver that maps functional tags to authoritative gameplay handlers (for example `status.poison`, `status.bleed`, `status.burn`) with audit-friendly diagnostics for invalid/unknown tags. |
| GOK-MMO-207 | ⬜ | 4 | Execute environment tileset overhaul by biome/floor themes with modular edge/corner variants, transition blends, and consistent texel density for professional visual cohesion. |
| GOK-MMO-208 | ⬜ | 4 | Implement atmosphere/lighting stack (shadow decals, emissive overlays, fog layers, ambient particles, weather layers) with performance-aware toggles and scalability presets, including global warm/vibrant baseline with effect layers that can shift local zones toward grim-dark presentation. |
| GOK-MMO-209 | ⬜ | 3 | Add material/shader style package for 2D assets (tinting, normal-map optionality, glow masks, highlight effects) to increase depth/readability while keeping art pipeline manageable. |
| GOK-MMO-210 | ⬜ | 3 | Expand prop library quality with variant sets and procedural randomization rules (rotation, tint, scale jitter) to reduce repeated patterns in authored levels. |
| GOK-MMO-211 | ⬜ | 3 | Standardize animation blueprint across entities (idle/walk/run/attack/cast/hit/death/interact) with explicit event-marker schema (`footstep`, `damage_apply`, `resource_spend`, `cast_commit`, `effect_spawn`, `recover_start`, `can_cancel`, `stagger_start`, `control_return`, `death_complete`) and enforce importer validation for missing clips/states/markers. |
| GOK-MMO-212 | ⬜ | 2 | Add post-processing profile system (color grading, vignette, bloom constraints, contrast tuning) with per-zone overrides sourced from data-driven config bundles, designed to support both warm default mood and localized dark/harsh overrides. |
| GOK-MMO-233 | ⬜ | 4 | Implement configurable day/night cycle service per zone/floor: data-driven cycle length, phase offset/start time, speed multiplier, and direction (`forward`/`reversed`) so zones like Mirror can run inverse or slower/faster lighting progression; include smooth interpolation, editor controls, and runtime sync hooks for multiplayer consistency. |
| GOK-MMO-213 | ⬜ | 3 | Refactor game/UI visual language package (fonts, spacing, iconography, tooltips, panel chrome) to match new iso art style and remove remaining prototype-era visual inconsistency. |
| GOK-MMO-214 | ⬜ | 4 | Expand DB-driven content model for asset definitions: visual variants, collision templates, placement rules, layer defaults, editor tags, and runtime behavior flags with strict validation. |
| GOK-MMO-215 | ⬜ | 3 | Expand DB-driven descriptive content coverage (skill/stat descriptions, tooltips, dropdown options, level-up text, affinity/race/background labels) with locale-ready key structure. |
| GOK-MMO-216 | ⬜ | 4 | Add schema registry + migration validator for data-driven bundles so invalid content changes are blocked pre-publish; include actionable diagnostics and auto-generated remediation hints. |
| GOK-MMO-217 | ⬜ | 3 | Add admin approval workflow for staged changes (author -> reviewer -> publish) with immutable audit records and batch publish manifests linking levels/assets/config deltas. |
| GOK-MMO-218 | ⬜ | 3 | Improve publish-to-player messaging: generate user-friendly release notes from changed content fields (for example collision/damage/cost changes) and display by build/content version at login. |
| GOK-MMO-219 | ⬜ | 3 | Add automated test suite for iso transform correctness, level `v3` serialization integrity, collision template propagation, transition graph validity, and editor command undo/redo determinism. |
| GOK-MMO-220 | ⬜ | 3 | Add performance/observability gates for isometric runtime and editor: frame-time histograms, zone preload latency SLOs, memory budgets, and regression alerts in CI/ops dashboards. |
| GOK-MMO-221 | ⬜ | 2 | Create large-level soak/perf scenarios (dense props, many transitions, long sessions) with repeatable scripts and acceptance thresholds before enabling broader player testing. |
| GOK-MMO-222 | ⬜ | 2 | Build vertical-slice acceptance checklist covering art quality, editor productivity, runtime smoothness, and backend data integrity; require full pass before gameplay feature expansion resumes. |
| GOK-MMO-223 | ⬜ | 2 | Prepare post-vertical-slice stabilization sprint plan: bug triage buckets, polish priorities, and explicit handoff from infrastructure/editor upgrade work back to gameplay systems development. |

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
| GOK-MMO-235 | ✅ | 4 | Implemented launcher-to-Godot runtime handoff behind `GOK_RUNTIME_HOST` with per-character bootstrap file emission, external Godot process launch/monitoring, minimize/restore behavior, and automatic fallback to legacy in-launcher gameplay if launch prerequisites fail. |
| GOK-MMO-236 | ✅ | 3 | Added deployable runtime-host defaults: release packaging now copies `game-client/` into payload, emits `runtime_host.properties`, release workflow passes `KARAXAS_RUNTIME_HOST`/`KARAXAS_GODOT_EXECUTABLE`/`KARAXAS_GODOT_PROJECT_PATH` into pack step, and launcher resolves runtime host settings from env > packaged config > defaults. |
| GOK-MMO-237 | ✅ | 2 | Fixed in-launcher gameplay presentation sizing: scene cards now fill full client bounds, gameplay panel chrome/title was removed, and launcher background/title/footer are hidden while `play` scene is active so the game world is not rendered in a small boxed viewport. |
| GOK-MMO-229 | ✅ | 3 | Implemented 8-direction sprite runtime scaffolding in launcher: character art discovery now supports 4-dir and 8-dir sheet metadata, and movement-facing now resolves to 8-way directions when available with automatic 4-way fallback. |
| GOK-MMO-230 | ✅ | 3 | Implemented modular equipment data foundations: assets content domain now supports equipment slots/visual definitions with validation, character records persist equipment loadout JSON, and launcher content bootstrap parsing now ingests equipment slot/visual metadata. |
