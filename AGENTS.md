# Gardens of Karaxas - Agent Guide

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
5. After each push, poll the latest GitHub Actions run every 2-3 minutes until it finishes.
6. If the run fails, fetch failing logs, implement a fix, push again, and continue the poll/fix cycle.
7. If the run succeeds, report success and wait for next instructions.

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
- Launcher checks:
  - `./gradlew :launcher:test`
- Local environment constraint:
  - Do not run `dotnet` build/publish commands locally in this repo (this workstation is Linux-first for launcher/backend work and does not have a local `dotnet` toolchain installed).
- Commit/push flow:
  - `git add <paths>`
  - `git commit -m "<message>"`
  - `git push`
- GitHub Actions polling (2-3 minute cadence, use `gh` by default):
  - `gh run list --limit 20 --json databaseId,workflowName,headSha,status,conclusion,displayTitle,createdAt`
  - `gh run view <run-id> --json status,conclusion,jobs,url`
  - `gh run view <run-id> --log-failed` (when a run fails and logs are needed)
  - `sleep 125 && ...` (repeat until `status=completed` for relevant workflows)

## Supporting Docs
- `docs/INSTALLER.md` - Windows installer/updater operation details.
- `docs/TASKS.md` - detailed development task tracking (active backlog + finished tasks).
- `docs/README.md` - quick repo orientation.
- Release note templates:
  - `docs/RELEASE_NOTES_TEMPLATE.md`
  - `.github/release-body-template.md`

## Architecture Guardrails
- Keep gameplay logic decoupled from launcher/updater code.
- Runtime must run without launcher/updater dependencies.
- Preserve portability path: Windows first, then Linux/Steam, then Android.

## UI Quality Rule
- All UI dialogs, panels, and controls must be themed to Gardens of Karaxas.
- Do not ship placeholder/system-default UI surfaces for in-game launcher flows.

## System Map
- Current repo structure:
  - `docs/` - repository documentation (canonical + supporting docs).
  - `launcher/` - Windows launcher/updater module (Gradle).
  - `game-client/` - Godot 4.x runtime/editor host scaffold and bootstrap contract.
  - `assets/` - shared content/data.
  - `scripts/` and `.github/workflows/` - packaging/release automation.
  - `tools/` - setup wrapper and update helper tooling.
  - `build.gradle.kts`, `settings.gradle.kts`, `gradlew`, `gradle/` - Gradle build system scaffold.
- Planned modules (not scaffolded yet):
  - `sim/` - pure gameplay/simulation logic.
  - `game/` - gameplay orchestration and presentation (engine-agnostic domain layer target).
  - `desktop/` - standalone runtime shell for Windows/Linux/Steam (beyond launcher shell flow).
