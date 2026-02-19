from app.services.observability import (
    record_transition_fallback,
    record_transition_handoff,
    record_zone_broadcast,
    record_zone_preload_latency_ms,
    record_zone_scope_update,
    reset_runtime_metrics_for_tests,
    zone_runtime_stats,
)


def test_zone_runtime_stats_aggregate_preload_transition_and_scope_counters() -> None:
    reset_runtime_metrics_for_tests()

    record_zone_preload_latency_ms(12.5, success=True)
    record_zone_preload_latency_ms(8.0, success=True)
    record_zone_preload_latency_ms(44.5, success=False)
    record_transition_handoff(success=True)
    record_transition_handoff(success=False)
    record_transition_fallback()
    record_zone_scope_update()
    record_zone_scope_update()
    record_zone_broadcast(3)
    record_zone_broadcast(2)

    stats = zone_runtime_stats()
    assert stats["preload_latency_ms"]["success"]["count"] == 2.0
    assert stats["preload_latency_ms"]["failed"]["count"] == 1.0
    assert stats["transition_handoff"]["success_total"] == 1
    assert stats["transition_handoff"]["failed_total"] == 1
    assert stats["transition_handoff"]["fallback_total"] == 1
    assert stats["zone_scope_updates_total"] == 2
    assert stats["zone_broadcast"]["events_total"] == 2
    assert stats["zone_broadcast"]["recipients_total"] == 5
