# Ambitions of Peace - Agent Guide

## Canonical Docs (Read First)
- `docs/GAME.md` - all game/product information and scope.
- `docs/TECHNICAL.md` - all technical architecture and engineering decisions.

## Documentation Policy (Strict)
1. `docs/GAME.md` is the single source of truth for game information.
2. `docs/TECHNICAL.md` is the single source of truth for technical information.
3. No implementation change is complete until the relevant canonical doc is updated in the same change.
4. Keep documentation constantly up to date; never defer doc updates to a later task.

## Development Cycle (Mandatory)
1. Make a focused change set (code + required doc updates).
2. Run relevant tests/checks before finalizing the change.
3. Commit after each completed change set.
4. Push commits automatically after each completed change set; do not ask for push confirmation.
5. If the push includes workflow-triggering paths, poll the latest GitHub Actions run every 2-3 minutes until it finishes.
6. If the push is docs-only (for example markdown-only changes under `docs/`), do not poll; report that no workflow-triggering changes were included.
7. If a polled run fails, fetch failing logs, implement a fix, push again, and continue the poll/fix cycle.
8. If a polled run succeeds, report success and wait for next instructions.

## UI Concept Iteration Cycle (Mandatory)
For UI concept generation work, each pass must be executed strictly one at a time using this exact loop:
1. Plan one pass (specific layout/art/composition goals).
2. Generate/draw assets and compose that single pass.
3. Review that single pass visually.
4. Record concrete issues and plan improvements.
5. Implement improvements in tooling/assets.
6. Only then generate the next pass.

Explicitly forbidden for UI concept iteration work:
- Batch-generating many passes first and reviewing later.
- Reusing the same composition with only trivial deltas and calling it a new pass.

## Patch Notes Policy
- Patch notes must include only improvements/fixes from the current development cycle.
- Do not carry forward, re-list, or append items from older cycles/commits.

## GitHub Actions Access
- GitHub PAT for Actions API access is stored at `/home/emillfilipov/.secrets/github_pat.env` as `GITHUB_PAT`.
- Never print or log the token value.

## Validated Command Cookbook
- Repository inspection:
  - `git status --short`
  - `git diff --stat`
  - `git diff -- <path>`
  - `sed -n '1,220p' <path>`
  - `grep -n "<pattern>" <path>`
- Backend checks:
  - `python3 -m compileall backend/app`
- Auth/session continuity gate:
  - `backend/scripts/validate_auth_session_gate.sh`
- Rust checks:
  - `~/.cargo/bin/cargo fmt --all -- --check`
  - `~/.cargo/bin/cargo clippy --workspace --all-targets -- -D warnings`
  - `~/.cargo/bin/cargo test --workspace`
- Designer world-promotion tests:
  - `PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_designer_world_promotion.py backend/tests/test_designer_publish_routes.py`
- Commit/push flow:
  - `git add <paths>`
  - `git commit -m "<message>"`
  - `git push`
- GitHub Actions polling (2-3 minute cadence, use `gh` by default):
  - `gh run list --limit 20 --json databaseId,workflowName,headSha,status,conclusion,displayTitle,createdAt`
  - `gh run view <run-id> --json status,conclusion,jobs,url`
  - `gh run view <run-id> --log-failed` (when a run fails and logs are needed)
  - `sleep 125 && ...` (repeat until `status=completed` for relevant workflows)
  - Skip polling when the pushed change set is docs-only and does not match workflow path triggers.

## Supporting Docs
- `docs/INSTALLER.md` - Windows installer/updater operation details.
- `docs/TASKS.md` - detailed development task tracking (active backlog + finished tasks).
- `docs/README.md` - quick repo orientation.
- Release note templates:
  - `docs/RELEASE_NOTES_TEMPLATE.md`
  - `.github/release-body-template.md`

## Architecture Guardrails
- Keep gameplay logic decoupled from install/update helper scripts.
- Runtime must run without external launcher dependencies.
- Preserve portability path: Windows first, then Linux/Steam, then Android.

## UI Quality Rule
- All UI dialogs, panels, and controls must be themed to Ambitions of Peace.
- Do not ship placeholder/system-default UI surfaces for in-game shell flows.

## System Map
- Current repo structure:
  - `docs/` - repository documentation (canonical + supporting docs).
  - `backend/` - FastAPI control plane and Cloud SQL-backed services.
  - `world-service/` - Rust world authority service.
  - `sim-core/` - shared simulation contracts/rules.
  - `client-app/` - Rust Bevy game runtime shell and tools mode.
  - `designer-client/` - standalone designer authoring/promotion client.
  - `tooling-core/` - deterministic content tooling pipelines.
  - `assets/` - shared content/data.
  - `scripts/` and `.github/workflows/` - packaging/release automation.
  - `tools/` - packaging/utilities.
- Planned modules (not scaffolded yet):
  - `battle-client/` - dedicated tactical battle runtime surface (post-vertical-slice hardening).
