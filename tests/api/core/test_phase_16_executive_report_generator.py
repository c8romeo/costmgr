"""tests.api.core.test_phase_16_executive_report_generator — Phase 16 executive report tests.

Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.3 verbatim + AD-43 (c) decision). 3 export_format
PDF/CSV/Excel + 3 cadence monthly/quarterly/annual.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from apps.api.modules.finops.executive_report_generator import (
    generate_executive_report,
)
from apps.api.modules.finops.reporting.serializers import (
    ALL_CADENCES,
    ALL_EXPORT_FORMATS,
)


TENANT_ID = str(uuid.uuid4())


# ── 9 NEW pytest cases ──────────────────────────────────────
def test_executive_report_typed_dict_13_fields() -> None:
    """Test 1: ExecutiveReport TypedDict has all 13 fields (PRD §F32.3-7)."""
    report = generate_executive_report(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        cadence="monthly",
        export_format="pdf",
        dry_run=True,
    )
    expected_fields = {
        "report_id",
        "tenant_id",
        "scope_type",
        "scope_id",
        "period_key",
        "cadence",
        "export_format",
        "report_file_url",
        "report_size_bytes",
        "report_generated_at",
        "generated_by",
        "status",
        "trace_id",
    }
    assert set(report.keys()) == expected_fields


def test_3_export_formats_supported() -> None:
    """Test 2: 3 export_format options (PDF/CSV/Excel)."""
    assert set(ALL_EXPORT_FORMATS) == {"pdf", "csv", "excel"}


def test_3_cadences_supported() -> None:
    """Test 3: 3 cadence options (monthly/quarterly/annual)."""
    assert set(ALL_CADENCES) == {"monthly", "quarterly", "annual"}


def test_generate_pdf_report_in_dry_run() -> None:
    """Test 4: PDF report generation succeeds in dry-run."""
    report = generate_executive_report(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        cadence="monthly",
        export_format="pdf",
        dry_run=True,
    )
    assert report["export_format"] == "pdf"
    assert report["cadence"] == "monthly"


def test_generate_csv_report_in_dry_run() -> None:
    """Test 5: CSV report generation succeeds in dry-run."""
    report = generate_executive_report(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        cadence="quarterly",
        export_format="csv",
        dry_run=True,
    )
    assert report["export_format"] == "csv"
    assert report["cadence"] == "quarterly"


def test_generate_excel_report_in_dry_run() -> None:
    """Test 6: Excel report generation succeeds in dry-run."""
    report = generate_executive_report(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026",
        cadence="annual",
        export_format="excel",
        dry_run=True,
    )
    assert report["export_format"] == "excel"
    assert report["cadence"] == "annual"


def test_invalid_export_format_raises_error() -> None:
    """Test 7: invalid export_format raises typed exception."""
    from apps.api.core.errors import ExecutiveReportExportError
    import pytest
    with pytest.raises(ExecutiveReportExportError):
        generate_executive_report(
            tenant_id=TENANT_ID,
            scope_type="tenant",
            scope_id="default",
            period_key="2026-08",
            cadence="monthly",
            export_format="invalid_format",
            dry_run=True,
        )


def test_invalid_cadence_raises_error() -> None:
    """Test 8: invalid cadence raises typed exception."""
    from apps.api.core.errors import CronExpressionInvalidError
    import pytest
    with pytest.raises(CronExpressionInvalidError):
        generate_executive_report(
            tenant_id=TENANT_ID,
            scope_type="tenant",
            scope_id="default",
            period_key="2026-08",
            cadence="invalid_cadence",
            export_format="pdf",
            dry_run=True,
        )


def test_report_status_initial_value() -> None:
    """Test 9: report.status starts as 'generating' or 'completed' in dry-run."""
    report = generate_executive_report(
        tenant_id=TENANT_ID,
        scope_type="tenant",
        scope_id="default",
        period_key="2026-08",
        cadence="monthly",
        export_format="pdf",
        dry_run=True,
    )
    assert report["status"] in {"generating", "completed"}