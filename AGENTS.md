# Gardens of Karaxas - Agent Guide

## Canonical Docs (Read First)
- `GAME.md` - all game/product information and scope.
- `TECHNICAL.md` - all technical architecture and engineering decisions.

## Documentation Policy (Strict)
1. `GAME.md` is the single source of truth for game information.
2. `TECHNICAL.md` is the single source of truth for technical information.
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

## Supporting Docs
- `INSTALLER.md` - Windows installer/updater operation details.
- `README.md` - quick repo orientation.
- Release note templates:
  - `RELEASE_NOTES_TEMPLATE.md`
  - `.github/release-body-template.md`

## Architecture Guardrails
- Keep gameplay logic decoupled from launcher/updater code.
- Runtime must run without launcher/updater dependencies.
- Preserve portability path: Windows first, then Linux/Steam, then Android.

## System Map
- Current repo structure:
  - `launcher/` - Windows launcher/updater module (Gradle).
  - `assets/` - shared content/data.
  - `scripts/` and `.github/workflows/` - packaging/release automation.
  - `tools/` - setup wrapper and update helper tooling.
  - `build.gradle.kts`, `settings.gradle.kts`, `gradlew`, `gradle/` - Gradle build system scaffold.
- Planned modules (not scaffolded yet):
  - `sim/` - pure gameplay/simulation logic.
  - `game/` - gameplay orchestration and presentation.
  - `desktop/` - standalone runtime for Windows/Linux/Steam.
