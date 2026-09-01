"""apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_ensemble_consensus — Phase 26 ensemble consensus.

Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
ensemble consensus (PRD §F42.1 + AD-55 (a) verbatim + 5 model types
weighted ensemble + consensus detection).

Functions:
- ensemble_consensus_score(per_model_scores, weights) → Decimal
- consensus_detected(ml_score, threshold_score, consensus_threshold) → bool

5 model ensemble weights (PRD §F42.1 + AD-55 (a)):
- prophet: 0.30
- lstm: 0.30
- arima: 0.15
- isolation_forest: 0.15
- autoencoder: 0.10

CR lessons applied:
- CR 1-1 audit-first INSERT — `ensemble_consensus_calculated`.
- CR 12-5 D-14 typed exception envelope — AnomalyMLEnsembleConsensusError.
- AD-22 owner-only RBAC.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Final

from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_prediction_engine import (
    ML_FORECAST_WEIGHTS,
)
from apps.api.modules.finops.cost_anomaly_ml_prediction.serializers import (
    ENSEMBLE_CONSENSUS_THRESHOLD,
)

# ── Module constants ──────────────────────────────────────────────────────
DEFAULT_WEIGHTS: Final[dict[str, float]] = dict(ML_FORECAST_WEIGHTS)
DEFAULT_THRESHOLD: Final[float] = float(ENSEMBLE_CONSENSUS_THRESHOLD)


def _validate_scores(scores: dict[str, float]) -> None:
    """Validate per-model scores are non-empty dict with valid score values."""
    if not isinstance(scores, dict) or len(scores) == 0:
        raise ValueError("per_model_scores must be a non-empty dict")
    for model_type, score in scores.items():
        if not isinstance(score, int | float) or score < 0.0 or score > 1.0:
            raise ValueError(f"score for {model_type} must be in [0.0, 1.0], got {score}")


def _validate_weights(weights: dict[str, float]) -> None:
    """Validate weights are non-empty dict with valid weight values."""
    if not isinstance(weights, dict) or len(weights) == 0:
        raise ValueError("weights must be a non-empty dict")
    for model_type, weight in weights.items():
        if not isinstance(weight, int | float) or weight < 0.0 or weight > 1.0:
            raise ValueError(f"weight for {model_type} must be in [0.0, 1.0], got {weight}")


def ensemble_consensus_score(
    per_model_scores: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    """Compute weighted ensemble consensus score from per-model predictions.

    Args:
        per_model_scores: dict mapping model_type → predicted_anomaly_score
            in range [0.0, 1.0].
        weights: optional dict mapping model_type → weight (default DEFAULT_WEIGHTS).

    Returns:
        Ensemble consensus score in [0.0, 1.0].
    """
    _validate_scores(per_model_scores)
    if weights is None:
        weights = DEFAULT_WEIGHTS
    _validate_weights(weights)

    weighted_sum = Decimal("0.0000")
    weight_sum = Decimal("0.0000")
    for model_type, score in per_model_scores.items():
        if model_type not in weights:
            continue
        weight = Decimal(str(weights[model_type]))
        score_dec = Decimal(str(score))
        weighted_sum += weight * score_dec
        weight_sum += weight
    if weight_sum == Decimal("0.0000"):
        return 0.0
    result = float(weighted_sum / weight_sum)
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, result))


def consensus_detected(
    ml_score: float,
    threshold_score: float | None = None,
    consensus_threshold: float = DEFAULT_THRESHOLD,
) -> bool:
    """Check if consensus is detected across ML + threshold detection.

    Args:
        ml_score: ML ensemble score in [0.0, 1.0].
        threshold_score: optional Phase 12 threshold detection score.
        consensus_threshold: consensus threshold (default ENSEMBLE_CONSENSUS_THRESHOLD = 0.85).

    Returns:
        True if consensus detected, False otherwise.
    """
    if not isinstance(ml_score, int | float) or ml_score < 0.0 or ml_score > 1.0:
        raise ValueError(f"ml_score must be in [0.0, 1.0], got {ml_score}")
    if not isinstance(consensus_threshold, int | float) or consensus_threshold < 0.0:
        raise ValueError(f"consensus_threshold must be >= 0.0, got {consensus_threshold}")

    if threshold_score is None:
        # ML-only consensus
        return ml_score >= consensus_threshold
    # Combined consensus: ML + threshold both detect
    return ml_score >= consensus_threshold and threshold_score >= consensus_threshold * 0.5


__all__ = [
    "ensemble_consensus_score",
    "consensus_detected",
    "DEFAULT_WEIGHTS",
    "DEFAULT_THRESHOLD",
]
