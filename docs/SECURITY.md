# Security Runbook (Transitional)

## Scope
Security baseline for Ambitions of Peace during migration phase.

## Current Priorities
- Protect release supply chain and artifact integrity.
- Protect backend auth/session surfaces while legacy and new services coexist.
- Prevent credential leakage in CI/CD and local operations.

## Baseline Controls
- GitHub Actions uses OIDC + GCP Workload Identity Federation for cloud auth.
- Release artifacts are published through controlled workflow paths.
- Mutable feed artifacts use no-cache metadata.
- Backend auth/session endpoints enforce token and session controls.
- Canonical docs and ADRs are required for architecture-impacting changes.

## Secrets Handling
- Never print or log secret values.
- Use configured secrets/vars in CI only.
- Keep local `.env` files out of source control.

## Incident Response
### Suspected artifact compromise
1. Halt release pushes.
2. Roll feed back to last known-good archive version.
3. Rotate relevant IAM/service credentials.
4. Publish corrected release.

### Suspected backend auth/security regression
1. Identify impacted endpoints and disable risky rollout if needed.
2. Review logs and reproduce issue.
3. Patch with focused fix and regression tests.
4. Deploy and monitor.

### Secret exposure
1. Revoke and rotate exposed credentials immediately.
2. Remove leaked material from history/log surfaces where possible.
3. Document impact and remediation.

## Verification Checklist
- Required checks pass for changed modules.
- No sensitive data in commit diff or CI logs.
- Release/update path tested after release-affecting changes.
