"""apps.api.jobs.errors — Scheduled reports typed exceptions (Story 30.4).

cj-300 wire sprint (cj-style 302번째) — 16 NEW typed exception classes
(CR 12-5 D-14 envelope verbatim).

PRD §F30.4-7 (T5) — 16 NEW typed exception classes:
1. ScheduledReportCronInvalidError          400
2. ScheduledReportTenantNotFoundError       404
3. ScheduledReportFinanceEmailNotFoundError 400
4. ScheduledReportLifecycleError            400
5. ScheduledReportRetryExhaustedError       500
6. ScheduledReportPersistenceError         500
7. ScheduledReportIdempotencyViolationError 409
8. ScheduledReportPermissionError           403
9. ScheduledReportFinanceContactEmailError  400
10. ScheduledReportAlembicMigrationError    500
11. ScheduledReportAsyncIOError             500
12. ScheduledReportPersistentJobStoreError  500
13. ScheduledReportTimezoneError            400
14. ScheduledReportPeriodKeyError           400
15. ScheduledReportDispatchError            500
16. ScheduledReportRecipientResolverError   500

All inherit from ScheduledReportError base class (CR 12-5 D-14).
"""

from __future__ import annotations

from typing import Any

from apps.api.core.errors import BaseError


class ScheduledReportError(BaseError):
    """Base scheduled reports failure (CR 12-5 D-14 envelope).

    Provides http_status=500 default + code + message_ko + details + trace_id.
    Inherits from BaseError (apps.api.core.errors) for typed exception
    envelope uniformity.
    """

    http_status: int = 500

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message_ko=message_ko,
            details=details or {},
        )


# ── 16 NEW typed exception classes (PRD §F30.4-7) ─────────────────────


class ScheduledReportCronInvalidError(ScheduledReportError):
    """400 SCHEDULED_REPORT_CRON_INVALID — cron expression not parseable."""

    http_status: int = 400

    def __init__(self, cron_expression: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_CRON_INVALID",
            message_ko="예약 리포트 cron 표현식이 올바르지 않습니다",
            details={"cron_expression": cron_expression},
        )


class ScheduledReportTenantNotFoundError(ScheduledReportError):
    """404 SCHEDULED_REPORT_TENANT_NOT_FOUND — tenant_id not registered."""

    http_status: int = 404

    def __init__(self, tenant_id: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_TENANT_NOT_FOUND",
            message_ko="해당 테넌트를 찾을 수 없습니다",
            details={"tenant_id": tenant_id},
        )


class ScheduledReportFinanceEmailNotFoundError(ScheduledReportError):
    """400 SCHEDULED_REPORT_FINANCE_EMAIL_NOT_FOUND — finance_contact_email = NULL + non-fallback strategy."""

    http_status: int = 400

    def __init__(self, tenant_id: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_FINANCE_EMAIL_NOT_FOUND",
            message_ko="재무 담당자 이메일이 등록되지 않았습니다 (관리자에게 문의)",
            details={"tenant_id": tenant_id},
        )


class ScheduledReportLifecycleError(ScheduledReportError):
    """400 SCHEDULED_REPORT_LIFECYCLE_INVALID — invalid state transition."""

    http_status: int = 400

    def __init__(self, current_status: str, event: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_LIFECYCLE_INVALID",
            message_ko="예약 리포트 lifecycle 상태 전이가 올바르지 않습니다",
            details={"current_status": current_status, "event": event},
        )


class ScheduledReportRetryExhaustedError(ScheduledReportError):
    """500 SCHEDULED_REPORT_RETRY_EXHAUSTED — retry 3회 소진."""

    http_status: int = 500

    def __init__(self, tenant_id: str, job_id: str, last_error: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_RETRY_EXHAUSTED",
            message_ko="예약 리포트 재시도 3회 소진 (관리자에게 문의)",
            details={
                "tenant_id": tenant_id,
                "job_id": job_id,
                "last_error": last_error,
            },
        )


class ScheduledReportPersistenceError(ScheduledReportError):
    """500 SCHEDULED_REPORT_PERSISTENCE_ERROR — DB INSERT/UPDATE 실패."""

    http_status: int = 500

    def __init__(self, tenant_id: str, operation: str, reason: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_PERSISTENCE_ERROR",
            message_ko="예약 리포트 DB 저장에 실패했습니다 (관리자에게 문의)",
            details={
                "tenant_id": tenant_id,
                "operation": operation,
                "reason": reason,
            },
        )


class ScheduledReportIdempotencyViolationError(ScheduledReportError):
    """409 SCHEDULED_REPORT_IDEMPOTENCY_VIOLATION — (tenant + schedule + period) tuple 중복."""

    http_status: int = 409

    def __init__(
        self,
        tenant_id: str,
        dispatch_schedule: str,
        period_key: str,
    ) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_IDEMPOTENCY_VIOLATION",
            message_ko="동일 기간에 이미 예약된 리포트가 있습니다",
            details={
                "tenant_id": tenant_id,
                "dispatch_schedule": dispatch_schedule,
                "period_key": period_key,
            },
        )


class ScheduledReportPermissionError(ScheduledReportError):
    """403 SCHEDULED_REPORT_PERMISSION_DENIED — owner/admin only RBAC."""

    http_status: int = 403

    def __init__(self, role: str, required_role: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_PERMISSION_DENIED",
            message_ko="예약 리포트 권한이 없습니다 (owner 또는 admin 필요)",
            details={"role": role, "required_role": required_role},
        )


class ScheduledReportFinanceContactEmailError(ScheduledReportError):
    """400 SCHEDULED_REPORT_FINANCE_CONTACT_EMAIL_INVALID — finance_contact_email 형식 오류."""

    http_status: int = 400

    def __init__(self, finance_contact_email: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_FINANCE_CONTACT_EMAIL_INVALID",
            message_ko="재무 담당자 이메일 형식이 올바르지 않습니다",
            details={"finance_contact_email": finance_contact_email},
        )


class ScheduledReportAlembicMigrationError(ScheduledReportError):
    """500 SCHEDULED_REPORT_ALEMBIC_MIGRATION_ERROR — alembic upgrade/downgrade 실패."""

    http_status: int = 500

    def __init__(self, migration_revision: str, reason: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_ALEMBIC_MIGRATION_ERROR",
            message_ko="alembic migration 실행에 실패했습니다 (관리자에게 문의)",
            details={
                "migration_revision": migration_revision,
                "reason": reason,
            },
        )


class ScheduledReportAsyncIOError(ScheduledReportError):
    """500 SCHEDULED_REPORT_ASYNCIO_ERROR — AsyncIOScheduler 비동기 작업 실패."""

    http_status: int = 500

    def __init__(self, job_id: str, reason: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_ASYNCIO_ERROR",
            message_ko="예약 리포트 비동기 작업 실행에 실패했습니다 (관리자에게 문의)",
            details={"job_id": job_id, "reason": reason},
        )


class ScheduledReportPersistentJobStoreError(ScheduledReportError):
    """500 SCHEDULED_REPORT_PERSISTENT_JOB_STORE_ERROR — PersistentJobStore 초기화/작업 실패."""

    http_status: int = 500

    def __init__(self, backend: str, reason: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_PERSISTENT_JOB_STORE_ERROR",
            message_ko="PersistentJobStore 초기화 또는 작업 실행에 실패했습니다 (관리자에게 문의)",
            details={"backend": backend, "reason": reason},
        )


class ScheduledReportTimezoneError(ScheduledReportError):
    """400 SCHEDULED_REPORT_TIMEZONE_INVALID — KST/Aisa/Seoul timezone 변환 실패."""

    http_status: int = 400

    def __init__(self, timezone_str: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_TIMEZONE_INVALID",
            message_ko="시간대 변환에 실패했습니다 (KST 기본)",
            details={"timezone": timezone_str},
        )


class ScheduledReportPeriodKeyError(ScheduledReportError):
    """400 SCHEDULED_REPORT_PERIOD_KEY_INVALID — period_key AD-24 mismatch."""

    http_status: int = 400

    def __init__(self, period_key: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_PERIOD_KEY_INVALID",
            message_ko="기간 키(period_key)가 'YYYY-MM' 형식이 아닙니다",
            details={"period_key": period_key},
        )


class ScheduledReportDispatchError(ScheduledReportError):
    """500 SCHEDULED_REPORT_DISPATCH_ERROR — email/PDF dispatch 실패."""

    http_status: int = 500

    def __init__(self, job_id: str, dispatch_target: str, reason: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_DISPATCH_ERROR",
            message_ko="예약 리포트 발송에 실패했습니다 (관리자에게 문의)",
            details={
                "job_id": job_id,
                "dispatch_target": dispatch_target,
                "reason": reason,
            },
        )


class ScheduledReportRecipientResolverError(ScheduledReportError):
    """500 SCHEDULED_REPORT_RECIPIENT_RESOLVER_ERROR — recipient strategy resolve 실패."""

    http_status: int = 500

    def __init__(self, recipient_strategy: str, reason: str) -> None:
        super().__init__(
            code="SCHEDULED_REPORT_RECIPIENT_RESOLVER_ERROR",
            message_ko="수신자 결정에 실패했습니다 (관리자에게 문의)",
            details={
                "recipient_strategy": recipient_strategy,
                "reason": reason,
            },
        )


# ── Aliases for backward compat with 11 precedent verbatim imports ─────
# Phase 16/22/23/24/25 verbatim pattern mirrors
# (scheduled_executive_dispatch.py imports these from older shared module).


class CronExpressionInvalidError(ScheduledReportCronInvalidError):
    """Backward-compat alias (verbatim mirror of scheduled_executive_dispatch.py)."""


class DispatchIdempotencyViolationError(ScheduledReportIdempotencyViolationError):
    """Backward-compat alias."""


class RecipientResolverError(ScheduledReportRecipientResolverError):
    """Backward-compat alias."""


__all__ = [
    "ScheduledReportError",
    "ScheduledReportCronInvalidError",
    "ScheduledReportTenantNotFoundError",
    "ScheduledReportFinanceEmailNotFoundError",
    "ScheduledReportLifecycleError",
    "ScheduledReportRetryExhaustedError",
    "ScheduledReportPersistenceError",
    "ScheduledReportIdempotencyViolationError",
    "ScheduledReportPermissionError",
    "ScheduledReportFinanceContactEmailError",
    "ScheduledReportAlembicMigrationError",
    "ScheduledReportAsyncIOError",
    "ScheduledReportPersistentJobStoreError",
    "ScheduledReportTimezoneError",
    "ScheduledReportPeriodKeyError",
    "ScheduledReportDispatchError",
    "ScheduledReportRecipientResolverError",
    # Backward-compat aliases
    "CronExpressionInvalidError",
    "DispatchIdempotencyViolationError",
    "RecipientResolverError",
]
