# Security Runbook

## Active Security Scope
Single-player runtime security focuses on distribution integrity, update safety, and local data hygiene.

## Implemented Baseline
- Release uploads use GitHub OIDC + GCP Workload Identity Federation (no static cloud key files).
- GCS feed artifacts are distributed through controlled CI workflow.
- No runtime backend auth/session tokens are required for gameplay.
- No embedded GitHub PAT/repo credentials in client update flow.
- Local logs and config are stored in user-space paths.

## Primary Threat Areas
1. Malicious/tampered update artifacts.
2. Feed cache staleness causing incorrect update state.
3. Local save/config corruption.
4. Accidental secret leakage in CI/workflows.

## Controls
- Optional SHA256 verification for downloaded Godot runtime in release pipeline.
- `Cache-Control: no-cache, max-age=0` on mutable feed artifacts.
- Feed publishing gated by authenticated workflow run.
- Runtime validates presence of required config domains and surfaces errors in diagnostics.

## Secrets Handling
Active secrets/vars are limited to release pipeline cloud auth and feed targets:
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `KARAXAS_GCS_RELEASE_BUCKET`
- optional runtime bundle/feed vars

Deprecated backend auth/ops secrets are no longer used in active release flow.

## Incident Response
### Suspected compromised release
1. Stop new releases.
2. Move feed pointer back to last known-good archived version.
3. Rotate cloud IAM credentials/service account bindings if needed.
4. Publish fixed release with new version.

### Bad update metadata/cache behavior
1. Verify `Cache-Control` metadata on feed objects.
2. Re-upload `RELEASES` and setup artifacts.
3. Re-run update test from clean install + stale install machines.

### Local save/config corruption reports
1. Reproduce with affected save files.
2. Inspect diagnostics log output.
3. Recover from slot backups (when available) or provide migration repair script.

## Security Checklist Before Release
- Release workflow green.
- No secrets echoed in logs.
- Feed objects present and metadata correct.
- Client can update and launch without backend connectivity.
