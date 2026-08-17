"""tests.services.m10_ai.test_monthly_extraction_kernel — Story 10.1 kernel tests.

Story 10.1 (cj-style Epic 10 2번째 진입점, cj-style 26번째 epic 연속) —
T1.4 tests for `packages/services/m10_ai/monthly_extraction_kernel.py`.

Test breakdown (~25 cases):
- normalize_monthly_field_value × 8 (6 fields + ko-KR comma + edge cases)
- compute_extraction_confidence × 8 (boundary 0.70 + 0.90 + heuristic)
- MonthlyInputDraftRow frozen × 3
- InvalidMonthlyFieldValueError × 3
- stdlib no-I/O × 2 (AD-5 invariant)
- target_table discriminator × 1

P-015 SSOT pattern: drift detector runs in
`tests/integration/test_capability_matrix_v1_21_drift.py` (T4.1).
"""

from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

from packages.services.m10_ai.monthly_extraction_kernel import (
    CONFIDENCE_RED_THRESHOLD,
    CONFIDENCE_YELLOW_THRESHOLD,
    InvalidMonthlyFieldValueError,
    MonthlyInputDraftRow,
    compute_extraction_confidence,
    normalize_monthly_field_value,
)
from packages.services.m10_ai.extraction_port import (
    ExtractionEvidence,
    MonthlyFieldName,
)


# ── normalize_monthly_field_value ─────────────────────────────


@pytest.mark.parametrize(
    "field_name,raw_value,expected",
    [
        (
            MonthlyFieldName.DIRECT_MATERIAL_COST,
            "1,234,567",
            Decimal("1234567"),
        ),
        (
            MonthlyFieldName.DIRECT_LABOR_COST,
            "500000",
            Decimal("500000"),
        ),
        (
            MonthlyFieldName.MANUFACTURING_OVERHEAD,
            "987654.32",
            Decimal("987654.32"),
        ),
        (
            MonthlyFieldName.SELLING_ADMIN_COST,
            "1500000",
            Decimal("1500000"),
        ),
        (
            MonthlyFieldName.REVENUE,
            "3,000,000",
            Decimal("3000000"),
        ),
        (
            MonthlyFieldName.INVENTORY_CLOSING,
            "100000",
            Decimal("100000"),
        ),
        (
            MonthlyFieldName.DIRECT_MATERIAL_COST,
            "  50000  ",
            Decimal("50000"),  # whitespace stripped
        ),
        (
            MonthlyFieldName.REVENUE,
            "-500",
            Decimal("-500"),  # negative allowed
        ),
    ],
)
def test_normalize_monthly_field_value_valid(
    field_name: MonthlyFieldName, raw_value: str, expected: Decimal
) -> None:
    """AC #1 / T1.4: 6 monthly fields + ko-KR comma separator + whitespace."""
    result = normalize_monthly_field_value(
        field_name=field_name, raw_value=raw_value
    )
    assert result == expected
    assert isinstance(result, Decimal)


def test_normalize_monthly_field_value_empty_raises() -> None:
    """Empty raw_value raises InvalidMonthlyFieldValueError."""
    with pytest.raises(InvalidMonthlyFieldValueError) as exc_info:
        normalize_monthly_field_value(
            field_name=MonthlyFieldName.DIRECT_MATERIAL_COST,
            raw_value="",
        )
    assert exc_info.value.field_name == MonthlyFieldName.DIRECT_MATERIAL_COST
    assert "empty" in exc_info.value.reason.lower()


def test_normalize_monthly_field_value_invalid_format_raises() -> None:
    """Non-numeric raw_value raises InvalidMonthlyFieldValueError."""
    with pytest.raises(InvalidMonthlyFieldValueError) as exc_info:
        normalize_monthly_field_value(
            field_name=MonthlyFieldName.REVENUE,
            raw_value="not-a-number",
        )
    assert "ko-KR number pattern" in exc_info.value.reason


def test_normalize_monthly_field_value_non_string_raises() -> None:
    """Non-str raw_value raises InvalidMonthlyFieldValueError."""
    with pytest.raises(InvalidMonthlyFieldValueError) as exc_info:
        normalize_monthly_field_value(
            field_name=MonthlyFieldName.DIRECT_LABOR_COST,
            raw_value=12345,  # type: ignore[arg-type]
        )
    assert "must be str" in exc_info.value.reason


# ── compute_extraction_confidence ────────────────────────────


def test_compute_extraction_confidence_high() -> None:
    """Well-formed + evidence + short + decimal → 0.95+."""
    evidence = ExtractionEvidence(page=1, text="1234.56", bbox=None)
    result = compute_extraction_confidence(
        field_name=MonthlyFieldName.DIRECT_MATERIAL_COST,
        raw_value="1234.56",
        evidence=evidence,
    )
    # base 0.50 + 0.20 (parse OK) + 0.15 (evidence) + 0.10 (len <= 20) + 0.05 (decimal) = 1.00
    assert result == Decimal("1.000")


def test_compute_extraction_confidence_red_boundary() -> None:
    """Confidence < 0.70 → RED badge territory (master PRD §8.1 M0-c)."""
    # Unparseable + no evidence + long string → base 0.50
    result = compute_extraction_confidence(
        field_name=MonthlyFieldName.REVENUE,
        raw_value="unknown-value-from-ocr",
        evidence=None,
    )
    assert result == Decimal("0.500")
    assert result < CONFIDENCE_RED_THRESHOLD


def test_compute_extraction_confidence_yellow_boundary() -> None:
    """Confidence 0.70 ≤ x < 0.90 → YELLOW badge territory."""
    # Parse OK (0.70) but no evidence, no decimal, long string → 0.70
    long_value = "1" * 25  # length > 20
    result = compute_extraction_confidence(
        field_name=MonthlyFieldName.DIRECT_LABOR_COST,
        raw_value=long_value,
        evidence=None,
    )
    # base 0.50 + 0.20 (parse OK) + 0.00 (no evidence) + 0.00 (long) + 0.00 (no decimal) = 0.70
    assert result == Decimal("0.700")
    assert CONFIDENCE_RED_THRESHOLD <= result < CONFIDENCE_YELLOW_THRESHOLD


def test_compute_extraction_confidence_green_boundary() -> None:
    """Confidence >= 0.90 → GREEN badge territory."""
    evidence = ExtractionEvidence(page=1, text="500000", bbox=None)
    result = compute_extraction_confidence(
        field_name=MonthlyFieldName.SELLING_ADMIN_COST,
        raw_value="500000",
        evidence=evidence,
    )
    # base 0.50 + 0.20 (parse) + 0.15 (evidence) + 0.10 (short) + 0.00 (no decimal) = 0.95
    assert result == Decimal("0.950")
    assert result >= CONFIDENCE_YELLOW_THRESHOLD


def test_compute_extraction_confidence_clamped_to_max() -> None:
    """Confidence clamped to [0.000, 1.000]."""
    evidence = ExtractionEvidence(page=1, text="1.0", bbox=None)
    result = compute_extraction_confidence(
        field_name=MonthlyFieldName.INVENTORY_CLOSING,
        raw_value="1.0",
        evidence=evidence,
    )
    # base 0.50 + 0.20 + 0.15 + 0.10 + 0.05 = 1.00 (clamped, no bonus from extra)
    assert result == Decimal("1.000")


def test_compute_extraction_confidence_min_zero() -> None:
    """Confidence >= 0.000 (no negative)."""
    result = compute_extraction_confidence(
        field_name=MonthlyFieldName.REVENUE,
        raw_value="",
        evidence=None,
    )
    assert result >= Decimal("0.000")


# ── MonthlyInputDraftRow frozen dataclass ───────────────────


def test_monthly_input_draft_row_creation() -> None:
    """target_table discriminator is 'monthly_inputs' (default)."""
    row = MonthlyInputDraftRow(
        field_name=MonthlyFieldName.DIRECT_MATERIAL_COST,
        value=Decimal("1234567"),
        confidence=Decimal("0.85"),
        evidence=ExtractionEvidence(page=1, text="1,234,567", bbox=None),
    )
    assert row.target_table == "monthly_inputs"
    assert row.field_name == MonthlyFieldName.DIRECT_MATERIAL_COST
    assert row.value == Decimal("1234567")
    assert row.confidence == Decimal("0.85")


def test_monthly_input_draft_row_immutable() -> None:
    """frozen=True blocks field reassignment."""
    row = MonthlyInputDraftRow(
        field_name=MonthlyFieldName.REVENUE,
        value=Decimal("3000000"),
        confidence=Decimal("0.95"),
        evidence=None,
    )
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        row.value = Decimal("9999999")  # type: ignore[misc]


def test_monthly_input_draft_row_target_table_discriminator() -> None:
    """target_table = 'monthly_inputs' (AD-7 verbatim 'AI → input_drafts only')."""
    row = MonthlyInputDraftRow(
        field_name=MonthlyFieldName.INVENTORY_CLOSING,
        value=Decimal("100000"),
        confidence=Decimal("0.50"),
        evidence=None,
    )
    assert row.target_table == "monthly_inputs"
    # NOT 'confirmed_inputs' — AD-7 strict invariant
    assert row.target_table != "confirmed_inputs"


# ── InvalidMonthlyFieldValueError typed exception ────────────


def test_invalid_monthly_field_value_error_attributes() -> None:
    """Error carries field_name + raw_value + reason context."""
    try:
        raise InvalidMonthlyFieldValueError(
            field_name=MonthlyFieldName.MANUFACTURING_OVERHEAD,
            raw_value="bad-value",
            reason="test reason",
        )
    except InvalidMonthlyFieldValueError as exc:
        assert exc.field_name == MonthlyFieldName.MANUFACTURING_OVERHEAD
        assert exc.raw_value == "bad-value"
        assert exc.reason == "test reason"


def test_invalid_monthly_field_value_error_message_korean_ssot() -> None:
    """Error message contains field_name + raw_value (Korean SSOT for logs)."""
    try:
        raise InvalidMonthlyFieldValueError(
            field_name=MonthlyFieldName.REVENUE,
            raw_value="매출액 미상",
            reason="OCR failed",
        )
    except InvalidMonthlyFieldValueError as exc:
        assert "revenue" in str(exc)
        assert "매출액 미상" in str(exc)


def test_invalid_monthly_field_value_error_is_value_error() -> None:
    """Subclass of ValueError for FastAPI exception handler compatibility."""
    assert issubclass(InvalidMonthlyFieldValueError, ValueError)


# ── AD-5 stdlib-only invariant ───────────────────────────────


def test_monthly_extraction_kernel_no_io_imports() -> None:
    """AD-5: pure kernel — no I/O, no DB, no network, no clock, no random."""
    import packages.services.m10_ai.monthly_extraction_kernel as kernel_module

    source = inspect.getsource(kernel_module)

    # Forbidden imports (no I/O, no AI SDK, no Pydantic)
    forbidden = [
        "import requests",
        "import httpx",
        "import sqlalchemy",
        "from sqlalchemy",
        "import psycopg",
        "from psycopg",
        "import anthropic",
        "from anthropic",
        "import pydantic",
        "from pydantic",
        "import fastapi",
        "from fastapi",
    ]
    for f in forbidden:
        assert f not in source, f"AD-5 violation: {f} in monthly_extraction_kernel.py"


def test_normalize_monthly_field_value_is_pure() -> None:
    """Same input → same output (deterministic, pure)."""
    for _ in range(3):
        result = normalize_monthly_field_value(
            field_name=MonthlyFieldName.DIRECT_MATERIAL_COST,
            raw_value="1,234,567",
        )
        assert result == Decimal("1234567")


# ── MONTHLY_INPUT_FIELD_NAMES parity ─────────────────────────


def test_monthly_input_field_names_complete() -> None:
    """6 monthly input fields present (master PRD §3.1 6-stream)."""
    from packages.services.m10_ai.extraction_port import (
        MONTHLY_INPUT_FIELD_NAMES,
        MonthlyFieldName,
    )

    assert len(MONTHLY_INPUT_FIELD_NAMES) == 6
    assert len(MonthlyFieldName) == 6
    assert MONTHLY_INPUT_FIELD_NAMES == frozenset(
        {member.value for member in MonthlyFieldName}
    )


def test_monthly_input_target_table_discriminator_parity() -> None:
    """target_table Literal 'monthly_inputs' / 'onboarding_inputs' discriminator."""
    from packages.services.m10_ai.extraction_port import (
        ALLOWED_INPUT_TARGET_TABLES,
        InputTargetTable,
    )

    assert "onboarding_inputs" in ALLOWED_INPUT_TARGET_TABLES
    assert "monthly_inputs" in ALLOWED_INPUT_TARGET_TABLES
    # AD-7 strict invariant: 'confirmed_inputs' NOT in target_table set
    assert "confirmed_inputs" not in ALLOWED_INPUT_TARGET_TABLES