# ADR-0004: Redis Deferral and Adoption Gate

- Status: accepted
- Date: 2026-03-12
- Deciders: project owner + implementation agent
- Related tasks: `AOP-PIVOT-003`, `AOP-PIVOT-018`, `AOP-PIVOT-019`, `AOP-PIVOT-030`

## Context
The project is in single-developer PoC mode with strict cost control. Managed Redis introduces a recurring baseline cost that may be unnecessary before scale pressure appears.

## Decision
Defer Redis in early PoC phases. Use PostgreSQL outbox + LISTEN/NOTIFY for low-volume eventing and wakeup signaling. Introduce Redis only when objective adoption thresholds are exceeded.

## Adoption Gate (must be met before enabling Redis)
- Sustained event fanout lag exceeds target under representative load.
- Database contention from event signaling is measurable and persistent.
- Cache/TTL-heavy workloads cannot meet latency targets using current approach.
- Migration plan includes rollback and dual-path validation.

## Consequences
- Positive:
  - Lower recurring cost during early development.
  - Fewer infrastructure components in initial operations.
- Tradeoffs:
  - Some eventing patterns may be less efficient at higher load.
  - Redis migration work is deferred, not removed.

## Notes
Redis deferral applies to PoC phase only and must be revisited at defined observability checkpoints.
