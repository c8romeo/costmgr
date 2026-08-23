"""apps.api.modules.finops — FinOps Showback / Chargeback territory.

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.1~§F27.7 + AD-38 (a)~(g) sub-decisions).

This package provides:
- `showback_dsl` — ShowbackDefinition TypedDict (13 fields) + 5 group_by
  options + 6 period selector modes + comparison view + currency
  formatting + tenant-scoped override + audit-first INSERT
  `showback_generated`.
- `showback_query` — DepartmentBreakdown TypedDict (8 fields) +
  ComparisonView TypedDict (7 fields) + query_showback_breakdown +
  query_showback_comparison + pagination.
- `chargeback_engine` — ChargebackRule TypedDict (6 fields) +
  compute_chargeback + 3 rule types (flat_fee / proportional_allocation
  / metered) + markup + tax + multi-region aggregation.
- `chargeback_rule_evaluator` — evaluate_chargeback_rule +
  ChargebackRuleInvalidError + ChargebackCalculationError.
- `department_mapping` — department_id ↔ cost_center_id 1:1 mapping +
  validate_department_mapping + auto-create on first calculation +
  audit-first INSERT `department_mapping_updated`.
- `chargeback_export` — export_chargeback_csv StreamingResponse +
  export_chargeback_pdf + rate limit + audit-first INSERT
  `chargeback_exported`.
- `serializers` — m19_finops.finops_serializers module version SSOT.

CR lessons applied:
- CR 0-2 RLS — every ShowbackDefinition + ChargebackRule carries
  tenant_id selector + every FinOps event goes through cross-tenant
  isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to 3 NEW actions (showback_generated +
  department_mapping_updated + chargeback_exported).
- CR 4-3/4-4 — showback baseline + chargeback baseline 30d rolling +
  golden_diff pattern verbatim 미러 (Phase 8 baseline freeze
  pattern carry-over).
- CR 1-1 ContextVar — trace_id request-scoped ContextVar binding.
- CR 1-1 RSC boundary — finops dashboard client/server separation.
- CR 9-6 commit message — `git commit -F <file>` usage.
- CR 11-3 honest-DEFER — 107번째 epic 연속 정직 회복.
- CR 12-1 L4 industry-agnostic — FINOPS_SHOWBACK + FINOPS_CHARGEBACK
  4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 6 NEW typed exception
  classes (ShowbackDefinitionInvalidError + ShowbackExportError +
  ChargebackRuleInvalidError + ChargebackCalculationError +
  ChargebackExportError + ChargebackExportRateLimitedError).
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity shared via CR 12-5 D-PARITY-01 verification tests.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only
  RBAC.

AD-14 stack pin — pandas + reportlab + jinja2 + openpyxl + pdfkit +
weasyprint + python-magic (Phase 10 stack pin EXTENSION).

AD-22 owner-only RBAC — showback generation + chargeback issue +
department mapping update + cost pool recalculation + CSV/PDF
export all owner-only + Epic 12 2FA 챌린지 mandatory.

NFR4 PII minimization PRESERVED — showback/chargeback data contains
only business metrics + cost amounts (no PII).

A19 cohesion pattern 9 surface EXTENSION PASS — FinOps showback/
chargeback surface NEW = F27.1~F27.7 territory.
"""
from __future__ import annotations

__all__ = []