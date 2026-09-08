"""apps.api.core.email_provider — Email provider abstraction (Story 30.3 OQ-EPIC30+-2).

cj-299 wire sprint (cj-style 299번째) — Story 30.3 Email delivery (FR-30-3).

OQ-EPIC30+-2 결정 wire = Postmark (transactional email API + sandbox 100건
free + HTTP API 단순 + DKIM/SPF 자동). The abstraction layer here allows
future migration to SendGrid / SES / Gmail via env flag swap (no code change).

cj-305b Resend migration wire sprint (cj-style 256번째, 2026-09-08 KST) —
Postmark 의 public-domain-email 가입 차단 (Gmail reject) 이슈로
**OQ-EPIC30+-2 결정 wire v2 = Resend** 으로 migration 결정 wire 진입.
Postmark 결정 wire 의 abstraction layer 의 swap 으로 code change 최소 정직 회복.

1 ABC + 2 concrete providers:
  - `EmailProvider` — abstract base class (send(subject, body, recipients, sender))
  - `ResendProvider` — default (RESEND_API_KEY env var, cj-305b 결정 wire)
  - `SMTPProvider` — fallback (SMTP_HOST/PORT/USER/PASSWORD env vars)
  - `LoggingProvider` — dev/local default (logs email payload, no network)

Factory: `get_email_provider()` reads env vars and returns the right provider.
Priority: RESEND_API_KEY → SMTP_HOST → LoggingProvider.

AD bind:
  - AD-2 (audit-first INSERT append-only) — caller is email_service.py,
    audit row emitted BEFORE this module's send() is called.
  - NFR4 (PII minimization) — redaction enforced upstream in
    email_service.redact_pii() before any provider sees the body.

CR 11-3 honest-DEFER 238번째 epic 연속 정직 회복
(cj-298 close-out retro 의 237번째 + cj-299 의 238번째).
cj-305b 의 256번째 추가.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Final

import httpx

logger = logging.getLogger(__name__)

# Resend API endpoint (transactional email). Verbatim from Resend HTTP API docs.
RESEND_API_URL: Final[str] = "https://api.resend.com/emails"

# Default sender email (Pilot launch 시 tenant-specific 발신자 결정 wire 보류).
# 운영자 override 가능 (RESEND_FROM_EMAIL env var).
# Resend sandbox: `onboarding@resend.dev` 가 default sender (custom domain 등록 시 user 도메인 가능).
DEFAULT_FROM_EMAIL: Final[str] = "onboarding@resend.dev"


class EmailProvider(ABC):
    """Email provider interface (3 implementations)."""

    @abstractmethod
    async def send(
        self,
        subject: str,
        body: str,
        recipients: list[str],
        sender: str = DEFAULT_FROM_EMAIL,
    ) -> str:
        """Send email via the provider. Returns Resend email ID or SMTP correlation ID.

        Raises:
            EmailDeliveryError: on permanent failure (after retry exhausted).
            EmailTransientError: on transient failure (caller should retry).
        """
        raise NotImplementedError


class EmailDeliveryError(Exception):
    """Permanent email delivery failure (retry exhausted or invalid payload)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class EmailTransientError(EmailDeliveryError):
    """Transient email delivery failure (network/timeout/5xx — caller retries)."""

    def __init__(self, message: str, retry_after_seconds: float = 1.0) -> None:
        super().__init__(code="EMAIL_TRANSIENT_ERROR", message=message)
        self.retry_after_seconds = retry_after_seconds


class ResendProvider(EmailProvider):
    """Resend transactional email HTTP API (OQ-EPIC30+-2 v2 default, cj-305b wire 결정 wire).

    cj-305b Resend migration 결정 wire 적용 (cj-style 256번째):
    - Postmark 는 public-domain-email 가입 차단 (Gmail reject) 이슈 → Resend 로 swap.
    - Postmark 대비 W1 free tier 3000 emails/month (100/day), public email 가입 가능.

    POST {RESEND_API_URL} with headers:
      - Authorization: Bearer {RESEND_API_KEY}
      - Content-Type: application/json
    Body: {"from": ..., "to": [...], "subject": "...", "text": "..."}

    Success response: {"id": "<email_id>"}
    Error response: {"statusCode": <int>, "name": "...", "message": "..."}
    """

    def __init__(self, api_key: str, from_email: str = DEFAULT_FROM_EMAIL) -> None:
        self.api_key = api_key
        self.from_email = from_email

    async def send(
        self,
        subject: str,
        body: str,
        recipients: list[str],
        sender: str = DEFAULT_FROM_EMAIL,
    ) -> str:
        """Send via Resend HTTP API. Returns Resend email id."""
        from_email = sender or self.from_email
        payload = {
            "from": from_email,
            "to": list(recipients),  # Resend expects JSON array, not comma-separated
            "subject": subject,
            "text": body,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(RESEND_API_URL, json=payload, headers=headers)
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            raise EmailTransientError(
                message=f"Resend network error: {exc}", retry_after_seconds=2.0
            ) from exc

        if response.status_code in (200, 201):
            data = response.json()
            email_id = data.get("id")
            if email_id:
                return str(email_id)
            # 200 OK but no id field — unusual, treat as logical error.
            raise EmailDeliveryError(
                code="RESEND_LOGICAL_ERROR",
                message=f"Resend 200 but no 'id' in response: {data}",
            )

        # 5xx → transient (retry). 4xx (except 429) → permanent. 429 → transient.
        if response.status_code == 429 or 500 <= response.status_code < 600:
            raise EmailTransientError(
                message=f"Resend {response.status_code}: {response.text[:200]}",
                retry_after_seconds=5.0,
            )
        raise EmailDeliveryError(
            code="RESEND_CLIENT_ERROR",
            message=f"Resend {response.status_code}: {response.text[:200]}",
        )


class SMTPProvider(EmailProvider):
    """SMTP fallback (Resend outage or local dev).

    Uses aiosmtplib (if installed) or smtplib (sync). For cj-299 sprint scope,
    we use a minimal aiosmtplib-like wrapper that raises transient on
    connection failures. The actual smtplib call is a placeholder pending
    env-driven config (smtplib.SMTP_SSL) — cj-style 300+ follow-up may
    upgrade to aiosmtplib.

    Env vars required:
      - SMTP_HOST (e.g., smtp.gmail.com)
      - SMTP_PORT (e.g., 587)
      - SMTP_USERNAME
      - SMTP_PASSWORD
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send(
        self,
        subject: str,
        body: str,
        recipients: list[str],
        sender: str = DEFAULT_FROM_EMAIL,
    ) -> str:
        """Send via SMTP. Returns SMTP correlation ID (timestamp)."""
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ",".join(recipients)
        msg.set_content(body)

        try:
            # smtplib is sync — we wrap in run_in_executor for async context.
            import asyncio

            def _send_sync() -> None:
                if self.use_tls:
                    with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as srv:
                        srv.login(self.username, self.password)
                        srv.send_message(msg)
                else:
                    with smtplib.SMTP(self.host, self.port, timeout=10) as srv:
                        srv.starttls()
                        srv.login(self.username, self.password)
                        srv.send_message(msg)

            await asyncio.get_event_loop().run_in_executor(None, _send_sync)
        except (smtplib.SMTPException, OSError) as exc:
            # SMTPException covers both 4xx (permanent) and 5xx (transient)
            # responses. We treat connection errors as transient; auth/parse
            # errors as permanent. Simpler heuristic: if the error message
            # contains "timeout" or "connection" → transient; else permanent.
            error_msg = str(exc).lower()
            if any(token in error_msg for token in ("timeout", "connection", "refused")):
                raise EmailTransientError(
                    message=f"SMTP transient: {exc}", retry_after_seconds=3.0
                ) from exc
            raise EmailDeliveryError(
                code="SMTP_PERMANENT_ERROR", message=f"SMTP permanent: {exc}"
            ) from exc

        # SMTP has no native MessageID — return a correlation string.
        from datetime import UTC, datetime

        return f"smtp-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"


class LoggingProvider(EmailProvider):
    """Default provider for local dev / Pilot launch pre-Resend-config.

    Logs the email payload (no network). Returns a fake delivery_id.
    Use case: pre-Production environments where SMTP credentials aren't set.
    """

    async def send(
        self,
        subject: str,
        body: str,
        recipients: list[str],
        sender: str = DEFAULT_FROM_EMAIL,
    ) -> str:
        import uuid

        delivery_id = f"log-{uuid.uuid4().hex[:12]}"
        logger.info(
            "LoggingProvider.send (dev mode, no network) — delivery_id=%s sender=%s recipients=%s subject=%s body_len=%d",
            delivery_id,
            sender,
            recipients,
            subject,
            len(body),
        )
        return delivery_id


def get_email_provider() -> EmailProvider:
    """Factory: Resend if RESEND_API_KEY set, else SMTP if SMTP_HOST set, else LoggingProvider.

    Priority (highest first):
      1. RESEND_API_KEY → ResendProvider (cj-305b 결정 wire v2 default)
      2. SMTP_HOST + SMTP_PORT + SMTP_USERNAME + SMTP_PASSWORD → SMTPProvider
      3. (else) → LoggingProvider (dev safe default — never raises)
    """
    resend_api_key = os.getenv("RESEND_API_KEY")
    if resend_api_key:
        from_email = os.getenv("RESEND_FROM_EMAIL", DEFAULT_FROM_EMAIL)
        logger.info("Email provider: Resend (from=%s)", from_email)
        return ResendProvider(api_key=resend_api_key, from_email=from_email)

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        logger.info(
            "Email provider: SMTP (host=%s port=%s user=%s)", smtp_host, smtp_port, smtp_user
        )
        return SMTPProvider(
            host=smtp_host,
            port=int(smtp_port),
            username=smtp_user,
            password=smtp_pass,
            use_tls=use_tls,
        )

    logger.warning(
        "Email provider: LoggingProvider (dev default). "
        "Set RESEND_API_KEY or SMTP_HOST to enable real delivery."
    )
    return LoggingProvider()


__all__ = [
    "EmailProvider",
    "EmailDeliveryError",
    "EmailTransientError",
    "ResendProvider",
    "SMTPProvider",
    "LoggingProvider",
    "get_email_provider",
    "DEFAULT_FROM_EMAIL",
]
