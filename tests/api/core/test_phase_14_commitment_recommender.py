"""tests.api.core.test_phase_14_commitment_recommender — Phase 14 commitment recommender tests.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.4). 6 commitment_type + 1y/3y + break-even + ROI.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    BreakEvenCalculationError,
    CommitmentRecommendationError,
)
from apps.api.modules.finops.commitment_recommender import (
    ALL_COMMITMENT_TERMS,
    ALL_COMMITMENT_TYPES,
    ALL_SEVERITIES,
    BREAK_EVEN_THRESHOLD_1Y_MONTHS,
    BREAK_EVEN_THRESHOLD_3Y_MONTHS,
    COMMITMENT_TERM_1_YEAR,
    COMMITMENT_TERM_3_YEAR,
    COMMITMENT_TYPE_EC2_RI,
    COMMITMENT_TYPE_RDS_RI,
    COMMITMENT_TYPE_EC2_SP,
    COMMITMENT_TYPE_S3_SP,
    COMMITMENT_TYPE_REDSHIFT_SP,
    COMMITMENT_TYPE_DYNAMODB_SP,
    RI_SP_DISCOUNT_1Y,
    RI_SP_DISCOUNT_3Y,
    ROI_THRESHOLD_HIGH,
    ROI_THRESHOLD_MEDIUM,
    SEVERITY_HIGH,
    CommitmentRecommendation,
    classify_severity_from_roi,
    compute_break_even_months,
    compute_roi_pct,
    recommend_commitments,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_commitment_types_enum_completeness() -> None:
    """Test 1: 6 commitment_type enum completeness."""
    assert len(ALL_COMMITMENT_TYPES) == 6
    assert COMMITMENT_TYPE_EC2_RI in ALL_COMMITMENT_TYPES
    assert COMMITMENT_TYPE_RDS_RI in ALL_COMMITMENT_TYPES
    assert COMMITMENT_TYPE_EC2_SP in ALL_COMMITMENT_TYPES
    assert COMMITMENT_TYPE_S3_SP in ALL_COMMITMENT_TYPES
    assert COMMITMENT_TYPE_REDSHIFT_SP in ALL_COMMITMENT_TYPES
    assert COMMITMENT_TYPE_DYNAMODB_SP in ALL_COMMITMENT_TYPES


def test_commitment_terms_and_discount_rates() -> None:
    """Test 2: 2 commitment_term + discount rates."""
    assert len(ALL_COMMITMENT_TERMS) == 2
    assert COMMITMENT_TERM_1_YEAR in ALL_COMMITMENT_TERMS
    assert COMMITMENT_TERM_3_YEAR in ALL_COMMITMENT_TERMS
    assert RI_SP_DISCOUNT_1Y == 0.40
    assert RI_SP_DISCOUNT_3Y == 0.60
    assert BREAK_EVEN_THRESHOLD_1Y_MONTHS == 8
    assert BREAK_EVEN_THRESHOLD_3Y_MONTHS == 18


def test_break_even_calculation_valid_inputs() -> None:
    """Test 3: break-even calculation with valid inputs."""
    # upfront 100k, monthly savings 25k → 4 months
    assert compute_break_even_months(100000.0, 25000.0) == 4
    # upfront 800k, monthly savings 100k → 8 months (1y threshold)
    assert compute_break_even_months(800000.0, 100000.0) == 8


def test_break_even_calculation_invalid_inputs() -> None:
    """Test 4: break-even calculation with invalid inputs raises."""
    with pytest.raises(BreakEvenCalculationError):
        compute_break_even_months(-100.0, 1000.0)
    with pytest.raises(BreakEvenCalculationError):
        compute_break_even_months(100.0, 0.0)


def test_roi_calculation_valid() -> None:
    """Test 5: ROI calculation."""
    # upfront 1000k, total_savings 3000k → 200% ROI
    assert compute_roi_pct(3000000.0, 1000000.0) == 200.0
    # upfront 100k, total_savings 50k → -50% ROI
    assert compute_roi_pct(50000.0, 100000.0) == -50.0


def test_classify_severity_from_roi_boundaries() -> None:
    """Test 6: ROI severity classification boundaries."""
    assert classify_severity_from_roi(150.0) == SEVERITY_HIGH
    assert classify_severity_from_roi(100.0) == SEVERITY_HIGH  # boundary
    assert classify_severity_from_roi(75.0) == "medium"
    assert classify_severity_from_roi(50.0) == "medium"  # boundary
    assert classify_severity_from_roi(25.0) == "low"


def test_build_commitment_recommendation_1y() -> None:
    """Test 7: 1-year commitment recommendation shape."""
    from apps.api.modules.finops.commitment_recommender import (
        _build_commitment_recommendation,
    )
    rec = _build_commitment_recommendation(
        tenant_id=TENANT_ID,
        commitment_type=COMMITMENT_TYPE_EC2_RI,
        commitment_term=COMMITMENT_TERM_1_YEAR,
        resource_pattern="m5.large",
        current_on_demand_cost_krw_per_month=200000.0,
        discount_rate=RI_SP_DISCOUNT_1Y,
        upfront_cost_krw=0.0,  # no upfront
    )
    assert rec["tenant_id"] == TENANT_ID
    assert rec["commitment_type"] == COMMITMENT_TYPE_EC2_RI
    assert rec["commitment_term"] == COMMITMENT_TERM_1_YEAR
    assert rec["resource_pattern"] == "m5.large"
    assert rec["current_on_demand_cost_krw_per_month"] == 200000.0
    assert rec["projected_commit_cost_krw_per_month"] == 120000.0  # 0.60 of 200k
    assert rec["projected_savings_pct"] == 40.0  # 0.40 * 100
    assert rec["upfront_cost_krw"] == 0.0
    assert rec["break_even_months"] == 0  # no upfront


def test_build_commitment_recommendation_3y_with_upfront() -> None:
    """Test 8: 3-year commitment with upfront cost + break-even."""
    from apps.api.modules.finops.commitment_recommender import (
        _build_commitment_recommendation,
    )
    rec = _build_commitment_recommendation(
        tenant_id=TENANT_ID,
        commitment_type=COMMITMENT_TYPE_EC2_SP,
        commitment_term=COMMITMENT_TERM_3_YEAR,
        resource_pattern="m5.xlarge",
        current_on_demand_cost_krw_per_month=400000.0,
        discount_rate=RI_SP_DISCOUNT_3Y,
        upfront_cost_krw=1000000.0,
    )
    assert rec["commitment_term"] == COMMITMENT_TERM_3_YEAR
    assert rec["current_on_demand_cost_krw_per_month"] == 400000.0
    assert rec["projected_commit_cost_krw_per_month"] == 160000.0  # 0.40 of 400k
    # monthly_savings = 400k - 160k = 240k
    # break_even = 1000k / 240k = 4 months
    assert rec["break_even_months"] == 4
    assert rec["upfront_cost_krw"] == 1000000.0


# ── enum invariants ─────────────────────────────────────────
def test_enum_invariants() -> None:
    """Test 9: enum invariants + recommend_commitments placeholder."""
    assert len(ALL_COMMITMENT_TYPES) == 6
    assert len(ALL_COMMITMENT_TERMS) == 2
    assert len(ALL_SEVERITIES) == 3
    assert ROI_THRESHOLD_HIGH == 100.0
    assert ROI_THRESHOLD_MEDIUM == 50.0
    assert recommend_commitments(tenant_id=TENANT_ID) == []
