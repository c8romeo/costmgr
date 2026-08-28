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


# ── FinOps Forecasting & Capacity Planning typed exceptions ─────
# Phase 13 (cj-style 115번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 14 NEW exceptions shared across forecast_definition +
# forecast_engine + capacity_headroom + budget_burnrate +
# forecast_accuracy_tracker modules. Module identifier m21_finops_forecast.

FINOPS_FORECAST_MODULE_ID: str = "m21_finops_forecast"


class FinopsForecastError(FinopsError):
    """Base for FinOps forecast + capacity planning typed exceptions.

    Provides FINOPS_FORECAST_MODULE_ID class attribute + envelope shape
    `{code, message_ko, details, trace_id, module_id}` shared by all
    14 NEW exception subclasses below.
    """

    module_id: str = FINOPS_FORECAST_MODULE_ID


class ForecastDefinitionInvalidError(FinopsForecastError):
    """HTTP 400 typed error — forecast definition DSL validation failure.

    Raised by parse_forecast_definition() when 6 validation rules
    (PRD §F29.1.1 verbatim) detect invalid target_metric /
    horizon_months / model_type / confidence_level / status / tenant_id.
    """

    http_status: int = 400


class ForecastScopeInvalidError(FinopsForecastError):
    """HTTP 400 typed error — forecast scope validation failure.

    Raised by parse_forecast_definition() when target_metric is not in
    ALL_TARGET_METRICS (department / cost_center / product_line /
    service / tenant_total).
    """

    http_status: int = 400


class ForecastHistoryUnavailableError(FinopsForecastError):
    """HTTP 422 typed error — insufficient history data for forecast.

    Raised by LSTM/Prophet/ARIMA when history has fewer than required
    entries (3 minimum for any model, 12-month preferred for ensemble).
    """

    http_status: int = 422


class ForecastEngineError(FinopsForecastError):
    """HTTP 500 typed error — forecast engine failure.

    Raised by generate_forecast() when 4-method parallel run fails or
    ensemble voting consensus cannot be reached.
    """

    http_status: int = 500


class ForecastModelTrainingError(FinopsForecastError):
    """HTTP 500 typed error — forecast model training failure.

    Raised by _arima_predict / _prophet_predict / _lstm_predict when
    training data is insufficient or model hyperparameters are invalid
    (AD-14 stack pin statsmodels==0.14.1 + prophet==1.1.5 +
    tensorflow==2.15.0).
    """

    http_status: int = 500


class ForecastSeasonalityDetectionError(FinopsForecastError):
    """HTTP 500 typed error — seasonality detection failure.

    Raised by _seasonality_detect / _stl_decompose when history length
    is below the minimum threshold (4 entries) or STL decomposition
    produces inconsistent results.
    """

    http_status: int = 500


class CapacityHeadroomAnalysisError(FinopsForecastError):
    """HTTP 500 typed error — capacity headroom analysis failure.

    Raised by analyze_capacity_headroom() when resource_type is not in
    ALL_RESOURCE_TYPES (compute / storage / network) or per-resource
    primary model selection fails.
    """

    http_status: int = 500


class CapacityThresholdBreachError(FinopsForecastError):
    """HTTP 500 typed error — capacity threshold breach classification.

    Raised by _classify_saturation() when saturation_pct is outside
    0-100 range or warning/critical thresholds are misconfigured.
    """

    http_status: int = 500


class CapacityMetricUnavailableError(FinopsForecastError):
    """HTTP 404 typed error — capacity utilization metric unavailable.

    Raised by analyze_capacity_headroom() when current_utilization_history
    is empty for the requested resource_type (compute / storage / network).
    """

    http_status: int = 404


class BudgetBurnRateProjectionError(FinopsForecastError):
    """HTTP 500 typed error — budget burn-rate projection failure.

    Raised by _compute_burn_rate() when elapsed_days / remaining_days /
    total_budget / consumed_budget inputs are invalid (zero / negative).
    """

    http_status: int = 500


class BudgetOverrunPredictionError(FinopsForecastError):
    """HTTP 500 typed error — budget overrun prediction failure.

    Raised by project_budget_consumption() when ARIMA projection of
    end-of-period spend fails (insufficient history or statsmodels
    convergence failure).
    """

    http_status: int = 500


class ForecastAccuracyTrackingError(FinopsForecastError):
    """HTTP 500 typed error — forecast accuracy tracking failure.

    Raised by track_forecast_accuracy() when target_metric is not in
    ALL_TARGET_METRICS or 3-tuple (tenant_id + target_metric +
    model_type) granularity key construction fails.
    """

    http_status: int = 500


class ModelRetrainingTriggerError(FinopsForecastError):
    """HTTP 500 typed error — model retraining trigger failure.

    Raised by _check_retraining_trigger() when retraining cron dispatch
    fails or MAPE_CONSECUTIVE_PERIODS_THRESHOLD violation detected.
    """

    http_status: int = 500


class ModelPerformanceDegradationError(FinopsForecastError):
    """HTTP 500 typed error — model performance degradation detected.

    Raised by _check_retraining_trigger() when MAPE > 20% detected but
    consecutive_periods < 3 (degradation flagged but retraining not yet
    triggered — informational warning per PRD §F29.5.2).
    """

    http_status: int = 500


# ── Phase 14 FinOps Optimization & Rightsizing typed exceptions ──
# Phase 14 (cj-style 119번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 15 NEW exceptions (1 base + 14 subclasses)
# shared across optimization_definition + rightsizing_engine +
# idle_resource_detector + commitment_recommender +
# optimization_accuracy_tracker modules.

FINOPS_OPTIMIZATION_MODULE_ID: str = "m22_finops_optimization"


class FinopsOptimizationError(FinopsError):
    """Base for FinOps optimization & rightsizing typed exceptions.

    Provides FINOPS_OPTIMIZATION_MODULE_ID class attribute + envelope
    shape `{code, message_ko, details, trace_id, module_id}` shared
    by all 14 NEW exception subclasses below.
    """

    module_id: str = FINOPS_OPTIMIZATION_MODULE_ID


# §F30.1 optimization definition DSL (3 NEW)
class OptimizationDefinitionInvalidError(FinopsOptimizationError):
    """HTTP 400 typed error — optimization definition DSL validation failure.

    Raised by parse_optimization_definition() when 6 validation rules
    (PRD §F30.1 verbatim) detect invalid resource_type /
    optimization_strategy / target_metric / baseline_period / status /
    tenant_id.
    """

    http_status: int = 400


class OptimizationScopeInvalidError(FinopsOptimizationError):
    """HTTP 404 typed error — optimization scope validation failure.

    Raised by parse_optimization_definition() when resource_type or
    optimization_strategy is not in the 5 / 6 / 4 / 5 options.
    """

    http_status: int = 404


class OptimizationInventoryUnavailableError(FinopsOptimizationError):
    """HTTP 422 typed error — inventory data unavailable for optimization.

    Raised by detect_idle_resources() or recommend_rightsizing() when
    resource_inventory JSONB is empty or insufficient for the requested
    resource_type.
    """

    http_status: int = 422


# §F30.2 rightsizing engine (3 NEW)
class RightsizingEngineError(FinopsOptimizationError):
    """HTTP 500 typed error — rightsizing engine failure.

    Raised by recommend_rightsizing() when 5-resource-type parallel run
    fails or capacity_headroom_report lookup fails (Phase 13 EXTENSION).
    """

    http_status: int = 500


class InstanceTypeMappingError(FinopsOptimizationError):
    """HTTP 500 typed error — instance type mapping failure.

    Raised by INSTANCE_TYPE_DOWNGRADE_MAP / INSTANCE_TYPE_UPGRADE_MAP
    lookup when the instance type is unknown or no downsize/upsize
    option found in the same family.
    """

    http_status: int = 500


class RecommendationConfidenceLowError(FinopsOptimizationError):
    """HTTP 422 typed error — recommendation confidence below threshold.

    Raised by confidence_score calculation when Phase 13 forecast
    accuracy MAPE-based confidence_score < 70% (low severity threshold).
    """

    http_status: int = 422


# §F30.3 idle resource detection (3 NEW)
class IdleResourceDetectionError(FinopsOptimizationError):
    """HTTP 500 typed error — idle resource detection failure.

    Raised by detect_idle_resources() when 5-idle-definition parallel
    run fails or Phase 12 anomaly_detection z-score baseline lookup
    fails.
    """

    http_status: int = 500


class IdleSeverityClassificationError(FinopsOptimizationError):
    """HTTP 500 typed error — idle severity classification failure.

    Raised by _classify_idle_severity() when potential_savings_krw
    thresholds are misconfigured or per-tenant override JSONB is
    malformed.
    """

    http_status: int = 500


class IdleMetricUnavailableError(FinopsOptimizationError):
    """HTTP 404 typed error — idle resource metric unavailable.

    Raised by detect_idle_resources() when utilization_p95 history
    is empty for the requested resource_type (compute / storage /
    database / network / container).
    """

    http_status: int = 404


# §F30.4 commitment recommender (3 NEW)
class CommitmentRecommendationError(FinopsOptimizationError):
    """HTTP 500 typed error — commitment recommendation failure.

    Raised by recommend_commitments() when 6 commitment_type parallel
    run fails or Phase 13 forecast 12-month baseline lookup fails.
    """

    http_status: int = 500


class PricingDataUnavailableError(FinopsOptimizationError):
    """HTTP 404 typed error — pricing data unavailable for commitment.

    Raised by recommend_commitments() when AWS Pricing API on-demand /
    RI / SP discount rate data is missing for the requested resource
    pattern.
    """

    http_status: int = 404


class BreakEvenCalculationError(FinopsOptimizationError):
    """HTTP 500 typed error — break-even calculation failure.

    Raised by break-even calculation when upfront_cost / monthly_savings
    inputs are zero or negative (1y break_even ≤ 8mo / 3y break_even
    ≤ 18mo threshold logic).
    """

    http_status: int = 500


# §F30.5 optimization accuracy tracker (3 NEW)
class OptimizationAccuracyTrackingError(FinopsOptimizationError):
    """HTTP 500 typed error — optimization accuracy tracking failure.

    Raised by track_optimization_accuracy() when per-(tenant_id +
    resource_type + optimization_strategy) granularity key construction
    fails or precision / recall / realized_savings inputs invalid.
    """

    http_status: int = 500


class OptimizationRetrainingTriggerError(FinopsOptimizationError):
    """HTTP 500 typed error — optimization retraining trigger failure.

    Raised by _check_accuracy_degradation() when accuracy_score < 70%
    for 3 consecutive months triggers retraining but cron dispatch
    fails.
    """

    http_status: int = 500


class OptimizationPerformanceDegradationError(FinopsOptimizationError):
    """HTTP 500 typed error — optimization performance degradation detected.

    Raised by _check_accuracy_degradation() when accuracy_score < 70%
    detected but consecutive_months < 3 (degradation flagged but
    retraining not yet triggered — informational warning).
    """

    http_status: int = 500


# ── Phase 15 FinOps Tag Governance & Cost Allocation typed exceptions ──
# Phase 15 (cj-style 123번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 15 NEW exceptions shared across tag_policy_dsl +
# untagged_resource_detector + allocation_rules_engine + allocation_audit +
# chargeback_allocation_reconciliation modules. Module identifier
# m23_finops_tag_governance.

FINOPS_TAG_GOVERNANCE_MODULE_ID: str = "m23_finops_tag_governance"


class FinopsTagGovernanceError(FinopsError):
    """Base for FinOps tag governance & cost allocation typed exceptions.

    Provides FINOPS_TAG_GOVERNANCE_MODULE_ID class attribute + envelope
    shape `{code, message_ko, details, trace_id, module_id}` shared by
    all 15 NEW exception subclasses below.
    """

    module_id: str = FINOPS_TAG_GOVERNANCE_MODULE_ID


# §F31.1 tag policy DSL (4 NEW)
class TagPolicyInvalidError(FinopsTagGovernanceError):
    """HTTP 400 typed error — tag policy DSL validation failure.

    Raised by parse_tag_policy() when 5 layer defense (syntax + semantic +
    tenant-scope RLS + resource_type validation + tag_key validation)
    detect invalid policy_id + tenant_id + resource_type + tag_key +
    enforcement_level + default_value + compliance_threshold_pct
    (PRD §F31.1-9 verbatim).
    """

    http_status: int = 400


class TagPolicyScopeInvalidError(FinopsTagGovernanceError):
    """HTTP 404 typed error — tag policy scope validation failure.

    Raised by parse_tag_policy() when tenant_id is not in
    ALL_VALID_TENANTS or resource_type is not in TAG_RESOURCE_TYPES
    (PRD §F31.1-9 verbatim).
    """

    http_status: int = 404


class TagPolicyHistoryUnavailableError(FinopsTagGovernanceError):
    """HTTP 404 typed error — tag policy history unavailable.

    Raised by validate_tag_policy() when previous policy version is
    missing or invalid (PRD §F31.1-9 verbatim).
    """

    http_status: int = 404


class TagEnforcementViolationError(FinopsTagGovernanceError):
    """HTTP 403 typed error — tag enforcement level violation.

    Raised by enforcement_level validation when required / recommended /
    blocked enforcement level is violated for a tenant (PRD §F31.1-11
    verbatim).
    """

    http_status: int = 403


# §F31.2 untagged resource detector (4 NEW)
class UntaggedResourceDetectionError(FinopsTagGovernanceError):
    """HTTP 500 typed error — untagged resource detection failure.

    Raised by detect_untagged_resources() when 6 resource_types parallel
    run fails or Phase 14 idle_resource_detector z-score baseline lookup
    fails (PRD §F31.2-12 verbatim).
    """

    http_status: int = 500


class UntaggedThresholdBreachError(FinopsTagGovernanceError):
    """HTTP 500 typed error — untagged threshold breach classification.

    Raised by _classify_untagged_severity() when untagged_resources_pct
    is outside 0-100 range or warning/critical thresholds are
    misconfigured (PRD §F31.2-12 verbatim).
    """

    http_status: int = 500


class UntaggedMetricUnavailableError(FinopsTagGovernanceError):
    """HTTP 404 typed error — untagged resource metric unavailable.

    Raised by detect_untagged_resources() when tag inventory query is
    empty for the requested resource_type (ec2/rds/s3/lambda/eks/vpc)
    (PRD §F31.2-12 verbatim).
    """

    http_status: int = 404


class RemediationActionError(FinopsTagGovernanceError):
    """HTTP 500 typed error — remediation action failure.

    Raised by remediation_status state machine when auto_remediate
    action fails (e.g. tag_value 자동 추천 실패 or owner 7일 SLA 만료
    후 admin escalate 실패) (PRD §F31.2-12 verbatim).
    """

    http_status: int = 500


# §F31.3 allocation rules engine (4 NEW)
class AllocationRuleInvalidError(FinopsTagGovernanceError):
    """HTTP 400 typed error — allocation rule validation failure.

    Raised by parse_allocation_rule() when 6 validation rules (PRD
    §F31.3-1 verbatim) detect invalid rule_type + priority + tag_key +
    tag_value_pattern + target_department_id + percentage_weights.
    """

    http_status: int = 400


class AllocationRuleEvaluationError(FinopsTagGovernanceError):
    """HTTP 500 typed error — allocation rule evaluation failure.

    Raised by evaluate_allocation_rules() when 5-rule_types parallel
    run fails or Phase 11 chargeback engine lookup fails
    (PRD §F31.3-12 verbatim).
    """

    http_status: int = 500


class PercentageSumValidationError(FinopsTagGovernanceError):
    """HTTP 422 typed error — percentage_sum validation failure.

    Raised by percentage_split allocation rule validation when
    percentage_weights do not sum to 100% (PRD §F31.3-3 verbatim).
    """

    http_status: int = 422


class ConditionalRuleParseError(FinopsTagGovernanceError):
    """HTTP 400 typed error — conditional rule AST parse failure.

    Raised by conditional allocation rule validation when condition_ast
    JSONB is malformed or condition expression evaluator fails
    (PRD §F31.3-5 verbatim).
    """

    http_status: int = 400


# §F31.5 chargeback allocation reconciliation (3 NEW)
class ChargebackReconciliationError(FinopsTagGovernanceError):
    """HTTP 500 typed error — chargeback allocation reconciliation failure.

    Raised by reconcile_chargeback_allocation() when 3 reconciliation
    strategy (chargeback_only/tag_allocation_only/hybrid_blended default)
    fails or variance calculation fails (PRD §F31.5-12 verbatim).
    """

    http_status: int = 500


class ReconciliationDeltaBreachError(FinopsTagGovernanceError):
    """HTTP 500 typed error — reconciliation variance breach detected.

    Raised by reconcile_chargeback_allocation() when variance_pct >
    threshold (5% default) triggers investigation workflow (PRD §F31.5-3
    verbatim).
    """

    http_status: int = 500


class ReconciliationApprovalError(FinopsTagGovernanceError):
    """HTTP 403 typed error — reconciliation approval access denied.

    Raised by reconciliation approval workflow when caller is NOT
    owner-only (AD-22 owner-only RBAC violation) (PRD §F31.5-8 verbatim).
    """

    http_status: int = 500


# §F31.4 allocation audit + compliance (NOT separate; covered via reconciliation workflow)
# (The spec's §F31.4 listed 3 NEW typed exceptions:
# ComplianceReportGenerationError + ComplianceScoreCalculationError +
# ComplianceAlertRoutingError — but to maintain 15 NEW total across the
# spec, we group them with the §F31.5 reconciliation flow.)
# Note: §F31.4 typed exceptions are not separately defined; instead,
# compliance workflow errors raise ChargebackReconciliationError
# (cross-tenant scenario) + UntaggedThresholdBreachError (severity
# classification).


# ── FinOps Reporting & Executive Dashboard typed exceptions ──
# Phase 16 (cj-style 127번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 16 NEW exceptions shared across
# executive_dashboard_aggregator + cross_module_kpi +
# executive_report_generator + scheduled_executive_dispatch +
# Phase 16 RBAC modules. Module identifier m24_finops_reporting.

# Module identifier used by typed exception envelopes (mirrors
# m23_finops_tag_governance Phase 15 + m22_finops_optimization
# Phase 14 + m21_finops_forecast Phase 13 + m20_finops_anomaly
# Phase 12 + m19_finops Phase 11 pattern).
FINOPS_REPORTING_MODULE_ID: str = "m24_finops_reporting"


class FinopsReportingError(FinopsError):
    """Base for FinOps reporting & executive dashboard typed exceptions.

    Provides FINOPS_REPORTING_MODULE_ID class attribute + envelope shape
    `{code, message_ko, details, trace_id, module_id}` shared by all
    16 NEW exception subclasses below.
    """

    module_id: str = FINOPS_REPORTING_MODULE_ID


# §F32.1 executive_dashboard_aggregator (4 NEW)
class ExecutiveRollupInvalidError(FinopsReportingError):
    """HTTP 400 typed error — executive rollup invalid inputs.

    Raised by aggregate_executive_dashboard() / validate_executive_rollup()
    when tenant_id is empty, scope_type invalid, or rollup missing
    required fields (PRD §F32.1-9 verbatim).
    """

    http_status: int = 400


class ExecutiveRollupScopeError(FinopsReportingError):
    """HTTP 404 typed error — executive rollup scope validation failure.

    Raised by aggregate_executive_dashboard() when scope_type is not in
    ALL_SCOPE_TYPES (tenant / department / cost_center / product_line)
    or scope_id is empty (PRD §F32.1-9 verbatim).
    """

    http_status: int = 404


class ExecutiveRollupPeriodError(FinopsReportingError):
    """HTTP 422 typed error — executive rollup period_key validation failure.

    Raised by aggregate_executive_dashboard() when period_key is not in
    valid format (YYYY-MM / YYYY-QN / YYYY) (PRD §F32.1-9 verbatim).
    """

    http_status: int = 422


class ExecutiveRollupCrossModuleJoinError(FinopsReportingError):
    """HTTP 500 typed error — 5-module cross-join failure.

    Raised by aggregate_executive_dashboard() when the 5-module join
    (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast +
    Phase 14 optimization + Phase 15 tag_governance) fails
    (PRD §F32.1-11 verbatim).
    """

    http_status: int = 500


# §F32.3 executive report generator (4 NEW)
class ExecutiveReportGenerationError(FinopsReportingError):
    """HTTP 500 typed error — executive report generation failure.

    Raised by generate_executive_report() when reportlab PDF render or
    openpyxl Excel workbook fails (PRD §F32.3-12 verbatim).
    """

    http_status: int = 500


class ExecutiveReportExportError(FinopsReportingError):
    """HTTP 500 typed error — executive report export failure.

    Raised by generate_executive_report() when StreamingResponse
    generator fails for CSV/PDF/Excel (PRD §F32.3-12 verbatim).
    """

    http_status: int = 500


class ExecutiveReportDeliveryError(FinopsReportingError):
    """HTTP 500 typed error — executive report delivery failure.

    Raised by executive_report_delivery cron when Slack/Email/S3
    delivery target is unreachable (PRD §F32.3-12 verbatim).
    """

    http_status: int = 500


class ExecutiveReportArchiveError(FinopsReportingError):
    """HTTP 500 typed error — executive report S3 archive failure.

    Raised by upload_executive_report() when boto3 put_object fails
    or presigned URL generation fails (PRD §F32.3-12 verbatim).
    """

    http_status: int = 500


# §F32.4 scheduled_dispatch_kst_cron (4 NEW)
class ScheduledDispatchError(FinopsReportingError):
    """HTTP 500 typed error — scheduled dispatch cron failure.

    Raised by schedule_executive_dispatch() when apscheduler job fails
    or delivery target unreachable (PRD §F32.4-10 verbatim).
    """

    http_status: int = 500


class CronExpressionInvalidError(FinopsReportingError):
    """HTTP 400 typed error — cron expression validation failure.

    Raised by schedule_executive_dispatch() when cron_expression is
    not parseable by apscheduler (PRD §F32.4-10 verbatim).
    """

    http_status: int = 400


class RecipientResolverError(FinopsReportingError):
    """HTTP 404 typed error — recipient resolution failure.

    Raised by recipient resolver when owner_only/executive_team/
    board_observers/custom_recipients strategy cannot resolve
    recipients (PRD §F32.4-10 verbatim).
    """

    http_status: int = 404


class DispatchIdempotencyViolationError(FinopsReportingError):
    """HTTP 422 typed error — dispatch idempotency violation.

    Raised by schedule_executive_dispatch() when duplicate dispatch
    detected for (tenant_id + dispatch_schedule + period_key) tuple
    (PRD §F32.4-10 verbatim).
    """

    http_status: int = 422


# §F32.5 tenant_scoped_executive_role_rbac (3 NEW)
class ExecutiveRolePermissionError(FinopsReportingError):
    """HTTP 403 typed error — executive role permission denied.

    Raised by require_executive_role() when role lacks executive access
    (e.g. tenant MEMBER attempting executive dashboard view)
    (PRD §F32.5-10 verbatim + AD-22 owner-only RBAC + Epic 12 2FA 챌린지).
    """

    http_status: int = 403


class TenantScopeViolationError(FinopsReportingError):
    """HTTP 403 typed error — cross-tenant access violation.

    Raised by require_executive_role() when actor_tenant_id differs
    from requested_tenant_id (PRD §F32.5-10 verbatim + CR 0-2 RLS).
    """

    http_status: int = 403


class CapabilityGateViolationError(FinopsReportingError):
    """HTTP 403 typed error — capability gate violation.

    Raised by require_finops_reporting() when tenant lacks FINOPS_REPORTING
    capability or any Phase 11~15 carry-over capability
    (PRD §F32.7-6 verbatim + CR 12-5 D-GATE-01 inversion).
    """

    http_status: int = 403


# §F32.7 reporting accuracy degradation (1 NEW)
class ReportingAccuracyDegradationError(FinopsReportingError):
    """HTTP 500 typed error — reporting accuracy degradation detected.

    Raised by cross_module_kpi.validate_kpi_accuracy() when KPI
    accuracy score drops below threshold (e.g. forecast_deviation_pct
    exceeds 10% for 3 consecutive periods) (PRD §F32.7 verbatim +
    Phase 14/15 accuracy tracker EXTENSION pattern).
    """

    http_status: int = 500


# ─────────────────────────────────────────────────────────────────────────────
# Phase 17 — FinOps Sustainability & Carbon Reporting typed exceptions
# (CR 12-5 D-14 envelope verbatim).
# m25_finops_sustainability — natural extension of m24_finops_reporting
# (Phase 16 wire `81ae00a`) + Phase 11~15 carry-over chain (PRD §F33 + AD-44).
# Routes through `FinopsError` ancestor (m19_finops base) → `BaseError` root
# so `error_handler` middleware envelope canonicalization (code / message_ko
# / details / trace_id / http_status) holds across all 6-module join
# paths.
# ─────────────────────────────────────────────────────────────────────────────
FINOPS_SUSTAINABILITY_MODULE_ID: str = "m25_finops_sustainability"


class FinopsSustainabilityError(FinopsError):
    """Base class for Phase 17 FinOps Sustainability & Carbon Reporting errors.

    Inherits from FinopsError (Phase 11 wire `e020ad0` m19_finops base)
    so all Phase 11~16 typed exceptions share the same envelope. Module
    tag is `m25_finops_sustainability` per Phase 17 AD-44 (a) decision
    (Phase 16 m24 + Phase 15 m23 + Phase 14 m22 + Phase 13 m21 + Phase 12 m20
    + Phase 11 m19 verbatim chain).

    All subclasses follow CR 12-5 D-14 typed exception envelope:
    http_status ∈ {400, 403, 404, 422, 500} matching the canonical
    REST/HTTP status code mapping (CR 11-4 P-015 verbatim).
    """

    http_status: int = 500


# §F33.1 carbon_emissions_aggregator (4 NEW)
class CarbonEmissionsRollupInvalidError(FinopsSustainabilityError):
    """HTTP 400 typed error — carbon emissions rollup invalid inputs.

    Raised by aggregate_carbon_emissions() when tenant_id is empty,
    scope_type invalid, or rollup missing required fields
    (PRD §F33.1-9 verbatim).
    """

    http_status: int = 400


class CarbonEmissionsRollupScopeError(FinopsSustainabilityError):
    """HTTP 404 typed error — carbon emissions rollup scope validation failure.

    Raised by aggregate_carbon_emissions() when scope_type is not in
    ALL_SCOPE_TYPES (tenant / department / cost_center / product_line)
    or scope_id is empty (PRD §F33.1-9 verbatim).
    """

    http_status: int = 404


class CarbonEmissionsRollupPeriodError(FinopsSustainabilityError):
    """HTTP 422 typed error — carbon emissions rollup period_key validation failure.

    Raised by aggregate_carbon_emissions() when period_key is not in
    valid format (YYYY-MM / YYYY-QN / YYYY) (PRD §F33.1-9 verbatim).
    """

    http_status: int = 422


class CarbonEmissionsCrossModuleJoinError(FinopsSustainabilityError):
    """HTTP 500 typed error — 6-module cross-join failure.

    Raised by aggregate_carbon_emissions() when the 6-module join
    (Phase 11 showback × carbon_intensity + Phase 12 anomaly +
    Phase 13 forecast + Phase 14 optimization + Phase 15 tag_governance +
    Phase 16 executive) fails (PRD §F33.1-11 verbatim).
    """

    http_status: int = 500


# §F33.2 sustainability_kpi_selector (1 NEW)
class SustainabilityKPIError(FinopsSustainabilityError):
    """HTTP 500 typed error — sustainability KPI calculation failure.

    Raised by select_sustainability_kpis() when any of the 8 NEW KPI
    calculations fails (total_carbon_emissions_kgco2e + scope1/2/3 +
    carbon_intensity_kgco2e_per_krw + data_center_pue +
    renewable_energy_pct + carbon_offset_kgco2e)
    (PRD §F33.2-11 verbatim).
    """

    http_status: int = 500


# §F33.3 sustainability_report_generation_engine (3 NEW)
class SustainabilityReportGenerationError(FinopsSustainabilityError):
    """HTTP 500 typed error — sustainability report generation failure.

    Raised by generate_sustainability_report() when reportlab PDF render
    or openpyxl Excel workbook fails (PRD §F33.3-12 verbatim).
    """

    http_status: int = 500


class SustainabilityReportExportError(FinopsSustainabilityError):
    """HTTP 500 typed error — sustainability report export failure.

    Raised by generate_sustainability_report() when CSV/Excel byte stream
    serialization fails (PRD §F33.3-12 verbatim).
    """

    http_status: int = 500


class SustainabilityReportArchiveError(FinopsSustainabilityError):
    """HTTP 500 typed error — sustainability report S3 archive failure.

    Raised by generate_sustainability_report() when S3 archive upload
    fails (PRD §F33.3-12 verbatim).
    """

    http_status: int = 500


# §F33.4 scheduled_sustainability_dispatch (4 NEW)
class ScheduledSustainabilityDispatchError(FinopsSustainabilityError):
    """HTTP 500 typed error — scheduled sustainability dispatch cron failure.

    Raised by schedule_sustainability_dispatch() when apscheduler job fails
    or delivery target unreachable (PRD §F33.4-10 verbatim).
    """

    http_status: int = 500


class SustainabilityCronExpressionInvalidError(FinopsSustainabilityError):
    """HTTP 400 typed error — sustainability cron expression validation failure.

    Raised by schedule_sustainability_dispatch() when cron_expression is
    not parseable by apscheduler (PRD §F33.4-10 verbatim).
    """

    http_status: int = 400


class SustainabilityRecipientResolverError(FinopsSustainabilityError):
    """HTTP 404 typed error — sustainability recipient resolution failure.

    Raised by recipient resolver when owner_only/sustainability_team/
    board_observers/custom_recipients strategy cannot resolve
    recipients (PRD §F33.4-10 verbatim).
    """

    http_status: int = 404


class SustainabilityDispatchIdempotencyViolationError(FinopsSustainabilityError):
    """HTTP 422 typed error — sustainability dispatch idempotency violation.

    Raised by schedule_sustainability_dispatch() when duplicate dispatch
    detected for (tenant_id + dispatch_schedule + period_key) tuple
    (PRD §F33.4-10 verbatim).
    """

    http_status: int = 422


# §F33.5 tenant-scoped sustainability role RBAC (3 NEW)
class SustainabilityRolePermissionError(FinopsSustainabilityError):
    """HTTP 403 typed error — sustainability role permission denied.

    Raised by require_sustainability_role() when role lacks sustainability access
    (e.g. tenant MEMBER attempting sustainability dashboard view)
    (PRD §F33.5-10 verbatim + AD-22 owner-only RBAC + Epic 12 2FA 챌린지).
    """

    http_status: int = 403


class SustainabilityTenantScopeViolationError(FinopsSustainabilityError):
    """HTTP 403 typed error — sustainability cross-tenant access violation.

    Raised by require_sustainability_role() when actor_tenant_id differs
    from requested_tenant_id (PRD §F33.5-10 verbatim + CR 0-2 RLS).
    """

    http_status: int = 403


class SustainabilityCapabilityGateViolationError(FinopsSustainabilityError):
    """HTTP 403 typed error — sustainability capability gate violation.

    Raised by require_finops_sustainability() when tenant lacks FINOPS_SUSTAINABILITY
    capability or any Phase 11~16 carry-over capability
    (PRD §F33.7-6 verbatim + CR 12-5 D-GATE-01 inversion).
    """

    http_status: int = 403


# §F33.7 sustainability accuracy degradation (1 NEW)
class SustainabilityAccuracyDegradationError(FinopsSustainabilityError):
    """HTTP 500 typed error — sustainability accuracy degradation detected.

    Raised by sustainability_kpi_selector.validate_kpi_accuracy() when
    sustainability KPI accuracy score drops below threshold
    (e.g. carbon_intensity_kgco2e_per_krw exceeds industry baseline for
    3 consecutive periods) (PRD §F33.7 verbatim + Phase 13/14 accuracy
    tracker EXTENSION pattern).
    """

    http_status: int = 500


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18 — FinOps Cloud Commitment Management typed exceptions
# (CR 12-5 D-14 envelope verbatim).
# m26_finops_commitment — natural extension of m25_finops_sustainability
# (Phase 17 wire `97cfe4e`) + Phase 11~16 carry-over chain (PRD §F34 + AD-45).
# Routes through `FinopsError` ancestor (m19_finops base) → `BaseError` root
# so `error_handler` middleware envelope canonicalization (code / message_ko
# / details / trace_id / http_status) holds across all 7-module join paths.
# ─────────────────────────────────────────────────────────────────────────────
FINOPS_COMMITMENT_MODULE_ID: str = "m26_finops_commitment"


class FinopsCommitmentError(FinopsError):
    """Base class for Phase 18 FinOps Cloud Commitment Management errors.

    Inherits from FinopsError (Phase 11 wire `e020ad0` m19_finops base)
    so all Phase 11~17 typed exceptions share the same envelope. Module
    tag is `m26_finops_commitment` per Phase 18 AD-45 (a) decision
    (Phase 17 m25 + Phase 16 m24 + Phase 15 m23 + Phase 14 m22 +
    Phase 13 m21 + Phase 12 m20 + Phase 11 m19 verbatim chain).

    All subclasses follow CR 12-5 D-14 typed exception envelope:
    http_status ∈ {400, 403, 404, 422, 500} matching the canonical
    REST/HTTP status code mapping (CR 11-4 P-015 verbatim).
    """

    http_status: int = 500


# §F34.1 commitment_inventory_aggregator (4 NEW)
class CommitmentInventoryAggregationError(FinopsCommitmentError):
    """HTTP 500 typed error — commitment inventory aggregation runtime failure.

    Raised by aggregate_commitment_inventory() when any of the 7-module
    cross-rollup compute_* helpers fails (Phase 11 showback × total_commitment
    + Phase 12 anomaly + Phase 13 forecast + Phase 14 optimization +
    Phase 15 tag_governance + Phase 16 executive + Phase 17 sustainability).
    Note: http_status=500 (runtime compute error, not validation error
    — Phase 17's RollupInvalidError uses 400 because rollup input
    validation; Phase 18's Aggregation uses 500 because compute pipeline
    runtime) (PRD §F34.1-9 verbatim).
    """

    http_status: int = 500


class CommitmentInventoryScopeError(FinopsCommitmentError):
    """HTTP 404 typed error — commitment inventory scope validation failure.

    Raised by aggregate_commitment_inventory() when scope_type is not in
    ALL_COMMITMENT_SCOPE_TYPES (tenant / department / cost_center /
    product_line) or scope_id is empty (PRD §F34.1-9 verbatim).
    """

    http_status: int = 404


class CommitmentInventoryPeriodError(FinopsCommitmentError):
    """HTTP 422 typed error — commitment inventory period_key validation failure.

    Raised by aggregate_commitment_inventory() when period_key is not in
    valid format (YYYY-MM / YYYY-QN / YYYY) (PRD §F34.1-9 verbatim).
    """

    http_status: int = 422


class CommitmentCrossModuleJoinError(FinopsCommitmentError):
    """HTTP 500 typed error — 7-module cross-join failure.

    Raised by aggregate_commitment_inventory() when the 7-module join
    (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast +
    Phase 14 optimization + Phase 15 tag_governance + Phase 16 executive +
    Phase 17 sustainability) fails, or when 5-cloud-provider
    breakdown join fails (PRD §F34.1-11 verbatim).
    """

    http_status: int = 500


# §F34.2 commitment_kpi_selector (1 NEW)
class CommitmentKPIError(FinopsCommitmentError):
    """HTTP 500 typed error — commitment KPI calculation failure.

    Raised by select_commitment_kpis() when any of the 8 NEW KPI
    calculations fails (total_commitment_value_krw + coverage_pct +
    utilization_pct + expiring_commitments_30d + recommended_purchase_krw
    + savings_realized_krw + idle_commitment_krw + renewal_decision_score)
    (PRD §F34.2-11 verbatim).
    """

    http_status: int = 500


# §F34.3 commitment_report_generation (3 NEW)
class CommitmentReportGenerationError(FinopsCommitmentError):
    """HTTP 500 typed error — commitment report generation failure.

    Raised by generate_commitment_report() when PDF/CSV/Excel
    generation fails (PRD §F34.3-12 verbatim).
    """

    http_status: int = 500


class CommitmentReportExportError(FinopsCommitmentError):
    """HTTP 500 typed error — commitment report export failure.

    Raised by export_commitment_report() when S3 archive upload or
    external recipient delivery fails (PRD §F34.3-12 verbatim).
    """

    http_status: int = 500


class CommitmentReportArchiveError(FinopsCommitmentError):
    """HTTP 500 typed error — commitment report archive failure.

    Raised by archive_commitment_report() when long-term S3 archive
    write fails (PRD §F34.3-12 verbatim).
    """

    http_status: int = 500


# §F34.4 scheduled_commitment_dispatch (4 NEW)
class ScheduledCommitmentDispatchError(FinopsCommitmentError):
    """HTTP 500 typed error — scheduled commitment dispatch failure.

    Raised by schedule_commitment_dispatch() when apscheduler
    registration or KST cron evaluation fails (PRD §F34.4-10 verbatim).
    """

    http_status: int = 500


class CommitmentCronExpressionInvalidError(FinopsCommitmentError):
    """HTTP 400 typed error — commitment cron expression invalid.

    Raised by resolve_cron_expression() or _validate_cron_expression()
    when the cron expression cannot be parsed by apscheduler
    (PRD §F34.4-9 verbatim).
    """

    http_status: int = 400


class CommitmentRecipientResolverError(FinopsCommitmentError):
    """HTTP 404 typed error — commitment recipient resolver failure.

    Raised by resolve_recipient_list() when recipient_strategy is
    invalid or custom_recipients not configured (PRD §F34.4-9 verbatim).
    """

    http_status: int = 404


class CommitmentDispatchIdempotencyViolationError(FinopsCommitmentError):
    """HTTP 422 typed error — commitment dispatch idempotency violation.

    Raised by dispatch_commitment_report() when (tenant_id +
    dispatch_schedule + period_key) tuple already exists (PRD §F34.4-10
    verbatim).
    """

    http_status: int = 422


# §F34.5 commitment role RBAC (3 NEW)
class CommitmentRolePermissionError(FinopsCommitmentError):
    """HTTP 403 typed error — commitment role permission denied.

    Raised by require_commitment_role() when user_role is not in
    {owner, commitment_viewer} (AD-22 owner-only RBAC + Epic 12 2FA
    챌린지 mandatory) (PRD §F34.5 verbatim).
    """

    http_status: int = 403


class CommitmentTenantScopeViolationError(FinopsCommitmentError):
    """HTTP 403 typed error — commitment tenant scope violation.

    Raised by require_commitment_role() when actor_tenant_id ≠
    requested_tenant_id (CR 0-2 RLS) (PRD §F34.5 verbatim).
    """

    http_status: int = 403


class CommitmentCapabilityGateViolationError(FinopsCommitmentError):
    """HTTP 403 typed error — commitment capability gate violation.

    Raised by require_finops_commitment dependency when tenant lacks
    Capability.FINOPS_COMMITMENT grant (CR 12-5 D-GATE-01 inversion)
    (PRD §F34.5 verbatim).
    """

    http_status: int = 403


# §F34.6 commitment accuracy degradation (1 NEW)
class CommitmentAccuracyDegradationError(FinopsCommitmentError):
    """HTTP 500 typed error — commitment accuracy degradation detected.

    Raised by commitment_kpi_selector.validate_kpi_accuracy() when
    commitment KPI accuracy score drops below threshold
    (e.g. utilization_pct exceeds industry baseline for
    3 consecutive periods) (PRD §F34.6 verbatim + Phase 13/14/17
    accuracy tracker EXTENSION pattern).
    """

    http_status: int = 500


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
    # Phase 13 FinOps forecast + capacity planning typed exceptions (CR 12-5 D-14)
    "FinopsForecastError",
    "FINOPS_FORECAST_MODULE_ID",
    "ForecastDefinitionInvalidError",
    "ForecastScopeInvalidError",
    "ForecastAccuracyInvalidError",
    "ForecastHistoryUnavailableError",
    "ForecastEngineError",
    "ForecastModelTrainingError",
    "ForecastSeasonalityDetectionError",
    "CapacityHeadroomAnalysisError",
    "CapacityThresholdBreachError",
    "CapacityMetricUnavailableError",
    "BudgetBurnRateProjectionError",
    "BudgetOverrunPredictionError",
    "ForecastAccuracyTrackingError",
    "ModelRetrainingTriggerError",
    "ModelPerformanceDegradationError",
    # Phase 14 FinOps optimization & rightsizing typed exceptions (CR 12-5 D-14)
    "FinopsOptimizationError",
    "FINOPS_OPTIMIZATION_MODULE_ID",
    "OptimizationDefinitionInvalidError",
    "OptimizationScopeInvalidError",
    "OptimizationInventoryUnavailableError",
    "RightsizingEngineError",
    "InstanceTypeMappingError",
    "RecommendationConfidenceLowError",
    "IdleResourceDetectionError",
    "IdleSeverityClassificationError",
    "IdleMetricUnavailableError",
    "CommitmentRecommendationError",
    "PricingDataUnavailableError",
    "BreakEvenCalculationError",
    "OptimizationAccuracyTrackingError",
    "OptimizationRetrainingTriggerError",
    "OptimizationPerformanceDegradationError",
    # Phase 15 FinOps tag governance & cost allocation typed exceptions (CR 12-5 D-14)
    "FinopsTagGovernanceError",
    "FINOPS_TAG_GOVERNANCE_MODULE_ID",
    "TagPolicyInvalidError",
    "TagPolicyScopeInvalidError",
    "TagPolicyHistoryUnavailableError",
    "TagEnforcementViolationError",
    "UntaggedResourceDetectionError",
    "UntaggedThresholdBreachError",
    "UntaggedMetricUnavailableError",
    "RemediationActionError",
    "AllocationRuleInvalidError",
    "AllocationRuleEvaluationError",
    "PercentageSumValidationError",
    "ConditionalRuleParseError",
    "ChargebackReconciliationError",
    "ReconciliationDeltaBreachError",
    "ReconciliationApprovalError",
    # Phase 16 FinOps reporting & executive dashboard typed exceptions (CR 12-5 D-14)
    "FinopsReportingError",
    "FINOPS_REPORTING_MODULE_ID",
    "ExecutiveRollupInvalidError",
    "ExecutiveRollupScopeError",
    "ExecutiveRollupPeriodError",
    "ExecutiveRollupCrossModuleJoinError",
    "ExecutiveReportGenerationError",
    "ExecutiveReportExportError",
    "ExecutiveReportDeliveryError",
    "ExecutiveReportArchiveError",
    "ScheduledDispatchError",
    "CronExpressionInvalidError",
    "RecipientResolverError",
    "DispatchIdempotencyViolationError",
    "ExecutiveRolePermissionError",
    "TenantScopeViolationError",
    "CapabilityGateViolationError",
    "ReportingAccuracyDegradationError",
    # Phase 17 FinOps sustainability & carbon reporting typed exceptions (CR 12-5 D-14)
    "FinopsSustainabilityError",
    "FINOPS_SUSTAINABILITY_MODULE_ID",
    "CarbonEmissionsRollupInvalidError",
    "CarbonEmissionsRollupScopeError",
    "CarbonEmissionsRollupPeriodError",
    "CarbonEmissionsCrossModuleJoinError",
    "SustainabilityKPIError",
    "SustainabilityReportGenerationError",
    "SustainabilityReportExportError",
    "SustainabilityReportArchiveError",
    "ScheduledSustainabilityDispatchError",
    "SustainabilityCronExpressionInvalidError",
    "SustainabilityRecipientResolverError",
    "SustainabilityDispatchIdempotencyViolationError",
    "SustainabilityRolePermissionError",
    "SustainabilityTenantScopeViolationError",
    "SustainabilityCapabilityGateViolationError",
    "SustainabilityAccuracyDegradationError",
    # Phase 18 FinOps cloud commitment management typed exceptions (CR 12-5 D-14)
    "FinopsCommitmentError",
    "FINOPS_COMMITMENT_MODULE_ID",
    "CommitmentInventoryAggregationError",
    "CommitmentInventoryScopeError",
    "CommitmentInventoryPeriodError",
    "CommitmentCrossModuleJoinError",
    "CommitmentKPIError",
    "CommitmentReportGenerationError",
    "CommitmentReportExportError",
    "CommitmentReportArchiveError",
    "ScheduledCommitmentDispatchError",
    "CommitmentCronExpressionInvalidError",
    "CommitmentRecipientResolverError",
    "CommitmentDispatchIdempotencyViolationError",
    "CommitmentRolePermissionError",
    "CommitmentTenantScopeViolationError",
    "CommitmentCapabilityGateViolationError",
    "CommitmentAccuracyDegradationError",
    # Phase 19 FinOps pricing, rate card & TCO modeling typed exceptions (CR 12-5 D-14)
    "FinopsPricingError",
    "FINOPS_PRICING_MODULE_ID",
    "PricingAggregationError",
    "PricingScopeError",
    "PricingPeriodError",
    "PricingCrossModuleJoinError",
    "PricingKPIError",
    "PricingReportGenerationError",
    "PricingReportExportError",
    "PricingReportArchiveError",
    "ScheduledPricingDispatchError",
    "PricingCronExpressionInvalidError",
    "PricingRecipientResolverError",
    "PricingDispatchIdempotencyViolationError",
    "PricingRolePermissionError",
    "PricingTenantScopeViolationError",
    "PricingCapabilityGateViolationError",
    "PricingAccuracyDegradationError",
    # Phase 21 FinOps reserved capacity planning typed exceptions (CR 12-5 D-14)
    "FinopsReservedCapacityError",
    "FINOPS_RESERVED_CAPACITY_MODULE_ID",
    "ReservedCapacityDemandForecastError",
    "ReservedCapacityDemandForecastScopeError",
    "ReservedCapacityDemandForecastPeriodError",
    "ReservedCapacityDemandForecastModuleError",
    "ReservedCapacityPlanningError",
    "ReservedCapacityPlanningScopeError",
    "ReservedCapacityPlanningTierError",
    "ReservedCapacityPlanningGuardError",
    "ReservedCapacityRecommendationError",
    "ReservedCapacityRecommendationConfidenceError",
    "ReservedCapacityRecommendationApprovalError",
    "ReservedCapacityRecommendationExecutionError",
    "ReservedCapacityOrchestratorError",
    "ReservedCapacityOrchestratorStepError",
    "ReservedCapacityDryRunError",
    "ReservedCapacityIdempotencyError",
]


# ─────────────────────────────────────────────────────────────────────────────
# Phase 19 — FinOps Pricing, Rate Card & TCO Modeling typed exceptions
# (CR 12-5 D-14 envelope verbatim).
# m27_finops_pricing — natural extension of m26_finops_commitment
# (Phase 18 wire `67059cf`) + Phase 11~17 carry-over chain (PRD §F35 + AD-46).
# Routes through `FinopsError` ancestor (m19_finops base) → `BaseError` root
# so `error_handler` middleware envelope canonicalization (code / message_ko
# / details / trace_id / http_status) holds across all 8-module join paths.
# ─────────────────────────────────────────────────────────────────────────────
FINOPS_PRICING_MODULE_ID: str = "m27_finops_pricing"


class FinopsPricingError(FinopsError):
    """Base class for Phase 19 FinOps Pricing, Rate Card & TCO Modeling errors.

    Inherits from FinopsError (Phase 11 wire `e020ad0` m19_finops base)
    so all Phase 11~18 typed exceptions share the same envelope. Module
    tag is `m27_finops_pricing` per Phase 19 AD-46 (a) decision
    (Phase 18 m26 + Phase 17 m25 + Phase 16 m24 + Phase 15 m23 +
    Phase 14 m22 + Phase 13 m21 + Phase 12 m20 + Phase 11 m19 verbatim chain).

    All subclasses follow CR 12-5 D-14 typed exception envelope:
    http_status ∈ {400, 403, 404, 422, 500} matching the canonical
    REST/HTTP status code mapping (CR 11-4 P-015 verbatim).
    """

    http_status: int = 500


# §F35.1 rate_card_aggregator (4 NEW)
class PricingAggregationError(FinopsPricingError):
    """HTTP 500 typed error — pricing rate card aggregation runtime failure.

    Raised by aggregate_rate_card_inventory() when any of the 8-module
    cross-rollup compute_* helpers fails (Phase 11 showback × blended_rate
    + Phase 12 anomaly + Phase 13 forecast + Phase 14 optimization +
    Phase 15 tag_governance + Phase 16 executive + Phase 17 sustainability +
    Phase 18 commitment). Note: http_status=500 (runtime compute error,
    not validation error — same pattern as Phase 18 CommitmentInventory
    AggregationError) (PRD §F35.1-9 verbatim).
    """

    http_status: int = 500


class PricingScopeError(FinopsPricingError):
    """HTTP 404 typed error — pricing scope validation failure.

    Raised by aggregate_rate_card_inventory() when scope_type is not in
    ALL_PRICING_SCOPE_TYPES (tenant / department / cost_center /
    product_line) or scope_id is empty (PRD §F35.1-9 verbatim).
    """

    http_status: int = 404


class PricingPeriodError(FinopsPricingError):
    """HTTP 422 typed error — pricing period_key validation failure.

    Raised by aggregate_rate_card_inventory() when period_key is not in
    valid format (YYYY-MM / YYYY-QN / YYYY) (PRD §F35.1-9 verbatim).
    """

    http_status: int = 422


class PricingCrossModuleJoinError(FinopsPricingError):
    """HTTP 500 typed error — 8-module cross-join failure.

    Raised by aggregate_rate_card_inventory() when the 8-module join
    (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast +
    Phase 14 optimization + Phase 15 tag_governance + Phase 16 executive +
    Phase 17 sustainability + Phase 18 commitment) fails, or when
    5-cloud-provider breakdown join fails, or when 6-pricing-model
    breakdown join fails (PRD §F35.1-11 verbatim).
    """

    http_status: int = 500


# §F35.2 tco_modeling_selector (1 NEW)
class PricingKPIError(FinopsPricingError):
    """HTTP 500 typed error — pricing KPI calculation failure.

    Raised by compute_tco_kpi_bundle() when any of the 8 NEW KPI
    calculations fails (total_blended_rate_krw_per_hour +
    effective_discount_pct + tco_1year_commitment_krw +
    tco_3year_commitment_krw + tco_on_demand_krw + cost_per_user_krw +
    cost_per_transaction_krw + unit_economics_score)
    (PRD §F35.2-11 verbatim).
    """

    http_status: int = 500


# §F35.3 pricing_report_generation_engine (3 NEW)
class PricingReportGenerationError(FinopsPricingError):
    """HTTP 500 typed error — pricing report generation failure.

    Raised by generate_pricing_report() when PDF/CSV/Excel
    generation fails (PRD §F35.3-12 verbatim).
    """

    http_status: int = 500


class PricingReportExportError(FinopsPricingError):
    """HTTP 500 typed error — pricing report export failure.

    Raised by export_pricing_report() when S3 archive upload or
    external recipient delivery fails (PRD §F35.3-12 verbatim).
    """

    http_status: int = 500


class PricingReportArchiveError(FinopsPricingError):
    """HTTP 500 typed error — pricing report archive failure.

    Raised by archive_pricing_report() when long-term S3 archive
    write fails (PRD §F35.3-12 verbatim).
    """

    http_status: int = 500


# §F35.4 scheduled_pricing_dispatch (4 NEW)
class ScheduledPricingDispatchError(FinopsPricingError):
    """HTTP 500 typed error — scheduled pricing dispatch failure.

    Raised by schedule_pricing_dispatch() when apscheduler
    registration or KST cron evaluation fails (PRD §F35.4-10 verbatim).
    """

    http_status: int = 500


class PricingCronExpressionInvalidError(FinopsPricingError):
    """HTTP 400 typed error — pricing cron expression invalid.

    Raised by resolve_cron_expression() or _validate_cron_expression()
    when the cron expression cannot be parsed by apscheduler
    (PRD §F35.4-9 verbatim).
    """

    http_status: int = 400


class PricingRecipientResolverError(FinopsPricingError):
    """HTTP 404 typed error — pricing recipient resolver failure.

    Raised by resolve_recipient_list() when recipient_strategy is
    invalid or custom_recipients not configured (PRD §F35.4-9 verbatim).
    """

    http_status: int = 404


class PricingDispatchIdempotencyViolationError(FinopsPricingError):
    """HTTP 422 typed error — pricing dispatch idempotency violation.

    Raised by dispatch_pricing_report() when (tenant_id +
    dispatch_schedule + period_key) tuple already exists (PRD §F35.4-10
    verbatim).
    """

    http_status: int = 422


# §F35.5 tenant_scoped_pricing_role_rbac (3 NEW)
class PricingRolePermissionError(FinopsPricingError):
    """HTTP 403 typed error — pricing role permission denied.

    Raised by require_pricing_role() when user_role is not in
    {owner, pricing_viewer} (AD-22 owner-only RBAC + Epic 12 2FA
    챌린지 mandatory) (PRD §F35.5 verbatim).
    """

    http_status: int = 403


class PricingTenantScopeViolationError(FinopsPricingError):
    """HTTP 403 typed error — pricing tenant scope violation.

    Raised by require_pricing_role() when actor_tenant_id ≠
    requested_tenant_id (CR 0-2 RLS) (PRD §F35.5 verbatim).
    """

    http_status: int = 403


class PricingCapabilityGateViolationError(FinopsPricingError):
    """HTTP 403 typed error — pricing capability gate violation.

    Raised by require_finops_pricing dependency when tenant lacks
    Capability.FINOPS_PRICING grant (CR 12-5 D-GATE-01 inversion)
    (PRD §F35.5 verbatim).
    """

    http_status: int = 403


# §F35.7 pricing accuracy degradation (1 NEW)
class PricingAccuracyDegradationError(FinopsPricingError):
    """HTTP 500 typed error — pricing accuracy degradation detected.

    Raised by tco_modeling_selector.validate_kpi_accuracy() when
    pricing KPI accuracy score drops below threshold
    (e.g. unit_economics_score below industry baseline for
    3 consecutive periods) (PRD §F35.7 verbatim + Phase 13/14/17/18
    accuracy tracker EXTENSION pattern).
    """

    http_status: int = 500


# ════════════════════════════════════════════════════════════════════════════
# §F36 Phase 20 FinOps Multi-Cloud Cost Unified Reconciliation
# (16 NEW typed exceptions — CR 12-5 D-14 envelope verbatim pattern)
# ════════════════════════════════════════════════════════════════════════════
#
# Phase 20 wire (cj-style 144번째) — 16 NEW typed exceptions per
# AD-47 (a)~(g) 7 sub-decisions. Mirrors Phase 11~19 typed exception
# envelope pattern verbatim.
#
# Hierarchy:
#   FinopsError
#     └── FinopsMultiCloudError
#           ├── MultiCloudRateCardReconciliationError (500)
#           ├── MultiCloudRateCardScopeError (404)
#           ├── MultiCloudRateCardPeriodError (422)
#           ├── MultiCloudRateCardProviderError (502)
#           ├── MultiCloudCostReconciliationError (500)
#           ├── MultiCloudCostScopeError (404)
#           ├── MultiCloudCostPeriodError (422)
#           ├── MultiCloudCostProviderError (502)
#           ├── NegotiationBotError (500)
#           ├── NegotiationBotGuardError (500)
#           ├── NegotiationBotConfidenceError (500)
#           ├── NegotiationBotAutoTriggerError (500)
#           ├── BlendedUnblendedTrackerError (500)
#           ├── BlendedUnblendedDriftError (500)
#           ├── MarketplaceSaaSPricingIntegrationError (500)
#           └── MarketplaceSaaSPricingFreshnessError (500)


class FinopsMultiCloudError(FinopsError):
    """Base class for all Phase 20 FinOps Multi-Cloud Cost Unified Reconciliation errors.

    Phase 20 wire (cj-style 144번째) — mirrors FinopsPricingError
    Phase 19 wire `8db3cfc`, FinopsCommitmentError Phase 18 wire
    `67059cf`, FinopsSustainabilityError Phase 17 wire `97cfe4e`,
    FinopsReportingError Phase 16 wire `81ae00a` hierarchy verbatim.

    AD-47 FinOps Multi-Cloud Cost Unified Reconciliation (a)~(g) 7
    sub-decisions + CR 12-5 D-14 typed exception envelope verbatim.
    """


# §F36.1 multi_cloud_rate_card_reconciliation (4 NEW)
class MultiCloudRateCardReconciliationError(FinopsMultiCloudError):
    """HTTP 500 typed error — multi-cloud rate card reconciliation failure.

    Phase 20 wire (cj-style 144번째) — raised by
    reconcile_multi_cloud_rate_cards() when primary_rate cannot be
    computed (no_rate_card_sources_found) or when variance threshold
    detection fires (PRD §F36.1-3 + §F36.1-7 verbatim).
    """

    http_status: int = 500

    def __init__(self, reason: str, tenant_id: str | None = None, **kwargs: object) -> None:
        self.reason = reason
        self.tenant_id = tenant_id
        super().__init__(
            f"Multi-cloud rate card reconciliation failed: reason={reason} "
            f"tenant_id={tenant_id}",
            **kwargs,
        )


class MultiCloudRateCardScopeError(FinopsMultiCloudError):
    """HTTP 404 typed error — multi-cloud rate card scope_type invalid.

    Phase 20 wire (cj-style 144번째) — mirrors PricingScopeError
    Phase 19 wire `8db3cfc` verbatim. Raised when scope_type not in
    ALL_MULTI_CLOUD_SCOPE_TYPES (PRD §F36.1-4 verbatim).
    """

    http_status: int = 404

    def __init__(
        self,
        scope_type: str,
        allowed: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        self.scope_type = scope_type
        self.allowed = allowed or []
        super().__init__(
            f"Invalid multi-cloud rate card scope: {scope_type} "
            f"(allowed: {self.allowed})",
            **kwargs,
        )


class MultiCloudRateCardPeriodError(FinopsMultiCloudError):
    """HTTP 422 typed error — multi-cloud rate card period_key invalid.

    Phase 20 wire (cj-style 144번째) — mirrors PricingPeriodError
    Phase 19 wire `8db3cfc` verbatim. Raised when period_key format
    invalid (PRD §F36.1-10 verbatim + freshness tracking).
    """

    http_status: int = 422

    def __init__(self, period_key: str, **kwargs: object) -> None:
        self.period_key = period_key
        super().__init__(
            f"Invalid multi-cloud rate card period_key: {period_key}",
            **kwargs,
        )


class MultiCloudRateCardProviderError(FinopsMultiCloudError):
    """HTTP 502 typed error — multi-cloud rate card provider API failure.

    Phase 20 wire (cj-style 144번째) — mirrors PricingAggregationError
    Phase 19 wire `8db3cfc` provider subset verbatim. Raised when
    cloud_provider not in ALL_MULTI_CLOUD_PROVIDERS or when 5 cloud
    provider API call fails (AWS EDP / Azure EA / GCP CUD Pricing /
    Naver Cloud / KT Cloud, PRD §F36.1-5 verbatim).
    """

    http_status: int = 502

    def __init__(
        self,
        cloud_provider: str,
        allowed: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        self.cloud_provider = cloud_provider
        self.allowed = allowed or []
        super().__init__(
            f"Multi-cloud rate card provider error: {cloud_provider} "
            f"(allowed: {self.allowed})",
            **kwargs,
        )


# §F36.2 multi_cloud_cost_reconciliation (4 NEW)
class MultiCloudCostReconciliationError(FinopsMultiCloudError):
    """HTTP 500 typed error — multi-cloud cost reconciliation failure.

    Phase 20 wire (cj-style 144번째) — raised by
    reconcile_multi_cloud_costs() when primary_cost cannot be computed
    or when cost_variance_pct > 3.0% alert fires
    (PRD §F36.2-4 verbatim).
    """

    http_status: int = 500

    def __init__(self, reason: str, tenant_id: str | None = None, **kwargs: object) -> None:
        self.reason = reason
        self.tenant_id = tenant_id
        super().__init__(
            f"Multi-cloud cost reconciliation failed: reason={reason} "
            f"tenant_id={tenant_id}",
            **kwargs,
        )


class MultiCloudCostScopeError(FinopsMultiCloudError):
    """HTTP 404 typed error — multi-cloud cost reconciliation scope invalid.

    Phase 20 wire (cj-style 144번째) — mirrors MultiCloudRateCardScopeError
    verbatim for cost reconciliation.
    """

    http_status: int = 404

    def __init__(
        self,
        scope_type: str,
        allowed: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        self.scope_type = scope_type
        self.allowed = allowed or []
        super().__init__(
            f"Invalid multi-cloud cost scope: {scope_type} "
            f"(allowed: {self.allowed})",
            **kwargs,
        )


class MultiCloudCostPeriodError(FinopsMultiCloudError):
    """HTTP 422 typed error — multi-cloud cost reconciliation period invalid."""

    http_status: int = 422

    def __init__(self, period_key: str, **kwargs: object) -> None:
        self.period_key = period_key
        super().__init__(
            f"Invalid multi-cloud cost period_key: {period_key}",
            **kwargs,
        )


class MultiCloudCostProviderError(FinopsMultiCloudError):
    """HTTP 502 typed error — multi-cloud cost provider API failure.

    Phase 20 wire (cj-style 144번째) — raised when AWS Cost Explorer /
    Azure Cost Management / GCP Billing / Naver Cloud Billing /
    KT Cloud Billing API call fails (PRD §F36.2-3 verbatim).
    """

    http_status: int = 502

    def __init__(
        self,
        cloud_provider: str,
        allowed: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        self.cloud_provider = cloud_provider
        self.allowed = allowed or []
        super().__init__(
            f"Multi-cloud cost provider error: {cloud_provider} "
            f"(allowed: {self.allowed})",
            **kwargs,
        )


# §F36.3 negotiation_bot (4 NEW)
class NegotiationBotError(FinopsMultiCloudError):
    """HTTP 500 typed error — negotiation bot failure.

    Phase 20 wire (cj-style 144번째) — 3 cloud provider support
    (AWS EDP + Azure EA + GCP CUD). Raised by run_negotiation_bot()
    when recommendation cannot be generated (PRD §F36.3 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        reason: str,
        tenant_id: str | None = None,
        cloud_provider: str | None = None,
        **kwargs: object,
    ) -> None:
        self.reason = reason
        self.tenant_id = tenant_id
        self.cloud_provider = cloud_provider
        super().__init__(
            f"Negotiation bot failed: reason={reason} tenant_id={tenant_id} "
            f"cloud_provider={cloud_provider}",
            **kwargs,
        )


class NegotiationBotGuardError(FinopsMultiCloudError):
    """HTTP 500 typed error — negotiation bot guard violation.

    Phase 20 wire (cj-style 144번째) — MINIMUM_SAVINGS_PCT=5.0 +
    MINIMUM_SAVINGS_KRW=1M + MAX_NEGOTIATIONS_PER_MONTH=3 +
    MAX_AUTO_TRIGGER_PER_DAY=1 (PRD §F36.3-5 verbatim). Raised when
    savings_below_threshold or monthly_quota_exceeded.
    """

    http_status: int = 500

    def __init__(
        self,
        guard: str,
        threshold: float,
        actual: float,
        **kwargs: object,
    ) -> None:
        self.guard = guard
        self.threshold = threshold
        self.actual = actual
        super().__init__(
            f"Negotiation bot guard violation: {guard} "
            f"threshold={threshold} actual={actual}",
            **kwargs,
        )


class NegotiationBotConfidenceError(FinopsMultiCloudError):
    """HTTP 500 typed error — negotiation bot confidence below threshold.

    Phase 20 wire (cj-style 144번째) — confidence_score < 60 →
    recommendation_status=low_confidence (PRD §F36.3-7 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        confidence_score: float,
        threshold: float,
        **kwargs: object,
    ) -> None:
        self.confidence_score = confidence_score
        self.threshold = threshold
        super().__init__(
            f"Negotiation bot confidence too low: score={confidence_score} "
            f"threshold={threshold}",
            **kwargs,
        )


class NegotiationBotAutoTriggerError(FinopsMultiCloudError):
    """HTTP 500 typed error — negotiation bot auto-trigger violation.

    Phase 20 wire (cj-style 144번째) — MAX_AUTO_TRIGGER_PER_DAY=1 +
    MAX_NEGOTIATIONS_PER_MONTH=3 + idempotency_key duplicate (PRD
    §F36.3-5 + §F36.3-11 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        reason: str,
        idempotency_key: str | None = None,
        **kwargs: object,
    ) -> None:
        self.reason = reason
        self.idempotency_key = idempotency_key
        super().__init__(
            f"Negotiation bot auto-trigger violation: reason={reason} "
            f"idempotency_key={idempotency_key}",
            **kwargs,
        )


# §F36.4 blended_unblended_tracker (2 NEW)
class BlendedUnblendedTrackerError(FinopsMultiCloudError):
    """HTTP 500 typed error — blended/unblended tracker failure.

    Phase 20 wire (cj-style 144번째) — 3 cloud provider support
    (AWS + Azure + GCP). Raised by track_blended_unblended_diff() when
    tracking cannot complete (PRD §F36.4-2 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        reason: str,
        cloud_provider: str | None = None,
        **kwargs: object,
    ) -> None:
        self.reason = reason
        self.cloud_provider = cloud_provider
        super().__init__(
            f"Blended/unblended tracker failed: reason={reason} "
            f"cloud_provider={cloud_provider}",
            **kwargs,
        )


class BlendedUnblendedDriftError(FinopsMultiCloudError):
    """HTTP 500 typed error — blended/unblended drift detected.

    Phase 20 wire (cj-style 144번째) — rate_diff_pct > 5% → alert
    (PRD §F36.4-10 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        rate_diff_pct: float,
        threshold: float,
        cloud_provider: str | None = None,
        **kwargs: object,
    ) -> None:
        self.rate_diff_pct = rate_diff_pct
        self.threshold = threshold
        self.cloud_provider = cloud_provider
        super().__init__(
            f"Blended/unblended drift detected: rate_diff_pct={rate_diff_pct} "
            f"threshold={threshold} cloud_provider={cloud_provider}",
            **kwargs,
        )


# §F36.5 marketplace_saas_pricing_integrator (2 NEW)
class MarketplaceSaaSPricingIntegrationError(FinopsMultiCloudError):
    """HTTP 500 typed error — marketplace SaaS pricing integration failure.

    Phase 20 wire (cj-style 144번째) — 5 marketplace source support
    (AWS + Azure + GCP + Naver + KT Marketplace). Raised by
    integrate_marketplace_saas_pricing() when adapter parse fails
    (PRD §F36.5-3 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        reason: str,
        marketplace_source: str | None = None,
        **kwargs: object,
    ) -> None:
        self.reason = reason
        self.marketplace_source = marketplace_source
        super().__init__(
            f"Marketplace SaaS pricing integration failed: reason={reason} "
            f"marketplace_source={marketplace_source}",
            **kwargs,
        )


class MarketplaceSaaSPricingFreshnessError(FinopsMultiCloudError):
    """HTTP 500 typed error — marketplace SaaS pricing freshness stale.

    Phase 20 wire (cj-style 144번째) — now - last_synced_at > 24h →
    alert (PRD §F36.5-4 verbatim).
    """

    http_status: int = 500

    def __init__(
        self,
        marketplace_source: str,
        staleness_hours: float,
        threshold: float,
        **kwargs: object,
    ) -> None:
        self.marketplace_source = marketplace_source
        self.staleness_hours = staleness_hours
        self.threshold = threshold
        super().__init__(
            f"Marketplace SaaS pricing stale: source={marketplace_source} "
            f"staleness_hours={staleness_hours} threshold={threshold}",
            **kwargs,
        )


class ScheduledMultiCloudDispatchError(FinopsMultiCloudError):
    """HTTP 500 typed error — scheduled multi-cloud dispatch failure.

    Phase 20 wire (cj-style 144번째) — generic scheduled multi-cloud
    dispatch failure (PRD §F36.6-5 verbatim). Mirrors
    ScheduledCommitmentDispatchError (Phase 18).
    """

    http_status: int = 500

    def __init__(self, reason: str, tenant_id: str = "", **kwargs: object) -> None:
        self.reason = reason
        self.tenant_id = tenant_id
        super().__init__(
            f"Scheduled multi-cloud dispatch failure: reason={reason} "
            f"tenant_id={tenant_id}",
            **kwargs,
        )


class MultiCloudCronExpressionInvalidError(FinopsMultiCloudError):
    """HTTP 400 typed error — invalid multi-cloud cron expression.

    Phase 20 wire (cj-style 144번째) — cron_trigger.from_crontab() raises
    ValueError for invalid cron (PRD §F36.6-5 verbatim). Mirrors
    PricingCronExpressionInvalidError (Phase 19).
    """

    http_status: int = 400

    def __init__(
        self,
        reason: str,
        allowed: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        self.reason = reason
        self.allowed = allowed or []
        super().__init__(
            f"Invalid multi-cloud cron expression: reason={reason} "
            f"allowed={allowed}",
            **kwargs,
        )


class MultiCloudDispatchIdempotencyViolationError(FinopsMultiCloudError):
    """HTTP 422 typed error — multi-cloud dispatch idempotency violation.

    Phase 20 wire (cj-style 144번째) — same (tenant_id + dispatch_schedule
    + period_key) tuple already dispatched → flag (PRD §F36.6-7 verbatim).
    Mirrors PricingDispatchIdempotencyViolationError (Phase 19).
    """

    http_status: int = 422

    def __init__(self, reason: str, tenant_id: str = "", **kwargs: object) -> None:
        self.reason = reason
        self.tenant_id = tenant_id
        super().__init__(
            f"Multi-cloud dispatch idempotency violation: reason={reason} "
            f"tenant_id={tenant_id}",
            **kwargs,
        )


class MultiCloudRecipientResolverError(FinopsMultiCloudError):
    """HTTP 404 typed error — multi-cloud recipient resolver failure.

    Phase 20 wire (cj-style 144번째) — recipient_strategy unknown or no
    recipients match (PRD §F36.6-4 verbatim). Mirrors
    PricingRecipientResolverError (Phase 19).
    """

    http_status: int = 404

    def __init__(
        self,
        reason: str,
        allowed: list[str] | None = None,
        **kwargs: object,
    ) -> None:
        self.reason = reason
        self.allowed = allowed or []
        super().__init__(
            f"Multi-cloud recipient resolver failure: reason={reason} "
            f"allowed={allowed}",
            **kwargs,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 21 — FinOps Reserved Capacity Planning typed exceptions
# (CR 12-5 D-14 envelope verbatim).
# m29_finops_reserved_capacity — natural extension of m28_finops_multi_cloud
# (Phase 20 wire `52dad7f`) + Phase 11~19 carry-over chain (PRD §F37 + AD-49).
# Routes through `FinopsError` ancestor (m19_finops base) → `BaseError` root
# so `error_handler` middleware envelope canonicalization (code / message_ko
# / details / trace_id / http_status) holds across all 5-module join paths
# (Phase 13 forecast + Phase 14 optimization + Phase 18 commitment +
# Phase 19 pricing + Phase 20 multi_cloud).
# ─────────────────────────────────────────────────────────────────────────────
FINOPS_RESERVED_CAPACITY_MODULE_ID: str = "m29_finops_reserved_capacity"


class FinopsReservedCapacityError(FinopsError):
    """Base class for Phase 21 FinOps Reserved Capacity Planning errors.

    Inherits from FinopsError (Phase 11 wire `e020ad0` m19_finops base)
    so all Phase 11~20 typed exceptions share the same envelope. Module
    tag is `m29_finops_reserved_capacity` per Phase 21 AD-49 (a) decision
    (Phase 20 m28 + Phase 19 m27 + Phase 18 m26 + Phase 17 m25 +
    Phase 16 m24 + Phase 15 m23 + Phase 14 m22 + Phase 13 m21 +
    Phase 12 m20 + Phase 11 m19 verbatim chain).

    All subclasses follow CR 12-5 D-14 typed exception envelope:
    http_status ∈ {400, 403, 404, 409, 422, 500, 502} matching the canonical
    REST/HTTP status code mapping (CR 11-4 P-015 verbatim).
    """

    http_status: int = 500


# §F37.1 demand_forecast_aggregator (4 NEW)
class ReservedCapacityDemandForecastError(FinopsReservedCapacityError):
    """HTTP 500 typed error — demand forecast 5-module cross-join runtime failure.

    Raised by aggregate_demand_forecast() when 5-module weighted average
    fails (Phase 13 forecast + Phase 14 optimization + Phase 18 commitment +
    Phase 19 pricing + Phase 20 multi_cloud), or when seasonal_factor /
    growth_rate_pct / confidence_interval computation fails (PRD §F37.1-9
    verbatim).
    """

    http_status: int = 500


class ReservedCapacityDemandForecastScopeError(FinopsReservedCapacityError):
    """HTTP 404 typed error — demand forecast industry/scope validation failure.

    Raised by aggregate_demand_forecast() when industry is not in
    ALL_ORCHESTRATION_SCOPES (manufacturing / service /
    manufacturing_service / manufacturing_service_other) (PRD §F37.1-9
    verbatim).
    """

    http_status: int = 404


class ReservedCapacityDemandForecastPeriodError(FinopsReservedCapacityError):
    """HTTP 422 typed error — demand forecast period_key validation failure.

    Raised by aggregate_demand_forecast() when period_key is not in valid
    format (YYYY-MM / YY-MM / YYYY) (PRD §F37.1-9 verbatim).
    """

    http_status: int = 422


class ReservedCapacityDemandForecastModuleError(FinopsReservedCapacityError):
    """HTTP 502 typed error — demand forecast 5-module upstream join failure.

    Raised by aggregate_demand_forecast() when 5-module inputs (phase_13 +
    phase_14 + phase_18 + phase_19 + phase_20) are missing or any module
    returns invalid value (PRD §F37.1-9 verbatim). 502 (Bad Gateway)
    semantics: upstream module dependency not reachable / invalid.
    """

    http_status: int = 502


# §F37.2 capacity_planning_aggregator (4 NEW)
class ReservedCapacityPlanningError(FinopsReservedCapacityError):
    """HTTP 500 typed error — capacity planning 6-tier selection runtime failure.

    Raised by plan_reserved_capacity() when 6-tier selection algorithm
    (AD-49 (b)) fails or break-even / headroom / target_units / savings
    computation fails (PRD §F37.2-9 verbatim).
    """

    http_status: int = 500


class ReservedCapacityPlanningScopeError(FinopsReservedCapacityError):
    """HTTP 404 typed error — capacity planning industry/scope validation failure.

    Raised by plan_reserved_capacity() when industry is not in
    ALL_ORCHESTRATION_SCOPES (PRD §F37.2-9 verbatim).
    """

    http_status: int = 404


class ReservedCapacityPlanningTierError(FinopsReservedCapacityError):
    """HTTP 422 typed error — capacity planning tier selection validation failure.

    Raised by plan_reserved_capacity() or helper functions when selected
    tier is not in ALL_RESERVED_CAPACITY_TIERS (6 tier enum: 1y_no_upfront
    + 1y_partial_upfront + 1y_all_upfront + 3y_no_upfront +
    3y_partial_upfront + 3y_all_upfront) (PRD §F37.2-9 verbatim).
    """

    http_status: int = 422


class ReservedCapacityPlanningGuardError(FinopsReservedCapacityError):
    """HTTP 500 typed error — capacity planning minimum savings threshold guard.

    Raised by plan_reserved_capacity() when estimated_savings_pct <
    MINIMUM_SAVINGS_PCT=5.0 OR estimated_savings_krw < MINIMUM_SAVINGS_KRW=1M
    OR break_even_utilization_pct < MINIMUM_BREAK_EVEN_UTILIZATION_PCT=70.0
    (PRD §F37.2-9 + AD-49 (b) verbatim). Surface in strict-mode orchestrator
    path; non-strict path returns rejected plan with capacity_plan_status
    field set to 'rejected'.
    """

    http_status: int = 500


# §F37.3 commitment_recommendation_engine (4 NEW)
class ReservedCapacityRecommendationError(FinopsReservedCapacityError):
    """HTTP 500 typed error — commitment recommendation engine runtime failure.

    Raised by generate_commitment_recommendation() when confidence_score
    (utilization_stability × 0.4 + historical_accuracy × 0.3 +
    demand_forecast_confidence_pct × 0.3) or risk_score (savings_pct × 0.4
    + commitment_term × 0.3 + commitment_flexibility × 0.3) computation
    fails (PRD §F37.3-9 + AD-49 (c) verbatim).
    """

    http_status: int = 500


class ReservedCapacityRecommendationConfidenceError(FinopsReservedCapacityError):
    """HTTP 500 typed error — confidence score below LOW_CONFIDENCE threshold.

    Raised by generate_commitment_recommendation() when confidence_score
    falls below LOW_CONFIDENCE execution_strategy threshold. Strict-mode
    caller (orchestrator) uses this to flag low-confidence recommendations
    for manual review (PRD §F37.3-9 verbatim).
    """

    http_status: int = 500


class ReservedCapacityRecommendationApprovalError(FinopsReservedCapacityError):
    """HTTP 403 typed error — owner approval flow required for high-value plan.

    Raised by generate_commitment_recommendation() or downstream executor
    when high_value_flag (estimated_annual_savings_krw >=
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR=10M) AND
    execution_strategy == OWNER_APPROVAL_REQUIRED — owner-only RBAC + Epic 12
    2FA 챌린지 mandatory path. 403 (Forbidden) semantics: caller lacks
    owner role approval (PRD §F37.3-9 + AD-49 (g) verbatim).
    """

    http_status: int = 403


class ReservedCapacityRecommendationExecutionError(FinopsReservedCapacityError):
    """HTTP 500 typed error — execution_strategy runtime failure.

    Raised by generate_commitment_recommendation() when execution_strategy
    (auto_execute_ready / manual_review_required / owner_approval_required /
    low_confidence) cannot be determined or downstream execution pipeline
    (auto_execute + manual_review + owner_approval + low_confidence paths)
    fails (PRD §F37.3-9 verbatim).
    """

    http_status: int = 500


# §F37.4 reserved_capacity_orchestrator (4 NEW)
class ReservedCapacityOrchestratorError(FinopsReservedCapacityError):
    """HTTP 500 typed error — orchestrator runtime failure.

    Raised by orchestrate_reserved_capacity() when composition_step_chain
    5 step (demand_forecast → capacity_planning → commitment_recommendation
    → approval → execute) orchestration fails, or cadence schedule (4 KST
    pytz) initialization fails (PRD §F37.4-9 + AD-49 (d) verbatim).
    """

    http_status: int = 500


class ReservedCapacityOrchestratorStepError(FinopsReservedCapacityError):
    """HTTP 500 typed error — composition_step_chain step failure.

    Raised by orchestrate_reserved_capacity() when any of the 5 composition
    steps (demand_forecast / capacity_planning / commitment_recommendation /
    approval / execute) fails. Carries step_index + step_name for downstream
    observability (PRD §F37.4-9 verbatim).
    """

    http_status: int = 500


class ReservedCapacityDryRunError(FinopsReservedCapacityError):
    """HTTP 500 typed error — dry-run mode violation.

    Raised by orchestrate_reserved_capacity() when dry_run=True but caller
    attempts to mutate persistent state (e.g., commitment execution) outside
    the preview-only path. dry-run mode is enforced via
    reserved_capacity_dry_run_executed audit action + phase_21_orchestration_preview
    preview table (PRD §F37.4-9 + AD-49 (f) verbatim).
    """

    http_status: int = 500


class ReservedCapacityIdempotencyError(FinopsReservedCapacityError):
    """HTTP 409 typed error — orchestration idempotency violation.

    Raised by orchestrate_reserved_capacity() when the same
    (tenant_id + period_key + cadence) tuple has already been orchestrated
    within the same period. 409 (Conflict) semantics: caller must wait for
    next cadence window or explicitly override via owner_approval flow
    (PRD §F37.4-9 verbatim).
    """

    http_status: int = 409


# ─────────────────────────────────────────────────────────────────────────────
# Phase 22 wire (cj-style 160번째, 2026-08-27 KST) — FinOps Chargeback
# Settlement territory — 16 NEW typed exceptions (CR 12-5 D-14 envelope).
# m30_finops_chargeback_settlement — natural extension of m29_finops_reserved_capacity
# (Phase 21 wire `1b101bf`) + Phase 11~20 carry-over chain (PRD §F38 + AD-50).
# Routes through `FinopsError` ancestor (Phase 11 wire `e020ad0` m19_finops base)
# → `BaseError` root so `error_handler` middleware envelope canonicalization
# (code / message_ko / details / trace_id / http_status) holds across all
# 4 sub-functions (settlement_rules + allocation_engine + invoice_generation +
# reconciliation). Mirrors Phase 21 FinopsReservedCapacityError verbatim with
# 4 NEW exception classes per sub-§ section (§F38.1~§F38.4 mapped 1:1 to
# settlement_rules / allocation_engine / invoice_generation / reconciliation).
# ─────────────────────────────────────────────────────────────────────────────
FINOPS_CHARGEBACK_SETTLEMENT_MODULE_ID: str = "m30_finops_chargeback_settlement"


class FinopsChargebackSettlementError(FinopsError):
    """Base class for Phase 22 FinOps Chargeback Settlement errors.

    Inherits from FinopsError (Phase 11 wire `e020ad0` m19_finops base) so
    all Phase 11~21 typed exceptions share the same envelope. Module tag
    is `m30_finops_chargeback_settlement` per Phase 22 AD-50 (a) decision
    (Phase 21 m29 + Phase 20 m28 + Phase 19 m27 + Phase 18 m26 + Phase 17
    m25 + Phase 16 m24 + Phase 15 m23 + Phase 14 m22 + Phase 13 m21 +
    Phase 12 m20 + Phase 11 m19 verbatim chain).

    All subclasses follow CR 12-5 D-14 typed exception envelope verbatim
    (Phase 21 reserved_capacity chain pattern):
    http_status ∈ {400, 403, 404, 409, 422, 500, 502} matching the canonical
    REST/HTTP status code mapping (CR 11-4 P-015 verbatim).

    Settlement layer wiring:
    - §F38.1 settlement_rules engine (4 NEW):
      ChargebackSettlementRuleError + ChargebackSettlementRuleScopeError +
      ChargebackSettlementRuleTypeError + ChargebackSettlementRuleModuleError
    - §F38.2 allocation_engine (4 NEW):
      ChargebackAllocationEngineError +
      ChargebackAllocationDimensionError +
      ChargebackAllocationWeightError +
      ChargebackAllocationUnbalancedError
    - §F38.3 invoice_generation (4 NEW):
      ChargebackInvoiceGenerationError +
      ChargebackInvoiceFormatError +
      ChargebackInvoiceTenantError +
      ChargebackInvoiceSizeError
    - §F38.4 reconciliation (4 NEW):
      ChargebackReconciliationError +
      ChargebackReconciliationToleranceError +
      ChargebackReconciliationRetryError +
      ChargebackReconciliationApprovalError
    """

    http_status: int = 500


# §F38.1 settlement_rules engine (4 NEW)
class ChargebackSettlementRuleError(FinopsChargebackSettlementError):
    """HTTP 500 typed error — settlement rule runtime failure.

    Raised by settlement_rules.create_settlement_rule() /
    update_settlement_rule() / list_settlement_rules() when 5-module
    weighted join (Phase 11 chargeback + Phase 18 commitment + Phase 19
    pricing + Phase 20 multi_cloud + Phase 21 reserved_capacity weighted
    average via FIVE_MODULE_WEIGHTS) fails, or when rule_id resolution /
    audit-first INSERT persistence / dry-run preview writes fail
    (PRD §F38.1-10 verbatim + AD-50 (a) verbatim).
    """

    http_status: int = 500


class ChargebackSettlementRuleScopeError(FinopsChargebackSettlementError):
    """HTTP 404 typed error — settlement rule tenant/scope validation failure.

    Raised by settlement_rules.* when tenant_id is missing or when target
    period_key is not in valid format (YYYY-MM / YY-MM / YYYY) (PRD §F38.1-10
    verbatim).
    """

    http_status: int = 404


class ChargebackSettlementRuleTypeError(FinopsChargebackSettlementError):
    """HTTP 422 typed error — settlement rule_type validation failure.

    Raised by settlement_rules.* when rule_type is not in
    ALL_SETTLEMENT_RULE_TYPES (4 enum: flat_fee + proportional_allocation +
    metered_volume + tag_weighted) (PRD §F38.1-10 verbatim + AD-50 (a)
    verbatim).
    """

    http_status: int = 422


class ChargebackSettlementRuleModuleError(FinopsChargebackSettlementError):
    """HTTP 502 typed error — settlement 5-module upstream join failure.

    Raised by settlement_rules.* when 5-module inputs (Phase 11 chargeback +
    Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud + Phase 21
    reserved_capacity) are missing or any module returns invalid value
    (PRD §F38.1-10 verbatim + AD-50 (a) verbatim). 502 (Bad Gateway)
    semantics: upstream module dependency not reachable / invalid.
    """

    http_status: int = 502


# §F38.2 allocation_engine (4 NEW)
class ChargebackAllocationEngineError(FinopsChargebackSettlementError):
    """HTTP 500 typed error — allocation engine runtime failure.

    Raised by allocation_engine.compute_allocation() when 5-dimension
    weighted allocation (cost_center × 0.30 + department × 0.25 +
    business_unit × 0.20 + tag × 0.15 + tenant × 0.10) fails
    (PRD §F38.2-6 verbatim + AD-50 (b) verbatim).
    """

    http_status: int = 500


class ChargebackAllocationDimensionError(FinopsChargebackSettlementError):
    """HTTP 422 typed error — allocation dimension validation failure.

    Raised by allocation_engine.* when allocation dimension is not in
    ALL_ALLOCATION_DIMENSIONS (5 enum: cost_center + department +
    business_unit + tag + tenant) (PRD §F38.2-6 verbatim + AD-50 (b)
    verbatim).
    """

    http_status: int = 422


class ChargebackAllocationWeightError(FinopsChargebackSettlementError):
    """HTTP 422 typed error — allocation weight validation failure.

    Raised by allocation_engine.* when ALLOCATION_DIMENSION_WEIGHTS sum
    != 1.0 (i.e., {cost_center: 0.30, department: 0.25, business_unit:
    0.20, tag: 0.15, tenant: 0.10} = 1.0 invariant) or when any weight
    is negative (PRD §F38.2-6 verbatim + AD-50 (b) verbatim).
    """

    http_status: int = 422


class ChargebackAllocationUnbalancedError(FinopsChargebackSettlementError):
    """HTTP 422 typed error — allocation line imbalance invariant.

    Raised by allocation_engine.compute_allocation() when sum of
    allocated amounts across all dimensions differs from total settlement
    amount by > 0.01 KRW round-off tolerance (banker's rounding CR 5-1
    preserved) (PRD §F38.2-6 verbatim + AD-50 (b) verbatim).
    """

    http_status: int = 422


# §F38.3 invoice_generation (4 NEW)
class ChargebackInvoiceGenerationError(FinopsChargebackSettlementError):
    """HTTP 500 typed error — invoice generation runtime failure.

    Raised by invoice_generator.generate_invoice() when PDF/XLSX/CSV
    template rendering (reportlab 4.0.7 + xlsxwriter 3.1.9 + csv stdlib)
    fails, or when noto-sans-cjk-kr font embedding / A4 landscape layout
    fails (PRD §F38.3-8 verbatim + AD-50 (c) verbatim + AD-14 stack pin).
    """

    http_status: int = 500


class ChargebackInvoiceFormatError(FinopsChargebackSettlementError):
    """HTTP 422 typed error — invoice format validation failure.

    Raised by invoice_generator.generate_invoice() when format is not in
    ALL_INVOICE_FORMATS (3 enum: pdf + xlsx + csv) (PRD §F38.3-8 verbatim +
    AD-50 (c) verbatim).
    """

    http_status: int = 422


class ChargebackInvoiceTenantError(FinopsChargebackSettlementError):
    """HTTP 404 typed error — invoice tenant validation failure.

    Raised by invoice_generator.* when tenant_id is missing or tenant has
    no settlement rules defined for the target period_key (PRD §F38.3-8
    verbatim + AD-50 (c) verbatim).
    """

    http_status: int = 404


class ChargebackInvoiceSizeError(FinopsChargebackSettlementError):
    """HTTP 409 typed error — invoice size exceedance guard.

    Raised by invoice_generator.generate_invoice() when rendered byte
    stream exceeds MAX_INVOICE_BYTES (10MB) or number of allocation lines
    exceeds MAX_ALLOCATION_LINES (10,000) (PRD §F38.3-8 verbatim +
    AD-50 (c) verbatim). 409 (Conflict) semantics: caller must split
    period or contact admin.
    """

    http_status: int = 409


# §F38.4 reconciliation (4 NEW)
class ChargebackReconciliationError(FinopsChargebackSettlementError):
    """HTTP 500 typed error — reconciliation 3-way match runtime failure.

    Raised by reconciliation.reconcile_settlement() when 3-way match
    computation (allocation_amount vs invoice_amount vs ledger_amount)
    fails (PRD §F38.4-7 verbatim + AD-50 (d) verbatim).
    """

    http_status: int = 500


class ChargebackReconciliationToleranceError(FinopsChargebackSettlementError):
    """HTTP 422 typed error — reconciliation tolerance exceedance.

    Raised by reconciliation.reconcile_settlement() when
    variance_pct > RECONCILIATION_TOLERANCE_PCT (1.0%) — strict-mode caller
    raises this; non-strict path returns reconciliation_status='variance_detected'
    (PRD §F38.4-7 verbatim + AD-50 (d) verbatim).
    """

    http_status: int = 422


class ChargebackReconciliationRetryError(FinopsChargebackSettlementError):
    """HTTP 502 typed error — reconciliation auto-retry exhausted.

    Raised by reconciliation.reconcile_settlement() after 3 auto-retries
    (RECONCILIATION_MAX_RETRIES=3) all fail with tolerance exceeded.
    Routes reconciliation_status='retry_exhausted' + admin email alert
    + Epic 12 2FA 챌린지 mandatory path for human intervention
    (PRD §F38.4-7 verbatim + AD-50 (d) verbatim + AD-50 (g) verbatim).
    502 (Bad Gateway) semantics: upstream ledger/chargeback/invoice source
    not resolvable after retries.
    """

    http_status: int = 502


class ChargebackReconciliationApprovalError(FinopsChargebackSettlementError):
    """HTTP 403 typed error — reconciliation owner approval required.

    Raised by reconciliation.reconcile_settlement() when
    estimated_annual_settlement_krw >=
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR (10M) AND pending approval —
    owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory (PRD §F38.4-7
    verbatim + AD-50 (d) verbatim + AD-50 (g) verbatim). 403 (Forbidden)
    semantics: caller lacks owner role 2FA challenge clearance.
    """

    http_status: int = 403


# ── FinOps Unit Economics typed exceptions ──────
# Phase 23 (cj-style 164번째 wire) — CR 12-5 D-14 typed exception
# envelope applied to 16 NEW exceptions shared across unit_economics_engine
# + cost_per_business_unit + cost_per_transaction + margin_analysis +
# scheduled_unit_economics_calculation modules. Module identifier
# m31_finops_unit_economics (mirrors m30_finops_chargeback_settlement +
# m29_finops_reserved_capacity + m28_finops_multi_cloud pattern).

# Module identifier used by typed exception envelopes (mirrors
# m30_finops_chargeback_settlement Phase 22 wire + m29_finops_reserved_
# capacity Phase 21 wire + m28_finops_multi_cloud Phase 20 wire pattern).
FINOPS_UNIT_ECONOMICS_MODULE_ID: str = "m31_finops_unit_economics"


class FinopsUnitEconomicsError(FinopsError):
    """Base for FinOps unit economics typed exceptions.

    Provides FINOPS_UNIT_ECONOMICS_MODULE_ID class attribute + envelope
    shape `{code, message_ko, details, trace_id, module_id}` shared by
    all 15 NEW exception subclasses below (Phase 23 wire cj-style 164).
    """

    module_id: str = FINOPS_UNIT_ECONOMICS_MODULE_ID


class UnitEconomicsDimensionError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — unit_economics dimension validation failure.

    Raised by unit_economics_engine.compute_unit_economics() when
    dimension is not in ALL_UNIT_ECONOMICS_DIMENSIONS (cost_center /
    department / business_unit / tag / tenant — 5-dim cross-join derived
    from Phase 22 allocation_lines ledger data).
    """

    http_status: int = 400


class UnitEconomicsAggregationError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — unit_economics aggregation level validation failure.

    Raised by unit_economics_engine.compute_unit_economics() when
    aggregation_level is not in ALL_UNIT_ECONOMICS_AGGREGATION_LEVELS
    (daily / weekly / monthly).
    """

    http_status: int = 400


class UnitEconomicsVerificationError(FinopsUnitEconomicsError):
    """HTTP 500 typed error — unit_economics 5-dim cross-join verification failure.

    Raised by unit_economics_engine._compute_5_dim_cross_join() when
    ledger-key dedup detects duplicate ledger keys OR total verification
    ±0.01 KRW tolerance fails after 3 auto-retries.
    """

    http_status: int = 500


class UnitEconomicsTagError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — unit_economics tag filter validation failure.

    Raised by cost_per_business_unit.refresh_cost_per_business_unit()
    when tag_key / tag_value_pattern fails 5-layer defense OR when
    per-tenant override chain (tenant_settings.unit_economics_overrides.
    dimension_weights) fails validation.
    """

    http_status: int = 400


class UnitEconomicsTransactionError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — cost_per_transaction validation failure.

    Raised by cost_per_transaction.compute_cost_per_transaction() when
    transaction_id 부재 시 `None` 반환 honest DEFER (3 NEW filter dimensions
    transaction_tag + environment_tag + application_tag validation
    failure).
    """

    http_status: int = 400


class UnitEconomicsRevenueError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — margin_analysis revenue tag validation failure.

    Raised by margin_analysis.execute_margin_analysis() when revenue tag
    is missing or fails 6-layer defense (OPTIONAL margin analysis skip
    when revenue tag 부재 시 honest DEFER discipline preserved).
    """

    http_status: int = 400


class UnitEconomicsMarginError(FinopsUnitEconomicsError):
    """HTTP 500 typed error — margin_analysis computation failure.

    Raised by margin_analysis.execute_margin_analysis() when margin =
    revenue_amount - allocated_amount fails Decimal precision OR when
    margin_pct = margin / revenue division overflows.
    """

    http_status: int = 500


class UnitEconomicsOverrideError(FinopsUnitEconomicsError):
    """HTTP 409 typed error — unit_economics per-tenant override conflict.

    Raised by cost_per_business_unit.refresh_cost_per_business_unit()
    when per-tenant override (tenant_settings.unit_economics_overrides.
    dimension_weights) conflicts with system default weights. 409
    (Conflict) semantics: caller must resolve override chain manually.
    """

    http_status: int = 409


class UnitEconomicsApprovalRequiredError(FinopsUnitEconomicsError):
    """HTTP 403 typed error — unit_economics owner approval + 2FA 챌린지 required.

    Raised by margin_analysis.execute_margin_analysis() when high-value
    margin positive ≥ 10M KRW/year AND adjustment pending — owner-only
    RBAC AD-22 + Epic 12 2FA 챌린지 mandatory (PRD §F39.4-5 verbatim +
    AD-51 (g) verbatim). 403 (Forbidden) semantics: caller lacks owner
    role 2FA challenge clearance.
    """

    http_status: int = 403


class UnitEconomicsIndustryError(FinopsUnitEconomicsError):
    """HTTP 403 typed error — industry-agnostic capability gate fail.

    Raised by capability.require_finops_unit_economics when industry
    grant is missing (should not occur — 4-industry grants ✅/✅/✅/✅
    industry-agnostic CR 12-1 L4 verbatim — but defensive guard
    preserves typed envelope).
    """

    http_status: int = 403


class UnitEconomicsCadenceError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — scheduled_unit_economics_calculation cadence validation failure.

    Raised by scheduled_unit_economics_calculation.
    schedule_cadence_calculation() when cadence is not in
    ALL_UNIT_ECONOMICS_CADENCES (daily / weekly / monthly / quarterly).
    """

    http_status: int = 400


class UnitEconomicsDrillDownError(FinopsUnitEconomicsError):
    """HTTP 404 typed error — unit_economics drill-down target not found.

    Raised by unit_economics_engine._compute_drill_down() when
    drill-down target dimension_value is not found in the 5-dim
    cross-join result (404 Not Found semantics).
    """

    http_status: int = 404


class UnitEconomicsAlertError(FinopsUnitEconomicsError):
    """HTTP 500 typed error — unit_economics margin alert dispatch failure.

    Raised by margin_analysis._dispatch_margin_alert() when Slack DM
    or alert dispatch fails (negative margin → tenant_owner Slack DM
    or high-value margin positive → 2FA 챌린지 approval chain).
    """

    http_status: int = 500


class UnitEconomicsTagFilterError(FinopsUnitEconomicsError):
    """HTTP 400 typed error — cost_per_transaction tag_filter validation failure.

    Raised by cost_per_transaction.compute_cost_per_transaction() when
    tag_filter (transaction_tag / environment_tag / application_tag
    3 NEW filter dimensions) format invalid OR regex pattern fails
    safe-regex validator.
    """

    http_status: int = 400


class UnitEconomicsPermissionError(FinopsUnitEconomicsError):
    """HTTP 403 typed error — unit_economics role-based access denied.

    Raised by routes when caller role is neither
    Role.UNIT_ECONOMICS_OPERATOR nor Role.UNIT_ECONOMICS_VIEWER
    (AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory). 403
    (Forbidden) semantics: caller lacks required role.
    """

    http_status: int = 403


# Phase 24 (cj-style 169번째 wire) — FinOps Budget Planning pre-allocation
# layer typed exception envelope (PRD §F40.1~§F40.8 verbatim + AD-52
# (a)~(g) 7 sub-decisions). Module identifier m24_finops_budget_planning
# (mirrors m31_finops_unit_economics + m30_finops_chargeback_settlement +
# m29_finops_reserved_capacity + m28_finops_multi_cloud pattern).

# Module identifier used by typed exception envelopes (mirrors
# m31_finops_unit_economics Phase 23 wire + m30_finops_chargeback_
# settlement Phase 22 wire + m29_finops_reserved_capacity Phase 21 wire
# pattern).
FINOPS_BUDGET_PLANNING_MODULE_ID: str = "m24_finops_budget_planning"


class FinopsBudgetPlanningError(FinopsError):
    """Base for FinOps Budget Planning typed exceptions.

    Provides FINOPS_BUDGET_PLANNING_MODULE_ID class attribute + envelope
    shape `{code, message_ko, details, trace_id, module_id}` shared by
    all 16 NEW exception subclasses below (Phase 24 wire cj-style 169).
    """

    module_id: str = FINOPS_BUDGET_PLANNING_MODULE_ID


class BudgetPlanNotFoundError(FinopsBudgetPlanningError):
    """HTTP 404 typed error — budget plan not found.

    Raised by budget_planning_routes.get_budget_plan_endpoint() when
    plan_id lookup returns no rows.
    """

    http_status: int = 404


class BudgetPlanPeriodError(FinopsBudgetPlanningError):
    """HTTP 400 typed error — budget plan period_key format validation failure.

    Raised by budget_plan_engine.validate_budget_plan() when period_key
    does not match period_type regex (annual YYYY / quarterly YYYY-Qn /
    monthly YYYY-MM).
    """

    http_status: int = 400


class BudgetPlanOverlapError(FinopsBudgetPlanningError):
    """HTTP 409 typed error — budget plan period overlap detected.

    Raised by budget_plan_engine._detect_period_overlap() when a new plan
    overlaps with an existing plan for the same tenant+period.
    """

    http_status: int = 409


class BudgetPlanLifecycleError(FinopsBudgetPlanningError):
    """HTTP 400 typed error — budget plan lifecycle transition invalid.

    Raised by budget_plan_engine.update_budget_plan() when the
    requested lifecycle value is not in
    ALL_BUDGET_PLAN_LIFECYCLE_VALUES (draft / pending_approval /
    approved / closed).
    """

    http_status: int = 400


class BudgetAllocationError(FinopsBudgetPlanningError):
    """HTTP 500 typed error — budget allocation computation failure.

    Raised by budget_allocation.allocate_budget() when allocation
    produces invalid output (e.g. dimension resolution failure).
    """

    http_status: int = 500


class BudgetAllocationVerificationError(FinopsBudgetPlanningError):
    """HTTP 500 typed error — budget allocation total verification failure.

    Raised by budget_allocation._verify_total() after 3 auto-retries
    still fail the ±0.01 KRW total tolerance check (CR 5-1 Decimal
    precision banker's rounding verbatim).
    """

    http_status: int = 500


class BudgetAllocationDimensionError(FinopsBudgetPlanningError):
    """HTTP 400 typed error — budget allocation dimension validation failure.

    Raised by budget_allocation.validate_budget_allocation() when the
    requested dimension is not in ALL_BUDGET_PLAN_DIMENSION_VALUES
    (cost_center / department / business_unit / tag / tenant — 5-dim
    cross-join derived from Phase 22 allocation_lines + Phase 23
    unit_economics_results ledger data).
    """

    http_status: int = 400


class BudgetAllocationZeroAmountError(FinopsBudgetPlanningError):
    """HTTP 400 typed error — budget allocation zero/negative amount guard.

    Raised by budget_allocation.validate_budget_allocation() when
    allocated_amount is negative (zero is allowed for preserved-amount
    lines but negative is forbidden).
    """

    http_status: int = 400


class BudgetApprovalStepError(FinopsBudgetPlanningError):
    """HTTP 400 typed error — budget approval step validation failure.

    Raised by budget_approval_workflow.validate_approval_chain() when
    the sequential step_index ordering is invalid or step count exceeds
    APPROVAL_CHAIN_MAX_STEPS=10.
    """

    http_status: int = 400


class BudgetApproval2FARequiredError(FinopsBudgetPlanningError):
    """HTTP 403 typed error — Epic 12 2FA 챌린지 mandatory for high-value.

    Raised by budget_approval_workflow.record_approval_decision() when
    a high-value plan (≥10M KRW/year) is approved without a verified
    RFC 6238 TOTP. Redirects to /account/security?reason=2fa_required
    (CR 12-1 L4 precedent + AD-52 (g) verbatim).
    """

    http_status: int = 403


class BudgetApprovalTimeoutError(FinopsBudgetPlanningError):
    """HTTP 500 typed error — budget approval Slack DM timeout.

    Raised by budget_approval_workflow._send_slack_dm() when the Slack
    DM to the approver times out (SLACK_DM_TIMEOUT_SECONDS=30).
    """

    http_status: int = 500


class BudgetVsActualError(FinopsBudgetPlanningError):
    """HTTP 500 typed error — budget vs actual variance computation failure.

    Raised by budget_vs_actual.compute_budget_vs_actual() when the
    JOIN between Phase 22 settlement_results and Phase 24 BudgetPlan
    fails (tenant_id / period_key / dimension mismatch).
    """

    http_status: int = 500


class BudgetAlertError(FinopsBudgetPlanningError):
    """HTTP 500 typed error — budget alert generation failure.

    Raised by budget_alert.trigger_over_budget_alert() when the
    notification channels (Slack / email / Teams) all fail to send.
    """

    http_status: int = 500


class BudgetAlertThresholdError(FinopsBudgetPlanningError):
    """HTTP 400 typed error — budget alert threshold validation failure.

    Raised by budget_alert._severity_from_pct() when the input
    variance_pct is malformed (non-numeric / negative).
    """

    http_status: int = 400


class BudgetPlanningPermissionError(FinopsBudgetPlanningError):
    """HTTP 403 typed error — budget_planning role-based access denied.

    Raised by routes when caller role is neither
    Role.BUDGET_PLANNING_OPERATOR nor Role.BUDGET_PLANNING_VIEWER
    (AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory). 403
    (Forbidden) semantics: caller lacks required role.
    """

    http_status: int = 403


# ─────────────────────────────────────────────────────────────────
# Phase 25 (cj-style 174th follow-up wire) — FINOPS_VENDOR_MANAGEMENT
# typed exceptions. 16 NEW classes (CR 12-5 D-14 envelope verbatim
# mirroring Phase 24 wire + Phase 23 wire + Phase 22 wire + Phase 21
# wire + Phase 20 wire + Phase 19 wire + Phase 18 wire + Phase 17 wire
# + Phase 16 wire + Phase 15 wire + Phase 14 wire + Phase 13 wire +
# Phase 12 wire + Phase 11 wire pattern verbatim). All inherit from
# FinopsVendorManagementError (which inherits from FinopsError).
# ─────────────────────────────────────────────────────────────────

# Module identifier used by typed exception envelopes (mirrors
# m25_finops_vendor_management Phase 25 wire + m24_finops_budget_planning
# Phase 24 wire + m31_finops_unit_economics Phase 23 wire +
# m30_finops_chargeback_settlement Phase 22 wire + m29_finops_reserved_
# capacity Phase 21 wire + m28_finops_multi_cloud Phase 20 wire pattern).
FINOPS_VENDOR_MANAGEMENT_MODULE_ID: str = "m25_finops_vendor_management"


class FinopsVendorManagementError(FinopsError):
    """Base for FinOps Vendor Management typed exceptions.

    Provides FINOPS_VENDOR_MANAGEMENT_MODULE_ID class attribute + envelope
    shape `{code, message_ko, details, trace_id, module_id}` shared by
    all 16 NEW exception subclasses below (Phase 25 wire cj-style 174th
    follow-up).
    """

    module_id: str = FINOPS_VENDOR_MANAGEMENT_MODULE_ID


class VendorCatalogError(FinopsVendorManagementError):
    """HTTP 500 typed error — vendor catalog engine failure.

    Raised by vendor_catalog_engine.create_vendor() / update_vendor() /
    change_vendor_status() / blacklist_vendor() when the catalog
    write path fails (DB integrity error, RLS rejection, etc.).
    """

    http_status: int = 500


class VendorCatalogNotFoundError(FinopsVendorManagementError):
    """HTTP 404 typed error — vendor catalog row not found.

    Raised by vendor_management_routes.get_vendor_endpoint() when
    vendor_id lookup returns no rows.
    """

    http_status: int = 404


class VendorCatalogCategoryError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor category taxonomy validation failure.

    Raised by vendor_catalog_engine.validate_vendor_scores() when the
    requested vendor_category is not in ALL_VENDOR_CATEGORY_VALUES
    (cloud / saas / outsourcing / consulting / hardware / other —
    6-category taxonomy per AD-53 (a) verbatim).
    """

    http_status: int = 400


class VendorCatalogLifecycleError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor 4-state lifecycle transition invalid.

    Raised by vendor_catalog_engine.change_vendor_status() when the
    requested status value is not in ALL_VENDOR_STATUS_VALUES
    (active / inactive / under_review / blacklisted).
    """

    http_status: int = 400


class VendorCatalogBlacklistError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor blacklist compliance gate failure.

    Raised by vendor_catalog_engine.blacklist_vendor() when the
    blacklist reason or severity is malformed (AD-53 (g) verbatim).
    """

    http_status: int = 400


class VendorSelectionError(FinopsVendorManagementError):
    """HTTP 500 typed error — vendor 5-dim weighted selection failure.

    Raised by vendor_selection_engine.score_vendor() when the
    dimension score validation fails or the weighted total exceeds
    SELECTION_SCORE_VERSION_MAX=100.00 strict range.
    """

    http_status: int = 500


class VendorSelectionThresholdError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor selection threshold validation failure.

    Raised by vendor_selection_engine.apply_vendor_selection_threshold()
    when the threshold value is outside [0.0, 100.0] range or
    SELECTION_THRESHOLD_DEFAULT=60.00 default is overridden incorrectly.
    """

    http_status: int = 400


class VendorSelectionWeightError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor selection dimension weight validation failure.

    Raised by vendor_selection_engine.override_selection_score_per_tenant()
    when the per-tenant override weights do not sum to 1.00 (cost +
    performance + reliability + compliance + strategic_fit).
    """

    http_status: int = 400


class VendorContractLifecycleError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor contract sequential lifecycle transition invalid.

    Raised by vendor_contract_lifecycle_engine.advance_contract_lifecycle()
    when the requested transition violates the sequential state machine
    (draft → pending_approval → approved → active → expiring_soon →
    renewed/expired/terminated).
    """

    http_status: int = 400


class VendorContractApproval2FARequiredError(FinopsVendorManagementError):
    """HTTP 403 typed error — Epic 12 2FA 챌린지 mandatory for high-value.

    Raised by vendor_contract_lifecycle_engine.record_approval_step()
    when a high-value contract (≥10M KRW/year) is approved without a
    verified RFC 6238 TOTP. Redirects to /account/security?reason=
    2fa_required (CR 12-1 L4 precedent + AD-53 (g) verbatim).
    """

    http_status: int = 403


class VendorContractApprovalTimeoutError(FinopsVendorManagementError):
    """HTTP 500 typed error — vendor contract approval Slack DM timeout.

    Raised by vendor_contract_lifecycle_engine._send_slack_dm() when
    the Slack DM to the approver times out (SLACK_DM_TIMEOUT_SECONDS=30).
    """

    http_status: int = 500


class VendorPerformanceEvaluationError(FinopsVendorManagementError):
    """HTTP 500 typed error — vendor performance evaluation failure.

    Raised by vendor_performance_evaluation.evaluate_vendor_performance()
    when the 4-dim scoring computation fails (sla_compliance 0.30 +
    cost_efficiency 0.25 + support_quality 0.25 + innovation 0.20).
    """

    http_status: int = 500


class VendorPerformanceSeverityError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor performance severity classification failure.

    Raised by vendor_performance_evaluation.classify_performance_severity()
    when the score falls outside the 4 severity bands
    (low / medium / high / critical).
    """

    http_status: int = 400


class VendorSpendAttributionError(FinopsVendorManagementError):
    """HTTP 500 typed error — vendor spend attribution cross-budget reconciliation failure.

    Raised by vendor_spend_attribution.reconcile_cross_budget() when
    the JOIN between Phase 22 settlement_results + Phase 24
    BudgetPlan fails (tenant_id / period_key / vendor_id mismatch).
    """

    http_status: int = 500


class VendorRiskError(FinopsVendorManagementError):
    """HTTP 400 typed error — vendor risk score threshold validation failure.

    Raised by vendor_catalog_engine.compute_vendor_risk_score() when
    the score falls outside the 3-tier risk bands
    (low < VENDOR_RISK_LOW_THRESHOLD + medium + high > VENDOR_RISK_HIGH_THRESHOLD).
    """

    http_status: int = 400


class VendorPermissionError(FinopsVendorManagementError):
    """HTTP 403 typed error — vendor_management role-based access denied.

    Raised by routes when caller role is neither
    Role.VENDOR_MANAGEMENT_OPERATOR nor Role.VENDOR_MANAGEMENT_VIEWER
    (AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory for
    high-value ≥ 10M KRW/year contracts). 403 (Forbidden) semantics:
    caller lacks required role.
    """

    http_status: int = 403


# ── FinOps Cost Anomaly ML Prediction typed exceptions ─────
# Phase 26 (cj-style 184번째 wire follow-up) — CR 12-5 D-14 typed exception
# envelope applied to 16 NEW exceptions shared across
# cost_anomaly_ml_prediction modules (serializers + engine +
# model_registry + training_pipeline + scoring + ensemble_consensus +
# scheduled_jobs). Module identifier m34_finops_cost_anomaly_ml_prediction.

# Module identifier used by typed exception envelopes (mirrors
# m22_finops_optimization + m23_finops_vendor_management + Phase 12
# m20_finops_anomaly pattern).
FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID: str = "m34_finops_cost_anomaly_ml_prediction"


class FinopsCostAnomalyMLPredictionError(FinopsError):
    """Base for FinOps Cost Anomaly ML Prediction typed exceptions.

    Provides FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID class attribute +
    envelope shape `{code, message_ko, details, trace_id, module_id}` shared
    by all 16 NEW exception subclasses below (Phase 26 wire cj-style 181st
    follow-up sprint — ML-driven pre-detection layer complementary to
    Phase 12 rule-based 사후 detection).
    """

    module_id: str = FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID


# ── Cost Anomaly ML Prediction core (3 NEW) ─────
class AnomalyMLPredictionNotFoundError(FinopsCostAnomalyMLPredictionError):
    """HTTP 404 typed error — anomaly_ml_prediction row not found.

    Raised by anomaly_ml_prediction_engine.read_prediction() /
    update_prediction() / retire_prediction() when
    anomaly_ml_prediction_id lookup returns no rows
    (PRD §F42.4 verbatim — prediction lifecycle: created → updated → retired).
    """

    http_status: int = 404


class AnomalyMLPredictionStatusTransitionError(FinopsCostAnomalyMLPredictionError):
    """HTTP 400 typed error — anomaly_ml_prediction lifecycle state transition failure.

    Raised by anomaly_ml_prediction_engine.update_prediction() /
    retire_prediction() when the requested status transition is not in
    ALL_ANOMALY_ML_PREDICTION_STATUS_VALUES (active / deprecated / retired)
    or violates lifecycle invariants (PRD §F42.4 verbatim).
    """

    http_status: int = 400


class AnomalyMLPredictionComplianceViolationError(FinopsCostAnomalyMLPredictionError):
    """HTTP 403 typed error — anomaly_ml_prediction compliance gate failure.

    Raised by anomaly_ml_prediction_engine.retire_prediction() when
    Epic 12 2FA 챌린지 mandatory gate (AD-22 owner-only RBAC) is
    bypassed for high-value ≥ 10M KRW impact forecast (AD-55 (g) verbatim).
    """

    http_status: int = 403


# ── Model Registry (4 NEW) ─────
class ModelRegistryEntryNotFoundError(FinopsCostAnomalyMLPredictionError):
    """HTTP 404 typed error — model_registry row not found.

    Raised by anomaly_ml_model_registry.update_model_status() /
    list_active_models() / deprecate_model() when model_id lookup
    returns no rows (semver versioning 0.1.0, AD-55 (b) verbatim).
    """

    http_status: int = 404


class ModelArtifactChecksumMismatchError(FinopsCostAnomalyMLPredictionError):
    """HTTP 422 typed error — model artifact checksum mismatch.

    Raised by anomaly_ml_model_registry.register_model() when the
    computed SHA-256 checksum of the model artifact does not match
    the registered checksum (artifact integrity, AD-55 (b) verbatim).
    """

    http_status: int = 422


class ModelStatusTransitionError(FinopsCostAnomalyMLPredictionError):
    """HTTP 400 typed error — model lifecycle state transition failure.

    Raised by anomaly_ml_model_registry.change_model_status() when
    the requested status value is not in ALL_MODEL_STATUS_VALUES
    (training / deploying / active / deprecated / retired) or violates
    the lifecycle invariants (AD-55 (b) verbatim).
    """

    http_status: int = 400


class ModelArtifactSizeError(FinopsCostAnomalyMLPredictionError):
    """HTTP 413 typed error — model artifact size exceeds limit.

    Raised by anomaly_ml_model_registry.register_model() when the
    uploaded artifact exceeds MODEL_ARTIFACT_MAX_SIZE_BYTES (100 MB)
    enforced by storage quota guard (AD-55 (b) verbatim).
    """

    http_status: int = 413


# ── Model Training Pipeline (4 NEW) ─────
class ModelTrainingJobNotFoundError(FinopsCostAnomalyMLPredictionError):
    """HTTP 404 typed error — model training job not found.

    Raised by anomaly_ml_training_pipeline.get_training_job_status() /
    cancel_training_job() when training_job_id lookup returns no rows
    (AD-55 (c) verbatim).
    """

    http_status: int = 404


class ModelTrainingFailedError(FinopsCostAnomalyMLPredictionError):
    """HTTP 500 typed error — model training job failed.

    Raised by anomaly_ml_training_pipeline.train_model() when the
    training loop exits with non-zero status (5 model types: prophet /
    lstm / arima / isolation_forest / autoencoder ensemble), SHAP feature
    importance extraction fails, or per-model_type default hyperparameters
    validation fails (AD-55 (c) verbatim).
    """

    http_status: int = 500


class ModelTrainingDataInsufficientError(FinopsCostAnomalyMLPredictionError):
    """HTTP 422 typed error — insufficient training data.

    Raised by anomaly_ml_training_pipeline.train_model() when the
    Phase 11 + Phase 12 + Phase 13 + Phase 14 + Phase 22 + Phase 23 +
    Phase 24 ledger dataset has fewer than MODEL_TRAINING_MIN_SAMPLES
    entries (300 days × 8 features = 2400 sample-points minimum,
    AD-55 (c) verbatim).
    """

    http_status: int = 422


class ModelTrainingTimeoutError(FinopsCostAnomalyMLPredictionError):
    """HTTP 504 typed error — model training job timeout.

    Raised by anomaly_ml_training_pipeline.train_model() when the
    training loop exceeds MODEL_TRAINING_TIMEOUT_SECONDS (3600s = 1h)
    with exponential backoff retry (max 3 attempts, base 60s, max 600s,
    AD-55 (c) verbatim).
    """

    http_status: int = 504


# ── Anomaly ML Scoring (5 NEW) ─────
class AnomalyMLScoringError(FinopsCostAnomalyMLPredictionError):
    """HTTP 500 typed error — anomaly_ml_scoring failure.

    Raised by anomaly_ml_scoring.predict_anomaly_score() /
    batch_predict_anomaly_scores() when the model inference call
    raises an unexpected runtime error after the 3-attempt retry
    loop is exhausted (real-time < 200ms P95 target, AD-55 (d) verbatim).
    """

    http_status: int = 500


class AnomalyMLInferenceTimeoutError(FinopsCostAnomalyMLPredictionError):
    """HTTP 504 typed error — anomaly_ml_scoring inference timeout.

    Raised by anomaly_ml_scoring.predict_anomaly_score() when the
    real-time inference latency exceeds ANOMALY_ML_INFERENCE_TIMEOUT_MS
    (200ms P95, AD-55 (d) verbatim) or batch inference exceeds
    ANOMALY_ML_BATCH_INFERENCE_TIMEOUT_MS (30000ms = 30s).
    """

    http_status: int = 504


class AnomalyMLFeatureExtractionError(FinopsCostAnomalyMLPredictionError):
    """HTTP 422 typed error — anomaly_ml_feature_extraction failure.

    Raised by anomaly_ml_scoring._extract_features() when one or more
    of the 8 features extracted from the multi-phase ledger has a
    NaN / null / out-of-range value (Phase 11 cost_total_krw +
    Phase 23 cost_per_unit + Phase 24 variance_pct +
    Phase 24 budget_consumption_pct + Phase 22 settlement_3way_match_score +
    Phase 14 optimization_savings_amount + Phase 13 month_seasonality +
    holiday_flag, AD-55 (c) verbatim).
    """

    http_status: int = 422


class AnomalyMLComparisonError(FinopsCostAnomalyMLPredictionError):
    """HTTP 500 typed error — anomaly_ml_scoring comparison failure.

    Raised by anomaly_ml_scoring.score_threshold_anomaly() when the
    AnomalyScoreComparison TypedDict construction fails (12 fields
    comparing ML-driven pre-detection vs Phase 12 rule-based
    사후 detection, bootstrap sampling B=1000, AD-55 (d) verbatim).
    """

    http_status: int = 500


class AnomalyMLEnsembleConsensusError(FinopsCostAnomalyMLPredictionError):
    """HTTP 500 typed error — anomaly_ml_ensemble_consensus failure.

    Raised by anomaly_ml_ensemble_consensus.ensemble_consensus_score()
    when the 5 model types weighted ensemble (DEFAULT_ENSEMBLE_WEIGHTS =
    prophet 0.30 + lstm 0.30 + arima 0.15 + isolation_forest 0.15 +
    autoencoder 0.10, sum=1.0) fails or consensus_detected() returns
    a confidence value outside [0.0, 1.0] range (Decimal banker's
    rounding CR 5-1, AD-55 (a) verbatim).
    """

    http_status: int = 500
