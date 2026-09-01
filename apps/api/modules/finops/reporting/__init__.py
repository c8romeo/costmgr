"""apps.api.modules.finops.reporting — FinOps Reporting & Executive Dashboard module.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.1~§F32.8 verbatim + AD-43 (a)~(g) 7 sub-decisions).

This package provides:
- `serializers` — m24_finops_reporting.reporting_serializers NEW
  (Phase 15 wire m23_finops_tag_governance EXTENSION pattern verbatim).
- `executive_dashboard_aggregator` — 5-module cross-join aggregator
  (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast +
  Phase 14 optimization + Phase 15 tag_governance) →
  ExecutiveRollup TypedDict 16 fields.
- `cross_module_kpi` — 8 NEW KPI calculations (total_monthly_cost_krw +
  monthly_cost_growth_pct + cost_per_employee_krw +
  cost_anomaly_count_30d + forecast_deviation_pct +
  idle_cost_monthly_krw + tag_compliance_pct +
  optimization_realized_savings_krw) + KPIMetric TypedDict 8 fields.
- `executive_report_generator` — 3 export_format (PDF + CSV + Excel) +
  3 cadence (monthly + quarterly + annual) + ExecutiveReport
  TypedDict 13 fields + S3 archive + delivery + recipient resolver.
- `scheduled_executive_dispatch` — 4 cron schedules (weekly +
  monthly + quarterly + annual) KST + apscheduler + ScheduledDispatch
  TypedDict 10 fields + lifecycle state machine + idempotency +
  retry policy.

CR lessons applied (17종):
- CR 0-2 RLS — 6 tables + 4 preview tables RLS auto-application.
- CR 1-1 audit-first INSERT — 8 NEW actions via emit_audit_typed.
- CR 4-3/4-4 — ExecutiveRollup golden_diff + tenant-scoped result_hash.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — Client-only dashboard delegation.
- CR 9-6 commit message discipline.
- CR 11-3 honest-DEFER — D-FINOPS-6 honestly DEFER 보존.
- CR 11-4 D-001~D-005 + P-015 — pure validator + SSOT.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- A19 cohesion pattern 9 surface EXTENSION PASS.
- A36 SDR 검증 4-step 자동 적용.
- AD-14 stack pin — Recharts 2.12.7 + slack-sdk==3.23.0 +
  pdpyras==5.2.0 + sendgrid==6.11.0 + reportlab==4.0.7 +
  openpyxl==3.1.2 + apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

from apps.api.modules.finops.reporting.serializers import (
    ALL_CADENCES,
    ALL_DISPATCH_SCHEDULES,
    ALL_EXPORT_FORMATS,
    ALL_KPI_THRESHOLD_STATUSES,
    ALL_RECIPIENT_STRATEGIES,
    ALL_SCOPE_TYPES,
    REPORTING_DEFAULTS,
    REPORTING_ENGINE_MODEL_VERSION,
    ExecutiveReport,
    ExecutiveRollup,
    KPIMetric,
    ScheduledDispatch,
)

__all__ = [
    "REPORTING_ENGINE_MODEL_VERSION",
    "REPORTING_DEFAULTS",
    "ExecutiveRollup",
    "KPIMetric",
    "ExecutiveReport",
    "ScheduledDispatch",
    "ALL_SCOPE_TYPES",
    "ALL_CADENCES",
    "ALL_EXPORT_FORMATS",
    "ALL_DISPATCH_SCHEDULES",
    "ALL_RECIPIENT_STRATEGIES",
    "ALL_KPI_THRESHOLD_STATUSES",
]
