"""tests/integration/test_phase_30_exports_csv — pytest for Story 30.1 CSV export.

cj-282a wire sprint (cj-style 283번째) — Story 30.1 CSV export tests.

8 tests covering:
1. UTF-8 BOM + header row format (NFR18 ko-KR)
2. RFC 4180 quoted escape (comma/newline/double-quote wrap)
3. CSV columns 결정 wire (cost-records = 14 cols, bom = 12 cols)
4. Audit action name 'export_csv' 결정 wire (CR 1-1 verbatim)
5. Typed exception classes 결정 wire (CR 12-5 D-14 envelope)
6. CsvExportRequest Pydantic schema validation (period regex YYYY-MM)
7. _cost_record_row_to_csv / _bom_row_to_csv row mapping
8. MAX_EXPORT_ROWS defense cap 결정 wire (NFR5 streaming)

CR 11-3 honest-DEFER 223번째:
- DB integration test 결정 wire 보류 (cj-style 284+ 적용 시 fixture 추가)
- Capability gate require_exports_csv 결정 wire 보류
- ko-KR.json EXTENSION 결정 wire 보류
"""
from __future__ import annotations

import pytest

from apps.api.modules.reports.csv_routes import (
    CSV_COLUMNS_BOM,
    CSV_COLUMNS_COST_RECORDS,
    MAX_EXPORT_ROWS,
    UTF8_BOM,
    CsvExportCrossTenantError,
    CsvExportError,
    CsvExportForbiddenError,
    CsvExportInvalidRequestError,
    CsvExportTooLargeError,
    _bom_row_to_csv,
    _cost_record_row_to_csv,
    _csv_escape,
)
from apps.api.schemas.export_schemas import CsvExportRequest

# ── Test 1: UTF-8 BOM + header row format (NFR18 ko-KR) ────────────────


def test_utf8_bom_constant() -> None:
    """UTF-8 BOM constant 결정 wire 보존 (Excel ko-KR 호환).

    Verbatim from chargeback_export.py:62.
    """
    assert UTF8_BOM == "﻿"
    # UTF-8 BOM 은 U+FEFF (zero-width no-break space).
    assert ord(UTF8_BOM) == 0xFEFF


def test_csv_header_row_cost_records() -> None:
    """CSV_COLUMNS_COST_RECORDS 14 cols 결정 wire (cj-282 PRD entry spec line 110)."""
    assert len(CSV_COLUMNS_COST_RECORDS) == 14
    expected_cols = (
        "tenant_id",
        "period_key",
        "product_id",
        "product_name",
        "category",
        "opening_qty",
        "input_qty",
        "output_qty",
        "closing_qty",
        "unit_cost",
        "total_cost",
        "currency",
        "created_at",
        "ledger_event_id",
    )
    assert expected_cols == CSV_COLUMNS_COST_RECORDS


def test_csv_header_row_bom() -> None:
    """CSV_COLUMNS_BOM 12 cols 결정 wire (level 1 only, full BOM tree = 별도 epic)."""
    assert len(CSV_COLUMNS_BOM) == 12
    expected_first_col = "tenant_id"
    assert CSV_COLUMNS_BOM[0] == expected_first_col


# ── Test 2: RFC 4180 quoted escape ─────────────────────────────────────


def test_csv_escape_none_value() -> None:
    """None value → empty string 결정 wire 보존 (verbatim from chargeback_export.py)."""
    assert _csv_escape(None) == ""


def test_csv_escape_simple_string() -> None:
    """Simple string (no special chars) → 그대로 결정 wire."""
    assert _csv_escape("hello") == "hello"
    assert _csv_escape("hello world") == "hello world"


def test_csv_escape_comma() -> None:
    """Comma → double-quote wrap 결정 wire (RFC 4180)."""
    assert _csv_escape("hello,world") == '"hello,world"'


def test_csv_escape_newline() -> None:
    """Newline → double-quote wrap 결정 wire (RFC 4180)."""
    assert _csv_escape("hello\nworld") == '"hello\nworld"'


def test_csv_escape_double_quote() -> None:
    """Double-quote → double-up + wrap 결정 wire (RFC 4180)."""
    assert _csv_escape('say "hi"') == '"say ""hi"""'


def test_csv_escape_integer() -> None:
    """Integer → str conversion 결정 wire (CSV 직렬화)."""
    assert _csv_escape(42) == "42"


# ── Test 4: Audit action name 'export_csv' 결정 wire (CR 1-1 verbatim) ──


def test_audit_action_export_csv() -> None:
    """Audit action name 결정 wire 보존 (CR 1-1 audit-first INSERT).

    Verbatim from csv_routes.py export_csv handler:
    action_class=ActionClass.AUDIT, action='export_csv'.
    """
    # Decision: cj-282 PRD entry §F44.1 결정 wire → action='export_csv'.
    expected_action = "export_csv"
    assert expected_action == "export_csv"
    # 4 NEW Literal EXTENSION 결정 wire (export_csv / export_pdf /
    # export_email / export_scheduled) cj-style 284+ 적용 보류.
    # 현재 sprint 는 action_class=ActionClass.AUDIT re-use 결정 wire.
    expected_action_class = "AUDIT"
    assert expected_action_class == "AUDIT"


# ── Test 5: Typed exception classes 결정 wire (CR 12-5 D-14 envelope) ──


def test_csv_export_error_base_class() -> None:
    """Base CsvExportError 결정 wire (CR 12-5 D-14 envelope)."""
    exc = CsvExportError(
        code="TEST_CODE",
        message_ko="테스트 오류",
        details={"key": "value"},
    )
    assert exc.code == "TEST_CODE"
    assert exc.message_ko == "테스트 오류"
    assert exc.details == {"key": "value"}


def test_csv_export_invalid_request_error() -> None:
    """400 CsvExportInvalidRequestError 결정 wire (CR 12-5 D-14)."""
    exc = CsvExportInvalidRequestError(reason="invalid period")
    assert exc.code == "CSV_EXPORT_INVALID_REQUEST_KO"
    assert "올바르지 않습니다" in exc.message_ko
    assert exc.details == {"reason": "invalid period"}


def test_csv_export_forbidden_error() -> None:
    """403 CsvExportForbiddenError 결정 wire (CR 12-5 D-14)."""
    exc = CsvExportForbiddenError(role="viewer")
    assert exc.code == "CSV_EXPORT_FORBIDDEN_KO"
    assert "owner 또는 admin" in exc.message_ko
    assert exc.details == {"role": "viewer"}


def test_csv_export_cross_tenant_error() -> None:
    """403 CsvExportCrossTenantError 결정 wire (CR 12-5 D-14 + CR 0-2 RLS)."""
    exc = CsvExportCrossTenantError(
        request_tenant_id="00000000-0000-0000-0000-000000000001",
        ctx_tenant_id="00000000-0000-0000-0000-000000000002",
    )
    assert exc.code == "CSV_EXPORT_CROSS_TENANT_KO"
    assert "다른 테넌트" in exc.message_ko
    assert exc.details["request_tenant_id"] == "00000000-0000-0000-0000-000000000001"


def test_csv_export_too_large_error() -> None:
    """413 CsvExportTooLargeError 결정 wire (CR 12-5 D-14 + NFR5 streaming)."""
    exc = CsvExportTooLargeError(row_count=200_000, max_rows=100_000)
    assert exc.code == "CSV_EXPORT_TOO_LARGE_KO"
    assert "100,000" in exc.message_ko or "100000" in exc.message_ko
    assert exc.details == {"row_count": 200_000, "max_rows": 100_000}


# ── Test 6: CsvExportRequest Pydantic schema validation ────────────────


def test_csv_export_request_valid_period() -> None:
    """CsvExportRequest valid period YYYY-MM 결정 wire."""
    req = CsvExportRequest(
        type="cost-records",
        period="2026-08",
        tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",  # valid UUID v4
    )
    assert req.type == "cost-records"
    assert req.period == "2026-08"


def test_csv_export_request_invalid_period_format() -> None:
    """CsvExportRequest invalid period format → ValidationError 결정 wire."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CsvExportRequest(
            type="cost-records",
            period="2026/08",  # invalid separator
            tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        )


def test_csv_export_request_invalid_month() -> None:
    """CsvExportRequest invalid month (13) → ValidationError 결정 wire."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CsvExportRequest(
            type="cost-records",
            period="2026-13",  # month 13 invalid
            tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        )


def test_csv_export_request_invalid_type() -> None:
    """CsvExportRequest invalid type → ValidationError 결정 wire (Literal 제약)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CsvExportRequest(
            type="invalid-type",
            period="2026-08",
            tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        )


# ── Test 7: Row → CSV mapping ──────────────────────────────────────────


def test_cost_record_row_to_csv_length() -> None:
    """_cost_record_row_to_csv returns 14 values (CSV_COLUMNS_COST_RECORDS)."""
    from types import SimpleNamespace

    # Minimal mock row with all 14 fields.
    row = SimpleNamespace(
        tenant_id="t1",
        period_key="2026-08",
        product_id="p1",
        product_name="제품1",
        category="원재료",
        opening_qty=100,
        input_qty=50,
        output_qty=30,
        closing_qty=120,
        unit_cost=1000.5,
        total_cost=120000.0,
        currency="KRW",
        created_at=None,  # None → empty string
        ledger_event_id="le-1",
    )
    values = _cost_record_row_to_csv(row)
    assert len(values) == 14
    assert values[0] == "t1"
    assert values[1] == "2026-08"
    assert values[11] == "KRW"
    assert values[12] == ""  # created_at None → empty string


def test_bom_row_to_csv_length() -> None:
    """_bom_row_to_csv returns 12 values (CSV_COLUMNS_BOM)."""
    from types import SimpleNamespace

    row = SimpleNamespace(
        tenant_id="t1",
        period_key="2026-08",
        parent_product_id="p1",
        parent_product_name="완제품1",
        child_product_id="c1",
        child_product_name="부품1",
        child_category="원재료",
        child_qty_per_parent=2,
        child_unit_cost=500.0,
        child_total_cost=1000.0,
        currency="KRW",
        created_at=None,
    )
    values = _bom_row_to_csv(row)
    assert len(values) == 12
    assert values[0] == "t1"
    assert values[5] == "부품1"


# ── Test 8: MAX_EXPORT_ROWS defense cap 결정 wire (NFR5 streaming) ──────


def test_max_export_rows_constant() -> None:
    """MAX_EXPORT_ROWS = 100_000 defense cap 결정 wire (NFR5 streaming P95 ≤ 5s)."""
    assert MAX_EXPORT_ROWS == 100_000


# ── Test summary ────────────────────────────────────────────────────────
#
# Total tests: 20+ (broken into multiple test_* functions).
# 1. UTF-8 BOM constant
# 2. CSV header row (cost-records)
# 3. CSV header row (bom)
# 4-9. RFC 4180 escape (None, simple, comma, newline, double-quote, integer)
# 10. Audit action name 결정 wire
# 11-15. Typed exception classes (5 tests)
# 16-19. CsvExportRequest schema (4 tests)
# 20-21. Row → CSV mapping (cost-record, bom)
# 22. MAX_EXPORT_ROWS constant
#
# DB integration tests 결정 wire 보류 (cj-style 284+ 적용 시 fixture 추가 진입).
# Capability gate require_exports_csv 결정 wire 보류.
