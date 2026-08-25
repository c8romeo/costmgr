/**
 * apps/web/lib/finops/commitment-types.ts —
 * Phase 18 T7 (cj-style 135번째 wire) — FinOps Cloud Commitment Management
 * TypedDict parity (CR 12-5 D-PARITY-01 inversion).
 *
 * Mirrors the backend Python TypedDicts in apps/api/modules/finops/commitment/:
 *   - CommitmentInventoryRollup (16 fields)
 *   - CommitmentKPI (16 fields)
 *   - CommitmentReport (14 fields)
 *   - ScheduledCommitmentDispatch (10 fields)
 *
 * CR lessons applied:
 * - CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 *   verbatim — every field name and type aligned.
 * - AD-45 (a)~(g) — 5-cloud-provider (AWS + Azure + GCP + Naver + KT)
 *   commitment inventory + 8 NEW KPI + 3 export_format + 4 cron
 *   schedules + 4 recipient strategies + 5 frameworks.
 */

export type CommitmentScopeType =
  | "tenant"
  | "department"
  | "cost_center"
  | "product_line";

export type CloudProvider = "aws" | "azure" | "gcp" | "naver" | "kt";

export type CommitmentType =
  | "ec2_ri"
  | "rds_ri"
  | "ec2_sp"
  | "s3_sp"
  | "redshift_sp"
  | "dynamodb_sp";

export type CommitmentTerm = "1_year" | "3_year";

export type CommitmentCadence = "monthly" | "quarterly" | "annual";

export type CommitmentExportFormat = "pdf" | "csv" | "excel";

export type CommitmentDispatchSchedule =
  | "weekly"
  | "monthly"
  | "quarterly"
  | "annual";

export type CommitmentRecipientStrategy =
  | "owner_only"
  | "commitment_team"
  | "finance_team"
  | "custom_recipients";

export type CommitmentFramework =
  | "finops_foundation"
  | "aws_cost_optimization"
  | "azure_cost_optimization"
  | "gcp_cost_optimization"
  | "korea_procurement";

export type CommitmentKPIThresholdStatus =
  | "on_track"
  | "warning"
  | "critical";

export interface CommitmentInventoryRollup {
  commitment_rollup_id: string;
  tenant_id: string;
  scope_type: CommitmentScopeType;
  scope_id: string;
  period_key: string;
  scope_chain: Record<string, unknown>;
  total_commitment_value_krw: number;
  coverage_pct: number;
  utilization_pct: number;
  expiring_commitments_30d: number;
  recommended_purchase_krw: number;
  savings_realized_krw: number;
  idle_commitment_krw: number;
  renewal_decision_score: number;
  cache_key: string;
  computed_at: string;
  trace_id: string;
}

export interface CommitmentKPI {
  kpi_id: string;
  tenant_id: string;
  scope_type: CommitmentScopeType;
  scope_id: string;
  period_key: string;
  kpi_name: string;
  kpi_value: number;
  kpi_unit: string;
  kpi_delta?: number | null;
  kpi_trend: "up" | "down" | "flat";
  kpi_threshold_status: CommitmentKPIThresholdStatus;
  computed_at: string;
  trace_id: string;
}

export interface CommitmentReport {
  report_id: string;
  tenant_id: string;
  scope_type: CommitmentScopeType;
  scope_id: string;
  period_key: string;
  cadence: CommitmentCadence;
  framework: CommitmentFramework;
  export_format: CommitmentExportFormat;
  report_file_url: string;
  report_size_bytes: number;
  report_generated_at: string;
  generated_by?: string | null;
  status: "generating" | "completed" | "failed" | "expired";
  expires_at?: string | null;
  trace_id: string;
}

export interface ScheduledCommitmentDispatch {
  dispatch_id: string;
  tenant_id: string;
  dispatch_schedule: CommitmentDispatchSchedule;
  cron_expression: string;
  recipient_strategy: CommitmentRecipientStrategy;
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

export const ALL_COMMITMENT_KPI_NAMES = [
  "total_commitment_value_krw",
  "coverage_pct",
  "utilization_pct",
  "expiring_commitments_30d",
  "recommended_purchase_krw",
  "savings_realized_krw",
  "idle_commitment_krw",
  "renewal_decision_score",
] as const;

export type CommitmentKPIName = (typeof ALL_COMMITMENT_KPI_NAMES)[number];
