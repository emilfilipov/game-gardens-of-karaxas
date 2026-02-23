# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-ONLINE-019 | ⬜ | 3 | Author final character preset catalog content (base appearance archetypes + personality/class-leaning starter skill/stat defaults) once design values are provided. |
| COI-ONLINE-020 | ⬜ | 3 | Wire curated preset selection UX in character creation once preset art/content payloads are finalized. |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
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

## Archived / Superseded
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-SPRPG-* | ✅ | 0 | Superseded by Children of Ikphelion online ARPG pivot; retained only as historical implementation record. |
| GOK-MMO-* | ✅ | 0 | Legacy MMO task stream is superseded and retained only for traceability. |
