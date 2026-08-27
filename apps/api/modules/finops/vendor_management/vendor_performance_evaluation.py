"""apps.api.modules.finops.vendor_management.vendor_performance_evaluation — Phase 25 vendor performance evaluation + 4-dim scoring + monthly + quarterly cadence.

Phase 25 wire (cj-style 173번째) — §F41.4 + AD-53 (d) verbatim.

Provides:
- aggregate_vendor_performance (cross-tenant dashboard aggregation)
- evaluate_vendor_performance (4-dim weighted scoring)
- compute_monthly_score (monthly cadence 1st 03:00 KST)
- compute_quarterly_score (quarterly cadence 1st 03:30 KST)
- classify_performance_severity (3-tier severity)

CR lessons applied:
- CR 0-2 RLS.
- CR 1-1 audit-first INSERT.
- CR 5-1 Decimal precision banker's rounding.
- CR 11-4 P-015.
- CR 12-1 L4 industry-agnostic.
- CR 12-5 D-14.
- AD-14 stack pin (Recharts 2.12.7 + TanStack Table v8).
- AD-22 owner-only RBAC.
- AD-53 (d).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
- D-FINOPS-14 honestly DEFER.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from apps.api.modules.finops.vendor_management.serializers import (
    SELECTION_SCORE_VERSION_MAX,
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VENDOR_PERFORMANCE_DIMENSION_WEIGHTS,
    VendorPerformanceScorecard,
    VendorPerformanceSeverity,
)

logger = logging.getLogger(__name__)


# ── Audit-first INSERT (CR 1-1 verbatim) ──────────────────────────────────
def _emit_audit_safe(
    *,
    tenant_id: str,
    action: str,
    target_id: str,
    payload: dict[str, Any],
) -> str | None:
    """Best-effort audit emit via apps.api.core.audit (CR 1-1 verbatim)."""
    audit_log_id: str | None = None
    try:
        from apps.api.core.audit import emit_audit  # type: ignore[import-not-found]

        result = emit_audit(
            tenant_id=tenant_id,
            action=action,
            target_id=target_id,
            payload=payload,
        )
        if isinstance(result, dict):
            audit_log_id = str(result.get("audit_log_id", ""))
        else:
            audit_log_id = str(result)
    except ImportError:
        logger.debug("audit emit skipped: module unavailable for %s", action)
        audit_log_id = None
    except Exception as exc:  # pragma: no cover — defensive guard
        logger.warning("audit emit failed for %s: %s", action, exc)
        audit_log_id = None
    return audit_log_id or None


def _bankers_round(value: float, places: str = "0.01") -> float:
    """CR 5-1 verbatim — Decimal(str(value)).quantize + ROUND_HALF_EVEN."""
    quantize = Decimal(places)
    return float(Decimal(str(value)).quantize(quantize, rounding=ROUND_HALF_EVEN))


def _new_uuid_v7() -> str:
    """UUID v7 with v4 fallback (CR 1-1)."""
    try:
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover — Python <3.12 fallback
        return str(uuid.uuid4())


# ── Monthly score (PRD §F41.4 + AD-53 (d) verbatim) ───────────────────────
def compute_monthly_score(
    *,
    sla_compliance_score: float,
    cost_efficiency_score: float,
    support_quality_score: float,
    innovation_score: float,
) -> float:
    """Compute monthly vendor performance score (0.00~100.00).

    Formula (PRD §F41.4 + AD-53 (d) verbatim):
        monthly_score = (
            sla_compliance * 0.30
            + cost_efficiency * 0.25
            + support_quality * 0.25
            + innovation * 0.20
        )

    CR 5-1 Decimal banker's rounding applied.
    """
    weights = VENDOR_PERFORMANCE_DIMENSION_WEIGHTS
    raw = (
        sla_compliance_score * weights["sla_compliance"]
        + cost_efficiency_score * weights["cost_efficiency"]
        + support_quality_score * weights["support_quality"]
        + innovation_score * weights["innovation"]
    )
    return _bankers_round(raw)


# ── Quarterly score (average of 3 monthly scores) ────────────────────────
def compute_quarterly_score(
    *,
    monthly_scores: list[float],
) -> float:
    """Compute quarterly vendor performance score from 3 monthly scores.

    Quarterly score = average of 3 monthly scores (PRD §F41.4 verbatim).
    Returns 0.00 if no monthly scores provided.
    """
    if not monthly_scores:
        return 0.00
    return _bankers_round(sum(monthly_scores) / len(monthly_scores))


# ── Severity classification (PRD §F41.4 verbatim) ─────────────────────────
def classify_performance_severity(
    *,
    weighted_total_score: float,
) -> str:
    """Classify vendor performance severity (3-tier).

    - excellent: score >= 80.00
    - needs_improvement: 60.00 <= score < 80.00
    - critical: score < 60.00
    """
    if weighted_total_score >= 80.00:
        return VendorPerformanceSeverity.EXCELLENT.value
    if weighted_total_score >= 60.00:
        return VendorPerformanceSeverity.NEEDS_IMPROVEMENT.value
    return VendorPerformanceSeverity.CRITICAL.value


# ── Main evaluation function ─────────────────────────────────────────────
def evaluate_vendor_performance(
    *,
    tenant_id: str,
    vendor_id: str,
    period_key: str,
    sla_compliance_score: float,
    cost_efficiency_score: float,
    support_quality_score: float,
    innovation_score: float,
    monthly_score: float | None = None,
    quarterly_score: float | None = None,
    source_attribution: dict[str, object] | None = None,
) -> VendorPerformanceScorecard:
    """Evaluate vendor performance with 4-dim scoring (PRD §F41.4 verbatim).

    Args:
        tenant_id: tenant UUID
        vendor_id: parent Vendor vendor_id
        period_key: "YYYY" / "YYYY-Qn" / "YYYY-MM"
        sla_compliance_score: 0.00~100.00
        cost_efficiency_score: 0.00~100.00
        support_quality_score: 0.00~100.00
        innovation_score: 0.00~100.00
        monthly_score: optional pre-computed monthly score
        quarterly_score: optional pre-computed quarterly score
        source_attribution: Phase 11/18/22/24 ledger JSONB provenance

    Returns:
        VendorPerformanceScorecard TypedDict (14 fields).
    """
    # Validate score range (CR 11-4 P-015 pure)
    scores = {
        "sla_compliance_score": sla_compliance_score,
        "cost_efficiency_score": cost_efficiency_score,
        "support_quality_score": support_quality_score,
        "innovation_score": innovation_score,
    }
    for name, value in scores.items():
        if not (0.00 <= value <= SELECTION_SCORE_VERSION_MAX):
            raise ValueError(
                f"{name}={value} out of strict range [0.00, {SELECTION_SCORE_VERSION_MAX}]"
            )

    # Compute monthly score if not provided
    if monthly_score is None:
        monthly_score = compute_monthly_score(
            sla_compliance_score=sla_compliance_score,
            cost_efficiency_score=cost_efficiency_score,
            support_quality_score=support_quality_score,
            innovation_score=innovation_score,
        )

    # Use monthly as weighted_total if no quarterly
    weighted_total = quarterly_score if quarterly_score is not None else monthly_score

    severity = classify_performance_severity(weighted_total_score=weighted_total)

    scorecard_id = _new_uuid_v7()
    now_iso = datetime.now(UTC).isoformat()

    scorecard: VendorPerformanceScorecard = {
        "scorecard_id": scorecard_id,
        "vendor_id": vendor_id,
        "tenant_id": tenant_id,
        "period_key": period_key,
        "sla_compliance_score": _bankers_round(sla_compliance_score),
        "cost_efficiency_score": _bankers_round(cost_efficiency_score),
        "support_quality_score": _bankers_round(support_quality_score),
        "innovation_score": _bankers_round(innovation_score),
        "weighted_total_score": _bankers_round(weighted_total),
        "severity": severity,
        "monthly_score": _bankers_round(monthly_score),
        "quarterly_score": _bankers_round(quarterly_score) if quarterly_score is not None else 0.00,
        "source_attribution": source_attribution or {},
        "audit_log_id": "",
        "computed_at": now_iso,
    }

    audit_log_id = _emit_audit_safe(
        tenant_id=tenant_id,
        action="vendor_performance_evaluated",
        target_id=scorecard_id,
        payload={
            "scorecard_id": scorecard_id,
            "vendor_id": vendor_id,
            "period_key": period_key,
            "weighted_total_score": weighted_total,
            "severity": severity,
            "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
        },
    )
    if audit_log_id is not None:
        scorecard["audit_log_id"] = audit_log_id

    logger.info(
        "vendor_performance_evaluated scorecard_id=%s vendor_id=%s severity=%s score=%.2f",
        scorecard_id,
        vendor_id,
        severity,
        weighted_total,
    )

    return scorecard


# ── Aggregation across tenant ─────────────────────────────────────────────
def aggregate_vendor_performance(
    *,
    tenant_id: str,
    scorecards: list[VendorPerformanceScorecard],
) -> dict[str, Any]:
    """Aggregate vendor performance scorecards for tenant dashboard.

    RLS via tenant_id selector.
    """
    tenant_scorecards = [
        s for s in scorecards if s.get("tenant_id") == tenant_id
    ]

    severity_counts: dict[str, int] = {}
    total_weighted = 0.0
    excellent_count = 0
    critical_count = 0

    for sc in tenant_scorecards:
        severity = sc.get("severity", "needs_improvement")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        total_weighted += sc.get("weighted_total_score", 0.0)
        if severity == VendorPerformanceSeverity.EXCELLENT.value:
            excellent_count += 1
        elif severity == VendorPerformanceSeverity.CRITICAL.value:
            critical_count += 1

    avg_weighted = _bankers_round(
        total_weighted / len(tenant_scorecards) if tenant_scorecards else 0.0
    )

    return {
        "tenant_id": tenant_id,
        "scorecard_count": len(tenant_scorecards),
        "severity_counts": severity_counts,
        "avg_weighted_total_score": avg_weighted,
        "excellent_count": excellent_count,
        "critical_count": critical_count,
        "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    }
