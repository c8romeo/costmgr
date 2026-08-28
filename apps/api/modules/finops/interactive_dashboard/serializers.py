"""apps.api.modules.finops.interactive_dashboard.serializers — Phase 28 serializers.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
cross-phase aggregation layer serializers (PRD §F43.1~§F43.8 verbatim +
AD-56 (a)~(g) 7 sub-decisions + Phase 11~27 18-capability FinOps
territory ledger data 활용).

Provides:
- Enums: KPIRefreshCadence (6: realtime/hourly/daily/weekly/monthly/
  on_demand) + ExportFormat (5: pdf/xlsx/csv/json/png) +
  DashboardSharingScope (4: private/tenant/tenant_owner/cross_tenant) +
  DashboardLayout (3: grid/masonry/tabs) + DrillDownDimension (7:
  tenant/cost_center/department/business_unit/tag/cloud_provider/
  service) + DrillDownGranularity (7: minute/hour/day/week/month/
  quarter/year).
- TypedDicts: UnifiedKPI (24 fields) + KPIBreakdown (8 fields) +
  DrillDownContext (6 fields) + SavedView (14 fields) + ExportJob (12
  fields) + SharingGrant (8 fields).
- Constants: INTERACTIVE_DASHBOARD_ENGINE_VERSION +
  DASHBOARD_KPI_DIMENSION_WEIGHTS (cost 0.30 + usage 0.20 +
  performance 0.20 + compliance 0.15 + sla 0.15) +
  DASHBOARD_CADENCE_HOURS_KST + DASHBOARD_RECIPIENT_TEMPLATES +
  DASHBOARD_DEFAULTS + PHASE_KPI_SOURCE_MODULES (18 entries) +
  PREDEFINED_VIEW_TEMPLATES (12 entries) + LISTEN/NOTIFY channels.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW audit actions via
  ActionClass.FINOPS_INTERACTIVE_DASHBOARD.
- CR 1-1 ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision NUMERIC(18,2) KRW.
- CR 11-4 P-015 — pure validator pattern, no pytest fixtures downstream.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — reportlab==4.0.7 + xlsxwriter==3.1.9 +
  pandas==2.1.4 + matplotlib==3.8.2 + Recharts 2.12.7 + TanStack Table
  v8 + noto-sans-cjk-kr + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
- D-FINOPS-15 honestly DEFER (multi-modal aggregation + causal
  inference + LLM auto-narrative + automated remediation + federated
  benchmarking + marketplace + streaming + online learning).
"""
from __future__ import annotations

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
INTERACTIVE_DASHBOARD_ENGINE_VERSION = "1.0.0"

# Module tag (Phase 28 territory identifier — used by router + audit + tests)
MODULE_TAG: str = "m28_finops_interactive_dashboard"

# FastAPI router prefix (PRD §F43.1 verbatim — T1.6)
DASHBOARD_ROUTER_PREFIX: str = "/api/v1/admin/finops/interactive-dashboard"

# High-value threshold for owner approval / 2FA challenge (AD-56 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW/year

# 5-dim weighted aggregation (PRD §F43.2 + AD-56 (b) verbatim)
DASHBOARD_KPI_DIMENSION_WEIGHTS: dict[str, float] = {
    "cost": 0.30,
    "usage": 0.20,
    "performance": 0.20,
    "compliance": 0.15,
    "sla": 0.15,
}

# Cadence → hours mapping (PRD §F43.1 + AD-56 (a) verbatim)
DASHBOARD_CADENCE_HOURS: dict[str, int] = {
    "realtime": 0,
    "hourly": 1,
    "daily": 24,
    "weekly": 168,
    "monthly": 720,
}

# Cadence schedule KST pytz (PRD §F43.1 + AD-56 (a) verbatim)
DASHBOARD_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "daily_unified_kpi_refresh": (4, 0),  # 04:00 KST daily
    "weekly_export_cleanup": (5, 0),  # 05:00 KST Monday
    "monthly_sharing_expiry": (6, 0),  # 06:00 KST 1st day
}

# Cost / capacity guards (PRD §F43.2 + §F43.3 verbatim)
MAX_SAVED_VIEWS_PER_TENANT = 50
MAX_EXPORT_SIZE_BYTES = 52_428_800  # 50MB
EXPORT_MAX_RETRIES = 3
SAVED_VIEW_CACHE_TTL_SECONDS = 300  # 5 minutes
SHARING_EXPIRES_DEFAULT_DAYS = 30
TOTAL_VERIFICATION_TOLERANCE_KRW = 0.01  # ±0.01 KRW

DASHBOARD_DEFAULTS: dict[str, object] = {
    "max_saved_views_per_tenant": MAX_SAVED_VIEWS_PER_TENANT,
    "cache_ttl_seconds": SAVED_VIEW_CACHE_TTL_SECONDS,
    "sharing_expires_default_days": SHARING_EXPIRES_DEFAULT_DAYS,
    "max_export_size_bytes": MAX_EXPORT_SIZE_BYTES,
    "export_max_retries": EXPORT_MAX_RETRIES,
    "default_layout": "grid",
    "default_cadence": "daily",
}

# Phase 11~28 unified KPI source modules (PRD §F43.1 verbatim — 18 KPIs)
PHASE_KPI_SOURCE_MODULES: dict[str, str] = {
    "phase_11": "showback_krw",
    "phase_12": "anomaly_count",
    "phase_13": "forecast_krw",
    "phase_14": "optimization_savings_krw",
    "phase_15": "tag_compliance_pct",
    "phase_16": "report_krw",
    "phase_17": "sustainability_co2_kg",
    "phase_18": "commitment_utilization_pct",
    "phase_19": "pricing_savings_krw",
    "phase_20": "multi_cloud_reconciliation_krw",
    "phase_21": "reserved_capacity_utilization_pct",
    "phase_22": "chargeback_settlement_krw",
    "phase_23": "unit_economics_cost_per_unit",
    "phase_24": "budget_consumption_pct",
    "phase_25": "vendor_spend_krw",
    "phase_26": "anomaly_ml_score",
    "phase_27": "carry_over_metric",
    "phase_28": "unified_kpi_total",
}

# 12 pre-defined saved-view templates (PRD §F43.2 verbatim)
PREDEFINED_VIEW_TEMPLATES: tuple[str, ...] = (
    "CostByCloudProvider",
    "CostByService",
    "CostByCostCenter",
    "CostByDepartment",
    "CostByBusinessUnit",
    "CostByTag",
    "SavingsByOptimizationType",
    "CommitmentUtilizationByCloud",
    "BudgetVarianceByPeriod",
    "SustainabilityByCloudProvider",
    "VendorSpendByCategory",
    "ReservedInstanceUtilizationByTier",
)

# LISTEN/NOTIFY channels (PRD §F43.1 + T6.2 verbatim — 18 channels)
UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS: tuple[str, ...] = tuple(
    [f"phase_{n}_unified_kpi_refreshed" for n in range(11, 28)]
    + ["phase_28_unified_kpi_calculated"]
)

# Recipient strategy templates (PRD §F43.3 verbatim)
DASHBOARD_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-interactive-dashboard"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": [
            "#finops-interactive-dashboard",
            "#finops-executive",
        ],
        "email_recipients": ["tenant_owner", "executive_viewer"],
        "ms_teams_channels": ["FinOps Executive"],
        "s3_archive_enabled": True,
    },
    "all_viewers": {
        "slack_channels": ["#finops-interactive-dashboard"],
        "email_recipients": ["tenant_owner", "executive_viewer", "viewer"],
        "ms_teams_channels": [],
        "s3_archive_enabled": False,
    },
}


# ── Enums (6 NEW) ─────────────────────────────────────────────────────────
class KPIRefreshCadence(str, enum.Enum):
    """Unified KPI refresh cadence (PRD §F43.1 + AD-56 (a))."""

    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class ExportFormat(str, enum.Enum):
    """Export pipeline output format (PRD §F43.3 + AD-56 (c))."""

    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"
    PNG = "png"


class DashboardSharingScope(str, enum.Enum):
    """Dashboard sharing RBAC scope (PRD §F43.7 + AD-56 (d))."""

    PRIVATE = "private"
    TENANT = "tenant"
    TENANT_OWNER = "tenant_owner"
    CROSS_TENANT = "cross_tenant"


class DashboardLayout(str, enum.Enum):
    """Dashboard layout mode (PRD §F43.4)."""

    GRID = "grid"
    MASONRY = "masonry"
    TABS = "tabs"


class DrillDownDimension(str, enum.Enum):
    """Drill-down dimension (PRD §F43.2 verbatim — 7 dims)."""

    TENANT = "tenant"
    COST_CENTER = "cost_center"
    DEPARTMENT = "department"
    BUSINESS_UNIT = "business_unit"
    TAG = "tag"
    CLOUD_PROVIDER = "cloud_provider"
    SERVICE = "service"


class DrillDownGranularity(str, enum.Enum):
    """Drill-down time granularity (PRD §F43.2 verbatim — 7 grains)."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ExportJobStatus(str, enum.Enum):
    """Export job lifecycle status (PRD §F43.3 + cancel_export_job T1.5)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ── TypedDicts (6 NEW) ────────────────────────────────────────────────────
class UnifiedKPI(TypedDict):
    """Cross-phase unified KPI record (PRD §F43.1 — 24 fields)."""

    unified_kpi_id: str
    tenant_id: str
    period_key: str
    dimension: str
    dimension_value: str
    kpi_value_krw: float
    showback_krw: float
    anomaly_count: int
    forecast_krw: float
    optimization_savings_krw: float
    tag_compliance_pct: float
    report_krw: float
    sustainability_co2_kg: float
    commitment_utilization_pct: float
    pricing_savings_krw: float
    multi_cloud_reconciliation_krw: float
    reserved_capacity_utilization_pct: float
    chargeback_settlement_krw: float
    unit_economics_cost_per_unit: float
    budget_consumption_pct: float
    vendor_spend_krw: float
    anomaly_ml_score: float
    refresh_cadence: str
    computed_at: str
    trace_id: str


class KPIBreakdown(TypedDict):
    """Weighted 5-dim KPI breakdown (PRD §F43.1 — 8 fields)."""

    tenant_id: str
    period_key: str
    cost_score: float
    usage_score: float
    performance_score: float
    compliance_score: float
    sla_score: float
    weighted_total: float


class DrillDownContext(TypedDict):
    """Drill-down navigation context (PRD §F43.2 — 6 fields)."""

    tenant_id: str
    dimension: str
    dimension_value: str
    granularity: str
    period_key: str
    parent_dimension: str | None


class SavedView(TypedDict):
    """Per-tenant saved dashboard view (PRD §F43.2 — 14 fields)."""

    saved_view_id: str
    tenant_id: str
    view_name: str
    template_id: str | None
    filter_by: dict[str, object]
    group_by: list[str]
    sort_by: str
    chart_type: str
    time_range: str
    layout: str
    is_shared: bool
    created_by_user_id: str
    created_at: str
    updated_at: str


class ExportJob(TypedDict):
    """Export job tracking record (PRD §F43.3 — 12 fields)."""

    export_job_id: str
    tenant_id: str
    saved_view_id: str
    export_format: str
    status: str
    progress_pct: float
    file_path: str | None
    file_size_bytes: int
    checksum_sha256: str | None
    expires_at: str | None
    started_at: str
    completed_at: str | None


class SharingGrant(TypedDict):
    """Dashboard sharing grant (PRD §F43.7 — 8 fields)."""

    sharing_grant_id: str
    tenant_id: str
    saved_view_id: str
    scope: str
    granted_to_user_id: str
    granted_by_user_id: str
    granted_at: str
    expires_at: str


__all__ = [
    "DASHBOARD_CADENCE_HOURS",
    "DASHBOARD_CADENCE_HOURS_KST",
    "DASHBOARD_DEFAULTS",
    "DASHBOARD_KPI_DIMENSION_WEIGHTS",
    "DASHBOARD_RECIPIENT_TEMPLATES",
    "DASHBOARD_ROUTER_PREFIX",
    "EXPORT_MAX_RETRIES",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "INTERACTIVE_DASHBOARD_ENGINE_VERSION",
    "MODULE_TAG",
    "MAX_EXPORT_SIZE_BYTES",
    "MAX_SAVED_VIEWS_PER_TENANT",
    "PHASE_KPI_SOURCE_MODULES",
    "PREDEFINED_VIEW_TEMPLATES",
    "SAVED_VIEW_CACHE_TTL_SECONDS",
    "SHARING_EXPIRES_DEFAULT_DAYS",
    "TOTAL_VERIFICATION_TOLERANCE_KRW",
    "UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS",
    "DashboardLayout",
    "DashboardSharingScope",
    "DrillDownContext",
    "DrillDownDimension",
    "DrillDownGranularity",
    "ExportFormat",
    "ExportJob",
    "ExportJobStatus",
    "KPIBreakdown",
    "KPIRefreshCadence",
    "SavedView",
    "SharingGrant",
    "UnifiedKPI",
]
