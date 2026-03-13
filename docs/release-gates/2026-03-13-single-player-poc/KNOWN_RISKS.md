# Single-Player External PoC Known Risks (2026-03-13)

## Risk Ledger
- Risk: release workflow build time variance on Windows can delay publish windows.
  - Mitigation: keep release smoke deterministic and preflight auth checks early in pipeline.
  - Owner: Emil Filipov
- Risk: world-sync transport is polling baseline, not SSE/WebSocket streaming.
  - Mitigation: stale-data indicators and retry/backoff are active; monitor lag metrics.
  - Owner: Emil Filipov
- Risk: single-region deterministic tick runner is not yet horizontally sharded.
  - Mitigation: keep cohort small, enforce single-player scope, monitor tick lag thresholds.
  - Owner: Emil Filipov
- Risk: release artifacts are Windows-first only.
  - Mitigation: external testers limited to Windows builds for this PoC phase.
  - Owner: Emil Filipov
