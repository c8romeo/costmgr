"""apps.api.modules.finops.pricing — FinOps Pricing, Rate Card & TCO Modeling module.

Phase 19 wire (cj-style 139번째) — FinOps Pricing, Rate Card & TCO
Modeling territory (PRD §F35.1~§F35.8 verbatim + AD-46 (a)~(g) 7
sub-decisions).

This package provides:
- `serializers` — m27_finops_pricing.pricing_serializers NEW
  (Phase 18 wire m26_finops_commitment.commitment_serializers EXTENSION
  pattern verbatim).
- `rate_card_aggregator` — 8-module cross-rollup aggregator
  (Phase 11 showback + Phase 12 anomaly + Phase 13 forecast + Phase 14
  optimization + Phase 15 tag_governance + Phase 16 executive + Phase 17
  sustainability + Phase 18 commitment) + 5-cloud-provider cross-rollup
  (AWS + Azure + GCP + Naver Cloud + KT Cloud) → RateCardInventory
  TypedDict 18 fields.
- `tco_modeling_selector` — 8 NEW KPI calculations
  (total_blended_rate_krw_per_hour + effective_discount_pct +
  tco_1year_commitment_krw + tco_3year_commitment_krw +
  tco_on_demand_krw + cost_per_user_krw + cost_per_transaction_krw +
  unit_economics_score) + TCOKPIBundle TypedDict 10 fields +
  4 industries baseline + break_even_months calculation.
- `pricing_report_generation` — 3 export_format (PDF + CSV + Excel)
  + 3 cadence (monthly + quarterly + annual) + 5-framework support
  (FinOps Foundation + AWS Pricing Models + Azure Pricing Calculator +
  GCP Pricing Calculator + 한국 공공 조달 가격 가이드라인) +
  PricingReport TypedDict 14 fields + S3 archive + delivery +
  recipient resolver.
- `scheduled_pricing_dispatch` — 4 cron schedules (weekly + monthly +
  quarterly + annual) KST + apscheduler +
  ScheduledPricingDispatch TypedDict 11 fields + lifecycle state
  machine + idempotency + retry policy.

CR lessons applied (18종):
- CR 0-2 RLS — 6 tables + 4 preview tables RLS auto-application.
- CR 1-1 audit-first INSERT — 8 NEW actions via emit_audit_typed.
- CR 4-3/4-4 — RateCardInventory golden_diff + tenant-scoped result_hash.
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
- AD-14 stack pin — Recharts 2.12.7 + reportlab==4.0.7 +
  openpyxl==3.1.2 + pandas==2.1.4 + xlsxwriter==3.1.9 +
  apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- AD-46 FinOps Pricing, Rate Card & TCO Modeling 신규 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

from apps.api.modules.finops.pricing.serializers import (
    ALL_PRICING_CADENCES,
    ALL_PRICING_CLOUD_PROVIDERS,
    ALL_PRICING_DISPATCH_SCHEDULES,
    ALL_PRICING_EXPORT_FORMATS,
    ALL_PRICING_FRAMEWORKS,
    ALL_PRICING_KPI_NAMES,
    ALL_PRICING_KPI_THRESHOLD_STATUSES,
    ALL_PRICING_MODELS,
    ALL_PRICING_RECIPIENT_STRATEGIES,
    ALL_PRICING_SCOPE_TYPES,
    ALL_PRICING_UNIT_METRICS,
    PRICING_DEFAULTS,
    PRICING_ENGINE_MODEL_VERSION,
    PricingReport,
    RateCardInventory,
    ScheduledPricingDispatch,
    TCOKPIBundle,
)

__all__ = [
    "PRICING_ENGINE_MODEL_VERSION",
    "PRICING_DEFAULTS",
    "RateCardInventory",
    "TCOKPIBundle",
    "PricingReport",
    "ScheduledPricingDispatch",
    "ALL_PRICING_SCOPE_TYPES",
    "ALL_PRICING_CLOUD_PROVIDERS",
    "ALL_PRICING_MODELS",
    "ALL_PRICING_UNIT_METRICS",
    "ALL_PRICING_CADENCES",
    "ALL_PRICING_DISPATCH_SCHEDULES",
    "ALL_PRICING_RECIPIENT_STRATEGIES",
    "ALL_PRICING_EXPORT_FORMATS",
    "ALL_PRICING_FRAMEWORKS",
    "ALL_PRICING_KPI_THRESHOLD_STATUSES",
    "ALL_PRICING_KPI_NAMES",
]
