# tests/api/core/test_phase_10_multi_region_aggregator.py —
# Phase 10 T7 (cj-style 103번째 wire) — Multi-region SLO aggregation
# + tenant-scoped SLO override tests. 6 cases.
#
# Verbatim PRD §F26.4 + Phase 5 wire 정합 (DEFAULT_REGION_WEIGHT_MAP
# seoul=0.6 tokyo=0.3 singapore=0.1 + REPLICATION_LAG_THRESHOLD_MB=100.0).
import pytest

from apps.api.modules.slo.multi_region_aggregator import (
    DEFAULT_REGION_WEIGHT_MAP,
    REPLICATION_LAG_MULTIPLIER,
    REPLICATION_LAG_THRESHOLD_MB,
    aggregate_multi_region,
    build_tenant_override,
    override_is_active,
)


def _sample_region_payload():
    return {
        "seoul": {
            "burn_rate": 0.5,
            "latency_p99_ms": 250.0,
            "replication_lag_mb": 5.0,
        },
        "tokyo": {
            "burn_rate": 0.3,
            "latency_p99_ms": 200.0,
            "replication_lag_mb": 8.0,
        },
        "singapore": {
            "burn_rate": 0.1,
            "latency_p99_ms": 180.0,
            "replication_lag_mb": 3.0,
        },
    }


def test_default_region_weight_map_phase_5_parity():
    assert DEFAULT_REGION_WEIGHT_MAP["seoul"] == pytest.approx(0.6)
    assert DEFAULT_REGION_WEIGHT_MAP["tokyo"] == pytest.approx(0.3)
    assert DEFAULT_REGION_WEIGHT_MAP["singapore"] == pytest.approx(0.1)


def test_replication_lag_threshold_constant():
    assert REPLICATION_LAG_THRESHOLD_MB == 100.0
    assert REPLICATION_LAG_MULTIPLIER == pytest.approx(1.2)


def test_aggregate_weighted_avg_burn_rate():
    payload = _sample_region_payload()
    result = aggregate_multi_region(payload, method="weighted_avg")
    expected = (
        0.5 * 0.6 + 0.3 * 0.3 + 0.1 * 0.1
    )
    assert result["aggregated_burn_rate"] == pytest.approx(expected)


def test_aggregate_any_failure_method_returns_max_burn_rate():
    payload = _sample_region_payload()
    result = aggregate_multi_region(payload, method="any_failure")
    assert result["aggregated_burn_rate"] == pytest.approx(0.5)


def test_aggregate_min_method_returns_min_burn_rate():
    payload = _sample_region_payload()
    result = aggregate_multi_region(payload, method="min")
    assert result["aggregated_burn_rate"] == pytest.approx(0.1)


def test_tenant_override_active_within_window():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    override = build_tenant_override(
        override_id="override:1",
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        objective_override=99.5,
        window_override="1h",
        effective_from=(now - timedelta(hours=1)).isoformat(),
        expires_at=(now + timedelta(hours=1)).isoformat(),
    )
    assert override_is_active(override, now=now) is True


def test_tenant_override_inactive_after_expiry():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    override = build_tenant_override(
        override_id="override:2",
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        objective_override=99.5,
        window_override="1h",
        effective_from=(now - timedelta(hours=2)).isoformat(),
        expires_at=(now - timedelta(hours=1)).isoformat(),
    )
    assert override_is_active(override, now=now) is False
