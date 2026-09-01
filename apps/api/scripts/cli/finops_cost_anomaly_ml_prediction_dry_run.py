"""apps.api.scripts.cli.finops_cost_anomaly_ml_prediction_dry_run — Phase 26 dry-run CLI.

Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
dry-run mode CLI (PRD §F42 + AD-55 (a)~(g) verbatim + 1 NEW CLI flag
`--finops-cost-anomaly-ml-prediction-dry-run`).

Usage:
    python -m apps.api.scripts.cli.finops_cost_anomaly_ml_prediction_dry_run \\
        --tenant-id <uuid> \\
        --finops-cost-anomaly-ml-prediction-dry-run

CR lessons applied:
- AD-22 owner-only RBAC.
- NFR18 ko-KR SSOT — Korean error messages.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from apps.api.modules.finops.cost_anomaly_ml_prediction import (
    DEFAULT_ENSEMBLE_WEIGHTS,
    ENSEMBLE_CONSENSUS_THRESHOLD,
    FEATURE_NAMES,
    ML_DEFAULTS,
    MODEL_HYPERPARAMETERS,
    create_prediction,
    predict_anomaly_score,
    train_model,
)


def main() -> int:
    """Run dry-run mode for Phase 26 cost_anomaly_ml_prediction.

    Returns:
        Exit code (0 success, 1 error).
    """
    parser = argparse.ArgumentParser(
        description="Phase 26 FinOps Cost Anomaly ML Prediction dry-run CLI",
    )
    parser.add_argument("--tenant-id", required=True, help="UUID tenant identifier")
    parser.add_argument(
        "--finops-cost-anomaly-ml-prediction-dry-run",
        action="store_true",
        default=True,
        help="Phase 26 dry-run mode flag (always True for this CLI)",
    )
    parser.add_argument(
        "--period-key",
        default="2026-08",
        help="Period key (default: 2026-08)",
    )
    parser.add_argument(
        "--model-type",
        default="ensemble",
        choices=["prophet", "lstm", "arima", "isolation_forest", "autoencoder", "ensemble"],
        help="Model type (default: ensemble)",
    )
    args = parser.parse_args()

    if not args.tenant_id:
        print("오류: --tenant-id는 필수입니다.", file=sys.stderr)
        return 1

    try:
        # Dry-run mode: simulate predictions without DB INSERT
        prediction = create_prediction(
            tenant_id=args.tenant_id,
            model_id="dry-run-model-id",
            period_key=args.period_key,
            predicted_cost_krw=Decimal("0.00"),
        )
        score_result = predict_anomaly_score(
            tenant_id=args.tenant_id,
            period_key=args.period_key,
        )
        training_job = train_model(
            tenant_id=args.tenant_id,
            model_type=args.model_type,
            trigger="manual_trigger",
        )
    except (ValueError, TypeError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    output = {
        "dry_run": True,
        "tenant_id": args.tenant_id,
        "period_key": args.period_key,
        "model_type": args.model_type,
        "prediction_id": prediction["prediction_id"],
        "ensemble_weights": dict(DEFAULT_ENSEMBLE_WEIGHTS),
        "ensemble_consensus_threshold": float(ENSEMBLE_CONSENSUS_THRESHOLD),
        "feature_names": list(FEATURE_NAMES),
        "ml_defaults": dict(ML_DEFAULTS),
        "model_hyperparameters": {k: dict(v) for k, v in MODEL_HYPERPARAMETERS.items()},
        "score_result": {
            "score_id": score_result["score_id"],
            "ml_ensemble_score": score_result["ml_ensemble_score"],
            "ml_anomaly_detected": score_result["ml_anomaly_detected"],
            "inference_latency_ms": score_result["inference_latency_ms"],
        },
        "training_job": {
            "training_job_id": training_job["training_job_id"],
            "status": training_job["status"],
            "model_type": training_job["model_type"],
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
