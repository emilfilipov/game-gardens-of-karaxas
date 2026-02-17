from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import RLock

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.publish_drain import PublishDrainEvent


@dataclass
class _MetricsState:
    forced_logout_events: int = 0
    snapshot_load_samples_ms: deque[float] = field(default_factory=lambda: deque(maxlen=256))


_state = _MetricsState()
_lock = RLock()


def record_forced_logout_event() -> None:
    with _lock:
        _state.forced_logout_events += 1


def record_snapshot_load_latency_ms(duration_ms: float) -> None:
    with _lock:
        _state.snapshot_load_samples_ms.append(max(0.0, float(duration_ms)))


def snapshot_latency_stats() -> dict[str, float]:
    with _lock:
        samples = list(_state.snapshot_load_samples_ms)
    if not samples:
        return {"count": 0.0, "avg_ms": 0.0, "p95_ms": 0.0}
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
    return {
        "count": float(len(samples)),
        "avg_ms": round(sum(samples) / len(samples), 3),
        "p95_ms": round(ordered[p95_index], 3),
    }


def build_publish_drain_metrics(db: Session) -> dict[str, int]:
    active = db.execute(
        select(func.count(PublishDrainEvent.id)).where(PublishDrainEvent.status == "draining")
    ).scalar_one()
    total = db.execute(select(func.count(PublishDrainEvent.id))).scalar_one()
    persist_failed = db.execute(select(func.coalesce(func.sum(PublishDrainEvent.sessions_persist_failed), 0))).scalar_one()
    revoked = db.execute(select(func.coalesce(func.sum(PublishDrainEvent.sessions_revoked), 0))).scalar_one()
    with _lock:
        forced_logout_events = _state.forced_logout_events
    return {
        "drain_events_total": int(total or 0),
        "drain_events_active": int(active or 0),
        "drain_persist_failed_total": int(persist_failed or 0),
        "drain_sessions_revoked_total": int(revoked or 0),
        "forced_logout_events_total": int(forced_logout_events),
    }
