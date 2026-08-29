/**
 * apps/web/lib/finops/pricing-types.ts —
 * Phase 19 T7 (cj-style 139번째 wire) — FinOps Pricing, Rate Card & TCO
 * Modeling TypedDict parity (CR 12-5 D-PARITY-01 inversion).
 *
 * Mirrors the backend Python TypedDicts in apps/api/modules/finops/pricing/:
 *   - RateCardInventory (18 fields)
 *   - TCOKPIBundle (10 fields)
 *   - PricingReport (14 fields)
 *   - ScheduledPricingDispatch (11 fields)
 *
 * CR lessons applied:
 * - CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 *   verbatim — every field name and type aligned.
 * - AD-46 (a)~(g) — 5-cloud-provider (AWS + Azure + GCP + Naver + KT)
 *   pricing inventory + 8 NEW KPI + 3 export_format + 4 cron
 *   schedules + 4 recipient strategies + 5 frameworks.
 */

export type PricingScopeType =
  | "tenant"
  | "department"
  | "cost_center"
  | "product_line";

export type PricingCloudProvider = "aws" | "azure" | "gcp" | "naver" | "kt";

export type PricingModel =
  | "on_demand"
  | "1y_ri"
  | "3y_ri"
  | "1y_sp"
  | "3y_sp"
  | "savings_plan";

export type PricingUnitMetric =
  | "cost_per_user"
  | "cost_per_transaction"
  | "cost_per_request"
  | "cost_per_hour";

export type PricingCadence = "monthly" | "quarterly" | "annual";

export type PricingExportFormat = "pdf" | "csv" | "excel";

export type PricingDispatchSchedule =
  | "weekly"
  | "monthly"
  | "quarterly"
  | "annual";

export type PricingRecipientStrategy =
  | "owner_only"
  | "pricing_team"
  | "finance_team"
  | "custom_recipients";

export type PricingFramework =
  | "finops_foundation"
  | "aws_pricing_models"
  | "azure_pricing_calculator"
  | "gcp_pricing_calculator"
  | "korea_procurement";

export type PricingKPIThresholdStatus =
  | "on_track"
  | "warning"
  | "critical";

export interface RateCardInventory {
  rate_card_id: string;
  tenant_id: string;
  scope_type: PricingScopeType;
  scope_id: string;
  period_key: string;
  scope_chain: Record<string, unknown>;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_blended_rate_krw_per_hour: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  effective_discount_pct: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  tco_1year_commitment_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  tco_3year_commitment_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  tco_on_demand_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  cost_per_user_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  cost_per_transaction_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  unit_economics_score: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  cloud_provider_breakdown: Record<string, number>;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  pricing_model_breakdown: Record<string, number>;
  cache_key: string;
  computed_at: string;
  trace_id: string;
}

export interface TCOKPIBundle {
  kpi_id: string;
  tenant_id: string;
  scope_type: PricingScopeType;
  scope_id: string;
  period_key: string;
  kpi_name: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  kpi_value: number;
  kpi_unit: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  kpi_delta?: number | null;
  kpi_trend: "up" | "down" | "flat";
  kpi_threshold_status: PricingKPIThresholdStatus;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  break_even_months: number;
  computed_at: string;
  trace_id: string;
}

export interface PricingReport {
  report_id: string;
  tenant_id: string;
  scope_type: PricingScopeType;
  scope_id: string;
  period_key: string;
  cadence: PricingCadence;
  framework: PricingFramework;
  export_format: PricingExportFormat;
  report_file_url: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  report_size_bytes: number;
  report_generated_at: string;
  generated_by?: string | null;
  status: "generating" | "completed" | "failed" | "expired";
  expires_at?: string | null;
  trace_id: string;
}

export interface ScheduledPricingDispatch {
  dispatch_id: string;
  tenant_id: string;
  dispatch_schedule: PricingDispatchSchedule;
  cron_expression: string;
  recipient_strategy: PricingRecipientStrategy;
  recipient_list: Record<string, unknown>;
  report_id?: string | null;
  status:
    | "scheduled"
    | "running"
    | "completed"
    | "failed"
    | "cancelled";
  scheduled_at: string;
  last_run_at?: string | null;
  next_run_at?: string | null;
  trace_id: string;
}

export const ALL_PRICING_KPI_NAMES = [
  "total_blended_rate_krw_per_hour",
  "effective_discount_pct",
  "tco_1year_commitment_krw",
  "tco_3year_commitment_krw",
  "tco_on_demand_krw",
  "cost_per_user_krw",
  "cost_per_transaction_krw",
  "unit_economics_score",
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type PricingKPIName = (typeof ALL_PRICING_KPI_NAMES)[number];
