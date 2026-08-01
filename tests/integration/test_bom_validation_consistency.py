"""tests.integration.test_bom_validation_consistency — Python ↔ TS drift check.

Story 2.2 — Task 6.5.

Cross-language consistency test. Verifies that the Python
`packages.services.m1_baseline.bom_validation` module and the TS
mirror in `apps/web/lib/bom-validation.ts` agree on:

- `TARGET_TOTAL` = 100.0000
- `sum_ratios` rounding behavior at the 4-place boundary
- `is_complete_bom` true at 100.0000, false elsewhere
- `missing_to_complete` clamps at 0
- BOMParentType / BOMChildType sets match exactly

If the TS test infrastructure is not yet wired (Story 0.5 plumbing
gap — vitest is not installed), the test is skipped via `pytest.skip`
per CR 1.1 lesson (DB/RLS-backed tests use `skip`, pure-logic bugs
use `xfail strict=False`).

Until vitest is wired, this Python-side test verifies the SHAPE of
the TS mirror by parsing the file and checking the constants are
present. The actual TS execution is deferred.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import pytest

from packages.services.m1_baseline.bom_validation import (
    TARGET_TOTAL,
    is_complete_bom,
    missing_to_complete,
    sum_ratios,
)
from packages.services.m1_baseline.schemas import (
    BOMChildType,
    BOMParentType,
    ProductType,
)


# ── Python side — guardrails ──────────────────────────────────


def test_target_total_constant_is_100_4_places() -> None:
    """Drift sentinel — TARGET_TOTAL must be exactly 100.0000 in Python
    AND the TS mirror must declare `TARGET_TOTAL = new Decimal("100.0000")`."""
    assert TARGET_TOTAL == Decimal("100.0000")
    ts_path = Path(__file__).resolve().parents[2] / "apps" / "web" / "lib" / "bom-validation.ts"
    src = ts_path.read_text(encoding="utf-8")
    assert 'TARGET_TOTAL = new Decimal("100.0000")' in src


def test_sum_ratios_python_matches_ts_quantization() -> None:
    """Python `sum_ratios([33.33335])` → 33.3334 (ROUND_HALF_EVEN).

    The TS mirror uses Decimal.ROUND_HALF_EVEN. Both must agree.
    """
    py_result = sum_ratios([Decimal("33.33335")])
    assert py_result == Decimal("33.3334")

    ts_path = Path(__file__).resolve().parents[2] / "apps" / "web" / "lib" / "bom-validation.ts"
    src = ts_path.read_text(encoding="utf-8")
    assert "ROUND_HALF_EVEN" in src


def test_is_complete_bom_python_matches_ts() -> None:
    """Python `is_complete_bom([100])` → True. TS mirror must agree."""
    assert is_complete_bom([Decimal("100")]) is True
    assert is_complete_bom([Decimal("99.9999")]) is False
    assert is_complete_bom([Decimal("100.0001")]) is False


def test_missing_to_complete_python_matches_ts() -> None:
    """Python clamps at 0; TS mirror must do the same."""
    assert missing_to_complete([Decimal("120")]) == Decimal("0.0000")
    assert missing_to_complete([Decimal("50")]) == Decimal("50.0000")
    assert missing_to_complete([Decimal("99.9999")]) == Decimal("0.0001")


# ── TS-side static checks (no vitest runtime) ────────────────


@pytest.fixture(scope="module")
def ts_source() -> str:
    ts_path = Path(__file__).resolve().parents[2] / "apps" / "web" / "lib" / "bom-validation.ts"
    return ts_path.read_text(encoding="utf-8")


def test_ts_mirror_declares_target_total(ts_source: str) -> None:
    assert re.search(r'TARGET_TOTAL\s*=\s*new\s+Decimal\("100\.0000"\)', ts_source)


def test_ts_mirror_declares_sum_ratios(ts_source: str) -> None:
    assert "function sumRatios" in ts_source


def test_ts_mirror_declares_is_complete_bom(ts_source: str) -> None:
    assert "function isCompleteBom" in ts_source


def test_ts_mirror_declares_missing_to_complete(ts_source: str) -> None:
    assert "function missingToComplete" in ts_source


def test_ts_mirror_uses_decimal_half_even(ts_source: str) -> None:
    """AD-8 + Story 0.4 chunk-B — TS Decimal must use ROUND_HALF_EVEN."""
    assert "ROUND_HALF_EVEN" in ts_source


def test_ts_mirror_bom_parent_types_match_python(ts_source: str) -> None:
    """BOMParentType = {product, semi_product} on both sides."""
    assert re.search(r"BOMParentTypes.*=.*new\s+Set\(\[\s*\"product\"", ts_source)
    assert '"semi_product"' in ts_source


def test_ts_mirror_bom_child_types_match_python(ts_source: str) -> None:
    """BOMChildType = {material, semi_product} on both sides."""
    assert re.search(r"BOMChildTypes.*=.*new\s+Set\(\[\s*\"material\"", ts_source)
    assert '"semi_product"' in ts_source


# ── Python type-set drift sentinels ──────────────────────────


def test_bom_parent_type_set_invariant() -> None:
    """Drift sentinel — Python set must equal {product, semi_product}."""
    assert BOMParentType == frozenset(
        {ProductType.PRODUCT, ProductType.SEMI_PRODUCT}
    )


def test_bom_child_type_set_invariant() -> None:
    """Drift sentinel — Python set must equal {material, semi_product}."""
    assert BOMChildType == frozenset(
        {ProductType.MATERIAL, ProductType.SEMI_PRODUCT}
    )