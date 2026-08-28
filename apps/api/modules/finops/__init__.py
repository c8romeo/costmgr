"""apps.api.modules.finops — FinOps Optimization & Rightsizing territory.

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.1~§F27.7 + AD-38 (a)~(g) sub-decisions).

Phase 12 (cj-style 111번째 wire) — Cost Anomaly Detection & Budget
Alerting territory (PRD §F28.1~§F28.8 + AD-39 (a)~(g) sub-decisions).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.1~§F29.8 + AD-39 (a)~(g) sub-decisions).

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.1~§F30.8 + AD-41 (a)~(g) 7 sub-decisions).

This package provides:
- `showback_dsl` — ShowbackDefinition TypedDict (13 fields) + 5 group_by
  options + 6 period selector modes + comparison view + currency
  formatting + tenant-scoped override + audit-first INSERT
  `showback_generated`.
- `showback_query` — DepartmentBreakdown TypedDict (8 fields) +
  ComparisonView TypedDict (7 fields) + query_showback_breakdown +
  query_showback_comparison + pagination.
- `chargeback_engine` — ChargebackRule TypedDict (6 fields) +
  compute_chargeback + 3 rule types (flat_fee / proportional_allocation
  / metered) + markup + tax + multi-region aggregation.
- `chargeback_rule_evaluator` — evaluate_chargeback_rule +
  ChargebackRuleInvalidError + ChargebackCalculationError.
- `department_mapping` — department_id ↔ cost_center_id 1:1 mapping +
  validate_department_mapping + auto-create on first calculation +
  audit-first INSERT `department_mapping_updated`.
- `chargeback_export` — export_chargeback_csv StreamingResponse +
  export_chargeback_pdf + rate limit + audit-first INSERT
  `chargeback_exported`.
- `anomaly_detection` — AnomalyDefinition TypedDict (8 fields) + 4
  detection methods (z_score / IQR / EWMA / isolation_forest) + 5
  dimensions + 3 baseline windows + audit-first INSERT
  `anomaly_detected`.
- `anomaly_detection_engine` — run_anomaly_detection + 4-method voting
  consensus (3 of 4 agree → anomaly confirmed) + severity assignment
  (low / medium / high / critical) + audit-first INSERT.
- `budget_definition` — BudgetDefinition TypedDict (12 fields) +
  budget_period (monthly/quarterly/yearly) + budget_scope
  (tenant/department/cost_center/product_line) + alert_thresholds
  TypedDict + audit-first INSERT `budget_definition_updated`.
- `budget_alert` — route_budget_alert + 3-level alert routing
  (warning → Slack / critical → Slack + PagerDuty / exceeded →
  Slack + PagerDuty + Email) + 24h dedup window + audit-first INSERT
  `budget_threshold_exceeded` + `budget_alert_sent`.
- `forecast_accuracy` — evaluate_forecast_accuracy + MAE / MAPE / RMSE
  metrics + retraining trigger when MAPE > 20% + audit-first INSERT
  `forecast_deviation` + `model_retraining_triggered`.
- `forecast_definition` — ForecastDefinition TypedDict (11 fields) + 5
  target_metric options + 4 horizon_months options + 4 forecast model
  types (ARIMA + Prophet + LSTM + ensemble) + 4 confidence_level
  options (80/90/95/99) + 3 status options + audit-first INSERT
  `forecast_definition_updated`.
- `forecast_engine` — generate_forecast + 4-method parallel run +
  ensemble voting consensus (3 of 4 agree → ensemble pick) + STL
  decomposition + 8 KST holidays seasonality + audit-first INSERT
  `forecast_generated`.
- `forecast_model_registry` — semver MAJOR.MINOR.PATCH + JSONB metadata
  registry for all 4 forecast models + is_active production flag.
- `capacity_headroom` — analyze_capacity_headroom + 3 resource types
  (compute + storage + network) + 3 saturation levels (ok + warning +
  critical) + 90일 lookahead + per-resource primary model
  (compute=LSTM + storage=Prophet + network=ARIMA) + audit-first
  INSERT `capacity_headroom_analyzed`.
- `budget_burnrate` — project_budget_consumption + 4-input burn-rate
  formula + 3-level severity routing (warning=Slack / critical=Slack+
  PagerDuty / exceeded=Slack+PagerDuty+Email) + 24h dedup window +
  ARIMA end-of-period prediction + audit-first INSERT
  `budget_burn_rate_projected`.
- `forecast_accuracy_tracker` — track_forecast_accuracy + 3-tuple
  granularity (tenant_id + target_metric + model_type) + MAE / MAPE /
  RMSE banker's rounding CR 5-1 + INDUSTRY_BASELINE_MAPE_4_INDUSTRIES
  + MAPE > 20% for 3 consecutive periods → retraining trigger
  (`model_retraining_triggered`).
- `serializers` — m19_finops.finops_serializers module version SSOT
  + m21_finops_forecast.finops_forecast_serializers (Phase 13 wire
  BACKFILL) + m22_finops_optimization.optimization_serializers
  (Phase 14 wire EXTENSION).
- `optimization_definition` — OptimizationDefinition TypedDict (11
  fields) + 5 resource_types (compute + storage + database + network +
  container) + 7 optimization_strategies (rightsize_down +
  rightsize_up + idle_terminate + commit_1y + commit_3y +
  storage_tier_down + composite) + 4 target_metrics +
  5 baseline_periods + 3 statuses + audit-first INSERT
  `optimization_definition_updated` + OPTIMIZATION_DEFAULTS constants
  (idle_cpu_threshold_pct=5.0 + commit_break_even_1y=8mo +
  commit_break_even_3y=18mo).
- `rightsizing_engine` — RightsizingRecommendation TypedDict (14
  fields) + StorageRecommendation TypedDict + 5 _recommend_*_rightsizing
  functions (compute + storage + database + network + container) +
  INSTANCE_TYPE_DOWNGRADE_MAP (80+ AWS EC2 types across 4 families) +
  INSTANCE_TYPE_UPGRADE_MAP + STORAGE_TIER_DOWNGRADE_MAP +
  RIGHTSIZING_ENGINE_MODEL_VERSION = "1.0.0".
- `idle_resource_detector` — IdleResource TypedDict (13 fields) + 3
  severities (low + medium + high) + 3 actions (review + downsize +
  terminate) + 3 detection methods (z_score + threshold + heuristic) +
  IDLE_Z_SCORE_THRESHOLD = -2.0 + IDLE_CPU_THRESHOLD_PCT = 5.0 +
  5 _detect_idle_* functions.
- `commitment_recommender` — CommitmentRecommendation TypedDict
  (12 fields) + 6 commitment_types (ec2_ri + rds_ri + ec2_sp + s3_sp +
  redshift_sp + dynamodb_sp) + 2 commitment_terms (1_year + 3_year) +
  RI_SP_DISCOUNT_1Y=0.40 + RI_SP_DISCOUNT_3Y=0.60 +
  compute_break_even_months + compute_roi_pct functions.
- `optimization_accuracy_tracker` — OptimizationAccuracyReport TypedDict
  (10 fields) + compute_precision + compute_recall +
  compute_accuracy_score + check_accuracy_degradation +
  ACCURACY_SCORE_RETRAINING_THRESHOLD_PCT = 70.0 +
  RETRAINING_CRON_DEFAULT = "0 3 * * 0".

CR lessons applied:
- CR 0-2 RLS — every ShowbackDefinition + ChargebackRule +
  AnomalyDefinition + BudgetDefinition carries tenant_id selector +
  every FinOps event goes through cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to 11 NEW actions across Phase 11 + Phase 12:
    Phase 11: showback_generated + department_mapping_updated +
              chargeback_calculated + chargeback_exported
    Phase 12: anomaly_detected + forecast_deviation +
              model_retraining_triggered + budget_definition_updated +
              budget_threshold_exceeded + budget_alert_sent +
              (Phase 12 alert_sent unified into budget_alert_sent)
- CR 4-3/4-4 — showback baseline + chargeback baseline 30d rolling +
  golden_diff pattern verbatim 미러 (Phase 8 baseline freeze
  pattern carry-over) + Phase 12 anomaly baseline window update
  (last_30d + last_90d + YTD).
- CR 1-1 ContextVar — trace_id request-scoped ContextVar binding.
- CR 1-1 RSC boundary — finops dashboard client/server separation +
  anomaly dashboard RSC boundary + budget dashboard RSC boundary.
- CR 9-6 commit message — `git commit -F <file>` usage.
- CR 11-3 honest-DEFER — 107번째 + 111번째 epic 연속 정직 회복.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern
  applied to AnomalyDefinition + BudgetDefinition (parse_*_definition).
- CR 12-1 L4 industry-agnostic — FINOPS_SHOWBACK + FINOPS_CHARGEBACK +
  FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 4-industry grants
  ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 14 NEW typed exception
  classes in Phase 12 (AnomalyDefinitionInvalidError +
  AnomalyDetectionError + AnomalyBaselineUnavailableError +
  AnomalyBaselineUpdateError + BudgetDefinitionInvalidError +
  BudgetScopeInvalidError + BudgetAmountInvalidError +
  BudgetAlertError + BudgetAlertRoutingError +
  BudgetAlertDedupWindowActiveError + ForecastAccuracyDegradedError +
  ForecastAccuracyInvalidError + ForecastModelRetrainingError +
  FinopsAnomalyCapabilityDeniedError).
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity shared via CR 12-5 D-PARITY-01 verification tests.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only
  RBAC.

AD-14 stack pin — pandas + reportlab + jinja2 + openpyxl + pdfkit +
weasyprint + python-magic (Phase 10 stack pin EXTENSION) +
sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0
(Phase 12 stack pin EXTENSION).

AD-22 owner-only RBAC — showback generation + chargeback issue +
department mapping update + cost pool recalculation + CSV/PDF
export + anomaly detection + budget definition + budget alert +
forecast accuracy tracking all owner-only + Epic 12 2FA 챌린지
mandatory.

AD-39 Cost Anomaly Detection & Budget Alerting 신규 (Phase 12).

AD-41 FinOps Optimization & Rightsizing 신규 (Phase 14) — 7
sub-decisions (a)~(g):
(a) OptimizationDefinition schema + audit-first INSERT
    `optimization_definition_updated`.
(b) RightsizingRecommendation engine — 5 resource types +
    80+ AWS EC2 instance type mapping.
(c) IdleResource detection — z-score < -2.0 (Phase 12 EXTENSION).
(d) CommitmentRecommendation — 6 commitment_types + 1y/3y break-even.
(e) OptimizationAccuracyReport — precision/recall/realized_savings
    + retraining trigger when accuracy_score < 70%.
(f) Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
(g) L4 industry-agnostic capability FINOPS_OPTIMIZATION with
    4-industry grants ✅/✅/✅/✅ (CR 12-1 verbatim pattern).

NFR4 PII minimization PRESERVED — showback/chargeback/anomaly/budget
data contains only business metrics + cost amounts (no PII).

A19 cohesion pattern 9 surface EXTENSION PASS — FinOps anomaly +
budget alert surface NEW = F28.1~F28.8 territory.
"""
from __future__ import annotations

from apps.api.modules.finops.anomaly_detection import (
    ALL_BASELINE_WINDOWS,
    ALL_DETECTION_METHODS,
    ALL_DIMENSIONS,
    ANOMALY_THRESHOLD_DEFAULTS,
    AnomalyDefinition,
    detect_anomaly,
    parse_anomaly_definition,
)
from apps.api.modules.finops.budget_alert import (
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_EXCEEDED,
    ALERT_LEVEL_WARNING,
    ALL_ALERT_LEVELS,
)
from apps.api.modules.finops.budget_burnrate import (
    ALL_SEVERITY_LEVELS,
    BudgetOverrunPrediction,
    BurnRateProjection,
    project_budget_consumption,
)
from apps.api.modules.finops.budget_definition import (
    ALL_BUDGET_PERIODS,
    ALL_BUDGET_SCOPES,
    BUDGET_THRESHOLD_DEFAULTS,
    BudgetDefinition,
    define_budget,
    parse_budget_definition,
)
from apps.api.modules.finops.capacity_headroom import (
    ALL_RESOURCE_TYPES,
    ALL_SATURATION_LEVELS,
    CapacityHeadroomReport,
    analyze_capacity_headroom,
)
from apps.api.modules.finops.commitment_recommender import (
    RI_SP_DISCOUNT_1Y,
    RI_SP_DISCOUNT_3Y,
    CommitmentRecommendation,
    compute_break_even_months,
    compute_roi_pct,
    recommend_commitments,
)
from apps.api.modules.finops.cross_module_kpi import (
    select_cross_module_kpis,
    validate_kpi_accuracy,
)

# Phase 16 wire — FinOps Reporting & Executive Dashboard territory
from apps.api.modules.finops.executive_dashboard_aggregator import (
    aggregate_executive_dashboard,
    compute_anomaly_count_30d,
    compute_forecast_projection,
    compute_idle_cost_krw,
    compute_optimization_savings,
    compute_showback_total,
    compute_tag_compliance_pct,
    validate_executive_rollup,
)
from apps.api.modules.finops.executive_report_generator import (
    generate_executive_report,
)
from apps.api.modules.finops.forecast_accuracy import (
    ForecastAccuracyMetrics,
    compute_mae,
    compute_mape,
    compute_rmse,
    evaluate_forecast_accuracy,
)
from apps.api.modules.finops.forecast_accuracy_tracker import (
    INDUSTRY_BASELINE_MAPE_4_INDUSTRIES,
    ForecastAccuracy,
    ModelRetrainingTrigger,
    track_forecast_accuracy,
)
from apps.api.modules.finops.forecast_definition import (
    ALL_CONFIDENCE_LEVELS,
    ALL_FORECAST_STATUSES,
    ALL_HORIZON_MONTHS,
    ALL_MODEL_TYPES,
    ALL_TARGET_METRICS,
    FORECAST_DEFAULTS,
    ForecastDefinition,
    define_forecast,
    parse_forecast_definition,
)
from apps.api.modules.finops.forecast_engine import (
    ALL_SEASONALITY_MODES,
    ENSEMBLE_VOTING_CONSENSUS_THRESHOLD,
    ForecastResult,
    generate_forecast,
)
from apps.api.modules.finops.forecast_model_registry import (
    SEMVER_DEFAULT_VERSION,
    ForecastModelRegistry,
    ForecastModelVersion,
)
from apps.api.modules.finops.idle_resource_detector import (
    IDLE_CPU_THRESHOLD_PCT,
    IDLE_Z_SCORE_THRESHOLD,
    IdleResource,
    detect_idle_resources,
)

# Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
# Reconciliation territory. 9-module cross-rollup (Phase 11~19
# carry-over chain) + 5 cloud provider cross-rollup (AWS EDP +
# Azure EA + GCP CUD Pricing + Naver Cloud Volume Tier + KT Cloud
# Volume Tier) + 5 marketplace source support + 3 negotiation bot
# cloud providers + 4 cron schedules KST.
from apps.api.modules.finops.multi_cloud import (
    ALL_BLENDED_UNBLENDED_TRACKING_STATUSES,
    ALL_MARKETPLACE_INTEGRATION_STATUSES,
    ALL_MARKETPLACE_PRICING_MODELS,
    ALL_MARKETPLACE_SAAS_CATEGORIES,
    ALL_MARKETPLACE_SOURCES,
    ALL_MARKETPLACE_UNITS,
    ALL_MULTI_CLOUD_COST_SOURCES,
    ALL_MULTI_CLOUD_PROVIDERS,
    ALL_MULTI_CLOUD_RATE_CARD_SOURCES,
    ALL_MULTI_CLOUD_SCOPE_TYPES,
    ALL_NEGOTIATION_COMMITMENT_TERMS,
    ALL_NEGOTIATION_RISK_LEVELS,
    ALL_NEGOTIATION_STATUSES,
    ALL_NEGOTIATION_STRATEGIES,
    MULTI_CLOUD_DEFAULTS,
    MULTI_CLOUD_ENGINE_MODEL_VERSION,
    BlendedUnblendedDiff,
    BlendedUnblendedTrackingStatus,
    MarketplaceIntegrationStatus,
    MarketplacePricingModel,
    MarketplaceSaaSCategory,
    MarketplaceSaaSPricingRollup,
    MarketplaceSource,
    MarketplaceUnit,
    MultiCloudCostReconciliation,
    MultiCloudCostSource,
    MultiCloudProvider,
    MultiCloudRateCardReconciliation,
    MultiCloudRateCardSource,
    MultiCloudScopeType,
    NegotiationCommitmentTerm,
    NegotiationRecommendation,
    NegotiationRiskLevel,
    NegotiationStatus,
    NegotiationStrategy,
    integrate_marketplace_saas_pricing,
    monitor_naver_kt_api_health,
    reconcile_multi_cloud_costs,
    reconcile_multi_cloud_rate_cards,
    run_negotiation_bot,
    track_blended_unblended_diff,
    validate_blended_unblended_diff,
    validate_marketplace_saas_pricing_rollup,
    validate_multi_cloud_cost_reconciliation,
    validate_multi_cloud_rate_card_reconciliation,
    validate_naver_kt_api_data_accuracy,
    validate_negotiation_recommendation,
)
from apps.api.modules.finops.optimization_accuracy_tracker import (
    ACCURACY_SCORE_RETRAINING_THRESHOLD_PCT,
    RETRAINING_CRON_DEFAULT,
    OptimizationAccuracyReport,
    check_accuracy_degradation,
    compute_accuracy_score,
    compute_precision,
    compute_recall,
)
from apps.api.modules.finops.optimization_definition import (
    ALL_BASELINE_PERIODS,
    ALL_OPTIMIZATION_STATUSES,
    ALL_OPTIMIZATION_STRATEGIES,
    OPTIMIZATION_DEFAULTS,
    OptimizationDefinition,
    define_optimization,
    parse_optimization_definition,
)
from apps.api.modules.finops.optimization_definition import (
    ALL_RESOURCE_TYPES as ALL_OPTIMIZATION_RESOURCE_TYPES,
)
from apps.api.modules.finops.optimization_definition import (
    ALL_TARGET_METRICS as ALL_OPTIMIZATION_TARGET_METRICS,
)

# Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
# territory. 5-module composition layer (Phase 13 forecast + Phase 14
# optimization + Phase 18 commitment + Phase 19 pricing + Phase 20
# multi_cloud weighted average → single demand_forecast_id +
# capacity_plan_id + commitment_recommendation_id + orchestration_id).
# 6 reserved_capacity_tier (1y/3y × no/partial/all upfront) + 4
# execution_strategy + 4 cadence schedule (daily 02:00 + weekly Mon
# 03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz) +
# dry-run mode + Epic 12 2FA 챌린지 mandatory (high-value threshold
# 10M KRW/year).
from apps.api.modules.finops.reserved_capacity import (
    ALL_EXECUTION_STRATEGIES,
    ALL_ORCHESTRATION_SCOPES,
    ALL_RESERVED_CAPACITY_CADENCES,
    ALL_RESERVED_CAPACITY_TIERS,
    RESERVED_CAPACITY_DEFAULTS,
    RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
    ExecutionStrategy,
    OrchestrationScope,
    ReservedCapacityCadence,
    ReservedCapacityDemandForecast,
    ReservedCapacityOrchestration,
    ReservedCapacityPlan,
    ReservedCapacityTier,
    aggregate_demand_forecast,
    dispatch_reserved_capacity_orchestration,
    generate_commitment_recommendation,
    orchestrate_reserved_capacity,
    plan_reserved_capacity,
    validate_capacity_plan,
    validate_commitment_recommendation,
    validate_demand_forecast,
    validate_orchestration,
    validate_reserved_capacity_dispatch,
)
from apps.api.modules.finops.reserved_capacity import (
    CommitmentRecommendation as ReservedCapacityCommitmentRecommendation,
)
from apps.api.modules.finops.rightsizing_engine import (
    INSTANCE_TYPE_DOWNGRADE_MAP,
    INSTANCE_TYPE_UPGRADE_MAP,
    RIGHTSIZING_ENGINE_MODEL_VERSION,
    RightsizingRecommendation,
    recommend_rightsizing,
)

__all__ = [
    # Phase 11 wire
    "showback_dsl",
    "showback_query",
    "chargeback_engine",
    "chargeback_rule_evaluator",
    "department_mapping",
    "chargeback_export",
    "serializers",
    # Phase 12 wire — anomaly detection
    "ANOMALY_THRESHOLD_DEFAULTS",
    "ALL_BASELINE_WINDOWS",
    "ALL_DETECTION_METHODS",
    "ALL_DIMENSIONS",
    "AnomalyDefinition",
    "detect_anomaly",
    "parse_anomaly_definition",
    # Phase 12 wire — budget definition
    "ALERT_LEVEL_CRITICAL",
    "ALERT_LEVEL_EXCEEDED",
    "ALERT_LEVEL_WARNING",
    "ALL_ALERT_LEVELS",
    "ALL_BUDGET_PERIODS",
    "ALL_BUDGET_SCOPES",
    "BUDGET_THRESHOLD_DEFAULTS",
    "BudgetDefinition",
    "define_budget",
    "parse_budget_definition",
    # Phase 12 wire — forecast accuracy
    "ForecastAccuracyMetrics",
    "compute_mae",
    "compute_mape",
    "compute_rmse",
    "evaluate_forecast_accuracy",
    # Phase 13 wire — forecast definition
    "ALL_CONFIDENCE_LEVELS",
    "ALL_FORECAST_STATUSES",
    "ALL_HORIZON_MONTHS",
    "ALL_MODEL_TYPES",
    "ALL_TARGET_METRICS",
    "FORECAST_DEFAULTS",
    "ForecastDefinition",
    "define_forecast",
    "parse_forecast_definition",
    # Phase 13 wire — forecast engine
    "ALL_SEASONALITY_MODES",
    "ENSEMBLE_VOTING_CONSENSUS_THRESHOLD",
    "ForecastResult",
    "generate_forecast",
    # Phase 13 wire — forecast model registry
    "SEMVER_DEFAULT_VERSION",
    "ForecastModelRegistry",
    "ForecastModelVersion",
    # Phase 13 wire — capacity headroom
    "ALL_RESOURCE_TYPES",
    "ALL_SATURATION_LEVELS",
    "CapacityHeadroomReport",
    "analyze_capacity_headroom",
    # Phase 13 wire — budget burn-rate
    "ALL_SEVERITY_LEVELS",
    "BudgetOverrunPrediction",
    "BurnRateProjection",
    "project_budget_consumption",
    # Phase 13 wire — forecast accuracy tracker
    "ForecastAccuracy",
    "INDUSTRY_BASELINE_MAPE_4_INDUSTRIES",
    "ModelRetrainingTrigger",
    "track_forecast_accuracy",
    # Phase 14 wire — optimization definition
    "ALL_BASELINE_PERIODS",
    "ALL_OPTIMIZATION_STATUSES",
    "ALL_OPTIMIZATION_STRATEGIES",
    "ALL_OPTIMIZATION_RESOURCE_TYPES",
    "ALL_OPTIMIZATION_TARGET_METRICS",
    "OPTIMIZATION_DEFAULTS",
    "OptimizationDefinition",
    "define_optimization",
    "parse_optimization_definition",
    # Phase 14 wire — rightsizing engine
    "INSTANCE_TYPE_DOWNGRADE_MAP",
    "INSTANCE_TYPE_UPGRADE_MAP",
    "RIGHTSIZING_ENGINE_MODEL_VERSION",
    "RightsizingRecommendation",
    "recommend_rightsizing",
    # Phase 14 wire — idle resource detector
    "IDLE_CPU_THRESHOLD_PCT",
    "IDLE_Z_SCORE_THRESHOLD",
    "IdleResource",
    "detect_idle_resources",
    # Phase 14 wire — commitment recommender
    "CommitmentRecommendation",
    "RI_SP_DISCOUNT_1Y",
    "RI_SP_DISCOUNT_3Y",
    "compute_break_even_months",
    "compute_roi_pct",
    "recommend_commitments",
    # Phase 14 wire — optimization accuracy tracker
    "ACCURACY_SCORE_RETRAINING_THRESHOLD_PCT",
    "OptimizationAccuracyReport",
    "RETRAINING_CRON_DEFAULT",
    "check_accuracy_degradation",
    "compute_accuracy_score",
    "compute_precision",
    "compute_recall",
    # Phase 16 wire — FinOps Reporting & Executive Dashboard
    "aggregate_executive_dashboard",
    "compute_showback_total",
    "compute_anomaly_count_30d",
    "compute_forecast_projection",
    "compute_optimization_savings",
    "compute_tag_compliance_pct",
    "compute_idle_cost_krw",
    "validate_executive_rollup",
    "select_cross_module_kpis",
    "validate_kpi_accuracy",
    "generate_executive_report",
    # Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
    # Reconciliation territory. 9-module cross-rollup (Phase 11~19
    # carry-over chain) + 5 cloud provider cross-rollup (AWS EDP +
    # Azure EA + GCP CUD Pricing + Naver Cloud Volume Tier + KT Cloud
    # Volume Tier) + 5 marketplace source support + 3 negotiation bot
    # cloud providers + 4 cron schedules KST.
    "reconcile_multi_cloud_rate_cards",
    "reconcile_multi_cloud_costs",
    "run_negotiation_bot",
    "track_blended_unblended_diff",
    "integrate_marketplace_saas_pricing",
    "MULTI_CLOUD_ENGINE_MODEL_VERSION",
    "MULTI_CLOUD_DEFAULTS",
    "validate_multi_cloud_rate_card_reconciliation",
    "validate_multi_cloud_cost_reconciliation",
    "validate_negotiation_recommendation",
    "validate_blended_unblended_diff",
    "validate_marketplace_saas_pricing_rollup",
    "monitor_naver_kt_api_health",
    "validate_naver_kt_api_data_accuracy",
    # Phase 20 wire — multi_cloud subpackage exports
    "MultiCloudRateCardReconciliation",
    "MultiCloudCostReconciliation",
    "NegotiationRecommendation",
    "BlendedUnblendedDiff",
    "MarketplaceSaaSPricingRollup",
    "MultiCloudScopeType",
    "MultiCloudProvider",
    "MultiCloudRateCardSource",
    "MultiCloudCostSource",
    "NegotiationStatus",
    "NegotiationRiskLevel",
    "NegotiationCommitmentTerm",
    "NegotiationStrategy",
    "BlendedUnblendedTrackingStatus",
    "MarketplaceSource",
    "MarketplaceSaaSCategory",
    "MarketplaceUnit",
    "MarketplacePricingModel",
    "MarketplaceIntegrationStatus",
    # Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
    # territory. 5-module composition layer + 6 reserved_capacity_tier +
    # 4 execution_strategy + 4 cadence schedule KST pytz + dry-run
    # mode + Epic 12 2FA 챌린지 mandatory (high-value threshold 10M
    # KRW/year).
    "RESERVED_CAPACITY_ENGINE_MODEL_VERSION",
    "RESERVED_CAPACITY_DEFAULTS",
    "ReservedCapacityDemandForecast",
    "ReservedCapacityPlan",
    "ReservedCapacityCommitmentRecommendation",
    "ReservedCapacityOrchestration",
    "ReservedCapacityTier",
    "ALL_RESERVED_CAPACITY_TIERS",
    "ExecutionStrategy",
    "ALL_EXECUTION_STRATEGIES",
    "ReservedCapacityCadence",
    "ALL_RESERVED_CAPACITY_CADENCES",
    "OrchestrationScope",
    "ALL_ORCHESTRATION_SCOPES",
    "aggregate_demand_forecast",
    "validate_demand_forecast",
    "plan_reserved_capacity",
    "validate_capacity_plan",
    "generate_commitment_recommendation",
    "validate_commitment_recommendation",
    "orchestrate_reserved_capacity",
    "validate_orchestration",
    "dispatch_reserved_capacity_orchestration",
    "validate_reserved_capacity_dispatch",
    # Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement
    # territory. 5-module cross-join + 5-dim allocation + PDF/XLSX/CSV
    # invoice + 3-way match reconciliation + 4 cadence KST + dry-run +
    # Epic 12 2FA 챌린지 mandatory.
    "CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION",
    "CHARGEBACK_SETTLEMENT_DEFAULTS",
    "ALLOCATION_DIMENSION_WEIGHTS",
    "ALLOCATION_DIMENSION_WEIGHT_SUM",
    "FIVE_MODULE_WEIGHTS",
    "FIVE_MODULE_WEIGHT_SUM",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "MAX_ALLOCATION_LINES",
    "MAX_INVOICE_BYTES",
    "RECONCILIATION_TOLERANCE_PCT",
    "RECONCILIATION_MAX_RETRIES",
    "RECONCILIATION_AMOUNT_TOLERANCE_KRW",
    "SETTLEMENT_CADENCE_HOURS_KST",
    "SETTLEMENT_RECIPIENT_TEMPLATES",
    "ALL_RECONCILIATION_STATUSES",
    "ALL_SETTLEMENT_CADENCES",
    "ALL_SETTLEMENT_RULE_TYPES",
    "ALL_SETTLEMENT_STATUSES",
    "ALL_ALLOCATION_DIMENSIONS",
    "ALL_INVOICE_FORMATS",
    "SettlementRule",
    "SettlementResult",
    "AllocationLine",
    "ReconciliationResult",
    "SettlementRuleType",
    "SettlementStatus",
    "AllocationDimension",
    "InvoiceFormat",
    "create_settlement_rule",
    "update_settlement_rule",
    "list_settlement_rules",
    "validate_settlement_rule",
    "compute_allocation",
    "validate_allocation_lines",
    "aggregate_allocation_breakdown",
    "generate_invoice",
    "validate_invoice_format",
    "reconcile_settlement",
    "validate_reconciliation_result",
    "compute_settlement_result",
    "schedule_cadence_dispatch",
    "execute_dispatch",
    "validate_cadence",
    "chargeback_settlement_router",
    # Phase 23 wire (cj-style 164번째) — FinOps Unit Economics
    # territory. Derived metric layer from Phase 22 settlement_id →
    # allocation_lines ledger via 5-dim cross-join + ledger-key dedup
    # + 5-dim rollup + OPTIONAL revenue attribution margin analysis
    # + 4 cadence KST pytz (daily 03:30 + weekly 04:00 + monthly 04:30
    # + quarterly 05:00) + dry-run mode + Epic 12 2FA 챌린지 mandatory
    # (high-value threshold 10M KRW/year) + D-FINOPS-12 honestly DEFER
    # (cost_per_customer CRM + multi-currency FX + real-time stream).
    "MODULE_TAG",  # m31_finops_unit_economics
    "UNIT_ECONOMICS_ENGINE_MODEL_VERSION",
    "UNIT_ECONOMICS_DEFAULTS",
    "DERIVATION_DIMENSION_WEIGHTS",
    "COST_PER_X_METRIC_WEIGHTS",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "MARGIN_HEALTHY_THRESHOLD_PCT",
    "MARGIN_WARNING_THRESHOLD_PCT",
    "MARGIN_CRITICAL_THRESHOLD_PCT",
    "MARGIN_NEGATIVE_PCT",
    "MAX_BUSINESS_UNITS_PER_TENANT",
    "MAX_TRANSACTIONS_PER_PERIOD",
    "MAX_COST_PER_X_OVERRIDE_KRW",
    "UNIT_ECONOMICS_CADENCE_HOURS_KST",
    "UNIT_ECONOMICS_RECIPIENT_TEMPLATES",
    "ALL_UNIT_ECONOMICS_CALCULATION_STATUSES",
    "ALL_UNIT_ECONOMICS_DIMENSIONS",
    "ALL_COST_PER_X_METRICS",
    "ALL_MARGIN_ANALYSIS_STATUSES",
    "ALL_UNIT_ECONOMICS_ALERT_SEVERITIES",
    "ALL_UNIT_ECONOMICS_CADENCES",
    "ALLOWED_TAG_KEYS",
    "UnitEconomicsCalculationStatus",
    "UnitEconomicsDimension",
    "CostPerXMetric",
    "MarginAnalysisStatus",
    "UnitEconomicsAlertSeverity",
    "UnitEconomicsResult",
    "CostPerBusinessUnitBreakdown",
    "CostPerTransactionBreakdown",
    "MarginAnalysisResult",
    "UnitEconomicsAlert",
    "compute_unit_economics",
    "list_unit_economics_results",
    "validate_unit_economics_result",
    "compute_cost_per_business_unit",
    "validate_cost_per_business_unit",
    "aggregate_cost_per_business_unit",
    "compute_cost_per_transaction",
    "validate_cost_per_transaction",
    "aggregate_cost_per_transaction",
    "execute_margin_analysis",
    "validate_margin_analysis",
    "aggregate_margin_analysis",
    "compute_unit_economics_period",
    "schedule_cadence_calculation",
    "execute_calculation",
    "validate_cadence",
    "unit_economics_router",
    # Phase 24 wire (cj-style 169번째) — FinOps Budget Planning
    "MODULE_TAG",  # m24_finops_budget_planning
    "BUDGET_PLANNING_ENGINE_MODEL_VERSION",
    "BUDGET_PLANNING_DEFAULTS",
    "BUDGET_PLANNING_DIMENSION_WEIGHTS",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "BUDGET_WARNING_THRESHOLD_PCT",
    "BUDGET_CRITICAL_THRESHOLD_PCT",
    "MAX_BUDGET_PLANS_PER_TENANT",
    "MAX_ALLOCATIONS_PER_PLAN",
    "MAX_BUDGET_OVERRIDE_KRW",
    "TOTAL_VERIFICATION_TOLERANCE_KRW",
    "BUDGET_PLANNING_CADENCE_HOURS_KST",
    "BUDGET_PLANNING_RECIPIENT_TEMPLATES",
    "BUDGET_ALERT_RECIPIENT_TEMPLATES",
    "ALL_BUDGET_PLAN_PERIOD_TYPES",
    "ALL_BUDGET_PLAN_PERIOD_TYPE_VALUES",
    "ALL_BUDGET_PLAN_LIFECYCLES",
    "ALL_BUDGET_PLAN_LIFECYCLE_VALUES",
    "ALL_BUDGET_PLAN_DRY_RUN_MODES",
    "ALL_BUDGET_PLAN_DRY_RUN_MODE_VALUES",
    "ALL_BUDGET_APPROVAL_STEP_STATUSES",
    "ALL_BUDGET_APPROVAL_STEP_STATUS_VALUES",
    "ALL_BUDGET_ALERT_SEVERITIES",
    "ALL_BUDGET_ALERT_SEVERITY_VALUES",
    "ALL_BUDGET_PLAN_DIMENSIONS",
    "ALL_BUDGET_PLAN_DIMENSION_VALUES",
    "LISTEN_NOTIFY_CHANNELS",
    "BudgetPlanPeriodType",
    "BudgetPlanLifecycle",
    "BudgetPlanDryRunMode",
    "BudgetApprovalStepStatus",
    "BudgetAlertSeverity",
    "BudgetPlanDimension",
    "BudgetPlan",
    "BudgetAllocationLine",
    "BudgetApprovalStep",
    "BudgetVsActual",
    "BudgetAlert",
    "create_budget_plan",
    "list_budget_plans",
    "update_budget_plan",
    "validate_budget_plan",
    "aggregate_budget_plans",
    "allocate_budget",
    "validate_budget_allocation",
    "aggregate_budget_allocations",
    "submit_for_approval",
    "record_approval_decision",
    "reject_plan",
    "validate_approval_chain",
    "aggregate_approval_steps",
    "compute_budget_vs_actual",
    "validate_budget_vs_actual",
    "aggregate_budget_vs_actual",
    "trigger_over_budget_alert",
    "escalate_alert",
    "acknowledge_alert",
    "validate_budget_alert",
    "aggregate_budget_alerts",
    "compute_budget_planning_period",
    "execute_lifecycle",
    "schedule_cadence_lifecycle",
    "validate_cadence",
    "consume_notify",
    "budget_planning_router",
    # Phase 25 wire (cj-style 174th follow-up) — FinOps Vendor Management
    # post-budget-allocation close-loop layer (AD-53 (a)~(g) 7
    # sub-decisions verbatim). 5-NEW-module composition layer
    # (vendor_catalog_engine + vendor_selection_engine +
    # vendor_contract_lifecycle_engine + vendor_performance_evaluation +
    # vendor_spend_attribution) + 9 NEW endpoints + 12 NEW audit actions +
    # 16 NEW typed exceptions + dry-run mode + 1 NEW CLI flag +
    # D-FINOPS-14 honestly DEFER (vendor marketplace + auto-procurement +
    # vendor consolidation + vendor ESG + AI-driven RFP + SLA
    # auto-inforcement + multi-currency FX + invoice OCR + KYC + risk
    # scoring ML — all honestly DEFER to future Phase 25.x).
    "MODULE_TAG",  # m25_finops_vendor_management
    "VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION",
    "VENDOR_SELECTION_DIMENSION_WEIGHTS",
    "VENDOR_PERFORMANCE_DIMENSION_WEIGHTS",
    "VENDOR_CADENCE_HOURS_KST",
    "VENDOR_RECIPIENT_TEMPLATES",
    "VENDOR_DEFAULTS",
    "VENDOR_BLACKLIST_GATE_FLAGS",
    "SELECTION_THRESHOLD_DEFAULT",
    "SELECTION_CANDIDATE_LIMIT_DEFAULT",
    "SELECTION_SCORE_VERSION_MAX",
    "VENDOR_RISK_LOW_THRESHOLD",
    "VENDOR_RISK_MEDIUM_THRESHOLD",
    "VENDOR_RISK_HIGH_THRESHOLD",
    "MAX_VENDORS_PER_TENANT",
    "MAX_CONTRACTS_PER_VENDOR",
    "MAX_CONTRACT_OVERRIDE_KRW",
    "TOTAL_VERIFICATION_TOLERANCE_KRW",
    "AUTO_RENEWAL_WINDOW_DAYS",
    "LISTEN_NOTIFY_CHANNELS",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "ALL_VENDOR_STATUSES",
    "ALL_VENDOR_CATEGORIES",
    "ALL_VENDOR_CONTRACT_LIFECYCLES",
    "ALL_VENDOR_PERFORMANCE_SEVERITIES",
    "ALL_VENDOR_SELECTION_MODES",
    "ALL_VENDOR_APPROVAL_STEP_STATUSES",
    "ALL_VENDOR_STATUS_VALUES",
    "ALL_VENDOR_CATEGORY_VALUES",
    "ALL_VENDOR_CONTRACT_LIFECYCLE_VALUES",
    "ALL_VENDOR_PERFORMANCE_SEVERITY_VALUES",
    "ALL_VENDOR_SELECTION_MODE_VALUES",
    "ALL_VENDOR_APPROVAL_STEP_STATUS_VALUES",
    "VendorStatus",
    "VendorCategory",
    "VendorContractLifecycle",
    "VendorPerformanceSeverity",
    "VendorSelectionMode",
    "VendorApprovalStepStatus",
    "Vendor",
    "VendorSelectionScore",
    "VendorContract",
    "VendorPerformanceScorecard",
    "VendorSpendAttribution",
    "VendorBlacklistEntry",
    "aggregate_vendor_catalog",
    "create_vendor",
    "update_vendor",
    "change_vendor_status",
    "blacklist_vendor",
    "compute_vendor_risk_score",
    "validate_vendor_scores",
    "aggregate_vendor_selection",
    "score_vendor",
    "apply_vendor_selection_threshold",
    "override_selection_score_per_tenant",
    "aggregate_vendor_contract_lifecycle",
    "create_vendor_contract",
    "advance_contract_lifecycle",
    "request_contract_approval",
    "approve_contract_step",
    "reject_contract_step",
    "request_contract_renewal",
    "terminate_contract",
    "check_auto_renewal_window",
    "check_over_budget",
    "check_vendor_blacklist_gate",
    "aggregate_vendor_performance",
    "evaluate_vendor_performance",
    "compute_monthly_score",
    "compute_quarterly_score",
    "classify_performance_severity",
    "aggregate_vendor_spend_attribution",
    "compute_vendor_spend_attribution",
    "reconcile_cross_budget",
    "daily_vendor_lifecycle_job",
    "monthly_vendor_performance_job",
    "monthly_vendor_spend_attribution_job",
    "quarterly_vendor_review_job",
    "schedule_vendor_management_jobs",
    "notify_listen_channels",
    "vendor_management_router",
]


# Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement
# territory. 5-module cross-join composition layer (Phase 11 chargeback
# + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud +
# Phase 21 reserved_capacity weighted average → single settlement_id +
# allocation_id + invoice_id + reconciliation_id). 5-dim allocation
# (cost_center + department + business_unit + tag + tenant) +
# PDF/XLSX/CSV invoice generation (reportlab 4.0.7 + xlsxwriter 3.1.9
# + noto-sans-cjk-kr) + 3-way match reconciliation (1.0% tolerance +
# 3 auto-retries) + 4 cadence schedule KST pytz (monthly 04:00 +
# quarterly 05:00 + semi_annual 06:00 + annual 07:00) + dry-run mode +
# Epic 12 2FA 챌린지 mandatory (high-value threshold 10M KRW/year) +
# 8 NEW audit actions + 16 NEW typed exceptions + 9 NEW endpoints +
# AD-50 (a)~(g) 7 sub-decisions.
from apps.api.modules.finops.chargeback_settlement import (
    ALL_ALLOCATION_DIMENSIONS,
    ALL_INVOICE_FORMATS,
    ALL_RECONCILIATION_STATUSES,
    ALL_SETTLEMENT_CADENCES,
    ALL_SETTLEMENT_RULE_TYPES,
    ALL_SETTLEMENT_STATUSES,
    ALLOCATION_DIMENSION_WEIGHT_SUM,
    ALLOCATION_DIMENSION_WEIGHTS,
    CHARGEBACK_SETTLEMENT_DEFAULTS,
    CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    FIVE_MODULE_WEIGHT_SUM,
    FIVE_MODULE_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_ALLOCATION_LINES,
    MAX_INVOICE_BYTES,
    RECONCILIATION_AMOUNT_TOLERANCE_KRW,
    RECONCILIATION_MAX_RETRIES,
    RECONCILIATION_TOLERANCE_PCT,
    SETTLEMENT_CADENCE_HOURS_KST,
    SETTLEMENT_RECIPIENT_TEMPLATES,
    AllocationDimension,
    AllocationLine,
    InvoiceFormat,
    ReconciliationResult,
    SettlementResult,
    SettlementRule,
    SettlementRuleType,
    SettlementStatus,
    aggregate_allocation_breakdown,
    chargeback_settlement_router,
    compute_allocation,
    compute_settlement_result,
    create_settlement_rule,
    execute_dispatch,
    generate_invoice,
    list_settlement_rules,
    reconcile_settlement,
    schedule_cadence_dispatch,
    update_settlement_rule,
    validate_allocation_lines,
    validate_cadence,
    validate_invoice_format,
    validate_reconciliation_result,
    validate_settlement_rule,
)

# Phase 23 wire (cj-style 164번째) — FinOps Unit Economics derived
# metric layer territory. 4-NEW-module composition layer:
# unit_economics_engine (5-dim cross-join from Phase 22
# settlement_id → allocation_lines ledger) + cost_per_business_unit
# (5-dim rollup + ledger-key dedup) + cost_per_transaction (tag
# propagation + ledger-key dedup) + margin_analysis (OPTIONAL
# revenue attribution + 3-tier status thresholds + alert generation).
# 4 cadence schedule KST pytz (daily 03:30 + weekly 04:00 + monthly
# 04:30 + quarterly 05:00) + dry-run mode + Epic 12 2FA 챌린지
# mandatory (high-value threshold 10M KRW/year) + 7 NEW audit
# actions + 15 NEW typed exceptions + 9 NEW endpoints +
# AD-51 (a)~(g) 7 sub-decisions + D-FINOPS-12 honestly DEFER
# (cost_per_customer CRM + multi-currency FX + real-time stream).
from apps.api.modules.finops.unit_economics import (
    ALLOWED_TAG_KEYS,
    ALL_COST_PER_X_METRICS,
    ALL_MARGIN_ANALYSIS_STATUSES,
    ALL_UNIT_ECONOMICS_ALERT_SEVERITIES,
    ALL_UNIT_ECONOMICS_CADENCES,
    ALL_UNIT_ECONOMICS_CALCULATION_STATUSES,
    ALL_UNIT_ECONOMICS_DIMENSIONS,
    COST_PER_X_METRIC_WEIGHTS,
    DERIVATION_DIMENSION_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MARGIN_CRITICAL_THRESHOLD_PCT,
    MARGIN_HEALTHY_THRESHOLD_PCT,
    MARGIN_NEGATIVE_PCT,
    MARGIN_WARNING_THRESHOLD_PCT,
    MAX_BUSINESS_UNITS_PER_TENANT,
    MAX_COST_PER_X_OVERRIDE_KRW,
    MAX_TRANSACTIONS_PER_PERIOD,
    MODULE_TAG,  # m31_finops_unit_economics
    UNIT_ECONOMICS_CADENCE_HOURS_KST,
    UNIT_ECONOMICS_DEFAULTS,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    UNIT_ECONOMICS_RECIPIENT_TEMPLATES,
    CostPerBusinessUnitBreakdown,
    CostPerTransactionBreakdown,
    CostPerXMetric,
    MarginAnalysisResult,
    MarginAnalysisStatus,
    UnitEconomicsAlert,
    UnitEconomicsAlertSeverity,
    UnitEconomicsCalculationStatus,
    UnitEconomicsDimension,
    UnitEconomicsResult,
    aggregate_cost_per_business_unit,
    aggregate_cost_per_transaction,
    aggregate_margin_analysis,
    compute_cost_per_business_unit,
    compute_cost_per_transaction,
    compute_unit_economics,
    compute_unit_economics_period,
    execute_calculation,
    execute_margin_analysis,
    list_unit_economics_results,
    schedule_cadence_calculation,
    unit_economics_router,
    validate_cadence,
    validate_cost_per_business_unit,
    validate_cost_per_transaction,
    validate_margin_analysis,
    validate_unit_economics_result,
)

# Phase 24 wire (cj-style 169번째) — FinOps Budget Planning
# pre-allocation layer territory. 5-NEW-module composition layer:
# budget_plan_engine (5-dim cross-join from Phase 22 allocation_lines
# + Phase 23 unit_economics_results ledger) + budget_allocation
# (5-dim weighted allocation with per-tenant override > industry
# baseline > system default precedence + ±0.01 KRW total verification
# + 3 auto-retries + admin email alert) + budget_approval_workflow
# (sequential approval chain + Epic 12 2FA 챌린지 mandatory
# high-value threshold 10M KRW/year + RFC 6238 TOTP) +
# budget_vs_actual (Phase 22 settlement_results JOIN Phase 24
# BudgetPlan on tenant_id + period_key + dimension) + budget_alert
# (over-budget detection warning 10% + critical 25% + auto-escalation
# chain on-call rotation). 4 cadence schedule KST pytz
# (daily_lifecycle 04:00 + weekly_variance 04:30 + monthly_rollover
# 05:00 + quarterly_review 05:30) + 4 LISTEN/NOTIFY channels +
# dry-run mode + 8 NEW audit actions + 16 NEW typed exceptions +
# 9 NEW endpoints + AD-52 (a)~(g) 7 sub-decisions +
# D-FINOPS-13 honestly DEFER (multi-currency FX + zero-based budgeting
# + incremental budgeting + envelope budgeting + scenario A/B testing
# + per-budget approval override).
from apps.api.modules.finops.budget_planning import (  # noqa: E402
    ALL_BUDGET_ALERT_SEVERITIES,
    ALL_BUDGET_ALERT_SEVERITY_VALUES,
    ALL_BUDGET_APPROVAL_STEP_STATUSES,
    ALL_BUDGET_APPROVAL_STEP_STATUS_VALUES,
    ALL_BUDGET_PLAN_DIMENSIONS,
    ALL_BUDGET_PLAN_DIMENSION_VALUES,
    ALL_BUDGET_PLAN_DRY_RUN_MODES,
    ALL_BUDGET_PLAN_DRY_RUN_MODE_VALUES,
    ALL_BUDGET_PLAN_LIFECYCLES,
    ALL_BUDGET_PLAN_LIFECYCLE_VALUES,
    ALL_BUDGET_PLAN_PERIOD_TYPES,
    ALL_BUDGET_PLAN_PERIOD_TYPE_VALUES,
    BUDGET_ALERT_RECIPIENT_TEMPLATES,
    BUDGET_CRITICAL_THRESHOLD_PCT,
    BUDGET_PLANNING_CADENCE_HOURS_KST,
    BUDGET_PLANNING_DEFAULTS,
    BUDGET_PLANNING_DIMENSION_WEIGHTS,
    BUDGET_PLANNING_ENGINE_MODEL_VERSION,
    BUDGET_PLANNING_RECIPIENT_TEMPLATES,
    BUDGET_WARNING_THRESHOLD_PCT,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    LISTEN_NOTIFY_CHANNELS,
    MAX_ALLOCATIONS_PER_PLAN,
    MAX_BUDGET_OVERRIDE_KRW,
    MAX_BUDGET_PLANS_PER_TENANT,
    MODULE_TAG,  # m24_finops_budget_planning
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    BudgetAlert,
    BudgetAlertSeverity,
    BudgetAllocationLine,
    BudgetApprovalStep,
    BudgetApprovalStepStatus,
    BudgetPlan,
    BudgetPlanDimension,
    BudgetPlanDryRunMode,
    BudgetPlanLifecycle,
    BudgetPlanPeriodType,
    BudgetVsActual,
    acknowledge_alert,
    aggregate_budget_alerts,
    aggregate_budget_allocations,
    aggregate_budget_plans,
    aggregate_budget_vs_actual,
    allocate_budget,
    budget_planning_router,
    compute_budget_planning_period,
    compute_budget_vs_actual,
    consume_notify,
    create_budget_plan,
    escalate_alert,
    execute_lifecycle,
    list_budget_plans,
    record_approval_decision,
    reject_plan,
    schedule_cadence_lifecycle,
    submit_for_approval,
    trigger_over_budget_alert,
    update_budget_plan,
    validate_approval_chain,
    validate_budget_alert,
    validate_budget_allocation,
    validate_budget_plan,
    validate_budget_vs_actual,
    validate_cadence,
)

# Phase 25 (cj-style 174th follow-up wire) — FinOps Vendor Management
# post-budget-allocation close-loop layer territory. 5-NEW-module
# composition layer: vendor_catalog_engine (5-dim scoring baseline +
# 6 vendor_category taxonomy: cloud / saas / outsourcing / consulting /
# hardware / other + 4-state lifecycle: active / inactive / under_review
# / blacklisted) + vendor_selection_engine (5-dim weighted scoring:
# cost 0.30 + performance 0.25 + reliability 0.20 + compliance 0.15 +
# strategic_fit 0.10 + per-tenant override > industry baseline >
# system default precedence + SELECTION_THRESHOLD_DEFAULT=60.00 +
# SELECTION_SCORE_VERSION_MAX=100.00 strict range) +
# vendor_contract_lifecycle_engine (sequential state machine: draft →
# pending_approval → approved → active → expiring_soon → renewed /
# expired / terminated + Epic 12 2FA 챌린지 mandatory high-value ≥ 10M
# KRW/year + tenant_owner approval chain Slack DM + 2FA +
# AUTO_RENEWAL_WINDOW_DAYS=90 + OVER_BUDGET cross-check + vendor_blacklist
# compliance gate AD-53 (g)) + vendor_performance_evaluation
# (4-dim scoring: sla_compliance 0.30 + cost_efficiency 0.25 +
# support_quality 0.25 + innovation 0.20 + monthly 1st-day 03:00 KST +
# quarterly 1st-day 03:30 KST cadence) + vendor_spend_attribution
# (cross-budget reconciliation: Phase 22 settlement_results JOIN
# Phase 24 BudgetPlan + 5-dim ledger-key dedup). 9 endpoints (vendor
# CRUD + selection + blacklist + contract + advance + dry-run) +
# 4 cadence KST pytz (daily_lifecycle 04:00 + monthly_performance 03:00
# + monthly_spend_attribution 03:30 + quarterly_review 03:30) +
# dry-run mode + 1 NEW CLI flag `--finops-vendor-management-dry-run` +
# 12 NEW audit actions + 16 NEW typed exceptions + AD-53 (a)~(g) 7
# sub-decisions + D-FINOPS-14 honestly DEFER (vendor marketplace +
# auto-procurement + vendor consolidation + vendor ESG + AI-driven RFP
# + SLA auto-inforcement + multi-currency FX + invoice OCR + KYC +
# risk scoring ML — all honestly DEFER to future Phase 25.x).
from apps.api.modules.finops.vendor_management import (  # noqa: E402
    ALL_VENDOR_APPROVAL_STEP_STATUS_VALUES,
    ALL_VENDOR_APPROVAL_STEP_STATUSES,
    ALL_VENDOR_CATEGORIES,
    ALL_VENDOR_CATEGORY_VALUES,
    ALL_VENDOR_CONTRACT_LIFECYCLE_VALUES,
    ALL_VENDOR_CONTRACT_LIFECYCLES,
    ALL_VENDOR_PERFORMANCE_SEVERITIES,
    ALL_VENDOR_PERFORMANCE_SEVERITY_VALUES,
    ALL_VENDOR_SELECTION_MODE_VALUES,
    ALL_VENDOR_SELECTION_MODES,
    ALL_VENDOR_STATUS_VALUES,
    ALL_VENDOR_STATUSES,
    AUTO_RENEWAL_WINDOW_DAYS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    LISTEN_NOTIFY_CHANNELS,
    MAX_CONTRACT_OVERRIDE_KRW,
    MAX_CONTRACTS_PER_VENDOR,
    MAX_VENDORS_PER_TENANT,
    MODULE_TAG,  # m25_finops_vendor_management
    SELECTION_CANDIDATE_LIMIT_DEFAULT,
    SELECTION_SCORE_VERSION_MAX,
    SELECTION_THRESHOLD_DEFAULT,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    VENDOR_BLACKLIST_GATE_FLAGS,
    VENDOR_CADENCE_HOURS_KST,
    VENDOR_DEFAULTS,
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VENDOR_PERFORMANCE_DIMENSION_WEIGHTS,
    VENDOR_RECIPIENT_TEMPLATES,
    VENDOR_RISK_HIGH_THRESHOLD,
    VENDOR_RISK_LOW_THRESHOLD,
    VENDOR_RISK_MEDIUM_THRESHOLD,
    VENDOR_SELECTION_DIMENSION_WEIGHTS,
    Vendor,
    VendorApprovalStepStatus,
    VendorBlacklistEntry,
    VendorCategory,
    VendorContract,
    VendorContractLifecycle,
    VendorPerformanceScorecard,
    VendorPerformanceSeverity,
    VendorSelectionMode,
    VendorSelectionScore,
    VendorSpendAttribution,
    VendorStatus,
    advance_contract_lifecycle,
    aggregate_vendor_catalog,
    aggregate_vendor_contract_lifecycle,
    aggregate_vendor_performance,
    aggregate_vendor_selection,
    aggregate_vendor_spend_attribution,
    apply_vendor_selection_threshold,
    approve_contract_step,
    blacklist_vendor,
    change_vendor_status,
    check_auto_renewal_window,
    check_over_budget,
    check_vendor_blacklist_gate,
    classify_performance_severity,
    compute_monthly_score,
    compute_quarterly_score,
    compute_vendor_risk_score,
    compute_vendor_spend_attribution,
    create_vendor,
    create_vendor_contract,
    daily_vendor_lifecycle_job,
    evaluate_vendor_performance,
    monthly_vendor_performance_job,
    monthly_vendor_spend_attribution_job,
    notify_listen_channels,
    override_selection_score_per_tenant,
    quarterly_vendor_review_job,
    reconcile_cross_budget,
    reject_contract_step,
    request_contract_approval,
    request_contract_renewal,
    score_vendor,
    schedule_vendor_management_jobs,
    terminate_contract,
    update_vendor,
    validate_vendor_scores,
    vendor_management_router,
)

# Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
# pre-detection layer territory. 5-NEW-module composition layer
# (anomaly_ml_prediction_engine + anomaly_ml_model_registry +
# anomaly_ml_training_pipeline + anomaly_ml_scoring +
# anomaly_ml_ensemble_consensus) + 5 model types ensemble (prophet
# 0.30 + lstm 0.30 + arima 0.15 + isolation_forest 0.15 + autoencoder
# 0.10) + 8 features from multi-phase ledger (Phase 11 cost_total_krw +
# Phase 23 cost_per_unit + Phase 24 variance_pct + Phase 24
# budget_consumption_pct + Phase 22 settlement_3way_match_score +
# Phase 14 optimization_savings_amount + Phase 13 month_seasonality +
# holiday_flag) + model_registry versioning semver + A/B testing
# champion/challenger traffic_split 50/50 + 3 drift detection types
# (data + concept + prediction PSI 0.25) + training_pipeline scheduled
# retraining KST 매주 일요일 03:00 + drift-triggered retraining +
# SHAP feature importance + 12 NEW audit actions + 16 NEW typed
# exception classes CR 12-5 D-14 envelope + dashboard UI 5
# sub-components + Capability matrix v1.52 EXTENSION
# FINOPS_COST_ANOMALY_ML_PREDICTION row 1 NEW (Phase 26 4-industry
# grants ✅/✅/✅/✅ industry-agnostic CR 12-1 L4 verbatim) + dry-run +
# `--finops-cost-anomaly-ml-prediction-dry-run` 1 NEW CLI flag +
# wire scope T1~T8 + AD-55 (a)~(g) 7 sub-decisions verbatim
# cross-reference.
from apps.api.modules.finops.cost_anomaly_ml_prediction import (  # noqa: E402
    AUTO_PROMOTE_CONSECUTIVE_DAYS,
    AUTO_PROMOTE_MARGIN,
    COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION,
    DEFAULT_ENSEMBLE_WEIGHTS,
    DEFAULT_THRESHOLD,
    DEFAULT_WEIGHTS,
    DRIFT_PSI_THRESHOLD_DEFAULT,
    FEATURE_NAMES,
    KST_TIMEZONE,
    LISTEN_NOTIFY_CHANNELS,
    ML_BATCH_SIZE_DEFAULT,
    ML_BATCH_SIZE_MAX,
    ML_CADENCE_HOURS_KST,
    ML_DEFAULTS,
    ML_INFERENCE_P95_LATENCY_MS,
    ML_MODEL_LRU_CACHE_MAX,
    ML_RECIPIENT_TEMPLATES,
    MODEL_HYPERPARAMETERS,
    MODEL_SCORING_WEIGHTS,
    PREDICTION_HORIZON_DAYS_DEFAULT,
    SEMVER_DEFAULT_VERSION,
    TRAINING_CRON_SCHEDULE,
    TRAINING_DATA_WINDOW_DAYS_DEFAULT,
    TRAINING_DATA_WINDOW_MAX_DAYS,
    TRAINING_DATA_WINDOW_MIN_DAYS,
    TRAINING_RETRY_BASE_SECONDS,
    TRAINING_RETRY_MAX,
    TRAINING_RETRY_MAX_SECONDS,
    TRAINING_TIMEOUT_SECONDS,
    TRAFFIC_SPLIT_DEFAULT,
    AnomalyMLDryRunMode,
    AnomalyMLPrediction,
    AnomalyMLScoreResult,
    DriftType,
    ModelRegistryEntry,
    ModelTrainingJob,
    ModelType,
    PredictionMethod,
    PredictionStatus,
    TrainingJobStatus,
    aggregate_predictions,
    batch_predict_anomaly_scores,
    cancel_training_job,
    consensus_detected,
    create_prediction,
    daily_drift_detection_job,
    daily_model_promotion_check_job,
    deprecate_model,
    ensemble_consensus_score,
    get_training_job_status,
    list_active_models,
    list_predictions,
    list_training_history,
    nightly_batch_inference_job,
    notify_listen_channels,
    predict_anomaly_score,
    register_model,
    retire_prediction,
    schedule_cost_anomaly_ml_prediction_jobs,
    score_threshold_anomaly,
    train_model,
    update_model_status,
    update_prediction,
    weekly_scheduled_training_job,
)
