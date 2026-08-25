/**
 * apps/web/lib/finops/commitment-client.ts —
 * Phase 18 T7 (cj-style 135번째 wire) — FinOps Cloud Commitment Management
 * client library (CR 12-5 D-PARITY-01 inversion TypeScript mirror).
 *
 * Provides typed client wrappers for the 4 backend commitment endpoints:
 *   - aggregateCommitmentInventory → CommitmentInventoryRollup
 *   - selectCommitmentKPIs → CommitmentKPI[]
 *   - generateCommitmentReport → CommitmentReport
 *   - dispatchCommitmentReport → ScheduledCommitmentDispatch
 *
 * AD-14 stack pin — fetch wrapper aligned with Phase 17 sustainability-client.
 */

import type {
  CommitmentCadence,
  CommitmentDispatchSchedule,
  CommitmentExportFormat,
  CommitmentFramework,
  CommitmentInventoryRollup,
  CommitmentKPI,
  CommitmentRecipientStrategy,
  CommitmentReport,
  ScheduledCommitmentDispatch,
} from "@/lib/finops/commitment-types";

const COMMITMENT_BASE_PATH = "/api/v1/admin/finops/commitment";

export interface AggregateCommitmentInventoryRequest {
  tenant_id: string;
  scope_type?: "tenant" | "department" | "cost_center" | "product_line";
  scope_id?: string;
  period_key: string;
  trace_id?: string;
  industry?: string;
  dry_run?: boolean;
}

export interface SelectCommitmentKPIsRequest {
  tenant_id: string;
  period_key: string;
  trace_id?: string;
  industry?: string;
}

export interface GenerateCommitmentReportRequest {
  tenant_id: string;
  period_key: string;
  cadence?: CommitmentCadence;
  export_format?: CommitmentExportFormat;
  framework?: CommitmentFramework;
  trace_id?: string;
  actor_id?: string;
  industry?: string;
}

export interface DispatchCommitmentReportRequest {
  tenant_id: string;
  dispatch_schedule: CommitmentDispatchSchedule;
  period_key: string;
  recipient_strategy: CommitmentRecipientStrategy;
  trace_id?: string;
}

async function commitmentFetch<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${COMMITMENT_BASE_PATH}${path}`,
    init,
  );
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `commitment_client: ${path} failed with HTTP ${response.status}: ${errorText}`,
    );
  }
  return (await response.json()) as T;
}

export async function aggregateCommitmentInventory(
  req: AggregateCommitmentInventoryRequest,
): Promise<CommitmentInventoryRollup> {
  return commitmentFetch<CommitmentInventoryRollup>(
    "/inventory/aggregate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    },
  );
}

export async function selectCommitmentKPIs(
  req: SelectCommitmentKPIsRequest,
): Promise<CommitmentKPI[]> {
  return commitmentFetch<CommitmentKPI[]>("/kpis/select", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function generateCommitmentReport(
  req: GenerateCommitmentReportRequest,
): Promise<CommitmentReport> {
  return commitmentFetch<CommitmentReport>("/reports/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function dispatchCommitmentReport(
  req: DispatchCommitmentReportRequest,
): Promise<ScheduledCommitmentDispatch> {
  return commitmentFetch<ScheduledCommitmentDispatch>(
    "/dispatch/schedule",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    },
  );
}
