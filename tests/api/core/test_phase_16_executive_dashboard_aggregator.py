"""tests.api.core.test_phase_16_executive_dashboard_aggregator — Phase 16 executive dashboard tests.

Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.1 verbatim + AD-43 (a) decision). 5-module cross-join
aggregator: Phase 11 showback + Phase 12 anomaly + Phase 13 forecast +
Phase 14 optimization + Phase 15 tag_governance → single ExecutiveRollup.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from apps.api.core.errors import (
    ExecutiveRollupInvalidError,
    ExecutiveRollupScopeError,
    ExecutiveRollupPeriodError,
)
from apps.api.modules.finops.executive_dashboard_aggregator import (
    aggregate_executive_dashboard,
    compute_showback_total,
    compute_anomaly_count_30d,
    compute_forecast_projection,
    compute_optimization_savings,
    compute_tag_compliance_pct,
    compute_idle_cost_krw,
    validate_executive_rollup,
)


TENANT_ID = str(uuid.uuid4())


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_executive_rollup_16_fields_present() -> None:
    """Test 1: ExecutiveRollup TypedDict has all 16 fields (PRD §F32.1-2)."""
    rollup = aggregate_executive_dashboard(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    expected_fields = {
        "rollup_id",
        "tenant_id",
        "scope_type",
        "scope_id",
        "period_key",
        "showback_total_krw",
        "anomaly_count_30d",
        "forecast_projection_krw",
        "optimization_savings_krw",
        "tag_compliance_pct",
        "idle_cost_krw",
        "department_breakdown",
        "cost_center_breakdown",
        "resource_type_breakdown",
        "generated_at",
        "trace_id",
    }
    assert set(rollup.keys()) == expected_fields


def test_4_scope_type_options_validated() -> None:
    """Test 2: 4 scope_type options (tenant/department/cost_center/product_line)."""
    for scope_type in ("tenant", "department", "cost_center", "product_line"):
        rollup = aggregate_executive_dashboard(
            tenant_id=TENANT_ID,
            scope_type=scope_type,
            scope_id="scope-id",
            period_key="2026-08",
            dry_run=True,
        )
        assert rollup["scope_type"] == scope_type


def test_invalid_scope_type_raises_scope_error() -> None:
    """Test 3: invalid scope_type raises ExecutiveRollupScopeError."""
    import pytest
    with pytest.raises(ExecutiveRollupScopeError):
        aggregate_executive_dashboard(
            tenant_id=TENANT_ID,
            scope_type="invalid_scope",
            scope_id="default",
            period_key="2026-08",
            dry_run=True,
        )


def test_invalid_period_key_raises_period_error() -> None:
    """Test 4: invalid period_key raises ExecutiveRollupPeriodError."""
    import pytest
    with pytest.raises(ExecutiveRollupPeriodError):
        aggregate_executive_dashboard(
            tenant_id=TENANT_ID,
            scope_type="tenant",
            scope_id="default",
            period_key="invalid-period",
            dry_run=True,
        )


def test_empty_tenant_id_raises_invalid_error() -> None:
    """Test 5: empty tenant_id raises ExecutiveRollupInvalidError."""
    import pytest
    with pytest.raises(ExecutiveRollupInvalidError):
        aggregate_executive_dashboard(
            tenant_id="",
            scope_type="tenant",
            scope_id="default",
            period_key="2026-08",
            dry_run=True,
        )


def test_5_module_cross_join_in_dry_run_returns_zeros() -> None:
    """Test 6: 5-module cross-join returns zeros in dry-run (PRD §F32.1-4)."""
    rollup = aggregate_executive_dashboard(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    assert rollup["showback_total_krw"] == 0.0
    assert rollup["anomaly_count_30d"] == 0
    assert rollup["forecast_projection_krw"] == 0.0
    assert rollup["optimization_savings_krw"] == 0.0
    assert rollup["tag_compliance_pct"] == 0.0
    assert rollup["idle_cost_krw"] == 0.0


def test_compute_helpers_return_zero_in_dry_run() -> None:
    """Test 7: all 6 compute_* helpers return 0 in dry-run path."""
    assert compute_showback_total(TENANT_ID, "2026-08") == 0.0
    assert compute_anomaly_count_30d(TENANT_ID) == 0
    assert compute_forecast_projection(TENANT_ID, "2026-08") == 0.0
    assert compute_optimization_savings(TENANT_ID, "2026-08") == 0.0
    assert compute_tag_compliance_pct(TENANT_ID, "2026-08") == 0.0
    assert compute_idle_cost_krw(TENANT_ID, "2026-08") == 0.0


def test_validate_executive_rollup_pure_validator() -> None:
    """Test 8: validate_executive_rollup validates 16 fields (CR 11-4 P-015)."""
    rollup = aggregate_executive_dashboard(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    assert validate_executive_rollup(rollup) is True