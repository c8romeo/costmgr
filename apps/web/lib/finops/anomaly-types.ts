/**
 * apps/web/lib/finops/anomaly-types.ts —
 * Phase 12 T7 (cj-style 111번째 wire) — FinOps Cost Anomaly Detection
 * & Budget Alerting TypedDict parity (CR 12-5 D-PARITY-01 inversion).
 *
 * Mirrors the backend Python TypedDicts in apps/api/modules/finops/:
 *   - AnomalyDefinition (8 fields, PRD §F28.1.1 verbatim)
 *   - DetectionResult (13 fields, PRD §F28.3.1 verbatim)
 *   - BudgetDefinition (12 fields, PRD §F28.2.1 verbatim)
 *   - AlertThresholds (3 fields, PRD §F28.2.5 verbatim)
 *   - BudgetAlert (12 fields, PRD §F28.4.1 verbatim)
 *   - AlertRouting (3 fields, PRD §F28.4.3 verbatim)
 *   - ForecastAccuracyMetrics (9 fields, PRD §F28.5.1 verbatim)
 */
export type DetectionMethod =
  | "z_score"
  | "iqr"
  | "ewma"
  | "isolation_forest";

export type Dimension =
  | "department"
  | "cost_center"
  | "product_line"
  | "service"
  | "tenant_total";

export type BaselineWindow = "last_30d" | "last_90d" | "ytd";

export type Severity = "low" | "medium" | "high" | "critical";

export type DetectionStatus = "confirmed" | "suspected" | "false_positive";

export type BudgetPeriod = "monthly" | "quarterly" | "yearly";

export type BudgetScope =
  | "tenant"
  | "department"
  | "cost_center"
  | "product_line";

export type BudgetStatus = "active" | "paused" | "expired";

export type AlertLevel = "warning" | "critical" | "exceeded";

export type AlertChannel = "slack" | "pagerduty" | "email";

export type AlertDispatchStatus =
  | "pending"
  | "sent"
  | "failed"
  | "deduplicated";

export type AccuracyStatus = "high" | "acceptable" | "degraded";

export interface AnomalyDefinition {
  tenant_id: string;
  period_key: string;
  dimension: Dimension;
  dimension_value: string;
  threshold_method: DetectionMethod;
  threshold_value: number;
  baseline_window: BaselineWindow;
  consecutive_periods_required: number;
  trace_id?: string;
}

export interface DetectionResult {
  result_id: string;
  tenant_id: string;
  period_key: string;
  dimension: Dimension;
  dimension_value: string;
  observed_cost: string;
  baseline_cost: string;
  deviation_pct: number;
  severity: Severity;
  methods_voted: DetectionMethod[];
  status: DetectionStatus;
  detected_at: string;
  trace_id: string;
}

export interface AlertThresholds {
  warning: number;
  critical: number;
  exceeded: number;
}

export interface BudgetDefinition {
  budget_id: string;
  tenant_id: string;
  period_key: string;
  budget_period: BudgetPeriod;
  scope: BudgetScope;
  scope_id: string;
  amount: string;
  currency_code: string;
  alert_thresholds: AlertThresholds;
  status: BudgetStatus;
  created_at: string;
  updated_at: string;
}

export interface AlertRouting {
  channels: AlertChannel[];
  recipients: string[];
  retry_policy: string;
}

export interface BudgetAlert {
  alert_id: string;
  tenant_id: string;
  budget_id: string;
  period_key: string;
  alert_level: AlertLevel;
  consumption_pct: number;
  consumption_amount: string;
  budget_amount: string;
  routing: AlertRouting;
  status: AlertDispatchStatus;
  created_at: string;
  trace_id: string;
}

export interface ForecastAccuracyMetrics {
  tenant_id: string;
  period_key: string;
  model_name: string;
  mae: number;
  mape: number;
  rmse: number;
  status: AccuracyStatus;
  retraining_recommended: boolean;
  trace_id: string;
}