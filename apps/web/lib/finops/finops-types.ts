/**
 * apps/web/lib/finops/finops-types.ts —
 * Phase 11 T7 (cj-style 107번째 wire) — FinOps Showback / Chargeback
 * TypedDict parity (CR 12-5 D-PARITY-01 inversion).
 * Phase 12 T7 (cj-style 111번째 wire) — Cost Anomaly Detection &
 * Budget Alerting TypedDict parity EXTENSION.
 *
 * Mirrors the backend Python TypedDicts in apps/api/modules/finops/:
 *   - ShowbackDefinition
 *   - DepartmentBreakdown
 *   - ComparisonView
 *   - ChargebackRule
 *   - ChargebackResult
 *   - DepartmentCostCenterMapping
 *   - AnomalyDefinition (Phase 12 EXTENSION)
 *   - DetectionResult (Phase 12 EXTENSION)
 *   - BudgetDefinition (Phase 12 EXTENSION)
 *   - AlertThresholds (Phase 12 EXTENSION)
 *   - BudgetAlert (Phase 12 EXTENSION)
 *   - AlertRouting (Phase 12 EXTENSION)
 *   - ForecastAccuracyMetrics (Phase 12 EXTENSION)
 */

export type {
  AlertChannel,
  AlertDispatchStatus,
  AlertLevel,
  AlertRouting,
  AlertThresholds,
  AccuracyStatus,
  AnomalyDefinition,
  BaselineWindow,
  BudgetAlert,
  BudgetDefinition,
  BudgetPeriod,
  BudgetScope,
  BudgetStatus,
  DetectionMethod,
  DetectionResult,
  DetectionStatus,
  Dimension,
  ForecastAccuracyMetrics,
  Severity,
} from "@/lib/finops/anomaly-types";
export type GroupBy =
  | "department"
  | "cost_center"
  | "product_line"
  | "service"
  | "custom_tag";

export type PeriodMode =
  | "current_month"
  | "previous_month"
  | "last_3_months"
  | "last_6_months"
  | "ytd"
  | "custom_range";

export type ComparisonPeriod =
  | "previous_month"
  | "previous_3_months"
  | "previous_6_months"
  | "previous_year_same_month"
  | "none";

export type RuleType =
  | "flat_fee"
  | "proportional_allocation"
  | "metered";

export type CostAllocationMethod = "direct" | "indirect" | "shared";

export type ExportFormat = "csv" | "pdf";

export interface ShowbackDefinition {
  tenant_id: string;
  showback_id?: string;
  group_by: GroupBy;
  period_mode: PeriodMode;
  period_start?: string;
  period_end?: string;
  currency_code: string;
  comparison_period?: ComparisonPeriod;
  governance_required: boolean;
  industry?: string;
  override_applied?: boolean;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  page_size?: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  offset?: number;
  trace_id?: string;
}

export interface DepartmentBreakdown {
  department_id: string;
  department_name: string;
  cost_center_id: string;
  cost_center_code: string;
  total_amount: string;
  currency_code: string;
  period_key: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  rank: number;
}

export interface ComparisonView {
  department_id: string;
  current_period_amount: string;
  previous_period_amount: string;
  delta_amount: string;
  delta_pct: string;
  currency_code: string;
  comparison_period: ComparisonPeriod;
}

export interface ChargebackRule {
  tenant_id: string;
  chargeback_rule_id?: string;
  rule_type: RuleType;
  cost_allocation_method: CostAllocationMethod;
  markup_pct?: string;
  tax_pct?: string;
  flat_fee_amount?: string;
  proportional_share_pct?: string;
  metered_unit_price?: string;
  metered_quantity?: string;
  tier_breaks?: Array<[string, string]>;
  region_weight_map?: Record<string, string>;
  currency_code?: string;
  dry_run?: boolean;
  trace_id?: string;
}

export interface ChargebackResult {
  chargeback_id: string;
  tenant_id: string;
  period_key: string;
  department_id: string;
  cost_center_id: string;
  rule_type: RuleType;
  base_amount: string;
  markup_amount: string;
  tax_amount: string;
  total_amount: string;
  currency_code: string;
  computed_at: string;
  trace_id: string;
}

export interface DepartmentCostCenterMapping {
  id?: string;
  tenant_id: string;
  department_id: string;
  department_name: string;
  cost_center_id: string;
  auto_created: boolean;
  created_at?: string;
  updated_at?: string;
  created_by: string;
  updated_by: string;
  trace_id?: string;
}
