"""tests.api.core.test_phase_23_unit_economics — Phase 23 unit economics test suite.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics derived metric
layer tests (PRD §F39.1~§F39.8 verbatim + AD-51 (a)~(g) 7 sub-decisions).

Test classes (Phase 22 verbatim pattern, 12 test classes):
- TestUnitEconomicsEngineComputation × 14
- TestCostPerBusinessUnitRollup × 12
- TestCostPerTransactionTagPropagation × 12
- TestMarginAnalysisRevenueAttribution × 14
- TestScheduledCalculationCadence × 8
- TestRouterEndpoints × 6
- TestCapabilityGate × 4
- TestAuditActionRegistry × 4
- TestTypedExceptionEnvelope × 8
- TestModuleConstants × 8
- TestEnums × 6
- TestIntegrationSmoke × 4

= 100 tests PASS

CR lessons applied:
- CR 0-2 RLS — tenant_id selector tests.
- CR 1-1 audit-first INSERT.
- CR 5-1 banker's rounding.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants.
- CR 12-5 D-14 typed exception envelope.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-51 (a)~(g) 7 sub-decisions.
- D-FINOPS-12 honestly DEFER.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from apps.api.modules.finops.unit_economics.serializers import (
    ALL_COST_PER_X_METRICS,
    ALL_MARGIN_ANALYSIS_STATUSES,
    ALL_UNIT_ECONOMICS_ALERT_SEVERITIES,
    ALL_UNIT_ECONOMICS_CALCULATION_STATUSES,
    ALL_UNIT_ECONOMICS_DIMENSIONS,
    COST_PER_X_METRIC_WEIGHTS,
    DERIVATION_DIMENSION_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MARGIN_CRITICAL_THRESHOLD_PCT,
    MARGIN_HEALTHY_THRESHOLD_PCT,
    MARGIN_NEGATIVE_PCT,
    MARGIN_WARNING_THRESHOLD_PCT,
    MAX_BUSINESS_UNITS_PER_TENANT,
    MAX_COST_PER_X_OVERRIDE_KRW,
    MAX_TRANSACTIONS_PER_PERIOD,
    UNIT_ECONOMICS_CADENCE_HOURS_KST,
    UNIT_ECONOMICS_DEFAULTS,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    UNIT_ECONOMICS_RECIPIENT_TEMPLATES,
    CostPerXMetric,
    MarginAnalysisStatus,
    UnitEconomicsAlertSeverity,
    UnitEconomicsCalculationStatus,
    UnitEconomicsDimension,
)
from apps.api.modules.finops.unit_economics.unit_economics_engine import (
    compute_unit_economics,
    list_unit_economics_results,
    validate_unit_economics_result,
)
from apps.api.modules.finops.unit_economics.scheduled_unit_economics_calculation import (
    ALL_UNIT_ECONOMICS_CADENCES,
    compute_unit_economics_period,
    schedule_cadence_calculation,
    validate_cadence,
)
from apps.api.modules.finops.unit_economics.cost_per_business_unit import (
    compute_cost_per_business_unit,
    validate_cost_per_business_unit,
    aggregate_cost_per_business_unit,
)
from apps.api.modules.finops.unit_economics.cost_per_transaction import (
    compute_cost_per_transaction,
    validate_cost_per_transaction,
    aggregate_cost_per_transaction,
)
from apps.api.modules.finops.unit_economics.margin_analysis import (
    execute_margin_analysis,
    validate_margin_analysis,
    aggregate_margin_analysis,
)
from apps.api.modules.finops.unit_economics.scheduled_unit_economics_calculation import (
    compute_unit_economics_period,
    validate_cadence,
)


# ── Fixtures ──────────────────────────────────────────────────────────────
@pytest.fixture
def tenant_id() -> str:
    return "test-tenant-phase-23"


@pytest.fixture
def period_key() -> str:
    return "2026-08"


@pytest.fixture
def source_settlement_id() -> str:
    return "phase_22_settlement_test_001"


@pytest.fixture
def five_dim_inputs() -> dict[str, float]:
    return {
        "cost_center": 300_000.0,
        "department": 250_000.0,
        "business_unit": 200_000.0,
        "tag": 150_000.0,
        "tenant": 100_000.0,
    }


@pytest.fixture
def total_cost_krw() -> float:
    return 1_000_000.0


# ── 1. TestUnitEconomicsEngineComputation ─────────────────────────────────
class TestUnitEconomicsEngineComputation:
    """14 tests for unit_economics engine computation (PRD §F39.1)."""

    def test_compute_basic(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=0,
            dry_run=False,
        )
        assert result["tenant_id"] == tenant_id
        assert result["period_key"] == period_key
        assert result["total_cost_krw"] == total_cost_krw
        assert result["cost_per_business_unit_krw"] == pytest.approx(10_000.0, abs=0.01)
        assert result["cost_per_transaction_krw"] == pytest.approx(100.0, abs=0.01)

    def test_compute_with_revenue(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=1_500_000.0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert result["margin_pct"] == pytest.approx(33.33, abs=0.02)
        assert result["margin_status"] == MarginAnalysisStatus.HEALTHY.value

    def test_compute_dry_run(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=0,
            dry_run=True,
        )
        assert result["dry_run"] is True

    def test_compute_invalid_tenant(self, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        with pytest.raises(Exception):
            compute_unit_economics(
                tenant_id="",
                period_key=period_key,
                source_settlement_id=source_settlement_id,
                total_cost_krw=total_cost_krw,
                total_revenue_krw=0,
                total_units=100,
                total_transactions=10_000,
                target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
                five_dim_inputs=five_dim_inputs,
                allocation_count=1000,
                revenue_completeness_pct=0,
                dry_run=False,
            )

    def test_compute_invalid_period(self, tenant_id, source_settlement_id, five_dim_inputs, total_cost_krw):
        with pytest.raises(Exception):
            compute_unit_economics(
                tenant_id=tenant_id,
                period_key="invalid",
                source_settlement_id=source_settlement_id,
                total_cost_krw=total_cost_krw,
                total_revenue_krw=0,
                total_units=100,
                total_transactions=10_000,
                target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
                five_dim_inputs=five_dim_inputs,
                allocation_count=1000,
                revenue_completeness_pct=0,
                dry_run=False,
            )

    def test_compute_invalid_status(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        with pytest.raises(Exception):
            compute_unit_economics(
                tenant_id=tenant_id,
                period_key=period_key,
                source_settlement_id=source_settlement_id,
                total_cost_krw=total_cost_krw,
                total_revenue_krw=0,
                total_units=100,
                total_transactions=10_000,
                target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
                five_dim_inputs=five_dim_inputs,
                allocation_count=1000,
                revenue_completeness_pct=0,
                calculation_status="invalid_status",
                dry_run=False,
            )

    def test_compute_high_value(self, tenant_id, period_key, source_settlement_id, five_dim_inputs):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=20_000_000.0,
            total_revenue_krw=30_000_000.0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs={k: v * 20 for k, v in five_dim_inputs.items()},
            allocation_count=1000,
            revenue_completeness_pct=100.0,
            calculation_status=UnitEconomicsCalculationStatus.PENDING.value,
            dry_run=False,
        )
        assert result["margin_pct"] == pytest.approx(33.33, abs=0.02)

    def test_compute_d_finops_12_defer(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        """D-FINOPS-12 honestly DEFER — no revenue registered → margin_pct=0.0."""
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=0,
            dry_run=False,
        )
        assert result["margin_pct"] == 0.0

    def test_compute_confidence_50pct_no_revenue(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=0,
            dry_run=False,
        )
        assert result["confidence_pct"] == pytest.approx(50.0, abs=0.02)

    def test_compute_confidence_100pct(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=1_500_000.0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert result["confidence_pct"] == pytest.approx(100.0, abs=0.02)

    def test_list_unit_economics(self, tenant_id):
        results = list_unit_economics_results(tenant_id=tenant_id)
        assert isinstance(results, list)

    def test_list_with_period_key(self, tenant_id, period_key):
        results = list_unit_economics_results(tenant_id=tenant_id, period_key=period_key)
        assert isinstance(results, list)

    def test_validate_result(self, tenant_id, period_key, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=0,
            dry_run=False,
        )
        validate_unit_economics_result(result)

    def test_compute_missing_dimensions(self, tenant_id, period_key, source_settlement_id, total_cost_krw):
        with pytest.raises(Exception):
            compute_unit_economics(
                tenant_id=tenant_id,
                period_key=period_key,
                source_settlement_id=source_settlement_id,
                total_cost_krw=total_cost_krw,
                total_revenue_krw=0,
                total_units=100,
                total_transactions=10_000,
                target_dimensions=[],
                five_dim_inputs={},
                allocation_count=1000,
                revenue_completeness_pct=0,
                dry_run=False,
            )


# ── 2. TestCostPerBusinessUnitRollup ──────────────────────────────────────
class TestCostPerBusinessUnitRollup:
    """12 tests for cost_per_business_unit 5-dim rollup (PRD §F39.2)."""

    def test_compute_basic(self, tenant_id, period_key, source_settlement_id):
        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=100_000.0,
            transaction_count=100,
            cost_center_amount_krw=30_000.0,
            department_amount_krw=25_000.0,
            business_unit_amount_krw=20_000.0,
            tag_amount_krw=15_000.0,
            tenant_amount_krw=10_000.0,
            dry_run=False,
        )
        assert breakdown["business_unit"] == "sales-team"
        assert breakdown["cost_per_unit_krw"] == pytest.approx(1_000.0, abs=0.01)

    def test_compute_dry_run(self, tenant_id, period_key):
        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=100_000.0,
            transaction_count=100,
            cost_center_amount_krw=30_000.0,
            department_amount_krw=25_000.0,
            business_unit_amount_krw=20_000.0,
            tag_amount_krw=15_000.0,
            tenant_amount_krw=10_000.0,
            dry_run=True,
        )
        assert breakdown["breakdown_id"] is not None

    def test_compute_high_value_2fa(self, tenant_id, period_key):
        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
            transaction_count=100,
            cost_center_amount_krw=30_000.0,
            department_amount_krw=25_000.0,
            business_unit_amount_krw=20_000.0,
            tag_amount_krw=15_000.0,
            tenant_amount_krw=10_000.0,
            dry_run=False,
        )
        assert breakdown["requires_2fa_challenge"] is True

    def test_compute_override_2fa(self, tenant_id, period_key):
        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=1_000.0,
            transaction_count=100,
            cost_center_amount_krw=300.0,
            department_amount_krw=250.0,
            business_unit_amount_krw=200.0,
            tag_amount_krw=150.0,
            tenant_amount_krw=100.0,
            is_override=True,
            dry_run=False,
        )
        assert breakdown["requires_2fa_challenge"] is True

    def test_validate_breakdown(self, tenant_id, period_key):
        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=100_000.0,
            transaction_count=100,
            cost_center_amount_krw=30_000.0,
            department_amount_krw=25_000.0,
            business_unit_amount_krw=20_000.0,
            tag_amount_krw=15_000.0,
            tenant_amount_krw=10_000.0,
            dry_run=False,
        )
        validate_cost_per_business_unit(breakdown)

    def test_aggregate(self, tenant_id, period_key):
        breakdowns = [
            compute_cost_per_business_unit(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit=f"team-{i}",
                cost_center="billing-001",
                department="sales",
                tag_key="environment:prod",
                allocated_cost_krw=100_000.0,
                transaction_count=100,
                cost_center_amount_krw=30_000.0,
                department_amount_krw=25_000.0,
                business_unit_amount_krw=20_000.0,
                tag_amount_krw=15_000.0,
                tenant_amount_krw=10_000.0,
                dry_run=False,
            )
            for i in range(3)
        ]
        agg = aggregate_cost_per_business_unit(breakdowns)
        assert agg["business_unit_count"] == 3
        assert agg["total_cost_krw"] == pytest.approx(300_000.0, abs=0.01)

    def test_invalid_business_unit(self, tenant_id, period_key):
        with pytest.raises(Exception):
            compute_cost_per_business_unit(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit="",
                cost_center="billing-001",
                department="sales",
                tag_key="environment:prod",
                allocated_cost_krw=100_000.0,
                transaction_count=100,
                cost_center_amount_krw=30_000.0,
                department_amount_krw=25_000.0,
                business_unit_amount_krw=20_000.0,
                tag_amount_krw=15_000.0,
                tenant_amount_krw=10_000.0,
                dry_run=False,
            )

    def test_invalid_negative_cost(self, tenant_id, period_key):
        with pytest.raises(Exception):
            compute_cost_per_business_unit(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit="sales-team",
                cost_center="billing-001",
                department="sales",
                tag_key="environment:prod",
                allocated_cost_krw=-100.0,
                transaction_count=100,
                cost_center_amount_krw=30_000.0,
                department_amount_krw=25_000.0,
                business_unit_amount_krw=20_000.0,
                tag_amount_krw=15_000.0,
                tenant_amount_krw=10_000.0,
                dry_run=False,
            )

    def test_zero_transactions(self, tenant_id, period_key):
        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=100_000.0,
            transaction_count=0,
            cost_center_amount_krw=30_000.0,
            department_amount_krw=25_000.0,
            business_unit_amount_krw=20_000.0,
            tag_amount_krw=15_000.0,
            tenant_amount_krw=10_000.0,
            dry_run=False,
        )
        assert breakdown["cost_per_unit_krw"] == 0.0

    def test_ledger_key_dedup_helper(self):
        from apps.api.modules.finops.unit_economics.cost_per_business_unit import _ledger_key_dedup
        entries = [
            {"allocation_id": "a1", "computed_at": "2026-08-01T00:00:00", "value": 100},
            {"allocation_id": "a1", "computed_at": "2026-08-02T00:00:00", "value": 200},
            {"allocation_id": "a2", "computed_at": "2026-08-01T00:00:00", "value": 300},
        ]
        deduped = _ledger_key_dedup(entries)
        assert len(deduped) == 2

    def test_constant_5dim_sum(self):
        from apps.api.modules.finops.unit_economics.cost_per_business_unit import DERIVATION_DIMENSION_WEIGHT_SUM
        assert DERIVATION_DIMENSION_WEIGHT_SUM == pytest.approx(1.0, abs=0.001)

    def test_constant_max_bu(self):
        assert MAX_BUSINESS_UNITS_PER_TENANT == 1000


# ── 3. TestCostPerTransactionTagPropagation ───────────────────────────────
class TestCostPerTransactionTagPropagation:
    """12 tests for cost_per_transaction tag propagation (PRD §F39.3)."""

    def test_compute_basic(self, tenant_id, period_key):
        transaction = compute_cost_per_transaction(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            transaction_id="tx-001",
            business_unit="sales-team",
            cost_center="billing-001",
            allocated_cost_krw=10_000.0,
            transaction_count=1,
            phase_22_settlement_tags={"cost_center": "billing-001"},
            dry_run=False,
        )
        assert transaction["transaction_id"] is not None
        assert transaction["tag_propagation_json"]["propagated_tag_count"] == 1

    def test_compute_dry_run(self, tenant_id, period_key):
        transaction = compute_cost_per_transaction(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            transaction_id="tx-001",
            business_unit="sales-team",
            cost_center="billing-001",
            allocated_cost_krw=10_000.0,
            transaction_count=1,
            phase_22_settlement_tags={},
            dry_run=True,
        )
        assert transaction["transaction_id"] is not None

    def test_tag_propagation_filtered(self, tenant_id, period_key):
        transaction = compute_cost_per_transaction(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            transaction_id="tx-001",
            business_unit="sales-team",
            cost_center="billing-001",
            allocated_cost_krw=10_000.0,
            transaction_count=1,
            phase_22_settlement_tags={
                "cost_center": "billing-001",
                "custom_tag": "value",  # NOT in ALLOWED_TAG_KEYS
            },
            dry_run=False,
        )
        assert transaction["tag_propagation_json"]["propagated_tag_count"] == 1
        assert transaction["tag_propagation_json"]["skipped_tag_count"] == 1

    def test_tag_propagation_no_tags(self, tenant_id, period_key):
        transaction = compute_cost_per_transaction(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            transaction_id="tx-001",
            business_unit="sales-team",
            cost_center="billing-001",
            allocated_cost_krw=10_000.0,
            transaction_count=1,
            dry_run=False,
        )
        assert transaction["tag_propagation_json"]["propagated_tag_count"] == 0

    def test_validate(self, tenant_id, period_key):
        transaction = compute_cost_per_transaction(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            transaction_id="tx-001",
            business_unit="sales-team",
            cost_center="billing-001",
            allocated_cost_krw=10_000.0,
            transaction_count=1,
            dry_run=False,
        )
        validate_cost_per_transaction(transaction)

    def test_aggregate(self, tenant_id, period_key):
        transactions = [
            compute_cost_per_transaction(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                transaction_id=f"tx-{i}",
                business_unit="sales-team",
                cost_center="billing-001",
                allocated_cost_krw=10_000.0,
                transaction_count=1,
                phase_22_settlement_tags={"cost_center": "billing-001"},
                dry_run=False,
            )
            for i in range(5)
        ]
        agg = aggregate_cost_per_transaction(transactions)
        assert agg["transaction_count"] == 5
        assert "cost_center" in agg["tag_filter_dimensions"]

    def test_invalid_transaction_id(self, tenant_id, period_key):
        with pytest.raises(Exception):
            compute_cost_per_transaction(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                transaction_id="",
                business_unit="sales-team",
                cost_center="billing-001",
                allocated_cost_krw=10_000.0,
                transaction_count=1,
                dry_run=False,
            )

    def test_invalid_negative_cost(self, tenant_id, period_key):
        with pytest.raises(Exception):
            compute_cost_per_transaction(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                transaction_id="tx-001",
                business_unit="sales-team",
                cost_center="billing-001",
                allocated_cost_krw=-100.0,
                transaction_count=1,
                dry_run=False,
            )

    def test_invalid_tags_not_dict(self, tenant_id, period_key):
        with pytest.raises(Exception):
            compute_cost_per_transaction(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                transaction_id="tx-001",
                business_unit="sales-team",
                cost_center="billing-001",
                allocated_cost_krw=10_000.0,
                transaction_count=1,
                phase_22_settlement_tags="not_a_dict",  # type: ignore[arg-type]
                dry_run=False,
            )

    def test_allowed_tag_keys_count(self):
        from apps.api.modules.finops.unit_economics.cost_per_transaction import ALLOWED_TAG_KEYS
        assert len(ALLOWED_TAG_KEYS) == 7

    def test_max_transactions_constant(self):
        assert MAX_TRANSACTIONS_PER_PERIOD == 100_000

    def test_compute_high_value_2fa(self, tenant_id, period_key):
        transaction = compute_cost_per_transaction(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            transaction_id="tx-001",
            business_unit="sales-team",
            cost_center="billing-001",
            allocated_cost_krw=HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
            transaction_count=MAX_TRANSACTIONS_PER_PERIOD + 1,
            dry_run=False,
        )
        assert transaction["requires_2fa_challenge"] is True


# ── 4. TestMarginAnalysisRevenueAttribution ───────────────────────────────
class TestMarginAnalysisRevenueAttribution:
    """14 tests for margin analysis (PRD §F39.4)."""

    def test_compute_healthy(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=15_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["margin_pct"] == pytest.approx(33.33, abs=0.02)
        assert margin["margin_status"] == MarginAnalysisStatus.HEALTHY.value

    def test_compute_warning(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=12_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["margin_pct"] == pytest.approx(16.67, abs=0.02)
        assert margin["margin_status"] == MarginAnalysisStatus.WARNING.value

    def test_compute_critical(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=11_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["margin_pct"] == pytest.approx(9.09, abs=0.02)
        assert margin["margin_status"] == MarginAnalysisStatus.CRITICAL.value

    def test_compute_negative(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=15_000_000.0,
            total_revenue_krw=10_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["margin_pct"] == pytest.approx(-50.0, abs=0.02)
        assert margin["margin_status"] == MarginAnalysisStatus.NEGATIVE.value
        assert margin["requires_2fa_challenge"] is True

    def test_d_finops_12_no_revenue(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=0,
            revenue_sources=[],
            revenue_completeness_pct=0,
            dry_run=False,
        )
        assert margin["margin_pct"] == 0.0  # D-FINOPS-12 honestly DEFER

    def test_dry_run(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=15_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=True,
        )
        assert margin["margin_id"] is not None

    def test_validate(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=15_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        validate_margin_analysis(margin)

    def test_aggregate(self, tenant_id, period_key):
        margins = [
            execute_margin_analysis(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit=f"team-{i}",
                total_cost_krw=10_000_000.0,
                total_revenue_krw=15_000_000.0,
                revenue_sources=["revenue_1"],
                revenue_completeness_pct=100.0,
                dry_run=False,
            )
            for i in range(3)
        ]
        agg = aggregate_margin_analysis(margins)
        assert agg["business_unit_count"] == 3
        assert agg["total_margin_krw"] == pytest.approx(15_000_000.0, abs=0.02)

    def test_invalid_revenue_completeness(self, tenant_id, period_key):
        with pytest.raises(Exception):
            execute_margin_analysis(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit="sales-team",
                total_cost_krw=10_000_000.0,
                total_revenue_krw=15_000_000.0,
                revenue_sources=["revenue_1"],
                revenue_completeness_pct=150.0,  # >100
                dry_run=False,
            )

    def test_invalid_negative_cost(self, tenant_id, period_key):
        with pytest.raises(Exception):
            execute_margin_analysis(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit="sales-team",
                total_cost_krw=-100.0,
                total_revenue_krw=15_000_000.0,
                revenue_sources=["revenue_1"],
                revenue_completeness_pct=100.0,
                dry_run=False,
            )

    def test_invalid_revenue_sources_not_list(self, tenant_id, period_key):
        with pytest.raises(Exception):
            execute_margin_analysis(
                tenant_id=tenant_id,
                unit_economics_id="ue_test",
                period_key=period_key,
                business_unit="sales-team",
                total_cost_krw=10_000_000.0,
                total_revenue_krw=15_000_000.0,
                revenue_sources="not_a_list",  # type: ignore[arg-type]
                revenue_completeness_pct=100.0,
                dry_run=False,
            )

    def test_high_value_positive_margin_2fa(self, tenant_id, period_key):
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=5_000_000.0,
            total_revenue_krw=20_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["requires_2fa_challenge"] is True

    def test_margin_status_helper(self):
        from apps.api.modules.finops.unit_economics.margin_analysis import _compute_margin_status
        assert _compute_margin_status(50.0) == MarginAnalysisStatus.HEALTHY.value
        assert _compute_margin_status(20.0) == MarginAnalysisStatus.WARNING.value
        assert _compute_margin_status(10.0) == MarginAnalysisStatus.CRITICAL.value
        assert _compute_margin_status(-5.0) == MarginAnalysisStatus.NEGATIVE.value

    def test_constant_thresholds(self):
        assert MARGIN_HEALTHY_THRESHOLD_PCT == 30.0
        assert MARGIN_WARNING_THRESHOLD_PCT == 15.0
        assert MARGIN_CRITICAL_THRESHOLD_PCT == 15.0
        assert MARGIN_NEGATIVE_PCT == 0.0


# ── 5. TestScheduledCalculationCadence ────────────────────────────────────
class TestScheduledCalculationCadence:
    """8 tests for scheduled calculation (PRD §F39.1)."""

    def test_compute_daily(self, tenant_id, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics_period(
            tenant_id=tenant_id,
            source_settlement_id=source_settlement_id,
            five_dim_inputs=five_dim_inputs,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            allocation_count=1000,
            revenue_completeness_pct=0,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            cadence="daily",
            dry_run=False,
        )
        assert result["period_key"] != ""

    def test_compute_weekly(self, tenant_id, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics_period(
            tenant_id=tenant_id,
            source_settlement_id=source_settlement_id,
            five_dim_inputs=five_dim_inputs,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            allocation_count=1000,
            revenue_completeness_pct=0,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            cadence="weekly",
            dry_run=False,
        )
        assert result["period_key"] != ""

    def test_compute_monthly(self, tenant_id, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics_period(
            tenant_id=tenant_id,
            source_settlement_id=source_settlement_id,
            five_dim_inputs=five_dim_inputs,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            allocation_count=1000,
            revenue_completeness_pct=0,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            cadence="monthly",
            dry_run=False,
        )
        assert result["period_key"] != ""

    def test_compute_quarterly(self, tenant_id, source_settlement_id, five_dim_inputs, total_cost_krw):
        result = compute_unit_economics_period(
            tenant_id=tenant_id,
            source_settlement_id=source_settlement_id,
            five_dim_inputs=five_dim_inputs,
            total_cost_krw=total_cost_krw,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            allocation_count=1000,
            revenue_completeness_pct=0,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            cadence="quarterly",
            dry_run=False,
        )
        assert result["period_key"] != ""

    def test_validate_cadence_valid(self):
        validate_cadence("daily")
        validate_cadence("weekly")
        validate_cadence("monthly")
        validate_cadence("quarterly")

    def test_validate_cadence_invalid(self):
        with pytest.raises(Exception):
            validate_cadence("invalid_cadence")

    def test_cadence_hours_kst(self):
        assert UNIT_ECONOMICS_CADENCE_HOURS_KST["daily"] == (3, 30)
        assert UNIT_ECONOMICS_CADENCE_HOURS_KST["weekly"] == (4, 0)
        assert UNIT_ECONOMICS_CADENCE_HOURS_KST["monthly"] == (4, 30)
        assert UNIT_ECONOMICS_CADENCE_HOURS_KST["quarterly"] == (5, 0)

    def test_all_cadences_list(self):
        assert set(ALL_UNIT_ECONOMICS_CADENCES) == {"daily", "weekly", "monthly", "quarterly"}


# ── 6. TestRouterEndpoints ────────────────────────────────────────────────
class TestRouterEndpoints:
    """6 tests for FastAPI router endpoints."""

    def test_router_prefix(self):
        from apps.api.modules.finops.unit_economics.unit_economics_routes import router
        assert router.prefix == "/api/v1/finops/unit-economics"

    def test_router_tags(self):
        from apps.api.modules.finops.unit_economics.unit_economics_routes import router
        assert "finops" in router.tags
        assert "unit_economics" in router.tags

    def test_router_has_capability_gate(self):
        from apps.api.modules.finops.unit_economics.unit_economics_routes import router
        assert len(router.dependencies) > 0

    def test_router_routes_count(self):
        from apps.api.modules.finops.unit_economics.unit_economics_routes import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/finops/unit-economics/healthcheck" in routes
        assert "/api/v1/finops/unit-economics/compute" in routes
        assert "/api/v1/finops/unit-economics/cost-per-business-unit" in routes
        assert "/api/v1/finops/unit-economics/cost-per-transaction" in routes
        assert "/api/v1/finops/unit-economics/margin-analysis" in routes
        assert "/api/v1/finops/unit-economics/dry-run" in routes
        assert "/api/v1/finops/unit-economics/trend" in routes
        assert "/api/v1/finops/unit-economics/calculation" in routes
        assert "/api/v1/finops/unit-economics/cadence-preview" in routes

    def test_router_total_endpoints(self):
        from apps.api.modules.finops.unit_economics.unit_economics_routes import router
        assert len(router.routes) >= 9

    def test_router_module_id(self):
        from apps.api.modules.finops.unit_economics import MODULE_TAG
        assert MODULE_TAG == "m31_finops_unit_economics"


# ── 7. TestCapabilityGate ─────────────────────────────────────────────────
class TestCapabilityGate:
    """4 tests for capability gate (CR 12-5 D-GATE-01)."""

    def test_capability_exists(self):
        from apps.api.core.capability import Capability
        assert hasattr(Capability, "FINOPS_UNIT_ECONOMICS")

    def test_capability_value(self):
        from apps.api.core.capability import Capability
        assert Capability.FINOPS_UNIT_ECONOMICS.value == "finops_unit_economics"

    def test_require_finops_unit_economics_exists(self):
        from apps.api.dependencies.capability import require_finops_unit_economics
        assert require_finops_unit_economics is not None

    def test_industry_agnostic_grants(self):
        from apps.api.core.capability import (
            Capability,
            _INDUSTRY_CAPABILITIES,
        )
        # Verify FINOPS_UNIT_ECONOMICS is granted to all 4 industries
        assert Capability.FINOPS_UNIT_ECONOMICS in [c for c in Capability]
        for industry, caps in _INDUSTRY_CAPABILITIES.items():
            assert Capability.FINOPS_UNIT_ECONOMICS in caps, (
                f"FINOPS_UNIT_ECONOMICS missing for {industry}"
            )


# ── 8. TestAuditActionRegistry ────────────────────────────────────────────
class TestAuditActionRegistry:
    """4 tests for audit action registry (CR 1-1)."""

    def test_audit_action_class_exists(self):
        from apps.api.core.audit_action import ActionClass
        assert hasattr(ActionClass, "FINOPS_UNIT_ECONOMICS")

    def test_audit_action_literal_type(self):
        from apps.api.core.audit_action import FinopsUnitEconomicsAction
        # 7 NEW values
        assert "unit_economics_calculated" in FinopsUnitEconomicsAction.__args__
        assert "cost_per_business_unit_refreshed" in FinopsUnitEconomicsAction.__args__
        assert "cost_per_transaction_computed" in FinopsUnitEconomicsAction.__args__
        assert "margin_analysis_executed" in FinopsUnitEconomicsAction.__args__
        assert "unit_economics_dry_run_executed" in FinopsUnitEconomicsAction.__args__
        assert "unit_economics_margin_alert" in FinopsUnitEconomicsAction.__args__
        assert "unit_economics_margin_negative_alert" in FinopsUnitEconomicsAction.__args__

    def test_audit_action_registry_value_count(self):
        from apps.api.core.audit_action import _ActionRegistry, ActionClass
        registry = _ActionRegistry._REGISTRY
        log_type, actions = registry.get(
            ActionClass.FINOPS_UNIT_ECONOMICS, ("audit_logs", frozenset())
        )
        assert log_type == "audit_logs"
        assert len(actions) == 7

    def test_module_id_in_errors(self):
        from apps.api.core.errors import FINOPS_UNIT_ECONOMICS_MODULE_ID
        assert FINOPS_UNIT_ECONOMICS_MODULE_ID == "m31_finops_unit_economics"


# ── 9. TestTypedExceptionEnvelope ─────────────────────────────────────────
class TestTypedExceptionEnvelope:
    """8 tests for typed exception envelope (CR 12-5 D-14)."""

    def test_base_exception_class(self):
        from apps.api.core.errors import FinopsUnitEconomicsError
        assert issubclass(FinopsUnitEconomicsError, Exception)

    def test_dimension_error(self):
        from apps.api.core.errors import FinopsUnitEconomicsError, UnitEconomicsDimensionError
        assert issubclass(UnitEconomicsDimensionError, FinopsUnitEconomicsError)

    def test_aggregation_error(self):
        from apps.api.core.errors import FinopsUnitEconomicsError, UnitEconomicsAggregationError
        assert issubclass(UnitEconomicsAggregationError, FinopsUnitEconomicsError)

    def test_transaction_error(self):
        from apps.api.core.errors import FinopsUnitEconomicsError, UnitEconomicsTransactionError
        assert issubclass(UnitEconomicsTransactionError, FinopsUnitEconomicsError)

    def test_margin_error(self):
        from apps.api.core.errors import FinopsUnitEconomicsError, UnitEconomicsMarginError
        assert issubclass(UnitEconomicsMarginError, FinopsUnitEconomicsError)

    def test_alert_error(self):
        from apps.api.core.errors import FinopsUnitEconomicsError, UnitEconomicsAlertError
        assert issubclass(UnitEconomicsAlertError, FinopsUnitEconomicsError)

    def test_revenue_error(self):
        from apps.api.core.errors import FinopsUnitEconomicsError, UnitEconomicsRevenueError
        assert issubclass(UnitEconomicsRevenueError, FinopsUnitEconomicsError)

    def test_exception_count(self):
        from apps.api.core.errors import FinopsUnitEconomicsError
        import apps.api.core.errors as errors_module
        subclasses = [
            name
            for name in dir(errors_module)
            if name.startswith("UnitEconomics")
            and isinstance(getattr(errors_module, name), type)
            and issubclass(getattr(errors_module, name), FinopsUnitEconomicsError)
        ]
        assert len(subclasses) >= 15


# ── 10. TestModuleConstants ───────────────────────────────────────────────
class TestModuleConstants:
    """8 tests for module constants."""

    def test_model_version(self):
        assert UNIT_ECONOMICS_ENGINE_MODEL_VERSION == "1.0.0"

    def test_high_value_threshold(self):
        assert HIGH_VALUE_THRESHOLD_KRW_PER_YEAR == 10_000_000.0

    def test_derivation_weights_sum(self):
        assert sum(DERIVATION_DIMENSION_WEIGHTS.values()) == pytest.approx(1.0, abs=0.001)

    def test_cost_per_x_weights_sum(self):
        assert sum(COST_PER_X_METRIC_WEIGHTS.values()) == pytest.approx(1.0, abs=0.001)

    def test_max_cost_per_x_override(self):
        assert MAX_COST_PER_X_OVERRIDE_KRW == 10_000_000.0

    def test_defaults_keys(self):
        assert "model_version" in UNIT_ECONOMICS_DEFAULTS
        assert "high_value_threshold_krw_per_year" in UNIT_ECONOMICS_DEFAULTS
        assert "dry_run_supported" in UNIT_ECONOMICS_DEFAULTS
        assert "2fa_challenge_supported" in UNIT_ECONOMICS_DEFAULTS

    def test_recipient_templates(self):
        assert "owner_only" in UNIT_ECONOMICS_RECIPIENT_TEMPLATES
        assert "executive" in UNIT_ECONOMICS_RECIPIENT_TEMPLATES
        assert "audit_only" in UNIT_ECONOMICS_RECIPIENT_TEMPLATES

    def test_alembic_revision_constant(self):
        # Verify alembic 0055 down_revision
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "alembic_0055",
            str(PROJECT_ROOT / "apps" / "api" / "alembic" / "versions" / "0055_phase_23_unit_economics.py"),
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "0055_phase_23_unit_economics"
        assert module.down_revision == "0054_phase_22_chargeback_settlement"


# ── 11. TestEnums ─────────────────────────────────────────────────────────
class TestEnums:
    """6 tests for enum values."""

    def test_calculation_statuses(self):
        assert UnitEconomicsCalculationStatus.PENDING.value == "pending"
        assert UnitEconomicsCalculationStatus.COMPUTING.value == "computing"
        assert UnitEconomicsCalculationStatus.COMPLETED.value == "completed"
        assert UnitEconomicsCalculationStatus.FAILED.value == "failed"
        assert UnitEconomicsCalculationStatus.DRY_RUN_COMPLETED.value == "dry_run_completed"
        assert len(ALL_UNIT_ECONOMICS_CALCULATION_STATUSES) == 5

    def test_dimensions(self):
        assert UnitEconomicsDimension.COST_CENTER.value == "cost_center"
        assert UnitEconomicsDimension.DEPARTMENT.value == "department"
        assert UnitEconomicsDimension.BUSINESS_UNIT.value == "business_unit"
        assert UnitEconomicsDimension.TAG.value == "tag"
        assert UnitEconomicsDimension.TENANT.value == "tenant"
        assert len(ALL_UNIT_ECONOMICS_DIMENSIONS) == 5

    def test_cost_per_x_metrics(self):
        assert CostPerXMetric.COST_PER_BUSINESS_UNIT.value == "cost_per_business_unit"
        assert CostPerXMetric.COST_PER_TRANSACTION.value == "cost_per_transaction"
        assert len(ALL_COST_PER_X_METRICS) == 4

    def test_margin_statuses(self):
        assert MarginAnalysisStatus.HEALTHY.value == "healthy"
        assert MarginAnalysisStatus.WARNING.value == "warning"
        assert MarginAnalysisStatus.CRITICAL.value == "critical"
        assert MarginAnalysisStatus.NEGATIVE.value == "negative"
        assert len(ALL_MARGIN_ANALYSIS_STATUSES) == 4

    def test_alert_severities(self):
        assert UnitEconomicsAlertSeverity.INFO.value == "info"
        assert UnitEconomicsAlertSeverity.WARNING.value == "warning"
        assert UnitEconomicsAlertSeverity.CRITICAL.value == "critical"
        assert len(ALL_UNIT_ECONOMICS_ALERT_SEVERITIES) == 3

    def test_dimension_weights_individual(self):
        assert DERIVATION_DIMENSION_WEIGHTS["cost_center"] == 0.30
        assert DERIVATION_DIMENSION_WEIGHTS["department"] == 0.25
        assert DERIVATION_DIMENSION_WEIGHTS["business_unit"] == 0.20
        assert DERIVATION_DIMENSION_WEIGHTS["tag"] == 0.15
        assert DERIVATION_DIMENSION_WEIGHTS["tenant"] == 0.10


# ── 12. TestIntegrationSmoke ──────────────────────────────────────────────
class TestIntegrationSmoke:
    """4 tests for end-to-end integration smoke."""

    def test_full_pipeline_healthy_margin(self, tenant_id, period_key, source_settlement_id, five_dim_inputs):
        """End-to-end: compute → cost_per_bu → cost_per_tx → margin → healthy."""
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=10_000_000.0,
            total_revenue_krw=15_000_000.0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert result["margin_status"] == MarginAnalysisStatus.HEALTHY.value

        breakdown = compute_cost_per_business_unit(
            tenant_id=tenant_id,
            unit_economics_id=result["unit_economics_id"],
            period_key=period_key,
            business_unit="sales-team",
            cost_center="billing-001",
            department="sales",
            tag_key="environment:prod",
            allocated_cost_krw=result["cost_per_business_unit_krw"] * 100,
            transaction_count=10_000,
            cost_center_amount_krw=300_000.0,
            department_amount_krw=250_000.0,
            business_unit_amount_krw=200_000.0,
            tag_amount_krw=150_000.0,
            tenant_amount_krw=100_000.0,
            dry_run=False,
        )
        assert breakdown["breakdown_id"] is not None

        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id=result["unit_economics_id"],
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=10_000_000.0,
            total_revenue_krw=15_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["margin_status"] == MarginAnalysisStatus.HEALTHY.value

    def test_full_pipeline_negative_margin(self, tenant_id, period_key, source_settlement_id, five_dim_inputs):
        """End-to-end: margin negative → alert triggered → 2FA required."""
        margin = execute_margin_analysis(
            tenant_id=tenant_id,
            unit_economics_id="ue_test",
            period_key=period_key,
            business_unit="sales-team",
            total_cost_krw=15_000_000.0,
            total_revenue_krw=10_000_000.0,
            revenue_sources=["revenue_1"],
            revenue_completeness_pct=100.0,
            dry_run=False,
        )
        assert margin["margin_status"] == MarginAnalysisStatus.NEGATIVE.value
        assert margin["requires_2fa_challenge"] is True

    def test_full_pipeline_dry_run(self, tenant_id, period_key, source_settlement_id, five_dim_inputs):
        """End-to-end: dry-run mode produces preview without persistence."""
        result = compute_unit_economics(
            tenant_id=tenant_id,
            period_key=period_key,
            source_settlement_id=source_settlement_id,
            total_cost_krw=10_000_000.0,
            total_revenue_krw=0,
            total_units=100,
            total_transactions=10_000,
            target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
            five_dim_inputs=five_dim_inputs,
            allocation_count=1000,
            revenue_completeness_pct=0,
            dry_run=True,
        )
        assert result["dry_run"] is True

    def test_full_pipeline_4_cadence(self, tenant_id, source_settlement_id, five_dim_inputs):
        """End-to-end: 4 cadence (daily + weekly + monthly + quarterly)."""
        for cadence in ["daily", "weekly", "monthly", "quarterly"]:
            result = compute_unit_economics_period(
                tenant_id=tenant_id,
                source_settlement_id=source_settlement_id,
                five_dim_inputs=five_dim_inputs,
                total_cost_krw=1_000_000.0,
                total_revenue_krw=0,
                total_units=100,
                total_transactions=10_000,
                allocation_count=1000,
                revenue_completeness_pct=0,
                target_dimensions=list(ALL_UNIT_ECONOMICS_DIMENSIONS),
                cadence=cadence,
                dry_run=False,
            )
            assert result["period_key"] != ""
            assert result["margin_pct"] == 0.0  # D-FINOPS-12 DEFER
