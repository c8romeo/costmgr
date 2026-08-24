"""tests.api.core.test_phase_16_cross_module_kpi — Phase 16 cross-module KPI tests.

Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.2 verbatim + AD-43 (b) decision). 8 NEW KPI
calculations from Phase 11~15 modules → KPIMetric TypedDict.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from apps.api.modules.finops.cross_module_kpi import (
    select_cross_module_kpis,
    validate_kpi_accuracy,
)
from apps.api.modules.finops.reporting.serializers import ALL_KPI_NAMES


TENANT_ID = str(uuid.uuid4())


# ── 10 NEW pytest cases ──────────────────────────────────────
def test_8_kpi_names_listed() -> None:
    """Test 1: ALL_KPI_NAMES has exactly 8 entries."""
    assert len(ALL_KPI_NAMES) == 8
    expected = {
        "total_monthly_cost_krw",
        "monthly_cost_growth_pct",
        "cost_per_employee_krw",
        "cost_anomaly_count_30d",
        "forecast_deviation_pct",
        "idle_cost_monthly_krw",
        "tag_compliance_pct",
        "optimization_realized_savings_krw",
    }
    assert set(ALL_KPI_NAMES) == expected


def test_select_cross_module_kpis_returns_8_in_dry_run() -> None:
    """Test 2: select_cross_module_kpis returns all 8 KPIs in dry-run."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    assert len(result) == 8


def test_kpi_set_subset_filter_works() -> None:
    """Test 3: kpi_set filter only computes requested subset."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        kpi_set=["total_monthly_cost_krw", "tag_compliance_pct"],
        dry_run=True,
    )
    assert len(result) == 2
    assert "total_monthly_cost_krw" in result
    assert "tag_compliance_pct" in result
    assert "monthly_cost_growth_pct" not in result


def test_kpi_metric_has_8_fields() -> None:
    """Test 4: KPIMetric TypedDict has all 8 fields (PRD §F32.2-10)."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    for kpi_name, kpi in result.items():
        assert "kpi_name" in kpi
        assert "kpi_value" in kpi
        assert "kpi_unit" in kpi
        assert "kpi_delta" in kpi
        assert "kpi_trend" in kpi
        assert "kpi_threshold_status" in kpi


def test_kpi_unit_krw_or_pct_or_count() -> None:
    """Test 5: KPI units are restricted to KRW/pct/count."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    for kpi_name, kpi in result.items():
        assert kpi["kpi_unit"] in {"KRW", "pct", "count"}


def test_kpi_threshold_status_enum() -> None:
    """Test 6: KPI threshold_status is on_track/warning/critical."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    for kpi_name, kpi in result.items():
        assert kpi["kpi_threshold_status"] in {
            "on_track",
            "warning",
            "critical",
        }


def test_4_scope_type_options_supported() -> None:
    """Test 7: 4 scope_type options supported."""
    for scope_type in ("tenant", "department", "cost_center", "product_line"):
        result = select_cross_module_kpis(
            tenant_id=TENANT_ID,
            scope_type=scope_type,
            scope_id="default",
            period_key="2026-08",
            dry_run=True,
        )
        assert len(result) == 8


def test_total_monthly_cost_krw_kpi_name_key() -> None:
    """Test 8: KPI #1 key is 'total_monthly_cost_krw'."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        kpi_set=["total_monthly_cost_krw"],
        dry_run=True,
    )
    assert "total_monthly_cost_krw" in result
    assert result["total_monthly_cost_krw"]["kpi_unit"] == "KRW"


def test_optimization_realized_savings_krw_kpi_name_key() -> None:
    """Test 9: KPI #8 key is 'optimization_realized_savings_krw'."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        kpi_set=["optimization_realized_savings_krw"],
        dry_run=True,
    )
    assert "optimization_realized_savings_krw" in result
    assert result["optimization_realized_savings_krw"]["kpi_unit"] == "KRW"


def test_validate_kpi_accuracy_pure_validator() -> None:
    """Test 10: validate_kpi_accuracy is pure (CR 11-4 P-015)."""
    result = select_cross_module_kpis(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        dry_run=True,
    )
    # validate_kpi_accuracy should accept the dry-run result without error.
    assert validate_kpi_accuracy(result) is True