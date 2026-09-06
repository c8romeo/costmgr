"""Story 30.3 Email delivery Pydantic schemas (cj-299 wire sprint).

cj-299 wire sprint (cj-style 299번째) — Story 30.3 Email delivery (FR-30-3).

POST /api/v1/exports/email request/response schemas.

- AD bind 3/3: AD-2 (audit-first INSERT) + AD-10 (identity/2FA via owner-only RBAC) +
  AD-12 (verify-first capability gate, in-route)
- NFR bind 3/7 active:
  - NFR4 (PII minimization) — `pii_redaction_enabled` default True
  - NFR5 (page load P95 ≤ 5s) — async dispatch, retry 3회 with exponential backoff
  - NFR18 (ko-KR vocabulary SSOT) — error message_ko
- OQ-EPIC30+-2 결정 wire: Postmark default (cj-299 sprint scope)
- capability matrix v1.54 EXTENSION 보존 (EXPORT_EMAIL)
- 1 NEW audit action EXTENSION 결정 wire (export_email — cj-285 EXTENSION 보존)

Mirrors the canonical Pydantic schema pattern from `apps/api/schemas/export_schemas.py`
(verbatim) for `BaseModel` + `Field` + `UUID4` + `Literal` typing.

CR 11-3 honest-DEFER 238번째 epic 연속 정직 회복
(cj-298 close-out retro 의 237번째 + cj-299 의 238번째).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator


# Email RFC 5322 simple regex (sufficient for SMTP delivery, not full RFC 5322).
EMAIL_REGEX: str = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


class EmailExportRequest(BaseModel):
    """Story 30.3 Email delivery request schema.

    Used by POST /api/v1/exports/email

    Fields:
        type: export type. cost-records (Story 30.3 first slice) or bom (level 1 only).
        period: target period in YYYY-MM format (KST 기준). 정규식 검증.
        tenant_id: tenant UUID (cross-tenant 차단 via tenant context, CR 0-2 RLS).
        recipients: 1~10개 이메일 주소 (multi-recipient broadcast). 정규식 검증.
        subject: 이메일 제목 (1~200자, ko-KR NFR18 SSOT 적용 가능).
        pii_redaction_enabled: PII redaction on/off (default True — NFR4 PII minimization).
            PII patterns: 한국 주민등록번호, 전화번호, 이메일. Redaction 결과는
            EmailDeliveryResult.pii_redacted_fields 에 반영.
        message: 선택적 본문 추가 메시지 (1~2000자). 이메일 본문 상단에 prepend.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "cost-records",
                "period": "2026-08",
                "tenant_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "recipients": ["cfo@example.com", "controller@example.com"],
                "subject": "[bizup 원가 관리] 2026-08 원가 보고서",
                "pii_redaction_enabled": True,
                "message": "회계감사 자료로 활용 부탁드립니다.",
            }
        },
    )

    type: Literal["cost-records", "bom"] = Field(
        ...,
        description="export type — cost-records (cost_records 테이블) | bom (BOM level 1)",
    )
    period: str = Field(
        ...,
        description="YYYY-MM format (KST 기준 monthly period)",
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    tenant_id: UUID4 = Field(
        ...,
        description="tenant UUID — cross-tenant 차단 via tenant context (CR 0-2 RLS)",
    )
    recipients: list[str] = Field(
        ...,
        description="1~10개 이메일 주소 (comma-separated broadcast)",
        min_length=1,
        max_length=10,
    )
    subject: str = Field(
        ...,
        description="이메일 제목 (1~200자, NFR18 ko-KR SSOT)",
        min_length=1,
        max_length=200,
    )
    pii_redaction_enabled: bool = Field(
        True,
        description="NFR4 PII minimization — True 면 주민등록번호/전화/이메일 패턴 redact",
    )
    message: str | None = Field(
        None,
        description="선택적 추가 메시지 (1~2000자). 이메일 본문 상단에 prepend.",
        max_length=2000,
    )

    @field_validator("period")
    @classmethod
    def _validate_period_format(cls, v: str) -> str:
        """NFR18 ko-KR SSOT 결정 wire 보존 — period 정규식 추가 검증."""
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError(
                "period는 YYYY-MM 형식이어야 합니다 (예: 2026-08). 월은 01~12 범위."
            )
        return v

    @field_validator("recipients")
    @classmethod
    def _validate_emails(cls, v: list[str]) -> list[str]:
        """Email RFC 5322 simple regex 결정 wire (NFR18 ko-KR error message)."""
        for idx, email in enumerate(v):
            if not re.match(EMAIL_REGEX, email):
                raise ValueError(
                    f"잘못된 이메일 형식입니다 (index {idx}: {email!r})."
                )
        return v

    @field_validator("subject")
    @classmethod
    def _validate_subject_not_empty(cls, v: str) -> str:
        """Subject 결정 wire — strip 후 empty 불가 (NFR18 ko-KR SSOT)."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("이메일 제목은 비어 있을 수 없습니다.")
        return stripped


class EmailDeliveryResult(BaseModel):
    """Story 30.3 Email delivery response envelope.

    Returns 200 OK on successful delivery (after retry exhaustion
    failed → 502 Bad Gateway envelope). On 200:
        delivery_id: provider-specific message ID (Postmark MessageID /
            SMTP correlation / LoggingProvider log-{uuid}).
        status: delivered (200 OK from provider) | queued (provider accepted
            but no delivery confirmation yet — Postmark outbound).
        recipient_count: int (len(req.recipients)).
        retry_count: int (0~3 — 0 means first try succeeded).
        delivered_at: UTC datetime.
        pii_redacted_fields: list of redacted PII pattern names (NFR4 audit).
            e.g. ["resident_id", "phone", "email"].
        trace_id: AD-15 trace_id for client-side error reporting.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "delivery_id": "8f0e1c2a-9b3d-4e7f-a1c5-2b8e3f4d5c6a",
                "status": "delivered",
                "recipient_count": 2,
                "retry_count": 0,
                "delivered_at": "2026-09-06T12:34:56Z",
                "pii_redacted_fields": ["phone", "email"],
                "trace_id": "trace-abc-123",
            }
        },
    )

    delivery_id: str = Field(
        ...,
        description="Provider-specific delivery ID (Postmark MessageID / SMTP correlation)",
        min_length=1,
        max_length=128,
    )
    status: Literal["delivered", "queued", "failed"] = Field(
        ...,
        description="delivered = provider accepted + delivered; queued = accepted but pending; failed = retry exhausted",
    )
    recipient_count: int = Field(
        ...,
        description="Number of recipients the email was sent to",
        ge=1,
        le=10,
    )
    retry_count: int = Field(
        ...,
        description="Number of retries used (0 = first try succeeded, max 3 = exhausted)",
        ge=0,
        le=3,
    )
    delivered_at: datetime = Field(
        ...,
        description="UTC datetime of successful delivery (or last failed attempt)",
    )
    pii_redacted_fields: list[str] = Field(
        default_factory=list,
        description="PII pattern names that were redacted (NFR4 audit)",
    )
    trace_id: str | None = Field(
        None,
        description="AD-15 trace_id for client-side error reporting",
    )


__all__ = ["EmailExportRequest", "EmailDeliveryResult", "EMAIL_REGEX"]
