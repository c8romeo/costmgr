"""tests.api.modules.audit.retention.test_erasure — GDPR Article 17 erasure tests.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — T7a tests — F22.4.
10 NEW pytest cases covering:
  - mask_pii_fields() replaces actor_email/phone with [REDACTED]
  - mask_pii_fields() nested payload_json masking
  - mask_pii_fields() preserves non-PII fields
  - generate_trace_id() returns UUID4 string
  - request_audit_log_erasure() rejects non-owner role (403)
  - request_audit_log_erasure() rejects empty reason (400)
  - request_audit_log_erasure() rejects invalid scope (400)
  - request_audit_log_erasure() returns ErasureResult dict structure
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from apps.api.modules.audit.retention.erasure import (
    AuditLogPiiErasureForbiddenError,
    AuditLogPiiErasureNotFoundError,
    generate_trace_id,
    mask_pii_fields,
    request_audit_log_erasure,
)


class TestMaskPiiFields:
    """mask_pii_fields() — 3 NEW cases."""

    def test_masks_actor_email_and_phone(self) -> None:
        masked = mask_pii_fields({"actor_email": "a@b.c", "actor_phone": "010"})
        assert masked["actor_email"] == "[REDACTED]"
        assert masked["actor_phone"] == "[REDACTED]"

    def test_masks_nested_user_data(self) -> None:
        masked = mask_pii_fields(
            {"payload_json": {"user_data": "secret", "non_pii": "ok"}}
        )
        assert masked["payload_json"]["user_data"] == "[REDACTED]"
        assert masked["payload_json"]["non_pii"] == "ok"

    def test_preserves_non_pii_fields(self) -> None:
        masked = mask_pii_fields({"non_pii_field": "keep_me", "actor_email": "x@y.z"})
        assert masked["non_pii_field"] == "keep_me"
        assert masked["actor_email"] == "[REDACTED]"


class TestGenerateTraceId:
    """generate_trace_id() — 1 NEW case."""

    def test_returns_uuid4_string(self) -> None:
        t = generate_trace_id()
        assert isinstance(t, str)
        parsed = uuid.UUID(t)
        assert parsed.version == 4


class TestRequestAuditLogErasure:
    """request_audit_log_erasure() — 6 NEW cases (no DB needed; use AsyncMock)."""

    def _tenant(self) -> uuid.UUID:
        return uuid.UUID("22222222-2222-2222-2222-222222222222")

    def _actor(self) -> uuid.UUID:
        return uuid.UUID("33333333-3333-3333-3333-333333333333")

    def _mock_db(self) -> AsyncMock:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.return_value.fetchall = lambda: []
        db.commit = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_rejects_non_owner_role(self) -> None:
        with pytest.raises(AuditLogPiiErasureForbiddenError) as exc:
            await request_audit_log_erasure(
                self._mock_db(),
                self._tenant(),
                actor_id=self._actor(),
                scope="actor",
                reason="GDPR",
                requester_role="member",
            )
        assert exc.value.code == "AUDIT_LOG_PII_ERASURE_FORBIDDEN"

    @pytest.mark.asyncio
    async def test_rejects_empty_reason(self) -> None:
        with pytest.raises(AuditLogPiiErasureForbiddenError) as exc:
            await request_audit_log_erasure(
                self._mock_db(),
                self._tenant(),
                actor_id=self._actor(),
                scope="actor",
                reason="   ",
                requester_role="owner",
            )
        assert exc.value.code == "AUDIT_LOG_PII_ERASURE_REASON_REQUIRED"

    @pytest.mark.asyncio
    async def test_rejects_invalid_scope(self) -> None:
        with pytest.raises(AuditLogPiiErasureForbiddenError) as exc:
            await request_audit_log_erasure(
                self._mock_db(),
                self._tenant(),
                actor_id=self._actor(),
                scope="bogus",  # type: ignore[arg-type]
                reason="GDPR",
                requester_role="owner",
            )
        assert exc.value.code == "AUDIT_LOG_PII_ERASURE_INVALID_SCOPE"

    @pytest.mark.asyncio
    async def test_owner_with_valid_scope_returns_dict(self) -> None:
        db = self._mock_db()
        result = await request_audit_log_erasure(
            db,
            self._tenant(),
            actor_id=self._actor(),
            scope="actor",
            reason="GDPR Article 17",
            requester_role="owner",
        )
        assert result["erased_count"] >= 0
        assert result["archived_preserved"] is True
        assert result["scope"] == "actor"
        assert result["actor_id"] == str(self._actor())
        assert result["tenant_id"] == str(self._tenant())

    @pytest.mark.asyncio
    async def test_generates_trace_id_when_not_provided(self) -> None:
        db = self._mock_db()
        result = await request_audit_log_erasure(
            db,
            self._tenant(),
            actor_id=self._actor(),
            scope="tenant",
            reason="GDPR",
            requester_role="owner",
        )
        # generated trace_id is a valid UUID4
        uuid.UUID(result["trace_id"])
        assert result["scope"] == "tenant"

    @pytest.mark.asyncio
    async def test_uses_caller_supplied_trace_id(self) -> None:
        db = self._mock_db()
        explicit = "12345678-1234-5678-1234-567812345678"
        result = await request_audit_log_erasure(
            db,
            self._tenant(),
            actor_id=self._actor(),
            scope="all",
            reason="GDPR",
            requester_role="owner",
            trace_id=explicit,
        )
        assert result["trace_id"] == explicit


class TestTypedExceptions:
    """Exception envelope — 1 NEW case (CR 12-5 D-14 verbatim)."""

    def test_forbidden_exception_envelope(self) -> None:
        exc = AuditLogPiiErasureForbiddenError(
            code="X",
            message_ko="테스트",
            details={"k": "v"},
        )
        assert exc.code == "X"
        assert exc.message_ko == "테스트"
        assert exc.details == {"k": "v"}

    def test_not_found_exception_envelope(self) -> None:
        exc = AuditLogPiiErasureNotFoundError(
            code="Y",
            message_ko="없음",
        )
        assert exc.code == "Y"
        assert exc.details == {}
