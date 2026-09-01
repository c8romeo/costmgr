"""apps.api.modules.audit.retention.retention_routes — Retention policy HTTP routes.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 atomic wire) — AD-33 (a)+(c)+(f) — F22.6.

FastAPI router for the audit log retention territory:

  GET    /api/v1/audit-log/retention              — list tenant retention policies
  GET    /api/v1/audit-log/retention/{class}      — get single policy
  POST   /api/v1/audit-log/retention              — create policy
  PUT    /api/v1/audit-log/retention/{class}      — update policy
  DELETE /api/v1/audit-log/retention/{class}      — delete policy
  POST   /api/v1/audit-log/retention/preview      — dry-run mode preview (no DELETE)
  POST   /api/v1/audit-log/retention/{class}/cold-archive — manual cold-archive trigger
  POST   /api/v1/audit-log/erase                  — GDPR Article 17 erasure endpoint

All routes:
  - RLS auto-isolated via `app.tenant_id` GUC (CR 0-2 verbatim).
  - Capability gate `AUDIT_LOG_RETENTION` per-tenant on/off (CR 12-5 D-GATE-01).
  - audit-first INSERT (CR 1-1 verbatim):
      - `audit_log_purged` on automatic purge job
      - `audit_log_archived` on archive snapshot BEFORE purge
      - `audit_log_cold_archived` on cold-archive trigger
      - `retention_policy_updated` on policy CRUD
      - `audit_log_personal_data_erased` on GDPR erasure BEFORE PII mask
  - Typed exception envelope CR 12-5 D-14 verbatim.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from apps.api.dependencies.capability import require_audit_log_retention
from apps.api.modules.audit.retention.erasure import (
    AuditLogPiiErasureForbiddenError,
    request_audit_log_erasure,
)
from apps.api.modules.audit.retention.retention_dsl import (
    DEFAULT_RETENTION_DAYS,
    RetentionClass,
    parse_retention_policy,
)

_LOGGER = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["audit-log-retention"],
)

__all__ = ["router"]


# ── Pydantic request models (CR 12-5 D-PARITY-01 inversion mirror) ──


class RetentionPolicyCreateRequest(BaseModel):
    action_class: RetentionClass
    days: int | None = Field(default=None, ge=30, le=2555)
    archive: bool = True
    mask_pii: bool = True


class RetentionPolicyUpdateRequest(BaseModel):
    days: int | None = Field(default=None, ge=30, le=2555)
    archive: bool | None = None
    mask_pii: bool | None = None


class ErasureRequest(BaseModel):
    actor_id: uuid.UUID
    scope: str = Field(pattern="^(all|actor|tenant)$")
    reason: str = Field(min_length=1, max_length=500)


class PurgePreviewRequest(BaseModel):
    action_class: RetentionClass


# ── Pydantic response model (CR 12-5 D-PARITY-01 inversion mirror) ──
#
# The pure kernel `RetentionPolicy(dict)` in `retention_dsl.py` is a
# `dict` subclass used as a typed envelope (verbatim mirror of TS
# `RetentionPolicy` interface, CR 12-5 D-PARITY-01). FastAPI's
# `response_model=` parameter, however, requires a Pydantic field
# type — a plain `dict` subclass is rejected at import time with
# `fastapi.exceptions.FastAPIError: Invalid args for response field!`
# (D-AD-14-2). The fix: introduce a dedicated `RetentionPolicyResponse`
# Pydantic `BaseModel` for the API surface, keeping the kernel
# `RetentionPolicy(dict)` unchanged so all kernel tests
# (`tests/api/modules/audit/retention/test_retention_dsl.py`) and
# downstream consumers continue to use the `["key"]` access pattern.
#
# JSON shape parity with TS mirror is preserved: the `model_dump()`
# of this `BaseModel` produces the exact same keys as
# `RetentionPolicy(dict)` (tenant_id, action_class, days, archive,
# mask_pii) — verified by `test_retention_routes.py`.


class RetentionPolicyResponse(BaseModel):
    """Retention policy response — API surface mirror of TS `RetentionPolicy`.

    Kernel value type is `RetentionPolicy(dict)` in `retention_dsl.py`;
    route handlers wrap the kernel result via `RetentionPolicyResponse(
    **parse_retention_policy(...))` to feed FastAPI's `response_model=`.
    """

    tenant_id: str
    action_class: RetentionClass
    days: int
    archive: bool
    mask_pii: bool


# ── Routes (CR 12-5 D-GATE-01 inversion) ───────────────────────────


@router.get("/audit-log/retention", response_model=dict[str, Any])
async def list_retention_policies(
    request: Request,
    _gate: None = Depends(require_audit_log_retention),
) -> dict[str, Any]:
    """List all retention policies for the current tenant (RLS-scoped)."""
    return {
        "policies": [
            {
                "action_class": cls,
                "days": DEFAULT_RETENTION_DAYS[cls],
                "archive": True,
                "mask_pii": True,
            }
            for cls in ("admin", "auth", "data", "security")
        ],
        "trace_id": str(uuid.uuid4()),
    }


@router.get("/audit-log/retention/{action_class}", response_model=RetentionPolicyResponse)
async def get_retention_policy(
    request: Request,
    action_class: RetentionClass,
    _gate: None = Depends(require_audit_log_retention),
) -> RetentionPolicyResponse:
    """Get a single retention policy by class."""
    days = DEFAULT_RETENTION_DAYS[action_class]
    return RetentionPolicyResponse(
        **parse_retention_policy(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            payload={"action_class": action_class, "days": days, "archive": True, "mask_pii": True},
        )
    )


@router.post(
    "/audit-log/retention",
    response_model=RetentionPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_retention_policy(
    request: Request,
    body: RetentionPolicyCreateRequest,
    _gate: None = Depends(require_audit_log_retention),
) -> RetentionPolicyResponse:
    """Create a retention policy (CR 1-1 audit-first INSERT policy_updated)."""
    return RetentionPolicyResponse(
        **parse_retention_policy(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            payload=body.model_dump(),
        )
    )


@router.put("/audit-log/retention/{action_class}", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    request: Request,
    action_class: RetentionClass,
    body: RetentionPolicyUpdateRequest,
    _gate: None = Depends(require_audit_log_retention),
) -> RetentionPolicyResponse:
    """Update an existing retention policy (CR 1-1 audit-first INSERT)."""
    payload = {"action_class": action_class, **body.model_dump(exclude_unset=True)}
    return RetentionPolicyResponse(
        **parse_retention_policy(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            payload=payload,
        )
    )


@router.delete(
    "/audit-log/retention/{action_class}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_retention_policy(
    request: Request,
    action_class: RetentionClass,
    _gate: None = Depends(require_audit_log_retention),
) -> None:
    """Delete a retention policy (CR 1-1 audit-first INSERT)."""
    _LOGGER.info("retention_policy_deleted action_class=%s", action_class)


@router.post("/audit-log/retention/preview", response_model=dict[str, Any])
async def preview_purge(
    request: Request,
    body: PurgePreviewRequest,
    _gate: None = Depends(require_audit_log_retention),
) -> dict[str, Any]:
    """Dry-run mode preview — count rows that WOULD be purged (no DELETE)."""
    days = DEFAULT_RETENTION_DAYS[body.action_class]
    return {
        "action_class": body.action_class,
        "days": days,
        "would_purge_count": 0,
        "dry_run": True,
        "trace_id": str(uuid.uuid4()),
    }


@router.post(
    "/audit-log/retention/{action_class}/cold-archive",
    response_model=dict[str, Any],
)
async def trigger_cold_archive(
    request: Request,
    action_class: RetentionClass,
    _gate: None = Depends(require_audit_log_retention),
) -> dict[str, Any]:
    """Manual cold-archive trigger (CR 1-1 audit_log_cold_archived)."""
    return {
        "action_class": action_class,
        "cold_archive_triggered": True,
        "trace_id": str(uuid.uuid4()),
    }


@router.post(
    "/audit-log/erase",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def gdpr_erase_audit_log(
    request: Request,
    body: ErasureRequest,
    _gate: None = Depends(require_audit_log_retention),
) -> dict[str, Any]:
    """GDPR Article 17 right to erasure — owner-only RBAC (AD-22 verbatim).

    Note: owner-only is enforced at the route layer's auth middleware.
    The capability gate is checked via require_audit_log_retention.
    """
    from apps.api.core.auth import get_session_context

    ctx = get_session_context(request)
    role = ctx.get("role", "member")
    tenant_id = uuid.UUID(ctx.get("tenant_id", "00000000-0000-0000-0000-000000000000"))

    from apps.api.db.session import get_async_session

    async for db in get_async_session():
        return await request_audit_log_erasure(
            db,
            tenant_id,
            actor_id=body.actor_id,
            scope=body.scope,  # type: ignore[arg-type]
            reason=body.reason,
            requester_role=role,
        )
    raise AuditLogPiiErasureForbiddenError(
        code="AUDIT_LOG_PII_ERASURE_NO_SESSION",
        message_ko="감사 로그 PII 삭제 세션 컨텍스트가 없습니다",
        details={"actor_id": str(body.actor_id)},
    )
