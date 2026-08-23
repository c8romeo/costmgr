"""apps.api.modules.slo — SLO Engineering / Error Budget Management territory.

Phase 10 (cj-style 103번째 wire) — SLO Engineering / Error Budget
Management (PRD §F26.1~§F26.7 + AD-37 (a)~(g) sub-decisions).

This package provides:
- `slo_dsl` — SloDefinition TypedDict (13 fields) + SLI types + windows +
  burn_rate_threshold + error_budget_policy + regions + multi_region
  aggregation + freeze + auto-rollback + governance_required.
- `slo_burn_rate_evaluator` — Google SRE Workbook verbatim 4 windows
  (fast 1h 14.4x + slow 6h 6x + exhaustion 24h 3x + long 3d 1x) +
  composite alert + 2min cadence evaluator.
- `error_budget` — ErrorBudget TypedDict (8 fields) + freeze mechanism +
  exhaustion prediction.
- `multi_region_aggregator` — MultiRegionSloAggregate TypedDict (7 fields)
  + region_weight_map + replication_lag weighted adjustment + tenant
  scoped override.
- `governance` — GovernanceReview TypedDict + auto-rollback SLO breach
  trigger 4 conditions + Phase 9 chaos_experiment auto-rollback
  integration.
- `tenant_scoping` — tenant_id selector + cross-tenant isolation
  verification + tenant-scoped override enforcement.

CR lessons applied:
- CR 0-2 RLS — every SloDefinition carries tenant_id selector + every
  SLO event goes through cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to 3 NEW actions (slo_target_updated + slo_budget_exhausted +
  slo_violation_detected).
- CR 4-3/4-4 — slo_definitions baseline + error_budget baseline 30d
  rolling + golden_diff pattern verbatim 미러 (Phase 8 baseline freeze
  pattern carry-over).
- CR 1-1 ContextVar lesson — trace_id request-scoped ContextVar binding.
- CR 1-1 RSC boundary — slo dashboard client/server separation.
- CR 9-6 commit message — `git commit -F <file>` usage.
- CR 11-3 honest-DEFER — 103번째 epic 연속 정직 회복.
- CR 12-1 L4 industry-agnostic — SLO_ENGINEERING 4-industry grants
  ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 5 NEW typed exception classes
  (SloDefinitionInvalidError + SloOverrideConflictError +
  SloBudgetExhaustedError + SloViolationDetectedError +
  SloGovernanceRequiredForbiddenError).
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity
  shared via CR 12-5 D-PARITY-01 verification tests.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only RBAC.

AD-14 stack pin — prometheus_client + alertmanager + slack_sdk +
pagerduty + libfaketime.

AD-22 owner-only RBAC — SLO creation/update/delete + freeze + unfreeze
+ override + auto-rollback trigger all owner-only + Epic 12 2FA 챌린지
mandatory when governance_required=True.

NFR4 PII minimization PRESERVED — slo_data contains only business
metrics + burn-rate (no PII).

A19 cohesion pattern 9 surface EXTENSION PASS — SLO engineering surface
NEW = F26.1~F26.7 territory.
"""
from __future__ import annotations

__all__ = []
