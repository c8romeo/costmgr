"""apps.api.modules.finops.commitment.serializers — FinOps Cloud Commitment TypedDicts.

Phase 18 wire (cj-style 135번째) — m26_finops_commitment.commitment_serializers
NEW (Phase 17 wire `97cfe4e` m25_finops_sustainability.sustainability_serializers
EXTENSION pattern verbatim).

This module defines the canonical TypedDict schemas shared between the
backend (Python) and the frontend (TypeScript) per CR 12-5 D-PARITY-01
inversion discipline.

TypedDicts:
- CommitmentInventoryRollup (16 fields) — 7-module cross-rollup + 5-cloud-provider aggregator output
- CommitmentKPI (16 fields) — commitment KPI selector output
- CommitmentReport (14 fields) — commitment report generator output
- ScheduledCommitmentDispatch (10 fields) — scheduled dispatch KST cron output

CR lessons applied:
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 11-4 P-015 — pure validator pattern.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 + openpyxl==3.1.2
  + pandas==2.1.4 + xlsxwriter==3.1.9 + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from typing_extensions import TypedDict

# Model version SSOT (Phase 17 EXTENSION pattern verbatim).
COMMITMENT_ENGINE_MODEL_VERSION = "1.0.0"

# Commitment defaults — Phase 18 NEW (CR 11-4 P-015 verbatim SSOT).
COMMITMENT_DEFAULTS: dict[str, Any] = {
    "default_scope_type": "tenant",
    "default_period_key_format": "YYYY-MM",
    "cache_ttl_hours": 24,
    "delta_threshold_pct": 5.0,
    "deviation_threshold_pct": 10.0,
    "coverage_target_pct": 70.0,  # target commitment coverage for cost optimization
    "utilization_target_pct": 80.0,  # target commitment utilization
    "renewal_decision_threshold": 50.0,  # renewal_decision_score cutoff
    "utilization_pct_industry_baselines": {
        # 4 industries baseline utilization_pct — PRD §F34.5 verbatim.
        "manufacturing": 1.2,
        "service": 0.8,
        "manufacturing_service": 1.0,
        "manufacturing_service_other": 1.1,
    },
    "ri_sp_discount_1y": 0.40,  # 1-year RI/SP discount (40%)
    "ri_sp_discount_3y": 0.60,  # 3-year RI/SP discount (60%)
    "max_retry_count": 3,
    "retry_backoff_minutes": [1, 5, 30],
    "presigned_url_expiry_days": 7,
    "audit_first_insert": True,
    "rls_tenant_selector": True,
    "industry_agnostic": True,
}


class CommitmentScopeType(str, enum.Enum):
    """CommitmentInventoryRollup scope_type options (4종)."""

    TENANT = "tenant"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PRODUCT_LINE = "product_line"


ALL_COMMITMENT_SCOPE_TYPES: list[str] = [s.value for s in CommitmentScopeType]


class CloudProvider(str, enum.Enum):
    """Cloud provider options for commitment cross-rollup (5종).

    Phase 18 NEW enum — 5 cloud providers (AWS + Azure + GCP +
    Naver Cloud + KT Cloud) per AD-45 (a) verbatim.
    """

    AWS = "aws"  # Amazon Web Services (EC2/RDS/ElastiCache/Redshift RI + EC2/S3/Redshift/DynamoDB SP)
    AZURE = "azure"  # Microsoft Azure (Reservations)
    GCP = "gcp"  # Google Cloud Platform (Committed Use Discounts)
    NAVER = "naver"  # Naver Cloud (commitment-based discount)
    KT = "kt"  # KT Cloud (commitment-based discount)


ALL_COMMITMENT_CLOUD_PROVIDERS: list[str] = [p.value for p in CloudProvider]


class CommitmentType(str, enum.Enum):
    """Cloud commitment type options (6종).

    Phase 18 EXTENSION of Phase 14 commitment_recommender verbatim
    (apps/api/modules/finops/commitment_recommender.py:49-83).
    """

    EC2_RI = "ec2_ri"
    RDS_RI = "rds_ri"
    EC2_SP = "ec2_sp"
    S3_SP = "s3_sp"
    REDSHIFT_SP = "redshift_sp"
    DYNAMODB_SP = "dynamodb_sp"


ALL_COMMITMENT_COMMITMENT_TYPES: list[str] = [c.value for c in CommitmentType]


class CommitmentTerm(str, enum.Enum):
    """Cloud commitment term options (2종)."""

    ONE_YEAR = "1_year"
    THREE_YEAR = "3_year"


ALL_COMMITMENT_TERMS: list[str] = [t.value for t in CommitmentTerm]


class CommitmentCadence(str, enum.Enum):
    """CommitmentReport cadence options (3종)."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_COMMITMENT_CADENCES: list[str] = [c.value for c in CommitmentCadence]


class CommitmentExportFormat(str, enum.Enum):
    """CommitmentReport export_format options (3종)."""

    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


ALL_COMMITMENT_EXPORT_FORMATS: list[str] = [e.value for e in CommitmentExportFormat]


class CommitmentDispatchSchedule(str, enum.Enum):
    """ScheduledCommitmentDispatch schedule options (4종)."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_COMMITMENT_DISPATCH_SCHEDULES: list[str] = [
    d.value for d in CommitmentDispatchSchedule
]


class CommitmentRecipientStrategy(str, enum.Enum):
    """ScheduledCommitmentDispatch recipient_strategy options (4종)."""

    OWNER_ONLY = "owner_only"
    COMMITMENT_TEAM = "commitment_team"
    FINANCE_TEAM = "finance_team"
    CUSTOM_RECIPIENTS = "custom_recipients"


ALL_COMMITMENT_RECIPIENT_STRATEGIES: list[str] = [
    r.value for r in CommitmentRecipientStrategy
]


class CommitmentFramework(str, enum.Enum):
    """Commitment reporting framework options (5종)."""

    FINOPS_FOUNDATION = "finops_foundation"  # FinOps Foundation framework
    AWS_COST_OPTIMIZATION = "aws_cost_optimization"  # AWS Cost Optimization Pillar
    AZURE_COST_OPTIMIZATION = "azure_cost_optimization"  # Azure Cost Optimization
    GCP_COST_OPTIMIZATION = "gcp_cost_optimization"  # GCP Cost Optimization
    KOREA_PROCUREMENT = "korea_procurement"  # 한국 조달청 클라우드 commitment 가이드라인


ALL_COMMITMENT_FRAMEWORKS: list[str] = [f.value for f in CommitmentFramework]


class CommitmentKPIThresholdStatus(str, enum.Enum):
    """CommitmentKPI threshold_status options (3종)."""

    ON_TRACK = "on_track"
    WARNING = "warning"
    CRITICAL = "critical"


ALL_COMMITMENT_KPI_THRESHOLD_STATUSES: list[str] = [
    s.value for s in CommitmentKPIThresholdStatus
]


class CommitmentInventoryRollup(TypedDict, total=False):
    """CommitmentInventoryRollup TypedDict 16 fields (PRD §F34.1-2 verbatim).

    Phase 18 wire (cj-style 135번째) — 7-module cross-rollup + 5-cloud-provider
    aggregator output (Phase 11 showback + Phase 12 anomaly + Phase 13
    forecast + Phase 14 optimization + Phase 15 tag_governance + Phase 16
    executive + Phase 17 sustainability).

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 1-1 audit-first INSERT — `commitment_inventory_aggregated` BEFORE view.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    commitment_rollup_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str  # TEXT
    period_key: str  # TEXT e.g. "2026-08"
    scope_chain: dict[str, Any]  # JSONB — 7-module source attribution + 5-cloud-provider breakdown
    total_commitment_value_krw: float  # NUMERIC(20, 2) SUM across 5 cloud providers
    coverage_pct: float  # NUMERIC(5, 2) Σcommitment_value / total_on_demand_cost × 100
    utilization_pct: float  # NUMERIC(5, 2) actual_used_hours / purchased_hours × 100
    expiring_commitments_30d: int  # INT count of commitments expiring within 30 days
    recommended_purchase_krw: float  # NUMERIC(20, 2) Phase 14 commitment_recommender recommended
    savings_realized_krw: float  # NUMERIC(20, 2) on_demand_cost - commitment_cost
    idle_commitment_krw: float  # NUMERIC(20, 2) unused_commitment_value
    renewal_decision_score: float  # NUMERIC(5, 2) renewal recommendation score 0-100
    computed_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT (CR 1-1 ContextVar)


class CommitmentKPI(TypedDict, total=False):
    """CommitmentKPI TypedDict 16 fields (PRD §F34.2-10 verbatim).

    Phase 18 wire (cj-style 135번째) — commitment KPI selector output.
    8 NEW KPI calculations per AD-45 (b) verbatim.

    CR lessons applied:
    - CR 1-1 audit-first INSERT — `commitment_kpi_calculated` AFTER compute.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    kpi_name: str  # TEXT (one of 8 commitment KPI names)
    kpi_value: float  # NUMERIC(20, 4)
    kpi_unit: str  # TEXT e.g. "krw"/"pct"/"count"/"score"
    kpi_delta: float | None  # NUMERIC nullable
    kpi_trend: str  # TEXT up/down/flat
    kpi_threshold_status: str  # TEXT on_track/warning/critical
    kpi_target: float | None  # NUMERIC nullable target value
    kpi_computed_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT
    cloud_provider_breakdown: dict[str, float]  # 5-cloud-provider breakdown
    commitment_type_breakdown: dict[str, float]  # 6-commitment-type breakdown
    industry: str  # tenant industry baseline
    coverage_target_pct: float  # target coverage_pct
    utilization_target_pct: float  # target utilization_pct
    renewal_decision_threshold: float  # renewal decision threshold
    scope_chain: dict[str, Any]  # 7-module source attribution


class CommitmentReport(TypedDict, total=False):
    """CommitmentReport TypedDict 14 fields (PRD §F34.3-7 verbatim).

    Phase 18 wire (cj-style 135번째) — commitment report generator output.
    """

    report_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # enum
    scope_id: str  # TEXT
    period_key: str  # TEXT
    cadence: str  # monthly/quarterly/annual
    framework: str  # finops_foundation/aws_cost_optimization/azure_cost_optimization/gcp_cost_optimization/korea_procurement
    export_format: str  # pdf/csv/excel
    report_file_url: str  # TEXT S3 archive URL
    report_size_bytes: int  # BIGINT
    report_generated_at: datetime  # TIMESTAMPTZ
    generated_by: str  # UUID actor_id
    status: str  # generating/completed/failed/expired
    trace_id: str  # TEXT


class ScheduledCommitmentDispatch(TypedDict, total=False):
    """ScheduledCommitmentDispatch TypedDict 10 fields (PRD §F34.4-5 verbatim).

    Phase 18 wire (cj-style 135번째) — scheduled dispatch KST cron output.
    """

    dispatch_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    dispatch_schedule: str  # weekly/monthly/quarterly/annual
    cron_expression: str  # TEXT e.g. "0 9 * * 1" weekly Mon 09:00 KST
    recipient_strategy: str  # owner_only/commitment_team/finance_team/custom_recipients
    recipient_list: dict[str, Any]  # JSONB
    report_id: str | None  # UUID FK nullable
    status: str  # scheduled/running/completed/failed/cancelled
    scheduled_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT


# 8 NEW commitment KPI names SSOT (PRD §F34.2 verbatim).
ALL_COMMITMENT_KPI_NAMES: list[str] = [
    "total_commitment_value_krw",
    "coverage_pct",
    "utilization_pct",
    "expiring_commitments_30d",
    "recommended_purchase_krw",
    "savings_realized_krw",
    "idle_commitment_krw",
    "renewal_decision_score",
]


__all__ = [
    "COMMITMENT_ENGINE_MODEL_VERSION",
    "COMMITMENT_DEFAULTS",
    "CommitmentScopeType",
    "ALL_COMMITMENT_SCOPE_TYPES",
    "CloudProvider",
    "ALL_COMMITMENT_CLOUD_PROVIDERS",
    "CommitmentType",
    "ALL_COMMITMENT_COMMITMENT_TYPES",
    "CommitmentTerm",
    "ALL_COMMITMENT_TERMS",
    "CommitmentCadence",
    "ALL_COMMITMENT_CADENCES",
    "CommitmentExportFormat",
    "ALL_COMMITMENT_EXPORT_FORMATS",
    "CommitmentDispatchSchedule",
    "ALL_COMMITMENT_DISPATCH_SCHEDULES",
    "CommitmentRecipientStrategy",
    "ALL_COMMITMENT_RECIPIENT_STRATEGIES",
    "CommitmentFramework",
    "ALL_COMMITMENT_FRAMEWORKS",
    "CommitmentKPIThresholdStatus",
    "ALL_COMMITMENT_KPI_THRESHOLD_STATUSES",
    "CommitmentInventoryRollup",
    "CommitmentKPI",
    "CommitmentReport",
    "ScheduledCommitmentDispatch",
    "ALL_COMMITMENT_KPI_NAMES",
]