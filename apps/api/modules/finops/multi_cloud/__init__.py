"""apps.api.modules.finops.multi_cloud — Phase 20 FinOps Multi-Cloud Cost Unified Reconciliation module.

Phase 20 wire (cj-style 144번째) — FinOps Multi-Cloud Cost Unified
Reconciliation territory (PRD §F36.1~§F36.5 verbatim + AD-47 (a)~(g) 7
sub-decisions).

This package provides:
- `serializers` — m28_finops_multi_cloud.multi_cloud_serializers NEW
  (Phase 19 wire `8db3cfc` m27_finops_pricing.pricing_serializers EXTENSION
  pattern verbatim).
- `rate_card_reconciliation_aggregator` — 9-module cross-rollup +
  5-cloud-provider rate card reconciliation (Phase 11 showback + Phase 12
  anomaly + Phase 13 forecast + Phase 14 optimization + Phase 15
  tag_governance + Phase 16 executive + Phase 17 sustainability + Phase 18
  commitment + Phase 19 pricing) + 5-tier source priority chain (negotiation
  + contract + rate_card_api + manual + audit) → MultiCloudRateCardReconciliation
  TypedDict 18 fields.
- `cost_reconciliation_aggregator` — unified source of truth 5-cloud-
  provider cost reconciliation (AWS Cost Explorer + Azure Cost Management
  + GCP Billing + Naver Cloud Billing + KT Cloud Billing) + 5-tier cost
  source priority chain → MultiCloudCostReconciliation TypedDict 19 fields.
- `negotiation_bot` — 3-cloud-provider negotiation bot (AWS EDP auto +
  Azure EA consumption commit + GCP CUD flexible/fixed) →
  NegotiationRecommendation TypedDict 16 fields.
- `blended_unblended_tracker` — 3-cloud-provider blended/unblended real-
  time tracker (AWS + Azure + GCP) + Naver/KT public pricing API stability
  검증 → BlendedUnblendedDiff TypedDict 14 fields.
- `marketplace_saas_pricing_integrator` — 5-marketplace adapter
  (AWS + Azure + GCP + Naver + KT Marketplace) + unified SaaS pricing
  view + freshness tracking → MarketplaceSaaSPricingRollup TypedDict
  16 fields.

CR lessons applied (18종):
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW actions via emit_audit_typed.
- CR 4-3/4-4 — MultiCloudRateCardReconciliation golden_diff + tenant-scoped
  result_hash.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — Client-only dashboard delegation.
- CR 9-6 commit message discipline.
- CR 11-3 honest-DEFER — D-FINOPS-9 honestly DEFER 보존.
- CR 11-4 D-001~D-005 + P-015 — pure validator + SSOT.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- A19 cohesion pattern 9 surface EXTENSION PASS.
- A36 SDR 검증 4-step 자동 적용.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 + openpyxl==3.1.2
  + pandas==2.1.4 + xlsxwriter==3.1.9 + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-47 FinOps Multi-Cloud Cost Unified Reconciliation 신규 (a)~(g) 7
  sub-decisions.
- NFR4 PII minimization PRESERVED.
"""
from __future__ import annotations

from apps.api.modules.finops.multi_cloud.serializers import (
    ALL_BLENDED_UNBLENDED_KPI_NAMES,
    ALL_BLENDED_UNBLENDED_TRACKING_STATUSES,
    ALL_MARKETPLACE_INTEGRATION_STATUSES,
    ALL_MARKETPLACE_PRICING_MODELS,
    ALL_MARKETPLACE_SAAS_CATEGORIES,
    ALL_MARKETPLACE_SOURCES,
    ALL_MARKETPLACE_UNITS,
    ALL_MULTI_CLOUD_COST_KPI_NAMES,
    ALL_MULTI_CLOUD_COST_SOURCES,
    ALL_MULTI_CLOUD_DISPATCH_RECIPIENT_STRATEGIES,
    ALL_MULTI_CLOUD_DISPATCH_SCHEDULES,
    ALL_MULTI_CLOUD_KPI_THRESHOLD_STATUSES,
    ALL_MULTI_CLOUD_PROVIDERS,
    ALL_MULTI_CLOUD_RATE_CARD_KPI_NAMES,
    ALL_MULTI_CLOUD_RATE_CARD_SOURCES,
    ALL_MULTI_CLOUD_SCOPE_TYPES,
    ALL_NEGOTIATION_COMMITMENT_TERMS,
    ALL_NEGOTIATION_RISK_LEVELS,
    ALL_NEGOTIATION_STATUSES,
    ALL_NEGOTIATION_STRATEGIES,
    MULTI_CLOUD_DEFAULTS,
    MULTI_CLOUD_ENGINE_MODEL_VERSION,
    BlendedUnblendedDiff,
    BlendedUnblendedTrackingStatus,
    MarketplaceIntegrationStatus,
    MarketplaceSaaSPricingRollup,
    MarketplaceSaaSCategory,
    MarketplacePricingModel,
    MarketplaceSource,
    MarketplaceUnit,
    MultiCloudCostReconciliation,
    MultiCloudCostSource,
    MultiCloudDispatchRecipientStrategy,
    MultiCloudDispatchSchedule,
    MultiCloudKPIThresholdStatus,
    MultiCloudProvider,
    MultiCloudRateCardReconciliation,
    MultiCloudRateCardSource,
    MultiCloudScopeType,
    NaverKTApiHealthStatus,
    NaverKTVolumeTier,
    NegotiationCommitmentTerm,
    NegotiationRecommendation,
    NegotiationRiskLevel,
    NegotiationStatus,
    NegotiationStrategy,
    ScheduledMultiCloudDispatch,
)
# Phase 20.5 wire (cj-style 147번째) — Re-export aggregator functions from
# multi_cloud submodules. Phase 20 wire `52dad7f` defined these functions
# but `multi_cloud/__init__.py` did NOT re-export them, breaking the
# `from apps.api.modules.finops.multi_cloud import integrate_marketplace_*`
# call sites in `apps/api/modules/finops/__init__.py` and elsewhere.
from apps.api.modules.finops.multi_cloud.rate_card_reconciliation_aggregator import (
    reconcile_multi_cloud_rate_cards,
    validate_multi_cloud_rate_card_reconciliation,
)
from apps.api.modules.finops.multi_cloud.cost_reconciliation_aggregator import (
    reconcile_multi_cloud_costs,
    validate_multi_cloud_cost_reconciliation,
)
from apps.api.modules.finops.multi_cloud.negotiation_bot import (
    run_negotiation_bot,
    validate_negotiation_recommendation,
)
from apps.api.modules.finops.multi_cloud.blended_unblended_tracker import (
    monitor_naver_kt_api_health,
    track_blended_unblended_diff,
    validate_blended_unblended_diff,
    validate_naver_kt_api_data_accuracy,
)
from apps.api.modules.finops.multi_cloud.marketplace_saas_pricing_integrator import (
    integrate_marketplace_saas_pricing,
    validate_marketplace_saas_pricing_rollup,
)

__all__ = [
    "MULTI_CLOUD_ENGINE_MODEL_VERSION",
    "MULTI_CLOUD_DEFAULTS",
    "MultiCloudRateCardReconciliation",
    "MultiCloudCostReconciliation",
    "NegotiationRecommendation",
    "BlendedUnblendedDiff",
    "MarketplaceSaaSPricingRollup",
    "ScheduledMultiCloudDispatch",
    "MultiCloudScopeType",
    "ALL_MULTI_CLOUD_SCOPE_TYPES",
    "MultiCloudProvider",
    "ALL_MULTI_CLOUD_PROVIDERS",
    "MultiCloudRateCardSource",
    "ALL_MULTI_CLOUD_RATE_CARD_SOURCES",
    "MultiCloudCostSource",
    "ALL_MULTI_CLOUD_COST_SOURCES",
    "NegotiationStatus",
    "ALL_NEGOTIATION_STATUSES",
    "NegotiationRiskLevel",
    "ALL_NEGOTIATION_RISK_LEVELS",
    "NegotiationCommitmentTerm",
    "NegotiationStrategy",
    "ALL_NEGOTIATION_COMMITMENT_TERMS",
    "ALL_NEGOTIATION_STRATEGIES",
    "BlendedUnblendedTrackingStatus",
    "ALL_BLENDED_UNBLENDED_TRACKING_STATUSES",
    "NaverKTApiHealthStatus",
    "NaverKTVolumeTier",
    "MarketplaceSource",
    "ALL_MARKETPLACE_SOURCES",
    "MarketplaceSaaSCategory",
    "ALL_MARKETPLACE_SAAS_CATEGORIES",
    "MarketplaceUnit",
    "ALL_MARKETPLACE_UNITS",
    "MarketplacePricingModel",
    "ALL_MARKETPLACE_PRICING_MODELS",
    "MarketplaceIntegrationStatus",
    "ALL_MARKETPLACE_INTEGRATION_STATUSES",
    "MultiCloudDispatchSchedule",
    "ALL_MULTI_CLOUD_DISPATCH_SCHEDULES",
    "MultiCloudDispatchRecipientStrategy",
    "ALL_MULTI_CLOUD_DISPATCH_RECIPIENT_STRATEGIES",
    "MultiCloudKPIThresholdStatus",
    "ALL_MULTI_CLOUD_KPI_THRESHOLD_STATUSES",
    "ALL_MULTI_CLOUD_COST_KPI_NAMES",
    "ALL_MULTI_CLOUD_RATE_CARD_KPI_NAMES",
    "ALL_BLENDED_UNBLENDED_KPI_NAMES",
    # Phase 20.5 wire (cj-style 147번째) — aggregator function re-exports.
    "reconcile_multi_cloud_rate_cards",
    "validate_multi_cloud_rate_card_reconciliation",
    "reconcile_multi_cloud_costs",
    "validate_multi_cloud_cost_reconciliation",
    "run_negotiation_bot",
    "validate_negotiation_recommendation",
    "monitor_naver_kt_api_health",
    "track_blended_unblended_diff",
    "validate_blended_unblended_diff",
    "validate_naver_kt_api_data_accuracy",
    "integrate_marketplace_saas_pricing",
    "validate_marketplace_saas_pricing_rollup",
]
