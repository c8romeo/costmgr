"""apps.api.modules.finops.commitment — FinOps Cloud Commitment Management (RIs/SPs/CUDs) module.

Phase 18 wire (cj-style 135번째) — FinOps Cloud Commitment Management
territory (PRD §F34.1~§F34.8 verbatim + AD-45 (a)~(g) 7 sub-decisions).

This package provides:
- `serializers` — m26_finops_commitment.commitment_serializers NEW
  (Phase 17 wire m25_finops_sustainability.sustainability_serializers EXTENSION
  pattern verbatim).
- `commitment_inventory_aggregator` — 7-module cross-rollup aggregator
  (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast + Phase 14
  optimization + Phase 15 tag_governance + Phase 16 executive + Phase 17
  sustainability) + 5-cloud-provider cross-rollup (AWS + Azure + GCP +
  Naver Cloud + KT Cloud) → CommitmentInventoryRollup TypedDict 16 fields.
- `commitment_kpi_selector` — 8 NEW KPI calculations
  (total_commitment_value_krw + coverage_pct + utilization_pct +
  expiring_commitments_30d + recommended_purchase_krw +
  savings_realized_krw + idle_commitment_krw + renewal_decision_score)
  + CommitmentKPI TypedDict 16 fields.
- `commitment_report_generation` — 3 export_format (PDF + CSV + Excel)
  + 3 cadence (monthly + quarterly + annual) + 5-framework support
  (FinOps Foundation + AWS Cost Optimization Pillar + Azure Cost
  Optimization + GCP Cost Optimization + 한국 조달청 클라우드 commitment
  가이드라인) + CommitmentReport TypedDict 14 fields + S3 archive +
  delivery + recipient resolver.
- `scheduled_commitment_dispatch` — 4 cron schedules (weekly +
  monthly + quarterly + annual) KST + apscheduler +
  ScheduledCommitmentDispatch TypedDict 10 fields + lifecycle state
  machine + idempotency + retry policy.

CR lessons applied (18종):
- CR 0-2 RLS — 6 tables + 4 preview tables RLS auto-application.
- CR 1-1 audit-first INSERT — 8 NEW actions via emit_audit_typed.
- CR 4-3/4-4 — CommitmentInventoryRollup golden_diff + tenant-scoped result_hash.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — Client-only dashboard delegation.
- CR 9-6 commit message discipline.
- CR 11-3 honest-DEFER — D-FINOPS-8 honestly DEFER 보존.
- CR 11-4 D-001~D-005 + P-015 — pure validator + SSOT.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- A19 cohesion pattern 9 surface EXTENSION PASS.
- A36 SDR 검증 4-step 자동 적용.
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 +
  openpyxl==3.1.2 + pandas==2.1.4 + xlsxwriter==3.1.9 +
  apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-45 FinOps Cloud Commitment Management 신규 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

from apps.api.modules.finops.commitment.serializers import (
    ALL_COMMITMENT_CLOUD_PROVIDERS,
    ALL_COMMITMENT_COMMITMENT_TYPES,
    ALL_COMMITMENT_DISPATCH_SCHEDULES,
    ALL_COMMITMENT_EXPORT_FORMATS,
    ALL_COMMITMENT_FRAMEWORKS,
    ALL_COMMITMENT_KPI_THRESHOLD_STATUSES,
    ALL_COMMITMENT_RECIPIENT_STRATEGIES,
    ALL_COMMITMENT_SCOPE_TYPES,
    ALL_COMMITMENT_TERMS,
    COMMITMENT_DEFAULTS,
    COMMITMENT_ENGINE_MODEL_VERSION,
    CommitmentInventoryRollup,
    CommitmentKPI,
    CommitmentReport,
    ScheduledCommitmentDispatch,
)

__all__ = [
    "COMMITMENT_ENGINE_MODEL_VERSION",
    "COMMITMENT_DEFAULTS",
    "CommitmentInventoryRollup",
    "CommitmentKPI",
    "CommitmentReport",
    "ScheduledCommitmentDispatch",
    "ALL_COMMITMENT_SCOPE_TYPES",
    "ALL_COMMITMENT_CLOUD_PROVIDERS",
    "ALL_COMMITMENT_COMMITMENT_TYPES",
    "ALL_COMMITMENT_TERMS",
    "ALL_COMMITMENT_DISPATCH_SCHEDULES",
    "ALL_COMMITMENT_RECIPIENT_STRATEGIES",
    "ALL_COMMITMENT_EXPORT_FORMATS",
    "ALL_COMMITMENT_FRAMEWORKS",
    "ALL_COMMITMENT_KPI_THRESHOLD_STATUSES",
]
