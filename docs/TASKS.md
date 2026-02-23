# TASKS

Status legend: `⬜` not started, `⏳` in progress/blocked, `✅` done.

## Task Backlog
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-ONLINE-002 | ⬜ | 4 | Replace remaining single-player save-driven entry assumptions in Godot shell with account/session-driven flow, including robust token refresh and 401 recovery handling in all authenticated requests. |
| COI-ONLINE-003 | ⬜ | 4 | Implement backend-authoritative character/session bootstrap contract for world entry: selected character + level/floor + coordinates + gameplay config hash + release/version policy snapshot. |
| COI-ONLINE-004 | ⬜ | 5 | Add party service v1 (invite/accept/leave/kick/promote owner) and wire party-aware instance routing so solo creates private instance while party shares one world instance. |
| COI-ONLINE-005 | ⬜ | 5 | Implement town/hub presence service: scoped player visibility in hub zones only, with websocket zone presence updates and deduplicated join/leave tracking. |
| COI-ONLINE-006 | ⬜ | 4 | Add instance lifecycle manager on backend (create/assign/expire) with deterministic instance IDs and reconnect-safe player restoration. |
| COI-ONLINE-007 | ⬜ | 4 | Move combat/progression authority checks server-side for critical actions (damage application, xp rewards, loot grants) and keep client-side prediction strictly cosmetic. |
| COI-ONLINE-008 | ⬜ | 3 | Complete runtime gameplay config service hardening: schema validation, versioning, signature pinning, staged publish and rollback for backend file-based config. |
| COI-ONLINE-009 | ⬜ | 3 | Wire client cache for backend gameplay config with signature/version verification and safe fallback behavior when backend is unavailable. |
| COI-ONLINE-010 | ⬜ | 3 | Extend backend CI/CD restoration with dedicated security scan workflow and deployment post-check smoke tests (deploy workflow baseline is already active). |
| COI-ONLINE-011 | ⬜ | 3 | Complete naming migration from Karaxas/GOK to Children of Ikphelion across remaining internal identifiers and automation scripts while preserving compatibility aliases for existing installs. |
| COI-ONLINE-012 | ⬜ | 4 | Reconcile admin tooling boundaries for online mode: keep level/asset/content tools admin-only and define publish path impact on live sessions with grace + forced logout policy. |
| COI-ONLINE-013 | ⬜ | 3 | Expand observability for online runtime: structured logs for auth/session/instance events, metrics for login success/failure, ws disconnect reasons, and instance occupancy. |
| COI-ONLINE-014 | ⬜ | 4 | Implement end-to-end smoke harness for online loop: register/login/MFA on/off, character create/select/play, world enter/exit, and location persistence assertions. |
| COI-ONLINE-015 | ⬜ | 4 | Rework updater UX copy and release messaging for online operations: show both build version and gameplay config version, and explain forced-update/logout reasons in player-friendly language. |
| COI-ONLINE-016 | ⬜ | 5 | Add anti-cheat trust boundaries v1: server-side movement sanity checks, action rate validation, replay/reuse protection for critical action payloads, and ban/suspicion event hooks. |
| COI-ONLINE-017 | ⬜ | 3 | Prepare Steam-compatible dual-distribution plan while retaining standalone launcher flow: package naming, branch/version mapping, and update-policy split by channel. |

## Completed Tasks
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| COI-ONLINE-001 | ✅ | 3 | Pivot baseline established: renamed project/product surfaces to Children of Ikphelion (user-facing), reactivated Godot online shell entry (`client_shell.gd`), preserved isometric world runtime, and introduced backend file-based runtime gameplay config endpoint (`/content/runtime-config`) with client-side fallback to `/content/bootstrap`. |
| COI-ONLINE-018 | ✅ | 3 | Restored backend deploy CI workflow (`deploy-backend.yml`) with backend-only change filtering and Cloud Run deploy path separated from launcher/game release workflow. |

## Archived / Superseded
| Task ID | Status | Complexity | Detailed Description |
| --- | --- | --- | --- |
| GOK-SPRPG-* | ✅ | 0 | Superseded by Children of Ikphelion online ARPG pivot; retained only as historical implementation record. |
| GOK-MMO-* | ✅ | 0 | Legacy MMO task stream is superseded and retained only for traceability. |
