/**
 * Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
 * Reconciliation Client SDK.
 *
 * Mirrors Python `apps/api/modules/finops/multi_cloud/*` aggregator
 * functions via REST calls to `/api/v1/admin/finops/multi-cloud/*`.
 *
 * CR 12-5 D-PARITY-01 — TypeScript types match Python TypedDict
 * via `lib/finops/multi-cloud-types.ts` verbatim.
 * AD-14 stack pin — fetch API + AbortSignal + idempotency-key header.
 */

import type {
  MultiCloudRateCardReconciliation,
  MultiCloudCostReconciliation,
  NegotiationRecommendation,
  BlendedUnblendedDiff,
  MarketplaceSaaSPricingRollup,
  ScheduledMultiCloudDispatch,
  MultiCloudScopeType,
  MultiCloudProvider,
} from "./multi-cloud-types";

const MULTI_CLOUD_API_PREFIX = "/api/v1/admin/finops/multi-cloud";

async function fetchTyped<T>(
  url: string,
  init: RequestInit = {},
  traceId: string = crypto.randomUUID(),
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Trace-Id", traceId);
  const response = await fetch(url, { ...init, headers });
  if (!response.ok) {
    const errPayload = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(
      errPayload.detail ?? `HTTP ${response.status} on ${url}`,
    );
  }
  return (await response.json()) as T;
}

export interface AggregateRateCardRequest {
  tenant_id: string;
  scope_type: MultiCloudScopeType;
  scope_id: string;
  period_key: string;
  dry_run?: boolean;
}

export interface AggregateCostRequest {
  tenant_id: string;
  scope_type: MultiCloudScopeType;
  scope_id: string;
  period_key: string;
  cloud_provider: MultiCloudProvider;
  cost_sources: Record<string, number | null>;
  dry_run?: boolean;
}

export interface NegotiationRequest {
  tenant_id: string;
  cloud_provider: MultiCloudProvider;
  commitment_term: "1_year" | "3_year" | "5_year";
}

export interface TrackBlendedUnblendedRequest {
  tenant_id: string;
  scope_type: MultiCloudScopeType;
  scope_id: string;
  period_key: string;
  cloud_provider: MultiCloudProvider;
}

export interface IntegrateMarketplaceRequest {
  tenant_id: string;
  vendor_name: string;
  product_name: string;
  saas_category: string;
  period_key: string;
}

export interface DispatchMultiCloudRequest {
  tenant_id: string;
  dispatch_schedule: "weekly" | "monthly" | "quarterly" | "annual";
  recipient_strategy: string;
  cron_expression?: string;
  dry_run?: boolean;
}

export async function reconcileRateCards(
  req: AggregateRateCardRequest,
  traceId?: string,
): Promise<MultiCloudRateCardReconciliation> {
  return fetchTyped<MultiCloudRateCardReconciliation>(
    `${MULTI_CLOUD_API_PREFIX}/rate-card/reconcile`,
    { method: "POST", body: JSON.stringify(req) },
    traceId,
  );
}

export async function reconcileCosts(
  req: AggregateCostRequest,
  traceId?: string,
): Promise<MultiCloudCostReconciliation> {
  return fetchTyped<MultiCloudCostReconciliation>(
    `${MULTI_CLOUD_API_PREFIX}/cost/reconcile`,
    { method: "POST", body: JSON.stringify(req) },
    traceId,
  );
}

export async function runNegotiationBot(
  req: NegotiationRequest,
  traceId?: string,
): Promise<NegotiationRecommendation> {
  return fetchTyped<NegotiationRecommendation>(
    `${MULTI_CLOUD_API_PREFIX}/negotiation/run`,
    { method: "POST", body: JSON.stringify(req) },
    traceId,
  );
}

export async function trackBlendedUnblended(
  req: TrackBlendedUnblendedRequest,
  traceId?: string,
): Promise<BlendedUnblendedDiff> {
  return fetchTyped<BlendedUnblendedDiff>(
    `${MULTI_CLOUD_API_PREFIX}/blended-unblended/track`,
    { method: "POST", body: JSON.stringify(req) },
    traceId,
  );
}

export async function integrateMarketplace(
  req: IntegrateMarketplaceRequest,
  traceId?: string,
): Promise<MarketplaceSaaSPricingRollup> {
  return fetchTyped<MarketplaceSaaSPricingRollup>(
    `${MULTI_CLOUD_API_PREFIX}/marketplace/integrate`,
    { method: "POST", body: JSON.stringify(req) },
    traceId,
  );
}

export async function dispatchMultiCloudReport(
  req: DispatchMultiCloudRequest,
  traceId?: string,
): Promise<ScheduledMultiCloudDispatch> {
  return fetchTyped<ScheduledMultiCloudDispatch>(
    `${MULTI_CLOUD_API_PREFIX}/dispatch`,
    { method: "POST", body: JSON.stringify(req) },
    traceId,
  );
}
