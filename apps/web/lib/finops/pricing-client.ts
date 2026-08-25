/**
 * apps/web/lib/finops/pricing-client.ts —
 * Phase 19 T7 (cj-style 139번째 wire) — FinOps Pricing, Rate Card & TCO
 * Modeling client library (CR 12-5 D-PARITY-01 inversion TypeScript mirror).
 *
 * Provides typed client wrappers for the 4 backend pricing endpoints:
 *   - aggregateRateCardInventory → RateCardInventory
 *   - selectTCOKPIs → TCOKPIBundle[]
 *   - generatePricingReport → PricingReport
 *   - dispatchPricingReport → ScheduledPricingDispatch
 *
 * AD-14 stack pin — fetch wrapper aligned with Phase 18 commitment-client.
 */

import type {
  PricingCadence,
  PricingDispatchSchedule,
  PricingExportFormat,
  PricingFramework,
  PricingRecipientStrategy,
  PricingReport,
  RateCardInventory,
  ScheduledPricingDispatch,
  TCOKPIBundle,
} from "@/lib/finops/pricing-types";

const PRICING_BASE_PATH = "/api/v1/admin/finops/pricing";

export interface AggregateRateCardInventoryRequest {
  tenant_id: string;
  scope_type?: "tenant" | "department" | "cost_center" | "product_line";
  scope_id?: string;
  period_key: string;
  trace_id?: string;
  industry?: string;
  dry_run?: boolean;
}

export interface SelectTCOKPIsRequest {
  tenant_id: string;
  period_key: string;
  trace_id?: string;
  industry?: string;
}

export interface GeneratePricingReportRequest {
  tenant_id: string;
  period_key: string;
  cadence?: PricingCadence;
  export_format?: PricingExportFormat;
  framework?: PricingFramework;
  trace_id?: string;
  actor_id?: string;
  industry?: string;
}

export interface DispatchPricingReportRequest {
  tenant_id: string;
  dispatch_schedule: PricingDispatchSchedule;
  period_key: string;
  recipient_strategy: PricingRecipientStrategy;
  trace_id?: string;
}

async function pricingFetch<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const response = await fetch(`${PRICING_BASE_PATH}${path}`, init);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `pricing_client: ${path} failed with HTTP ${response.status}: ${errorText}`,
    );
  }
  return (await response.json()) as T;
}

export async function aggregateRateCardInventory(
  req: AggregateRateCardInventoryRequest,
): Promise<RateCardInventory> {
  return pricingFetch<RateCardInventory>("/rate-card/aggregate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function selectTCOKPIs(
  req: SelectTCOKPIsRequest,
): Promise<TCOKPIBundle[]> {
  return pricingFetch<TCOKPIBundle[]>("/tco-kpis/select", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function generatePricingReport(
  req: GeneratePricingReportRequest,
): Promise<PricingReport> {
  return pricingFetch<PricingReport>("/reports/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function dispatchPricingReport(
  req: DispatchPricingReportRequest,
): Promise<ScheduledPricingDispatch> {
  return pricingFetch<ScheduledPricingDispatch>("/dispatch/schedule", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}
