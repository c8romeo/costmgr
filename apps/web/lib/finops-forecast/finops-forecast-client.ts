/**
 * apps/web/lib/finops-forecast/finops-forecast-client.ts —
 * Phase 13 forecast client (CR 12-5 D-PARITY-01 mirror).
 *
 * Phase 13 (cj-style 115번째 wire) — TS TypedDict mirror of Python
 * TypedDicts in apps/api/modules/finops/. D-PARITY-01 verification
 * ensures Python ↔ TS parity.
 */

export type TargetMetric =
  | "department"
  | "cost_center"
  | "product_line"
  | "service"
  | "tenant_total";

export type HorizonMonths = "3m" | "6m" | "12m" | "24m";
export type ModelType = "arima" | "prophet" | "lstm" | "ensemble";
export type ConfidenceLevel = 80 | 90 | 95 | 99;
export type ForecastStatus = "active" | "paused" | "expired";
export type ResourceType = "compute" | "storage" | "network";
export type SaturationLevel = "ok" | "warning" | "critical";
export type SeverityLevel = "normal" | "warning" | "critical" | "exceeded";

export interface ForecastDefinition {
  forecast_id: string;
  tenant_id: string;
  target_metric: TargetMetric;
  dimension_value: string;
  horizon_months: HorizonMonths;
  model_type: ModelType;
  confidence_level: ConfidenceLevel;
  retraining_cron: string;
  status: ForecastStatus;
  created_at: string;
  updated_at: string;
}

export interface ForecastResult {
  forecast_id: string;
  tenant_id: string;
  target_metric: TargetMetric;
  horizon_months: HorizonMonths;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  predicted_values: number[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  confidence_lower: number[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  confidence_upper: number[];
  model_type: ModelType;
  model_version: string;
  generated_at: string;
}

export interface CapacityHeadroomReport {
  report_id: string;
  tenant_id: string;
  resource_type: ResourceType;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  saturation_pct: number;
  saturation_level: SaturationLevel;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  lookahead_days: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  predicted_utilization: number[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  headroom_pct: number;
  primary_model: ModelType;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  ensemble_predicted: number[];
  recommendation: string;
  trace_id: string;
  created_at: string;
  expires_at: string;
}

export interface BurnRateProjection {
  projection_id: string;
  tenant_id: string;
  budget_id: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  consumed_budget: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_budget: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  elapsed_days: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  remaining_days: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  burn_rate_pct: number;
  severity: SeverityLevel;
  alert_required: boolean;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  predicted_end_period_spend: number;
  trace_id: string;
}

export interface ForecastAccuracy {
  accuracy_id: string;
  tenant_id: string;
  target_metric: TargetMetric;
  model_type: ModelType;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  mae: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  mape: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  rmse: number;
  mape_above_baseline: boolean;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  periods_above_threshold: number;
  evaluated_at: string;
}

export class FinopsForecastApiError extends Error {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "FinopsForecastApiError";
  }
}

const API_BASE = "/api/v1/finops-forecast";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    throw new FinopsForecastApiError(
      `FinOps forecast API error: ${res.statusText}`,
      res.status,
    );
  }
  return res.json() as Promise<T>;
}

export async function fetchFinopsForecastDefinition(
  params: { target_metric: TargetMetric; horizon: HorizonMonths },
): Promise<ForecastDefinition> {
  return fetchJson<ForecastDefinition>(
    `${API_BASE}/definition?target_metric=${params.target_metric}&horizon=${params.horizon}`,
  );
}

export async function fetchFinopsCapacityHeadroom(
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  params: { resource_type: ResourceType; lookahead_days: number },
): Promise<CapacityHeadroomReport> {
  return fetchJson<CapacityHeadroomReport>(
    `${API_BASE}/capacity-headroom?resource_type=${params.resource_type}&lookahead_days=${params.lookahead_days}`,
  );
}

export async function fetchFinopsBudgetBurnRate(
  params: { budget_id: string },
): Promise<BurnRateProjection> {
  return fetchJson<BurnRateProjection>(
    `${API_BASE}/budget-burnrate?budget_id=${params.budget_id}`,
  );
}

export async function fetchFinopsForecastAccuracy(
  params: { target_metric: TargetMetric; model_type: ModelType },
): Promise<ForecastAccuracy> {
  return fetchJson<ForecastAccuracy>(
    `${API_BASE}/accuracy?target_metric=${params.target_metric}&model_type=${params.model_type}`,
  );
}