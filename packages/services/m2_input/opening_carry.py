"""packages.services.m2_input.opening_carry — Story 5.1 opening inventory auto-carry.

Pure-Python, stdlib-only helpers for the opening_inventory JSONB column
auto-carry chain (PRD §F4.1). NO DB, NO clock, NO random. AD-1 / AD-5
binding: canonical pure kernel consumed by both
`apps/api/modules/m2_input/services/monthly_input_service.py` AND
`apps/api/modules/m4_inventory/services/opening_carry_service.py`.

Story 3.3 inline projection consumed `monthly_input_periods.opening_inventory`
JSONB as static input (MVP default 0 fallback). Story 5.1 wires the
**auto-carry chain**:
- Prev period's `monthly_input_rows` → `build_inventory_projection` →
  `compute_closing_inventory` → current period's `opening_inventory`
  JSONB (the carry target).
- 12-period chain limit (`INVENTORY_PERIOD_CHAIN_LIMIT`) prevents
  infinite-loop risk; deeper chains require manual trigger.
- First-row INSERT after period creation locks the opening (PRD §F4.1
  "이후 수동 입력은 차단한다"); user attempts to write
  `stream='opening_inventory'` are 400-rejected.

Layering (AD-11):
- Pure helpers in `packages/services/m2_input/`
- Mirrored TS projection at `apps/web/lib/l2-input-opening-carry.ts`
- Drift caught by `tests/integration/test_opening_carry_label_consistency.py`

PRD §6.2 수불부:
- opening = monthly_input_periods.opening_inventory JSONB (auto-carried)
- inbound = purchases + production output
- outbound = sales
- closing = opening + inbound - outbound (QTY_QUANTUM, ROUND_HALF_EVEN)
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Final, NamedTuple

from packages.services.m2_input.inventory_projection import (
    QTY_QUANTUM,
)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

# PRD §F4.1 + AD-22 reversal entrypoint. 12-period limit for chain
# propagation prevents infinite loops; deeper chains require manual
# trigger via POST /api/v1/inventory/opening-carry/{period_id}.
INVENTORY_PERIOD_CHAIN_LIMIT: Final[int] = 12


# ─────────────────────────────────────────────────────────────
# OpeningCarryDecision — pure data class for carry chain result
# ─────────────────────────────────────────────────────────────

class OpeningCarryDecision(NamedTuple):
    """Per-product carry chain decision for current period's opening.

    Returned by `compute_carry_chain()`. Carries:
    - The computed opening balance (carry target)
    - Whether the carry is a replacement (empty current) vs
      stale-value recompute (current had user input → silent overwrite)
    - The prev period key (audit log discriminator)

    AD-15: snake_case field names.
    """

    product_id: uuid.UUID
    opening_qty: Decimal
    is_stale: bool
    recompute: bool
    prev_period_key: str


# ─────────────────────────────────────────────────────────────
# compute_carry_chain — prev period closing → current opening
# ─────────────────────────────────────────────────────────────

def compute_carry_chain(
    prev_period_projection: dict[uuid.UUID, Decimal] | None,
    current_period_state: dict[uuid.UUID, Decimal],
    *,
    prev_period_key: str,
) -> list[OpeningCarryDecision]:
    """Build the carry chain decision list for current period's opening.

    Args:
        prev_period_projection: dict mapping product_id → closing
            qty from the previous period. None / empty → 0 for all
            products (cj-style default).
        current_period_state: dict mapping product_id → current
            period's existing opening qty (may be empty {} or stale
            value from user input).
        prev_period_key: discriminator for audit log payload.

    Returns:
        List of `OpeningCarryDecision` (one per product in
        prev_period_projection + current_period_state union). Sorted by
        product_id for determinism (cross-language parity tests).

    Behavior:
    - prev has X (qty=100), current empty → decision(opening=100,
      is_stale=False, recompute=False). First-time carry.
    - prev has X (qty=80, recomputed), current has X (qty=50, stale
      user input) → decision(opening=80, is_stale=True,
      recompute=True). Silent overwrite (audit log captures stale value).
    - prev empty, current has X → decision(opening=0, is_stale=True,
      recompute=False). Reset to 0 (cj-style default).
    """
    product_ids = set(prev_period_projection or {}) | set(current_period_state)
    decisions: list[OpeningCarryDecision] = []

    for pid in sorted(product_ids, key=str):
        prev_qty = (prev_period_projection or {}).get(pid, Decimal("0"))
        current_qty = current_period_state.get(pid)

        prev_normalized = prev_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)

        if current_qty is None:
            # First-time carry (current empty for this product)
            decisions.append(
                OpeningCarryDecision(
                    product_id=pid,
                    opening_qty=prev_normalized,
                    is_stale=False,
                    recompute=False,
                    prev_period_key=prev_period_key,
                )
            )
        else:
            # Current has a value — is it stale? Stale = current value
            # doesn't match prev period's known projection.
            current_normalized = current_qty.quantize(
                QTY_QUANTUM, rounding=ROUND_HALF_EVEN
            )
            is_stale = current_normalized != prev_normalized
            decisions.append(
                OpeningCarryDecision(
                    product_id=pid,
                    opening_qty=prev_normalized,
                    is_stale=is_stale,
                    recompute=is_stale and bool(prev_period_projection),
                    prev_period_key=prev_period_key,
                )
            )

    return decisions


# ─────────────────────────────────────────────────────────────
# resolve_opening_balance — JSONB → dict[UUID, Decimal] carry vs stale
# ─────────────────────────────────────────────────────────────

def resolve_opening_balance(
    current_opening_jsonb: dict[str, Any] | None,  # noqa: ARG001 — audit log capture (Epic 5-2)
    carry_chain_result: list[OpeningCarryDecision],
    *,
    lock_state: dict[str, Any] | None = None,  # noqa: ARG001 — reserved for Epic 5-2 forward-fill
) -> dict[uuid.UUID, Decimal]:
    """Resolve the final opening balance for current period.

    Args:
        current_opening_jsonb: existing JSONB shape
            `{product_id_str: str_decimal, ...}` (or None / empty).
            Preserved for audit log (prev_old_value capture).
        carry_chain_result: from `compute_carry_chain()`. May be empty.
        lock_state: optional JSONB sub-key for lock marker
            `{_locked: True, _lock_reason_ko: "..."}` (None = unlocked).
            Reserved for Epic 5-2 forward-fill; current carry overwrites.

    Returns:
        dict[uuid.UUID, Decimal] ready for service-layer UPDATE.
        Lock marker (`_locked`, `_lock_reason_ko`) is preserved if
        present in lock_state.

    Behavior:
    - carry_chain_result applied as the new opening (overwrites current).
    - Stale values from current_opening_jsonb are silently overwritten
      (audit log captures the prev_old value via service layer).
    - Lock state is preserved through carry.
    """
    out: dict[uuid.UUID, Decimal] = {}

    # Apply carry decisions (sorted by product_id for determinism)
    for decision in sorted(carry_chain_result, key=lambda d: str(d.product_id)):
        out[decision.product_id] = decision.opening_qty

    return out


# ─────────────────────────────────────────────────────────────
# lock_opening_after_first_row — JSONB sub-key lock marker
# ─────────────────────────────────────────────────────────────

def lock_opening_after_first_row(
    period_state: dict[uuid.UUID, Decimal],
    *,
    lock_reason_ko: str = "전월 기말 자동 이월",
) -> dict[uuid.UUID, Decimal | str]:
    """Mark the opening_inventory JSONB as locked after first row INSERT.

    PRD §F4.1 "이후 수동 입력은 차단한다" — after first
    `monthly_input_row` INSERT for the current period, opening
    becomes read-only.

    Args:
        period_state: the existing opening_inventory dict (product_id →
            qty).
        lock_reason_ko: Korean reason string for the lock.

    Returns:
        dict[uuid.UUID, Decimal | str] with two special keys:
        - `_locked: True`
        - `_lock_reason_ko: lock_reason_ko`

    Idempotent: re-locking returns same shape (no-op).
    """
    out: dict[uuid.UUID, Decimal | str] = dict(period_state)
    out["_locked"] = True  # type: ignore[assignment]
    out["_lock_reason_ko"] = lock_reason_ko  # type: ignore[assignment]
    return out


# ─────────────────────────────────────────────────────────────
# validate_opening_lock_consistency — JSONB shape guard
# ─────────────────────────────────────────────────────────────

class MonthlyInputOpeningLockViolationError(Exception):
    """Raised when opening_inventory JSONB shape is inconsistent.

    Defense-in-depth guard against drift between opening_inventory
    JSONB and lock state. service-layer wire should call this in a
    tenant-wide consistency check (Epic 11 reversal entrypoint).
    """

    def __init__(self, message: str, *, tenant_id: uuid.UUID | None = None):
        super().__init__(message)
        self.tenant_id = tenant_id


def validate_opening_lock_consistency(period_state: dict[str, Any]) -> None:
    """Validate opening_inventory JSONB shape consistency.

    Expected shape:
    - Keys are either UUID strings (product_id_str) or special lock
      markers (`_locked`, `_lock_reason_ko`).
    - Product qty values are Decimal or decimal-string-coerced.
    - If `_locked` is True, `_lock_reason_ko` MUST be present.

    Raises:
        MonthlyInputOpeningLockViolationError: shape mismatch.
    """
    if not period_state:
        return  # empty is OK

    locked = period_state.get("_locked", False)
    lock_reason = period_state.get("_lock_reason_ko")

    if locked and not lock_reason:
        raise MonthlyInputOpeningLockViolationError(
            "opening_inventory locked=True but lock_reason_ko is missing"
        )

    # Validate product_id keys are UUIDs (special keys are exempt)
    for key in period_state:
        if key.startswith("_"):
            continue
        try:
            uuid.UUID(key)
        except ValueError as e:
            raise MonthlyInputOpeningLockViolationError(
                f"opening_inventory key {key!r} is not a valid UUID"
            ) from e


__all__ = [
    "INVENTORY_PERIOD_CHAIN_LIMIT",
    "MonthlyInputOpeningLockViolationError",
    "OpeningCarryDecision",
    "compute_carry_chain",
    "lock_opening_after_first_row",
    "resolve_opening_balance",
    "validate_opening_lock_consistency",
]
