"""apps.api.modules.finops.sustainability — FinOps Sustainability & Carbon Reporting module.

Phase 17 wire (cj-style 131번째) — FinOps Sustainability & Carbon Reporting
territory (PRD §F33.1~§F33.8 verbatim + AD-44 (a)~(g) 7 sub-decisions).

This package provides:
- `serializers` — m25_finops_sustainability.sustainability_serializers NEW
  (Phase 16 wire m24_finops_reporting.reporting_serializers EXTENSION
  pattern verbatim).
- `carbon_emissions_aggregator` — 6-module cross-rollup aggregator
  (Phase 11 showback × carbon_intensity + Phase 12 anomaly + Phase 13
  forecast + Phase 14 optimization + Phase 15 tag_governance + Phase 16
  executive) → CarbonEmissionsRollup TypedDict 14 fields.
- `sustainability_kpi_selector` — 8 NEW KPI calculations
  (total_carbon_emissions_kgco2e + scope1/2/3_emissions_kgco2e +
  carbon_intensity_kgco2e_per_krw + data_center_pue + renewable_energy_pct
  + carbon_offset_kgco2e) + SustainabilityKPIMetric TypedDict 8 fields.
- `sustainability_report_generator` — 3 export_format (PDF + CSV + Excel)
  + 3 cadence (monthly + quarterly + annual) + 5-framework support (CSRD
  + SEC Climate Disclosure + EU Taxonomy + IFRS S2 + KSSB) +
  SustainabilityReport TypedDict 13 fields + S3 archive + delivery +
  recipient resolver.
- `scheduled_sustainability_dispatch` — 4 cron schedules (weekly +
  monthly + quarterly + annual) KST + apscheduler +
  ScheduledSustainabilityDispatch TypedDict 10 fields + lifecycle state
  machine + idempotency + retry policy.

CR lessons applied (17종):
- CR 0-2 RLS — 6 tables + 4 preview tables RLS auto-application.
- CR 1-1 audit-first INSERT — 8 NEW actions via emit_audit_typed.
- CR 4-3/4-4 — CarbonEmissionsRollup golden_diff + tenant-scoped result_hash.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — Client-only dashboard delegation.
- CR 9-6 commit message discipline.
- CR 11-3 honest-DEFER — D-FINOPS-7 honestly DEFER 보존.
- CR 11-4 D-001~D-005 + P-015 — pure validator + SSOT.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- A19 cohesion pattern 9 surface EXTENSION PASS.
- A36 SDR 검증 4-step 자동 적용.
- AD-14 stack pin — Recharts 2.12.7 + slack-sdk==3.23.0 +
  pdpyras==5.2.0 + sendgrid==6.11.0 + reportlab==4.0.7 +
  openpyxl==3.1.2 + pandas==2.1.4 + xlsxwriter==3.1.9 +
  apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-44 FinOps Sustainability & Carbon Reporting 신규 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
"""
from __future__ import annotations

from apps.api.modules.finops.sustainability.serializers import (
    ALL_CARBON_OFFSET_REGISTRIES,
    ALL_CARBON_SCOPE_TYPES,
    ALL_SUSTAINABILITY_CADENCES,
    ALL_SUSTAINABILITY_DISPATCH_SCHEDULES,
    ALL_SUSTAINABILITY_EXPORT_FORMATS,
    ALL_SUSTAINABILITY_FRAMEWORKS,
    ALL_SUSTAINABILITY_KPI_THRESHOLD_STATUSES,
    ALL_SUSTAINABILITY_RECIPIENT_STRATEGIES,
    SUSTAINABILITY_DEFAULTS,
    SUSTAINABILITY_ENGINE_MODEL_VERSION,
    CarbonEmissionsRollup,
    ScheduledSustainabilityDispatch,
    SustainabilityKPIMetric,
    SustainabilityReport,
)

__all__ = [
    "SUSTAINABILITY_ENGINE_MODEL_VERSION",
    "SUSTAINABILITY_DEFAULTS",
    "CarbonEmissionsRollup",
    "SustainabilityKPIMetric",
    "SustainabilityReport",
    "ScheduledSustainabilityDispatch",
    "ALL_CARBON_SCOPE_TYPES",
    "ALL_CARBON_OFFSET_REGISTRIES",
    "ALL_SUSTAINABILITY_CADENCES",
    "ALL_SUSTAINABILITY_EXPORT_FORMATS",
    "ALL_SUSTAINABILITY_DISPATCH_SCHEDULES",
    "ALL_SUSTAINABILITY_RECIPIENT_STRATEGIES",
    "ALL_SUSTAINABILITY_FRAMEWORKS",
    "ALL_SUSTAINABILITY_KPI_THRESHOLD_STATUSES",
]
