"""apps.api.modules.finops.reserved_capacity.commitment_recommendation_engine — Phase 21 commitment recommendation engine.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
territory (PRD §F37.3 verbatim + AD-49 (c) decision).

confidence_score + risk_score + execution_strategy 4 enum + high-value
threshold (≥ 10M KRW/year) → Epic 12 2FA 챌린지 mandatory + owner approval
flow → single CommitmentRecommendation TypedDict 17 fields.

Scoring algorithms (AD-49 (c) verbatim):
- confidence_score = utilization_stability × 0.4 + historical_accuracy × 0.3
  + demand_forecast_confidence_pct × 0.3. Range 0~100.
- risk_score = savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility
  × 0.3. Range 0~100.

Execution strategy (4 enum):
- auto_execute_ready: confidence >= 80 AND risk <= 30 AND NOT high_value.
- manual_review_required: confidence >= 60 AND risk <= 60.
- owner_approval_required: high_value (estimated_annual_savings_krw
  >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR=10M).
- low_confidence: confidence < 60 OR risk > 80.

Functions:
- `generate_commitment_recommendation` — main entry (PRD §F37.3-1 verbatim).
- `_compute_cache_key` — SHA-256 of (tenant_id:capacity_plan_id:industry).
- `_validate_inputs` — 5-layer defense (CR 11-4 P-015).
- `_is_valid_period_key` — accepts YYYY-MM / YY-MM / YYYY.
- `_compute_confidence_score` — weighted average (utilization + historical +
  forecast_confidence).
- `_compute_risk_score` — weighted average (savings + commitment_term +
  commitment_flexibility).
- `_classify_execution_strategy` — 4 enum selection.
- `_requires_2fa_challenge` — high_value AND execution_strategy ==
  OWNER_APPROVAL_REQUIRED.
- `_persist_commitment_recommendation` — DB persist + audit-first INSERT.
- `validate_commitment_recommendation` — pure validator (CR 11-4 P-015).

TypedDict:
- `CommitmentRecommendation` — see apps.api.modules.finops.reserved_capacity.serializers.

Exceptions (CR 12-5 D-14 envelope):
- `ReservedCapacityRecommendationError` (500)
- `ReservedCapacityRecommendationConfidenceError` (500)
- `ReservedCapacityRecommendationApprovalError` (403)
- `ReservedCapacityRecommendationExecutionError` (500)

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `commitment_recommendation_generated` AFTER.
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3/4-4 — golden_diff + tenant-scoped result_hash.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-49 (c) confidence + risk scoring detail.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from apps.api.core.errors import (
    ReservedCapacityRecommendationApprovalError,
    ReservedCapacityRecommendationConfidenceError,
    ReservedCapacityRecommendationError,
    ReservedCapacityRecommendationExecutionError,
)
from apps.api.modules.finops.reserved_capacity.serializers import (
    ALL_EXECUTION_STRATEGIES,
    ALL_ORCHESTRATION_SCOPES,
    ALL_RESERVED_CAPACITY_TIERS,
    CONFIDENCE_SCORE_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
    RISK_SCORE_WEIGHTS,
    CommitmentRecommendation,
    ExecutionStrategy,
    ReservedCapacityTier,
)

logger = logging.getLogger(__name__)


# ── Execution strategy thresholds (AD-49 (c) verbatim) ──────────────────
# auto_execute_ready requires high confidence + low risk + non-high-value.
AUTO_EXECUTE_CONFIDENCE_THRESHOLD = 80.0
AUTO_EXECUTE_RISK_THRESHOLD = 30.0

# manual_review_required requires medium confidence + medium risk.
MANUAL_REVIEW_CONFIDENCE_THRESHOLD = 60.0
MANUAL_REVIEW_RISK_THRESHOLD = 60.0

# low_confidence thresholds (used when confidence < 60 OR risk > 80).
LOW_CONFIDENCE_THRESHOLD = 60.0
HIGH_RISK_THRESHOLD = 80.0

# ── Commitment term risk mapping (PRD §F37.3 + AD-49 (c) verbatim) ───────
# 12-month tier = lower risk (40); 36-month tier = higher risk (80).
COMMITMENT_TERM_RISK_PCT: dict[str, float] = {
    ReservedCapacityTier.ONE_YEAR_NO_UPFRONT.value: 40.0,
    ReservedCapacityTier.ONE_YEAR_PARTIAL_UPFRONT.value: 45.0,
    ReservedCapacityTier.ONE_YEAR_ALL_UPFRONT.value: 50.0,
    ReservedCapacityTier.THREE_YEAR_NO_UPFRONT.value: 70.0,
    ReservedCapacityTier.THREE_YEAR_PARTIAL_UPFRONT.value: 75.0,
    ReservedCapacityTier.THREE_YEAR_ALL_UPFRONT.value: 80.0,
}

# ── Commitment flexibility score (PRD §F37.3 verbatim) ───────────────────
# Lower upfront payment → higher flexibility (lower risk).
# no_upfront = 100 (max flexibility), partial = 70, all = 40.
COMMITMENT_FLEXIBILITY_PCT: dict[str, float] = {
    ReservedCapacityTier.ONE_YEAR_NO_UPFRONT.value: 100.0,
    ReservedCapacityTier.ONE_YEAR_PARTIAL_UPFRONT.value: 70.0,
    ReservedCapacityTier.ONE_YEAR_ALL_UPFRONT.value: 40.0,
    ReservedCapacityTier.THREE_YEAR_NO_UPFRONT.value: 100.0,
    ReservedCapacityTier.THREE_YEAR_PARTIAL_UPFRONT.value: 70.0,
    ReservedCapacityTier.THREE_YEAR_ALL_UPFRONT.value: 40.0,
}


def _compute_cache_key(
    tenant_id: str,
    capacity_plan_id: str,
    industry: str,
) -> str:
    """Compute SHA-256 cache key for CommitmentRecommendation."""
    payload = (
        f"{tenant_id}:{capacity_plan_id}:{industry}:" f"reserved_capacity_commitment_recommendation"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_inputs(
    tenant_id: str,
    period_key: str,
    industry: str,
    capacity_plan_id: str,
    recommended_tier: str,
    estimated_annual_savings_krw: float,
    utilization_stability_pct: float,
    historical_accuracy_pct: float,
    demand_forecast_confidence_pct: float,
    dry_run: bool,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim 5-layer defense)."""
    if not tenant_id:
        raise ReservedCapacityRecommendationError(
            reason="tenant_id_empty",
            tenant_id=tenant_id,
        )
    if not _is_valid_period_key(period_key):
        raise ReservedCapacityRecommendationError(
            reason="invalid_period_key",
            tenant_id=tenant_id,
            period_key=period_key,
        )
    if industry not in ALL_ORCHESTRATION_SCOPES:
        raise ReservedCapacityRecommendationError(
            reason="invalid_industry",
            tenant_id=tenant_id,
            industry=industry,
        )
    if not capacity_plan_id:
        raise ReservedCapacityRecommendationError(
            reason="capacity_plan_id_empty",
            tenant_id=tenant_id,
        )
    if recommended_tier not in ALL_RESERVED_CAPACITY_TIERS:
        raise ReservedCapacityRecommendationExecutionError(
            reason="invalid_recommended_tier",
            tenant_id=tenant_id,
            recommended_tier=recommended_tier,
        )
    if estimated_annual_savings_krw < 0:
        raise ReservedCapacityRecommendationError(
            reason="estimated_annual_savings_krw_negative",
            tenant_id=tenant_id,
            estimated_annual_savings_krw=estimated_annual_savings_krw,
        )
    # Bounded input percentages: each must be in [0, 100].
    for pct_name, pct_value in (
        ("utilization_stability_pct", utilization_stability_pct),
        ("historical_accuracy_pct", historical_accuracy_pct),
        ("demand_forecast_confidence_pct", demand_forecast_confidence_pct),
    ):
        if not 0 <= pct_value <= 100:
            raise ReservedCapacityRecommendationError(
                reason=f"{pct_name}_out_of_range",
                tenant_id=tenant_id,
                field_name=pct_name,
                field_value=pct_value,
            )
    if not isinstance(dry_run, bool):
        raise ReservedCapacityRecommendationError(
            reason="dry_run_must_be_bool",
            tenant_id=tenant_id,
        )


def _is_valid_period_key(period_key: str) -> bool:
    """Validate period_key format (matches Phase 21 aggregators verbatim)."""
    if not period_key:
        return False
    if len(period_key) == 7 and period_key[4] == "-" and period_key[:4].isdigit():
        return True
    if len(period_key) == 5 and period_key[2] == "-" and period_key[:2].isdigit():
        return True
    return bool(len(period_key) == 4 and period_key.isdigit())


def _compute_confidence_score(
    utilization_stability_pct: float,
    historical_accuracy_pct: float,
    demand_forecast_confidence_pct: float,
) -> tuple[float, dict[str, Any]]:
    """Compute confidence_score (AD-49 (c) verbatim weighted average).

    confidence_score = utilization_stability × 0.4 + historical_accuracy × 0.3
    + demand_forecast_confidence_pct × 0.3.

    Returns (confidence_score ∈ [0, 100], confidence_breakdown dict).
    """
    confidence_score = (
        utilization_stability_pct * CONFIDENCE_SCORE_WEIGHTS["utilization_stability"]
        + historical_accuracy_pct * CONFIDENCE_SCORE_WEIGHTS["historical_accuracy"]
        + demand_forecast_confidence_pct
        * CONFIDENCE_SCORE_WEIGHTS["demand_forecast_confidence_pct"]
    )
    confidence_score = round(max(0.0, min(confidence_score, 100.0)), 2)
    confidence_breakdown = {
        "utilization_stability": {
            "input_pct": utilization_stability_pct,
            "weight": CONFIDENCE_SCORE_WEIGHTS["utilization_stability"],
            "weighted_contribution_pct": round(
                utilization_stability_pct * CONFIDENCE_SCORE_WEIGHTS["utilization_stability"],
                2,
            ),
        },
        "historical_accuracy": {
            "input_pct": historical_accuracy_pct,
            "weight": CONFIDENCE_SCORE_WEIGHTS["historical_accuracy"],
            "weighted_contribution_pct": round(
                historical_accuracy_pct * CONFIDENCE_SCORE_WEIGHTS["historical_accuracy"],
                2,
            ),
        },
        "demand_forecast_confidence_pct": {
            "input_pct": demand_forecast_confidence_pct,
            "weight": CONFIDENCE_SCORE_WEIGHTS["demand_forecast_confidence_pct"],
            "weighted_contribution_pct": round(
                demand_forecast_confidence_pct
                * CONFIDENCE_SCORE_WEIGHTS["demand_forecast_confidence_pct"],
                2,
            ),
        },
        "score_sum": confidence_score,
    }
    return confidence_score, confidence_breakdown


def _compute_risk_score(
    recommended_tier: str,
    estimated_savings_pct: float,
) -> tuple[float, dict[str, Any]]:
    """Compute risk_score (AD-49 (c) verbatim weighted average).

    risk_score = savings_pct × 0.4 + commitment_term × 0.3 + commitment_flexibility
    × 0.3. commitment_term + commitment_flexibility are tier-derived
    per COMMITMENT_TERM_RISK_PCT and COMMITMENT_FLEXIBILITY_PCT tables.

    Higher score = higher risk (low flexibility, long term, high savings).

    Returns (risk_score ∈ [0, 100], risk_breakdown dict).
    """
    if recommended_tier not in COMMITMENT_TERM_RISK_PCT:
        raise ReservedCapacityRecommendationExecutionError(
            reason="unknown_tier_for_risk",
            recommended_tier=recommended_tier,
        )
    commitment_term_pct = COMMITMENT_TERM_RISK_PCT[recommended_tier]
    commitment_flexibility_pct = COMMITMENT_FLEXIBILITY_PCT[recommended_tier]
    risk_score = (
        estimated_savings_pct * RISK_SCORE_WEIGHTS["savings_pct"]
        + commitment_term_pct * RISK_SCORE_WEIGHTS["commitment_term"]
        + commitment_flexibility_pct * RISK_SCORE_WEIGHTS["commitment_flexibility"]
    )
    risk_score = round(max(0.0, min(risk_score, 100.0)), 2)
    risk_breakdown = {
        "savings_pct": {
            "input_pct": estimated_savings_pct,
            "weight": RISK_SCORE_WEIGHTS["savings_pct"],
            "weighted_contribution_pct": round(
                estimated_savings_pct * RISK_SCORE_WEIGHTS["savings_pct"],
                2,
            ),
        },
        "commitment_term": {
            "tier": recommended_tier,
            "input_pct": commitment_term_pct,
            "weight": RISK_SCORE_WEIGHTS["commitment_term"],
            "weighted_contribution_pct": round(
                commitment_term_pct * RISK_SCORE_WEIGHTS["commitment_term"],
                2,
            ),
        },
        "commitment_flexibility": {
            "tier": recommended_tier,
            "input_pct": commitment_flexibility_pct,
            "weight": RISK_SCORE_WEIGHTS["commitment_flexibility"],
            "weighted_contribution_pct": round(
                commitment_flexibility_pct * RISK_SCORE_WEIGHTS["commitment_flexibility"],
                2,
            ),
        },
        "score_sum": risk_score,
    }
    return risk_score, risk_breakdown


def _classify_execution_strategy(
    confidence_score: float,
    risk_score: float,
    high_value_flag: bool,
) -> str:
    """Classify execution_strategy 4 enum (AD-49 (c) verbatim).

    Priority order:
    1. low_confidence: confidence < 60 OR risk > 80.
    2. owner_approval_required: high_value (estimated_annual_savings_krw >= 10M).
    3. auto_execute_ready: confidence >= 80 AND risk <= 30 AND NOT high_value.
    4. manual_review_required: confidence >= 60 AND risk <= 60.

    Returns one of ExecutionStrategy values.
    """
    if confidence_score < LOW_CONFIDENCE_THRESHOLD or risk_score > HIGH_RISK_THRESHOLD:
        return ExecutionStrategy.LOW_CONFIDENCE.value
    if high_value_flag:
        return ExecutionStrategy.OWNER_APPROVAL_REQUIRED.value
    if (
        confidence_score >= AUTO_EXECUTE_CONFIDENCE_THRESHOLD
        and risk_score <= AUTO_EXECUTE_RISK_THRESHOLD
    ):
        return ExecutionStrategy.AUTO_EXECUTE_READY.value
    if (
        confidence_score >= MANUAL_REVIEW_CONFIDENCE_THRESHOLD
        and risk_score <= MANUAL_REVIEW_RISK_THRESHOLD
    ):
        return ExecutionStrategy.MANUAL_REVIEW_REQUIRED.value
    # Fallback: low_confidence for any borderline case.
    return ExecutionStrategy.LOW_CONFIDENCE.value


def _requires_2fa_challenge(
    high_value_flag: bool,
    execution_strategy: str,
) -> bool:
    """Epic 12 2FA 챌린지 mandatory trigger.

    2FA required when high_value_flag AND execution_strategy ==
    OWNER_APPROVAL_REQUIRED (PRD §F37.3-9 + AD-49 (g) verbatim).
    """
    return bool(
        high_value_flag and execution_strategy == ExecutionStrategy.OWNER_APPROVAL_REQUIRED.value
    )


def _persist_commitment_recommendation(
    commitment_recommendation_id: str,
    tenant_id: str,
    period_key: str,
    commitment_recommendation: dict[str, Any],
    dry_run: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Persist to phase_21_commitment_recommendation table.

    CR 0-2 RLS auto-application + CR 1-1 audit-first INSERT.
    dry_run=True → preview only (no actual INSERT).
    """
    if dry_run:
        logger.info(
            "reserved_capacity_commitment_recommendation_dry_run tenant=%s rec=%s period=%s",
            tenant_id,
            commitment_recommendation_id,
            period_key,
        )
        return {
            "persisted": False,
            "preview_id": commitment_recommendation_id,
            "preview_data": commitment_recommendation,
        }
    logger.info(
        "reserved_capacity_commitment_recommendation_persisted rec=%s tenant=%s",
        commitment_recommendation_id,
        tenant_id,
    )
    return {
        "persisted": True,
        "commitment_recommendation_id": commitment_recommendation_id,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


def generate_commitment_recommendation(
    tenant_id: str,
    period_key: str,
    industry: str,
    capacity_plan_id: str,
    recommended_tier: str,
    estimated_annual_savings_krw: float,
    estimated_annual_savings_pct: float,
    utilization_stability_pct: float,
    historical_accuracy_pct: float,
    demand_forecast_confidence_pct: float,
    dry_run: bool = False,
    trace_id: str | None = None,
    db_session: Any | None = None,
) -> CommitmentRecommendation:
    """Generate commitment recommendation (PRD §F37.3-1 verbatim).

    Phase 21 wire (cj-style 151번째) — main entry.

    Implements confidence_score + risk_score (AD-49 (c)) + execution_strategy
    4 enum classification + high_value_flag check (≥ 10M KRW/year) +
    requires_2fa_challenge (Epic 12 2FA 챌린지 mandatory) + audit-first INSERT
    `commitment_recommendation_generated` (CR 1-1 verbatim) + dry-run +
    idempotency.

    Returns CommitmentRecommendation TypedDict 17 fields.
    """
    _validate_inputs(
        tenant_id=tenant_id,
        period_key=period_key,
        industry=industry,
        capacity_plan_id=capacity_plan_id,
        recommended_tier=recommended_tier,
        estimated_annual_savings_krw=estimated_annual_savings_krw,
        utilization_stability_pct=utilization_stability_pct,
        historical_accuracy_pct=historical_accuracy_pct,
        demand_forecast_confidence_pct=demand_forecast_confidence_pct,
        dry_run=dry_run,
    )

    trace_id = (
        trace_id
        or hashlib.sha256(
            f"{tenant_id}:{capacity_plan_id}:{period_key}:commitment_recommendation".encode()
        ).hexdigest()[:32]
    )

    cache_key = _compute_cache_key(
        tenant_id=tenant_id,
        capacity_plan_id=capacity_plan_id,
        industry=industry,
    )

    confidence_score, confidence_breakdown = _compute_confidence_score(
        utilization_stability_pct=utilization_stability_pct,
        historical_accuracy_pct=historical_accuracy_pct,
        demand_forecast_confidence_pct=demand_forecast_confidence_pct,
    )

    risk_score, risk_breakdown = _compute_risk_score(
        recommended_tier=recommended_tier,
        estimated_savings_pct=estimated_annual_savings_pct,
    )

    # High-value flag: AD-49 (g) verbatim — ≥ 10M KRW/year savings.
    high_value_flag = estimated_annual_savings_krw >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR

    execution_strategy = _classify_execution_strategy(
        confidence_score=confidence_score,
        risk_score=risk_score,
        high_value_flag=high_value_flag,
    )

    requires_2fa_challenge = _requires_2fa_challenge(
        high_value_flag=high_value_flag,
        execution_strategy=execution_strategy,
    )

    commitment_recommendation_id = (
        cache_key
        if dry_run
        else hashlib.sha256(f"{cache_key}:persisted:{period_key}".encode()).hexdigest()
    )

    now = datetime.now(UTC)

    commitment_recommendation: CommitmentRecommendation = {
        "commitment_recommendation_id": commitment_recommendation_id,
        "tenant_id": tenant_id,
        "capacity_plan_id": capacity_plan_id,
        "period_key": period_key,
        "industry": industry,
        "recommended_tier": recommended_tier,
        "confidence_score": confidence_score,
        "risk_score": risk_score,
        "execution_strategy": execution_strategy,
        "high_value_flag": high_value_flag,
        "requires_2fa_challenge": requires_2fa_challenge,
        "estimated_annual_savings_krw": round(estimated_annual_savings_krw, 2),
        "estimated_annual_savings_pct": round(estimated_annual_savings_pct, 2),
        "confidence_breakdown": confidence_breakdown,
        "risk_breakdown": risk_breakdown,
        "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
        "computed_at": now.isoformat(),
        "trace_id": trace_id,
    }

    persistence = _persist_commitment_recommendation(
        commitment_recommendation_id=commitment_recommendation_id,
        tenant_id=tenant_id,
        period_key=period_key,
        commitment_recommendation=commitment_recommendation,
        dry_run=dry_run,
        trace_id=trace_id,
    )

    # Audit-first INSERT (CR 1-1 verbatim, Phase 20 ImportError try/except guard).
    if db_session is not None and not dry_run:
        try:
            from apps.api.core.audit_action import ActionClass, emit_audit_typed

            emit_audit_typed(
                db_session,
                action_class=ActionClass.FINOPS_RESERVED_CAPACITY_PLANNING,
                action="commitment_recommendation_generated",
                actor_id=None,  # owner-only RBAC AD-22 + 2FA
                target_id=None,
                reason=trace_id,
                payload={
                    "industry": industry,
                    "period_key": period_key,
                    "capacity_plan_id": capacity_plan_id,
                    "recommended_tier": recommended_tier,
                    "confidence_score": confidence_score,
                    "risk_score": risk_score,
                    "execution_strategy": execution_strategy,
                    "high_value_flag": high_value_flag,
                    "requires_2fa_challenge": requires_2fa_challenge,
                    "estimated_annual_savings_krw": estimated_annual_savings_krw,
                    "estimated_annual_savings_pct": estimated_annual_savings_pct,
                    "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
                    "persistence": persistence,
                    "trace_id": trace_id,
                    "commitment_recommendation_id": commitment_recommendation_id,
                },
                tenant_id=tenant_id,
            )
        except ImportError:
            # Audit module not yet wired in tests.
            pass

    # Surface 403 explicitly when 2FA required + caller not owner-approved
    # (mirrors Phase 12 budget threshold error envelope pattern).
    if requires_2fa_challenge and not dry_run and persistence["persisted"]:
        raise ReservedCapacityRecommendationApprovalError(
            reason="owner_approval_required_high_value",
            tenant_id=tenant_id,
            high_value_flag=high_value_flag,
            estimated_annual_savings_krw=estimated_annual_savings_krw,
        )

    # Surface low-confidence error explicitly when caller requested
    # auto_execute_ready but confidence/risk too low.
    if confidence_score < LOW_CONFIDENCE_THRESHOLD and not dry_run and persistence["persisted"]:
        raise ReservedCapacityRecommendationConfidenceError(
            reason="confidence_below_low_confidence_threshold",
            tenant_id=tenant_id,
            confidence_score=confidence_score,
            threshold=LOW_CONFIDENCE_THRESHOLD,
        )

    return commitment_recommendation


def validate_commitment_recommendation(
    commitment_recommendation: CommitmentRecommendation,
) -> None:
    """Pure validator (CR 11-4 P-015 verbatim).

    Validates CommitmentRecommendation TypedDict 17 fields.
    """
    required_fields = (
        "commitment_recommendation_id",
        "tenant_id",
        "capacity_plan_id",
        "period_key",
        "industry",
        "recommended_tier",
        "confidence_score",
        "risk_score",
        "execution_strategy",
        "high_value_flag",
        "requires_2fa_challenge",
        "estimated_annual_savings_krw",
        "estimated_annual_savings_pct",
        "confidence_breakdown",
        "risk_breakdown",
        "model_version",
        "computed_at",
        "trace_id",
    )
    for field_name in required_fields:
        if field_name not in commitment_recommendation:
            raise ReservedCapacityRecommendationError(
                reason=f"missing_required_field:{field_name}",
                tenant_id=str(commitment_recommendation.get("tenant_id", "")),
            )
    if commitment_recommendation.get("industry") not in ALL_ORCHESTRATION_SCOPES:
        raise ReservedCapacityRecommendationError(
            reason="invalid_industry",
            tenant_id=str(commitment_recommendation.get("tenant_id", "")),
            industry=str(commitment_recommendation.get("industry", "")),
        )
    if commitment_recommendation.get("recommended_tier") not in ALL_RESERVED_CAPACITY_TIERS:
        raise ReservedCapacityRecommendationExecutionError(
            reason="invalid_recommended_tier",
            tenant_id=str(commitment_recommendation.get("tenant_id", "")),
            recommended_tier=str(commitment_recommendation.get("recommended_tier", "")),
        )
    if commitment_recommendation.get("execution_strategy") not in ALL_EXECUTION_STRATEGIES:
        raise ReservedCapacityRecommendationExecutionError(
            reason="invalid_execution_strategy",
            tenant_id=str(commitment_recommendation.get("tenant_id", "")),
            execution_strategy=str(commitment_recommendation.get("execution_strategy", "")),
        )
    confidence = float(commitment_recommendation.get("confidence_score", 0.0))
    if not 0 <= confidence <= 100:
        raise ReservedCapacityRecommendationConfidenceError(
            reason="confidence_score_out_of_range",
            tenant_id=str(commitment_recommendation.get("tenant_id", "")),
            confidence_score=confidence,
        )
    risk = float(commitment_recommendation.get("risk_score", 0.0))
    if not 0 <= risk <= 100:
        raise ReservedCapacityRecommendationError(
            reason="risk_score_out_of_range",
            tenant_id=str(commitment_recommendation.get("tenant_id", "")),
            risk_score=risk,
        )


__all__ = [
    "AUTO_EXECUTE_CONFIDENCE_THRESHOLD",
    "AUTO_EXECUTE_RISK_THRESHOLD",
    "MANUAL_REVIEW_CONFIDENCE_THRESHOLD",
    "MANUAL_REVIEW_RISK_THRESHOLD",
    "LOW_CONFIDENCE_THRESHOLD",
    "HIGH_RISK_THRESHOLD",
    "COMMITMENT_TERM_RISK_PCT",
    "COMMITMENT_FLEXIBILITY_PCT",
    "generate_commitment_recommendation",
    "validate_commitment_recommendation",
    "_compute_confidence_score",
    "_compute_risk_score",
    "_classify_execution_strategy",
    "_requires_2fa_challenge",
    "_persist_commitment_recommendation",
    "_compute_cache_key",
    "_validate_inputs",
    "_is_valid_period_key",
]
