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
    zone_preload_success_samples_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    zone_preload_failed_samples_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    transition_handoff_success_total: int = 0
    transition_handoff_failed_total: int = 0
    transition_fallback_total: int = 0
    zone_scope_updates_total: int = 0
    zone_broadcast_events_total: int = 0
    zone_broadcast_recipients_total: int = 0
    auth_login_success_total: int = 0
    auth_login_failure_total: int = 0
    world_sync_success_total: int = 0
    world_sync_failure_total: int = 0
    world_sync_samples_ms: deque[float] = field(default_factory=lambda: deque(maxlen=512))
    ws_disconnect_reason_counts: dict[str, int] = field(default_factory=dict)
    instance_assignments_by_kind: dict[str, int] = field(default_factory=dict)
    instance_restores_total: int = 0


_state = _MetricsState()
_lock = RLock()


def record_forced_logout_event() -> None:
    with _lock:
        _state.forced_logout_events += 1


def record_snapshot_load_latency_ms(duration_ms: float) -> None:
    with _lock:
        _state.snapshot_load_samples_ms.append(max(0.0, float(duration_ms)))


def record_zone_preload_latency_ms(duration_ms: float, *, success: bool) -> None:
    sample = max(0.0, float(duration_ms))
    with _lock:
        if success:
            _state.zone_preload_success_samples_ms.append(sample)
        else:
            _state.zone_preload_failed_samples_ms.append(sample)


def record_transition_handoff(*, success: bool) -> None:
    with _lock:
        if success:
            _state.transition_handoff_success_total += 1
        else:
            _state.transition_handoff_failed_total += 1


def record_transition_fallback() -> None:
    with _lock:
        _state.transition_fallback_total += 1


def record_zone_scope_update() -> None:
    with _lock:
        _state.zone_scope_updates_total += 1


def record_zone_broadcast(recipients: int) -> None:
    with _lock:
        _state.zone_broadcast_events_total += 1
        _state.zone_broadcast_recipients_total += max(0, int(recipients))


def record_auth_login_result(success: bool) -> None:
    with _lock:
        if success:
            _state.auth_login_success_total += 1
        else:
            _state.auth_login_failure_total += 1


def record_world_sync_result(*, success: bool, latency_ms: float | None = None) -> None:
    with _lock:
        if success:
            _state.world_sync_success_total += 1
            if latency_ms is not None:
                _state.world_sync_samples_ms.append(max(0.0, float(latency_ms)))
        else:
            _state.world_sync_failure_total += 1


def record_ws_disconnect(reason: str) -> None:
    normalized = (reason or "unknown").strip().lower() or "unknown"
    with _lock:
        _state.ws_disconnect_reason_counts[normalized] = int(_state.ws_disconnect_reason_counts.get(normalized, 0)) + 1


def record_instance_assignment(kind: str, restored: bool) -> None:
    normalized = (kind or "unknown").strip().lower() or "unknown"
    with _lock:
        _state.instance_assignments_by_kind[normalized] = int(_state.instance_assignments_by_kind.get(normalized, 0)) + 1
        if restored:
            _state.instance_restores_total += 1


def _sample_stats(samples: list[float]) -> dict[str, float]:
    if not samples:
        return {"count": 0.0, "avg_ms": 0.0, "p95_ms": 0.0}
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
    return {
        "count": float(len(samples)),
        "avg_ms": round(sum(samples) / len(samples), 3),
        "p95_ms": round(ordered[p95_index], 3),
    }


def snapshot_latency_stats() -> dict[str, float]:
    with _lock:
        samples = list(_state.snapshot_load_samples_ms)
    return _sample_stats(samples)


def zone_runtime_stats() -> dict[str, object]:
    with _lock:
        success_samples = list(_state.zone_preload_success_samples_ms)
        failed_samples = list(_state.zone_preload_failed_samples_ms)
        handoff_success = _state.transition_handoff_success_total
        handoff_failed = _state.transition_handoff_failed_total
        fallback_total = _state.transition_fallback_total
        scope_updates = _state.zone_scope_updates_total
        zone_broadcast_events = _state.zone_broadcast_events_total
        zone_broadcast_recipients = _state.zone_broadcast_recipients_total
        auth_success = _state.auth_login_success_total
        auth_failure = _state.auth_login_failure_total
        world_sync_success = _state.world_sync_success_total
        world_sync_failure = _state.world_sync_failure_total
        world_sync_samples = list(_state.world_sync_samples_ms)
        ws_disconnect_reason_counts = dict(_state.ws_disconnect_reason_counts)
        instance_assignments_by_kind = dict(_state.instance_assignments_by_kind)
        instance_restores_total = _state.instance_restores_total
    return {
        "preload_latency_ms": {
            "success": _sample_stats(success_samples),
            "failed": _sample_stats(failed_samples),
        },
        "transition_handoff": {
            "success_total": int(handoff_success),
            "failed_total": int(handoff_failed),
            "fallback_total": int(fallback_total),
        },
        "zone_scope_updates_total": int(scope_updates),
        "zone_broadcast": {
            "events_total": int(zone_broadcast_events),
            "recipients_total": int(zone_broadcast_recipients),
        },
        "auth_logins": {
            "success_total": int(auth_success),
            "failure_total": int(auth_failure),
        },
        "world_sync": {
            "success_total": int(world_sync_success),
            "failure_total": int(world_sync_failure),
            "latency_ms": _sample_stats(world_sync_samples),
        },
        "ws_disconnect_reasons": ws_disconnect_reason_counts,
        "instance_assignments_by_kind": instance_assignments_by_kind,
        "instance_restores_total": int(instance_restores_total),
    }


def reset_runtime_metrics_for_tests() -> None:
    with _lock:
        _state.snapshot_load_samples_ms.clear()
        _state.zone_preload_success_samples_ms.clear()
        _state.zone_preload_failed_samples_ms.clear()
        _state.transition_handoff_success_total = 0
        _state.transition_handoff_failed_total = 0
        _state.transition_fallback_total = 0
        _state.zone_scope_updates_total = 0
        _state.zone_broadcast_events_total = 0
        _state.zone_broadcast_recipients_total = 0
        _state.forced_logout_events = 0
        _state.auth_login_success_total = 0
        _state.auth_login_failure_total = 0
        _state.world_sync_success_total = 0
        _state.world_sync_failure_total = 0
        _state.world_sync_samples_ms.clear()
        _state.ws_disconnect_reason_counts.clear()
        _state.instance_assignments_by_kind.clear()
        _state.instance_restores_total = 0


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
