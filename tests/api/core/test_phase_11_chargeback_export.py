# tests/api/core/test_phase_11_chargeback_export.py —
# Phase 11 T4 (cj-style 107번째 wire) — Chargeback export tests.
# 6 cases per cj-style Phase 10 SLO pattern verbatim mirror.
import io

import pytest

from apps.api.core.errors import (
    ChargebackExportError,
    ChargebackExportRateLimitedError,
)
from apps.api.modules.finops.chargeback_export import (
    CSV_COLUMNS,
    CSV_HEADER_ROW,
    EXPORT_RATE_LIMIT_PER_MINUTE_DEFAULT,
    UTF8_BOM,
    ChargebackExportRateLimitTracker,
    audit_first_insert_chargeback_export_rate_limited,
    audit_first_insert_chargeback_exported,
    export_chargeback_csv,
    export_chargeback_pdf,
)


def _sample_row(**overrides):
    base = {
        "chargeback_id": "cb-1",
        "tenant_slug": "acme",
        "period_key": "2026-08",
        "department_id": "dept-1",
        "cost_center_id": "CC-0001",
        "rule_type": "flat_fee",
        "base_amount": "1000.00",
        "markup_amount": "100.00",
        "tax_amount": "110.00",
        "total_amount": "1210.00",
        "currency_code": "KRW",
        "computed_at": "2026-08-24T00:00:00Z",
        "trace_id": "trace-1",
    }
    base.update(overrides)
    return base


def test_csv_streaming_yields_bom_and_header():
    chunks = list(export_chargeback_csv([]))
    assert len(chunks) == 1
    decoded = chunks[0].decode("utf-8")
    assert decoded.startswith(UTF8_BOM)
    header = decoded[len(UTF8_BOM):].rstrip("\r\n")
    assert header == CSV_HEADER_ROW
    assert header.count(",") == len(CSV_COLUMNS) - 1


def test_csv_streaming_renders_row():
    rows = [_sample_row()]
    chunks = list(export_chargeback_csv(rows))
    decoded = b"".join(chunks).decode("utf-8")
    assert "cb-1" in decoded
    assert "CC-0001" in decoded
    assert "1210.00" in decoded


def test_csv_escapes_double_quote_in_field():
    rows = [_sample_row(department_id='dept"with"quote')]
    chunks = list(export_chargeback_csv(rows))
    decoded = b"".join(chunks).decode("utf-8")
    # CSV double-quote escape: " becomes ""
    assert '"dept""with""quote"' in decoded


def test_pdf_export_returns_bytes_with_tenant_period_header():
    rows = [_sample_row()]
    pdf_bytes = export_chargeback_pdf(
        rows,
        tenant_slug="acme",
        period_key="2026-08",
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"acme" in pdf_bytes
    assert b"2026-08" in pdf_bytes


def test_pdf_export_empty_rows():
    pdf_bytes = export_chargeback_pdf(
        [],
        tenant_slug="acme",
        period_key="2026-08",
    )
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"rows=0" in pdf_bytes


def test_rate_limit_blocks_second_export_within_60_seconds():
    tracker = ChargebackExportRateLimitTracker(per_minute=1)
    tracker.check_and_record("tenant-a")
    with pytest.raises(ChargebackExportRateLimitedError) as excinfo:
        tracker.check_and_record("tenant-a")
    assert excinfo.value.http_status == 429
    assert excinfo.value.code == "CHARGEBACK_EXPORT_RATE_LIMITED"
    assert "retry_after_seconds" in excinfo.value.details


def test_rate_limit_default_per_minute():
    assert EXPORT_RATE_LIMIT_PER_MINUTE_DEFAULT == 1


def test_audit_first_insert_chargeback_exported():
    payload = audit_first_insert_chargeback_exported(
        tenant_id="t1",
        period_key="2026-08",
        export_format="csv",
        row_count=42,
        file_size_bytes=1234,
        actor_id="u1",
        trace_id="trace-1",
    )
    assert payload["action"] == "chargeback_exported"
    assert payload["action_class"] == "FINOPS"
    assert payload["module_id"] == "m19_finops"
    assert payload["row_count"] == 42


def test_audit_first_insert_chargeback_export_rate_limited():
    payload = audit_first_insert_chargeback_export_rate_limited(
        tenant_id="t1",
        actor_id="u1",
        retry_after_seconds=30,
        trace_id="trace-1",
    )
    assert payload["action"] == "chargeback_export_rate_limited"
    assert payload["retry_after_seconds"] == 30
    assert payload["audit_first"] is True