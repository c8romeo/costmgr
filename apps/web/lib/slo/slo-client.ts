/**
 * apps/web/lib/slo/slo-client.ts —
 * Phase 10 T7 (cj-style 103번째 wire) — SLO Engineering / Error Budget
 * Management client. Mirrors apps/web/lib/chaos/chaos-client.ts.
 *
 * TypedDict parity (CR 12-5 D-PARITY-01) — the SloDefinition +
 * ErrorBudget + GovernanceReview types here mirror the backend Python
 * TypedDicts in apps/api/modules/slo/.
 */
import type {
  SloDefinition,
  ErrorBudget,
  GovernanceReview,
} from "@/lib/slo/slo-types";

export type { SloDefinition, ErrorBudget, GovernanceReview };

export interface SloApiPage<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export class SloApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly trace_id: string;
  constructor(
    message: string,
    opts: { status: number; code: string; trace_id: string },
  ) {
    super(message);
    this.name = "SloApiError";
    this.status = opts.status;
    this.code = opts.code;
    this.trace_id = opts.trace_id;
  }
}

const API_BASE = "/api/v1/admin/slo";

async function fetchSloJson<T>(
  path: string,
  accessToken: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    let payload: { detail?: { message_ko?: string; code?: string; trace_id?: string } } = {};
    try {
      payload = await res.json();
    } catch {
      // ignore JSON parse error
    }
    throw new SloApiError(
      payload.detail?.message_ko ?? `SLO API ${res.status}`,
      {
        status: res.status,
        code: payload.detail?.code ?? "SLO_API_ERROR",
        trace_id: payload.detail?.trace_id ?? "",
      },
    );
  }
  return (await res.json()) as T;
}

export async function listSloDefinitions(
  accessToken: string,
  page = 1,
  pageSize = 20,
): Promise<SloApiPage<SloDefinition>> {
  return fetchSloJson<SloApiPage<SloDefinition>>(
    `/definitions?page=${page}&page_size=${pageSize}`,
    accessToken,
  );
}

export async function listErrorBudgets(
  accessToken: string,
): Promise<{ budgets: ErrorBudget[] }> {
  return fetchSloJson<{ budgets: ErrorBudget[] }>("/error-budgets", accessToken);
}

export async function listGovernanceReviews(
  accessToken: string,
): Promise<{ reviews: GovernanceReview[] }> {
  return fetchSloJson<{ reviews: GovernanceReview[] }>(
    "/governance/reviews",
    accessToken,
  );
}

export async function freezeErrorBudget(
  accessToken: string,
  sloId: string,
  reason: string,
): Promise<{ frozen: true; slo_id: string; reason: string }> {
  return fetchSloJson<{ frozen: true; slo_id: string; reason: string }>(
    `/error-budgets/${encodeURIComponent(sloId)}/freeze`,
    accessToken,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    },
  );
}

export async function approveGovernanceReview(
  accessToken: string,
  reviewId: string,
  notes: string,
): Promise<{ approved: true; review_id: string; notes: string }> {
  return fetchSloJson<{ approved: true; review_id: string; notes: string }>(
    `/governance/reviews/${encodeURIComponent(reviewId)}/approve`,
    accessToken,
    {
      method: "POST",
      body: JSON.stringify({ notes }),
    },
  );
}
