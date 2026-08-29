/**
 * apps/web/lib/slo/slo-types.ts —
 * Phase 10 T7 (cj-style 103번째 wire) — TypeScript TypedDict mirrors
 * for the backend Python TypedDicts in apps/api/modules/slo/.
 *
 * CR 12-5 D-PARITY-01 — Python FastAPI backend SloDefinition ↔
 * TypeScript Next.js frontend SloDefinition interface parity.
 */

export type SliType =
  | "latency"
  | "availability"
  | "throughput"
  | "error_rate"
  | "freshness";

export type SliWindow = "1h" | "6h" | "24h" | "3d" | "7d" | "30d";

export type ErrorBudgetPolicy =
  | "freeze_on_exhaust"
  | "alert_only"
  | "auto_rollback";

export type SloRegion = "seoul" | "tokyo" | "all";

export type MultiRegionAggregation =
  | "weighted_avg"
  | "min"
  | "max"
  | "any_failure";

export type SloState = "draft" | "active" | "paused" | "retired";

export interface SloDefinition {
  slo_id: string;
  tenant_id: string;
  service: string;
  sli_type: SliType;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  objective: number;
  window: SliWindow;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  burn_rate_threshold: number;
  error_budget_policy: ErrorBudgetPolicy;
  region: SloRegion;
  multi_region_aggregation: MultiRegionAggregation;
  freeze_enabled: boolean;
  auto_rollback_trigger: boolean;
  governance_required: boolean;
  state: SloState;
  created_at: string;
  updated_at: string;
}

export interface ErrorBudget {
  slo_id: string;
  tenant_id: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  budget_total_minutes: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  budget_consumed_minutes: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  budget_remaining_minutes: number;
  freeze_triggered: boolean;
  exhaustion_predicted_at: string | null;
  last_evaluated_at: string;
}

export type GovernanceReviewStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "escalated";

export interface GovernanceReview {
  review_id: string;
  slo_id: string;
  tenant_id: string;
  reviewer_id: string;
  review_status: GovernanceReviewStatus;
  governance_notes: string;
  reviewed_at: string;
}
