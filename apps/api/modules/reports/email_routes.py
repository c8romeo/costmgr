"""apps.api.modules.reports.email_routes — Story 30.3 Email delivery endpoint.

cj-299 wire sprint (cj-style 299번째 epic 연속 정직 회복 source+docs atomic single
sprint) — Story 30.3 Email delivery (FR-30-3).

1 route (mounted at `/api/v1/`):
  1. POST /api/v1/exports/email
     Body (EmailExportRequest JSON):
       {
         "type": "cost-records" | "bom",
         "period": "YYYY-MM",
         "tenant_id": "uuid",
         "recipients": ["email1", "email2", ...],   // 1~10
         "subject": "이메일 제목 (1~200자)",
         "pii_redaction_enabled": true,              // default true (NFR4)
         "message": "선택적 추가 메시지"               // optional
       }
     Response (EmailDeliveryResult JSON):
       {
         "delivery_id": "Postmark MessageID | SMTP correlation | log-{uuid}",
         "status": "delivered" | "queued" | "failed",
         "recipient_count": 2,
         "retry_count": 0,                            // 0~3
         "delivered_at": "2026-09-06T12:34:56Z",
         "pii_redacted_fields": ["phone", "email"],
         "trace_id": "trace-abc-123"
       }

CR 0-2 RLS lesson: tenant context (GUC `app.tenant_id`) is auto-applied
via `get_tenant_context` dep — no manual SET LOCAL needed.
CR 1-1 audit-first: 1 NEW audit log row `export_email` INSERTed
BEFORE the SMTP dispatch (T5 verbatim).
CR 12-5 D-14 typed exception envelope for 4 NEW error classes.

Verbatim mirror of `apps/api/modules/reports/csv_routes.py` for:
  - APIRouter setup + AD-22 owner/admin RBAC + Capability.EXPORT_EMAIL gate
  - TenantContext cross-tenant check
  - Audit-first INSERT `export_email` (CR 1-1 verbatim + ActionClass.REPORTS)
  - Typed exception base class + 4 subclasses (CR 12-5 D-14 envelope)

AD bind 3/3:
- AD-2 (audit-first INSERT append-only)
- AD-10 (identity + 2FA via owner-only RBAC, AD-22 owner-only)
- AD-12 (verify-first capability gate, in-route. Capability.EXPORT_EMAIL — cj-285
  EXTENSION 보존, capability matrix v1.54)

NFR bind 3/7 active:
- NFR4 (PII minimization) — email_service.redact_pii() before dispatch
- NFR5 (page load P95 ≤ 5s) — async dispatch + retry 3회 with exponential backoff
- NFR18 (ko-KR vocabulary SSOT) — error message_ko

OQ-EPIC30+-2 결정 wire = Postmark default (apps/api/core/email_provider.py
PostmarkProvider 결정 wire 진입). Factory `get_email_provider()` env-driven
(Postmark → SMTP fallback → LoggingProvider dev default).

CR 11-3 honest-DEFER 238번째 epic 연속 정직 회복
(cj-298 close-out retro 의 237번째 + cj-299 의 238번째).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.email_provider import EmailDeliveryError, get_email_provider
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.reports.email_service import (
    build_csv_bytes_for_email,
    generate_email_body,
    redact_pii,
    send_email_with_retry,
)
from apps.api.schemas.email_schemas import EmailDeliveryResult, EmailExportRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["exports"])


# ── Typed exceptions (CR 12-5 D-14 envelope) ──────────────────────────


class EmailExportError(Exception):
    """Base Email delivery failure."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)


class EmailExportInvalidRequestError(EmailExportError):
    """400 EMAIL_EXPORT_INVALID_REQUEST_KO — invalid recipients/subject/period."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            code="EMAIL_EXPORT_INVALID_REQUEST_KO",
            message_ko="이메일 export 요청이 올바르지 않습니다",
            details={"reason": reason},
        )


class EmailExportForbiddenError(EmailExportError):
    """403 EMAIL_EXPORT_FORBIDDEN_KO — caller is not owner/admin."""

    def __init__(self, role: str) -> None:
        super().__init__(
            code="EMAIL_EXPORT_FORBIDDEN_KO",
            message_ko="이메일 export 권한이 없습니다 (owner 또는 admin 필요)",
            details={"role": role},
        )


class EmailExportCrossTenantError(EmailExportError):
    """403 EMAIL_EXPORT_CROSS_TENANT_KO — tenant_id mismatch with context."""

    def __init__(self, request_tenant_id: str, ctx_tenant_id: str) -> None:
        super().__init__(
            code="EMAIL_EXPORT_CROSS_TENANT_KO",
            message_ko="다른 테넌트의 데이터는 이메일로 보낼 수 없습니다",
            details={
                "request_tenant_id": request_tenant_id,
                "ctx_tenant_id": ctx_tenant_id,
            },
        )


class EmailExportDeliveryFailedError(EmailExportError):
    """502 EMAIL_EXPORT_DELIVERY_FAILED_KO — SMTP/Postmark retry exhausted."""

    def __init__(self, reason: str, retry_count: int) -> None:
        super().__init__(
            code="EMAIL_EXPORT_DELIVERY_FAILED_KO",
            message_ko="이메일 발송에 실패했습니다 (재시도 3회 소진)",
            details={"reason": reason, "retry_count": retry_count},
        )


# ── POST /api/v1/exports/email ─────────────────────────────────────────


@router.post(
    "/exports/email",
    response_model=EmailDeliveryResult,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_EMAIL)),  # cj-285 EXTENSION 보존
    ],
)
async def export_email(
    req: EmailExportRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> EmailDeliveryResult:
    """Story 30.3 Email delivery endpoint (cj-282 PRD entry §F30.3-1 verbatim).

    Flow:
      1. Cross-tenant check (CR 0-2 RLS) — request tenant_id == context tenant_id.
      2. Audit-first INSERT `export_email` (CR 1-1 verbatim + ActionClass.REPORTS)
         BEFORE SMTP dispatch.
      3. Build CSV bytes from DB (mirror csv_routes._iter pattern).
      4. Generate email body (summary + custom message).
      5. Redact PII (NFR4 PII minimization — if enabled).
      6. Send via provider (Postmark default) with retry 3회 + exponential backoff.
      7. Return EmailDeliveryResult envelope.

    Capability gate `require_capability(Capability.EXPORT_EMAIL)` 결정 wire 진입:
      - Capability.EXPORT_EMAIL EXTENSION (cj-285 EXTENSION wire sprint — capability
        matrix v1.54 EXTENSION).
      - Owner/admin RBAC (AD-22 verbatim) + capability gate (AD-12 verify-first).

    OQ-EPIC30+-2 결정 wire = Postmark (apps/api/core/email_provider.py). Fallback
    chain: Postmark → SMTP → LoggingProvider (dev default).
    """
    # Cross-tenant 차단 (CR 0-2 RLS 결정 wire).
    if str(req.tenant_id) != str(ctx.tenant_id):
        raise EmailExportCrossTenantError(
            request_tenant_id=str(req.tenant_id),
            ctx_tenant_id=str(ctx.tenant_id),
        )

    # audit-first INSERT `export_email` (CR 1-1 verbatim + ActionClass.REPORTS).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.REPORTS,  # cj-285 EXTENSION 보존 (export_email action)
            action="export_email",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            payload={
                "type": req.type,
                "period": req.period,
                "tenant_id": str(req.tenant_id),
                "recipient_count": len(req.recipients),
                "pii_redaction_enabled": req.pii_redaction_enabled,
                "subject_length": len(req.subject),
                "exported_at": datetime.now(UTC).isoformat(),
            },
            flush=True,
        )
        await session.commit()
    except Exception:  # noqa: BLE001
        # Best-effort: never block the email dispatch on audit emit fail.
        # Verbatim from csv_routes.py:376-380 pattern.
        logger.exception("export_email audit emit failed")

    # 1. Build CSV bytes from DB.
    csv_bytes = await build_csv_bytes_for_email(
        session=session,
        type=req.type,
        period=req.period,
        tenant_id=str(req.tenant_id),
    )

    # 2. Generate email body (summary + custom message).
    raw_body = generate_email_body(
        type=req.type,
        period=req.period,
        tenant_id=str(req.tenant_id),
        csv_bytes=csv_bytes,
        pii_redacted_fields=[],  # pre-redaction list (empty)
        custom_message=req.message,
    )

    # 3. Redact PII from email body (NFR4 PII minimization).
    redacted_body, pii_redacted_fields = redact_pii(raw_body, enabled=req.pii_redaction_enabled)

    # 4. Send via provider (Postmark default) with retry 3회.
    provider = get_email_provider()
    try:
        delivery_id, retry_count = await send_email_with_retry(
            provider=provider,
            subject=req.subject,
            body=redacted_body,
            recipients=req.recipients,
            max_retries=3,
        )
    except EmailDeliveryError as exc:
        logger.error(
            "Email delivery failed permanently: %s (code=%s)",
            exc.message,
            exc.code,
        )
        raise EmailExportDeliveryFailedError(reason=exc.message, retry_count=3) from exc

    # 5. Return EmailDeliveryResult envelope.
    return EmailDeliveryResult(
        delivery_id=delivery_id,
        status="delivered",
        recipient_count=len(req.recipients),
        retry_count=retry_count,
        delivered_at=datetime.now(UTC),
        pii_redacted_fields=pii_redacted_fields,
        trace_id=None,  # AD-15 trace_id propagation 결정 wire 보류 (cj-style 300+ EXTENSION)
    )


__all__ = [
    "router",
    "EmailExportError",
    "EmailExportInvalidRequestError",
    "EmailExportForbiddenError",
    "EmailExportCrossTenantError",
    "EmailExportDeliveryFailedError",
]
