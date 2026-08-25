/**
 * Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
 * Reconciliation TypeScript interfaces.
 *
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/multi-cloud-types.ts`.
 * Mirrors `apps/api/modules/finops/multi_cloud/serializers.py` verbatim.
 */

export type MultiCloudProvider =
  | "aws"
  | "azure"
  | "gcp"
  | "naver"
  | "kt";

export type MultiCloudScopeType =
  | "tenant"
  | "department"
  | "cost_center"
  | "product_line";

export type MultiCloudRateCardSource =
  | "negotiation"
  | "contract"
  | "rate_card_api"
  | "manual"
  | "audit";

export type MultiCloudCostSource =
  | "billing_api"
  | "invoice_pdf"
  | "contract_estimated"
  | "manual"
  | "audit";

export type NegotiationStatus =
  | "auto_negotiate_ready"
  | "manual_review_required"
  | "low_confidence";

export type NegotiationRiskLevel = "low" | "medium" | "high";

export type NegotiationCommitmentTerm = "1_year" | "3_year" | "5_year";

export type NegotiationStrategy =
  | "aggressive"
  | "moderate"
  | "conservative";

export type BlendedUnblendedTrackingStatus =
  | "real_time"
  | "near_real_time"
  | "drift_detected"
  | "api_unavailable";

export type MarketplaceSource =
  | "aws_marketplace"
  | "azure_marketplace"
  | "gcp_marketplace"
  | "naver_marketplace"
  | "kt_marketplace";

export type MarketplaceSaaSCategory =
  | "analytics"
  | "security"
  | "devops"
  | "productivity"
  | "ai_ml"
  | "other";

export type MarketplaceUnit =
  | "per_user"
  | "per_request"
  | "per_gb"
  | "per_transaction"
  | "per_hour";

export type MarketplacePricingModel =
  | "subscription"
  | "per_use"
  | "tiered";

export type MarketplaceIntegrationStatus =
  | "active"
  | "pending"
  | "failed"
  | "disabled";

export interface MultiCloudRateCardReconciliation {
  rate_card_reconciliation_id: string;
  tenant_id: string;
  scope_type: MultiCloudScopeType;
  scope_id: string;
  period_key: string;
  effective_rate_krw_per_hour: number;
  rate_card_variance_krw_per_hour: number;
  rate_card_variance_pct: number;
  rate_card_source_count: number;
  primary_rate_card_source: MultiCloudRateCardSource;
  cloud_provider_breakdown: Record<MultiCloudProvider, number>;
  rate_card_source_breakdown: Record<MultiCloudRateCardSource, number>;
  negotiation_recommendation_count: number;
  rate_card_savings_krw_per_year: number;
  cache_key: string;
  computed_at: string;
  trace_id: string;
}

export interface MultiCloudCostReconciliation {
  cost_reconciliation_id: string;
  tenant_id: string;
  period_key: string;
  scope_type: MultiCloudScopeType;
  scope_id: string;
  cloud_provider: MultiCloudProvider;
  service_code: string;
  region: string;
  blended_cost_krw: number;
  unblended_cost_krw: number;
  cost_variance_krw: number;
  cost_variance_pct: number;
  cost_source_count: number;
  primary_cost_source: MultiCloudCostSource;
  cost_growth_pct: number;
  cost_forecast_krw: number;
  scope_chain: Record<string, unknown>;
  last_reconciled_at: string;
  computed_at: string;
  trace_id: string;
}

export interface NegotiationRecommendation {
  negotiation_id: string;
  tenant_id: string;
  cloud_provider: MultiCloudProvider;
  commitment_term: NegotiationCommitmentTerm;
  strategy: NegotiationStrategy;
  discount_pct_target: number;
  savings_krw_per_year: number;
  savings_pct: number;
  confidence_score: number;
  risk_score: number;
  auto_trigger_eligible: boolean;
  recommendation_status: NegotiationStatus;
  guard_check_passed: boolean;
  expires_at?: string | null;
  triggered_at?: string | null;
  computed_at: string;
  trace_id: string;
}

export interface BlendedUnblendedDiff {
  diff_id: string;
  tenant_id: string;
  period_key: string;
  cloud_provider: MultiCloudProvider;
  scope_type: MultiCloudScopeType;
  scope_id: string;
  blended_rate_krw_per_hour: number;
  unblended_rate_krw_per_hour: number;
  rate_diff_krw_per_hour: number;
  rate_diff_pct: number;
  service_count: number;
  resource_count: number;
  tracking_status: BlendedUnblendedTrackingStatus;
  last_tracked_at: string;
  computed_at: string;
  trace_id: string;
}

export interface MarketplaceSaaSPricingRollup {
  marketplace_pricing_id: string;
  tenant_id: string;
  period_key: string;
  marketplace_source: MarketplaceSource;
  vendor_name: string;
  product_name: string;
  sku: string;
  list_price_krw_per_unit: number;
  negotiated_price_krw_per_unit: number;
  effective_price_krw_per_unit: number;
  unit: MarketplaceUnit;
  saas_category: MarketplaceSaaSCategory;
  pricing_model: MarketplacePricingModel;
  integration_status: MarketplaceIntegrationStatus;
  last_synced_at: string;
  computed_at: string;
  trace_id: string;
}

export interface ScheduledMultiCloudDispatch {
  dispatch_id: string;
  tenant_id: string;
  dispatch_schedule: "weekly" | "monthly" | "quarterly" | "annual";
  cron_expression: string;
  recipient_strategy:
    | "owner_only"
    | "finops_team"
    | "exec_team"
    | "custom_recipients";
  report_id?: string | null;
  status: "scheduled" | "running" | "completed" | "failed" | "cancelled";
  scheduled_at: string;
  trace_id: string;
}
