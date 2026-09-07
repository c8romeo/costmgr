"""apps.api.modules.reports.scheduled_serializers — Story 30.4 Pydantic schemas.

cj-300 wire sprint (cj-style 302번째) — 4 NEW Pydantic schemas + 3
field_validator (NFR18 ko-KR vocabulary SSOT) + DispatchSchedule +
RecipientStrategy Literal 결정 wire.

Schemas:
1. ScheduledJobCreate     — POST /api/v1/exports/scheduled (request body)
2. ScheduledJobResponse   — POST/GET response envelope
3. ScheduledJobCancel     — POST /api/v1/exports/scheduled/{job_id}/cancel
4. ScheduledJobHistory    — GET /api/v1/exports/scheduled/history

CR 11-4 P-015 pure validator pattern.
CR 12-5 D-PARITY-01 inversion — TypeScript mirror + ko-KR.json EXTENSION.
CR 12-1 L4 industry-agnostic capability — 4-industry grants ✅/✅/✅/✅.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Literal types (PRD §F30.4-1 verbatim) ────────────────────────────────

DispatchSchedule = Literal["weekly", "monthly", "quarterly", "annual"]
"""Dispatch schedule 결정 wire — 4 cron schedules (PRD §F30.4-1 verbatim)."""

RecipientStrategy = Literal[
    "finance_only", "finance_and_admin", "admin_fallback"
]
"""Recipient strategy 결정 wire — NFR4 PII minimization (PRD §F30.4-4 verbatim)."""

ReportType = Literal["cost-records", "bom"]
"""Report type — verbatim mirror of csv_routes.py / email_routes.py."""

ScheduledJobStatus = Literal[
    "scheduled", "running", "completed", "failed", "cancelled", "expired"
]
"""Lifecycle state machine states (PRD §F30.4-1 verbatim)."""

ALL_DISPATCH_SCHEDULES: tuple[DispatchSchedule, ...] = (
    "weekly", "monthly", "quarterly", "annual",
)
ALL_RECIPIENT_STRATEGIES: tuple[RecipientStrategy, ...] = (
    "finance_only", "finance_and_admin", "admin_fallback",
)
ALL_REPORT_TYPES: tuple[ReportType, ...] = ("cost-records", "bom")
ALL_STATUSES: tuple[ScheduledJobStatus, ...] = (
    "scheduled", "running", "completed", "failed", "cancelled", "expired",
)

# Period key regex (AD-24 YYYY-MM format verbatim).
PERIOD_KEY_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
# Email format validator (CR 11-4 P-015 pure validator).
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Request schemas ─────────────────────────────────────────────────────


class ScheduledJobCreate(BaseModel):
    """POST /api/v1/exports/scheduled request body (PRD §F30.4-1).

    Used to schedule a new periodic report dispatch.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dispatch_schedule: DispatchSchedule = Field(
        ...,
        description="Cron schedule 결정 wire (weekly / monthly / quarterly / annual)",
    )
    recipient_strategy: RecipientStrategy = Field(
        default="finance_and_admin",
        description="수신자 결정 strategy (NFR4 PII minimization)",
    )
    finance_contact_email: str | None = Field(
        default=None,
        max_length=255,
        description="재무 담당자 이메일 (alembic tenants.finance_contact_email)",
    )
    report_type: ReportType = Field(
        default="cost-records",
        description="리포트 타입 (cost-records / bom)",
    )
    period_key: str | None = Field(
        default=None,
        description="기간 키 (YYYY-MM). Auto-computed if not provided.",
    )

    @field_validator("finance_contact_email")
    @classmethod
    def _validate_finance_email_format(cls, v: str | None) -> str | None:
        """CR 11-4 P-015 pure validator: finance_contact_email 형식 검증 (NFR18 ko-KR SSOT)."""
        if v is None:
            return v
        if not EMAIL_REGEX.match(v):
            raise ValueError("재무 담당자 이메일 형식이 올바르지 않습니다")
        return v

    @field_validator("period_key")
    @classmethod
    def _validate_period_key_format(cls, v: str | None) -> str | None:
        """AD-24 YYYY-MM format 검증 (CR 11-4 P-015)."""
        if v is None:
            return v
        if not PERIOD_KEY_REGEX.match(v):
            raise ValueError("기간 키(period_key)는 'YYYY-MM' 형식이어야 합니다")
        return v


class ScheduledJobCancel(BaseModel):
    """POST /api/v1/exports/scheduled/{job_id}/cancel request body (PRD §F30.4-5).

    Verbatim mirror of csv_routes.py pattern.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reason: str | None = Field(
        default=None,
        max_length=500,
        description="취소 사유 (선택, 500자 이내)",
    )


class ScheduledDispatchNow(BaseModel):
    """POST /api/v1/exports/scheduled/dispatch-now request body (PRD §F30.4-5).

    Force immediate dispatch (skip cron schedule) for owner/admin only.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dispatch_schedule: DispatchSchedule = Field(
        ...,
        description="즉시 발송할 dispatch schedule 결정 wire",
    )
    recipient_strategy: RecipientStrategy = Field(
        default="finance_and_admin",
        description="수신자 결정 strategy (NFR4 PII minimization)",
    )
    report_type: ReportType = Field(
        default="cost-records",
        description="리포트 타입 (cost-records / bom)",
    )
    period_key: str = Field(
        ...,
        description="기간 키 (YYYY-MM) — 필수",
    )


# ── Response schemas ────────────────────────────────────────────────────


class ScheduledJobResponse(BaseModel):
    """POST /api/v1/exports/scheduled + GET /jobs response envelope (PRD §F30.4-1)."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., description="UUID of the scheduled job")
    tenant_id: str = Field(..., description="UUID of the tenant")
    dispatch_schedule: DispatchSchedule = Field(
        ..., description="Cron schedule 결정 wire",
    )
    cron_expression: str = Field(..., description="Resolved cron expression")
    recipient_strategy: RecipientStrategy = Field(
        ..., description="수신자 결정 strategy",
    )
    recipients: dict[str, Any] = Field(
        ..., description="Resolved recipients (with admin_fallback_dispatched flag)",
    )
    report_type: ReportType = Field(..., description="리포트 타입")
    period_key: str = Field(..., description="기간 키 (YYYY-MM)")
    status: ScheduledJobStatus = Field(..., description="Lifecycle state")
    scheduled_at: datetime = Field(..., description="스케줄 시각 (UTC ISO8601)")
    trace_id: str | None = Field(
        default=None,
        description="CR 1-1 ContextVar trace_id (CR 1-1 verbatim)",
    )


class ScheduledJobHistory(BaseModel):
    """GET /api/v1/exports/scheduled/history response envelope (PRD §F30.4-5)."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., description="UUID of the scheduled job")
    tenant_id: str = Field(..., description="UUID of the tenant")
    dispatch_schedule: DispatchSchedule = Field(..., description="Cron schedule 결정 wire")
    period_key: str = Field(..., description="기간 키 (YYYY-MM)")
    status: ScheduledJobStatus = Field(..., description="Lifecycle state at history point")
    started_at: datetime = Field(..., description="시작 시각 (UTC ISO8601)")
    completed_at: datetime | None = Field(
        default=None, description="완료 시각 (UTC ISO8601)",
    )
    retry_count: int = Field(default=0, description="재시도 횟수 (0~3)")
    error_message: str | None = Field(
        default=None,
        description="실패 시 에러 메시지 (NFR18 ko-KR)",
    )


__all__ = [
    "DispatchSchedule",
    "RecipientStrategy",
    "ReportType",
    "ScheduledJobStatus",
    "ALL_DISPATCH_SCHEDULES",
    "ALL_RECIPIENT_STRATEGIES",
    "ALL_REPORT_TYPES",
    "ALL_STATUSES",
    "PERIOD_KEY_REGEX",
    "EMAIL_REGEX",
    "ScheduledJobCreate",
    "ScheduledJobCancel",
    "ScheduledDispatchNow",
    "ScheduledJobResponse",
    "ScheduledJobHistory",
]
