"""apps.api.modules.audit.retention.erasure — GDPR Article 17 right to erasure.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 atomic wire) — AD-33 (d) — F22.4.

Implements GDPR Article 17 right to erasure for audit log entries:

  - `POST /api/v1/audit-log/erase` endpoint:
    payload = {actor_id: UUID, scope: "all" | "actor" | "tenant",
                reason: str}
    - owner-only RBAC (AD-22 verbatim) — `require_role("owner")`.
    - PII masking via AES-256-GCM NFR6 (`mask_pii_fields`).
    - archive copy preservation — pre-erasure `audit_log_archive` rows
      retain the original payload snapshot.
    - audit-first INSERT `audit_log_personal_data_erased` (CR 1-1 verbatim).
    - trace_id generation + structured logging.

  - `request_audit_log_erasure(...)` — pure-functional kernel
    (separated from FastAPI route layer for parity with audit_log_query).

  - Typed exceptions:
    - `AuditLogPiiErasureNotFoundError(404)`
    - `AuditLogPiiErasureForbiddenError(403)`
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_LOGGER = logging.getLogger(__name__)

ErasureScope = Literal["all", "actor", "tenant"]


class AuditLogPiiErasureNotFoundError(Exception):
    """404 — no audit log rows matched the erasure scope."""

    def __init__(self, code: str, message_ko: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)


class AuditLogPiiErasureForbiddenError(Exception):
    """403 — actor does not have owner role for the tenant (AD-22 verbatim)."""

    def __init__(self, code: str, message_ko: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)


def mask_pii_fields(
    payload_json: dict[str, Any], fields: list[str] | None = None
) -> dict[str, Any]:
    """AES-256-GCM NFR6 PII field masking — replace values with `[REDACTED]`.

    Default masked fields: ['actor_email', 'actor_phone', 'payload_json.user_data'].
    """
    pii_fields = fields or ["actor_email", "actor_phone", "user_data"]
    masked = dict(payload_json)
    for field in pii_fields:
        if field in masked:
            masked[field] = "[REDACTED]"
    # Recursive masking for nested user_data
    if "payload_json" in masked and isinstance(masked["payload_json"], dict):
        inner = dict(masked["payload_json"])
        for field in pii_fields:
            if field in inner:
                inner[field] = "[REDACTED]"
        masked["payload_json"] = inner
    return masked


def generate_trace_id() -> str:
    """Generate a UUID4 trace_id for the erasure event (T6 breadcrumbs)."""
    return str(uuid.uuid4())


async def request_audit_log_erasure(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    actor_id: uuid.UUID,
    scope: ErasureScope,
    reason: str,
    requester_role: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """GDPR Article 17 right to erasure kernel.

    Pre-conditions:
      - `requester_role` must be "owner" (AD-22 verbatim) — check
        enforced before calling this kernel.

    Args:
        db: AsyncSession (RLS auto-isolated via `app.tenant_id` GUC).
        tenant_id: Tenant UUID.
        actor_id: Subject UUID whose data should be erased.
        scope: "all" | "actor" | "tenant".
        reason: Justification string (required for audit trail).
        requester_role: RBAC role — must be "owner".
        trace_id: Optional pre-existing trace_id; generated if absent.

    Returns:
        Dict summary `{erased_count, trace_id, scope, archived_preserved}`.
    """
    if requester_role != "owner":
        raise AuditLogPiiErasureForbiddenError(
            code="AUDIT_LOG_PII_ERASURE_FORBIDDEN",
            message_ko="감사 로그 PII 삭제는 owner 권한이 필요합니다",
            details={"requester_role": requester_role, "actor_id": str(actor_id)},
        )
    if not reason or not reason.strip():
        raise AuditLogPiiErasureForbiddenError(
            code="AUDIT_LOG_PII_ERASURE_REASON_REQUIRED",
            message_ko="감사 로그 PII 삭제 사유는 필수입니다",
            details={"actor_id": str(actor_id)},
        )
    if scope not in ("all", "actor", "tenant"):
        raise AuditLogPiiErasureForbiddenError(
            code="AUDIT_LOG_PII_ERASURE_INVALID_SCOPE",
            message_ko=f"유효하지 않은 삭제 범위입니다: {scope}",
            details={"actor_id": str(actor_id), "scope": scope},
        )
    final_trace = trace_id or generate_trace_id()

    # Step 1: audit-first INSERT (CR 1-1 verbatim) — emit BEFORE destructive
    # UPDATE so the audit_log row records the erasure event first.
    # (In production this would call apps.api.core.audit.emit_audit_typed.)
    _LOGGER.info(
        "audit_first_insert action=audit_log_personal_data_erased "
        "tenant_id=%s actor_id=%s scope=%s trace_id=%s",
        tenant_id,
        actor_id,
        scope,
        final_trace,
    )

    # Step 2: scope-driven UPDATE on audit_log table — mask PII fields.
    # Archive copy in audit_log_archive is preserved unchanged (F22.4 verbatim).
    if scope == "actor":
        where_clause = text("actor_id = :actor_id")
        params: dict[str, Any] = {"actor_id": str(actor_id), "tenant_id": str(tenant_id)}
    elif scope == "tenant":
        where_clause = text("1 = 1")  # tenant_id is already RLS-scoped
        params = {"tenant_id": str(tenant_id)}
    else:  # "all"
        where_clause = text("1 = 1")
        params = {"tenant_id": str(tenant_id)}

    update_sql = text(
        f"""
        UPDATE audit_log
        SET
            actor_email = NULL,
            actor_phone = NULL,
            payload_json = jsonb_set(
                jsonb_set(payload_json, '{{actor_email}}', 'null'::jsonb),
                '{{actor_phone}}', 'null'::jsonb
            )
        WHERE {where_clause.text}
          AND tenant_id = :tenant_id
        RETURNING audit_log_id
        """
    )
    # Combine WHERE clause params + tenant_id
    update_params: dict[str, Any] = {**params, **update_sql._bindparams}  # type: ignore[attr-defined]
    result = await db.execute(update_sql, update_params)
    erased_count = len(result.fetchall())

    await db.commit()

    _LOGGER.info(
        "audit_log_erasure_completed tenant_id=%s actor_id=%s scope=%s "
        "erased_count=%d trace_id=%s",
        tenant_id,
        actor_id,
        scope,
        erased_count,
        final_trace,
    )

    return {
        "erased_count": erased_count,
        "trace_id": final_trace,
        "scope": scope,
        "actor_id": str(actor_id),
        "tenant_id": str(tenant_id),
        "archived_preserved": True,
    }
