# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-ONLINE-022 | ⬜ | 3 | Optional art-tool integration backlog item: formalize external artist workflow for `Aseprite`/`Krita` and import automation into the repo pipeline. Scope includes (1) canonical folder/naming/export conventions for layered source files and runtime sprite sheets, (2) optional CLI export wrappers where tooling is available locally, (3) validation script updates to fail on malformed/partial packs, and (4) concise contributor documentation for handoff between art authoring and runtime ingest. Deferred until active art production requires it. |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-ONLINE-028 | ✅ | 2 | Synced `assets/iso_asset_manifest.json` Sellsword idle registry entries to the current `640x640` generated sheets (`*_640` keys/paths, `5120x5120` sheet dimensions) so release-time asset ingest validation succeeds after fidelity-v2 generation changes. |
| COI-ONLINE-026 | ✅ | 4 | Implemented account-hub UX polish pass from live feedback: removed manual list refresh action in favor of auto-refresh on view transitions, eliminated duplicate create buttons in list flow, hid left list sidebar during create flow, converted top-right settings cog into rectangular `Menu` button, moved create-flow back action to right sidebar footer, reordered create fields (`Character Name`, `Character Type`, `Sex`, `Character Type Lore`), removed starter-skills line from create lore block, and removed input field titles for name/type/sex. |
| COI-ONLINE-027 | ✅ | 5 | Implemented preview grounding + sprite fidelity v2: added podium grounding anchor/contact shadow/floor strip to prevent floating in large preview, added stronger world-scale inset backdrop/border for readability, upgraded procedural sellsword generator detail pass (armor/cloth/hair/face shading and materials), and increased generated source frame fidelity to `640x640` while preserving runtime world downscale behavior. |
| COI-ONLINE-001 | ✅ | 3 | Pivot baseline established: renamed project/product surfaces to Children of Ikphelion (user-facing), reactivated Godot online shell entry (`client_shell.gd`), preserved isometric world runtime, and introduced backend file-based runtime gameplay config endpoint (`/content/runtime-config`) with client-side fallback to `/content/bootstrap`. |
| COI-ONLINE-002 | ✅ | 4 | Added authenticated request recovery in Godot shell: automatic `/auth/refresh` retry for protected `401` responses, single retry of original request, and safe session reset to auth screen when refresh fails. |
| COI-ONLINE-003 | ✅ | 4 | Added backend world bootstrap contract endpoint (`/characters/{id}/world-bootstrap`) and client play-flow integration so world entry is assembled from one server-authored payload (character snapshot, level payload, spawn coordinates, runtime config descriptor/domains, version policy, instance assignment). |
| COI-ONLINE-004 | ✅ | 5 | Implemented party service v1 (`/party`) with create/invite/accept/decline/leave/kick/promote-owner and party-aware instance routing for world entry. |
| COI-ONLINE-005 | ✅ | 5 | Implemented hub-scoped websocket presence behavior: zone presence broadcasts limited to hub levels and deduplicated hub join/leave fanout tracking in realtime hub state. |
| COI-ONLINE-006 | ✅ | 4 | Implemented instance lifecycle manager with deterministic instance IDs (`solo/party/hub`), session assignment persistence, expiration handling, reconnect-aware restoration hints, and `/instances/current` + `/instances/heartbeat`. |
| COI-ONLINE-007 | ✅ | 4 | Added server-authoritative gameplay action resolver (`/gameplay/resolve-action`) with skill validation, XP/level progression updates, loot grants, and persistence of authoritative location/progression changes. |
| COI-ONLINE-008 | ✅ | 3 | Hardened runtime gameplay config service with schema/domain validation, explicit schema+version metadata, signature pin enforcement, staged publish, active publish, and rollback endpoints under `/content/runtime-config/*`. |
| COI-ONLINE-009 | ✅ | 3 | Added runtime gameplay config cache with signature verification in Godot client (`runtime_gameplay_cache.json`) and safe fallback when runtime-config endpoint is unavailable. |
| COI-ONLINE-010 | ✅ | 3 | Added dedicated `Security Scan` workflow and expanded backend deploy workflow with post-deploy smoke coverage (`health/deep` + online auth/character/gameplay loop smoke). |
| COI-ONLINE-011 | ✅ | 3 | Continued naming migration and compatibility pass for Children of Ikphelion across backend defaults/scripts and build metadata while preserving compatibility where required for existing installs. |
| COI-ONLINE-012 | ✅ | 4 | Consolidated admin-only boundaries for designer/config publish surfaces (level/content/runtime-config controls) with existing grace/forced-logout publish-drain enforcement. |
| COI-ONLINE-013 | ✅ | 3 | Expanded observability with auth success/failure counters, websocket disconnect reason tracking, instance assignment/restore counters, and instance occupancy metrics exposed via ops metrics endpoint. |
| COI-ONLINE-014 | ✅ | 4 | Added end-to-end online smoke harness (`backend/scripts/smoke_online_loop.py`) for register/login/MFA toggle/create/bootstrap/location/gameplay authority flow validation. |
| COI-ONLINE-015 | ✅ | 4 | Updated updater UX messaging to show build/content release context and clearer forced-update/content-mismatch reasons in client-side user-facing error/status copy. |
| COI-ONLINE-016 | ✅ | 5 | Implemented anti-cheat trust-boundary v1 on server action ingestion: movement sanity checks, action rate guardrails, action nonce replay protection, and security-event hook emission. |
| COI-ONLINE-017 | ✅ | 3 | Added Steam dual-distribution implementation plan document (`docs/STEAM_DUAL_DISTRIBUTION.md`) while keeping standalone launcher/update flow intact. |
| COI-ONLINE-018 | ✅ | 3 | Restored backend deploy CI workflow (`deploy-backend.yml`) with backend-only change filtering and Cloud Run deploy path separated from launcher/game release workflow. |
| COI-ONLINE-019 | ✅ | 3 | Authored initial hard character preset catalog in runtime gameplay config and then consolidated it to a single production preset (`sellsword`) with male/female selection handled through `appearance_key`. |
| COI-ONLINE-020 | ✅ | 3 | Wired curated preset selection UX in Godot character creation: preset dropdown, preset-to-fields/stat/skill/budget application, preview sync, and `preset_key` posting to backend character create API. |
| COI-ONLINE-021 | ✅ | 4 | Implemented Sellsword V1 character art pipeline: generated 96x96 layered-ready male/female sprite sheets (8 directions; idle/walk/run/attack/cast/hurt/death/sit-crossed/sit-kneel), added runtime catalog metadata, and wired animated directional preview + world actor rendering. |
| COI-ONLINE-023 | ✅ | 4 | Account-hub UI regression recovery: replaced unstable split-container composition with fixed side-navigation + dedicated list/create view containers, restored centered non-world title behavior, and reinstated themed confirmation dialogs for character create/delete actions. |
| COI-ONLINE-024 | ✅ | 3 | Added dual preview for list/create flows: large podium preview plus inset world-scale mirror preview, with rotation/facing synchronization from primary preview drag/arrow controls. |
| COI-ONLINE-025 | ✅ | 4 | Upgraded Sellsword pipeline to 4x source fidelity (384 frame size), regenerated catalog/runtime sheets, and updated in-world actor rendering to downscale source frames to gameplay draw size for stable readability/performance. |

## Archived / Superseded
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-SPRPG-* | ✅ | 0 | Superseded by Children of Ikphelion online ARPG pivot; retained only as historical implementation record. |
| GOK-MMO-* | ✅ | 0 | Legacy MMO task stream is superseded and retained only for traceability. |
