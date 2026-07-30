"""apps.api.core.audit — typed audit log writer (AD-2).

Story 0.2 — Task 7.1.

`emit_audit()` writes a typed `audit_logs` row. Used for non-bypass events
(user login, settings change, etc.) AND for service_role bypass records
(see `apps.api.core.service_role`).

Per AD-2: audit_logs is INSERT-only. Updates and deletes are blocked by
the trigger defined in migration 0001.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import AuditLog


async def emit_audit(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    target_table: str,
    target_id: uuid.UUID | None = None,
    reason: str | None = None,
    payload: dict[str, Any] | None = None,
    tenant_id: uuid.UUID | None = None,
    flush: bool = True,
) -> AuditLog:
    """Insert a typed audit row. Caller commits the transaction.

    Args:
        session: SQLAlchemy 2.0 async session.
        actor_id: User performing the action (NULL for platform/system).
        action: Free-form action label (e.g. 'login', 'settings_update', 'service_role_bypass').
        target_table: Logical table the action targets (e.g. 'tenant_settings', 'users').
        target_id: Row UUID when applicable.
        reason: Free-form reason (required for service_role bypass).
        payload: Structured details (JSONB).
        tenant_id: Tenant scope. NULL for platform-level audit.
        flush: If True, flush to surface constraint errors immediately.

    Returns:
        The persisted AuditLog row (id and occurred_at populated by DB).
    """
    if not target_table:
        raise ValueError("emit_audit: target_table is required (AD-2)")
    if not action:
        raise ValueError("emit_audit: action is required (AD-2)")

    row = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        target_table=target_table,
        target_id=target_id,
        reason=reason,
        payload=payload or {},
        occurred_at=datetime.now(tz=UTC),
    )
    session.add(row)
    if flush:
        await session.flush()
    return row
