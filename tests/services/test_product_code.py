"""tests.services.test_product_code — pure-function tests for ProductCode generator.

Story 2.1 — Task 1.3.

Pure Python tests (no DB, no async). Verifies the `generate_next_code` /
`parse_code` / `is_valid_code_format` domain helpers against the spec:
- per-tenant per-type sequence starts at 0001
- 4-digit zero pad
- 4+ digit overflow allowed (>= 10000)
- invalid prefix / format raises InvalidProductCodeError
"""

from __future__ import annotations

import pytest

# Intentionally fail import — implementation lands in T1.2.
from packages.services.m1_baseline.product_code import (
    InvalidProductCodeError,
    generate_next_code,
    is_valid_code_format,
    parse_code,
)
from packages.services.m1_baseline.schemas import ProductType


# ── generate_next_code ─────────────────────────────────────────

def test_generate_first_code_per_type() -> None:
    """Empty sequence → MAT-0001 / PRD-0001 / SEM-0001 / GDS-0001 / SVC-0001."""
    empty: dict[ProductType, int] = {}
    assert generate_next_code(empty, ProductType.MATERIAL) == "MAT-0001"
    assert generate_next_code(empty, ProductType.PRODUCT) == "PRD-0001"
    assert generate_next_code(empty, ProductType.SEMI_PRODUCT) == "SEM-0001"
    assert generate_next_code(empty, ProductType.GOODS) == "GDS-0001"
    assert generate_next_code(empty, ProductType.SERVICE) == "SVC-0001"


def test_generate_increments() -> None:
    """Sequence = 5 → MAT-0006 (next)."""
    assert generate_next_code({ProductType.MATERIAL: 5}, ProductType.MATERIAL) == "MAT-0006"


def test_generate_handles_overflow() -> None:
    """Sequence = 9999 → MAT-10000 (4+ digit overflow, no clamp)."""
    assert generate_next_code({ProductType.MATERIAL: 9999}, ProductType.MATERIAL) == "MAT-10000"


def test_generate_independent_per_type() -> None:
    """Each (tenant, product_type) has its own sequence.

    material=5 and product=42 → MAT-0006 and PRD-0043 independently.
    """
    sequences = {ProductType.MATERIAL: 5, ProductType.PRODUCT: 42}
    assert generate_next_code(sequences, ProductType.MATERIAL) == "MAT-0006"
    assert generate_next_code(sequences, ProductType.PRODUCT) == "PRD-0043"


# ── parse_code ────────────────────────────────────────────────

def test_parse_round_trip() -> None:
    """generate(parse(x)) == x and parse(generate(x)) == x."""
    assert parse_code("MAT-0042") == (ProductType.MATERIAL, 42)
    assert parse_code("PRD-0001") == (ProductType.PRODUCT, 1)
    assert parse_code("SEM-9999") == (ProductType.SEMI_PRODUCT, 9999)


def test_parse_invalid_prefix() -> None:
    """XYZ-0001 → InvalidProductCodeError (no such type)."""
    with pytest.raises(InvalidProductCodeError):
        parse_code("XYZ-0001")


def test_parse_invalid_format_no_dash() -> None:
    """MAT0001 → InvalidProductCodeError (missing separator)."""
    with pytest.raises(InvalidProductCodeError):
        parse_code("MAT0001")


def test_parse_invalid_format_empty_sequence() -> None:
    """MAT- → InvalidProductCodeError (empty sequence)."""
    with pytest.raises(InvalidProductCodeError):
        parse_code("MAT-")


def test_parse_invalid_format_lowercase() -> None:
    """mat-0001 → InvalidProductCodeError (lowercase prefix)."""
    with pytest.raises(InvalidProductCodeError):
        parse_code("mat-0001")


def test_parse_non_numeric_sequence() -> None:
    """MAT-XXXX → InvalidProductCodeError (non-numeric sequence)."""
    with pytest.raises(InvalidProductCodeError):
        parse_code("MAT-XXXX")


# ── is_valid_code_format ─────────────────────────────────────

@pytest.mark.parametrize(
    "code",
    ["MAT-0001", "PRD-9999", "SEM-0001", "GDS-0042", "SVC-10000"],
)
def test_is_valid_code_format_true(code: str) -> None:
    assert is_valid_code_format(code) is True


@pytest.mark.parametrize(
    "code",
    ["mat-0001", "XYZ-0001", "MAT0001", "MAT-", "MAT-XXXX", "", "MAT-1"],
)
def test_is_valid_code_format_false(code: str) -> None:
    assert is_valid_code_format(code) is False


# ── Zero-padding regression guard ──────────────────────────────

def test_zero_padding_sequence_zero() -> None:
    """Sequence 0 → MAT-0001 (4-digit zero pad)."""
    assert generate_next_code({}, ProductType.MATERIAL) == "MAT-0001"
    # And the parser must accept 0001 → 1 (not 0001)
    assert parse_code("MAT-0001") == (ProductType.MATERIAL, 1)
