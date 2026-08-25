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
]
