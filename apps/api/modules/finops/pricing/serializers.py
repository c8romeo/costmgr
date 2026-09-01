"""apps.api.modules.finops.pricing.serializers — FinOps Pricing, Rate Card & TCO Modeling TypedDicts.

Phase 19 wire (cj-style 139번째) — m27_finops_pricing.pricing_serializers
NEW (Phase 18 wire `67059cf` m26_finops_commitment.commitment_serializers
EXTENSION pattern verbatim).

This module defines the canonical TypedDict schemas shared between the
backend (Python) and the frontend (TypeScript) per CR 12-5 D-PARITY-01
inversion discipline.

TypedDicts:
- RateCardInventory (18 fields) — 8-module cross-rollup + 5-cloud-provider
  rate card aggregator output (Phase 11 showback + Phase 12 anomaly +
  Phase 13 forecast + Phase 14 optimization + Phase 15 tag_governance +
  Phase 16 executive + Phase 17 sustainability + Phase 18 commitment).
- TCOKPIBundle (10 fields) — TCO modeling selector output (8 NEW KPI
  calculations + scope_chain + break_even_months).
- PricingReport (14 fields) — pricing report generator output
  (PDF + CSV + Excel + 3 cadence + 5-framework support).
- ScheduledPricingDispatch (11 fields) — scheduled dispatch KST cron output
  (4 cron schedules + recipient resolver Slack+Email+MS Teams+S3).

Enums (verbatim):
- PricingScopeType (4) — tenant/department/cost_center/product_line
- CloudProvider (5) — AWS/Azure/GCP/Naver/KT (reused from Phase 18)
- PricingModel (6) — on_demand/1y_ri/3y_ri/1y_sp/3y_sp/savings_plan
- PricingUnitMetric (4) — cost_per_user/cost_per_transaction/
  cost_per_request/cost_per_hour
- PricingCadence (3) — monthly/quarterly/annual
- PricingExportFormat (3) — pdf/csv/excel
- PricingDispatchSchedule (4) — weekly/monthly/quarterly/annual
- PricingRecipientStrategy (4) — owner_only/pricing_team/finance_team/custom_recipients
- PricingFramework (5) — finops_foundation/aws_pricing_models/
  azure_pricing_calculator/gcp_pricing_calculator/korea_procurement
- PricingKPIThresholdStatus (3) — on_track/warning/critical

CR lessons applied:
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 11-4 P-015 — pure validator pattern.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 + openpyxl==3.1.2
  + pandas==2.1.4 + xlsxwriter==3.1.9 + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-46 FinOps Pricing, Rate Card & TCO Modeling (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from typing_extensions import TypedDict

# Model version SSOT (Phase 18 EXTENSION pattern verbatim).
PRICING_ENGINE_MODEL_VERSION = "1.0.0"

# Pricing defaults — Phase 19 NEW (CR 11-4 P-015 verbatim SSOT).
PRICING_DEFAULTS: dict[str, Any] = {
    "default_scope_type": "tenant",
    "default_period_key_format": "YYYY-MM",
    "cache_ttl_hours": 24,
    "delta_threshold_pct": 5.0,
    "deviation_threshold_pct": 10.0,
    "blended_rate_target_krw_per_hour": 1000.0,  # target blended rate (KRW/hour)
    "effective_discount_target_pct": 30.0,  # target effective discount %
    "break_even_threshold_months": 12.0,  # break_even_months cutoff for 1y commitment
    "unit_economics_score_threshold": 50.0,  # unit_economics_score cutoff for actionability
    "unit_economics_score_industry_baselines": {
        # 4 industries baseline unit_economics_score — PRD §F35.2 verbatim.
        "manufacturing": 1.2,
        "service": 0.8,
        "manufacturing_service": 1.0,
        "manufacturing_service_other": 1.1,
    },
    "on_demand_multiplier_1y_ri": 0.60,  # 1-year RI = 40% discount → multiplier 0.60
    "on_demand_multiplier_3y_ri": 0.40,  # 3-year RI = 60% discount → multiplier 0.40
    "on_demand_multiplier_1y_sp": 0.65,  # 1-year SP = 35% discount → multiplier 0.65
    "on_demand_multiplier_3y_sp": 0.45,  # 3-year SP = 55% discount → multiplier 0.45
    "on_demand_multiplier_savings_plan": 0.70,  # flexible savings plan = 30% discount
    "max_retry_count": 3,
    "retry_backoff_minutes": [1, 5, 30],
    "presigned_url_expiry_days": 7,
    "audit_first_insert": True,
    "rls_tenant_selector": True,
    "industry_agnostic": True,
}


class PricingScopeType(str, enum.Enum):
    """RateCardInventory + PricingReport scope_type options (4종)."""

    TENANT = "tenant"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PRODUCT_LINE = "product_line"


ALL_PRICING_SCOPE_TYPES: list[str] = [s.value for s in PricingScopeType]


class CloudProvider(str, enum.Enum):
    """Cloud provider options for pricing cross-rollup (5종).

    Phase 19 reuse from Phase 18 commitment module verbatim
    (apps/api/modules/finops/commitment/serializers.py:77-91) — 5 cloud
    providers (AWS + Azure + GCP + Naver Cloud + KT Cloud) per AD-46 (a).
    """

    AWS = "aws"  # Amazon Web Services (EC2 RI/SP, RDS RI, Redshift RI/SP, DynamoDB SP)
    AZURE = "azure"  # Microsoft Azure (Reservations + Savings Plans)
    GCP = "gcp"  # Google Cloud Platform (Committed Use Discounts + flexible CUD)
    NAVER = "naver"  # Naver Cloud (volume tier pricing)
    KT = "kt"  # KT Cloud (volume tier pricing)


ALL_PRICING_CLOUD_PROVIDERS: list[str] = [p.value for p in CloudProvider]


class PricingModel(str, enum.Enum):
    """Pricing model options (6종).

    Phase 19 NEW enum — 6 pricing models per AD-46 (a) verbatim:
    - on_demand — pay-as-you-go (baseline)
    - 1y_ri — 1-year reserved instance (40% discount)
    - 3y_ri — 3-year reserved instance (60% discount)
    - 1y_sp — 1-year savings plan (35% discount)
    - 3y_sp — 3-year savings plan (55% discount)
    - savings_plan — flexible savings plan (30% discount)
    """

    ON_DEMAND = "on_demand"
    ONE_YEAR_RI = "1y_ri"
    THREE_YEAR_RI = "3y_ri"
    ONE_YEAR_SP = "1y_sp"
    THREE_YEAR_SP = "3y_sp"
    SAVINGS_PLAN = "savings_plan"


ALL_PRICING_MODELS: list[str] = [m.value for m in PricingModel]


class PricingUnitMetric(str, enum.Enum):
    """Unit economics metric options (4종).

    Phase 19 NEW enum — 4 unit metrics per AD-46 (a) verbatim:
    - cost_per_user — cost per active user
    - cost_per_transaction — cost per business transaction
    - cost_per_request — cost per API/HTTP request
    - cost_per_hour — cost per compute hour
    """

    COST_PER_USER = "cost_per_user"
    COST_PER_TRANSACTION = "cost_per_transaction"
    COST_PER_REQUEST = "cost_per_request"
    COST_PER_HOUR = "cost_per_hour"


ALL_PRICING_UNIT_METRICS: list[str] = [m.value for m in PricingUnitMetric]


class PricingCadence(str, enum.Enum):
    """PricingReport cadence options (3종)."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_PRICING_CADENCES: list[str] = [c.value for c in PricingCadence]


class PricingExportFormat(str, enum.Enum):
    """PricingReport export_format options (3종)."""

    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


ALL_PRICING_EXPORT_FORMATS: list[str] = [e.value for e in PricingExportFormat]


class PricingDispatchSchedule(str, enum.Enum):
    """ScheduledPricingDispatch schedule options (4종)."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_PRICING_DISPATCH_SCHEDULES: list[str] = [d.value for d in PricingDispatchSchedule]


class PricingRecipientStrategy(str, enum.Enum):
    """ScheduledPricingDispatch recipient_strategy options (4종)."""

    OWNER_ONLY = "owner_only"
    PRICING_TEAM = "pricing_team"
    FINANCE_TEAM = "finance_team"
    CUSTOM_RECIPIENTS = "custom_recipients"


ALL_PRICING_RECIPIENT_STRATEGIES: list[str] = [r.value for r in PricingRecipientStrategy]


class PricingFramework(str, enum.Enum):
    """Pricing reporting framework options (5종).

    Phase 19 NEW enum — 5 frameworks per AD-46 (a) verbatim:
    - finops_foundation — FinOps Foundation Pricing & TCO Modeling framework
    - aws_pricing_models — AWS Pricing Models (EDP) framework
    - azure_pricing_calculator — Azure Pricing Calculator (EA) framework
    - gcp_pricing_calculator — GCP Pricing Calculator (CUD) framework
    - korea_procurement — 한국 공공 조달 가격 가이드라인
    """

    FINOPS_FOUNDATION = "finops_foundation"
    AWS_PRICING_MODELS = "aws_pricing_models"
    AZURE_PRICING_CALCULATOR = "azure_pricing_calculator"
    GCP_PRICING_CALCULATOR = "gcp_pricing_calculator"
    KOREA_PROCUREMENT = "korea_procurement"


ALL_PRICING_FRAMEWORKS: list[str] = [f.value for f in PricingFramework]


class PricingKPIThresholdStatus(str, enum.Enum):
    """TCOKPIBundle threshold_status options (3종)."""

    ON_TRACK = "on_track"
    WARNING = "warning"
    CRITICAL = "critical"


ALL_PRICING_KPI_THRESHOLD_STATUSES: list[str] = [s.value for s in PricingKPIThresholdStatus]


class RateCardInventory(TypedDict, total=False):
    """RateCardInventory TypedDict 18 fields (PRD §F35.1-2 verbatim).

    Phase 19 wire (cj-style 139번째) — 8-module cross-rollup + 5-cloud-provider
    rate card aggregator output (Phase 11 showback + Phase 12 anomaly +
    Phase 13 forecast + Phase 14 optimization + Phase 15 tag_governance +
    Phase 16 executive + Phase 17 sustainability + Phase 18 commitment).

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 1-1 audit-first INSERT — `pricing_dashboard_viewed` BEFORE view.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    rate_card_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str  # TEXT
    period_key: str  # TEXT e.g. "2026-08"
    scope_chain: dict[str, Any]  # JSONB — 8-module source attribution + 5-cloud-provider breakdown
    total_blended_rate_krw_per_hour: float  # NUMERIC(20, 2) blended rate across 5 cloud providers
    effective_discount_pct: float  # NUMERIC(5, 2) effective discount % vs on_demand baseline
    pricing_model_breakdown: dict[str, float]  # 6-pricing-model breakdown JSONB
    unit_metric_breakdown: dict[str, float]  # 4-unit-metric breakdown JSONB
    cloud_provider_breakdown: dict[str, float]  # 5-cloud-provider breakdown JSONB
    cost_per_user_krw: float  # NUMERIC(20, 2) unit metric 1/4
    cost_per_transaction_krw: float  # NUMERIC(20, 2) unit metric 2/4
    cost_per_request_krw: float  # NUMERIC(20, 2) unit metric 3/4
    cost_per_hour_krw: float  # NUMERIC(20, 2) unit metric 4/4
    on_demand_cost_krw: float  # NUMERIC(20, 2) baseline on_demand cost
    discounted_cost_krw: float  # NUMERIC(20, 2) actual cost after discount
    rate_card_hash: str  # TEXT SHA-256 of scope_chain + breakdown (CR 4-3/4-4)
    computed_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT (CR 1-1 ContextVar)


class TCOKPIBundle(TypedDict, total=False):
    """TCOKPIBundle TypedDict 10 fields (PRD §F35.2-11 verbatim).

    Phase 19 wire (cj-style 139번째) — TCO modeling selector output.
    8 NEW KPI calculations per AD-46 (b) verbatim:
    - total_blended_rate_krw_per_hour
    - effective_discount_pct
    - tco_1year_commitment_krw
    - tco_3year_commitment_krw
    - tco_on_demand_krw
    - cost_per_user_krw
    - cost_per_transaction_krw
    - unit_economics_score

    CR lessons applied:
    - CR 1-1 audit-first INSERT — `cross_module_pricing_kpi_calculated` AFTER compute.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    kpi_name: str  # TEXT (one of 8 pricing KPI names)
    kpi_value: float  # NUMERIC(20, 4)
    kpi_unit: str  # TEXT e.g. "krw"/"pct"/"count"/"score"
    kpi_delta: float | None  # NUMERIC nullable
    kpi_trend: str  # TEXT up/down/flat
    kpi_threshold_status: str  # TEXT on_track/warning/critical
    break_even_months: float  # NUMERIC(8, 2) 1y commitment payback period
    cloud_provider_breakdown: dict[str, float]  # 5-cloud-provider breakdown
    pricing_model_breakdown: dict[str, float]  # 6-pricing-model breakdown
    scope_chain: dict[str, Any]  # 8-module source attribution + industry baseline


class PricingReport(TypedDict, total=False):
    """PricingReport TypedDict 14 fields (PRD §F35.3-7 verbatim).

    Phase 19 wire (cj-style 139번째) — pricing report generator output.
    """

    report_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # enum
    scope_id: str  # TEXT
    period_key: str  # TEXT
    cadence: str  # monthly/quarterly/annual
    framework: str  # finops_foundation/aws_pricing_models/azure_pricing_calculator/gcp_pricing_calculator/korea_procurement
    export_format: str  # pdf/csv/excel
    report_file_url: str  # TEXT S3 archive URL
    report_size_bytes: int  # BIGINT
    report_generated_at: datetime  # TIMESTAMPTZ
    generated_by: str  # UUID actor_id
    status: str  # generating/completed/failed/expired
    trace_id: str  # TEXT
    pricing_model_breakdown: dict[str, float]  # 6-pricing-model coverage JSONB


class ScheduledPricingDispatch(TypedDict, total=False):
    """ScheduledPricingDispatch TypedDict 11 fields (PRD §F35.4-5 verbatim).

    Phase 19 wire (cj-style 139번째) — scheduled dispatch KST cron output.
    4 cron schedules (weekly Mon 09:00 + monthly 1st-day 09:00 +
    quarterly 1st-day 09:00 + annual Jan-1 09:00 KST) + recipient
    resolver (Slack + Email + MS Teams + S3 archive).
    """

    dispatch_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    dispatch_schedule: str  # weekly/monthly/quarterly/annual
    cron_expression: str  # TEXT e.g. "0 9 * * 1" weekly Mon 09:00 KST
    recipient_strategy: str  # owner_only/pricing_team/finance_team/custom_recipients
    recipient_list: dict[str, Any]  # JSONB
    report_id: str | None  # UUID FK nullable
    delivery_channels: list[str]  # JSONB slack/email/ms_teams/s3_archive
    status: str  # scheduled/running/completed/failed/cancelled
    scheduled_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT


# 8 NEW pricing KPI names SSOT (PRD §F35.2 verbatim).
ALL_PRICING_KPI_NAMES: list[str] = [
    "total_blended_rate_krw_per_hour",
    "effective_discount_pct",
    "tco_1year_commitment_krw",
    "tco_3year_commitment_krw",
    "tco_on_demand_krw",
    "cost_per_user_krw",
    "cost_per_transaction_krw",
    "unit_economics_score",
]


__all__ = [
    "PRICING_ENGINE_MODEL_VERSION",
    "PRICING_DEFAULTS",
    "PricingScopeType",
    "ALL_PRICING_SCOPE_TYPES",
    "CloudProvider",
    "ALL_PRICING_CLOUD_PROVIDERS",
    "PricingModel",
    "ALL_PRICING_MODELS",
    "PricingUnitMetric",
    "ALL_PRICING_UNIT_METRICS",
    "PricingCadence",
    "ALL_PRICING_CADENCES",
    "PricingExportFormat",
    "ALL_PRICING_EXPORT_FORMATS",
    "PricingDispatchSchedule",
    "ALL_PRICING_DISPATCH_SCHEDULES",
    "PricingRecipientStrategy",
    "ALL_PRICING_RECIPIENT_STRATEGIES",
    "PricingFramework",
    "ALL_PRICING_FRAMEWORKS",
    "PricingKPIThresholdStatus",
    "ALL_PRICING_KPI_THRESHOLD_STATUSES",
    "RateCardInventory",
    "TCOKPIBundle",
    "PricingReport",
    "ScheduledPricingDispatch",
    "ALL_PRICING_KPI_NAMES",
]
