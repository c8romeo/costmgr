/**
 * finops-optimization-client — Phase 14 FinOps Optimization TS mirror.
 *
 * Phase 14 (cj-style 119번째 wire) — CR 12-5 D-PARITY-01 Python
 * TypedDict ↔ TypeScript interface parity. Mirrors apps/api/modules/
 * finops/optimization_definition.py + rightsizing_engine.py +
 * idle_resource_detector.py + commitment_recommender.py +
 * optimization_accuracy_tracker.py TypedDict definitions.
 */

// ── OptimizationDefinition ──
export interface OptimizationDefinition {
  optimization_id: string;
  tenant_id: string;
  resource_type: "compute" | "storage" | "database" | "network" | "container";
  optimization_strategy:
    | "rightsize_down"
    | "rightsize_up"
    | "idle_terminate"
    | "commit_1y"
    | "commit_3y"
    | "storage_tier_down"
    | "composite";
  target_metric:
    | "cost_saving_pct"
    | "cost_saving_amount"
    | "utilization_target"
    | "commit_break_even_months";
  baseline_period:
    | "last_7d"
    | "last_30d"
    | "last_90d"
    | "last_180d"
    | "last_365d";
  status: "active" | "paused" | "expired";
  created_at: string;
  updated_at: string;
  trace_id: string;
  metadata: Record<string, unknown>;
}

// ── RightsizingRecommendation ──
export interface RightsizingRecommendation {
  recommendation_id: string;
  tenant_id: string;
  resource_id: string;
  resource_type: "compute" | "storage" | "database" | "network" | "container";
  current_instance_type: string;
  recommended_instance_type: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  current_cost_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  recommended_cost_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected_savings_pct: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected_savings_amount_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  confidence_score: number;
  recommendation_severity: "low" | "medium" | "high";
  model_version: string;
  generated_at: string;
  trace_id: string;
}

// ── IdleResource ──
export interface IdleResource {
  idle_resource_id: string;
  tenant_id: string;
  resource_id: string;
  resource_type: "compute" | "storage" | "database" | "network" | "container";
  idle_reason: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  idle_duration_days: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  current_cost_krw_per_month: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  potential_savings_krw_per_month: number;
  idle_severity: "low" | "medium" | "high";
  action: "review" | "downsize" | "terminate";
  detection_method: "z_score" | "threshold" | "heuristic";
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  detection_window_days: number;
  generated_at: string;
  trace_id: string;
}

// ── CommitmentRecommendation ──
export interface CommitmentRecommendation {
  recommendation_id: string;
  tenant_id: string;
  commitment_type:
    | "ec2_ri"
    | "rds_ri"
    | "ec2_sp"
    | "s3_sp"
    | "redshift_sp"
    | "dynamodb_sp";
  commitment_term: "1_year" | "3_year";
  resource_pattern: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  current_on_demand_cost_krw_per_month: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected_commit_cost_krw_per_month: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected_savings_pct: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected_savings_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  upfront_cost_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  break_even_months: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  roi_pct: number;
  recommendation_severity: "low" | "medium" | "high";
  generated_at: string;
  trace_id: string;
}

// ── OptimizationAccuracyReport ──
export interface OptimizationAccuracyReport {
  report_id: string;
  tenant_id: string;
  resource_type: "compute" | "storage" | "database" | "network" | "container";
  optimization_strategy:
    | "rightsize_down"
    | "rightsize_up"
    | "idle_terminate"
    | "commit_1y"
    | "commit_3y"
    | "storage_tier_down"
    | "composite";
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_recommendations: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  applied_recommendations: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  precision: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  recall: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  realized_savings_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected_savings_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  accuracy_score: number;
  generated_at: string;
  trace_id: string;
}

// ── Custom error class for FinOps optimization API calls ──
export class FinopsOptimizationApiError extends Error {
  constructor(
    // cj-246: same stacked-disable fix on the `FinopsOptimizationApiError`
    // ctor parameter — merging `@typescript-eslint/no-restricted-types,
    // camelcase` so both rules apply to the `http_status: number` field.
    // eslint-disable-next-line @typescript-eslint/no-restricted-types, camelcase
    public http_status: number,
    public code: string,
    // eslint-disable-next-line camelcase
    public message_ko: string,
    public details: Record<string, unknown> = {},
    // eslint-disable-next-line camelcase
    public trace_id: string = "",
  ) {
    super(message_ko);
    this.name = "FinopsOptimizationApiError";
  }
}

// ── Fetch wrappers (5 NEW) ──

export async function fetchOptimizationRecommendations(
  strategy: string,
  resourceType: string,
  baselinePeriod: string,
): Promise<RightsizingRecommendation[]> {
  const response = await fetch(
    `/api/v1/admin/finops/optimization/recommendations?strategy=${encodeURIComponent(strategy)}&resource_type=${encodeURIComponent(resourceType)}&baseline_period=${encodeURIComponent(baselinePeriod)}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsOptimizationApiError(
      response.status,
      "OPTIMIZATION_RECOMMENDATIONS_FETCH_FAILED",
      `권고 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<RightsizingRecommendation[]>;
}

export async function fetchIdleResources(
  resourceType: string,
  baselinePeriod: string,
): Promise<IdleResource[]> {
  const response = await fetch(
    `/api/v1/admin/finops/optimization/idle-resources?resource_type=${encodeURIComponent(resourceType)}&baseline_period=${encodeURIComponent(baselinePeriod)}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsOptimizationApiError(
      response.status,
      "IDLE_RESOURCES_FETCH_FAILED",
      `Idle 리소스 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<IdleResource[]>;
}

export async function fetchCommitmentRecommendations(
  baselinePeriod: string,
): Promise<CommitmentRecommendation[]> {
  const response = await fetch(
    `/api/v1/admin/finops/optimization/commitment-recommendations?baseline_period=${encodeURIComponent(baselinePeriod)}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsOptimizationApiError(
      response.status,
      "COMMITMENT_RECOMMENDATIONS_FETCH_FAILED",
      `Commitment 권고 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<CommitmentRecommendation[]>;
}

export async function fetchOptimizationAccuracy(
  resourceType: string,
  strategy: string,
): Promise<OptimizationAccuracyReport[]> {
  const response = await fetch(
    `/api/v1/admin/finops/optimization/accuracy?resource_type=${encodeURIComponent(resourceType)}&strategy=${encodeURIComponent(strategy)}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsOptimizationApiError(
      response.status,
      "OPTIMIZATION_ACCURACY_FETCH_FAILED",
      `정확도 추적 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<OptimizationAccuracyReport[]>;
}
