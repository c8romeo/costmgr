"""apps.api.modules.finops — FinOps Cost Anomaly Detection & Budget Alerting territory.

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.1~§F27.7 + AD-38 (a)~(g) sub-decisions).

Phase 12 (cj-style 111번째 wire) — Cost Anomaly Detection & Budget
Alerting territory (PRD §F28.1~§F28.8 + AD-39 (a)~(g) sub-decisions).

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
- `serializers` — m19_finops.finops_serializers module version SSOT.

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
    ANOMALY_THRESHOLD_DEFAULTS,
    ALL_BASELINE_WINDOWS,
    ALL_DETECTION_METHODS,
    ALL_DIMENSIONS,
    AnomalyDefinition,
    detect_anomaly,
    parse_anomaly_definition,
)
from apps.api.modules.finops.budget_definition import (
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_EXCEEDED,
    ALERT_LEVEL_WARNING,
    ALL_ALERT_LEVELS,
    ALL_BUDGET_PERIODS,
    ALL_BUDGET_SCOPES,
    BUDGET_THRESHOLD_DEFAULTS,
    BudgetDefinition,
    define_budget,
    parse_budget_definition,
)
from apps.api.modules.finops.forecast_accuracy import (
    ForecastAccuracyMetrics,
    compute_mae,
    compute_mape,
    compute_rmse,
    evaluate_forecast_accuracy,
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
]