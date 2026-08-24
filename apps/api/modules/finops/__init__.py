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
]
