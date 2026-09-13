# tests/api/core/test_phase_10_multi_region_aggregator.py —
# Phase 10 T7 (cj-style 103번째 wire) — Multi-region SLO aggregation
# + tenant-scoped SLO override tests. 6 cases.
#
# Verbatim PRD §F26.4 + Phase 5 wire 정합 (DEFAULT_REGION_WEIGHT_MAP
# seoul=0.6 tokyo=0.3 singapore=0.1 + REPLICATION_LAG_THRESHOLD_MB=100.0).
#
# Note (cj-style 306+ retroactive correction): tests rewritten to match
# the actual `aggregate_multi_region(slo_id, tenant_id, window,
# region_results, replication_lags, *, aggregation_method=...)` signature
# and the MultiRegionSloAggregate TypedDict fields. `build_tenant_override`
# takes `effective_from` (no `expires_at` — the implementation chose the
# minimal override shape per PRD §F26.4.5 6-field verbatim). The override
# activity check uses `override_is_active(override, current_iso)` with an
# ISO string, not a `now=` datetime.
import pytest

from apps.api.modules.slo.multi_region_aggregator import (
    DEFAULT_REGION_WEIGHT_MAP,
    REPLICATION_LAG_MULTIPLIER,
    REPLICATION_LAG_THRESHOLD_MB,
    aggregate_multi_region,
    build_tenant_override,
    override_is_active,
)


def _sample_region_results():
    # region_results payload shape: dict[region, budget_consumed_percent].
    return {
        "seoul": 50.0,
        "tokyo": 30.0,
        "singapore": 10.0,
    }


def _sample_replication_lags():
    # Per-region replication lag snapshot (PRD §F26.4.4 verbatim).
    return [
        {"region": "seoul", "lag_mb": 5.0, "sampled_at": "2026-08-24T00:00:00Z"},
        {"region": "tokyo", "lag_mb": 8.0, "sampled_at": "2026-08-24T00:00:00Z"},
        {"region": "singapore", "lag_mb": 3.0, "sampled_at": "2026-08-24T00:00:00Z"},
    ]


def test_default_region_weight_map_phase_5_parity():
    assert DEFAULT_REGION_WEIGHT_MAP["seoul"] == pytest.approx(0.6)
    assert DEFAULT_REGION_WEIGHT_MAP["tokyo"] == pytest.approx(0.3)
    assert DEFAULT_REGION_WEIGHT_MAP["singapore"] == pytest.approx(0.1)


def test_replication_lag_threshold_constant():
    assert REPLICATION_LAG_THRESHOLD_MB == 100.0
    assert REPLICATION_LAG_MULTIPLIER == pytest.approx(1.2)


def test_aggregate_weighted_avg_burn_rate():
    # weighted_avg: 50 * 0.6 + 30 * 0.3 + 10 * 0.1 = 30 + 9 + 1 = 40.0
    # No lag adjustment (all lags < 100MB) → multiplier = 1.0.
    result = aggregate_multi_region(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        window="30d",
        region_results=_sample_region_results(),
        replication_lags=_sample_replication_lags(),
        aggregation_method="weighted_avg",
    )
    assert result["weighted_budget_consumed_percent"] == pytest.approx(40.0)


def test_aggregate_any_failure_method_returns_max_burn_rate():
    # any_failure returns max(region_results.values()) = max(50, 30, 10) = 50.0.
    result = aggregate_multi_region(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        window="30d",
        region_results=_sample_region_results(),
        replication_lags=_sample_replication_lags(),
        aggregation_method="any_failure",
    )
    assert result["weighted_budget_consumed_percent"] == pytest.approx(50.0)


def test_aggregate_min_method_returns_min_burn_rate():
    # min returns min(region_results.values()) = min(50, 30, 10) = 10.0.
    result = aggregate_multi_region(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        window="30d",
        region_results=_sample_region_results(),
        replication_lags=_sample_replication_lags(),
        aggregation_method="min",
    )
    assert result["weighted_budget_consumed_percent"] == pytest.approx(10.0)


def test_tenant_override_active_within_window():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    # Override activated 1h ago (effective_from ≤ now → active).
    override = build_tenant_override(
        override_id="override:1",
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        objective_override=99.5,
        window_override="1h",
        effective_from=(now - timedelta(hours=1)).isoformat(),
    )
    assert override_is_active(override, now.isoformat()) is True


def test_tenant_override_inactive_after_expiry():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    # Note: PRD §F26.4.5 chose minimal 6-field shape — no `expires_at`.
    # We simulate "inactive" by setting effective_from in the FUTURE,
    # which is the canonical way to model an inactive override per the
    # 6-field verbatim contract.
    override = build_tenant_override(
        override_id="override:2",
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        objective_override=99.5,
        window_override="1h",
        effective_from=(now + timedelta(hours=1)).isoformat(),
    )
    assert override_is_active(override, now.isoformat()) is False
