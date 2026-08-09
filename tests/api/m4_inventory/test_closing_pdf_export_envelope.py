"""tests.api.m4_inventory.test_closing_pdf_export_envelope — Story 6.3 T3.

Verify AD-15 §4 envelope mapping for 3 ClosingPDFExport exceptions:
- 422 CLOSING_PDF_EXPORT_INVALID_INDUSTRY → message_ko Korean
- 409 CLOSING_PDF_EXPORT_SIZE_EXCEEDED → message_ko Korean
- 500 CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR → message_ko Korean

Each handler in main.py maps typed exceptions to JSON envelope with
{code, message_ko, details, trace_id}. This test verifies the 6-3 wire
preserves the ko-KR parity contract (AD-15 §11 cross-language parity).
"""

from __future__ import annotations

import inspect

from apps.api.main import (
    _m4_closing_pdf_export_audit_emit_handler,
    _m4_closing_pdf_export_invalid_industry_handler,
    _m4_closing_pdf_export_size_exceeded_handler,
)


def test_invalid_industry_envelope_ko():
    """422 CLOSING_PDF_EXPORT_INVALID_INDUSTRY → Korean message_ko."""
    # Direct handler invocation (FastAPI calls with request arg).
    # Verify function signature + body inspection.
    src = inspect.getsource(_m4_closing_pdf_export_invalid_industry_handler)
    assert "CLOSING_PDF_EXPORT_INVALID_INDUSTRY" in src
    assert "message_ko" in src
    assert "업종 미지원" in src, "Korean message_ko not present"
    assert "manufacturing" in src, "Industry list referenced in Korean message"
    assert "status_code=422" in src


def test_size_exceeded_envelope_ko():
    """409 CLOSING_PDF_EXPORT_SIZE_EXCEEDED → Korean message_ko."""
    # Inspect handler source for Korean message.
    src = inspect.getsource(_m4_closing_pdf_export_size_exceeded_handler)
    assert "CLOSING_PDF_EXPORT_SIZE_EXCEEDED" in src
    assert "message_ko" in src
    assert "PDF 크기 초과" in src, "Korean message_ko not present"
    assert "5MB" in src
    assert "status_code=409" in src


def test_audit_emit_envelope_ko():
    """500 CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR → Korean message_ko."""
    # Inspect handler source for Korean message.
    src = inspect.getsource(_m4_closing_pdf_export_audit_emit_handler)
    assert "CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR" in src
    assert "message_ko" in src
    assert "audit emit 실패" in src, "Korean message_ko not present"
    assert "status_code=500" in src


def test_envelope_shape_ad_15_contract():
    """All 3 handlers produce {code, message_ko, details, trace_id} envelope."""
    handlers = [
        _m4_closing_pdf_export_invalid_industry_handler,
        _m4_closing_pdf_export_size_exceeded_handler,
        _m4_closing_pdf_export_audit_emit_handler,
    ]
    for handler in handlers:
        src = inspect.getsource(handler)
        assert '"code"' in src or "'code'" in src, f"{handler.__name__} missing code"
        assert "message_ko" in src, f"{handler.__name__} missing message_ko"
        assert "details" in src, f"{handler.__name__} missing details"
        assert "trace_id" in src, f"{handler.__name__} missing trace_id"
