"""apps.api.modules.finops.reporting.serializers — FinOps Reporting TypedDicts.

Phase 16 wire (cj-style 127번째) — m24_finops_reporting.reporting_serializers
NEW (Phase 15 wire `1b800d9` m23_finops_tag_governance.tag_governance_serializers
EXTENSION pattern verbatim 미러).

This module defines the canonical TypedDict schemas shared between the
backend (Python) and the frontend (TypeScript) per CR 12-5 D-PARITY-01
inversion discipline.

TypedDicts:
- ExecutiveRollup (16 fields) — 5-module cross-join aggregator output
- KPIMetric (8 fields) — cross-module KPI selector output
- ExecutiveReport (13 fields) — executive report generator output
- ScheduledDispatch (10 fields) — scheduled dispatch KST cron output

CR lessons applied:
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 11-4 P-015 — pure validator pattern.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 + openpyxl==3.1.2
  + apscheduler==3.10.4 + pytz==2024.1.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from typing_extensions import TypedDict

# Model version SSOT (Phase 15 EXTENSION pattern verbatim).
REPORTING_ENGINE_MODEL_VERSION = "1.0.0"

# Reporting defaults — Phase 16 NEW (CR 11-4 P-015 verbatim SSOT).
REPORTING_DEFAULTS: dict[str, Any] = {
    "default_scope_type": "tenant",
    "default_period_key_format": "YYYY-MM",
    "cache_ttl_hours": 24,
    "delta_threshold_pct": 5.0,
    "auto_approve_below_pct": 1.0,
    "deviation_threshold_pct": 10.0,
    "growth_threshold_pct": 5.0,
    "max_retry_count": 3,
    "retry_backoff_minutes": [1, 5, 30],
    "presigned_url_expiry_days": 7,
    "audit_first_insert": True,
    "rls_tenant_selector": True,
    "industry_agnostic": True,
}


class ScopeType(str, enum.Enum):
    """ExecutiveRollup scope_type options (4종)."""

    TENANT = "tenant"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PRODUCT_LINE = "product_line"


ALL_SCOPE_TYPES: list[str] = [s.value for s in ScopeType]


class Cadence(str, enum.Enum):
    """ExecutiveReport cadence options (3종)."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_CADENCES: list[str] = [c.value for c in Cadence]


class ExportFormat(str, enum.Enum):
    """ExecutiveReport export_format options (3종)."""

    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


ALL_EXPORT_FORMATS: list[str] = [e.value for e in ExportFormat]


class DispatchSchedule(str, enum.Enum):
    """ScheduledDispatch schedule options (4종)."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_DISPATCH_SCHEDULES: list[str] = [d.value for d in DispatchSchedule]


class RecipientStrategy(str, enum.Enum):
    """ScheduledDispatch recipient_strategy options (4종)."""

    OWNER_ONLY = "owner_only"
    EXECUTIVE_TEAM = "executive_team"
    BOARD_OBSERVERS = "board_observers"
    CUSTOM_RECIPIENTS = "custom_recipients"


ALL_RECIPIENT_STRATEGIES: list[str] = [r.value for r in RecipientStrategy]


class KPIThresholdStatus(str, enum.Enum):
    """KPIMetric threshold_status options (3종)."""

    ON_TRACK = "on_track"
    WARNING = "warning"
    CRITICAL = "critical"


ALL_KPI_THRESHOLD_STATUSES: list[str] = [s.value for s in KPIThresholdStatus]


class ExecutiveRollup(TypedDict, total=False):
    """ExecutiveRollup TypedDict 16 fields (PRD §F32.1-2 verbatim).

    Phase 16 wire (cj-style 127번째) — 5-module cross-join aggregator
    output (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast +
    Phase 14 optimization + Phase 15 tag_governance).

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 1-1 audit-first INSERT — `executive_dashboard_viewed` BEFORE view.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    rollup_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str  # TEXT
    period_key: str  # TEXT e.g. "2026-08"
    showback_total_krw: float  # NUMERIC(20, 2) Phase 11
    anomaly_count_30d: int  # INT Phase 12
    forecast_projection_krw: float  # NUMERIC(20, 2) Phase 13
    optimization_savings_krw: float  # NUMERIC(20, 2) Phase 14
    tag_compliance_pct: float  # NUMERIC(8, 4) Phase 15
    idle_cost_krw: float  # NUMERIC(20, 2) Phase 14 idle_resource
    department_breakdown: dict[str, float]  # JSONB
    cost_center_breakdown: dict[str, float]  # JSONB
    resource_type_breakdown: dict[str, float]  # JSONB
    generated_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT (CR 1-1 ContextVar)


class KPIMetric(TypedDict, total=False):
    """KPIMetric TypedDict 8 fields (PRD §F32.2-10 verbatim).

    Phase 16 wire (cj-style 127번째) — cross-module KPI selector output.

    CR lessons applied:
    - CR 1-1 audit-first INSERT — `cross_module_kpi_calculated` AFTER compute.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    kpi_name: str  # TEXT (one of 8 KPI names)
    kpi_value: float  # NUMERIC(20, 2)
    kpi_unit: str  # TEXT e.g. "KRW"/"pct"/"count"
    kpi_delta: float | None  # NUMERIC nullable
    kpi_trend: str  # TEXT up/down/flat
    kpi_threshold_status: str  # TEXT on_track/warning/critical
    kpi_computed_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT


class ExecutiveReport(TypedDict, total=False):
    """ExecutiveReport TypedDict 13 fields (PRD §F32.3-7 verbatim).

    Phase 16 wire (cj-style 127번째) — executive report generator output.
    """

    report_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # enum
    scope_id: str  # TEXT
    period_key: str  # TEXT
    cadence: str  # monthly/quarterly/annual
    export_format: str  # pdf/csv/excel
    report_file_url: str  # TEXT S3 archive URL
    report_size_bytes: int  # BIGINT
    report_generated_at: datetime  # TIMESTAMPTZ
    generated_by: str  # UUID actor_id
    status: str  # generating/completed/failed/expired
    trace_id: str  # TEXT


class ScheduledDispatch(TypedDict, total=False):
    """ScheduledDispatch TypedDict 10 fields (PRD §F32.4-5 verbatim).

    Phase 16 wire (cj-style 127번째) — scheduled dispatch KST cron output.
    """

    dispatch_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    dispatch_schedule: str  # weekly/monthly/quarterly/annual
    cron_expression: str  # TEXT e.g. "0 9 1 * *"
    recipient_strategy: str  # owner_only/executive_team/...
    recipient_list: dict[str, Any]  # JSONB
    report_id: str | None  # UUID FK nullable
    status: str  # scheduled/running/completed/failed/cancelled
    scheduled_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT


# 8 NEW KPI names SSOT (PRD §F32.2 verbatim).
ALL_KPI_NAMES: list[str] = [
    "total_monthly_cost_krw",
    "monthly_cost_growth_pct",
    "cost_per_employee_krw",
    "cost_anomaly_count_30d",
    "forecast_deviation_pct",
    "idle_cost_monthly_krw",
    "tag_compliance_pct",
    "optimization_realized_savings_krw",
]


__all__ = [
    "REPORTING_ENGINE_MODEL_VERSION",
    "REPORTING_DEFAULTS",
    "ScopeType",
    "ALL_SCOPE_TYPES",
    "Cadence",
    "ALL_CADENCES",
    "ExportFormat",
    "ALL_EXPORT_FORMATS",
    "DispatchSchedule",
    "ALL_DISPATCH_SCHEDULES",
    "RecipientStrategy",
    "ALL_RECIPIENT_STRATEGIES",
    "KPIThresholdStatus",
    "ALL_KPI_THRESHOLD_STATUSES",
    "ExecutiveRollup",
    "KPIMetric",
    "ExecutiveReport",
    "ScheduledDispatch",
    "ALL_KPI_NAMES",
]
