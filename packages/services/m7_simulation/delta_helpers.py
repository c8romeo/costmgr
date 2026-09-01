"""packages.services.m7_simulation.delta_helpers — Story 7.1 delta helpers.

Pure helpers for CVP delta validation:
- `clamp_delta(delta)` — clamp each delta percentage to its slider bounds
  (Story 7.1 spec: 단가 ±50%, 단위변동비 ±50%, 고정비 ±30%, 조업도 50%~150%).
- `validate_delta_bounds(delta)` — raise `CVPInvalidDeltaError` if delta
  outside allowed bounds (defense-in-depth before engine call).

No I/O — pure functions. CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep.
"""

from __future__ import annotations

from decimal import Decimal

from packages.cost_engine.cvp import (
    FIXED_COST_DELTA_PCT_BOUNDS,
    OPERATING_RATE_DELTA_PCT_BOUNDS,
    PRICE_DELTA_PCT_BOUNDS,
    CVPDelta,
    CVPInvalidInputError,
)


def clamp_delta(delta: CVPDelta) -> CVPDelta:
    """Clamp each delta percentage to its respective slider bounds.

    Returns a NEW CVPDelta instance (frozen=True immutability).
    """
    return CVPDelta(
        unit_price_delta_pct=_clamp(delta.unit_price_delta_pct, PRICE_DELTA_PCT_BOUNDS),
        unit_variable_cost_delta_pct=_clamp(
            delta.unit_variable_cost_delta_pct, PRICE_DELTA_PCT_BOUNDS
        ),
        fixed_cost_delta_pct=_clamp(delta.fixed_cost_delta_pct, FIXED_COST_DELTA_PCT_BOUNDS),
        operating_rate_delta_pct=_clamp(
            delta.operating_rate_delta_pct, OPERATING_RATE_DELTA_PCT_BOUNDS
        ),
    )


def _clamp(value: Decimal, bounds: tuple[Decimal, Decimal]) -> Decimal:
    """Clamp value to [bounds[0], bounds[1]]."""
    lo, hi = bounds
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def validate_delta_bounds(delta: CVPDelta) -> None:
    """Validate delta is within allowed bounds.

    Raises:
        CVPInvalidDeltaError: if any field is out of bounds. Wraps
            `CVPInvalidInputError` with a typed `code` attribute.
    """
    if not (PRICE_DELTA_PCT_BOUNDS[0] <= delta.unit_price_delta_pct <= PRICE_DELTA_PCT_BOUNDS[1]):
        raise CVPInvalidDeltaError(
            field="unit_price_delta_pct",
            value=delta.unit_price_delta_pct,
            bounds=PRICE_DELTA_PCT_BOUNDS,
        )
    if not (
        PRICE_DELTA_PCT_BOUNDS[0] <= delta.unit_variable_cost_delta_pct <= PRICE_DELTA_PCT_BOUNDS[1]
    ):
        raise CVPInvalidDeltaError(
            field="unit_variable_cost_delta_pct",
            value=delta.unit_variable_cost_delta_pct,
            bounds=PRICE_DELTA_PCT_BOUNDS,
        )
    if not (
        FIXED_COST_DELTA_PCT_BOUNDS[0]
        <= delta.fixed_cost_delta_pct
        <= FIXED_COST_DELTA_PCT_BOUNDS[1]
    ):
        raise CVPInvalidDeltaError(
            field="fixed_cost_delta_pct",
            value=delta.fixed_cost_delta_pct,
            bounds=FIXED_COST_DELTA_PCT_BOUNDS,
        )
    if not (
        OPERATING_RATE_DELTA_PCT_BOUNDS[0]
        <= delta.operating_rate_delta_pct
        <= OPERATING_RATE_DELTA_PCT_BOUNDS[1]
    ):
        raise CVPInvalidDeltaError(
            field="operating_rate_delta_pct",
            value=delta.operating_rate_delta_pct,
            bounds=OPERATING_RATE_DELTA_PCT_BOUNDS,
        )


class CVPInvalidDeltaError(CVPInvalidInputError):
    """422 CVP_INVALID_DELTA — delta가 허용 범위 밖 (Story 7.1).

    Typed exception delimiter from `CVPInvalidInputError` (kernel-level
    input validation) for service-layer HTTP envelope (CR 12-5 D-14).
    """

    def __init__(
        self,
        *,
        field: str,
        value: Decimal,
        bounds: tuple[Decimal, Decimal],
    ) -> None:
        self.field = field
        self.value = value
        self.bounds = bounds
        super().__init__(
            message=(
                f"CVP delta field {field!r}={value} outside bounds " f"[{bounds[0]}, {bounds[1]}]"
            ),
            code="CVP_INVALID_DELTA",
            field=field,
        )


__all__ = [
    "clamp_delta",
    "validate_delta_bounds",
    "CVPInvalidDeltaError",
]
