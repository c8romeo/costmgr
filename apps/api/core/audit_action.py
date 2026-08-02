"""apps.api.core.audit_action — single source of truth for audit log actions.

Story 4.3 (A5 spike Phase 1) — Epic 1·2·3·4 CR 1.1 lesson, 4-epic
recurrence pattern. Action values were typed as free-form `str` literals
scattered across 17+ call sites. This module centralizes:

1. `ActionClass` — the audit target class (which table / aggregate)
2. `AuditAction` — the typed verb-subject-context union per ActionClass
3. `AuditLogType` — the destination ledger discriminator
4. `emit_audit_typed()` — typed wrapper that validates (ActionClass, action)
   and routes to the correct destination table.

Per AD-11: this module is in `apps/api/core/` (infra layer). It does NOT
import `packages.cost_engine` directly.

Per AD-22: append-only-leaning preserved. Triggers in migration 0001 still
block UPDATE/DELETE on audit_logs.

Phase 1 (this commit): introduce `audit_action.py` + migrate audit_logs
call sites (17) + CalcLog (3) + `verification_log` (via existing
`_write_verification_log` in `calc_orchestrator.py`). DB schema unchanged
for audit_logs; verification_log gets a CHECK constraint in Alembic 0013.

Phase 2 (Epic 5+): inventory_ledger / reversal_log registry slots pre-fill.
Phase 3 (production data 누적 후): audit_logs / calc_log CHECK additions.
Phase 4 (Epic 5 spec 진입 시): Convention §10 lint + drift detector.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession


# ────────────────────────────────────────────────────────────
# 1. ActionClass — the target class (which table / aggregate)
# ────────────────────────────────────────────────────────────
class ActionClass(str, __import__("enum").Enum):
    """Audit target class. One enum value per logical target.

    Order = introduction order. Do NOT renumber — append-only.
    """

    TENANT_SETTINGS = "tenant_settings"
    SERVICE_ROLE = "service_role"
    UPLOADED_DOCUMENT = "uploaded_document"
    INPUT_DRAFT = "input_draft"
    PRODUCT = "product"
    BOM_LINE = "bom_line"
    MONTHLY_INPUT_ROW = "monthly_input_row"
    MONTHLY_INPUT_PERIOD = "monthly_input_period"
    CALC_LOG = "calc_log"
    VERIFICATION_LOG = "verification_log"  # Story 4.3 (NEW)
    INVENTORY_LEDGER = "inventory_ledger"  # Epic 5 (NEW — slot pre-fill)
    REVERSAL_LOG = "reversal_log"  # Epic 11 (NEW — slot pre-fill)


# ────────────────────────────────────────────────────────────
# 2. AuditLogType — destination ledger discriminator
# ────────────────────────────────────────────────────────────
AuditLogType = Literal[
    "audit_logs",
    "calc_log",
    "verification_log",
    "inventory_ledger",
    "reversal_log",
]


# ────────────────────────────────────────────────────────────
# 3. AuditAction — typed literal per ActionClass
# ────────────────────────────────────────────────────────────
# tenant_settings actions (m0_onboarding + m10_ai company_subblock)
TenantSettingsAction = Literal[
    "industry_selected",  # AC #1 first-time
    "industry_change_initial",  # AC #4 within-grace
    "onboarding_field_saved",  # Story 1.2 fiscal_year_start / currency / language
    "allocation_criterion_saved",  # Story 1.2 allocation_criteria JSONB
    "company_subblock_promoted",  # Story 1.3 confirmed drafts → tenant_settings JSONB
]

# service_role action
ServiceRoleAction = Literal[
    "service_role_bypass",  # AD-2 audit-first guard
]

# uploaded_document actions (m10_ai)
UploadedDocumentAction = Literal[
    "document_uploaded",
    "document_reprocess_requested",
    "document_retention_soft_deleted",
]

# input_draft actions (m10_ai)
InputDraftAction = Literal[
    "input_draft_confirm",
    "input_draft_reject",
]

# product actions (m1_baseline)
ProductAction = Literal[
    "product_created",
    "product_updated",  # mixed PATCH
    "product_type_changed",  # type-only PATCH
    "product_soft_deleted",
    "product_reactivated",
]

# bom_line actions (m1_baseline)
BOMLineAction = Literal[
    "bom_set",  # bulk replace
    "bom_cleared",
]

# monthly_input_row actions (m2_input)
MonthlyInputRowAction = Literal[
    "monthly_input_row_created",
    "monthly_input_row_updated",  # both save_row update + update_row PATCH
    "monthly_input_row_deleted",
]

# monthly_input_period actions (m2_input)
MonthlyInputPeriodAction = Literal[
    "monthly_input_mode_changed",
    # Story 5.1 (Epic 5) — opening carry chain audit-first events.
    # Audit routes to audit_logs (NOT inventory_ledger — that's 5-2).
    "monthly_input_period_opening_carried",  # auto/manual carry applied
    "monthly_input_period_opening_locked",  # first-row lock marker added
]

# calc_log actions (m3_calculate) — DB CHECK constraint applied (0012)
CalcLogAction = Literal[
    "compute",
    "idempotent_skip",
    "rollback",
]

# verification_log actions (Story 4.3 NEW + Story 4.4 forward-lock)
VerificationLogAction = Literal[
    "verification_passed",
    "verification_failed",
    "verification_skipped",
    "verify_v8_golden_match",  # Story 4.4 (V8 골든 mismatch audit-first)
]

# inventory_ledger actions (Epic 5 NEW — design-only placeholder)
# TODO(epic-5): FILL_INVENTORY_LEDGER_ACTIONS when m4_inventory module ships
# Use a placeholder literal until Epic 5 lands (avoid empty Literal syntax).
InventoryLedgerAction = Literal[
    "_placeholder_inventory_ledger",
]

# reversal_log actions (Epic 11 NEW — design-only placeholder)
# TODO(epic-11): FILL_REVERSAL_LOG_ACTIONS when m11_reversal module ships
# Use a placeholder literal until Epic 11 lands (avoid empty Literal syntax).
ReversalLogAction = Literal[
    "_placeholder_reversal_log",
]


# Union type for type checking
AuditAction = (
    TenantSettingsAction
    | ServiceRoleAction
    | UploadedDocumentAction
    | InputDraftAction
    | ProductAction
    | BOMLineAction
    | MonthlyInputRowAction
    | MonthlyInputPeriodAction
    | CalcLogAction
    | VerificationLogAction
    | InventoryLedgerAction
    | ReversalLogAction
)


# ────────────────────────────────────────────────────────────
# 4. Mapping table — ActionClass → AuditLogType + accepted actions
# ────────────────────────────────────────────────────────────
class _ActionRegistry:
    """Internal registry — (ActionClass, AuditAction) → AuditLogType.

    Used by `emit_audit_typed()` to validate action against ActionClass
    and route to the correct destination table.
    """

    _REGISTRY: dict[ActionClass, tuple[AuditLogType, frozenset[str]]] = {
        ActionClass.TENANT_SETTINGS: (
            "audit_logs",
            frozenset(
                {
                    "industry_selected",
                    "industry_change_initial",
                    "onboarding_field_saved",
                    "allocation_criterion_saved",
                    "company_subblock_promoted",
                }
            ),
        ),
        ActionClass.SERVICE_ROLE: ("audit_logs", frozenset({"service_role_bypass"})),
        ActionClass.UPLOADED_DOCUMENT: (
            "audit_logs",
            frozenset(
                {
                    "document_uploaded",
                    "document_reprocess_requested",
                    "document_retention_soft_deleted",
                }
            ),
        ),
        ActionClass.INPUT_DRAFT: (
            "audit_logs",
            frozenset({"input_draft_confirm", "input_draft_reject"}),
        ),
        ActionClass.PRODUCT: (
            "audit_logs",
            frozenset(
                {
                    "product_created",
                    "product_updated",
                    "product_type_changed",
                    "product_soft_deleted",
                    "product_reactivated",
                }
            ),
        ),
        ActionClass.BOM_LINE: ("audit_logs", frozenset({"bom_set", "bom_cleared"})),
        ActionClass.MONTHLY_INPUT_ROW: (
            "audit_logs",
            frozenset(
                {
                    "monthly_input_row_created",
                    "monthly_input_row_updated",
                    "monthly_input_row_deleted",
                }
            ),
        ),
        ActionClass.MONTHLY_INPUT_PERIOD: (
            "audit_logs",
            frozenset(
                {
                    "monthly_input_mode_changed",
                    # Story 5.1 — opening carry chain
                    "monthly_input_period_opening_carried",
                    "monthly_input_period_opening_locked",
                }
            ),
        ),
        ActionClass.CALC_LOG: (
            "calc_log",
            frozenset({"compute", "idempotent_skip", "rollback"}),
        ),
        ActionClass.VERIFICATION_LOG: (
            "verification_log",
            frozenset(
                {
                    "verification_passed",
                    "verification_failed",
                    "verification_skipped",
                    "verify_v8_golden_match",  # Story 4.4 (V8 골든 mismatch audit-first)
                }
            ),
        ),
        # Epic 5 / Epic 11 placeholder — empty until module ships
        ActionClass.INVENTORY_LEDGER: ("inventory_ledger", frozenset()),
        ActionClass.REVERSAL_LOG: ("reversal_log", frozenset()),
    }

    @classmethod
    def validate(cls, *, action_class: ActionClass, action: str) -> AuditLogType:
        """Return destination ledger for (action_class, action). Raise if invalid."""
        if action_class not in cls._REGISTRY:
            raise ValueError(
                f"audit_action: unknown ActionClass {action_class!r}. "
                f"Add to _REGISTRY in apps/api/core/audit_action.py"
            )
        log_type, accepted = cls._REGISTRY[action_class]
        if action not in accepted:
            raise ValueError(
                f"audit_action: action {action!r} is not in ActionClass "
                f"{action_class.value!r}. Accepted: {sorted(accepted)}. "
                f"This is the CR 1.1 lesson — free-form string drift is forbidden."
            )
        return log_type


# ────────────────────────────────────────────────────────────
# 5. Helper — typed emit_audit wrapper
# ────────────────────────────────────────────────────────────
async def emit_audit_typed(
    session: AsyncSession,
    *,
    action_class: ActionClass,
    action: AuditAction,
    actor_id: uuid.UUID | None,
    target_id: uuid.UUID | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    tenant_id: uuid.UUID | None = None,
    flush: bool = True,
) -> None:
    """Typed emit_audit wrapper. Routes to correct destination ledger.

    Args:
        action_class: Which target class (CR 1.1 single source of truth).
        action: Typed action literal. Must match action_class's accepted set.
        actor_id, target_id, reason, payload, tenant_id, flush:
            Same semantics as emit_audit (apps/api/core/audit.py).

    Raises:
        ValueError: If action not in action_class's accepted set.
        NotImplementedError: If action_class routes to a destination
            (calc_log, verification_log, inventory_ledger, reversal_log)
            that is not yet wired through `emit_audit_typed()`. Call sites
            for those classes must use the service-layer writer
            (e.g. `CalcOrchestrator._write_calc_log`).

    Example:
        await emit_audit_typed(
            session,
            action_class=ActionClass.TENANT_SETTINGS,
            action="industry_selected",
            actor_id=actor_id,
            target_id=tenant_id,
            payload={"..."},
            tenant_id=tenant_id,
        )
    """
    log_type = _ActionRegistry.validate(action_class=action_class, action=action)

    if log_type == "audit_logs":
        # delegate to existing emit_audit (apps/api/core/audit.py)
        from apps.api.core.audit import emit_audit

        await emit_audit(
            session,
            actor_id=actor_id,
            action=action,
            target_table=action_class.value,
            target_id=target_id,
            reason=reason,
            payload=payload or {},
            tenant_id=tenant_id,
            flush=flush,
        )
    elif log_type == "calc_log":
        # CalcLog is written via CalcOrchestrator._write_calc_log
        # (m3_calculate/services/calc_orchestrator.py).
        # The service-layer writer owns the typed writer because it
        # requires the orchestrator's session/trace_id context.
        raise NotImplementedError(
            "audit_action: calc_log destination is wired through "
            "CalcOrchestrator._write_calc_log — call site is "
            "apps/api/modules/m3_calculate/services/calc_orchestrator.py"
        )
    elif log_type in ("verification_log", "inventory_ledger", "reversal_log"):
        # verification_log → CalcOrchestrator._write_verification_log (Story 4.3)
        # inventory_ledger → m4_inventory service (Epic 5)
        # reversal_log → m11_reversal service (Epic 11)
        # Each is wired through its domain service, not via emit_audit_typed.
        raise NotImplementedError(
            f"audit_action: {log_type!r} destination is wired through its "
            f"domain service writer — see story spec for wire contract."
        )


__all__ = [
    "ActionClass",
    "AuditAction",
    "AuditLogType",
    "TenantSettingsAction",
    "ServiceRoleAction",
    "UploadedDocumentAction",
    "InputDraftAction",
    "ProductAction",
    "BOMLineAction",
    "MonthlyInputRowAction",
    "MonthlyInputPeriodAction",
    "CalcLogAction",
    "VerificationLogAction",
    "InventoryLedgerAction",
    "ReversalLogAction",
    "emit_audit_typed",
]
