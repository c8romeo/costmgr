/**
 * apps/web/lib/finops/sustainability-types.ts —
 * Phase 17 T7 (cj-style 131번째 wire) — FinOps Sustainability & Carbon
 * Reporting TypedDict parity (CR 12-5 D-PARITY-01 inversion).
 *
 * Mirrors the backend Python TypedDicts in apps/api/modules/finops/sustainability/:
 *   - CarbonEmissionsRollup (14 fields)
 *   - SustainabilityKPIMetric (8 fields)
 *   - SustainabilityReport (13 fields)
 *   - ScheduledSustainabilityDispatch (10 fields)
 */

export type CarbonScopeType =
  | "tenant"
  | "department"
  | "cost_center"
  | "product_line";

export type CarbonOffsetRegistry = "vcu" | "cer" | "kcu";

export type SustainabilityCadence = "monthly" | "quarterly" | "annual";

export type SustainabilityExportFormat = "pdf" | "csv" | "excel";

export type SustainabilityDispatchSchedule =
  | "weekly"
  | "monthly"
  | "quarterly"
  | "annual";

export type SustainabilityRecipientStrategy =
  | "owner_only"
  | "sustainability_team"
  | "board_observers"
  | "custom_recipients";

export type SustainabilityFramework =
  | "csrd"
  | "sec_climate"
  | "eu_taxonomy"
  | "ifrs_s2"
  | "kssb";

export type SustainabilityKPIThresholdStatus =
  | "on_track"
  | "warning"
  | "critical";

export interface CarbonEmissionsRollup {
  carbon_rollup_id: string;
  tenant_id: string;
  scope_type: CarbonScopeType;
  scope_id: string;
  period_key: string;
  scope_chain: Record<string, unknown>;
  total_carbon_emissions_kgco2e: number;
  scope1_emissions_kgco2e: number;
  scope2_emissions_kgco2e: number;
  scope3_emissions_kgco2e: number;
  carbon_offset_kgco2e: number;
  net_carbon_emissions_kgco2e: number;
  renewable_energy_pct: number;
  computed_at: string;
  trace_id: string;
}

export interface SustainabilityKPIMetric {
  kpi_name: string;
  kpi_value: number;
  kpi_unit: string;
  kpi_delta?: number | null;
  kpi_trend: "up" | "down" | "flat";
  kpi_threshold_status: SustainabilityKPIThresholdStatus;
  kpi_computed_at: string;
  trace_id: string;
}

export interface SustainabilityReport {
  report_id: string;
  tenant_id: string;
  scope_type: CarbonScopeType;
  scope_id: string;
  period_key: string;
  cadence: SustainabilityCadence;
  framework: SustainabilityFramework;
  export_format: SustainabilityExportFormat;
  report_file_url: string;
  report_size_bytes: number;
  report_generated_at: string;
  generated_by: string;
  status: "generating" | "completed" | "failed" | "expired";
  trace_id: string;
}

export interface ScheduledSustainabilityDispatch {
  dispatch_id: string;
  tenant_id: string;
  dispatch_schedule: SustainabilityDispatchSchedule;
  cron_expression: string;
  recipient_strategy: SustainabilityRecipientStrategy;
  recipient_list: Record<string, unknown>;
  report_id?: string | null;
  status:
    | "scheduled"
    | "running"
    | "completed"
    | "failed"
    | "cancelled";
  scheduled_at: string;
  trace_id: string;
}

export const ALL_SUSTAINABILITY_KPI_NAMES = [
  "total_carbon_emissions_kgco2e",
  "scope1_emissions_kgco2e",
  "scope2_emissions_kgco2e",
  "scope3_emissions_kgco2e",
  "carbon_intensity_kgco2e_per_krw",
  "data_center_pue",
  "renewable_energy_pct",
  "carbon_offset_kgco2e",
] as const;

export type SustainabilityKPIName =
  (typeof ALL_SUSTAINABILITY_KPI_NAMES)[number];