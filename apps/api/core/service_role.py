"""apps.api.core.service_role — bypass guard (AD-3, AD-2).

Story 0.2 — Task 7.2 ~ 7.4.

`service_role` JWTs bypass RLS by default in Supabase. This module is the
SINGLE entry point for service_role-backed writes. Every bypass writes a
typed `audit_logs` row in a SEPARATE TRANSACTION that is COMMITTED
BEFORE the privileged action runs. If the audit insert fails, the
action is aborted (audit-first guarantee). If the action's transaction
subsequently rolls back, the audit row survives — providing tamper-
evident traceability (AD-2 / compliance).

Usage:

    async def backfill_settings(tenant_id: UUID) -> None:
        async with with_service_role(
            actor_id=SYSTEM_ACTOR_ID,
            reason="backfill tenant_settings.onboarding defaults",
            target_table="tenant_settings",
        ) as ctx:
            await ctx.session.execute(...)

    async with with_service_role(
        actor_id=current_user_id,
        reason="force-recalculate for tenant due to correction",
        target_table="tenant_settings",
    ) as ctx:
        await ctx.session.execute(...)

Anti-pattern guard (Task 7.4): `grep -r 'service_role' apps/api/ --include="*.py"`
should only return references inside this module. CI enforces this.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db import get_session
from apps.api.core.db_models import AuditLog

# Sentinel for platform-initiated actions (no human actor)
SYSTEM_ACTOR_ID: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


@dataclass
class ServiceRoleContext:
    """Context exposed to the wrapped action."""

    session: AsyncSession
    audit_row: AuditLog


@asynccontextmanager
async def with_service_role(
    *,
    actor_id: uuid.UUID,
    reason: str,
    target_table: str,
    target_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    tenant_id: uuid.UUID | None = None,
) -> AsyncIterator[ServiceRoleContext]:
    """Run a privileged action under service_role, with audit-first guarantee.

    Step 1: open a SHORT-LIVED session, insert the audit row, COMMIT it.
            The audit row is now durable — it survives any action rollback.
    Step 2: open a SECOND session for the privileged action; yield to caller.
    Step 3: caller commits/rolls back the action session; exceptions propagate.

    Rationale (per CR 2026-07-25, decision AUDIT-1): sharing a single
    transaction between audit and action meant an action rollback erased
    the audit evidence — defeating AD-2 compliance. Two separate
    transactions guarantee audit durability.

    Args:
        actor_id: UUID of the user authorizing the bypass (required).
        reason: Human-readable reason (required).
        target_table: Logical table the action targets (required).
        target_id: Optional row UUID.
        payload: Optional structured details.
        tenant_id: Tenant scope (NULL for cross-tenant ops).

    Raises:
        ValueError: missing required fields.
        sqlalchemy.exc.SQLAlchemyError: if audit insert fails — action is NOT run.
    """
    if actor_id is None:
        raise ValueError("with_service_role: actor_id is required (AD-2 audit)")
    if not reason:
        raise ValueError("with_service_role: reason is required (AD-2 audit)")
    if not target_table:
        raise ValueError("with_service_role: target_table is required (AD-2 audit)")

    # ── Step 1: write + commit audit in its own transaction ─────
    audit_row: AuditLog | None = None
    async for audit_session in get_session():
        # Story 4.3 (A5 Phase 1) — typed emit wrapper. action_class
        # SERVICE_ROLE routes to audit_logs with target_table='service_role'.
        # The caller-supplied `target_table` param is preserved for the
        # specific breached row (e.g. 'tenant_settings') and recorded
        # in `payload` to keep the audit trail self-describing.
        await emit_audit_typed(
            audit_session,
            action_class=ActionClass.SERVICE_ROLE,
            action="service_role_bypass",
            actor_id=actor_id,
            target_id=target_id,
            reason=reason,
            payload={
                **(payload or {}),
                "bypass_target_table": target_table,
            },
            tenant_id=tenant_id,
            flush=True,
        )
        # Re-fetch the AuditLog row to populate context.audit_row
        # (the same lookup pattern emit_audit() used).
        from sqlalchemy import select

        stmt = (
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id, AuditLog.action == "service_role_bypass")
            .order_by(AuditLog.occurred_at.desc())
            .limit(1)
        )
        result = await audit_session.execute(stmt)
        audit_row = result.scalar_one()
        await audit_session.commit()
        break  # single iteration — close this session

    assert audit_row is not None  # emit_audit_typed always persists the row

    # ── Step 2: open a fresh session for the privileged action ───
    async for action_session in get_session():
        try:
            yield ServiceRoleContext(session=action_session, audit_row=audit_row)
        except Exception:
            await action_session.rollback()
            raise


# ── Functional helper (Task 9.1 alternative) ────────────────
async def run_with_service_role(
    *,
    actor_id: uuid.UUID,
    reason: str,
    target_table: str,
    action: Callable[[AsyncSession], Awaitable[Any]],
    target_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    tenant_id: uuid.UUID | None = None,
) -> Any:
    """Functional wrapper — runs `action` inside the service_role context.

    The audit insert is committed BEFORE `action` runs (in a separate
    transaction). If the audit insert fails, `action` is NOT invoked
    (audit-first guarantee).
    """
    async with with_service_role(
        actor_id=actor_id,
        reason=reason,
        target_table=target_table,
        target_id=target_id,
        payload=payload,
        tenant_id=tenant_id,
    ) as ctx:
        return await action(ctx.session)
