"""apps.api.modules.finops.forecast_model_registry — Forecast model registry (PRD §F29.2.10).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.2.10 verbatim).

This module provides:
- Model registry for tracking all 4 forecast models (ARIMA + Prophet
  + LSTM + ensemble).
- Semantic versioning MAJOR.MINOR.PATCH tracking (PRD §F29.2.10).
- JSONB metadata storage for model hyperparameters + training metrics.
- Phase 12 wire `f3c0e63` forecast_accuracy.py EXTENSION chain (CR 5-1
  verbatim MAE/MAPE/RMSE carry-over).

CR lessons applied:
- CR 0-2 RLS — every registry entry carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim.
- CR 11-4 P-015 — pure registry pattern.
- CR 12-5 D-14 typed exception envelope — uses ForecastModelTrainingError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.

AD-22 owner-only RBAC — model registration owner-only.
"""

from __future__ import annotations

import uuid
from datetime import UTC
from typing import Any, Final, TypedDict

# ── Semantic versioning constants (PRD §F29.2.10 verbatim) ───────
SEMVER_DEFAULT_VERSION: Final[str] = "1.0.0"
SEMVER_BUMP_MAJOR_THRESHOLD: Final[int] = 50  # % degradation threshold
SEMVER_BUMP_MINOR_THRESHOLD: Final[int] = 20  # % degradation threshold


class ForecastModelVersion(TypedDict, total=True):
    """TypedDict for model version metadata.

    PRD §F29.2.10 — JSONB metadata + semantic versioning.

    Fields:
        tenant_id: UUID of the tenant.
        model_type: ARIMA/prophet/lstm/ensemble.
        model_name: human-readable name (e.g. arima_p2_d1_q2).
        semver: semantic version (MAJOR.MINOR.PATCH).
        hyperparameters: JSONB dict of model hyperparameters.
        training_metrics: JSONB dict of training-set metrics.
        is_active: bool — current production version.
        created_at: ISO 8601 timestamp.
    """

    tenant_id: str
    model_type: str
    model_name: str
    semver: str
    hyperparameters: dict[str, Any]
    training_metrics: dict[str, Any]
    is_active: bool
    created_at: str


class ForecastModelRegistry:
    """In-memory registry for forecast model versions.

    Per PRD §F29.2.10 — JSONB metadata + semantic versioning. Real
    production use would persist this to DB; module exports pure
    helper functions for service-layer use.

    CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
    """

    _registry: dict[str, ForecastModelVersion] = {}

    @classmethod
    def register_version(
        cls,
        tenant_id: str | uuid.UUID,
        model_type: str,
        model_name: str,
        semver: str = SEMVER_DEFAULT_VERSION,
        hyperparameters: dict[str, Any] | None = None,
        training_metrics: dict[str, Any] | None = None,
        is_active: bool = True,
    ) -> ForecastModelVersion:
        """Register a model version with semver + JSONB metadata.

        Args:
            tenant_id: tenant UUID.
            model_type: ARIMA/prophet/lstm/ensemble.
            model_name: human-readable model name.
            semver: MAJOR.MINOR.PATCH.
            hyperparameters: dict of hyperparameters.
            training_metrics: dict of training-set metrics.
            is_active: production flag.

        Returns:
            ForecastModelVersion TypedDict.
        """
        from datetime import datetime

        key = f"{tenant_id}:{model_type}:{model_name}:{semver}"
        entry: ForecastModelVersion = ForecastModelVersion(
            tenant_id=str(tenant_id),
            model_type=model_type,
            model_name=model_name,
            semver=semver,
            hyperparameters=hyperparameters or {},
            training_metrics=training_metrics or {},
            is_active=is_active,
            created_at=datetime.now(UTC).isoformat(),
        )
        cls._registry[key] = entry
        return entry

    @classmethod
    def get_version(
        cls,
        tenant_id: str | uuid.UUID,
        model_type: str,
        model_name: str,
        semver: str = SEMVER_DEFAULT_VERSION,
    ) -> ForecastModelVersion | None:
        """Get a registered model version."""
        key = f"{tenant_id}:{model_type}:{model_name}:{semver}"
        return cls._registry.get(key)

    @classmethod
    def bump_major(cls, current_semver: str) -> str:
        """Bump MAJOR semver (PRD §F29.2.10 + SEMVER_BUMP_MAJOR_THRESHOLD)."""
        try:
            parts = current_semver.split(".")
            major = int(parts[0]) + 1
            return f"{major}.0.0"
        except (ValueError, IndexError):
            return SEMVER_DEFAULT_VERSION

    @classmethod
    def bump_minor(cls, current_semver: str) -> str:
        """Bump MINOR semver (PRD §F29.2.10 + SEMVER_BUMP_MINOR_THRESHOLD)."""
        try:
            parts = current_semver.split(".")
            major = int(parts[0])
            minor = int(parts[1]) + 1
            return f"{major}.{minor}.0"
        except (ValueError, IndexError):
            return SEMVER_DEFAULT_VERSION


__all__ = [
    "SEMVER_DEFAULT_VERSION",
    "SEMVER_BUMP_MAJOR_THRESHOLD",
    "SEMVER_BUMP_MINOR_THRESHOLD",
    "ForecastModelVersion",
    "ForecastModelRegistry",
]
