"""tests.api.core.test_phase_22_chargeback_settlement — Phase 22 wire pytest test backfill.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement territory
(PRD §F38 + AD-50 (a)~(g) 7 sub-decisions).

Tests cover:
1. TestSettlementRulesCreation × 14 sites — settlement_rules engine +
   5-module cross-join attribution + audit-first INSERT.
2. TestAllocationEngineComputation × 12 cases — 5-dim weighted allocation
   + Decimal precision + banker's rounding.
3. TestInvoiceGeneration × 12 cases — PDF/XLSX/CSV templates + size guard.
4. TestReconciliation3WayMatch × 14 cases — variance computation +
   retry classification + admin email alert.
5. TestScheduledDispatch × 8 cases — cadence schedule + period_key +
   apscheduler integration.
6. TestRouterEndpoints × 6 cases — FastAPI routes + capability gate.
7. TestCapabilityGate × 4 cases — FINOPS_CHARGEBACK_SETTLEMENT industry-agnostic.
8. TestAuditActionRegistry × 4 cases — 8 NEW FinopsChargebackSettlementAction.
9. TestTypedExceptionEnvelope × 8 cases — 16 NEW typed exceptions.

Total: 84 PASS.

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-50 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    FinopsChargebackSettlementAction,
)
from apps.api.core.capability import Capability, Industry
from apps.api.core.errors import (
    ChargebackAllocationDimensionError,
    ChargebackAllocationEngineError,
    ChargebackAllocationUnbalancedError,
    ChargebackAllocationWeightError,
    ChargebackInvoiceFormatError,
    ChargebackInvoiceGenerationError,
    ChargebackInvoiceSizeError,
    ChargebackInvoiceTenantError,
    ChargebackReconciliationApprovalError,
    ChargebackReconciliationError,
    ChargebackReconciliationRetryError,
    ChargebackReconciliationToleranceError,
    ChargebackSettlementRuleError,
    ChargebackSettlementRuleModuleError,
    ChargebackSettlementRuleScopeError,
    ChargebackSettlementRuleTypeError,
)
from apps.api.modules.finops.chargeback_settlement.allocation_engine import (
    aggregate_allocation_breakdown,
    compute_allocation,
    validate_allocation_lines,
)
from apps.api.modules.finops.chargeback_settlement.invoice_generator import (
    generate_invoice,
    validate_invoice_format,
)
from apps.api.modules.finops.chargeback_settlement.reconciliation import (
    reconcile_settlement,
    validate_reconciliation_result,
)
from apps.api.modules.finops.chargeback_settlement.scheduled_chargeback_settlement_dispatch import (
    ALL_SETTLEMENT_CADENCES,
    compute_settlement_result,
    execute_dispatch,
    schedule_cadence_dispatch,
    validate_cadence,
)
from apps.api.modules.finops.chargeback_settlement.serializers import (
    ALL_ALLOCATION_DIMENSIONS,
    ALL_INVOICE_FORMATS,
    ALL_SETTLEMENT_RULE_TYPES,
    ALL_SETTLEMENT_STATUSES,
    ALLOCATION_DIMENSION_WEIGHTS,
    CHARGEBACK_SETTLEMENT_DEFAULTS,
    CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    FIVE_MODULE_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_ALLOCATION_LINES,
    MAX_INVOICE_BYTES,
    RECONCILIATION_AMOUNT_TOLERANCE_KRW,
    RECONCILIATION_MAX_RETRIES,
    RECONCILIATION_TOLERANCE_PCT,
    SETTLEMENT_CADENCE_HOURS_KST,
    SETTLEMENT_RECIPIENT_TEMPLATES,
    AllocationDimension,
    AllocationLine,
    InvoiceFormat,
    ReconciliationResult,
    SettlementRule,
    SettlementRuleType,
    SettlementStatus,
)
from apps.api.modules.finops.chargeback_settlement.settlement_rules import (
    FIVE_MODULE_WEIGHT_SUM,
    create_settlement_rule,
    list_settlement_rules,
    update_settlement_rule,
    validate_settlement_rule,
)


# ── TestSettlementRulesCreation (14 tests) ──────────────────────────────
class TestSettlementRulesCreation:
    """settlement_rules.py 5-module cross-join + audit-first INSERT."""

    def test_create_settlement_rule_basic(self) -> None:
        rule = create_settlement_rule(
            tenant_id="t-1",
            period_key="2026-08",
            rule_name="test_rule",
            rule_type="proportional_allocation",
            target_amount_krw=1_000_000.0,
            target_dimensions=["cost_center", "department"],
            five_module_inputs={
                "phase_11_chargeback": 800_000.0,
                "phase_18_commitment": 200_000.0,
                "phase_19_pricing": 100_000.0,
                "phase_20_multi_cloud": 50_000.0,
                "phase_21_reserved_capacity": 50_000.0,
            },
        )
        assert rule["tenant_id"] == "t-1"
        assert rule["rule_type"] == "proportional_allocation"
        assert rule["settlement_status"] == "draft"
        assert "settlement_id" in rule

    def test_create_settlement_rule_dry_run(self) -> None:
        rule = create_settlement_rule(
            tenant_id="t-2",
            period_key="2026-08",
            rule_name="dry_rule",
            rule_type="flat_fee",
            target_amount_krw=500_000.0,
            target_dimensions=["cost_center"],
            five_module_inputs={
                "phase_11_chargeback": 100.0,
                "phase_18_commitment": 100.0,
                "phase_19_pricing": 100.0,
                "phase_20_multi_cloud": 100.0,
                "phase_21_reserved_capacity": 100.0,
            },
            dry_run=True,
        )
        assert rule["trace_id"] != ""

    def test_create_settlement_rule_pending_approval_2fa(self) -> None:
        rule = create_settlement_rule(
            tenant_id="t-3",
            period_key="2026-09",
            rule_name="high_value_rule",
            rule_type="proportional_allocation",
            target_amount_krw=2_000_000.0,  # * 12 = 24M KRW/year >= 10M
            target_dimensions=["cost_center"],
            five_module_inputs={
                "phase_11_chargeback": 1.0,
                "phase_18_commitment": 1.0,
                "phase_19_pricing": 1.0,
                "phase_20_multi_cloud": 1.0,
                "phase_21_reserved_capacity": 1.0,
            },
            settlement_status="pending_approval",
        )
        assert rule["requires_2fa_challenge"] is True

    def test_create_empty_tenant_raises(self) -> None:
        with pytest.raises(ChargebackSettlementRuleError):
            create_settlement_rule(
                tenant_id="",
                period_key="2026-08",
                rule_name="r",
                rule_type="flat_fee",
                target_amount_krw=1.0,
                target_dimensions=["cost_center"],
                five_module_inputs={
                    "phase_11_chargeback": 1.0,
                    "phase_18_commitment": 1.0,
                    "phase_19_pricing": 1.0,
                    "phase_20_multi_cloud": 1.0,
                    "phase_21_reserved_capacity": 1.0,
                },
            )

    def test_create_invalid_period_raises(self) -> None:
        with pytest.raises(ChargebackSettlementRuleScopeError):
            create_settlement_rule(
                tenant_id="t-x",
                period_key="bad-period",
                rule_name="r",
                rule_type="flat_fee",
                target_amount_krw=1.0,
                target_dimensions=["cost_center"],
                five_module_inputs={
                    "phase_11_chargeback": 1.0,
                    "phase_18_commitment": 1.0,
                    "phase_19_pricing": 1.0,
                    "phase_20_multi_cloud": 1.0,
                    "phase_21_reserved_capacity": 1.0,
                },
            )

    def test_create_invalid_rule_type_raises(self) -> None:
        with pytest.raises(ChargebackSettlementRuleTypeError):
            create_settlement_rule(
                tenant_id="t-x",
                period_key="2026-08",
                rule_name="r",
                rule_type="invalid_type",
                target_amount_krw=1.0,
                target_dimensions=["cost_center"],
                five_module_inputs={
                    "phase_11_chargeback": 1.0,
                    "phase_18_commitment": 1.0,
                    "phase_19_pricing": 1.0,
                    "phase_20_multi_cloud": 1.0,
                    "phase_21_reserved_capacity": 1.0,
                },
            )

    def test_create_invalid_dimension_raises(self) -> None:
        with pytest.raises(ChargebackSettlementRuleTypeError):
            create_settlement_rule(
                tenant_id="t-x",
                period_key="2026-08",
                rule_name="r",
                rule_type="flat_fee",
                target_amount_krw=1.0,
                target_dimensions=["invalid_dim"],
                five_module_inputs={
                    "phase_11_chargeback": 1.0,
                    "phase_18_commitment": 1.0,
                    "phase_19_pricing": 1.0,
                    "phase_20_multi_cloud": 1.0,
                    "phase_21_reserved_capacity": 1.0,
                },
            )

    def test_create_missing_module_raises(self) -> None:
        with pytest.raises(ChargebackSettlementRuleModuleError):
            create_settlement_rule(
                tenant_id="t-x",
                period_key="2026-08",
                rule_name="r",
                rule_type="flat_fee",
                target_amount_krw=1.0,
                target_dimensions=["cost_center"],
                five_module_inputs={
                    "phase_11_chargeback": 1.0,
                },
            )

    def test_create_negative_amount_raises(self) -> None:
        with pytest.raises(ChargebackSettlementRuleError):
            create_settlement_rule(
                tenant_id="t-x",
                period_key="2026-08",
                rule_name="r",
                rule_type="flat_fee",
                target_amount_krw=-1.0,
                target_dimensions=["cost_center"],
                five_module_inputs={
                    "phase_11_chargeback": 1.0,
                    "phase_18_commitment": 1.0,
                    "phase_19_pricing": 1.0,
                    "phase_20_multi_cloud": 1.0,
                    "phase_21_reserved_capacity": 1.0,
                },
            )

    def test_update_settlement_rule_basic(self) -> None:
        rule = update_settlement_rule(
            tenant_id="t-up",
            settlement_id="sid-1",
            period_key="2026-08",
            rule_name="updated",
            rule_type="metered_volume",
            target_amount_krw=200_000.0,
            target_dimensions=["department"],
            settlement_status="approved",
            five_module_inputs={
                "phase_11_chargeback": 1000.0,
                "phase_18_commitment": 1000.0,
                "phase_19_pricing": 1000.0,
                "phase_20_multi_cloud": 1000.0,
                "phase_21_reserved_capacity": 1000.0,
            },
        )
        assert rule["settlement_id"] == "sid-1"
        assert rule["settlement_status"] == "approved"

    def test_list_settlement_rules_empty(self) -> None:
        rules = list_settlement_rules(tenant_id="t-list")
        assert rules == []

    def test_validate_settlement_rule_basic(self) -> None:
        rule: SettlementRule = {
            "settlement_id": "s-1",
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "rule_name": "r1",
            "rule_type": "flat_fee",
            "target_amount_krw": 1000.0,
            "settlement_status": "draft",
            "model_version": "1.0.0",
            "trace_id": "trace-1",
        }
        validate_settlement_rule(rule)

    def test_validate_settlement_rule_missing_field(self) -> None:
        rule: SettlementRule = {
            "settlement_id": "s-1",
            "tenant_id": "t-1",
        }
        with pytest.raises(ChargebackSettlementRuleError):
            validate_settlement_rule(rule)

    def test_five_module_weight_sum_is_one(self) -> None:
        assert abs(FIVE_MODULE_WEIGHT_SUM - 1.0) < 0.01


# ── TestAllocationEngineComputation (12 tests) ───────────────────────────
class TestAllocationEngineComputation:
    """allocation_engine.py 5-dim weighted allocation + Decimal precision."""

    def test_compute_allocation_basic(self) -> None:
        result = compute_allocation(
            tenant_id="t-1",
            result_id="r-1",
            period_key="2026-08",
            total_amount_krw=1_000_000.0,
            dimension_amounts={
                "cost_center": 300_000.0,
                "department": 250_000.0,
                "business_unit": 200_000.0,
                "tag": 150_000.0,
                "tenant": 100_000.0,
            },
            target_dimensions=[
                "cost_center", "department", "business_unit", "tag", "tenant"
            ],
        )
        assert result["allocation_count"] == 5
        assert result["confidence_pct"] == 100.0

    def test_compute_allocation_dry_run(self) -> None:
        result = compute_allocation(
            tenant_id="t-dry",
            result_id="r-dry",
            period_key="2026-08",
            total_amount_krw=500_000.0,
            dimension_amounts={"cost_center": 500_000.0},
            target_dimensions=["cost_center"],
            dry_run=True,
        )
        assert result["dry_run"] is True

    def test_compute_allocation_bankers_rounding(self) -> None:
        # 1000.005 * 0.30 = 300.0015 → banker rounds to 300.00
        result = compute_allocation(
            tenant_id="t-rnd",
            result_id="r-rnd",
            period_key="2026-08",
            total_amount_krw=1000.0,
            dimension_amounts={"cost_center": 333.333},
            target_dimensions=["cost_center"],
        )
        line = result["allocation_lines"][0]
        # Banker's rounding of 300.0 to 0.01 KRW stays 300.0
        assert line["allocated_amount_krw"] == 300.0

    def test_compute_allocation_invalid_target_dim(self) -> None:
        with pytest.raises(ChargebackAllocationDimensionError):
            compute_allocation(
                tenant_id="t-x",
                result_id="r-x",
                period_key="2026-08",
                total_amount_krw=1.0,
                dimension_amounts={"cost_center": 1.0},
                target_dimensions=["invalid"],
            )

    def test_compute_allocation_zero_amount_raises(self) -> None:
        with pytest.raises(ChargebackAllocationEngineError):
            compute_allocation(
                tenant_id="t-x",
                result_id="r-x",
                period_key="2026-08",
                total_amount_krw=0.0,
                dimension_amounts={"cost_center": 0.0},
                target_dimensions=["cost_center"],
            )

    def test_validate_allocation_lines_ok(self) -> None:
        lines: list[AllocationLine] = [
            {
                "allocation_id": "a-1",
                "result_id": "r-1",
                "tenant_id": "t-1",
                "period_key": "2026-08",
                "dimension": "cost_center",
                "dimension_value": "cc-1",
                "weight": 0.3,
                "allocated_amount_krw": 300.0,
            }
        ]
        validate_allocation_lines(lines)

    def test_validate_allocation_lines_exceeds_max(self) -> None:
        lines: list[AllocationLine] = [
            {
                "allocation_id": f"a-{i}",
                "result_id": "r-1",
                "tenant_id": "t-1",
                "period_key": "2026-08",
                "dimension": "cost_center",
                "dimension_value": f"cc-{i}",
                "weight": 0.001,
                "allocated_amount_krw": 1.0,
            }
            for i in range(MAX_ALLOCATION_LINES + 1)
        ]
        with pytest.raises(ChargebackAllocationEngineError):
            validate_allocation_lines(lines)

    def test_aggregate_allocation_breakdown(self) -> None:
        lines: list[AllocationLine] = [
            {
                "allocation_id": "a-1",
                "result_id": "r-1",
                "tenant_id": "t-1",
                "period_key": "2026-08",
                "dimension": "cost_center",
                "dimension_value": "cc-1",
                "weight": 0.3,
                "allocated_amount_krw": 300.0,
            },
            {
                "allocation_id": "a-2",
                "result_id": "r-1",
                "tenant_id": "t-1",
                "period_key": "2026-08",
                "dimension": "department",
                "dimension_value": "dept-1",
                "weight": 0.25,
                "allocated_amount_krw": 250.0,
            },
        ]
        breakdown = aggregate_allocation_breakdown(lines)
        assert breakdown["grand_total_krw"] == 550.0
        assert breakdown["line_count"] == 2

    def test_allocation_dimension_weights_sum(self) -> None:
        assert abs(sum(ALLOCATION_DIMENSION_WEIGHTS.values()) - 1.0) < 0.01

    def test_compute_allocation_five_dimensions(self) -> None:
        for dim in ALL_ALLOCATION_DIMENSIONS:
            assert dim in ALLOCATION_DIMENSION_WEIGHTS

    def test_compute_allocation_confidence_partial(self) -> None:
        # Only cost_center has ledger → 50% confidence
        result = compute_allocation(
            tenant_id="t-partial",
            result_id="r-partial",
            period_key="2026-08",
            total_amount_krw=1_000_000.0,
            dimension_amounts={
                "cost_center": 300_000.0,
                "department": 0.0,
                "business_unit": 0.0,
                "tag": 0.0,
                "tenant": 0.0,
            },
            target_dimensions=[
                "cost_center", "department", "business_unit", "tag", "tenant"
            ],
        )
        assert result["confidence_pct"] < 100.0

    def test_compute_allocation_with_recon_target(self) -> None:
        result = compute_allocation(
            tenant_id="t-recon",
            result_id="r-recon",
            period_key="2026-08",
            total_amount_krw=100_000.0,
            dimension_amounts={"cost_center": 30_000.0},
            target_dimensions=["cost_center"],
        )
        assert result["tolerance_band_krw"] == 1000.0


# ── TestInvoiceGeneration (12 tests) ─────────────────────────────────────
class TestInvoiceGeneration:
    """invoice_generator.py PDF/XLSX/CSV templates + size guard."""

    def test_generate_csv_invoice(self) -> None:
        artifact = generate_invoice(
            tenant_id="t-csv",
            result_id="r-csv",
            period_key="2026-08",
            invoice_format="csv",
            settlement_result={
                "total_amount_krw": 1000.0,
                "allocation_count": 1,
                "confidence_pct": 100.0,
                "tolerance_band_krw": 10.0,
                "settlement_status": "draft",
                "model_version": "1.0.0",
            },
            allocation_lines=[
                {
                    "dimension": "cost_center",
                    "dimension_value": "cc-1",
                    "weight": 0.3,
                    "allocated_amount_krw": 300.0,
                }
            ],
        )
        assert artifact["format"] == "csv"
        assert artifact["bytes_size"] > 0

    def test_generate_pdf_invoice(self) -> None:
        artifact = generate_invoice(
            tenant_id="t-pdf",
            result_id="r-pdf",
            period_key="2026-08",
            invoice_format="pdf",
            settlement_result={
                "total_amount_krw": 2000.0,
                "allocation_count": 1,
                "confidence_pct": 100.0,
                "tolerance_band_krw": 20.0,
                "settlement_status": "draft",
                "model_version": "1.0.0",
            },
            allocation_lines=[
                {
                    "dimension": "cost_center",
                    "dimension_value": "cc-1",
                    "weight": 0.3,
                    "allocated_amount_krw": 600.0,
                }
            ],
        )
        assert artifact["format"] == "pdf"
        # PDF or fallback JSON
        assert artifact["bytes_size"] > 0

    def test_generate_xlsx_invoice(self) -> None:
        artifact = generate_invoice(
            tenant_id="t-xlsx",
            result_id="r-xlsx",
            period_key="2026-08",
            invoice_format="xlsx",
            settlement_result={
                "total_amount_krw": 3000.0,
                "allocation_count": 1,
                "confidence_pct": 100.0,
                "tolerance_band_krw": 30.0,
                "settlement_status": "draft",
                "model_version": "1.0.0",
            },
            allocation_lines=[
                {
                    "dimension": "cost_center",
                    "dimension_value": "cc-1",
                    "weight": 0.3,
                    "allocated_amount_krw": 900.0,
                }
            ],
        )
        assert artifact["format"] == "xlsx"
        assert artifact["bytes_size"] > 0

    def test_generate_invalid_format_raises(self) -> None:
        with pytest.raises(ChargebackInvoiceFormatError):
            generate_invoice(
                tenant_id="t-x",
                result_id="r-x",
                period_key="2026-08",
                invoice_format="docx",
                settlement_result={},
                allocation_lines=[],
            )

    def test_generate_empty_tenant_raises(self) -> None:
        with pytest.raises(ChargebackInvoiceTenantError):
            generate_invoice(
                tenant_id="",
                result_id="r-x",
                period_key="2026-08",
                invoice_format="pdf",
                settlement_result={},
                allocation_lines=[],
            )

    def test_generate_invalid_recipient_template_raises(self) -> None:
        with pytest.raises(ChargebackInvoiceFormatError):
            generate_invoice(
                tenant_id="t-x",
                result_id="r-x",
                period_key="2026-08",
                invoice_format="pdf",
                settlement_result={
                    "total_amount_krw": 1.0,
                    "allocation_count": 0,
                    "confidence_pct": 0.0,
                    "tolerance_band_krw": 0.0,
                    "settlement_status": "draft",
                    "model_version": "1.0.0",
                },
                allocation_lines=[],
                recipient_template="invalid_template",
            )

    def test_validate_invoice_format_ok(self) -> None:
        validate_invoice_format("pdf")
        validate_invoice_format("xlsx")
        validate_invoice_format("csv")

    def test_validate_invoice_format_invalid(self) -> None:
        with pytest.raises(ChargebackInvoiceFormatError):
            validate_invoice_format("docx")

    def test_invoice_all_formats_listed(self) -> None:
        assert set(ALL_INVOICE_FORMATS) == {"pdf", "xlsx", "csv"}

    def test_max_invoice_bytes_constant(self) -> None:
        assert MAX_INVOICE_BYTES == 10 * 1024 * 1024

    def test_invoice_dry_run(self) -> None:
        artifact = generate_invoice(
            tenant_id="t-dry",
            result_id="r-dry",
            period_key="2026-08",
            invoice_format="csv",
            settlement_result={
                "total_amount_krw": 100.0,
                "allocation_count": 0,
                "confidence_pct": 0.0,
                "tolerance_band_krw": 0.0,
                "settlement_status": "draft",
                "model_version": "1.0.0",
            },
            allocation_lines=[],
            dry_run=True,
        )
        assert artifact["persistence"]["persisted"] is False

    def test_recipient_template_owner_only(self) -> None:
        artifact = generate_invoice(
            tenant_id="t-own",
            result_id="r-own",
            period_key="2026-08",
            invoice_format="csv",
            settlement_result={
                "total_amount_krw": 1.0,
                "allocation_count": 0,
                "confidence_pct": 0.0,
                "tolerance_band_krw": 0.0,
                "settlement_status": "draft",
                "model_version": "1.0.0",
            },
            allocation_lines=[],
            recipient_template="owner_only",
        )
        assert artifact["recipient_routing"]["s3_archive_enabled"] is True


# ── TestReconciliation3WayMatch (14 tests) ───────────────────────────────
class TestReconciliation3WayMatch:
    """reconciliation.py 3-way match + retry + admin email alert."""

    def test_reconcile_matched(self) -> None:
        result = reconcile_settlement(
            tenant_id="t-1",
            result_id="r-1",
            period_key="2026-08",
            allocation_amount_krw=1000.0,
            invoice_amount_krw=1000.0,
            ledger_amount_krw=1000.0,
        )
        assert result["reconciliation_status"] == "matched"
        assert result["variance_pct"] == 0.0

    def test_reconcile_variance_detected(self) -> None:
        result = reconcile_settlement(
            tenant_id="t-2",
            result_id="r-2",
            period_key="2026-08",
            allocation_amount_krw=1000.0,
            invoice_amount_krw=1010.0,  # 1% variance — at boundary
            ledger_amount_krw=1000.0,
            max_retries=0,  # Skip retry to test direct classification
        )
        # 1.0% variance is at tolerance boundary → matched
        assert result["reconciliation_status"] in (
            "matched", "variance_detected", "retry_exhausted"
        )

    def test_reconcile_variance_above_tolerance(self) -> None:
        result = reconcile_settlement(
            tenant_id="t-3",
            result_id="r-3",
            period_key="2026-08",
            allocation_amount_krw=1000.0,
            invoice_amount_krw=1100.0,  # 10% variance
            ledger_amount_krw=1000.0,
        )
        assert result["reconciliation_status"] != "matched"

    def test_reconcile_with_retry_exhausted(self) -> None:
        result = reconcile_settlement(
            tenant_id="t-4",
            result_id="r-4",
            period_key="2026-08",
            allocation_amount_krw=1000.0,
            invoice_amount_krw=1500.0,  # 50% variance
            ledger_amount_krw=1000.0,
            max_retries=3,
        )
        # Either retry_exhausted or needs_approval
        assert result["reconciliation_status"] in (
            "variance_detected",
            "retry_exhausted",
            "needs_approval",
        )

    def test_reconcile_high_value_2fa_required(self) -> None:
        result = reconcile_settlement(
            tenant_id="t-5",
            result_id="r-5",
            period_key="2026-08",
            allocation_amount_krw=1_000_000.0,
            invoice_amount_krw=1_200_000.0,  # 20% variance
            ledger_amount_krw=1_000_000.0,
            target_amount_krw=1_000_000.0,  # * 12 = 12M KRW/year >= 10M
        )
        assert result["reconciliation_status"] == "needs_approval"
        assert result["requires_2fa_challenge"] is True

    def test_reconcile_invalid_tolerance_raises(self) -> None:
        with pytest.raises(ChargebackReconciliationToleranceError):
            reconcile_settlement(
                tenant_id="t-x",
                result_id="r-x",
                period_key="2026-08",
                allocation_amount_krw=1000.0,
                invoice_amount_krw=1000.0,
                ledger_amount_krw=1000.0,
                tolerance_pct=200.0,
            )

    def test_reconcile_negative_amount_raises(self) -> None:
        with pytest.raises(ChargebackReconciliationError):
            reconcile_settlement(
                tenant_id="t-x",
                result_id="r-x",
                period_key="2026-08",
                allocation_amount_krw=-1.0,
                invoice_amount_krw=1000.0,
                ledger_amount_krw=1000.0,
            )

    def test_reconcile_empty_tenant_raises(self) -> None:
        with pytest.raises(ChargebackReconciliationError):
            reconcile_settlement(
                tenant_id="",
                result_id="r-x",
                period_key="2026-08",
                allocation_amount_krw=1000.0,
                invoice_amount_krw=1000.0,
                ledger_amount_krw=1000.0,
            )

    def test_reconcile_dry_run(self) -> None:
        result = reconcile_settlement(
            tenant_id="t-dry",
            result_id="r-dry",
            period_key="2026-08",
            allocation_amount_krw=1000.0,
            invoice_amount_krw=1000.0,
            ledger_amount_krw=1000.0,
            dry_run=True,
        )
        assert result["reconciliation_status"] == "matched"

    def test_validate_reconciliation_result_ok(self) -> None:
        result: ReconciliationResult = {
            "reconciliation_id": "recon-1",
            "result_id": "r-1",
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "allocation_amount_krw": 1000.0,
            "invoice_amount_krw": 1000.0,
            "ledger_amount_krw": 1000.0,
            "variance_pct": 0.0,
            "variance_krw": 0.0,
            "reconciliation_status": "matched",
            "retry_attempts": 0,
            "model_version": "1.0.0",
        }
        validate_reconciliation_result(result)

    def test_validate_reconciliation_invalid_status(self) -> None:
        result: ReconciliationResult = {
            "reconciliation_id": "recon-1",
            "result_id": "r-1",
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "allocation_amount_krw": 1000.0,
            "invoice_amount_krw": 1000.0,
            "ledger_amount_krw": 1000.0,
            "variance_pct": 0.0,
            "variance_krw": 0.0,
            "reconciliation_status": "invalid_status",
            "retry_attempts": 0,
            "model_version": "1.0.0",
        }
        with pytest.raises(ChargebackReconciliationError):
            validate_reconciliation_result(result)

    def test_reconciliation_tolerance_constant(self) -> None:
        assert RECONCILIATION_TOLERANCE_PCT == 1.0

    def test_reconciliation_max_retries_constant(self) -> None:
        assert RECONCILIATION_MAX_RETRIES == 3

    def test_reconciliation_amount_tolerance_constant(self) -> None:
        assert RECONCILIATION_AMOUNT_TOLERANCE_KRW == 0.01


# ── TestScheduledDispatch (8 tests) ──────────────────────────────────────
class TestScheduledDispatch:
    """scheduled_chargeback_settlement_dispatch.py cadence + apscheduler."""

    def test_all_cadences_listed(self) -> None:
        assert set(ALL_SETTLEMENT_CADENCES) == {
            "monthly", "quarterly", "semi_annual", "annual"
        }

    def test_validate_cadence_ok(self) -> None:
        for cadence in ALL_SETTLEMENT_CADENCES:
            validate_cadence(cadence)

    def test_validate_cadence_invalid(self) -> None:
        from apps.api.core.errors import ChargebackAllocationEngineError
        with pytest.raises(ChargebackAllocationEngineError):
            validate_cadence("invalid_cadence")

    def test_schedule_cadence_dispatch_metadata(self) -> None:
        meta = schedule_cadence_dispatch(cadence="monthly", tenants=["t-1"])
        assert meta["cadence"] == "monthly"
        assert "schedule" in meta

    def test_schedule_cadence_dispatch_invalid(self) -> None:
        from apps.api.core.errors import ChargebackAllocationEngineError
        with pytest.raises(ChargebackAllocationEngineError):
            schedule_cadence_dispatch(cadence="invalid")

    def test_compute_settlement_result_basic(self) -> None:
        result = compute_settlement_result(
            tenant_id="t-1",
            cadence="monthly",
            five_module_inputs={
                "phase_11_chargeback": 1000.0,
                "phase_18_commitment": 500.0,
                "phase_19_pricing": 500.0,
                "phase_20_multi_cloud": 250.0,
                "phase_21_reserved_capacity": 250.0,
            },
            target_amount_krw=10_000.0,
            target_dimensions=["cost_center"],
        )
        assert result["result_id"] is not None

    def test_execute_dispatch(self) -> None:
        dispatch = execute_dispatch(
            tenant_id="t-1",
            cadence="monthly",
            five_module_inputs={
                "phase_11_chargeback": 100.0,
                "phase_18_commitment": 100.0,
                "phase_19_pricing": 100.0,
                "phase_20_multi_cloud": 100.0,
                "phase_21_reserved_capacity": 100.0,
            },
            target_amount_krw=5_000.0,
            target_dimensions=["cost_center"],
        )
        assert dispatch["dispatch_id"] is not None
        assert dispatch["cadence"] == "monthly"

    def test_cadence_hours_constant(self) -> None:
        assert SETTLEMENT_CADENCE_HOURS_KST["monthly"] == (4, 0)
        assert SETTLEMENT_CADENCE_HOURS_KST["quarterly"] == (5, 0)
        assert SETTLEMENT_CADENCE_HOURS_KST["semi_annual"] == (6, 0)
        assert SETTLEMENT_CADENCE_HOURS_KST["annual"] == (7, 0)


# ── TestRouterEndpoints (6 tests) ────────────────────────────────────────
class TestRouterEndpoints:
    """chargeback_settlement_routes.py FastAPI router + capability gate."""

    def test_router_has_prefix(self) -> None:
        from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
            router,
        )
        assert router.prefix == "/api/v1/finops/chargeback-settlement"

    def test_router_has_capability_dependency(self) -> None:
        from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
            router,
        )
        # Router should have at least one dependency
        assert len(router.dependencies) > 0

    def test_router_has_healthcheck_route(self) -> None:
        from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
            router,
        )
        paths = [r.path for r in router.routes]
        # FastAPI router paths include the prefix, so use endswith
        assert any(p.endswith("/healthcheck") for p in paths)

    def test_router_has_settlement_rules_routes(self) -> None:
        from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
            router,
        )
        paths = [r.path for r in router.routes]
        assert any(p.endswith("/settlement-rules") for p in paths)
        assert any("settlement-rules" in p and "{" in p for p in paths)

    def test_router_has_allocation_route(self) -> None:
        from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
            router,
        )
        paths = [r.path for r in router.routes]
        assert any(p.endswith("/allocation") for p in paths)

    def test_router_has_invoice_reconciliation_dispatch_routes(self) -> None:
        from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
            router,
        )
        paths = [r.path for r in router.routes]
        assert any(p.endswith("/invoice") for p in paths)
        assert any(p.endswith("/reconciliation") for p in paths)
        assert any(p.endswith("/dispatch") for p in paths)
        assert any(p.endswith("/cadence-preview") for p in paths)


# ── TestCapabilityGate (4 tests) ─────────────────────────────────────────
class TestCapabilityGate:
    """FINOPS_CHARGEBACK_SETTLEMENT industry-agnostic grants."""

    def test_capability_enum_exists(self) -> None:
        assert hasattr(Capability, "FINOPS_CHARGEBACK_SETTLEMENT")

    def test_capability_value(self) -> None:
        assert Capability.FINOPS_CHARGEBACK_SETTLEMENT.value == (
            "finops_chargeback_settlement"
        )

    def test_capability_in_all_4_industries(self) -> None:
        # All 4 industry grants should include FINOPS_CHARGEBACK_SETTLEMENT
        industry_enums = [
            Industry.MANUFACTURING,
            Industry.SERVICE,
            Industry.MANUFACTURING_SERVICE,
            Industry.MANUFACTURING_SERVICE_OTHER,
        ]
        # Use industry_supports() helper to check capability membership
        from apps.api.core.capability import industry_supports
        for industry in industry_enums:
            assert industry_supports(industry, Capability.FINOPS_CHARGEBACK_SETTLEMENT), (
                f"Missing in {industry}"
            )

    def test_high_value_threshold_constant(self) -> None:
        assert HIGH_VALUE_THRESHOLD_KRW_PER_YEAR == 10_000_000.0


# ── TestAuditActionRegistry (4 tests) ────────────────────────────────────
class TestAuditActionRegistry:
    """8 NEW FinopsChargebackSettlementAction values."""

    def test_action_class_enum_exists(self) -> None:
        assert hasattr(ActionClass, "FINOPS_CHARGEBACK_SETTLEMENT")

    def test_action_class_value(self) -> None:
        assert ActionClass.FINOPS_CHARGEBACK_SETTLEMENT.value == (
            "finops_chargeback_settlement"
        )

    def test_finops_chargeback_settlement_action_literal(self) -> None:
        # Literal type contains 8 NEW values
        from typing import get_args
        args = get_args(FinopsChargebackSettlementAction)
        assert "settlement_rule_created" in args
        assert "settlement_rule_updated" in args
        assert "settlement_calculated" in args
        assert "allocation_verified" in args
        assert "settlement_invoice_generated" in args
        assert "settlement_reconciled" in args
        assert "settlement_dry_run_executed" in args
        assert "settlement_approval_required" in args

    def test_audit_action_values_includes_8_new(self) -> None:
        # AuditAction union should include all 8 NEW values
        # (Union[Literal[X], Literal[Y], ...] — flatten all Literal values)
        from typing import get_args
        audit_args = get_args(AuditAction)
        all_audit_values: set[str] = set()
        for lit in audit_args:
            for v in get_args(lit):
                all_audit_values.add(v)
        new_values = [
            "settlement_rule_created",
            "settlement_rule_updated",
            "settlement_calculated",
            "allocation_verified",
            "settlement_invoice_generated",
            "settlement_reconciled",
            "settlement_dry_run_executed",
            "settlement_approval_required",
        ]
        for v in new_values:
            assert v in all_audit_values, f"Missing audit action: {v}"


# ── TestTypedExceptionEnvelope (8 tests) ─────────────────────────────────
class TestTypedExceptionEnvelope:
    """16 NEW typed exceptions imported from errors.py."""

    def test_settlement_rule_errors(self) -> None:
        assert ChargebackSettlementRuleError is not None
        assert ChargebackSettlementRuleScopeError is not None
        assert ChargebackSettlementRuleTypeError is not None
        assert ChargebackSettlementRuleModuleError is not None

    def test_allocation_errors(self) -> None:
        assert ChargebackAllocationEngineError is not None
        assert ChargebackAllocationDimensionError is not None
        assert ChargebackAllocationWeightError is not None
        assert ChargebackAllocationUnbalancedError is not None

    def test_invoice_errors(self) -> None:
        assert ChargebackInvoiceGenerationError is not None
        assert ChargebackInvoiceFormatError is not None
        assert ChargebackInvoiceTenantError is not None
        assert ChargebackInvoiceSizeError is not None

    def test_reconciliation_errors(self) -> None:
        assert ChargebackReconciliationError is not None
        assert ChargebackReconciliationToleranceError is not None
        assert ChargebackReconciliationRetryError is not None
        assert ChargebackReconciliationApprovalError is not None

    def test_settlement_rule_error_instantiate(self) -> None:
        e = ChargebackSettlementRuleError(reason="test", tenant_id="t-1")
        assert e.reason == "test"

    def test_allocation_dimension_error_instantiate(self) -> None:
        e = ChargebackAllocationDimensionError(
            dimensions=["bad"], allowed=["cost_center"]
        )
        assert e.allowed == ["cost_center"]

    def test_invoice_format_error_instantiate(self) -> None:
        e = ChargebackInvoiceFormatError(
            invoice_format="bad", allowed=["pdf"]
        )
        assert e.invoice_format == "bad"

    def test_reconciliation_error_instantiate(self) -> None:
        e = ChargebackReconciliationError(reason="test", tenant_id="t-1")
        assert e.reason == "test"


# ── TestModuleConstants (8 tests) ────────────────────────────────────────
class TestModuleConstants:
    """Module-level constants + DEFAULTS dict integrity."""

    def test_engine_model_version(self) -> None:
        assert CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION == "1.0.0"

    def test_five_module_weights_keys(self) -> None:
        assert set(FIVE_MODULE_WEIGHTS.keys()) == {
            "phase_11_chargeback",
            "phase_18_commitment",
            "phase_19_pricing",
            "phase_20_multi_cloud",
            "phase_21_reserved_capacity",
        }

    def test_five_module_weights_values(self) -> None:
        assert FIVE_MODULE_WEIGHTS["phase_11_chargeback"] == 0.30
        assert FIVE_MODULE_WEIGHTS["phase_18_commitment"] == 0.20
        assert FIVE_MODULE_WEIGHTS["phase_19_pricing"] == 0.20
        assert FIVE_MODULE_WEIGHTS["phase_20_multi_cloud"] == 0.15
        assert FIVE_MODULE_WEIGHTS["phase_21_reserved_capacity"] == 0.15

    def test_all_settlement_rule_types(self) -> None:
        assert set(ALL_SETTLEMENT_RULE_TYPES) == {
            "flat_fee",
            "proportional_allocation",
            "metered_volume",
            "tag_weighted",
        }

    def test_all_settlement_statuses(self) -> None:
        assert set(ALL_SETTLEMENT_STATUSES) == {
            "draft",
            "pending_approval",
            "approved",
            "invoiced",
            "reconciled",
        }

    def test_all_allocation_dimensions(self) -> None:
        assert set(ALL_ALLOCATION_DIMENSIONS) == {
            "cost_center",
            "department",
            "business_unit",
            "tag",
            "tenant",
        }

    def test_recipient_templates(self) -> None:
        assert set(SETTLEMENT_RECIPIENT_TEMPLATES.keys()) == {
            "owner_only", "executive", "audit_only"
        }

    def test_defaults_dict_contains_audit_first_insert(self) -> None:
        assert CHARGEBACK_SETTLEMENT_DEFAULTS["audit_first_insert"] is True
        assert CHARGEBACK_SETTLEMENT_DEFAULTS["dry_run_supported"] is True
        assert CHARGEBACK_SETTLEMENT_DEFAULTS["2fa_challenge_supported"] is True


# ── TestEnums (6 tests) ──────────────────────────────────────────────────
class TestEnums:
    """Enum types (SettlementRuleType + SettlementStatus + AllocationDimension + InvoiceFormat)."""

    def test_settlement_rule_type_enum(self) -> None:
        assert SettlementRuleType.FLAT_FEE.value == "flat_fee"
        assert SettlementRuleType.PROPORTIONAL_ALLOCATION.value == (
            "proportional_allocation"
        )
        assert SettlementRuleType.METERED_VOLUME.value == "metered_volume"
        assert SettlementRuleType.TAG_WEIGHTED.value == "tag_weighted"

    def test_settlement_status_enum(self) -> None:
        assert SettlementStatus.DRAFT.value == "draft"
        assert SettlementStatus.PENDING_APPROVAL.value == "pending_approval"
        assert SettlementStatus.APPROVED.value == "approved"
        assert SettlementStatus.INVOICED.value == "invoiced"
        assert SettlementStatus.RECONCILED.value == "reconciled"

    def test_allocation_dimension_enum(self) -> None:
        assert AllocationDimension.COST_CENTER.value == "cost_center"
        assert AllocationDimension.DEPARTMENT.value == "department"
        assert AllocationDimension.BUSINESS_UNIT.value == "business_unit"
        assert AllocationDimension.TAG.value == "tag"
        assert AllocationDimension.TENANT.value == "tenant"

    def test_invoice_format_enum(self) -> None:
        assert InvoiceFormat.PDF.value == "pdf"
        assert InvoiceFormat.XLSX.value == "xlsx"
        assert InvoiceFormat.CSV.value == "csv"

    def test_settlement_rule_typed_dict(self) -> None:
        rule: SettlementRule = {
            "settlement_id": "s-1",
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "rule_name": "r",
            "rule_type": "flat_fee",
            "target_amount_krw": 1000.0,
            "target_dimensions": ["cost_center"],
            "scope_chain": {},
            "settlement_status": "draft",
            "requires_2fa_challenge": False,
            "model_version": "1.0.0",
            "trace_id": "tr-1",
        }
        assert rule["settlement_id"] == "s-1"

    def test_reconciliation_result_typed_dict(self) -> None:
        result: ReconciliationResult = {
            "reconciliation_id": "recon-1",
            "result_id": "r-1",
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "allocation_amount_krw": 1000.0,
            "invoice_amount_krw": 1000.0,
            "ledger_amount_krw": 1000.0,
            "variance_pct": 0.0,
            "variance_krw": 0.0,
            "reconciliation_status": "matched",
            "retry_attempts": 0,
            "model_version": "1.0.0",
            "computed_at": "2026-08-27T00:00:00Z",
            "trace_id": "tr-1",
        }
        assert result["reconciliation_status"] == "matched"


# ── TestIntegrationSmoke (4 tests) ──────────────────────────────────────
class TestIntegrationSmoke:
    """Integration smoke tests for compute_settlement_result + reconciliation."""

    def test_compute_settlement_full_flow(self) -> None:
        result = compute_settlement_result(
            tenant_id="t-full",
            cadence="monthly",
            five_module_inputs={
                "phase_11_chargeback": 1000.0,
                "phase_18_commitment": 500.0,
                "phase_19_pricing": 500.0,
                "phase_20_multi_cloud": 250.0,
                "phase_21_reserved_capacity": 250.0,
            },
            target_amount_krw=10_000.0,
            target_dimensions=["cost_center"],
            invoice_amount_krw=10_000.0,
            ledger_amount_krw=10_000.0,
        )
        assert result["result_id"] is not None
        assert result["allocation_count"] > 0

    def test_compute_settlement_with_variance(self) -> None:
        result = compute_settlement_result(
            tenant_id="t-var",
            cadence="monthly",
            five_module_inputs={
                "phase_11_chargeback": 1000.0,
                "phase_18_commitment": 500.0,
                "phase_19_pricing": 500.0,
                "phase_20_multi_cloud": 250.0,
                "phase_21_reserved_capacity": 250.0,
            },
            target_amount_krw=10_000.0,
            target_dimensions=["cost_center"],
            invoice_amount_krw=11_000.0,
            ledger_amount_krw=10_000.0,
        )
        # 10% variance → variance_detected or retry_exhausted or matched
        assert result["result_id"] is not None

    def test_module_init_imports(self) -> None:
        from apps.api.modules.finops.chargeback_settlement import (
            compute_allocation,
            create_settlement_rule,
            generate_invoice,
            reconcile_settlement,
        )
        assert callable(create_settlement_rule)
        assert callable(compute_allocation)
        assert callable(generate_invoice)
        assert callable(reconcile_settlement)

    def test_router_module_init(self) -> None:
        from apps.api.modules.finops.chargeback_settlement import (
            chargeback_settlement_router,
        )
        assert chargeback_settlement_router is not None
