"""tests.services.test_bom_validation — pure-Python BOM validator tests.

Story 2.2 — Task 1.3 / Task 6.1.

Pure-function tests for `packages.services.m1_baseline.bom_validation`.
No DB, no clock, no random — matches the AD-1 / AD-5 purity contract.

Coverage:
- sum_ratios: zero, simple, decimal precision, incomplete, overflow, type errors
- is_complete_bom: true at 100, false at empty / partial / over-100
- missing_to_complete: clamps at zero, reports positive delta
- quantize_ratio: ROUND_HALF_EVEN at the half-up boundary + extra precision truncate
- BOMParentType / BOMChildType membership (drift sentinel)
- is_valid_bom_parent / is_valid_bom_child predicates
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.services.m1_baseline.bom_validation import (
    InvalidRatioTypeError,
    TARGET_TOTAL,
    is_complete_bom,
    missing_to_complete,
    quantize_ratio,
    sum_ratios,
)
from packages.services.m1_baseline.schemas import (
    BOMChildType,
    BOMParentType,
    ProductType,
    is_valid_bom_child,
    is_valid_bom_parent,
)


# ── sum_ratios ────────────────────────────────────────────────
def test_sum_ratios_zero() -> None:
    """Empty iterable → 0.0000."""
    assert sum_ratios([]) == Decimal("0.0000")


def test_sum_ratios_simple() -> None:
    """[40, 30, 20, 10] (ints) → 100.0000 (Decimal)."""
    assert sum_ratios([40, 30, 20, 10]) == Decimal("100.0000")


def test_sum_ratios_decimal() -> None:
    """4-place decimals summing to exactly 100.0000.

    CR Story 0.4 chunk-B parity — Decimal arithmetic must not drift.
    33.3333 + 33.3333 + 33.3334 = 100.0001 in float land; in Decimal
    it's exactly 100.0000.
    """
    rows = [Decimal("33.3333"), Decimal("33.3333"), Decimal("33.3334")]
    assert sum_ratios(rows) == Decimal("100.0000")


def test_sum_ratios_incomplete() -> None:
    """[40, 30, 20] → 90.0000 (not complete)."""
    assert sum_ratios([40, 30, 20]) == Decimal("90.0000")


def test_sum_ratios_overflow() -> None:
    """[60, 60] → 120.0000 — over-100 is allowed at the sum level
    (the completion check rejects it). This is by design — the user
    might temporarily have a >100% state while editing."""
    assert sum_ratios([60, 60]) == Decimal("120.0000")


def test_sum_ratios_rejects_non_numeric() -> None:
    """sum_ratios must raise InvalidRatioTypeError, not silently coerce.

    Defense-in-depth — Pydantic catches this at the wire; this catches
    any in-service caller that skipped Pydantic.
    """
    with pytest.raises(InvalidRatioTypeError):
        sum_ratios([40, "30"])  # type: ignore[list-item]


def test_sum_ratios_rejects_object_input() -> None:
    """A bare object should also be rejected."""
    with pytest.raises(InvalidRatioTypeError):
        sum_ratios([Decimal("10"), object()])  # type: ignore[list-item]


def test_sum_ratios_quantizes_extra_precision() -> None:
    """A ratio with 6 decimal places still quantizes to 4 places."""
    rows = [Decimal("33.333333")]
    # 33.333333 → 33.3333 (truncated, ROUND_HALF_EVEN).
    assert sum_ratios(rows) == Decimal("33.3333")


# ── is_complete_bom ───────────────────────────────────────────
def test_is_complete_true() -> None:
    """[100] → True."""
    assert is_complete_bom([Decimal("100")]) is True


def test_is_complete_true_multi() -> None:
    """[40, 30, 20, 10] → True."""
    assert is_complete_bom([Decimal("40"), Decimal("30"), Decimal("20"), Decimal("10")]) is True


def test_is_complete_false_empty() -> None:
    """[] → False (sum=0, expected 100)."""
    assert is_complete_bom([]) is False


def test_is_complete_false_partial() -> None:
    """[99.9999] → False (off by a tenth)."""
    assert is_complete_bom([Decimal("99.9999")]) is False


def test_is_complete_false_over() -> None:
    """[60, 60] → False (sum=120, NOT complete)."""
    assert is_complete_bom([Decimal("60"), Decimal("60")]) is False


# ── missing_to_complete ───────────────────────────────────────
def test_missing_to_complete_zero_when_full() -> None:
    """[40, 30, 20, 10] → 0.0000 (no missing)."""
    assert missing_to_complete(
        [Decimal("40"), Decimal("30"), Decimal("20"), Decimal("10")]
    ) == Decimal("0.0000")


def test_missing_to_complete_partial() -> None:
    """[40, 30, 20] → 10.0000 (10% short)."""
    assert missing_to_complete(
        [Decimal("40"), Decimal("30"), Decimal("20")]
    ) == Decimal("10.0000")


def test_missing_to_complete_negative_clamped() -> None:
    """[120] → 0.0000 (over-100 clamps to 0, NOT negative)."""
    assert missing_to_complete([Decimal("120")]) == Decimal("0.0000")


def test_missing_to_complete_empty() -> None:
    """[] → 100.0000 (entire BOM missing)."""
    assert missing_to_complete([]) == Decimal("100.0000")


# ── quantize_ratio ────────────────────────────────────────────
def test_quantize_ratio_half_even() -> None:
    """33.33335 → 33.3334 (ROUND_HALF_EVEN: 5 rounds to even).

    The 4th decimal is 3 (odd), so 5 rounds up to 4. If the 4th decimal
    were 4 (even), 5 would round DOWN to 4. The test pins the
    banker's-rounding behavior per AD-8.
    """
    result = quantize_ratio(Decimal("33.33335"))
    assert result == Decimal("33.3334")


def test_quantize_ratio_half_even_round_down() -> None:
    """33.33345 → 33.3334 (4 is even, 5 rounds DOWN to 4).

    Counter-test to the above — proves ROUND_HALF_EVEN, not HALF_UP.
    """
    result = quantize_ratio(Decimal("33.33345"))
    assert result == Decimal("33.3334")


def test_quantize_ratio_truncates_extra() -> None:
    """12.345678 → 12.3457 (extra precision truncated; HALF_EVEN at 4)."""
    assert quantize_ratio(Decimal("12.345678")) == Decimal("12.3457")


def test_quantize_ratio_no_change_when_already_4_places() -> None:
    """12.3456 → 12.3456 (idempotent)."""
    assert quantize_ratio(Decimal("12.3456")) == Decimal("12.3456")


def test_quantize_ratio_rejects_non_numeric() -> None:
    """String input → InvalidRatioTypeError."""
    with pytest.raises(InvalidRatioTypeError):
        quantize_ratio("12.34")  # type: ignore[arg-type]


# ── TARGET_TOTAL constant ─────────────────────────────────────
def test_target_total_is_100_4_places() -> None:
    """Drift sentinel — TARGET_TOTAL must be exactly 100.0000.

    If a future refactor changes this (e.g., to allow 99.9999), every
    test in this file catches the drift.
    """
    assert TARGET_TOTAL == Decimal("100.0000")


# ── BOM type rules (PRD §6.1) ─────────────────────────────────
@pytest.mark.parametrize(
    "pt",
    [ProductType.PRODUCT, ProductType.SEMI_PRODUCT],
)
def test_is_valid_bom_parent_accepts(pt: ProductType) -> None:
    """PRD §6.1 — `product` and `semi_product` are valid BOM parents."""
    assert is_valid_bom_parent(pt) is True
    assert pt in BOMParentType


@pytest.mark.parametrize(
    "pt",
    [ProductType.MATERIAL, ProductType.GOODS, ProductType.SERVICE],
)
def test_is_valid_bom_parent_rejects(pt: ProductType) -> None:
    """PRD §6.1 — `material`, `goods`, `service` are NOT valid BOM parents."""
    assert is_valid_bom_parent(pt) is False
    assert pt not in BOMParentType


@pytest.mark.parametrize(
    "pt",
    [ProductType.MATERIAL, ProductType.SEMI_PRODUCT],
)
def test_is_valid_bom_child_accepts(pt: ProductType) -> None:
    """PRD §6.1(1) — `material` and `semi_product` are valid BOM children."""
    assert is_valid_bom_child(pt) is True
    assert pt in BOMChildType


@pytest.mark.parametrize(
    "pt",
    [ProductType.PRODUCT, ProductType.GOODS, ProductType.SERVICE],
)
def test_is_valid_bom_child_rejects(pt: ProductType) -> None:
    """PRD §6.1(1) — `product`, `goods`, `service` are NOT valid BOM children."""
    assert is_valid_bom_child(pt) is False
    assert pt not in BOMChildType


def test_bom_parent_type_set_size_is_2() -> None:
    """Drift sentinel — BOM parents are exactly {product, semi_product}.

    PRD §6.1 / §8.M1(b). If a future story adds a new valid parent
    type, this test must be updated in tandem.
    """
    assert BOMParentType == frozenset(
        {ProductType.PRODUCT, ProductType.SEMI_PRODUCT}
    )


def test_bom_child_type_set_size_is_2() -> None:
    """Drift sentinel — BOM children are exactly {material, semi_product}.

    PRD §6.1(1). If a future story adds a new valid child type
    (e.g., a packaged-goods subassembly), this test must be updated.
    """
    assert BOMChildType == frozenset(
        {ProductType.MATERIAL, ProductType.SEMI_PRODUCT}
    )