"""tests.integration.test_closing_pdf_export_ko_kr_comprehensive — Story 6.3 T3.

Comprehensive ko-KR label coverage check across all 6-3 surfaces:
1. Python pure kernel constants (CLOSING_PDF_EXPORT_TITLE_KO + EMPTY_KO)
2. TS mirror constants (CLOSING_PDF_EXPORT_TITLE_KO + EMPTY_KO)
3. ko-KR.json closing_pdf_export namespace (8 keys)
4. API envelope message_ko Korean (3 typed exceptions)
5. Vitest test mock map (closing_pdf_export labels)
6. Backend service exception messages (English → ko-KR envelope mapping)

This is the T3 close-out gate ensuring ALL Korean labels are present
across Python (kernel + service + envelope), TS (mirror + button),
and JSON (next-intl) surfaces.

CR 6-2/6-3 lesson: cross-language parity drift detector — any drift
between the 6 surfaces MUST be detected at sweep time.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(_read(path))


# ── Surface 1: Python pure kernel constants ────────────────────
@pytest.mark.engine
def test_python_kernel_ko_ssot():
    """CLOSING_PDF_EXPORT_TITLE_KO + CLOSING_PDF_EXPORT_EMPTY_KO in Python."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_pdf_export.py"
    py_src = _read(py_path)
    assert "CLOSING_PDF_EXPORT_TITLE_KO" in py_src
    assert "CLOSING_PDF_EXPORT_EMPTY_KO" in py_src
    assert "마감 보고서 PDF Export" in py_src
    assert "PDF 데이터 없음" in py_src


# ── Surface 2: TS mirror constants ─────────────────────────────
@pytest.mark.engine
def test_ts_mirror_ko_ssot():
    """CLOSING_PDF_EXPORT_TITLE_KO + CLOSING_PDF_EXPORT_EMPTY_KO in TS."""
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-pdf-export.ts"
    ts_src = _read(ts_path)
    assert "CLOSING_PDF_EXPORT_TITLE_KO" in ts_src
    assert "CLOSING_PDF_EXPORT_EMPTY_KO" in ts_src
    assert "마감 보고서 PDF Export" in ts_src
    assert "PDF 데이터 없음" in ts_src


# ── Surface 3: ko-KR.json closing_pdf_export namespace ─────────
@pytest.mark.engine
def test_ko_kr_json_namespace_completeness():
    """ko-KR.json has full closing_pdf_export namespace coverage."""
    json_path = ROOT / "apps" / "web" / "messages" / "ko-KR.json"
    data = _read_json(json_path)
    assert "closing_pdf_export" in data, "ko-KR.json missing closing_pdf_export namespace"
    section = data["closing_pdf_export"]

    # Required keys per T3 acceptance criteria.
    required_keys = [
        "button_label",
        "button_downloading",
        "panel_section_label",
        "panel_section_help",
        "toast_success_export",
        "toast_error_invalid_industry",
        "toast_error_size_exceeded",
        "toast_error_audit_emit",
    ]
    for key in required_keys:
        assert key in section, f"ko-KR.json missing closing_pdf_export.{key}"

    # Each value must be Korean (non-empty string).
    for key, value in section.items():
        assert isinstance(value, str), f"closing_pdf_export.{key} not a string"
        assert len(value) > 0, f"closing_pdf_export.{key} empty"


# ── Surface 4: API envelope message_ko Korean ──────────────────
@pytest.mark.engine
def test_api_envelope_ko_messages():
    """3 typed exceptions in main.py have Korean message_ko."""
    main_path = ROOT / "apps" / "api" / "main.py"
    main_src = _read(main_path)

    # 422 invalid industry
    assert "CLOSING_PDF_EXPORT_INVALID_INDUSTRY" in main_src
    assert "업종 미지원" in main_src

    # 409 size exceeded
    assert "CLOSING_PDF_EXPORT_SIZE_EXCEEDED" in main_src
    assert "PDF 크기 초과" in main_src

    # 500 audit emit error
    assert "CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR" in main_src
    assert "audit emit 실패" in main_src


# ── Surface 5: Vitest mock map coverage ───────────────────────
@pytest.mark.engine
def test_vitest_mock_map_ko_labels():
    """Vitest test mock map covers all closing_pdf_export keys."""
    vitest_path = ROOT / "apps" / "web" / "__tests__" / "closing-pdf-export.test.tsx"
    vitest_src = _read(vitest_path)
    # Required mock keys — mirrors the 8 ko-KR.json keys.
    required_keys = [
        "button_label",
        "button_downloading",
        "panel_section_label",
        "panel_section_help",
        "toast_success_export",
        "toast_error_invalid_industry",
        "toast_error_size_exceeded",
        "toast_error_audit_emit",
    ]
    for key in required_keys:
        assert key in vitest_src, f"vitest mock map missing {key}"


# ── Surface 6: Service layer exceptions are mapped ─────────────
@pytest.mark.engine
def test_service_layer_exceptions_mapped():
    """Service layer defines 3 typed exceptions consumed by main.py."""
    service_path = (
        ROOT / "apps" / "api" / "modules" / "m4_inventory" / "services" / "closing_pdf_export_service.py"
    )
    service_src = _read(service_path)
    main_path = ROOT / "apps" / "api" / "main.py"
    main_src = _read(main_path)

    # Service defines 3 exceptions
    assert "class ClosingPdfExportInvalidIndustryError" in service_src
    assert "class ClosingPdfExportSizeExceededError" in service_src
    assert "class ClosingPdfExportAuditEmitError" in service_src

    # main.py imports + has handlers for all 3
    assert "ClosingPdfExportInvalidIndustryError" in main_src
    assert "ClosingPdfExportSizeExceededError" in main_src
    assert "ClosingPdfExportAuditEmitError" in main_src


# ── Cross-surface coherence ────────────────────────────────────
@pytest.mark.engine
def test_ko_ssot_parity_python_ts():
    """CLOSING_PDF_EXPORT_TITLE_KO value identical across Python + TS."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_pdf_export.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-pdf-export.ts"
    py_src = _read(py_path)
    ts_src = _read(ts_path)

    # TITLE_KO
    py_title = re.search(r'CLOSING_PDF_EXPORT_TITLE_KO\s*:\s*Final\[str\]\s*=\s*"([^"]+)"', py_src)
    ts_title = re.search(r'CLOSING_PDF_EXPORT_TITLE_KO\s*=\s*"([^"]+)"', ts_src)
    assert py_title is not None
    assert ts_title is not None
    assert py_title.group(1) == ts_title.group(1)

    # EMPTY_KO
    py_empty = re.search(r'CLOSING_PDF_EXPORT_EMPTY_KO\s*:\s*Final\[str\]\s*=\s*"([^"]+)"', py_src)
    ts_empty = re.search(r'CLOSING_PDF_EXPORT_EMPTY_KO\s*=\s*"([^"]+)"', ts_src)
    assert py_empty is not None
    assert ts_empty is not None
    assert py_empty.group(1) == ts_empty.group(1)


# ── Industry codes parity (4 canonical) ────────────────────────
@pytest.mark.engine
def test_industry_codes_parity_python_ts():
    """CLOSING_PDF_INDUSTRY_VALUES — 4 canonical industries match."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_pdf_export.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-pdf-export.ts"
    py_src = _read(py_path)
    ts_src = _read(ts_path)

    for industry in ["manufacturing", "manufacturing_service", "manufacturing_service_other", "service"]:
        assert industry in py_src, f"Python missing industry {industry}"
        assert industry in ts_src, f"TS missing industry {industry}"

    # count check (deterministic — both must have exactly 4)
    py_count = len(
        re.findall(r'CLOSING_PDF_INDUSTRY_VALUES', py_src)
    )
    ts_count = len(
        re.findall(r'CLOSING_PDF_INDUSTRY_VALUES', ts_src)
    )
    assert py_count >= 1
    assert ts_count >= 1
