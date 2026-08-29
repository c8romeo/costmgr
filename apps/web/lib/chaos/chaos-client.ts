/**
 * apps/web/lib/chaos/chaos-client.ts —
 * Phase 9 (cj-style 99번째 wire) — Chaos engineering client fetcher.
 *
 * TypedAPI client for /api/v1/admin/chaos/* routes. Mirrors
 * apps/web/lib/audit/audit-log-retention-client.ts pattern verbatim.
 *
 * CR 11-4 D-003 (typed exception envelope) +
 * CR 12-5 D-PARITY-01 (TS interface ↔ Python TypedDict parity).
 */

export type ChaosFaultType =
  | "latency"
  | "error"
  | "resource"
  | "network_partition"
  | "disk_io"
  | "db_connection_pool"
  | "cache_failure"
  | "dns_failure"
  | "process_kill"
  | "clock_skew";

export type ChaosBlastRadius =
  | "single_request"
  | "single_tenant"
  | "all_tenants"
  | "single_region"
  | "multi_region";

export type ChaosIntensity = "low" | "medium" | "high";

export type ChaosStatus =
  | "pending"
  | "running"
  | "completed"
  | "aborted"
  | "failed";

export type ChaosRegion = "seoul" | "tokyo" | "all";

export interface ChaosExperiment {
  experiment_id: string;
  experiment_name: string;
  fault_type: ChaosFaultType;
  blast_radius: ChaosBlastRadius;
  region: ChaosRegion;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  duration_seconds: number;
  intensity: ChaosIntensity;
  status: ChaosStatus;
  dry_run: boolean;
  started_at: string | null;
  trace_id: string;
}

export interface ChaosRollback {
  rollback_id: string;
  experiment_id: string;
  strategy: "automatic" | "manual" | "hybrid" | "scheduled_abort";
  reason: string;
  triggered_at: string;
}

export interface ChaosTriggerRequest {
  fault_type: ChaosFaultType;
  blast_radius: ChaosBlastRadius;
  region: ChaosRegion;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  duration_seconds: number;
  intensity: ChaosIntensity;
  dry_run: boolean;
}

export class ChaosExperimentApiError extends Error {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  readonly status: number;
  readonly traceId: string | null;
  constructor(
    message: string,
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    status: number,
    traceId: string | null = null,
  ) {
    super(message);
    this.name = "ChaosExperimentApiError";
    this.status = status;
    this.traceId = traceId;
  }
}

const API_BASE = "/api/v1/admin/chaos";

async function chaosFetch<T>(
  accessToken: string,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const traceId = res.headers.get("x-trace-id");
    const body = await res.text();
    throw new ChaosExperimentApiError(
      `chaos fetch failed: ${res.status} ${body}`,
      res.status,
      traceId,
    );
  }
  return (await res.json()) as T;
}

export async function listChaosExperiments(
  accessToken: string,
): Promise<{ experiments: ChaosExperiment[]; trace_id: string }> {
  return chaosFetch(accessToken, "/experiments", { method: "GET" });
}

export async function listChaosRollbacks(
  accessToken: string,
): Promise<{ rollbacks: ChaosRollback[]; trace_id: string }> {
  return chaosFetch(accessToken, "/rollbacks", { method: "GET" });
}

export async function triggerChaosExperiment(
  accessToken: string,
  req: ChaosTriggerRequest,
): Promise<{ experiment_id: string; trace_id: string }> {
  return chaosFetch(accessToken, "/experiments", {
    method: "POST",
    body: JSON.stringify(req),
  });
}
