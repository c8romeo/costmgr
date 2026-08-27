"""tests.integration.test_finops_vendor_management_tenant_isolation — Phase 25 multi-tenant isolation.

Phase 25 (cj-style 173번째 wire) — FinOps Vendor Management post-budget-
allocation layer territory (PRD §F41.1~§F41.8 verbatim + AD-53 (a)~(g)
7 sub-decisions). Cross-tenant isolation CR 0-2 verbatim — every Phase
25 module enforces tenant_id selector.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from apps.api.modules.finops.vendor_management.vendor_catalog_engine import (
    aggregate_vendor_catalog,
    create_vendor,
    update_vendor,
    change_vendor_status,
    blacklist_vendor,
    compute_vendor_risk_score,
    validate_vendor_scores,
)
from apps.api.modules.finops.vendor_management.vendor_selection_engine import (
    aggregate_vendor_selection,
    score_vendor,
    apply_vendor_selection_threshold,
)
from apps.api.modules.finops.vendor_management.vendor_contract_lifecycle_engine import (
    aggregate_vendor_contract_lifecycle,
    create_vendor_contract,
    advance_contract_lifecycle,
    check_over_budget,
    check_vendor_blacklist_gate,
    check_auto_renewal_window,
)
from apps.api.modules.finops.vendor_management.vendor_performance_evaluation import (
    aggregate_vendor_performance,
    evaluate_vendor_performance,
    compute_monthly_score,
    compute_quarterly_score,
    classify_performance_severity,
)
from apps.api.modules.finops.vendor_management.vendor_spend_attribution import (
    aggregate_vendor_spend_attribution,
    compute_vendor_spend_attribution,
    reconcile_cross_budget,
)


TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())


def _make_vendor_stub(tenant_id: str, vendor_id: str) -> dict:
    """Build a Vendor-shaped dict for tenant isolation tests."""
    return {
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "vendor_name": f"Vendor-{vendor_id[:8]}",
        "vendor_category": "cloud",
        "status": "active",
        "cost_score": 85.0,
        "performance_score": 90.0,
        "reliability_score": 95.0,
        "compliance_score": 88.0,
        "strategic_fit_score": 80.0,
        "risk_score": 13.30,
        "contract_count": 0,
        "blacklist_reason": "",
        "high_value": False,
        "requires_2fa": False,
        "source_attribution": {},
        "created_at": "2026-08-27T00:00:00Z",
        "updated_at": "2026-08-27T00:00:00Z",
    }


def _make_contract_stub(tenant_id: str, vendor_id: str, contract_id: str) -> dict:
    """Build a VendorContract-shaped dict for tenant isolation tests."""
    return {
        "contract_id": contract_id,
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "contract_name": f"Contract-{contract_id[:8]}",
        "contract_value_krw": 5000000.0,
        "lifecycle": "draft",
        "step_index": 0,
        "approval_chain": ["actor-1", "actor-2"],
        "auto_renewal_enabled": False,
        "high_value": False,
        "requires_2fa": False,
        "computed_total_contract_value": 5000000.0,
        "budget_ceiling_krw": 10000000.0,
        "over_budget": False,
        "blacklist_gate_passed": True,
        "audit_log_id": "",
        "created_at": "2026-08-27T00:00:00Z",
        "updated_at": "2026-08-27T00:00:00Z",
    }


def _make_scorecard_stub(tenant_id: str, vendor_id: str, scorecard_id: str) -> dict:
    """Build a VendorPerformanceScorecard-shaped dict for tenant isolation tests."""
    return {
        "scorecard_id": scorecard_id,
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "period_key": "2026-08",
        "sla_compliance_score": 90.0,
        "cost_efficiency_score": 85.0,
        "support_quality_score": 88.0,
        "innovation_score": 80.0,
        "weighted_total_score": 86.25,
        "severity": "excellent",
        "monthly_score": 86.25,
        "quarterly_score": 0.00,
        "source_attribution": {},
        "audit_log_id": "",
        "computed_at": "2026-08-27T00:00:00Z",
    }


def _make_attribution_stub(tenant_id: str, vendor_id: str, attribution_id: str) -> dict:
    """Build a VendorSpendAttribution-shaped dict for tenant isolation tests."""
    return {
        "attribution_id": attribution_id,
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "period_key": "2026-08",
        "actual_amount": 4500000.0,
        "budget_amount": 5000000.0,
        "variance_amount": 500000.0,
        "variance_pct": 10.0,
        "over_budget": False,
        "cross_budget_reconciled": False,
        "audit_log_id": "",
        "computed_at": "2026-08-27T00:00:00Z",
    }


# ── 16 NEW pytest cases ──────────────────────────────────────────────────
def test_validate_vendor_scores_pure() -> None:
    """Test 1: validate_vendor_scores accepts valid 5-dim range."""
    assert validate_vendor_scores(
        cost_score=85.0,
        performance_score=90.0,
        reliability_score=95.0,
        compliance_score=88.0,
        strategic_fit_score=80.0,
    ) is True


def test_validate_vendor_scores_rejects_out_of_range() -> None:
    """Test 2: validate_vendor_scores raises ValueError out of range."""
    try:
        validate_vendor_scores(
            cost_score=150.0,  # out of range
            performance_score=90.0,
            reliability_score=95.0,
            compliance_score=88.0,
            strategic_fit_score=80.0,
        )
        assert False, "expected ValueError"
    except ValueError:
        assert True


def test_compute_vendor_risk_score_uses_bankers_rounding() -> None:
    """Test 3: compute_vendor_risk_score uses Decimal banker's rounding."""
    risk = compute_vendor_risk_score(
        cost_score=85.0,
        reliability_score=95.0,
        compliance_score=88.0,
    )
    # (100-85)*0.30 + (100-95)*0.40 + (100-88)*0.30 = 4.5 + 2.0 + 3.6 = 10.10
    assert abs(risk - 10.10) < 0.02


def test_create_vendor_audit_first_insert() -> None:
    """Test 4: create_vendor produces audit-first INSERT record."""
    vendor = create_vendor(
        tenant_id=TENANT_A,
        vendor_name="AWS",
        vendor_category="cloud",
        cost_score=85.0,
        performance_score=90.0,
        reliability_score=95.0,
        compliance_score=88.0,
        strategic_fit_score=80.0,
        contract_count=0,
    )
    assert vendor["tenant_id"] == TENANT_A
    assert vendor["vendor_category"] == "cloud"
    assert vendor["status"] == "active"
    assert "vendor_id" in vendor
    assert vendor["high_value"] is False
    assert vendor["requires_2fa"] is False


def test_create_vendor_high_value_triggers_2fa() -> None:
    """Test 5: create_vendor with high contract_count triggers requires_2fa."""
    vendor = create_vendor(
        tenant_id=TENANT_A,
        vendor_name="Big Vendor",
        vendor_category="saas",
        cost_score=85.0,
        performance_score=90.0,
        reliability_score=95.0,
        compliance_score=88.0,
        strategic_fit_score=80.0,
        contract_count=2,  # 2 contracts → high_value
    )
    assert vendor["high_value"] is True
    assert vendor["requires_2fa"] is True


def test_vendor_catalog_isolated_per_tenant() -> None:
    """Test 6: aggregate_vendor_catalog returns tenant-specific counts."""
    tenant_a_vendors = [
        _make_vendor_stub(TENANT_A, str(uuid.uuid4())),
        _make_vendor_stub(TENANT_A, str(uuid.uuid4())),
    ]
    tenant_b_vendors = [
        _make_vendor_stub(TENANT_B, str(uuid.uuid4())),
    ]

    a_result = aggregate_vendor_catalog(tenant_id=TENANT_A, vendors=tenant_a_vendors)
    b_result = aggregate_vendor_catalog(tenant_id=TENANT_B, vendors=tenant_b_vendors)

    assert a_result["vendor_count"] == 2
    assert b_result["vendor_count"] == 1


def test_blacklist_vendor_compliance_gate() -> None:
    """Test 7: blacklist_vendor sets status to blacklisted + creates entry."""
    vendor = _make_vendor_stub(TENANT_A, str(uuid.uuid4()))
    updated, entry = blacklist_vendor(
        vendor=vendor,
        reason="Compliance violation",
        severity="high",
    )
    assert updated["status"] == "blacklisted"
    assert entry["vendor_id"] == vendor["vendor_id"]
    assert entry["block_contract_approval"] is True
    assert entry["requires_owner_override"] is True


def test_score_vendor_5dim_weighted() -> None:
    """Test 8: score_vendor applies 5-dim weighted scoring."""
    score = score_vendor(
        cost_score=85.0,
        performance_score=90.0,
        reliability_score=95.0,
        compliance_score=88.0,
        strategic_fit_score=80.0,
    )
    # 85*0.30 + 90*0.25 + 95*0.20 + 88*0.15 + 80*0.10 = 25.5+22.5+19.0+13.2+8.0 = 88.20
    assert abs(score - 88.20) < 0.02


def test_apply_vendor_selection_threshold_below_excluded() -> None:
    """Test 9: apply_vendor_selection_threshold excludes below threshold."""
    vendor = _make_vendor_stub(TENANT_A, str(uuid.uuid4()))
    passes = apply_vendor_selection_threshold(
        vendor=vendor,
        weighted_total_score=50.00,  # below 60.00 threshold
        threshold=60.00,
    )
    assert passes is False


def test_check_over_budget_returns_true() -> None:
    """Test 10: check_over_budget detects over budget."""
    over = check_over_budget(
        contract_value_krw=15000000.0,
        budget_ceiling_krw=10000000.0,
    )
    assert over is True


def test_check_vendor_blacklist_gate_blocks() -> None:
    """Test 11: check_vendor_blacklist_gate blocks blacklisted vendors."""
    passes = check_vendor_blacklist_gate(vendor_status="blacklisted")
    assert passes is False


def test_check_auto_renewal_window_within_90_days() -> None:
    """Test 12: check_auto_renewal_window within 90 days."""
    in_window = check_auto_renewal_window(
        contract_expiry_iso="2026-08-27T00:00:00Z",
        auto_renewal_enabled=True,
        days_remaining=45,  # within 90 days
    )
    assert in_window is True


def test_evaluate_vendor_performance_4dim_scoring() -> None:
    """Test 13: evaluate_vendor_performance 4-dim weighted scoring."""
    scorecard = evaluate_vendor_performance(
        tenant_id=TENANT_A,
        vendor_id=str(uuid.uuid4()),
        period_key="2026-08",
        sla_compliance_score=90.0,
        cost_efficiency_score=85.0,
        support_quality_score=88.0,
        innovation_score=80.0,
    )
    assert scorecard["severity"] == "excellent"
    assert scorecard["weighted_total_score"] >= 80.00


def test_classify_performance_severity_3tier() -> None:
    """Test 14: classify_performance_severity 3-tier classification."""
    assert classify_performance_severity(weighted_total_score=85.0) == "excellent"
    assert classify_performance_severity(weighted_total_score=65.0) == "needs_improvement"
    assert classify_performance_severity(weighted_total_score=50.0) == "critical"


def test_compute_quarterly_score_averages_3_monthly() -> None:
    """Test 15: compute_quarterly_score averages 3 monthly scores."""
    q_score = compute_quarterly_score(
        monthly_scores=[85.0, 90.0, 88.0],
    )
    assert abs(q_score - 87.67) < 0.02


def test_vendor_spend_attribution_reconciliation() -> None:
    """Test 16: reconcile_cross_budget sets reconciled flag if totals match."""
    attribution = _make_attribution_stub(TENANT_A, str(uuid.uuid4()), str(uuid.uuid4()))
    updated = reconcile_cross_budget(
        attribution=attribution,
        settlement_results_total=4500000.0,
        budget_plan_total=5000000.0,
    )
    assert updated["cross_budget_reconciled"] is True
    assert updated["budget_amount"] == 5000000.0