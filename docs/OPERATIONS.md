# Operations Runbook (Transitional)

## Scope
Operational runbook for Ambitions of Peace during migration from legacy prototype modules to Rust-first runtime/services.

## Active CI/CD Workflows
- Release packaging workflow: `.github/workflows/release.yml`
- Backend deploy workflow: `.github/workflows/deploy-backend.yml`
- Security scan workflow: `.github/workflows/security-scan.yml`

## Standard Change-Set Flow
1. Implement focused change set and required documentation updates.
2. Run relevant local checks for changed surfaces.
3. Commit and push.
4. If push includes workflow-triggering paths, monitor GitHub Actions to completion.
5. If push is docs-only and does not match workflow triggers, skip polling and report that condition.

## Release Operations (Current)
1. Confirm patch notes contain only current-cycle changes.
2. Run release prechecks used by workflow gates.
3. Push workflow-triggering changes.
4. Verify generated artifacts in `releases/windows/` and GCS feed/archive paths.
5. Confirm retention policy keeps latest 3 feed/archive build versions.

## Failure Handling
### CI failure
1. Identify failing workflow/job.
2. Collect failing logs (`gh run view <run-id> --log-failed`).
3. Implement focused fix.
4. Push and repeat poll/fix cycle.

### Release integrity failure
1. Pause new release pushes.
2. Restore last known-good feed artifacts from archive path.
3. Validate updater behavior from installed client.
4. Publish corrective release notes and replacement build.

## Logging Surfaces
- launcher logs: `<install_root>/logs/launcher.log`
- runtime logs: `<install_root>/logs/game.log`
- updater logs: `<install_root>/logs/velopack.log`
- updater status: `<install_root>/logs/update_status.json`
