"""tests.api.test_jsonb_schemas — JSONB validator tests (Story 1.2 Task 1.1).

Verifies `apps/api/core/jsonb_schemas.py` against the canonical schema in
`docs/onboarding-schema.md`. Pure-Python tests — no DB.
"""

from __future__ import annotations

import pytest

from apps.api.core.jsonb_schemas import (
    OnboardingField,
    OnboardingValidationError,
    enforce_onboarding_schema,
    validate_onboarding_schema,
)


def test_validate_onboarding_empty_passes_partial() -> None:
    """Empty JSONB with partial=True passes (every field is optional)."""
    errors = validate_onboarding_schema({}, partial=True)
    assert errors == []


def test_validate_onboarding_full_required_partial_false() -> None:
    """`partial=False` requires every canonical field to be present + valid."""
    errors = validate_onboarding_schema(
        {
            "industry": "manufacturing",
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
            "allocation_criteria": {
                "direct_indirect": {"completed": True, "count": 5},
                "fixed_variable": {"completed": True, "count": 5},
                "drivers": {"completed": False, "count": 0},
            },
        },
        partial=False,
    )
    assert errors == []


def test_validate_invalid_industry_returns_error() -> None:
    """Unknown industry value is flagged (defends against JSONB corruption)."""
    errors = validate_onboarding_schema({"industry": "construction"})
    assert len(errors) == 1
    assert errors[0].field == "industry"
    assert "unknown industry value" in errors[0].reason


def test_validate_invalid_fiscal_year_format() -> None:
    """Invalid YYYY-MM is flagged (month > 12)."""
    errors = validate_onboarding_schema({"fiscal_year_start": "2026-13"})
    assert len(errors) == 1
    assert errors[0].field == "fiscal_year_start"


def test_validate_invalid_fiscal_year_low_month() -> None:
    """Month 00 is flagged (PRD A1: 01..12)."""
    errors = validate_onboarding_schema({"fiscal_year_start": "2026-00"})
    assert len(errors) == 1


def test_validate_invalid_fiscal_year_non_numeric() -> None:
    """Non-numeric year is flagged."""
    errors = validate_onboarding_schema({"fiscal_year_start": "abcd-01"})
    assert len(errors) == 1


def test_validate_invalid_currency() -> None:
    """Currency outside the {KRW, USD} set is flagged."""
    errors = validate_onboarding_schema({"currency": "EUR"})
    assert len(errors) == 1
    assert errors[0].field == "currency"


def test_validate_invalid_language() -> None:
    """Language outside MVP set is flagged (NFR-18: ko-KR only)."""
    errors = validate_onboarding_schema({"language": "en-US"})
    assert len(errors) == 1
    assert errors[0].field == "language"


def test_validate_allocation_criteria_unknown_key() -> None:
    """Unknown criterion key is flagged."""
    errors = validate_onboarding_schema(
        {"allocation_criteria": {"unknown_criterion": {"completed": True}}}
    )
    assert any("unknown_criterion" in e.field for e in errors)


def test_validate_allocation_criteria_count_non_int() -> None:
    """count must be int ≥ 1."""
    errors = validate_onboarding_schema(
        {"allocation_criteria": {"direct_indirect": {"completed": True, "count": "five"}}}
    )
    assert any(e.field == "allocation_criteria.direct_indirect.count" for e in errors)


def test_validate_allocation_criteria_completed_non_bool() -> None:
    """completed must be bool."""
    errors = validate_onboarding_schema(
        {"allocation_criteria": {"direct_indirect": {"completed": "yes", "count": 5}}}
    )
    assert any(e.field == "allocation_criteria.direct_indirect.completed" for e in errors)


def test_validate_allocation_criteria_not_object() -> None:
    """allocation_criteria must be an object."""
    errors = validate_onboarding_schema({"allocation_criteria": "broken"})
    assert any(e.field == "allocation_criteria" for e in errors)


def test_enforce_raises_on_corrupt_jsonb() -> None:
    """`enforce_onboarding_schema` raises `OnboardingValidationError`."""
    with pytest.raises(OnboardingValidationError) as exc_info:
        enforce_onboarding_schema(
            {"industry": "unknown"},
            trace_id="trace-1",
            partial=True,
        )
    assert exc_info.value.trace_id == "trace-1"
    assert any(e.field == "industry" for e in exc_info.value.errors)


def test_enforce_passes_clean_jsonb() -> None:
    """No errors → no raise."""
    enforce_onboarding_schema(
        {"industry": "service", "currency": "KRW"},
        trace_id="trace-2",
        partial=True,
    )


def test_onboarding_field_enum_values() -> None:
    """The OnboardingField enum exposes the canonical field names."""
    assert OnboardingField.INDUSTRY.value == "industry"
    assert OnboardingField.FISCAL_YEAR_START.value == "fiscal_year_start"
    assert OnboardingField.CURRENCY.value == "currency"
    assert OnboardingField.LANGUAGE.value == "language"
    assert OnboardingField.ALLOCATION_CRITERIA.value == "allocation_criteria"


def test_validate_partial_skips_absent_top_level_fields() -> None:
    """partial=True skips fields not present (default behavior)."""
    # Only `industry` set; the other 3 fields aren't flagged because partial=True.
    errors = validate_onboarding_schema(
        {"industry": "manufacturing"},
        partial=True,
    )
    assert errors == []