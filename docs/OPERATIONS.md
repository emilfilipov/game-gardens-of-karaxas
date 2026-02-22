# Operations Runbook

## Active Operations Scope
The active production surface is release packaging + GCS update distribution for the single-player client.

## Release Runbook
1. Update `docs/patch_notes.md` for the current development cycle.
2. Push to `main`/`master` (non-markdown change).
3. Confirm `.github/workflows/release.yml` starts.
4. Verify workflow stages:
   - preflight inputs
   - cloud auth (WIF)
   - launcher tests + UI regression
   - packaging
   - GCS upload
5. Confirm feed artifacts exist in GCS (`RELEASES`, `.nupkg`, setup exe).
6. Confirm mutable feed objects have `Cache-Control: no-cache, max-age=0`.
7. Validate client update from an installed build.

## Rollback Runbook
1. Identify previous stable version in `gs://<bucket>/archive/<version>/`.
2. Copy archived artifacts back to feed prefix (`win/`) to revert active feed.
3. Re-run client update test from a machine with the affected build.
4. Publish corrective patch notes and new release if full rollback is not sufficient.

## Diagnostics
- Launcher log: `<install_root>/logs/launcher.log`
- Game log: `<install_root>/logs/game.log`
- Updater log: `<install_root>/logs/velopack.log`
- In-client diagnostics panel displays local log tail and key paths.

## CI/CD Notes
- Only release workflow is active for production path.
- Backend deploy/security workflows are removed from active pipeline in single-player mode.

## Checklist Before Shipping
- `./gradlew :launcher:test` passes.
- `python3 game-client/tests/check_ui_regression.py` passes.
- Main menu actions all work locally.
- Save/load flow verified.
- Update action verified on installed build.
