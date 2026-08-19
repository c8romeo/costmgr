"""Tests for Story 11.6 EXTENSION `apps.api.modules.m5_reports.schemas` Report #15.

Coverage (11-6 wire Surface 5 — handlers EXTENSION):
  - `Report15Request` (3 cases)
  - `Report15ActivityCostRow` (3 cases)
  - `Report15Response` (2 cases)
  - `Report15PdfRequest` (2 cases)
  - `Report15PdfResponse` (2 cases)

Total: ~12 NEW pytest cases (T4.x) — AD-15 §1 cross-language parity + envelope
schema SSOT 검증.

PRD §9 #15 verbatim wire:
  - 활동원가 내역서 (활동별 원가·동인 단가)
  - AD-15 §1: extra="forbid" envelope + min/max length invariants
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from apps.api.modules.m5_reports.schemas import (
    Report15ActivityCostRow,
    Report15PdfRequest,
    Report15PdfResponse,
    Report15Request,
    Report15Response,
)

# ── Report15Request (3 cases) ─────────────────────────────


def test_report15_request_period_key_valid() -> None:
    """SSOT — period_key min_length=1, max_length=20."""
    request = Report15Request(period_key="2026-Q1")
    assert request.period_key == "2026-Q1"


def test_report15_request_period_key_empty_raises() -> None:
    """Validation — empty period_key → ValidationError (PRD §9 #15)."""
    with pytest.raises(ValidationError) as exc_info:
        Report15Request(period_key="")
    assert "period_key" in str(exc_info.value)


def test_report15_request_period_key_too_long_raises() -> None:
    """Validation — period_key > 20 chars → ValidationError."""
    with pytest.raises(ValidationError):
        Report15Request(period_key="2026-Q1-extra-long-period-key")


# ── Report15ActivityCostRow (3 cases) ─────────────────────


def test_report15_activity_cost_row_full_fields() -> None:
    """Full envelope — 10 fields accepted (PRD §9 #15 + §7.1 ABC Step 0~3)."""
    row = Report15ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw="6600000",
        total_cost_usd="4950",
        driver_count=4,
        cost_per_driver_krw="1650000",
        cost_per_driver_usd="1237.50",
        allocated_krw="6600000",
        allocated_usd="4950",
    )
    assert row.activity_id == "act-1"
    assert row.activity_name_ko == "고객 상담"
    assert row.total_cost_krw == "6600000"


def test_report15_activity_cost_row_extra_forbid() -> None:
    """AD-15 §1 — extra="forbid" envelope 강제."""
    with pytest.raises(ValidationError) as exc_info:
        Report15ActivityCostRow(
            activity_id="act-1",
            activity_name_ko="x",
            activity_name_en="y",
            total_cost_krw="1",
            total_cost_usd="1",
            driver_count=1,
            cost_per_driver_krw="1",
            cost_per_driver_usd="1",
            allocated_krw="1",
            allocated_usd="1",
            extra_field="not_allowed",  # type: ignore[call-arg]
        )
    assert "extra_field" in str(exc_info.value)


def test_report15_activity_cost_row_negative_driver_count_raises() -> None:
    """Validation — driver_count >= 0 (ge=0 invariant)."""
    with pytest.raises(ValidationError):
        Report15ActivityCostRow(
            activity_id="act-1",
            activity_name_ko="x",
            activity_name_en="y",
            total_cost_krw="1",
            total_cost_usd="1",
            driver_count=-1,
            cost_per_driver_krw="1",
            cost_per_driver_usd="1",
            allocated_krw="1",
            allocated_usd="1",
        )


# ── Report15Response (2 cases) ───────────────────────────


def test_report15_response_envelope_assemble() -> None:
    """200 OK response — full envelope shape + report_code literal."""
    response = Report15Response(
        period_key="2026-Q1",
        activity_breakdown=[],
        v7_verdict_is_balanced=True,
        generation_hash="sha256:" + "a" * 64,
        report_code="ACTIVITY_COST_DETAIL",
        activity_count=0,
        total_driver_count=0,
        total_cost_krw="0",
        total_cost_usd="0",
    )
    assert response.report_code == "ACTIVITY_COST_DETAIL"
    assert response.period_key == "2026-Q1"
    assert response.generation_hash.startswith("sha256:")


def test_report15_response_generation_hash_length() -> None:
    """V8 invariant — generation_hash length = 7 (sha256:) + 64 = 71."""
    valid_hash = "sha256:" + "a" * 64
    response = Report15Response(
        period_key="2026-Q1",
        activity_breakdown=[],
        v7_verdict_is_balanced=True,
        generation_hash=valid_hash,
        activity_count=0,
        total_driver_count=0,
        total_cost_krw="0",
        total_cost_usd="0",
    )
    assert len(response.generation_hash) == 71


# ── Report15PdfRequest (2 cases) ─────────────────────────


def test_report15_pdf_request_period_key_valid() -> None:
    """PDF request envelope — period_key 최소 길이 1 검증."""
    body = Report15PdfRequest(period_key="2026-Q1")
    assert body.period_key == "2026-Q1"


def test_report15_pdf_request_extra_forbid() -> None:
    """AD-15 §1 — extra="forbid" envelope 강제."""
    with pytest.raises(ValidationError):
        Report15PdfRequest(period_key="2026-Q1", extra="bad")  # type: ignore[call-arg]


# ── Report15PdfResponse (2 cases) ─────────────────────────


def test_report15_pdf_response_envelope_assemble() -> None:
    """200 OK PDF response envelope — pdf_base64 + size_bytes + report_code."""
    response = Report15PdfResponse(
        period_key="2026-Q1",
        pdf_base64="JVBERi0xLjQK",
        size_bytes=4096,
        generation_hash="sha256:" + "b" * 64,
        report_code="ACTIVITY_COST_DETAIL",
    )
    assert response.pdf_base64 == "JVBERi0xLjQK"
    assert response.size_bytes == 4096
    assert response.report_code == "ACTIVITY_COST_DETAIL"


def test_report15_pdf_response_size_bytes_non_negative() -> None:
    """Validation — size_bytes >= 0."""
    response = Report15PdfResponse(
        period_key="2026-Q1",
        pdf_base64="x",
        size_bytes=0,
        generation_hash="sha256:" + "c" * 64,
    )
    assert response.size_bytes == 0
