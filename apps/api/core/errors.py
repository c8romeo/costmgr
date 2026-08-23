"""apps/api/core/errors.py — Base error hierarchy for typed exception envelope.

CR 12-5 D-14 typed exception envelope + CR 11-4 P-015.

Phase 9 (cj-style 99번째 wire) — central BaseError + HTTPError subclasses
shared by chaos (chaos_experiment + fault_injection + auto_rollback +
tenant_scoping + game_day + continuous_chaos) and prior phases
(dr_drill + failover_orchestrator).
"""
from __future__ import annotations

import uuid
from typing import Any


class BaseError(Exception):
    """Root of the typed-exception hierarchy (CR 12-5 D-14 + CR 11-4 P-015).

    All domain errors inherit from this so catch blocks can reliably
    distinguish typed exceptions from generic Python exceptions.

    Accepts arbitrary keyword args via **kwargs so subclasses can pass
    structured envelope fields (code + message_ko + details + trace_id +
    http_status) without each one redefining __init__.
    """

    http_status: int = 500

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        message = kwargs.pop("message", args[0] if args else "")
        message_ko = kwargs.pop("message_ko", "")
        # Store message_ko as the primary args so __str__ returns it.
        primary = message_ko or message
        super().__init__(primary)
        self.message = message
        self.code = kwargs.pop("code", self.__class__.__name__)
        self.message_ko = message_ko or message
        self.details: dict[str, Any] = kwargs.pop("details", {})
        self.trace_id: str = kwargs.pop("trace_id", str(uuid.uuid4()))
        self.http_status = kwargs.pop("http_status", self.http_status)
        # Store any additional kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


# ── HTTP error classes (typed exception envelope helpers) ──────

class BadRequestError(BaseError):
    """HTTP 400 typed error."""

    http_status: int = 400


class ForbiddenError(BaseError):
    """HTTP 403 typed error (owner-only RBAC, AD-22)."""

    http_status: int = 403


class ConflictError(BaseError):
    """HTTP 409 typed error."""

    http_status: int = 409


class UnprocessableEntityError(BaseError):
    """HTTP 422 typed error."""

    http_status: int = 422


class LockedError(BaseError):
    """HTTP 423 typed error."""

    http_status: int = 423


class GatewayTimeoutError(BaseError):
    """HTTP 504 typed error."""

    http_status: int = 504


# ── FinOps Showback / Chargeback typed exceptions ──────
# Phase 11 (cj-style 107번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 6 NEW exceptions shared across showback_dsl +
# showback_query + chargeback_engine + chargeback_rule_evaluator +
# department_mapping + chargeback_export modules.

# Module identifier used by typed exception envelopes (mirrors
# m17_chaos_engineering + m18_slo_engineering pattern).
FINOPS_MODULE_ID: str = "m19_finops"


class FinopsError(BaseError):
    """Base for FinOps showback/chargeback typed exceptions.

    Provides FINOPS_MODULE_ID class attribute + finops envelope shape
    `{code, message_ko, details, trace_id, module_id}` shared by all
    6 NEW exception subclasses below.
    """

    module_id: str = FINOPS_MODULE_ID


class ShowbackDefinitionInvalidError(FinopsError):
    """HTTP 400 typed error — showback DSL validation failure.

    Raised by parse_showback_definition() when 6 validation rules
    (PRD §F27.1.7 verbatim) detect invalid group_by / period_key /
    currency_code / comparison_period / pagination / tenant_id.
    """

    http_status: int = 400


class ShowbackExportError(FinopsError):
    """HTTP 500 typed error — showback CSV export failure.

    Raised by export_showback_csv() when StreamingResponse generator
    fails (e.g. DB connection drop mid-stream, encoding error).
    """

    http_status: int = 500


class ChargebackRuleInvalidError(FinopsError):
    """HTTP 400 typed error — chargeback rule validation failure.

    Raised by evaluate_chargeback_rule() when 4 validation rules
    detect invalid rule_type / markup_pct / tax_pct / cost_allocation.
    """

    http_status: int = 400


class ChargebackCalculationError(FinopsError):
    """HTTP 500 typed error — chargeback calculation failure.

    Raised by compute_chargeback() when banker's rounding fails or
    Decimal precision overflows.
    """

    http_status: int = 500


class ChargebackExportError(FinopsError):
    """HTTP 500 typed error — chargeback CSV/PDF export failure.

    Raised by export_chargeback_csv() + export_chargeback_pdf()
    when StreamingResponse generator fails (e.g. reportlab rendering
    error, PDF encryption failure).
    """

    http_status: int = 500


class ChargebackExportRateLimitedError(FinopsError):
    """HTTP 429 typed error — chargeback export rate limit exceeded.

    Raised when owner > 1 export / minute default + Retry-After header.
    """

    http_status: int = 429


# ── FinOps Cost Anomaly Detection & Budget Alerting typed exceptions ──
# Phase 12 (cj-style 111번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 14 NEW exceptions shared across anomaly_detection +
# budget_definition + anomaly_detection_engine + budget_alert +
# forecast_accuracy modules. Module identifier m20_finops_anomaly.

# Module identifier used by typed exception envelopes (mirrors
# m19_finops Phase 11 + m18_slo_engineering Phase 10 + m17_chaos_engineering
# Phase 9 pattern).
FINOPS_ANOMALY_MODULE_ID: str = "m20_finops_anomaly"


class FinopsAnomalyError(FinopsError):
    """Base for FinOps anomaly + budget alert typed exceptions.

    Provides FINOPS_ANOMALY_MODULE_ID class attribute + envelope shape
    `{code, message_ko, details, trace_id, module_id}` shared by all
    14 NEW exception subclasses below.
    """

    module_id: str = FINOPS_ANOMALY_MODULE_ID


class AnomalyDefinitionInvalidError(FinopsAnomalyError):
    """HTTP 400 typed error — anomaly detection DSL validation failure.

    Raised by parse_anomaly_definition() when 6 validation rules
    (PRD §F28.1.5 verbatim) detect invalid dimension / threshold_method /
    baseline_window / threshold_value / consecutive_periods_required /
    tenant_id.
    """

    http_status: int = 400


class AnomalyDetectionError(FinopsAnomalyError):
    """HTTP 500 typed error — anomaly detection engine failure.

    Raised by run_anomaly_detection() when 4-method voting consensus
    fails or when the algorithm returns inconsistent results.
    """

    http_status: int = 500


class AnomalyBaselineUnavailableError(FinopsAnomalyError):
    """HTTP 422 typed error — insufficient baseline data for detection.

    Raised by _z_score_method / _iqr_method / _isolation_forest_method
    when baseline_history has fewer than required entries (z_score: ≥2,
    IQR: ≥4, isolation_forest: ≥2).
    """

    http_status: int = 422


class AnomalyBaselineUpdateError(FinopsAnomalyError):
    """HTTP 500 typed error — baseline window update failure.

    Raised by baseline_window updater (last_30d + last_90d + YTD) when
    aggregation query fails or partition pruning is invalid.
    """

    http_status: int = 500


class BudgetDefinitionInvalidError(FinopsAnomalyError):
    """HTTP 400 typed error — budget definition DSL validation failure.

    Raised by parse_budget_definition() when 6 validation rules
    (PRD §F28.2.1 verbatim) detect invalid budget_period / scope / amount /
    currency_code / status / tenant_id.
    """

    http_status: int = 400


class BudgetScopeInvalidError(FinopsAnomalyError):
    """HTTP 400 typed error — budget scope validation failure.

    Raised by parse_budget_definition() when scope is not in
    ALL_BUDGET_SCOPES (tenant / department / cost_center / product_line).
    """

    http_status: int = 400


class BudgetAmountInvalidError(FinopsAnomalyError):
    """HTTP 400 typed error — budget amount validation failure.

    Raised by parse_budget_definition() when amount is not a valid
    Decimal > 0 or fails banker's rounding precision.
    """

    http_status: int = 400


class BudgetAlertError(FinopsAnomalyError):
    """HTTP 500 typed error — budget alert routing failure.

    Raised by route_budget_alert() when consumption calculation fails
    or alert routing table is invalid.
    """

    http_status: int = 500


class BudgetAlertRoutingError(FinopsAnomalyError):
    """HTTP 400 typed error — budget alert routing validation failure.

    Raised by _build_routing() when alert_level is not in ALL_ALERT_LEVELS
    or routing table has invalid channel combination.
    """

    http_status: int = 400


class BudgetAlertDedupWindowActiveError(FinopsAnomalyError):
    """HTTP 409 typed error — budget alert dedup window active.

    Raised by route_budget_alert() when last_alert_at is within 24h
    dedup window for same budget + alert level.
    """

    http_status: int = 409


class ForecastAccuracyDegradedError(FinopsAnomalyError):
    """HTTP 422 typed error — forecast accuracy degraded (triggers retrain).

    Raised by evaluate_forecast_accuracy() when MAPE > 20% (RETRAIN
    threshold) — flagged for model retraining.
    """

    http_status: int = 422


class ForecastAccuracyInvalidError(FinopsAnomalyError):
    """HTTP 400 typed error — forecast accuracy input validation failure.

    Raised by compute_mae / compute_mape / compute_rmse when input lists
    have mismatched lengths, are empty, or contain zero values (MAPE
    zero division guard).
    """

    http_status: int = 400


class ForecastModelRetrainingError(FinopsAnomalyError):
    """HTTP 500 typed error — forecast model retraining failure.

    Raised by model retraining trigger when sklearn isolation_forest
    fit fails (AD-14 pin sklearn==1.4.0) or training data is invalid.
    """

    http_status: int = 500


class FinopsAnomalyCapabilityDeniedError(FinopsAnomalyError):
    """HTTP 403 typed error — FinOps anomaly/budget capability denied.

    Raised when tenant's industry does not unlock FINOPS_ANOMALY_DETECTION
    or FINOPS_BUDGET_ALERT capability (CR 12-1 L4 industry-agnostic gate).
    """

    http_status: int = 403


__all__ = [
    "BaseError",
    "BadRequestError",
    "ForbiddenError",
    "ConflictError",
    "UnprocessableEntityError",
    "LockedError",
    "GatewayTimeoutError",
    # Phase 11 FinOps showback/chargeback typed exceptions (CR 12-5 D-14)
    "FinopsError",
    "FINOPS_MODULE_ID",
    "ShowbackDefinitionInvalidError",
    "ShowbackExportError",
    "ChargebackRuleInvalidError",
    "ChargebackCalculationError",
    "ChargebackExportError",
    "ChargebackExportRateLimitedError",
    # Phase 12 FinOps anomaly + budget alert typed exceptions (CR 12-5 D-14)
    "FinopsAnomalyError",
    "FINOPS_ANOMALY_MODULE_ID",
    "AnomalyDefinitionInvalidError",
    "AnomalyDetectionError",
    "AnomalyBaselineUnavailableError",
    "AnomalyBaselineUpdateError",
    "BudgetDefinitionInvalidError",
    "BudgetScopeInvalidError",
    "BudgetAmountInvalidError",
    "BudgetAlertError",
    "BudgetAlertRoutingError",
    "BudgetAlertDedupWindowActiveError",
    "ForecastAccuracyDegradedError",
    "ForecastAccuracyInvalidError",
    "ForecastModelRetrainingError",
    "FinopsAnomalyCapabilityDeniedError",
]
