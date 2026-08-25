"""apps.api.modules.finops.multi_cloud.serializers — Phase 20 Multi-Cloud Cost Unified Reconciliation TypedDicts.

Phase 20 wire (cj-style 144번째) — m28_finops_multi_cloud.multi_cloud_serializers
NEW (Phase 19 wire `8db3cfc` m27_finops_pricing.pricing_serializers EXTENSION
pattern verbatim).

This module defines the canonical TypedDict schemas shared between the
backend (Python) and the frontend (TypeScript) per CR 12-5 D-PARITY-01
inversion discipline.

TypedDicts (PRD §F36.1~§F36.5 verbatim):
- MultiCloudRateCardReconciliation (18 fields) — 9-module cross-rollup +
  5-cloud-provider rate card reconciliation output.
- MultiCloudCostReconciliation (19 fields) — unified source of truth
  5-cloud-provider cost reconciliation.
- NegotiationRecommendation (16 fields) — negotiation bot output
  (3 cloud provider support: AWS EDP + Azure EA + GCP CUD).
- BlendedUnblendedDiff (14 fields) — blended vs unblended real-time
  tracker (3 cloud provider: AWS + Azure + GCP).
- MarketplaceSaaSPricingRollup (16 fields) — marketplace SaaS pricing
  integrated view (5 marketplace source).
- ScheduledMultiCloudDispatch (11 fields) — scheduled dispatch KST cron
  output (4 cron schedules).

Enums (verbatim):
- MultiCloudScopeType (4) — tenant/department/cost_center/product_line
- MultiCloudProvider (5) — AWS/Azure/GCP/Naver/KT
- MultiCloudRateCardSource (5) — negotiation/contract/rate_card_api/manual/audit
- MultiCloudCostSource (5) — billing_api/invoice_pdf/contract_estimated/manual/audit
- NegotiationStatus (3) — auto_negotiate_ready/manual_review_required/low_confidence
- NegotiationRiskLevel (3) — low/medium/high
- BlendedUnblendedTrackingStatus (4) — real_time/near_real_time/drift_detected/manual
- MarketplaceSource (5) — AWS/Azure/GCP/Naver/KT marketplace
- MarketplaceSaaSCategory (6) — crm/erp/devops/security/analytics/other
- MarketplaceUnit (5) — per_user/per_transaction/per_request/per_gb/per_hour
- MarketplacePricingModel (3) — subscription/per_use/metered
- MarketplaceIntegrationStatus (4) — active/paused/expired/manual
- MultiCloudDispatchSchedule (4) — weekly/monthly/quarterly/annual
- MultiCloudDispatchRecipientStrategy (4) — owner_only/multi_cloud_team/finance_team/custom_recipients

CR lessons applied:
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 11-4 P-015 — pure validator pattern.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 + openpyxl==3.1.2
  + pandas==2.1.4 + xlsxwriter==3.1.9 + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-47 FinOps Multi-Cloud Cost Unified Reconciliation (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from typing_extensions import TypedDict

# Model version SSOT (Phase 19 EXTENSION pattern verbatim).
MULTI_CLOUD_ENGINE_MODEL_VERSION = "1.0.0"

# Multi-cloud defaults — Phase 20 NEW (CR 11-4 P-015 verbatim SSOT).
MULTI_CLOUD_DEFAULTS: dict[str, Any] = {
    "default_scope_type": "tenant",
    "default_period_key_format": "YYYY-MM",
    "cache_ttl_hours": 24,
    # Rate card reconciliation thresholds
    "rate_card_variance_threshold_pct": 5.0,  # variance_pct > 5.0% → alert
    "rate_card_staleness_threshold_minutes": 60,  # > 60min → "rate card stale" alert
    "reconciliation_match_rate_target_pct": 95.0,
    "reconciliation_drift_count_30d_target": 5,
    "reconciliation_avg_variance_target_pct": 2.0,
    # Cost reconciliation thresholds
    "cost_variance_threshold_pct": 3.0,  # cost_variance_pct > 3.0% → alert
    "total_multi_cloud_cost_target_krw": None,  # tenant-customized baseline
    "cost_variance_total_target_pct": 1.0,
    "cost_variance_avg_target_pct": 1.5,
    "reconciliation_freshness_target_minutes": 60,
    "cost_source_coverage_target_pct": 98.0,
    # Forecast
    "cost_forecast_deviation_threshold_pct": 20.0,
    "cost_vs_benchmark_threshold_pct": 10.0,
    # Industry growth baseline EXTENSION (4 industries)
    "cost_growth_baseline_pct": {
        "manufacturing": 15.0,
        "service": 25.0,
        "manufacturing_service": 18.0,
        "manufacturing_service_other": 35.0,
    },
    "forecast_deviation_baseline_pct": {
        "manufacturing": 10.0,
        "service": 15.0,
        "manufacturing_service": 12.0,
        "manufacturing_service_other": 18.0,
    },
    # Blended/Unblended
    "blended_unblended_diff_threshold_pct": 5.0,
    "blended_unblended_drift_count_30d_target": 3,
    "blended_unblended_avg_diff_target_krw_per_hour": {
        "manufacturing": 100.0,
        "service": 50.0,
        "manufacturing_service": 80.0,
        "manufacturing_service_other": 30.0,
    },
    # Naver/KT public pricing API stability
    "naver_kt_api_uptime_target_pct": 99.0,
    "naver_kt_api_p95_target_seconds": 2.0,
    "naver_kt_data_freshness_target_hours": 24,
    "naver_kt_accuracy_target_pct": 95.0,
    "naver_kt_rate_limited_backoff_seconds": [60, 120, 240],
    # Negotiation bot guards (PRD §F36.3-5 verbatim)
    "minimum_savings_pct": 5.0,
    "minimum_savings_krw": 1_000_000,
    "max_negotiations_per_month": 3,
    "max_auto_trigger_per_day": 1,
    "negotiation_confidence_low_threshold": 60.0,
    "negotiation_confidence_high_threshold": 80.0,
    "negotiation_break_even_utilization_flexible_tier_pct": 50.0,
    "negotiation_break_even_utilization_fixed_tier_pct": 70.0,
    # Marketplace
    "marketplace_staleness_threshold_hours": 24,
    "marketplace_coverage_target_pct": 90.0,
    "marketplace_alternative_savings_target_krw_per_year": 1_000_000,
    "marketplace_alternative_recommended_threshold_pct": 10.0,
    "marketplace_alternative_manual_review_threshold_pct": 5.0,
    # Volume tiers (Naver/KT 4-tier)
    "naver_kt_volume_tiers": {
        "tier_1": {"min": 0, "max": 100, "discount_pct": 0.0},
        "tier_2": {"min": 100, "max": 500, "discount_pct": 5.0},
        "tier_3": {"min": 500, "max": 1000, "discount_pct": 10.0},
        "tier_4": {"min": 1000, "max": None, "discount_pct": None, "type": "custom_contract"},
    },
    # Retry policy
    "max_retry_count": 3,
    "retry_backoff_seconds": [1, 2, 4],
    "presigned_url_expiry_days": 7,
    "audit_first_insert": True,
    "rls_tenant_selector": True,
    "industry_agnostic": True,
    "real_time_strategy_default": "near_real_time",  # 1-hour cron refresh
    "cross_tenant_attempt_protection": True,
}


class MultiCloudScopeType(str, enum.Enum):
    """MultiCloud reconciliation scope_type options (4종)."""

    TENANT = "tenant"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PRODUCT_LINE = "product_line"


ALL_MULTI_CLOUD_SCOPE_TYPES: list[str] = [s.value for s in MultiCloudScopeType]


class MultiCloudProvider(str, enum.Enum):
    """Cloud provider options for multi-cloud cross-rollup (5종).

    Phase 20 reuse Phase 19 pricing + Phase 18 commitment verbatim
    (apps/api/modules/finops/pricing/serializers.py:102-114) — 5 cloud
    providers (AWS + Azure + GCP + Naver Cloud + KT Cloud) per AD-47 (a).
    """

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    NAVER = "naver"
    KT = "kt"


ALL_MULTI_CLOUD_PROVIDERS: list[str] = [p.value for p in MultiCloudProvider]


class MultiCloudRateCardSource(str, enum.Enum):
    """5-tier rate card source priority chain (PRD §F36.1-2 verbatim)."""

    NEGOTIATION = "negotiation"  # (1) AWS EDP / Azure EA / GCP CUD bot result
    CONTRACT = "contract"  # (2) negotiated_rate from SaaS contract PDF
    RATE_CARD_API = "rate_card_api"  # (3) provider official pricing API
    MANUAL = "manual"  # (4) tenant_admin custom rate
    AUDIT = "audit"  # (5) recovered from past audit log


ALL_MULTI_CLOUD_RATE_CARD_SOURCES: list[str] = [
    s.value for s in MultiCloudRateCardSource
]


class MultiCloudCostSource(str, enum.Enum):
    """5-tier cost source priority chain (PRD §F36.2-3 verbatim)."""

    BILLING_API = "billing_api"  # (1) AWS Cost Explorer / Azure / GCP Billing
    INVOICE_PDF = "invoice_pdf"  # (2) textract OCR of monthly invoice PDF
    CONTRACT_ESTIMATED = "contract_estimated"  # (3) Phase 18+19 TCO modeling estimated
    MANUAL = "manual"  # (4) tenant_admin custom cost
    AUDIT = "audit"  # (5) recovered from past audit log


ALL_MULTI_CLOUD_COST_SOURCES: list[str] = [s.value for s in MultiCloudCostSource]


class NegotiationStatus(str, enum.Enum):
    """Negotiation bot recommendation status (3종)."""

    AUTO_NEGOTIATE_READY = "auto_negotiate_ready"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    LOW_CONFIDENCE = "low_confidence"


ALL_NEGOTIATION_STATUSES: list[str] = [s.value for s in NegotiationStatus]


class NegotiationRiskLevel(str, enum.Enum):
    """Negotiation bot risk score level (3종)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


ALL_NEGOTIATION_RISK_LEVELS: list[str] = [l.value for l in NegotiationRiskLevel]


class NegotiationCommitmentTerm(str, enum.Enum):
    """Negotiation recommended commitment term (2종)."""

    ONE_YEAR = "1_year"
    THREE_YEAR = "3_year"


class NegotiationStrategy(str, enum.Enum):
    """Negotiation strategy (3종)."""

    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"


ALL_NEGOTIATION_STRATEGIES: list[str] = [s.value for s in NegotiationStrategy]


class BlendedUnblendedTrackingStatus(str, enum.Enum):
    """Blended/Unblended tracker status (4종)."""

    REAL_TIME = "real_time"
    NEAR_REAL_TIME = "near_real_time"
    DRIFT_DETECTED = "drift_detected"
    MANUAL = "manual"


ALL_BLENDED_UNBLENDED_TRACKING_STATUSES: list[str] = [
    s.value for s in BlendedUnblendedTrackingStatus
]


class NaverKTApiHealthStatus(str, enum.Enum):
    """Naver/KT public pricing API stability status (4종)."""

    VERIFIED_REALTIME = "verified_realtime"
    VERIFIED_NEAR_REALTIME = "verified_near_realtime"
    DRIFT_DETECTED = "drift_detected"
    API_UNAVAILABLE = "api_unavailable"


class NaverKTVolumeTier(str, enum.Enum):
    """Naver/KT 4-tier volume pricing tier (PRD §F36.4-6 verbatim)."""

    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_4 = "tier_4"


class MarketplaceSource(str, enum.Enum):
    """5 marketplace source (PRD §F36.5-1 verbatim)."""

    AWS_MARKETPLACE = "aws_marketplace"
    AZURE_MARKETPLACE = "azure_marketplace"
    GCP_MARKETPLACE = "gcp_marketplace"
    NAVER_MARKETPLACE = "naver_marketplace"
    KT_MARKETPLACE = "kt_marketplace"


ALL_MARKETPLACE_SOURCES: list[str] = [s.value for s in MarketplaceSource]


class MarketplaceSaaSCategory(str, enum.Enum):
    """SaaS category (6종)."""

    CRM = "crm"
    ERP = "erp"
    DEVOPS = "devops"
    SECURITY = "security"
    ANALYTICS = "analytics"
    OTHER = "other"


ALL_MARKETPLACE_SAAS_CATEGORIES: list[str] = [c.value for c in MarketplaceSaaSCategory]


class MarketplaceUnit(str, enum.Enum):
    """Marketplace SaaS pricing unit (5종)."""

    PER_USER = "per_user"
    PER_TRANSACTION = "per_transaction"
    PER_REQUEST = "per_request"
    PER_GB = "per_gb"
    PER_HOUR = "per_hour"


ALL_MARKETPLACE_UNITS: list[str] = [u.value for u in MarketplaceUnit]


class MarketplacePricingModel(str, enum.Enum):
    """Marketplace pricing model (3종)."""

    SUBSCRIPTION = "subscription"
    PER_USE = "per_use"
    METERED = "metered"


ALL_MARKETPLACE_PRICING_MODELS: list[str] = [m.value for m in MarketplacePricingModel]


class MarketplaceIntegrationStatus(str, enum.Enum):
    """Marketplace integration status (4종)."""

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    MANUAL = "manual"


ALL_MARKETPLACE_INTEGRATION_STATUSES: list[str] = [
    s.value for s in MarketplaceIntegrationStatus
]


class MultiCloudDispatchSchedule(str, enum.Enum):
    """ScheduledMultiCloudDispatch schedule options (4종)."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_MULTI_CLOUD_DISPATCH_SCHEDULES: list[str] = [
    d.value for d in MultiCloudDispatchSchedule
]


class MultiCloudDispatchRecipientStrategy(str, enum.Enum):
    """ScheduledMultiCloudDispatch recipient_strategy options (4종)."""

    OWNER_ONLY = "owner_only"
    MULTI_CLOUD_TEAM = "multi_cloud_team"
    FINANCE_TEAM = "finance_team"
    CUSTOM_RECIPIENTS = "custom_recipients"


ALL_MULTI_CLOUD_DISPATCH_RECIPIENT_STRATEGIES: list[str] = [
    r.value for r in MultiCloudDispatchRecipientStrategy
]


class MultiCloudKPIThresholdStatus(str, enum.Enum):
    """Multi-cloud KPI threshold status (3종)."""

    ON_TRACK = "on_track"
    WARNING = "warning"
    CRITICAL = "critical"


ALL_MULTI_CLOUD_KPI_THRESHOLD_STATUSES: list[str] = [
    s.value for s in MultiCloudKPIThresholdStatus
]


class MultiCloudRateCardReconciliation(TypedDict, total=False):
    """MultiCloudRateCardReconciliation TypedDict 18 fields (PRD §F36.1 verbatim).

    Phase 20 wire (cj-style 144번째) — 9-module cross-rollup +
    5-cloud-provider rate card reconciliation output (Phase 11 showback +
    Phase 12 anomaly + Phase 13 forecast + Phase 14 optimization +
    Phase 15 tag_governance + Phase 16 executive + Phase 17 sustainability +
    Phase 18 commitment + Phase 19 pricing). 5-tier source priority chain.

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 1-1 audit-first INSERT — `multi_cloud_rate_card_reconciled` AFTER.
    - CR 4-3/4-4 — golden_diff + tenant-scoped result_hash.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    rate_card_reconciliation_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    period_key: str  # TEXT
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str
    scope_chain: dict[str, Any]  # 9-module source attribution JSONB
    cloud_provider: str  # aws/azure/gcp/naver/kt
    service_code: str
    region: str
    reconciled_rate_krw_per_hour: float  # NUMERIC(18,6)
    variance_rate_krw_per_hour: float  # NUMERIC(18,6)
    variance_pct: float  # NUMERIC(5,2)
    source_count: int
    primary_source: str  # 5-tier source chain
    source_attribution: dict[str, Any]  # 5 cloud provider × 5 source tier JSONB
    last_negotiated_at: datetime  # nullable
    last_reconciled_at: datetime  # TIMESTAMPTZ
    computed_at: datetime
    trace_id: str


class MultiCloudCostReconciliation(TypedDict, total=False):
    """MultiCloudCostReconciliation TypedDict 19 fields (PRD §F36.2 verbatim).

    Phase 20 wire (cj-style 144번째) — unified source of truth
    5-cloud-provider cost reconciliation (AWS Cost Explorer + Azure
    Cost Management + GCP Billing + Naver Cloud Billing + KT Cloud
    Billing). 5-tier cost source priority chain.
    """

    cost_reconciliation_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    period_key: str  # TEXT
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str
    scope_chain: dict[str, Any]  # 9-module source attribution JSONB
    cloud_provider: str  # aws/azure/gcp/naver/kt
    service_code: str
    region: str
    blended_cost_krw: float  # NUMERIC(20,2)
    unblended_cost_krw: float  # NUMERIC(20,2)
    cost_variance_krw: float  # NUMERIC(20,2)
    cost_variance_pct: float  # NUMERIC(5,2)
    cost_source_count: int
    primary_cost_source: str  # 5-tier source chain
    cost_growth_pct: float  # vs previous period
    cost_forecast_krw: float  # next period forecast
    last_reconciled_at: datetime
    computed_at: datetime
    trace_id: str


class NegotiationRecommendation(TypedDict, total=False):
    """NegotiationRecommendation TypedDict 16 fields (PRD §F36.3 verbatim).

    Phase 20 wire (cj-style 144번째) — negotiation bot output (3 cloud
    provider support: AWS EDP auto-negotiation + Azure EA consumption
    commit reconciliation + GCP CUD flexible/fixed tier break-even
    optimization).

    CR lessons applied:
    - CR 1-1 audit-first INSERT — `negotiation_bot_triggered` AFTER trigger.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    negotiation_recommendation_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    cloud_provider: str  # aws/azure/gcp (3 cloud provider)
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str
    current_rate_krw_per_hour: float  # NUMERIC(18,6)
    recommended_rate_krw_per_hour: float  # NUMERIC(18,6)
    recommended_commitment_term: str  # 1_year/3_year
    estimated_savings_pct: float  # NUMERIC(5,2)
    estimated_savings_krw_per_year: float  # NUMERIC(20,2)
    payback_period_months: int
    break_even_utilization_pct: float  # NUMERIC(5,2)
    confidence_score: float  # NUMERIC(5,2)
    risk_score: str  # low/medium/high
    negotiation_strategy: str  # aggressive/moderate/conservative
    auto_negotiate_enabled: bool
    recommendation_status: str  # auto_negotiate_ready/manual_review_required/low_confidence
    idempotency_key: str
    computed_at: datetime
    trace_id: str


class BlendedUnblendedDiff(TypedDict, total=False):
    """BlendedUnblendedDiff TypedDict 14 fields (PRD §F36.4 verbatim).

    Phase 20 wire (cj-style 144번째) — blended vs unblended real-time
    tracker (3 cloud provider support: AWS + Azure + GCP). Naver/KT public
    pricing API stability 검증 P2 entry.
    """

    diff_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    period_key: str  # TEXT
    cloud_provider: str  # aws/azure/gcp (3 cloud provider)
    scope_type: str
    scope_id: str
    blended_rate_krw_per_hour: float  # NUMERIC(18,6)
    unblended_rate_krw_per_hour: float  # NUMERIC(18,6)
    rate_diff_krw_per_hour: float  # NUMERIC(18,6)
    rate_diff_pct: float  # NUMERIC(5,2)
    service_count: int
    resource_count: int
    tracking_status: str  # real_time/near_real_time/drift_detected/manual
    last_tracked_at: datetime
    computed_at: datetime
    trace_id: str


class MarketplaceSaaSPricingRollup(TypedDict, total=False):
    """MarketplaceSaaSPricingRollup TypedDict 16 fields (PRD §F36.5 verbatim).

    Phase 20 wire (cj-style 144번째) — marketplace SaaS pricing integrated
    view (5 marketplace source: AWS + Azure + GCP + Naver + KT Marketplace).
    5 marketplace adapter pattern + unified pricing view + freshness tracking.
    """

    marketplace_pricing_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    period_key: str  # TEXT
    marketplace_source: str  # 5 marketplace source enum
    vendor_name: str
    product_name: str
    sku: str
    list_price_krw_per_unit: float  # NUMERIC(18,6)
    negotiated_price_krw_per_unit: float  # NUMERIC(18,6)
    effective_price_krw_per_unit: float  # NUMERIC(18,6)
    unit: str  # 5 unit enum
    saas_category: str  # 6 SaaS category
    pricing_model: str  # 3 pricing model
    integration_status: str  # 4 status
    last_synced_at: datetime
    trace_id: str


class ScheduledMultiCloudDispatch(TypedDict, total=False):
    """ScheduledMultiCloudDispatch TypedDict 11 fields (PRD §F36.6 verbatim).

    Phase 20 wire (cj-style 144번째) — scheduled dispatch KST cron output.
    4 cron schedules (weekly Mon 09:00 + monthly 1st-day 09:00 +
    quarterly 1st-day 09:00 + annual Jan-1 09:00 KST) + recipient
    resolver (Slack + Email + MS Teams + S3 archive).
    """

    dispatch_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    dispatch_schedule: str  # weekly/monthly/quarterly/annual
    cron_expression: str  # TEXT e.g. "0 9 * * 1"
    recipient_strategy: str
    recipient_list: dict[str, Any]
    dispatch_target_modules: list[str]
    idempotency_key: str
    last_status: str
    next_run_at: datetime
    last_run_at: datetime  # nullable
    trace_id: str


# 9 NEW multi-cloud cost KPI names SSOT (PRD §F36.2-8 + §F36.5-6 verbatim).
ALL_MULTI_CLOUD_COST_KPI_NAMES: list[str] = [
    "total_multi_cloud_cost_krw",
    "cost_variance_total_krw",
    "cost_variance_avg_pct",
    "reconciliation_freshness_minutes",
    "cost_source_coverage_pct",
    "cost_forecast_krw",
    "cost_growth_pct",
    "cost_vs_benchmark_pct",
    "marketplace_alternative_savings_krw_per_year",
]

# 4 NEW multi-cloud rate card KPI names (PRD §F36.1-9).
ALL_MULTI_CLOUD_RATE_CARD_KPI_NAMES: list[str] = [
    "reconciliation_match_rate_pct",
    "reconciliation_drift_count_30d",
    "reconciliation_avg_variance_pct",
    "reconciliation_freshness_minutes_rc",
]

# 3 NEW blended/unblended KPI names (PRD §F36.4-3).
ALL_BLENDED_UNBLENDED_KPI_NAMES: list[str] = [
    "blended_unblended_diff_pct",
    "blended_unblended_drift_count_30d",
    "blended_unblended_avg_diff_krw_per_hour",
]


__all__ = [
    "MULTI_CLOUD_ENGINE_MODEL_VERSION",
    "MULTI_CLOUD_DEFAULTS",
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
    "MultiCloudRateCardReconciliation",
    "MultiCloudCostReconciliation",
    "NegotiationRecommendation",
    "BlendedUnblendedDiff",
    "MarketplaceSaaSPricingRollup",
    "ScheduledMultiCloudDispatch",
    "ALL_MULTI_CLOUD_COST_KPI_NAMES",
    "ALL_MULTI_CLOUD_RATE_CARD_KPI_NAMES",
    "ALL_BLENDED_UNBLENDED_KPI_NAMES",
]
