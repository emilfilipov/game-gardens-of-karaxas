# Single-Player External PoC Rollback Proof (2026-03-13)

## Rollback Trigger Thresholds
- Immediate rollback if auth/session continuity gate fails.
- Immediate rollback if installer acceptance smoke fails for game or designer channel.
- Immediate rollback if battle writeback regression appears in vertical-slice tests.
- Immediate rollback if runtime health check reports page-worthy lag/latency breach during rollout.

## Rollback Procedure Evidence
1. Use GCS archive rollback source (`archive/game/<version>` and `archive/designer/<version>`).
2. Re-point channel `latest.json` to last known-good version.
3. Run installer acceptance smoke against corrected feed.
4. Re-run auth/session + vertical-slice gates.
5. Announce rollback and freeze new release publish until root cause is fixed.

## Proof Artifacts
- Archive retention + rollback policy: `.github/workflows/release.yml`
- Rollback helper script (release policy): `backend/scripts/rollback_release_policy.sh`
- Operations release failure handling runbook: `docs/OPERATIONS.md`
