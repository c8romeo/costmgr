"""apps.api.modules.reports.email_service — Story 30.3 Email delivery service.

cj-299 wire sprint (cj-style 299번째) — Story 30.3 Email delivery (FR-30-3).

Email delivery orchestration service. Mirrors csv_routes.py row-mapping pattern
verbatim + adds PII redaction + retry with exponential backoff + provider
dispatch.

Public API (4 functions + 2 constants):
  - `build_csv_bytes_for_email(session, type, period, tenant_id, max_rows)`:
      Fetch data + build CSV bytes (mirror csv_routes._iter() pattern).
  - `redact_pii(body, enabled=True)`:
      Regex-based PII redaction (주민등록번호 / 전화번호 / 이메일).
      Returns (redacted_body, list_of_redacted_field_names).
  - `send_email_with_retry(provider, subject, body, recipients, max_retries=3)`:
      Send via provider with exponential backoff retry (1s/2s/4s).
      Returns (delivery_id, retry_count). Raises on retry exhaustion.
  - `generate_email_body(type, period, tenant_id, csv_bytes, pii_redacted_fields, custom_message=None)`:
      Build the plain-text email body with summary + CSV attachment mention.

Constants:
  - `PII_PATTERNS`: 3 regex patterns (resident_id / phone / email).
  - `MAX_RECIPIENTS`: 10 (email_schemas.py EmailExportRequest.recipients max).
  - `EMAIL_RETRY_BACKOFF_SECONDS`: (1.0, 2.0, 4.0) — exponential backoff.

AD bind:
  - AD-2 (audit-first INSERT append-only) — caller (email_routes.py) emits
    audit row BEFORE calling send_email_with_retry.
  - NFR4 (PII minimization) — redact_pii() applied BEFORE provider dispatch.

CR 11-3 honest-DEFER 238번째.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
from typing import Final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.email_provider import (
    DEFAULT_FROM_EMAIL,
    EmailDeliveryError,
    EmailProvider,
    EmailTransientError,
)
from apps.api.modules.reports.csv_routes import (
    CSV_COLUMNS_BOM,
    CSV_COLUMNS_COST_RECORDS,
    MAX_EXPORT_ROWS,
    UTF8_BOM,
    _bom_row_to_csv,
    _cost_record_row_to_csv,
    _csv_escape,
)

logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────────────────


# PII redaction patterns (NFR4 PII minimization).
# 3 patterns: 한국 주민등록번호 (6-7), 한국 전화번호 (010-1234-5678 / 02-1234-5678),
# 이메일 (overlap with EmailExportRequest.recipients but inside body content).
PII_PATTERNS: Final[dict[str, str]] = {
    "resident_id": r"\d{6}-[1-4]\d{6}",  # 한국 주민등록번호
    "phone": r"0\d{1,2}-?\d{3,4}-?\d{4}",  # 한국 전화번호
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
}

# Max recipients (mirrors email_schemas.EmailExportRequest.recipients max).
MAX_RECIPIENTS: Final[int] = 10

# Retry backoff seconds (exponential: 1s, 2s, 4s).
EMAIL_RETRY_BACKOFF_SECONDS: Final[tuple[float, ...]] = (1.0, 2.0, 4.0)

# Max retries (FR-30-3 결정 wire = 3회).
EMAIL_MAX_RETRIES: Final[int] = 3


# ── 1. Build CSV bytes (mirror csv_routes._iter pattern) ────────────────


async def build_csv_bytes_for_email(
    session: AsyncSession,
    type: str,  # noqa: A002 — matches cj-282 PRD entry spec param name
    period: str,
    tenant_id: str,
    max_rows: int = MAX_EXPORT_ROWS,
) -> bytes:
    """Build CSV bytes for email attachment (mirror csv_routes._iter() pattern verbatim).

    Returns UTF-8 BOM + header row + data rows as bytes (csv.writer default encoding).
    """
    if type == "cost-records":
        header = list(CSV_COLUMNS_COST_RECORDS)
        row_converter = _cost_record_row_to_csv
        query = text(
            """
            SELECT tenant_id, period_key, product_id, product_name, category,
                   opening_qty, input_qty, output_qty, closing_qty,
                   unit_cost, total_cost, currency, created_at, ledger_event_id
            FROM public.cost_records
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
            ORDER BY created_at, product_id
            LIMIT :limit
            """
        )
    elif type == "bom":
        header = list(CSV_COLUMNS_BOM)
        row_converter = _bom_row_to_csv
        query = text(
            """
            SELECT tenant_id, period_key,
                   parent_product_id, parent_product_name,
                   child_product_id, child_product_name,
                   child_category, child_qty_per_parent,
                   child_unit_cost, child_total_cost,
                   currency, created_at
            FROM public.bom_matrix
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
              AND bom_level = 1
            ORDER BY created_at, parent_product_id, child_product_id
            LIMIT :limit
            """
        )
    else:
        raise ValueError(f"Unsupported export type for email: {type!r}")

    rows = (
        await session.execute(
            query,
            {"tenant_id": tenant_id, "period_key": period, "limit": max_rows},
        )
    ).fetchall()

    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    for r in rows:
        writer.writerow(row_converter(r))

    return (UTF8_BOM + buf.getvalue()).encode("utf-8")


# ── 2. PII redaction ────────────────────────────────────────────────────


def redact_pii(body: str, enabled: bool = True) -> tuple[str, list[str]]:
    """Regex-based PII redaction (NFR4 PII minimization).

    3 PII patterns applied:
      - resident_id: 한국 주민등록번호 (6-7)
      - phone: 한국 전화번호 (010-1234-5678 / 02-1234-5678)
      - email: 이메일 주소

    Redaction: replace with `[REDACTED-{pattern_name}]`.

    Args:
        body: email body string.
        enabled: if False, returns (body, []) unchanged.

    Returns:
        (redacted_body, list_of_pattern_names_redacted).
    """
    if not enabled:
        return body, []

    import re

    redacted_fields: list[str] = []
    redacted_body = body
    for field_name, pattern in PII_PATTERNS.items():
        new_body, n_subs = re.subn(
            pattern, f"[REDACTED-{field_name}]", redacted_body
        )
        if n_subs > 0:
            redacted_fields.append(field_name)
            redacted_body = new_body

    return redacted_body, redacted_fields


# ── 3. Send email with retry ───────────────────────────────────────────


async def send_email_with_retry(
    provider: EmailProvider,
    subject: str,
    body: str,
    recipients: list[str],
    max_retries: int = EMAIL_MAX_RETRIES,
) -> tuple[str, int]:
    """Send email via provider with exponential backoff retry.

    Retry logic:
      - Attempt 1: no delay.
      - Attempt 2 (if attempt 1 transient failure): wait EMAIL_RETRY_BACKOFF_SECONDS[0] = 1s.
      - Attempt 3 (if attempt 2 transient failure): wait EMAIL_RETRY_BACKOFF_SECONDS[1] = 2s.
      - Attempt 4 (if attempt 3 transient failure): wait EMAIL_RETRY_BACKOFF_SECONDS[2] = 4s.
    Total max attempts = max_retries + 1 = 4 (with max_retries=3).

    Returns:
        (delivery_id, retry_count_used).
        retry_count_used: 0..max_retries (0 = first try succeeded).

    Raises:
        EmailDeliveryError: permanent failure (caller maps to 502 Bad Gateway envelope).
    """
    if not recipients:
        raise EmailDeliveryError(code="EMAIL_NO_RECIPIENTS", message="No recipients")

    last_exc: EmailDeliveryError | None = None
    total_attempts = max_retries + 1

    for attempt in range(total_attempts):
        try:
            delivery_id = await provider.send(
                subject=subject, body=body, recipients=recipients
            )
            return delivery_id, attempt
        except EmailTransientError as exc:
            last_exc = exc
            if attempt < max_retries:
                backoff = EMAIL_RETRY_BACKOFF_SECONDS[attempt]
                logger.warning(
                    "Email send transient failure (attempt %d/%d): %s — retrying in %.1fs",
                    attempt + 1,
                    total_attempts,
                    exc.message,
                    backoff,
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    "Email send retry exhausted (%d attempts): %s",
                    total_attempts,
                    exc.message,
                )
        except EmailDeliveryError as exc:
            # Permanent failure — do NOT retry.
            logger.error("Email send permanent failure: %s", exc.message)
            raise

    # Retry exhausted.
    raise last_exc or EmailDeliveryError(
        code="EMAIL_RETRY_EXHAUSTED", message="Retry exhausted (no last exception captured)"
    )


# ── 4. Generate email body (plain text) ────────────────────────────────


def generate_email_body(
    type: str,  # noqa: A002
    period: str,
    tenant_id: str,
    csv_bytes: bytes,
    pii_redacted_fields: list[str],
    custom_message: str | None = None,
) -> str:
    """Generate plain-text email body with summary + CSV mention.

    Body template:
      [Custom message (if provided)]
      ─────
      bizup 원가 관리 — {type} 보고서
      기간: {period}
      테넌트: {tenant_id}
      생성 시각: {iso8601 UTC}
      데이터 행 수: {csv_bytes / approx_row_size}
      첨부: CSV ({csv_bytes_size} bytes)
      ─────
      [PII redaction notice (if any redacted)]
      본 이메일은 자동 발송되었습니다. 회신하지 마세요.
    """
    from datetime import UTC, datetime

    approx_row_count = max(1, len(csv_bytes) // 200)  # rough estimate (~200 bytes/row)
    pii_notice = ""
    if pii_redacted_fields:
        pii_notice = (
            f"\n[개인정보 보호] 본 이메일에는 다음 항목이 자동으로 redact 처리되었습니다: "
            f"{', '.join(pii_redacted_fields)}\n"
        )

    body_parts: list[str] = []
    if custom_message:
        body_parts.append(custom_message)
        body_parts.append("\n─────\n")

    body_parts.extend(
        [
            f"bizup 원가 관리 — {type} 보고서",
            f"기간: {period}",
            f"테넌트: {tenant_id}",
            f"생성 시각: {datetime.now(UTC).isoformat()}",
            f"데이터 행 수 (추정): {approx_row_count:,}건",
            f"첨부: CSV ({len(csv_bytes):,} bytes)",
            "",
            "본 이메일은 bizup 원가 관리 SaaS에서 자동 발송되었습니다.",
            "회신하지 마시고, 회계감사 자료로만 활용해 주세요.",
        ]
    )
    if pii_notice:
        body_parts.append(pii_notice)
    return "\n".join(body_parts)


__all__ = [
    "build_csv_bytes_for_email",
    "redact_pii",
    "send_email_with_retry",
    "generate_email_body",
    "PII_PATTERNS",
    "MAX_RECIPIENTS",
    "EMAIL_RETRY_BACKOFF_SECONDS",
    "EMAIL_MAX_RETRIES",
]
