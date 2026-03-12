# ADR-0003: Phased FastAPI to Rust Authority Migration

- Status: accepted
- Date: 2026-03-12
- Deciders: project owner + implementation agent
- Related tasks: `AOP-PIVOT-003`, `AOP-PIVOT-006`, `AOP-PIVOT-007`, `AOP-PIVOT-026`

## Context
Existing operational APIs (auth/session/content/release) are implemented in FastAPI and already integrated with deployment workflows. A full stop-and-replace migration would increase risk and block forward progress.

## Decision
Migrate in phases:
1. Keep FastAPI as transitional control plane for auth/session/content/release.
2. Introduce Rust world-authority service for simulation and gameplay authority.
3. Bridge control-plane world bootstrap/handoff to Rust service.
4. Retire or narrow FastAPI responsibilities only after Rust services are production-viable for equivalent flows.

## Consequences
- Positive:
  - Lower migration risk and better continuity for live operational paths.
  - Incremental validation and rollback options at each boundary.
- Tradeoffs:
  - Temporary dual-stack complexity.
  - Additional inter-service auth and contract testing requirements.

## Notes
Cutover decisions must be milestone-based and backed by regression and compatibility tests.
