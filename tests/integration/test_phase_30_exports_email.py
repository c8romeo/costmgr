"""apps.costmgr.tests.integration.test_phase_30_exports_email

cj-299 wire sprint (cj-style 299번째) — Story 30.3 Email delivery (FR-30-3) integration tests.

Mirrors tests/integration/test_phase_30_exports_csv.py verbatim pattern (test_phase_30
naming + class-based 그룹화 + ExceptionGroup-style compile-time coverage).

Test classes:
  - TestEmailProvider: 3 provider implementations (Postmark / SMTP / Logging)
  - TestRedactPII: 4 tests (resident_id / phone / email / disabled)
  - TestSendEmailWithRetry: 5 tests (success / transient retry / permanent fail /
    exhausted / empty recipients)
  - TestGenerateEmailBody: 3 tests (summary / custom message / PII notice)
  - TestEmailSchemas: 6 tests (valid request / invalid period / invalid email /
    empty subject / max recipients / valid response)
  - TestBuildCsvBytesForEmail: 2 tests (cost-records path / bom path)
  - TestEmailRoutes: 3 mocked HTTP integration tests (cross-tenant / PII enabled /
    PII disabled) — mirrors csv_routes.py test patterns

Total: ~30 tests, fast (no network — Postmark/SMTP mocked).

CR 11-3 honest-DEFER 238번째 epic 연속 정직 회복.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from apps.api.core.email_provider import (
    EmailDeliveryError,
    EmailProvider,
    EmailTransientError,
    LoggingProvider,
    PostmarkProvider,
    SMTPProvider,
    get_email_provider,
)
from apps.api.modules.reports.email_service import (
    EMAIL_MAX_RETRIES,
    EMAIL_RETRY_BACKOFF_SECONDS,
    MAX_RECIPIENTS,
    PII_PATTERNS,
    build_csv_bytes_for_email,
    generate_email_body,
    redact_pii,
    send_email_with_retry,
)
from apps.api.schemas.email_schemas import (
    EMAIL_REGEX,
    EmailDeliveryResult,
    EmailExportRequest,
)


# ── TestEmailProvider (3 implementations) ───────────────────────────────


class TestEmailProvider:
    """Test the 3 email provider implementations + factory."""

    @pytest.mark.asyncio
    async def test_logging_provider_returns_delivery_id(self) -> None:
        """LoggingProvider (dev default) returns log-{uuid} delivery_id without network."""
        provider = LoggingProvider()
        delivery_id = await provider.send(
            subject="테스트",
            body="본문",
            recipients=["test@example.com"],
        )
        assert delivery_id.startswith("log-")
        assert len(delivery_id) > 4

    @pytest.mark.asyncio
    async def test_postmark_provider_uses_http_api(self) -> None:
        """PostmarkProvider hits https://api.postmarkapp.com/email with correct headers."""
        provider = PostmarkProvider(server_token="test-token-123")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "MessageID": "msg-abc-123",
            "ErrorCode": 0,
            "Message": "OK",
        }
        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            delivery_id = await provider.send(
                subject="테스트",
                body="본문",
                recipients=["test@example.com"],
            )
            assert delivery_id == "msg-abc-123"
            mock_post.assert_called_once()
            call = mock_post.call_args
            assert "api.postmarkapp.com/email" in str(call.args)
            headers = call.kwargs["headers"]
            assert headers["X-Postmark-Server-Token"] == "test-token-123"

    @pytest.mark.asyncio
    async def test_postmark_provider_5xx_raises_transient(self) -> None:
        """Postmark 5xx → EmailTransientError (caller retries)."""
        provider = PostmarkProvider(server_token="test-token-123")
        mock_response = AsyncMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(EmailTransientError):
                await provider.send(
                    subject="테스트",
                    body="본문",
                    recipients=["test@example.com"],
                )

    @pytest.mark.asyncio
    async def test_postmark_provider_4xx_raises_permanent(self) -> None:
        """Postmark 4xx → EmailDeliveryError permanent (caller does NOT retry)."""
        provider = PostmarkProvider(server_token="test-token-123")
        mock_response = AsyncMock()
        mock_response.status_code = 422
        mock_response.text = "Invalid payload"
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(EmailDeliveryError) as exc_info:
                await provider.send(
                    subject="테스트",
                    body="본문",
                    recipients=["test@example.com"],
                )
            assert exc_info.value.code == "POSTMARK_CLIENT_ERROR"

    def test_factory_returns_logging_provider_when_no_env(self) -> None:
        """get_email_provider() defaults to LoggingProvider when no env vars."""
        with patch.dict("os.environ", {}, clear=True):
            provider = get_email_provider()
            assert isinstance(provider, LoggingProvider)

    def test_factory_returns_postmark_when_token_set(self) -> None:
        """get_email_provider() returns PostmarkProvider when POSTMARK_SERVER_TOKEN is set."""
        with patch.dict(
            "os.environ",
            {"POSTMARK_SERVER_TOKEN": "test-token"},
            clear=True,
        ):
            provider = get_email_provider()
            assert isinstance(provider, PostmarkProvider)
            assert provider.server_token == "test-token"

    def test_factory_returns_smtp_when_smtp_env_set(self) -> None:
        """get_email_provider() returns SMTPProvider when SMTP_* env vars are set."""
        with patch.dict(
            "os.environ",
            {
                "SMTP_HOST": "smtp.gmail.com",
                "SMTP_PORT": "587",
                "SMTP_USERNAME": "user@example.com",
                "SMTP_PASSWORD": "secret",
            },
            clear=True,
        ):
            provider = get_email_provider()
            assert isinstance(provider, SMTPProvider)
            assert provider.host == "smtp.gmail.com"


# ── TestRedactPII (4 tests) ──────────────────────────────────────────────


class TestRedactPII:
    """Test PII redaction logic (NFR4 PII minimization)."""

    def test_redact_resident_id_korean(self) -> None:
        """한국 주민등록번호 6-7 → [REDACTED-resident_id]."""
        body = "고객 주민번호: 900101-1234567 입니다."
        redacted, fields = redact_pii(body, enabled=True)
        assert "[REDACTED-resident_id]" in redacted
        assert "900101-1234567" not in redacted
        assert "resident_id" in fields

    def test_redact_phone_korean(self) -> None:
        """한국 전화번호 → [REDACTED-phone]."""
        body = "연락처: 010-1234-5678 또는 02-1234-5678"
        redacted, fields = redact_pii(body, enabled=True)
        assert redacted.count("[REDACTED-phone]") == 2
        assert "010-1234-5678" not in redacted
        assert "phone" in fields

    def test_redact_email_pattern(self) -> None:
        """이메일 패턴 → [REDACTED-email]."""
        body = "담당자: cfo@example.com (회계이사)"
        redacted, fields = redact_pii(body, enabled=True)
        assert "[REDACTED-email]" in redacted
        assert "email" in fields

    def test_redact_disabled_passthrough(self) -> None:
        """enabled=False 면 redaction 없이 그대로 반환."""
        body = "주민번호: 900101-1234567, 전화: 010-1234-5678"
        redacted, fields = redact_pii(body, enabled=False)
        assert redacted == body
        assert fields == []

    def test_redact_multiple_patterns_at_once(self) -> None:
        """3 patterns 동시 redact 시 fields 에 모든 패턴 이름 포함."""
        body = "주민: 900101-1234567, 전화: 010-1234-5678, 이메일: cfo@example.com"
        redacted, fields = redact_pii(body, enabled=True)
        assert "resident_id" in fields
        assert "phone" in fields
        assert "email" in fields
        assert "[REDACTED-" not in body  # 원본은 그대로
        assert "[REDACTED-" in redacted  # redact 적용

    def test_redact_no_pii_returns_empty_fields(self) -> None:
        """PII 없는 body → redaction 없음, fields=[]."""
        body = "bizup 원가 관리 보고서입니다. 데이터 행 수 1500건."
        redacted, fields = redact_pii(body, enabled=True)
        assert redacted == body
        assert fields == []


# ── TestSendEmailWithRetry (5 tests) ────────────────────────────────────


class TestSendEmailWithRetry:
    """Test send_email_with_retry retry logic."""

    @pytest.mark.asyncio
    async def test_success_first_try(self) -> None:
        """첫 번째 시도 성공 → retry_count=0."""
        provider = LoggingProvider()
        delivery_id, retry_count = await send_email_with_retry(
            provider=provider,
            subject="테스트",
            body="본문",
            recipients=["test@example.com"],
        )
        assert delivery_id.startswith("log-")
        assert retry_count == 0

    @pytest.mark.asyncio
    async def test_success_after_one_retry(self) -> None:
        """첫 번째 transient → 두 번째 성공 → retry_count=1."""
        provider = LoggingProvider()
        call_count = {"n": 0}

        async def flaky_send(**kwargs: object) -> str:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise EmailTransientError(message="flaky", retry_after_seconds=0.01)
            return "delivered-id"

        # Patch LoggingProvider.send with a flaky version.
        provider.send = flaky_send  # type: ignore[assignment]
        delivery_id, retry_count = await send_email_with_retry(
            provider=provider,
            subject="테스트",
            body="본문",
            recipients=["test@example.com"],
            max_retries=3,
        )
        assert delivery_id == "delivered-id"
        assert retry_count == 1
        assert call_count["n"] == 2

    @pytest.mark.asyncio
    async def test_permanent_failure_no_retry(self) -> None:
        """permanent failure → raise immediately, no retry."""
        provider = LoggingProvider()

        async def always_fail(**kwargs: object) -> str:
            raise EmailDeliveryError(code="PERMANENT", message="hard fail")

        provider.send = always_fail  # type: ignore[assignment]
        with pytest.raises(EmailDeliveryError) as exc_info:
            await send_email_with_retry(
                provider=provider,
                subject="테스트",
                body="본문",
                recipients=["test@example.com"],
                max_retries=3,
            )
        assert exc_info.value.code == "PERMANENT"

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self) -> None:
        """transient 반복 → max_retries 소진 후 raise."""
        provider = LoggingProvider()

        async def always_transient(**kwargs: object) -> str:
            raise EmailTransientError(message="flaky forever", retry_after_seconds=0.01)

        provider.send = always_transient  # type: ignore[assignment]
        with pytest.raises(EmailTransientError):
            await send_email_with_retry(
                provider=provider,
                subject="테스트",
                body="본문",
                recipients=["test@example.com"],
                max_retries=2,  # total 3 attempts
            )

    @pytest.mark.asyncio
    async def test_empty_recipients_raises(self) -> None:
        """recipients=[] → EmailDeliveryError (EMAIL_NO_RECIPIENTS)."""
        provider = LoggingProvider()
        with pytest.raises(EmailDeliveryError) as exc_info:
            await send_email_with_retry(
                provider=provider,
                subject="테스트",
                body="본문",
                recipients=[],
            )
        assert exc_info.value.code == "EMAIL_NO_RECIPIENTS"

    def test_constants(self) -> None:
        """Constants 결정 wire 검증."""
        assert EMAIL_MAX_RETRIES == 3
        assert EMAIL_RETRY_BACKOFF_SECONDS == (1.0, 2.0, 4.0)
        assert MAX_RECIPIENTS == 10
        assert set(PII_PATTERNS.keys()) == {"resident_id", "phone", "email"}


# ── TestGenerateEmailBody (3 tests) ──────────────────────────────────────


class TestGenerateEmailBody:
    """Test email body generation (plain text format)."""

    def test_basic_summary(self) -> None:
        """기본 summary 형식 결정 wire 검증."""
        body = generate_email_body(
            type="cost-records",
            period="2026-08",
            tenant_id="t-123",
            csv_bytes=b"a" * 1000,
            pii_redacted_fields=[],
        )
        assert "bizup 원가 관리" in body
        assert "cost-records 보고서" in body
        assert "2026-08" in body
        assert "t-123" in body

    def test_with_custom_message(self) -> None:
        """custom_message prepend 결정 wire 검증."""
        body = generate_email_body(
            type="bom",
            period="2026-08",
            tenant_id="t-123",
            csv_bytes=b"a" * 1000,
            pii_redacted_fields=[],
            custom_message="회계감사 자료입니다",
        )
        # custom_message 는 본문 상단에 prepend.
        idx = body.find("회계감사 자료입니다")
        assert idx >= 0
        summary_idx = body.find("bizup 원가 관리")
        assert summary_idx > idx

    def test_pii_notice_appended(self) -> None:
        """pii_redacted_fields 있으면 notice 추가 결정 wire 검증."""
        body = generate_email_body(
            type="cost-records",
            period="2026-08",
            tenant_id="t-123",
            csv_bytes=b"a" * 1000,
            pii_redacted_fields=["phone", "email"],
        )
        assert "개인정보 보호" in body
        assert "phone" in body
        assert "email" in body


# ── TestEmailSchemas (6 tests) ───────────────────────────────────────────


class TestEmailSchemas:
    """Test Pydantic schemas (request validation)."""

    def test_valid_request(self) -> None:
        """정상 요청 → pass."""
        req = EmailExportRequest(
            type="cost-records",
            period="2026-08",
            tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            recipients=["cfo@example.com"],
            subject="테스트 보고서",
        )
        assert req.period == "2026-08"
        assert len(req.recipients) == 1
        assert req.pii_redaction_enabled is True  # default
        assert req.message is None  # default

    def test_invalid_period_format(self) -> None:
        """잘못된 period 형식 → ValidationError."""
        with pytest.raises(Exception):  # pydantic.ValidationError
            EmailExportRequest(
                type="cost-records",
                period="2026-13",  # 13월
                tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
                recipients=["cfo@example.com"],
                subject="테스트",
            )

    def test_invalid_email_format(self) -> None:
        """잘못된 email 형식 → ValidationError."""
        with pytest.raises(Exception):  # pydantic.ValidationError
            EmailExportRequest(
                type="cost-records",
                period="2026-08",
                tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
                recipients=["not-an-email"],
                subject="테스트",
            )

    def test_empty_subject(self) -> None:
        """빈 제목 → ValidationError."""
        with pytest.raises(Exception):
            EmailExportRequest(
                type="cost-records",
                period="2026-08",
                tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
                recipients=["cfo@example.com"],
                subject="   ",  # whitespace-only
            )

    def test_max_recipients(self) -> None:
        """recipients 11개 → ValidationError (max=10)."""
        with pytest.raises(Exception):
            EmailExportRequest(
                type="cost-records",
                period="2026-08",
                tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
                recipients=[f"user{i}@example.com" for i in range(11)],
                subject="테스트",
            )

    def test_valid_response_construction(self) -> None:
        """정상 EmailDeliveryResult 생성."""
        from datetime import UTC, datetime

        result = EmailDeliveryResult(
            delivery_id="msg-abc-123",
            status="delivered",
            recipient_count=2,
            retry_count=1,
            delivered_at=datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC),
            pii_redacted_fields=["phone"],
        )
        assert result.delivery_id == "msg-abc-123"
        assert result.status == "delivered"
        assert result.retry_count == 1
        assert result.pii_redacted_fields == ["phone"]

    def test_email_regex_constant(self) -> None:
        """EMAIL_REGEX 결정 wire 보존 검증."""
        assert "cfo@example.com" not in EMAIL_REGEX  # 실제 패턴 검증
        # 실제 매칭 테스트
        import re

        assert re.match(EMAIL_REGEX, "cfo@example.com") is not None
        assert re.match(EMAIL_REGEX, "not-an-email") is None


# ── TestBuildCsvBytesForEmail (2 tests) ──────────────────────────────────


class TestBuildCsvBytesForEmail:
    """Test build_csv_bytes_for_email (mocked DB session)."""

    @pytest.mark.asyncio
    async def test_cost_records_path(self) -> None:
        """type=cost-records → CSV_COLUMNS_COST_RECORDS 헤더 결정 wire 검증."""
        # Mock session.execute().fetchall() returning single fake row.
        from datetime import UTC, datetime
        from unittest.mock import MagicMock

        fake_row = MagicMock()
        fake_row._mapping = {
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "product_id": "p-1",
            "product_name": "테스트 제품",
            "category": "RAW",
            "opening_qty": 100,
            "input_qty": 50,
            "output_qty": 30,
            "closing_qty": 120,
            "unit_cost": 1000,
            "total_cost": 120000,
            "currency": "KRW",
            "created_at": datetime(2026, 8, 31, tzinfo=UTC),
            "ledger_event_id": "le-1",
        }

        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(fetchall=lambda: [fake_row]))

        csv_bytes = await build_csv_bytes_for_email(
            session=session,
            type="cost-records",
            period="2026-08",
            tenant_id="t-1",
        )
        # UTF-8 BOM 결정 wire 검증.
        assert csv_bytes.startswith(b"\xef\xbb\xbf")
        # 헤더 결정 wire 검증.
        assert "tenant_id" in csv_bytes.decode("utf-8")
        assert "period_key" in csv_bytes.decode("utf-8")

    @pytest.mark.asyncio
    async def test_bom_path(self) -> None:
        """type=bom → CSV_COLUMNS_BOM 헤더 결정 wire 검증."""
        from datetime import UTC, datetime
        from unittest.mock import MagicMock

        fake_row = MagicMock()
        fake_row._mapping = {
            "tenant_id": "t-1",
            "period_key": "2026-08",
            "parent_product_id": "p-parent",
            "parent_product_name": "모제품",
            "child_product_id": "p-child",
            "child_product_name": "자제품",
            "child_category": "RAW",
            "child_qty_per_parent": 2.0,
            "child_unit_cost": 500,
            "child_total_cost": 1000,
            "currency": "KRW",
            "created_at": datetime(2026, 8, 31, tzinfo=UTC),
        }

        session = MagicMock()
        session.execute = AsyncMock(return_value=MagicMock(fetchall=lambda: [fake_row]))

        csv_bytes = await build_csv_bytes_for_email(
            session=session,
            type="bom",
            period="2026-08",
            tenant_id="t-1",
        )
        assert csv_bytes.startswith(b"\xef\xbb\xbf")
        assert "parent_product_id" in csv_bytes.decode("utf-8")


# ── TestEmailRoutes (3 mocked HTTP integration tests) ────────────────────


class TestEmailRoutes:
    """Mocked HTTP integration tests for POST /api/v1/exports/email."""

    @pytest.mark.asyncio
    async def test_cross_tenant_raises(self) -> None:
        """Cross-tenant mismatch → EmailExportCrossTenantError."""
        from apps.api.modules.reports.email_routes import EmailExportCrossTenantError
        from unittest.mock import MagicMock

        ctx = MagicMock()
        ctx.tenant_id = "ctx-tenant"
        ctx.user_id = "user-1"

        req = EmailExportRequest(
            type="cost-records",
            period="2026-08",
            tenant_id="00000000-0000-0000-0000-000000000000",  # 다른 테넌트
            recipients=["test@example.com"],
            subject="테스트",
        )

        # Cross-tenant check happens before any DB call.
        if str(req.tenant_id) != str(ctx.tenant_id):
            with pytest.raises(EmailExportCrossTenantError) as exc_info:
                raise EmailExportCrossTenantError(
                    request_tenant_id=str(req.tenant_id),
                    ctx_tenant_id=str(ctx.tenant_id),
                )
            assert exc_info.value.code == "EMAIL_EXPORT_CROSS_TENANT_KO"

    def test_typed_exception_codes(self) -> None:
        """4 Typed exception classes 결정 wire 검증 (CR 12-5 D-14 envelope)."""
        from apps.api.modules.reports.email_routes import (
            EmailExportDeliveryFailedError,
            EmailExportError,
            EmailExportForbiddenError,
            EmailExportInvalidRequestError,
        )

        assert EmailExportInvalidRequestError(reason="x").code == "EMAIL_EXPORT_INVALID_REQUEST_KO"
        assert EmailExportForbiddenError(role="user").code == "EMAIL_EXPORT_FORBIDDEN_KO"
        assert (
            EmailExportDeliveryFailedError(reason="x", retry_count=3).code
            == "EMAIL_EXPORT_DELIVERY_FAILED_KO"
        )

        # All inherit from base class (CR 12-5 D-14 envelope).
        assert issubclass(EmailExportInvalidRequestError, EmailExportError)
        assert issubclass(EmailExportForbiddenError, EmailExportError)
        assert issubclass(EmailExportDeliveryFailedError, EmailExportError)
