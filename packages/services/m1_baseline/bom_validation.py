"""packages.services.m1_baseline.bom_validation — pure BOM validators (Story 2.2).

Pure-Python, stdlib-only module (AD-1 / AD-5). NO DB, NO clock, NO random.

Holds the **pure** transformations and invariants for the BOM matrix:

- `TARGET_TOTAL` — the 100% invariant (AD-8 + A6 axiom).
- `sum_ratios` — Decimal-arithmetic sum, no float (AD-8 strict).
- `is_complete_bom` — `sum == TARGET_TOTAL` check (A6 derived invariant).
- `missing_to_complete` — `max(TARGET_TOTAL - sum, 0)` (UX: "{missing}% 부족").
- `quantize_ratio` — `ROUND_HALF_EVEN` to 4 decimal places (AD-8 parity).

The DB-level `bom_lines.ratio` is `NUMERIC(7,4)` (max 100.0000, 4 decimals).
The Pydantic schema `BOMRowInput.ratio` carries `max_digits=7, decimal_places=4`
defense-in-depth at the wire boundary. This module is the third layer of
defense: any caller that constructs a `Decimal` for storage must run it
through `quantize_ratio()` first.

Why this lives in `packages/services/` (not `apps/api/`):
- Story 2.2 TS mirror lives at `apps/web/lib/bom-validation.ts`.
- Drift is caught by `tests/integration/test_bom_validation_consistency.py`.
- AD-11 layer rule — `apps/api/core/` may NOT import `packages.cost_engine`
  directly, and pure helpers belong in `packages/services/` so both API
  and web can share them.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

# ── A6 invariant — 100.0000% complete ───────────────────────────
# NUMERIC(7,4) → 4 decimal places, max 100.0000. Matches the DB column
# precision so the on-disk sum and the in-Python sum are bit-identical.
TARGET_TOTAL: Final[Decimal] = Decimal("100.0000")

# Quantization granularity — `Decimal("0.0001")` enforces 4-decimal-place
# rounding via `ROUND_HALF_EVEN` (AD-8 + Story 0.4 chunk-B Decimal.set parity).
_RATIO_QUANTUM: Final[Decimal] = Decimal("0.0001")


# ── Typed errors (mapped to HTTP by handlers.py) ──────────────
class BOMValidationError(ValueError):
    """Base class for BOM pure-validation failures.

    Subclasses carry `details` and `trace_id` for the AD-15 §4 envelope.
    """


class InvalidRatioTypeError(BOMValidationError):
    """422 BOM_INVALID_RATIO — a non-numeric value was passed to `sum_ratios`.

    Defense-in-depth — Pydantic `BOMRowInput.ratio: Decimal = Field(...)`
    should reject this at the wire boundary. If a service-level call
    skips Pydantic, this exception fires instead of silently coercing
    (which would invite `float` arithmetic drift).
    """

    def __init__(self, value: object) -> None:
        super().__init__(f"ratio must be Decimal, int, or float; got {type(value).__name__}")
        self.value = value


# ── Public helpers ────────────────────────────────────────────
def sum_ratios(rows: Iterable[Decimal | float | int]) -> Decimal:
    """Pure: sum an iterable of ratios as Decimal with 4-decimal precision.

    Defense-in-depth: rejects non-numeric inputs (would otherwise coerce
    to Decimal incorrectly or raise `TypeError` from `Decimal(float)`'s
    own checks).

    Args:
        rows: An iterable of `Decimal`, `int`, or `float`. `float` is
            accepted (not encouraged) for legacy callers; the function
            uses `Decimal(value)` conversion which traps `NaN` / `Inf`.

    Returns:
        `Decimal` quantized to 4 decimal places (the NUMERIC(7,4) DB
        precision). `ROUND_HALF_EVEN` per AD-8.

    Raises:
        InvalidRatioTypeError: A non-numeric value was in the iterable.
        decimal.InvalidOperation: `NaN` / `Inf` (from float → Decimal).
    """
    total = Decimal("0")
    for r in rows:
        if isinstance(r, Decimal | int):
            total += Decimal(r)
        elif isinstance(r, float):
            # Decimal(float) traps NaN / Inf via InvalidOperation.
            total += Decimal(r)
        else:
            raise InvalidRatioTypeError(r)
    return total.quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def is_complete_bom(rows: Iterable[Decimal]) -> bool:
    """Pure: is the BOM complete? (A6 axiom: `sum == 100.0000`).

    An empty BOM is NOT complete (`sum == 0`, expected `100`).
    A BOM summing to `120` is NOT complete (over-100 is invalid).
    A BOM summing to `99.9999` is NOT complete (off-by-tiny).
    Only `100.0000` is complete.

    Args:
        rows: An iterable of ratio `Decimal`s.

    Returns:
        `True` iff the sum is exactly `100.0000`.
    """
    return sum_ratios(rows) == TARGET_TOTAL


def missing_to_complete(rows: Iterable[Decimal]) -> Decimal:
    """Pure: how much is needed to reach 100.0000%?

    Clamped at zero (over-100 still reports `0` so the UX toast says
    "비중 합 100% 필요 (현재 X%)" instead of "비중 합 100% 필요 (-20% 부족)").
    Used by the matrix UI to render "{missing}% 부족" inline.

    Args:
        rows: An iterable of ratio `Decimal`s.

    Returns:
        `Decimal` quantized to 4 decimal places in `[0, 100.0000]`.
    """
    total = sum_ratios(rows)
    delta = TARGET_TOTAL - total
    if delta <= Decimal("0"):
        return Decimal("0.0000")
    return delta.quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def quantize_ratio(value: Decimal) -> Decimal:
    """Pure: round a single ratio to 4-decimal NUMERIC(7,4) precision.

    `ROUND_HALF_EVEN` per AD-8 / Story 0.4 chunk-B Decimal.set parity.

    Args:
        value: A `Decimal` ratio.

    Returns:
        `Decimal` quantized to 4 decimal places.

    Raises:
        InvalidRatioTypeError: Non-Decimal / non-numeric input.
    """
    if not isinstance(value, Decimal | int):
        raise InvalidRatioTypeError(value)
    return Decimal(value).quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


# Re-exports — keep the public API flat.
__all__ = [
    "BOMValidationError",
    "InvalidRatioTypeError",
    "TARGET_TOTAL",
    "sum_ratios",
    "is_complete_bom",
    "missing_to_complete",
    "quantize_ratio",
]
