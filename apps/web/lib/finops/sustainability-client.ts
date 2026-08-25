/**
 * apps/web/lib/finops/sustainability-client.ts —
 * Phase 17 T7 (cj-style 131번째 wire) — FinOps Sustainability & Carbon
 * Reporting client library (CR 12-5 D-PARITY-01 inversion TypeScript mirror).
 *
 * Provides typed client wrappers for the 4 backend sustainability endpoints:
 *   - aggregateCarbonEmissions → CarbonEmissionsRollup
 *   - selectSustainabilityKPIs → SustainabilityKPIMetric[]
 *   - generateSustainabilityReport → SustainabilityReport
 *   - dispatchSustainabilityReport → ScheduledSustainabilityDispatch
 */

import type {
  CarbonEmissionsRollup,
  ScheduledSustainabilityDispatch,
  SustainabilityCadence,
  SustainabilityDispatchSchedule,
  SustainabilityExportFormat,
  SustainabilityFramework,
  SustainabilityKPIMetric,
  SustainabilityRecipientStrategy,
  SustainabilityReport,
} from "@/lib/finops/sustainability-types";

const SUSTAINABILITY_BASE_PATH = "/api/v1/admin/finops/sustainability";

export interface AggregateCarbonEmissionsRequest {
  tenant_id: string;
  scope_type?: "tenant" | "department" | "cost_center" | "product_line";
  scope_id?: string;
  period_key: string;
  trace_id?: string;
  industry?: string;
}

export interface SelectSustainabilityKPIsRequest {
  tenant_id: string;
  period_key: string;
  trace_id?: string;
  industry?: string;
}

export interface GenerateSustainabilityReportRequest {
  tenant_id: string;
  period_key: string;
  cadence?: SustainabilityCadence;
  export_format?: SustainabilityExportFormat;
  framework?: SustainabilityFramework;
  trace_id?: string;
  actor_id?: string;
  industry?: string;
}

export interface DispatchSustainabilityReportRequest {
  tenant_id: string;
  dispatch_schedule: SustainabilityDispatchSchedule;
  period_key: string;
  recipient_strategy: SustainabilityRecipientStrategy;
  trace_id?: string;
}

async function sustainabilityFetch<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${SUSTAINABILITY_BASE_PATH}${path}`,
    init,
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `sustainability_client: ${path} failed with HTTP ${response.status}: ${errorText}`,
    );
  }
  return (await response.json()) as T;
}

export async function aggregateCarbonEmissions(
  req: AggregateCarbonEmissionsRequest,
): Promise<CarbonEmissionsRollup> {
  return sustainabilityFetch<CarbonEmissionsRollup>("/carbon-emissions/aggregate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function selectSustainabilityKPIs(
  req: SelectSustainabilityKPIsRequest,
): Promise<SustainabilityKPIMetric[]> {
  return sustainabilityFetch<SustainabilityKPIMetric[]>("/kpis/select", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function generateSustainabilityReport(
  req: GenerateSustainabilityReportRequest,
): Promise<SustainabilityReport> {
  return sustainabilityFetch<SustainabilityReport>("/reports/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function dispatchSustainabilityReport(
  req: DispatchSustainabilityReportRequest,
): Promise<ScheduledSustainabilityDispatch> {
  return sustainabilityFetch<ScheduledSustainabilityDispatch>("/dispatch/schedule", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}