"""apps.api.modules.finops — FinOps Forecasting & Capacity Planning territory.

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.1~§F27.7 + AD-38 (a)~(g) sub-decisions).

Phase 12 (cj-style 111번째 wire) — Cost Anomaly Detection & Budget
Alerting territory (PRD §F28.1~§F28.8 + AD-39 (a)~(g) sub-decisions).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.1~§F29.8 + AD-39 (a)~(g) sub-decisions).

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
  BACKFILL).

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
]
