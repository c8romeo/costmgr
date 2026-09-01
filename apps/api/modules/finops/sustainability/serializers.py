"""apps.api.modules.finops.sustainability.serializers — FinOps Sustainability TypedDicts.

Phase 17 wire (cj-style 131번째) — m25_finops_sustainability.sustainability_serializers
NEW (Phase 16 wire `81ae00a` m24_finops_reporting.reporting_serializers
EXTENSION pattern verbatim).

This module defines the canonical TypedDict schemas shared between the
backend (Python) and the frontend (TypeScript) per CR 12-5 D-PARITY-01
inversion discipline.

TypedDicts:
- CarbonEmissionsRollup (14 fields) — 6-module cross-rollup aggregator output
- SustainabilityKPIMetric (8 fields) — sustainability KPI selector output
- SustainabilityReport (13 fields) — sustainability report generator output
- ScheduledSustainabilityDispatch (10 fields) — scheduled dispatch KST cron output

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

# Model version SSOT (Phase 16 EXTENSION pattern verbatim).
SUSTAINABILITY_ENGINE_MODEL_VERSION = "1.0.0"

# Sustainability defaults — Phase 17 NEW (CR 11-4 P-015 verbatim SSOT).
SUSTAINABILITY_DEFAULTS: dict[str, Any] = {
    "default_scope_type": "tenant",
    "default_period_key_format": "YYYY-MM",
    "cache_ttl_hours": 24,
    "delta_threshold_pct": 5.0,
    "deviation_threshold_pct": 10.0,
    "renewable_energy_threshold_pct": 30.0,
    "carbon_intensity_industry_baselines": {
        # 4 industries baseline carbon intensity (kgCO2e / KRW) — PRD §F33.5 verbatim.
        "manufacturing": 0.0008,
        "service": 0.0004,
        "manufacturing_service": 0.0006,
        "manufacturing_service_other": 0.0007,
    },
    "data_center_pue_baseline": 1.5,  # industry-average PUE 1.5 baseline
    "max_retry_count": 3,
    "retry_backoff_minutes": [1, 5, 30],
    "presigned_url_expiry_days": 7,
    "audit_first_insert": True,
    "rls_tenant_selector": True,
    "industry_agnostic": True,
}


class CarbonScopeType(str, enum.Enum):
    """CarbonEmissionsRollup scope_type options (4종)."""

    TENANT = "tenant"
    DEPARTMENT = "department"
    COST_CENTER = "cost_center"
    PRODUCT_LINE = "product_line"


ALL_CARBON_SCOPE_TYPES: list[str] = [s.value for s in CarbonScopeType]


class CarbonOffsetRegistry(str, enum.Enum):
    """Carbon offset registry options (3종)."""

    VCU = "vcu"  # Verified Carbon Unit (Verra)
    CER = "cer"  # Certified Emission Reduction (UNFCCC)
    KCU = "kcu"  # Korean Credit Unit (KCU)


ALL_CARBON_OFFSET_REGISTRIES: list[str] = [r.value for r in CarbonOffsetRegistry]


class SustainabilityCadence(str, enum.Enum):
    """SustainabilityReport cadence options (3종)."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_SUSTAINABILITY_CADENCES: list[str] = [c.value for c in SustainabilityCadence]


class SustainabilityExportFormat(str, enum.Enum):
    """SustainabilityReport export_format options (3종)."""

    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


ALL_SUSTAINABILITY_EXPORT_FORMATS: list[str] = [e.value for e in SustainabilityExportFormat]


class SustainabilityDispatchSchedule(str, enum.Enum):
    """ScheduledSustainabilityDispatch schedule options (4종)."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


ALL_SUSTAINABILITY_DISPATCH_SCHEDULES: list[str] = [d.value for d in SustainabilityDispatchSchedule]


class SustainabilityRecipientStrategy(str, enum.Enum):
    """ScheduledSustainabilityDispatch recipient_strategy options (4종)."""

    OWNER_ONLY = "owner_only"
    SUSTAINABILITY_TEAM = "sustainability_team"
    BOARD_OBSERVERS = "board_observers"
    CUSTOM_RECIPIENTS = "custom_recipients"


ALL_SUSTAINABILITY_RECIPIENT_STRATEGIES: list[str] = [
    r.value for r in SustainabilityRecipientStrategy
]


class SustainabilityFramework(str, enum.Enum):
    """Sustainability reporting framework options (5종)."""

    CSRD = "csrd"  # EU Corporate Sustainability Reporting Directive
    SEC_CLIMATE = "sec_climate"  # SEC Climate Disclosure
    EU_TAXONOMY = "eu_taxonomy"  # EU Taxonomy
    IFRS_S2 = "ifrs_s2"  # IFRS S2 Climate-related Disclosures
    KSSB = "kssb"  # 한국 지속가능성 공시기준 (KSSB)


ALL_SUSTAINABILITY_FRAMEWORKS: list[str] = [f.value for f in SustainabilityFramework]


class SustainabilityKPIThresholdStatus(str, enum.Enum):
    """SustainabilityKPIMetric threshold_status options (3종)."""

    ON_TRACK = "on_track"
    WARNING = "warning"
    CRITICAL = "critical"


ALL_SUSTAINABILITY_KPI_THRESHOLD_STATUSES: list[str] = [
    s.value for s in SustainabilityKPIThresholdStatus
]


class CarbonEmissionsRollup(TypedDict, total=False):
    """CarbonEmissionsRollup TypedDict 14 fields (PRD §F33.1-2 verbatim).

    Phase 17 wire (cj-style 131번째) — 6-module cross-rollup aggregator
    output (Phase 11 showback × carbon_intensity + Phase 12 anomaly +
    Phase 13 forecast + Phase 14 optimization + Phase 15 tag_governance
    + Phase 16 executive).

    CR lessons applied:
    - CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
    - CR 1-1 audit-first INSERT — `carbon_emissions_aggregated` BEFORE view.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    carbon_rollup_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # tenant/department/cost_center/product_line
    scope_id: str  # TEXT
    period_key: str  # TEXT e.g. "2026-08"
    scope_chain: dict[str, Any]  # JSONB — 6-module source attribution
    total_carbon_emissions_kgco2e: float  # NUMERIC(20, 4)
    scope1_emissions_kgco2e: float  # NUMERIC(20, 4)
    scope2_emissions_kgco2e: float  # NUMERIC(20, 4)
    scope3_emissions_kgco2e: float  # NUMERIC(20, 4)
    carbon_offset_kgco2e: float  # NUMERIC(20, 4) VCU + CER + KCU
    net_carbon_emissions_kgco2e: float  # NUMERIC(20, 4) total - offset
    renewable_energy_pct: float  # NUMERIC(8, 4)
    computed_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT (CR 1-1 ContextVar)


class SustainabilityKPIMetric(TypedDict, total=False):
    """SustainabilityKPIMetric TypedDict 8 fields (PRD §F33.2-10 verbatim).

    Phase 17 wire (cj-style 131번째) — sustainability KPI selector output.

    CR lessons applied:
    - CR 1-1 audit-first INSERT — `sustainability_kpi_calculated` AFTER compute.
    - CR 12-5 D-PARITY-01 — Python ↔ TypeScript parity.
    """

    kpi_name: str  # TEXT (one of 8 sustainability KPI names)
    kpi_value: float  # NUMERIC(20, 4)
    kpi_unit: str  # TEXT e.g. "kgCO2e"/"kgCO2e_per_krw"/"pct"/"ratio"
    kpi_delta: float | None  # NUMERIC nullable
    kpi_trend: str  # TEXT up/down/flat
    kpi_threshold_status: str  # TEXT on_track/warning/critical
    kpi_computed_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT


class SustainabilityReport(TypedDict, total=False):
    """SustainabilityReport TypedDict 13 fields (PRD §F33.3-7 verbatim).

    Phase 17 wire (cj-style 131번째) — sustainability report generator output.
    """

    report_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    scope_type: str  # enum
    scope_id: str  # TEXT
    period_key: str  # TEXT
    cadence: str  # monthly/quarterly/annual
    framework: str  # csrd/sec_climate/eu_taxonomy/ifrs_s2/kssb
    export_format: str  # pdf/csv/excel
    report_file_url: str  # TEXT S3 archive URL
    report_size_bytes: int  # BIGINT
    report_generated_at: datetime  # TIMESTAMPTZ
    generated_by: str  # UUID actor_id
    status: str  # generating/completed/failed/expired
    trace_id: str  # TEXT


class ScheduledSustainabilityDispatch(TypedDict, total=False):
    """ScheduledSustainabilityDispatch TypedDict 10 fields (PRD §F33.4-5 verbatim).

    Phase 17 wire (cj-style 131번째) — scheduled dispatch KST cron output.
    """

    dispatch_id: str  # UUID PK
    tenant_id: str  # UUID (RLS selector)
    dispatch_schedule: str  # weekly/monthly/quarterly/annual
    cron_expression: str  # TEXT e.g. "0 9 * * 1" weekly Mon 09:00 KST
    recipient_strategy: str  # owner_only/sustainability_team/...
    recipient_list: dict[str, Any]  # JSONB
    report_id: str | None  # UUID FK nullable
    status: str  # scheduled/running/completed/failed/cancelled
    scheduled_at: datetime  # TIMESTAMPTZ
    trace_id: str  # TEXT


# 8 NEW sustainability KPI names SSOT (PRD §F33.2 verbatim).
ALL_SUSTAINABILITY_KPI_NAMES: list[str] = [
    "total_carbon_emissions_kgco2e",
    "scope1_emissions_kgco2e",
    "scope2_emissions_kgco2e",
    "scope3_emissions_kgco2e",
    "carbon_intensity_kgco2e_per_krw",
    "data_center_pue",
    "renewable_energy_pct",
    "carbon_offset_kgco2e",
]


__all__ = [
    "SUSTAINABILITY_ENGINE_MODEL_VERSION",
    "SUSTAINABILITY_DEFAULTS",
    "CarbonScopeType",
    "ALL_CARBON_SCOPE_TYPES",
    "CarbonOffsetRegistry",
    "ALL_CARBON_OFFSET_REGISTRIES",
    "SustainabilityCadence",
    "ALL_SUSTAINABILITY_CADENCES",
    "SustainabilityExportFormat",
    "ALL_SUSTAINABILITY_EXPORT_FORMATS",
    "SustainabilityDispatchSchedule",
    "ALL_SUSTAINABILITY_DISPATCH_SCHEDULES",
    "SustainabilityRecipientStrategy",
    "ALL_SUSTAINABILITY_RECIPIENT_STRATEGIES",
    "SustainabilityFramework",
    "ALL_SUSTAINABILITY_FRAMEWORKS",
    "SustainabilityKPIThresholdStatus",
    "ALL_SUSTAINABILITY_KPI_THRESHOLD_STATUSES",
    "CarbonEmissionsRollup",
    "SustainabilityKPIMetric",
    "SustainabilityReport",
    "ScheduledSustainabilityDispatch",
    "ALL_SUSTAINABILITY_KPI_NAMES",
]
