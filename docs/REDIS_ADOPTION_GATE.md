# Redis Adoption Gate (PoC -> Scale)

## Purpose
Define a strict, metric-driven go/no-go gate for introducing Redis (GCP Memorystore) after the PostgreSQL outbox + LISTEN/NOTIFY baseline stops meeting operational targets.

Redis adoption is forbidden unless this gate is met.

## Current Baseline
- Durable source of truth: PostgreSQL `world_outbox`.
- Wake signaling: PostgreSQL `NOTIFY` from `world_outbox` insert trigger.
- Listener behavior: reconnecting LISTEN worker with replay-safe outbox claim semantics.

## Gate Metrics and Thresholds
All thresholds are evaluated on production-like traffic windows (minimum 24h) and must breach for at least 3 consecutive days before cutover is approved.

### 1) p95 authoritative write latency
- Metric: p95 latency for outbox/event write transactions (`world_events` + `world_outbox` commit path).
- Threshold: `> 45 ms` p95 for 3 consecutive daily windows.

### 2) fanout wake lag
- Metric: p95 delay from outbox `created_at` to first successful processor claim attempt (wake-to-claim lag).
- Threshold: `> 1200 ms` p95 for 3 consecutive daily windows.

### 3) queue backlog pressure
- Metric: count of unprocessed outbox rows (`processed_at IS NULL`) and sustained backlog growth.
- Threshold (either condition):
  - backlog `> 5000` rows for more than 15 minutes, or
  - positive growth slope `> 300 rows/min` for more than 10 minutes.

### 4) lock contention
- Metric: fraction of claim attempts that find rows already locked/retried due contention, plus lock wait pressure.
- Threshold (either condition):
  - contention ratio `> 8%` over 1h windows, or
  - p95 lock wait `> 150 ms` over 1h windows.

## Required Preconditions Before Redis Enablement
1. Metrics above are instrumented and retained for historical comparison.
2. A rollback drill was executed successfully in a staging environment.
3. Cost impact estimate is documented (Memorystore + added egress/ops overhead).
4. On-call/incident notes include Redis outage handling.

## Migration Plan (Dual-Path)
### Phase 0: PostgreSQL hardening first
1. Tune existing outbox worker batch sizes, retry delay, and polling cadence.
2. Validate index health and vacuum/autovacuum behavior.
3. Re-measure gate metrics for one full day before any Redis work.

### Phase 1: Introduce Redis as secondary fanout only
1. Provision Memorystore Redis with smallest viable tier.
2. Keep PostgreSQL outbox as authoritative queue.
3. Add optional Redis publisher in outbox processor (feature-flagged):
   - primary path remains PostgreSQL outbox processing,
   - secondary path publishes equivalent event envelope to Redis channel/stream.

### Phase 2: Dual-write validation window
1. Enable dual-write in staging, then production canary.
2. Compare PostgreSQL-derived and Redis-derived fanout counts and lag distributions.
3. Require `>= 99.9%` payload parity and no durable event loss before progressing.

### Phase 3: Consumer cutover
1. Switch non-authoritative hot fanout consumers to Redis.
2. Keep PostgreSQL outbox processing active for durability and replay.
3. Retain dual-write for at least 7 days after cutover.

## Rollback Plan
1. Disable Redis consumer path via feature flag.
2. Disable Redis secondary publish path.
3. Continue processing from PostgreSQL outbox only.
4. Reconcile any in-flight mismatch by replaying outbox rows from last safe cursor.
5. Record incident summary and update gate thresholds if needed.

## Non-Negotiable Rules
- Redis is never the durable source of truth for authoritative gameplay events.
- PostgreSQL outbox replay must remain available even after Redis cutover.
- No permanent Redis dependency is accepted without passing this gate and rollback drill.
