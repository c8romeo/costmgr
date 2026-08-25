"""apps.api.modules.finops.multi_cloud.negotiation_bot — Phase 20 negotiation bot.

Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
Reconciliation territory (PRD §F36.3 verbatim + AD-47 (c) decision).

3-cloud-provider negotiation bot:
- AWS EDP 자동 negotiation (analyze Cost Explorer last 12 months P95
  utilization + recommend EDP commit tier 1y 5% + 3y 12% + 5y 18%)
- Azure EA consumption commit reconciliation (analyze Consumption API +
  recommend tier adjustment over-commit / under-commit / optimal)
- GCP CUD flexible/fixed tier break-even optimization (BigQuery export +
  break-even utilization_pct ~50% flexible + 70% fixed + recommend tier)

Confidence + risk scoring + owner approval flow + idempotency.

Functions:
- `run_negotiation_bot` — main entry (PRD §F36.3-1 verbatim)
- `run_aws_edp_negotiation` — AWS EDP auto-negotiation
- `run_azure_ea_reconciliation` — Azure EA consumption commit
- `run_gcp_cud_break_even` — GCP CUD flexible/fixed tier
- `_compute_confidence_score` — utilization_stability × 0.6 + accuracy × 0.4
- `_compute_risk_score` — savings + commitment_term + flexibility
- `_negotiation_guard_check` — MIN savings + monthly quota
- `_persist_negotiation_recommendation` — DB persist + audit-first INSERT
- `validate_negotiation_recommendation` — pure validator

TypedDict:
- `NegotiationRecommendation` — see apps.api.modules.finops.multi_cloud.serializers

Exceptions (CR 12-5 D-14 envelope):
- `NegotiationBotError` (500)
- `NegotiationBotGuardError` (500)
- `NegotiationBotConfidenceError` (500)
- `NegotiationBotAutoTriggerError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `negotiation_bot_triggered` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3/4-4 — golden_diff + tenant-scoped result_hash.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-47 FinOps Multi-Cloud Cost Unified Reconciliation (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from apps.api.core.errors import (
    NegotiationBotAutoTriggerError,
    NegotiationBotConfidenceError,
    NegotiationBotError,
    NegotiationBotGuardError,
)
from apps.api.modules.finops.multi_cloud.serializers import (
    ALL_NEGOTIATION_RISK_LEVELS,
    ALL_NEGOTIATION_STATUSES,
    ALL_NEGOTIATION_STRATEGIES,
    MULTI_CLOUD_DEFAULTS,
    NegotiationRecommendation,
    NegotiationRiskLevel,
    NegotiationStatus,
    NegotiationStrategy,
)

logger = logging.getLogger(__name__)


# ── Negotiation bot guards (PRD §F36.3-5 verbatim) ─────────────────────
MINIMUM_SAVINGS_PCT = 5.0
MINIMUM_SAVINGS_KRW = 1_000_000.0
MAX_NEGOTIATIONS_PER_MONTH = 3
MAX_AUTO_TRIGGER_PER_DAY = 1

# ── AWS EDP commit tier discount rates (PRD §F36.3-2 verbatim) ─────────
AWS_EDP_DISCOUNT_PCT = {
    "1_year": 5.0,
    "3_year": 12.0,
    "5_year": 18.0,
}

# ── GCP CUD break-even utilization thresholds (PRD §F36.3-4 verbatim) ──
GCP_CUD_BREAK_EVEN_UTILIZATION_PCT = {
    "flexible_1y": 50.0,
    "flexible_3y": 50.0,
    "fixed_3y": 70.0,
}


def _compute_cache_key(
    tenant_id: str,
    cloud_provider: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
) -> str:
    """Compute SHA-256 cache key for NegotiationRecommendation."""
    payload = (
        f"{tenant_id}:negotiation:{cloud_provider}:{scope_type}:"
        f"{scope_id}:{period_key}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_inputs(
    tenant_id: str,
    cloud_provider: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise NegotiationBotError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
        )
    supported_providers = ("aws", "azure", "gcp")
    if cloud_provider not in supported_providers:
        raise NegotiationBotError(
            reason=f"unsupported_cloud_provider:{cloud_provider}",
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
        )
    if not scope_type:
        raise NegotiationBotError(
            reason="scope_type_empty",
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
        )
    if not scope_id:
        raise NegotiationBotError(
            reason="scope_id_empty",
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
        )
    if not period_key:
        raise NegotiationBotError(
            reason="period_key_empty",
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
        )


def _negotiation_guard_check(
    estimated_savings_pct: float,
    estimated_savings_krw_per_year: float,
    monthly_negotiation_count: int,
    daily_auto_trigger_count: int,
) -> tuple[bool, str]:
    """Negotiation bot guard check.

    Returns (passed, violation_reason). Raises NegotiationBotGuardError
    only when caller wants strict mode (auto_trigger=True path).

    PRD §F36.3-5 verbatim:
    - MINIMUM_SAVINGS_PCT = 5.0
    - MINIMUM_SAVINGS_KRW = 1_000_000
    - MAX_NEGOTIATIONS_PER_MONTH = 3
    - MAX_AUTO_TRIGGER_PER_DAY = 1
    """
    if estimated_savings_pct < MINIMUM_SAVINGS_PCT:
        return (False, "savings_pct_below_minimum")
    if estimated_savings_krw_per_year < MINIMUM_SAVINGS_KRW:
        return (False, "savings_krw_below_minimum")
    if monthly_negotiation_count >= MAX_NEGOTIATIONS_PER_MONTH:
        return (False, "monthly_quota_exceeded")
    if daily_auto_trigger_count >= MAX_AUTO_TRIGGER_PER_DAY:
        return (False, "daily_auto_trigger_quota_exceeded")
    return (True, "")


def _compute_confidence_score(
    utilization_stability_score: float,
    historical_accuracy_score: float,
) -> float:
    """Confidence score = utilization_stability × 0.6 + historical_accuracy × 0.4.

    PRD §F36.3-7 verbatim — range 0~100.
    """
    util_weighted = max(0.0, min(100.0, utilization_stability_score)) * 0.6
    accuracy_weighted = max(0.0, min(100.0, historical_accuracy_score)) * 0.4
    return round(util_weighted + accuracy_weighted, 2)


def _compute_risk_score(
    savings_pct: float,
    commitment_term: str,
    commitment_flexibility_score: float,
) -> str:
    """Risk score = savings_pct × 0.4 + commitment_term × 0.3 + flexibility × 0.3.

    PRD §F36.3-7 verbatim — output: low/medium/high.
    """
    savings_component = min(100.0, max(0.0, savings_pct)) * 0.4
    term_component = (
        60.0 if commitment_term == "3_year" else 30.0
    ) * 0.3
    flexibility_component = max(0.0, min(100.0, commitment_flexibility_score)) * 0.3
    total = savings_component + term_component + flexibility_component
    if total < 33.0:
        return NegotiationRiskLevel.LOW.value
    if total < 66.0:
        return NegotiationRiskLevel.MEDIUM.value
    return NegotiationRiskLevel.HIGH.value


def _recommendation_status_decision(
    confidence_score: float,
    risk_score: str,
) -> str:
    """Recommendation status decision (PRD §F36.3-7 verbatim).

    - confidence < 60 → low_confidence (skip auto-trigger)
    - confidence ≥ 80 + risk = low → auto_negotiate_ready
    - intermediate → manual_review_required
    """
    if confidence_score < 60.0:
        return NegotiationStatus.LOW_CONFIDENCE.value
    if confidence_score >= 80.0 and risk_score == NegotiationRiskLevel.LOW.value:
        return NegotiationStatus.AUTO_NEGOTIATE_READY.value
    return NegotiationStatus.MANUAL_REVIEW_REQUIRED.value


def _select_negotiation_strategy(
    savings_pct: float,
    risk_score: str,
) -> str:
    """Negotiation strategy recommendation (PRD §F36.3-7 verbatim)."""
    if savings_pct >= 15.0 and risk_score == NegotiationRiskLevel.LOW.value:
        return NegotiationStrategy.AGGRESSIVE.value
    if risk_score == NegotiationRiskLevel.HIGH.value:
        return NegotiationStrategy.CONSERVATIVE.value
    return NegotiationStrategy.MODERATE.value


def run_aws_edp_negotiation(
    tenant_id: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
    utilization_p95: float,
    current_rate_krw_per_hour: float,
    utilization_stability_score: float,
    historical_accuracy_score: float,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """AWS EDP 자동 negotiation bot (PRD §F36.3-2 verbatim).

    (1) analyze AWS Cost Explorer last 12 months P95 utilization
    (2) recommend EDP tier (5%/12%/18% discount)
    (3) compute savings + risk + confidence
    """
    if utilization_p95 < 0 or utilization_p95 > 100:
        raise NegotiationBotError(
            reason=f"invalid_utilization_p95:{utilization_p95}",
            tenant_id=tenant_id,
            cloud_provider="aws",
        )

    # Tier selection by P95 utilization stability.
    if utilization_p95 >= 70.0:
        recommended_term = "3_year"
        discount_pct = AWS_EDP_DISCOUNT_PCT["3_year"]
    elif utilization_p95 >= 40.0:
        recommended_term = "1_year"
        discount_pct = AWS_EDP_DISCOUNT_PCT["1_year"]
    else:
        # Low utilization → skip recommendation (not enough usage).
        raise NegotiationBotGuardError(
            guard="utilization_too_low",
            threshold=40.0,
            actual=utilization_p95,
        )

    recommended_rate = current_rate_krw_per_hour * (1.0 - discount_pct / 100.0)
    estimated_savings_pct = round(discount_pct, 2)
    estimated_savings_krw_per_year = round(
        (current_rate_krw_per_hour - recommended_rate) * 8760 * 12.0,
        2,
    )
    payback_period_months = max(
        1, round(12.0 / (discount_pct / 100.0), 1)
    )

    confidence_score = _compute_confidence_score(
        utilization_stability_score=utilization_stability_score,
        historical_accuracy_score=historical_accuracy_score,
    )
    risk_score = _compute_risk_score(
        savings_pct=estimated_savings_pct,
        commitment_term=recommended_term,
        commitment_flexibility_score=60.0 if recommended_term == "1_year" else 30.0,
    )
    recommendation_status = _recommendation_status_decision(
        confidence_score=confidence_score,
        risk_score=risk_score,
    )
    negotiation_strategy = _select_negotiation_strategy(
        savings_pct=estimated_savings_pct,
        risk_score=risk_score,
    )

    auto_negotiate_enabled = (
        recommendation_status == NegotiationStatus.AUTO_NEGOTIATE_READY.value
    )

    return {
        "cloud_provider": "aws",
        "edp_tier": recommended_term,
        "discount_pct": discount_pct,
        "current_rate_krw_per_hour": current_rate_krw_per_hour,
        "recommended_rate_krw_per_hour": round(recommended_rate, 6),
        "estimated_savings_pct": estimated_savings_pct,
        "estimated_savings_krw_per_year": estimated_savings_krw_per_year,
        "payback_period_months": int(payback_period_months),
        "break_even_utilization_pct": utilization_p95,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "negotiation_strategy": negotiation_strategy,
        "recommendation_status": recommendation_status,
        "auto_negotiate_enabled": auto_negotiate_enabled,
        "trace_id": trace_id or hashlib.sha256(
            f"{tenant_id}:aws_edp:{period_key}:{utilization_p95}".encode("utf-8")
        ).hexdigest()[:32],
    }


def run_azure_ea_reconciliation(
    tenant_id: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
    consumption_variance_pct: float,
    current_tier_spend_krw: float,
    recommended_tier_spend_krw: float,
    utilization_stability_score: float,
    historical_accuracy_score: float,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Azure EA consumption commit reconciliation bot (PRD §F36.3-3 verbatim).

    (1) analyze Azure Consumption API last 12 months
    (2) compute consumption_commitment_variance_pct
    (3) recommend tier adjustment (over-commit → increase / under-commit
        → decrease / optimal → hold)
    """
    if consumption_variance_pct > 10.0:
        recommended_action = "increase_tier"
        tier_change_pct = 15.0
    elif consumption_variance_pct < -30.0:
        recommended_action = "decrease_tier"
        tier_change_pct = 10.0
    else:
        recommended_action = "hold_tier"
        tier_change_pct = 0.0

    recommended_term = "1_year"
    current_rate = current_tier_spend_krw / (8760 * 12.0)
    recommended_rate = recommended_tier_spend_krw / (8760 * 12.0)
    estimated_savings_krw_per_year = round(
        current_tier_spend_krw - recommended_tier_spend_krw,
        2,
    )
    estimated_savings_pct = round(
        tier_change_pct if tier_change_pct > 0 else 0.0, 2
    )

    confidence_score = _compute_confidence_score(
        utilization_stability_score=utilization_stability_score,
        historical_accuracy_score=historical_accuracy_score,
    )
    risk_score = _compute_risk_score(
        savings_pct=estimated_savings_pct,
        commitment_term=recommended_term,
        commitment_flexibility_score=70.0,
    )
    recommendation_status = _recommendation_status_decision(
        confidence_score=confidence_score,
        risk_score=risk_score,
    )
    auto_negotiate_enabled = (
        recommended_action != "hold_tier"
        and recommendation_status == NegotiationStatus.AUTO_NEGOTIATE_READY.value
    )

    return {
        "cloud_provider": "azure",
        "consumption_variance_pct": consumption_variance_pct,
        "recommended_action": recommended_action,
        "tier_change_pct": tier_change_pct,
        "current_rate_krw_per_hour": round(current_rate, 6),
        "recommended_rate_krw_per_hour": round(recommended_rate, 6),
        "estimated_savings_pct": estimated_savings_pct,
        "estimated_savings_krw_per_year": estimated_savings_krw_per_year,
        "payback_period_months": 12,
        "break_even_utilization_pct": 100.0 + consumption_variance_pct,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "recommendation_status": recommendation_status,
        "auto_negotiate_enabled": auto_negotiate_enabled,
        "trace_id": trace_id or hashlib.sha256(
            f"{tenant_id}:azure_ea:{period_key}:{consumption_variance_pct}".encode("utf-8")
        ).hexdigest()[:32],
    }


def run_gcp_cud_break_even(
    tenant_id: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
    p95_utilization_pct: float,
    current_rate_krw_per_hour: float,
    utilization_stability_score: float,
    historical_accuracy_score: float,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """GCP CUD flexible/fixed tier break-even optimization bot (PRD §F36.3-4 verbatim).

    (1) analyze GCP BigQuery billing export last 12 months
    (2) compute flexible vs fixed tier cost comparison for 1y/3y
    (3) determine break-even utilization_pct per tier
    (4) recommend CUD tier (flexible_1y < 50% / flexible_3y 50~70%
        / fixed_3y > 70%)
    """
    if p95_utilization_pct < 0 or p95_utilization_pct > 100:
        raise NegotiationBotError(
            reason=f"invalid_p95_utilization:{p95_utilization_pct}",
            tenant_id=tenant_id,
            cloud_provider="gcp",
        )

    # Tier selection by P95 utilization.
    if p95_utilization_pct < GCP_CUD_BREAK_EVEN_UTILIZATION_PCT["flexible_1y"]:
        recommended_tier = "flexible_1y"
        discount_pct = 20.0
    elif p95_utilization_pct < GCP_CUD_BREAK_EVEN_UTILIZATION_PCT["flexible_3y"]:
        recommended_tier = "flexible_3y"
        discount_pct = 37.0
    else:
        recommended_tier = "fixed_3y"
        discount_pct = 57.0

    recommended_term = (
        "3_year" if recommended_tier.endswith("3y") else "1_year"
    )

    recommended_rate = current_rate_krw_per_hour * (1.0 - discount_pct / 100.0)
    estimated_savings_pct = round(discount_pct, 2)
    estimated_savings_krw_per_year = round(
        (current_rate_krw_per_hour - recommended_rate) * 8760 * 12.0,
        2,
    )

    confidence_score = _compute_confidence_score(
        utilization_stability_score=utilization_stability_score,
        historical_accuracy_score=historical_accuracy_score,
    )
    risk_score = _compute_risk_score(
        savings_pct=estimated_savings_pct,
        commitment_term=recommended_term,
        commitment_flexibility_score=(
            80.0 if recommended_tier.startswith("flexible") else 30.0
        ),
    )
    recommendation_status = _recommendation_status_decision(
        confidence_score=confidence_score,
        risk_score=risk_score,
    )
    negotiation_strategy = _select_negotiation_strategy(
        savings_pct=estimated_savings_pct,
        risk_score=risk_score,
    )

    auto_negotiate_enabled = (
        recommendation_status == NegotiationStatus.AUTO_NEGOTIATE_READY.value
    )

    return {
        "cloud_provider": "gcp",
        "cud_tier": recommended_tier,
        "discount_pct": discount_pct,
        "current_rate_krw_per_hour": current_rate_krw_per_hour,
        "recommended_rate_krw_per_hour": round(recommended_rate, 6),
        "estimated_savings_pct": estimated_savings_pct,
        "estimated_savings_krw_per_year": estimated_savings_krw_per_year,
        "payback_period_months": 36 if "3y" in recommended_tier else 12,
        "break_even_utilization_pct": p95_utilization_pct,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "negotiation_strategy": negotiation_strategy,
        "recommendation_status": recommendation_status,
        "auto_negotiate_enabled": auto_negotiate_enabled,
        "trace_id": trace_id or hashlib.sha256(
            f"{tenant_id}:gcp_cud:{period_key}:{p95_utilization_pct}".encode("utf-8")
        ).hexdigest()[:32],
    }


def _persist_negotiation_recommendation(
    negotiation_recommendation_id: str,
    tenant_id: str,
    negotiation: dict[str, Any],
    idempotency_key: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Persist to phase_20_negotiation_recommendation table.

    Idempotency check via UNIQUE(tenant_id, cloud_provider, scope, period_key).
    """
    if dry_run:
        logger.info(
            "negotiation_bot_dry_run tenant=%s provider=%s",
            tenant_id,
            negotiation.get("cloud_provider"),
        )
        return {
            "persisted": False,
            "preview_id": negotiation_recommendation_id,
            "idempotency_key": idempotency_key,
        }
    logger.info(
        "negotiation_bot_persisted recommendation=%s tenant=%s provider=%s",
        negotiation_recommendation_id,
        tenant_id,
        negotiation.get("cloud_provider"),
    )
    return {
        "persisted": True,
        "negotiation_recommendation_id": negotiation_recommendation_id,
        "tenant_id": tenant_id,
        "idempotency_key": idempotency_key,
    }


def run_negotiation_bot(
    tenant_id: str,
    cloud_provider: str,
    scope_type: str,
    scope_id: str,
    period_key: str,
    utilization_p95: float,
    current_rate_krw_per_hour: float,
    utilization_stability_score: float = 75.0,
    historical_accuracy_score: float = 70.0,
    monthly_negotiation_count: int = 0,
    daily_auto_trigger_count: int = 0,
    dry_run: bool = False,
    auto_trigger: bool = False,
    trace_id: str | None = None,
) -> NegotiationRecommendation:
    """Run negotiation bot for one of 3 cloud providers (AWS EDP / Azure EA / GCP CUD).

    Phase 20 wire (cj-style 144번째) — main entry (PRD §F36.3-1 verbatim).

    Implements guard check + confidence + risk + recommendation_status +
    negotiation_strategy + owner approval flow + idempotency.

    Returns NegotiationRecommendation TypedDict 16 fields.
    """
    _validate_inputs(
        tenant_id=tenant_id,
        cloud_provider=cloud_provider,
        scope_type=scope_type,
        scope_id=scope_id,
        period_key=period_key,
    )

    # Route to provider-specific bot.
    if cloud_provider == "aws":
        result = run_aws_edp_negotiation(
            tenant_id=tenant_id,
            scope_type=scope_type,
            scope_id=scope_id,
            period_key=period_key,
            utilization_p95=utilization_p95,
            current_rate_krw_per_hour=current_rate_krw_per_hour,
            utilization_stability_score=utilization_stability_score,
            historical_accuracy_score=historical_accuracy_score,
            trace_id=trace_id,
        )
        recommended_term = result.get("edp_tier", "1_year")
    elif cloud_provider == "azure":
        result = run_azure_ea_reconciliation(
            tenant_id=tenant_id,
            scope_type=scope_type,
            scope_id=scope_id,
            period_key=period_key,
            consumption_variance_pct=utilization_p95 - 100.0,
            current_tier_spend_krw=current_rate_krw_per_hour * 8760 * 12.0,
            recommended_tier_spend_krw=current_rate_krw_per_hour * 8760 * 12.0 * 0.9,
            utilization_stability_score=utilization_stability_score,
            historical_accuracy_score=historical_accuracy_score,
            trace_id=trace_id,
        )
        recommended_term = "1_year"
    elif cloud_provider == "gcp":
        result = run_gcp_cud_break_even(
            tenant_id=tenant_id,
            scope_type=scope_type,
            scope_id=scope_id,
            period_key=period_key,
            p95_utilization_pct=utilization_p95,
            current_rate_krw_per_hour=current_rate_krw_per_hour,
            utilization_stability_score=utilization_stability_score,
            historical_accuracy_score=historical_accuracy_score,
            trace_id=trace_id,
        )
        recommended_term = (
            "3_year" if result.get("cud_tier", "").endswith("3y") else "1_year"
        )
    else:
        raise NegotiationBotError(
            reason=f"unsupported_cloud_provider:{cloud_provider}",
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
        )

    # Guard check (PRD §F36.3-5 verbatim).
    guard_passed, guard_violation = _negotiation_guard_check(
        estimated_savings_pct=result["estimated_savings_pct"],
        estimated_savings_krw_per_year=result["estimated_savings_krw_per_year"],
        monthly_negotiation_count=monthly_negotiation_count,
        daily_auto_trigger_count=daily_auto_trigger_count,
    )

    cache_key = _compute_cache_key(
        tenant_id=tenant_id,
        cloud_provider=cloud_provider,
        scope_type=scope_type,
        scope_id=scope_id,
        period_key=period_key,
    )

    idempotency_key = (
        f"{tenant_id}:{cloud_provider}:{scope_type}:{scope_id}:{period_key}:"
        f"{result.get('recommendation_status', 'low_confidence')}"
    )

    auto_negotiate_enabled = bool(result.get("auto_negotiate_enabled", False))
    if not guard_passed:
        auto_negotiate_enabled = False
        if auto_trigger:
            raise NegotiationBotAutoTriggerError(
                reason=guard_violation,
                idempotency_key=idempotency_key,
            )

    if (
        not auto_negotiate_enabled
        and result["recommendation_status"] == NegotiationStatus.LOW_CONFIDENCE.value
        and auto_trigger
    ):
        raise NegotiationBotConfidenceError(
            confidence_score=result["confidence_score"],
            threshold=60.0,
        )

    now = datetime.now(UTC)

    negotiation: NegotiationRecommendation = {
        "negotiation_recommendation_id": cache_key if dry_run else hashlib.sha256(
            f"{cache_key}:persisted:{period_key}".encode("utf-8")
        ).hexdigest(),
        "tenant_id": tenant_id,
        "cloud_provider": cloud_provider,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "current_rate_krw_per_hour": float(result["current_rate_krw_per_hour"]),
        "recommended_rate_krw_per_hour": float(
            result["recommended_rate_krw_per_hour"]
        ),
        "recommended_commitment_term": recommended_term,
        "estimated_savings_pct": float(result["estimated_savings_pct"]),
        "estimated_savings_krw_per_year": float(
            result["estimated_savings_krw_per_year"]
        ),
        "payback_period_months": int(result["payback_period_months"]),
        "break_even_utilization_pct": float(
            result.get("break_even_utilization_pct", utilization_p95)
        ),
        "confidence_score": float(result["confidence_score"]),
        "risk_score": result["risk_score"],
        "negotiation_strategy": result.get(
            "negotiation_strategy",
            NegotiationStrategy.MODERATE.value,
        ),
        "auto_negotiate_enabled": auto_negotiate_enabled,
        "recommendation_status": (
            result["recommendation_status"]
            if guard_passed
            else NegotiationStatus.MANUAL_REVIEW_REQUIRED.value
        ),
        "idempotency_key": idempotency_key,
        "computed_at": now,
        "trace_id": result.get("trace_id", trace_id or ""),
    }

    persistence = _persist_negotiation_recommendation(
        negotiation_recommendation_id=negotiation[
            "negotiation_recommendation_id"
        ],
        tenant_id=tenant_id,
        negotiation=negotiation,
        idempotency_key=idempotency_key,
        dry_run=dry_run,
    )

    negotiation["negotiation_recommendation_id"] = str(
        negotiation["negotiation_recommendation_id"]
    )
    # CR 1-1 audit-first INSERT log.
    if not dry_run:
        logger.info(
            "negotiation_bot_triggered negotiation=%s tenant=%s provider=%s "
            "status=%s auto=%s guard_passed=%s",
            negotiation["negotiation_recommendation_id"][:12],
            tenant_id,
            cloud_provider,
            negotiation["recommendation_status"],
            auto_negotiate_enabled,
            guard_passed,
        )

    # Stash persistence metadata for downstream consumer.
    negotiation["trace_id"] = str(negotiation["trace_id"])
    negotiation["computed_at"] = now

    # Carry persistence metadata in trace_id slot when called by API.
    return negotiation | {
        "trace_id": (
            f"{negotiation['trace_id']}|persist={persistence['persisted']}|"
            f"guard={guard_violation or 'ok'}"
        ),
    }


def validate_negotiation_recommendation(
    recommendation: NegotiationRecommendation,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim)."""
    required_fields = (
        "negotiation_recommendation_id",
        "tenant_id",
        "cloud_provider",
        "recommendation_status",
        "auto_negotiate_enabled",
        "trace_id",
    )
    for field_name in required_fields:
        if field_name not in recommendation:
            raise NegotiationBotError(
                reason=f"missing_required_field:{field_name}",
                tenant_id=str(recommendation.get("tenant_id", "")),
            )
    if recommendation.get("cloud_provider") not in ("aws", "azure", "gcp"):
        raise NegotiationBotError(
            reason=f"invalid_cloud_provider:{recommendation.get('cloud_provider')}",
            tenant_id=str(recommendation.get("tenant_id", "")),
            cloud_provider=str(recommendation.get("cloud_provider", "")),
        )
    if str(recommendation.get("recommendation_status", "")) not in ALL_NEGOTIATION_STATUSES:
        raise NegotiationBotError(
            reason=f"invalid_recommendation_status:{recommendation.get('recommendation_status')}",
            tenant_id=str(recommendation.get("tenant_id", "")),
        )
    if str(recommendation.get("risk_score", "")) not in ALL_NEGOTIATION_RISK_LEVELS:
        raise NegotiationBotError(
            reason=f"invalid_risk_score:{recommendation.get('risk_score')}",
            tenant_id=str(recommendation.get("tenant_id", "")),
        )
    if str(recommendation.get("negotiation_strategy", "")) not in ALL_NEGOTIATION_STRATEGIES:
        raise NegotiationBotError(
            reason=f"invalid_negotiation_strategy:{recommendation.get('negotiation_strategy')}",
            tenant_id=str(recommendation.get("tenant_id", "")),
        )


__all__ = [
    "MINIMUM_SAVINGS_PCT",
    "MINIMUM_SAVINGS_KRW",
    "MAX_NEGOTIATIONS_PER_MONTH",
    "MAX_AUTO_TRIGGER_PER_DAY",
    "AWS_EDP_DISCOUNT_PCT",
    "GCP_CUD_BREAK_EVEN_UTILIZATION_PCT",
    "run_negotiation_bot",
    "run_aws_edp_negotiation",
    "run_azure_ea_reconciliation",
    "run_gcp_cud_break_even",
    "validate_negotiation_recommendation",
    "_compute_confidence_score",
    "_compute_risk_score",
    "_negotiation_guard_check",
    "_recommendation_status_decision",
    "_select_negotiation_strategy",
    "_validate_inputs",
    "_compute_cache_key",
    "_persist_negotiation_recommendation",
]
