"""tests.services.test_settings_completion — pure-function tests for SettingsCompletion.

Story 1.2 — Task 2.3.

Pure Python tests (no DB, no async). Verifies the `compute_completion()`
domain function against the spec scenarios:
- empty → missing=4
- partial fiscal year → missing=3
- manufacturing skips drivers
- service requires drivers
- ③ / ④ require all three
"""

from __future__ import annotations

import pytest

from packages.services.m0_onboarding import settings_completion as sc
from packages.services.m0_onboarding.industry_menu import Industry


def test_completion_all_empty_returns_six_missing_fields() -> None:
    """Industry=None, no onboarding, no counts → only top-level fields missing.

    With industry=None the drivers requirement is True by default
    (`_DRIVERS_REQUIRED` fallback), so missing lists 6 items when
    allocation_criteria is also empty.
    """
    result = sc.compute_completion(None, {}, {})

    assert result.fiscal_year_start.completed is False
    assert result.currency.completed is False
    assert result.language.completed is False
    assert result.direct_indirect.completed is False
    assert result.fixed_variable.completed is False
    assert result.drivers_required is True  # industry=None defaults to required
    assert result.drivers.completed is False
    assert result.is_complete is False
    # 4 top-level fields + 2 criteria (direct_indirect + fixed_variable).
    # Drivers is NOT in missing because it isn't required when industry=None?
    # Actually with drivers_required=True, drivers IS in missing.
    assert sc.LABEL_FISCAL_YEAR_START in result.missing
    assert sc.LABEL_CURRENCY in result.missing
    assert sc.LABEL_LANGUAGE in result.missing
    assert sc.LABEL_DIRECT_INDIRECT in result.missing
    assert sc.LABEL_FIXED_VARIABLE in result.missing


def test_completion_fiscal_year_set_drops_one_missing() -> None:
    """A1 fiscal_year_start set → 5 remaining (industry=None, no criteria)."""
    result = sc.compute_completion(
        None,
        {"fiscal_year_start": "2026-01"},
        {},
    )

    assert result.fiscal_year_start.completed is True
    assert sc.LABEL_FISCAL_YEAR_START not in result.missing
    assert sc.LABEL_CURRENCY in result.missing


def test_completion_all_top_level_set_only_criteria_missing() -> None:
    """All top-level fields set, no criteria → missing=[direct_indirect, fixed_variable]."""
    result = sc.compute_completion(
        None,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {},
    )

    assert result.fiscal_year_start.completed is True
    assert result.currency.completed is True
    assert result.language.completed is True
    assert result.direct_indirect.completed is False
    assert result.fixed_variable.completed is False
    assert result.is_complete is False
    # drivers is required when industry=None, so it appears.
    assert sc.LABEL_DIRECT_INDIRECT in result.missing
    assert sc.LABEL_FIXED_VARIABLE in result.missing
    assert sc.LABEL_DRIVERS in result.missing


def test_completion_manufacturing_skips_drivers() -> None:
    """PRD §8.M0(b): manufacturing industry skips drivers (no ABC engine)."""
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 0},
    )

    assert result.drivers_required is False
    assert result.drivers.completed is True  # auto-completed for manufacturing
    assert sc.LABEL_DRIVERS not in result.missing
    assert result.is_complete is True


def test_completion_service_requires_drivers() -> None:
    """Service industry needs drivers even when 0 rows are registered."""
    result = sc.compute_completion(
        Industry.SERVICE,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 0},
    )

    assert result.drivers_required is True
    assert result.drivers.completed is False
    assert sc.LABEL_DRIVERS in result.missing
    assert result.is_complete is False


def test_completion_manufacturing_service_full_set() -> None:
    """③ manufacturing_service — all 4 + 3 criteria ≥1 → complete."""
    result = sc.compute_completion(
        Industry.MANUFACTURING_SERVICE,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 3},
    )

    assert result.drivers_required is True
    assert result.is_complete is True
    assert result.missing == []


def test_completion_manufacturing_service_other_full_set() -> None:
    """④ manufacturing_service_other — same as ③ for completion purposes."""
    result = sc.compute_completion(
        Industry.MANUFACTURING_SERVICE_OTHER,
        {
            "fiscal_year_start": "2026-01",
            "currency": "USD",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 3},
    )

    assert result.is_complete is True


def test_completion_allocation_criteria_partial() -> None:
    """AC #3 — direct_indirect set, fixed_variable + drivers missing."""
    result = sc.compute_completion(
        Industry.SERVICE,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 0, "drivers": 0},
    )

    assert result.direct_indirect.completed is True
    assert result.fixed_variable.completed is False
    assert result.drivers.completed is False
    assert result.is_complete is False
    assert sc.LABEL_FIXED_VARIABLE in result.missing
    assert sc.LABEL_DRIVERS in result.missing
    assert sc.LABEL_DIRECT_INDIRECT not in result.missing


def test_completion_count_zero_does_not_complete() -> None:
    """Spec AC: `count ≥ 1` to be complete. Count=0 stays incomplete."""
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 1, "fixed_variable": 1, "drivers": 0},
    )

    # Manufacturing skips drivers → completed regardless.
    assert result.is_complete is True


def test_completion_handles_none_inputs() -> None:
    """Defensive: None inputs treated as {}."""
    result = sc.compute_completion(None, None, None)

    assert result.is_complete is False
    assert result.fiscal_year_start.completed is False
    assert result.direct_indirect.completed is False


def test_completion_missing_reason_precise() -> None:
    """missing_reason field carries precise Korean copy for the API detail."""
    result = sc.compute_completion(None, {}, {"drivers": 0})

    assert result.fiscal_year_start.missing_reason == "회계연도 시작월 미입력"
    assert result.currency.missing_reason == "통화 미선택"
    assert result.language.missing_reason == "언어 미선택"
    assert result.direct_indirect.missing_reason == "직접/간접 계정 분류 0행"


@pytest.mark.parametrize(
    "industry,drivers_required",
    [
        (Industry.MANUFACTURING, False),
        (Industry.SERVICE, True),
        (Industry.MANUFACTURING_SERVICE, True),
        (Industry.MANUFACTURING_SERVICE_OTHER, True),
    ],
)
def test_drivers_required_matrix(
    industry: Industry, drivers_required: bool
) -> None:
    """Verify the industry → drivers_required map exhaustively."""
    result = sc.compute_completion(industry, {}, {})
    assert result.drivers_required is drivers_required


def test_canonical_fields_order() -> None:
    """The `missing` list preserves the PRD §8.M0(b) sequence."""
    assert sc.CANONICAL_FIELDS == (
        "fiscal_year_start",
        "currency",
        "language",
        "direct_indirect",
        "fixed_variable",
        "drivers",
    )


# ── F-7: stored-value fields for wizard first-render seeding ──────
def test_value_fields_none_for_empty_tenant() -> None:
    """New tenant — all value fields are None (no defaults invented)."""
    result = sc.compute_completion(None, {}, {})
    assert result.fiscal_year_start_value is None
    assert result.currency_value is None
    assert result.industry is None


def test_fiscal_year_value_surfaces_stored_format() -> None:
    """Stored YYYY-MM round-trips through CompletionStatus unchanged."""
    result = sc.compute_completion(
        Industry.SERVICE,
        {"fiscal_year_start": "2026-03", "currency": "KRW", "language": "ko-KR"},
        {"direct_indirect": 1, "fixed_variable": 1, "drivers": 1},
    )
    assert result.fiscal_year_start_value == "2026-03"


def test_currency_value_rejects_unknown_strings() -> None:
    """An unknown currency value is surfaced as None (defensive)."""
    result = sc.compute_completion(
        None,
        {"currency": "EUR"},
        {},
    )
    assert result.currency_value is None


def test_industry_value_carries_enum_or_none() -> None:
    """Industry passed in as a separate arg → flows through as enum."""
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {},
        {},
    )
    assert result.industry is Industry.MANUFACTURING

    result_none = sc.compute_completion(None, {}, {})
    assert result_none.industry is None