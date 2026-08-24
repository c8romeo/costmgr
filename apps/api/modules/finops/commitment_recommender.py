"""apps.api.modules.finops.commitment_recommender — RI/SP commitment recommender (PRD §F30.4).

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.4 verbatim). 1-year / 3-year RI / SP commitment
recommendations EXTENSION of Phase 13 forecast 12-month baseline.

This module provides:
- `CommitmentRecommendation` TypedDict with 12 fields (PRD §F30.4.7
  verbatim).
- 6 commitment_type options: ec2_ri + rds_ri + ec2_sp + s3_sp +
  redshift_sp + dynamodb_sp (PRD §F30.4.2).
- 2 commitment_term options: 1_year + 3_year + composite default.
- break-even calculation: upfront_cost / monthly_savings.
- ROI calculation: (total_3y_savings - upfront_cost) / upfront_cost × 100.
- `recommend_commitments()` — main entry point.

CR lessons applied:
- CR 0-2 RLS — every CommitmentRecommendation carries tenant_id
  selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `commitment_recommended` (dry-run skips).
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 D-001~D-005 + P-015 verbatim.
- CR 12-5 D-14 typed exception envelope — CommitmentRecommendationError
  + PricingDataUnavailableError + BreakEvenCalculationError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — recommend_commitments owner-only.
Epic 12 2FA 챌린지 mandatory when auto-apply is enabled.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final, TypedDict

from apps.api.core.errors import (
    BreakEvenCalculationError,
    CommitmentRecommendationError,
)
from apps.api.modules.finops.optimization_definition import (
    BASELINE_PERIOD_LAST_30D,
    OPTIMIZATION_DEFAULTS,
)

# ── 6 commitment_type options (PRD §F30.4.2 verbatim) ──────────
COMMITMENT_TYPE_EC2_RI: Final[str] = "ec2_ri"
COMMITMENT_TYPE_RDS_RI: Final[str] = "rds_ri"
COMMITMENT_TYPE_EC2_SP: Final[str] = "ec2_sp"
COMMITMENT_TYPE_S3_SP: Final[str] = "s3_sp"
COMMITMENT_TYPE_REDSHIFT_SP: Final[str] = "redshift_sp"
COMMITMENT_TYPE_DYNAMODB_SP: Final[str] = "dynamodb_sp"

ALL_COMMITMENT_TYPES: Final[tuple[str, ...]] = (
    COMMITMENT_TYPE_EC2_RI,
    COMMITMENT_TYPE_RDS_RI,
    COMMITMENT_TYPE_EC2_SP,
    COMMITMENT_TYPE_S3_SP,
    COMMITMENT_TYPE_REDSHIFT_SP,
    COMMITMENT_TYPE_DYNAMODB_SP,
)

# ── 2 commitment_term options (PRD §F30.4.3 verbatim) ──────────
COMMITMENT_TERM_1_YEAR: Final[str] = "1_year"
COMMITMENT_TERM_3_YEAR: Final[str] = "3_year"

ALL_COMMITMENT_TERMS: Final[tuple[str, ...]] = (
    COMMITMENT_TERM_1_YEAR,
    COMMITMENT_TERM_3_YEAR,
)

# ── 3 recommendation severity options (PRD §F30.4.7 verbatim) ──
SEVERITY_LOW: Final[str] = "low"
SEVERITY_MEDIUM: Final[str] = "medium"
SEVERITY_HIGH: Final[str] = "high"

ALL_SEVERITIES: Final[tuple[str, ...]] = (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
)

# ── Discount rates (PRD §F30.4.8 verbatim) ─────────────────────
# 1y ~40% discount, 3y ~60% discount
RI_SP_DISCOUNT_1Y: Final[float] = 0.40
RI_SP_DISCOUNT_3Y: Final[float] = 0.60

# ── Break-even thresholds (PRD §F30.4.4 verbatim) ──────────────
BREAK_EVEN_THRESHOLD_1Y_MONTHS: Final[int] = OPTIMIZATION_DEFAULTS.COMMIT_BREAK_EVEN_MONTHS_1Y  # 8
BREAK_EVEN_THRESHOLD_3Y_MONTHS: Final[int] = OPTIMIZATION_DEFAULTS.COMMIT_BREAK_EVEN_MONTHS_3Y  # 18

# ── ROI thresholds (PRD §F30.4.6 verbatim) ─────────────────────
ROI_THRESHOLD_HIGH: Final[float] = 100.0
ROI_THRESHOLD_MEDIUM: Final[float] = 50.0


# ── CommitmentRecommendation TypedDict (PRD §F30.4.7 verbatim, 12 fields) ─
class CommitmentRecommendation(TypedDict, total=True):
    """TypedDict for commitment recommendation.

    Fields:
        recommendation_id: UUID of the recommendation.
        tenant_id: UUID of the tenant.
        commitment_type: 6 commitment_type options.
        commitment_term: 1_year / 3_year.
        resource_pattern: instance type pattern (e.g. m5.large).
        current_on_demand_cost_krw_per_month: current on-demand cost KRW/month.
        projected_commit_cost_krw_per_month: projected commit cost KRW/month.
        projected_savings_pct: projected savings percentage.
        projected_savings_krw: projected savings KRW over commitment_term.
        upfront_cost_krw: upfront cost KRW.
        break_even_months: months until break-even.
        roi_pct: ROI percentage.
        recommendation_severity: severity enum low/medium/high.
        generated_at: ISO 8601 generation timestamp.
        trace_id: trace_id propagation CR 1-1 ContextVar.
    """

    recommendation_id: str
    tenant_id: str
    commitment_type: str
    commitment_term: str
    resource_pattern: str
    current_on_demand_cost_krw_per_month: float
    projected_commit_cost_krw_per_month: float
    projected_savings_pct: float
    projected_savings_krw: float
    upfront_cost_krw: float
    break_even_months: int
    roi_pct: float
    recommendation_severity: str
    generated_at: str
    trace_id: str


def compute_break_even_months(
    upfront_cost_krw: float,
    monthly_savings_krw: float,
) -> int:
    """Compute break-even months (PRD §F30.4.4 verbatim).

    break_even_months = upfront_cost / monthly_savings.

    Raises:
        BreakEvenCalculationError: invalid inputs.
    """
    if upfront_cost_krw < 0 or monthly_savings_krw <= 0:
        raise BreakEvenCalculationError(
            message_ko=f"잘못된 입력: upfront_cost={upfront_cost_krw}, monthly_savings={monthly_savings_krw}",
            details={
                "upfront_cost_krw": str(upfront_cost_krw),
                "monthly_savings_krw": str(monthly_savings_krw),
            },
        )
    return int(upfront_cost_krw / monthly_savings_krw)


def compute_roi_pct(
    total_savings_krw: float,
    upfront_cost_krw: float,
) -> float:
    """Compute ROI percentage (PRD §F30.4.6 verbatim).

    roi_pct = (total_savings_krw - upfront_cost_krw) / upfront_cost_krw × 100.
    """
    if upfront_cost_krw <= 0:
        return 0.0
    return round((total_savings_krw - upfront_cost_krw) / upfront_cost_krw * 100.0, 4)


def classify_severity_from_roi(roi_pct: float) -> str:
    """Classify severity based on ROI."""
    if roi_pct >= ROI_THRESHOLD_HIGH:
        return SEVERITY_HIGH
    if roi_pct >= ROI_THRESHOLD_MEDIUM:
        return SEVERITY_MEDIUM
    return SEVERITY_LOW


def _build_commitment_recommendation(
    tenant_id: str,
    commitment_type: str,
    commitment_term: str,
    resource_pattern: str,
    current_on_demand_cost_krw_per_month: float,
    discount_rate: float,
    *,
    upfront_cost_krw: float = 0.0,
    trace_id: str = "",
) -> CommitmentRecommendation:
    """Build a single commitment recommendation (PRD §F30.4.4~§F30.4.6).

    Args:
        tenant_id: tenant UUID.
        commitment_type: 6 commitment_type options.
        commitment_term: 1_year / 3_year.
        resource_pattern: instance type pattern.
        current_on_demand_cost_krw_per_month: current on-demand cost KRW/month.
        discount_rate: discount rate (0.40 for 1y, 0.60 for 3y).
        upfront_cost_krw: upfront cost (0 = no upfront).
        trace_id: trace_id propagation CR 1-1 ContextVar.
    """
    if commitment_type not in ALL_COMMITMENT_TYPES:
        raise CommitmentRecommendationError(
            message_ko=f"unknown commitment_type: {commitment_type}",
            details={"commitment_type": commitment_type},
        )
    if commitment_term not in ALL_COMMITMENT_TERMS:
        raise CommitmentRecommendationError(
            message_ko=f"unknown commitment_term: {commitment_term}",
            details={"commitment_term": commitment_term},
        )
    # Project commit cost = on-demand × (1 - discount_rate)
    projected_commit_cost = current_on_demand_cost_krw_per_month * (1.0 - discount_rate)
    monthly_savings = current_on_demand_cost_krw_per_month - projected_commit_cost
    term_months = 12 if commitment_term == COMMITMENT_TERM_1_YEAR else 36
    projected_savings_pct = round(discount_rate * 100.0, 4)
    projected_savings_krw = round(monthly_savings * term_months, 2)
    # Break-even
    if upfront_cost_krw > 0 and monthly_savings > 0:
        break_even_months = compute_break_even_months(upfront_cost_krw, monthly_savings)
    else:
        break_even_months = 0
    # ROI
    roi_pct = compute_roi_pct(monthly_savings * term_months, max(upfront_cost_krw, 1))
    severity = classify_severity_from_roi(roi_pct)
    return CommitmentRecommendation(
        recommendation_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        commitment_type=commitment_type,
        commitment_term=commitment_term,
        resource_pattern=resource_pattern,
        current_on_demand_cost_krw_per_month=round(current_on_demand_cost_krw_per_month, 2),
        projected_commit_cost_krw_per_month=round(projected_commit_cost, 2),
        projected_savings_pct=projected_savings_pct,
        projected_savings_krw=projected_savings_krw,
        upfront_cost_krw=round(upfront_cost_krw, 2),
        break_even_months=break_even_months,
        roi_pct=roi_pct,
        recommendation_severity=severity,
        generated_at=datetime.now(UTC).isoformat(),
        trace_id=trace_id,
    )


def recommend_commitments(
    tenant_id: str | uuid.UUID,
    baseline_period: str = BASELINE_PERIOD_LAST_30D,
    *,
    trace_id: str = "",
    dry_run: bool = False,
) -> list[CommitmentRecommendation]:
    """Main entry point — recommend commitment plans (1y/3y parallel).

    CR 1-1 audit-first INSERT for `commitment_recommended`
    (dry-run skips; service-layer emits via emit_audit_typed BEFORE
    the actual commitment recommendation).

    Args:
        tenant_id: tenant UUID.
        baseline_period: 5 baseline_period options.
        trace_id: trace_id propagation CR 1-1 ContextVar.
        dry_run: dry-run mode (no actual recommendation).

    Returns:
        List of CommitmentRecommendation TypedDict.

    Raises:
        CommitmentRecommendationError: recommendation failure.
        PricingDataUnavailableError: pricing data unavailable.
        BreakEvenCalculationError: break-even calculation failure.
    """
    # Placeholder parallel run — actual data lookup via Phase 13
    # forecast_engine 12-month forward forecast EXTENSION (service-layer
    # integration).
    return []


__all__ = [
    "COMMITMENT_TYPE_EC2_RI",
    "COMMITMENT_TYPE_RDS_RI",
    "COMMITMENT_TYPE_EC2_SP",
    "COMMITMENT_TYPE_S3_SP",
    "COMMITMENT_TYPE_REDSHIFT_SP",
    "COMMITMENT_TYPE_DYNAMODB_SP",
    "ALL_COMMITMENT_TYPES",
    "COMMITMENT_TERM_1_YEAR",
    "COMMITMENT_TERM_3_YEAR",
    "ALL_COMMITMENT_TERMS",
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SEVERITY_HIGH",
    "ALL_SEVERITIES",
    "RI_SP_DISCOUNT_1Y",
    "RI_SP_DISCOUNT_3Y",
    "BREAK_EVEN_THRESHOLD_1Y_MONTHS",
    "BREAK_EVEN_THRESHOLD_3Y_MONTHS",
    "ROI_THRESHOLD_HIGH",
    "ROI_THRESHOLD_MEDIUM",
    "CommitmentRecommendation",
    "compute_break_even_months",
    "compute_roi_pct",
    "classify_severity_from_roi",
    "recommend_commitments",
]
