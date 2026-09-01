"""apps.api.modules.finops.chargeback_settlement — Phase 22 FinOps Chargeback Settlement module.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement territory
(PRD §F38.1~§F38.8 verbatim + AD-50 (a)~(g) 7 sub-decisions).

5-NEW backend settlement modules + scheduled dispatch job + FastAPI router:
1. `settlement_rules.py` — settlement_rules engine + 5-module cross-join
2. `allocation_engine.py` — 5-dim weighted allocation + Decimal precision
3. `invoice_generator.py` — PDF/XLSX/CSV template (AD-14 stack pin)
4. `reconciliation.py` — 3-way match + 1.0% tolerance + 3 auto-retries
5. `scheduled_chargeback_settlement_dispatch.py` — apscheduler + 4 cadence KST
6. `chargeback_settlement_routes.py` — FastAPI router 9 endpoints

Module tag: `m30_finops_chargeback_settlement`
ALLOWED_SERVICE_SUBMODULES EXTENSION 신규 결정 wire
(Phase 21 m21_finops_reserved_capacity 패턴 verbatim mirror).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW audit actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 idempotent no-op — duplicate dispatch cached.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-2 AUTHORIZABLE_TARGET_EVENT_TYPES — auth-layer check.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — TypeScript mirror parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — reportlab 4.0.7 + xlsxwriter 3.1.9 + apscheduler 3.10.4 + noto-sans-cjk-kr.
- AD-22 owner-only RBAC.
- AD-50 (a)~(g) 7 sub-decisions.
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""

from __future__ import annotations

from apps.api.modules.finops.chargeback_settlement.allocation_engine import (
    ALLOCATION_AMOUNT_QUANTUM,
    ALLOCATION_DIMENSION_WEIGHT_SUM,
    aggregate_allocation_breakdown,
    compute_allocation,
    validate_allocation_lines,
)
from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
    router as chargeback_settlement_router,
)
from apps.api.modules.finops.chargeback_settlement.invoice_generator import (
    PDF_MARGIN_PT,
    PDF_PAGE_HEIGHT_PT,
    PDF_PAGE_WIDTH_PT,
    generate_invoice,
    validate_invoice_format,
)
from apps.api.modules.finops.chargeback_settlement.reconciliation import (
    ALL_RECONCILIATION_STATUSES,
    RECONCILIATION_STATUS_MATCHED,
    RECONCILIATION_STATUS_NEEDS_APPROVAL,
    RECONCILIATION_STATUS_RETRY_EXHAUSTED,
    RECONCILIATION_STATUS_VARIANCE_DETECTED,
    reconcile_settlement,
    validate_reconciliation_result,
)
from apps.api.modules.finops.chargeback_settlement.scheduled_chargeback_settlement_dispatch import (
    ALL_SETTLEMENT_CADENCES,
    compute_settlement_result,
    execute_dispatch,
    schedule_cadence_dispatch,
    validate_cadence,
)
from apps.api.modules.finops.chargeback_settlement.serializers import (
    ALL_ALLOCATION_DIMENSIONS,
    ALL_INVOICE_FORMATS,
    ALL_SETTLEMENT_RULE_TYPES,
    ALL_SETTLEMENT_STATUSES,
    ALLOCATION_DIMENSION_WEIGHTS,
    CHARGEBACK_SETTLEMENT_DEFAULTS,
    CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    FIVE_MODULE_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_ALLOCATION_LINES,
    MAX_INVOICE_BYTES,
    RECONCILIATION_AMOUNT_TOLERANCE_KRW,
    RECONCILIATION_MAX_RETRIES,
    RECONCILIATION_TOLERANCE_PCT,
    SETTLEMENT_CADENCE_HOURS_KST,
    SETTLEMENT_RECIPIENT_TEMPLATES,
    AllocationDimension,
    AllocationLine,
    InvoiceFormat,
    ReconciliationResult,
    SettlementResult,
    SettlementRule,
    SettlementRuleType,
    SettlementStatus,
)
from apps.api.modules.finops.chargeback_settlement.settlement_rules import (
    FIVE_MODULE_WEIGHT_SUM,
    create_settlement_rule,
    list_settlement_rules,
    update_settlement_rule,
    validate_settlement_rule,
)

__all__ = [
    # Module constants
    "ALLOCATION_AMOUNT_QUANTUM",
    "ALLOCATION_DIMENSION_WEIGHT_SUM",
    "ALL_RECONCILIATION_STATUSES",
    "ALL_SETTLEMENT_CADENCES",
    "ALL_ALLOCATION_DIMENSIONS",
    "ALL_INVOICE_FORMATS",
    "ALL_SETTLEMENT_RULE_TYPES",
    "ALL_SETTLEMENT_STATUSES",
    "ALLOCATION_DIMENSION_WEIGHTS",
    "CHARGEBACK_SETTLEMENT_DEFAULTS",
    "CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION",
    "FIVE_MODULE_WEIGHT_SUM",
    "FIVE_MODULE_WEIGHTS",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "MAX_ALLOCATION_LINES",
    "MAX_INVOICE_BYTES",
    "PDF_MARGIN_PT",
    "PDF_PAGE_HEIGHT_PT",
    "PDF_PAGE_WIDTH_PT",
    "RECONCILIATION_AMOUNT_TOLERANCE_KRW",
    "RECONCILIATION_MAX_RETRIES",
    "RECONCILIATION_STATUS_MATCHED",
    "RECONCILIATION_STATUS_NEEDS_APPROVAL",
    "RECONCILIATION_STATUS_RETRY_EXHAUSTED",
    "RECONCILIATION_STATUS_VARIANCE_DETECTED",
    "RECONCILIATION_TOLERANCE_PCT",
    "SETTLEMENT_CADENCE_HOURS_KST",
    "SETTLEMENT_RECIPIENT_TEMPLATES",
    # Enums
    "AllocationDimension",
    "InvoiceFormat",
    "SettlementRuleType",
    "SettlementStatus",
    # TypedDicts
    "AllocationLine",
    "ReconciliationResult",
    "SettlementResult",
    "SettlementRule",
    # Settlement rules
    "create_settlement_rule",
    "update_settlement_rule",
    "list_settlement_rules",
    "validate_settlement_rule",
    # Allocation engine
    "compute_allocation",
    "validate_allocation_lines",
    "aggregate_allocation_breakdown",
    # Invoice generator
    "generate_invoice",
    "validate_invoice_format",
    # Reconciliation
    "reconcile_settlement",
    "validate_reconciliation_result",
    # Scheduled dispatch
    "compute_settlement_result",
    "schedule_cadence_dispatch",
    "execute_dispatch",
    "validate_cadence",
    # Router
    "chargeback_settlement_router",
]
