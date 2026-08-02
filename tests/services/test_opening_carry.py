"""Story 5.1 — pure helpers test suite (T1).

Drives the red-green-refactor cycle for `packages.services.m2_input.opening_carry`.
Per CR 4-3 F-1 — async tests avoided in pure helper layer; sync test
functions only. Determinism + banker's rounding parity enforced.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m2_input.opening_carry import (
    INVENTORY_PERIOD_CHAIN_LIMIT,
    MonthlyInputOpeningLockViolationError,
    OpeningCarryDecision,
    compute_carry_chain,
    lock_opening_after_first_row,
    resolve_opening_balance,
    validate_opening_lock_consistency,
)

# ─────────────────────────────────────────────────────────────
# Test data
# ─────────────────────────────────────────────────────────────

PROD_X = uuid.UUID("11111111-1111-1111-1111-111111111111")
PROD_Y = uuid.UUID("22222222-2222-2222-2222-222222222222")
PROD_Z = uuid.UUID("33333333-3333-3333-3333-333333333333")


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

def test_inventory_period_chain_limit_constant() -> None:
    """Story 5.1 AC #1 + OQ4 cj-style default: 12-period chain limit."""
    assert INVENTORY_PERIOD_CHAIN_LIMIT == 12


# ─────────────────────────────────────────────────────────────
# compute_carry_chain
# ─────────────────────────────────────────────────────────────

def test_compute_carry_chain_empty_prev_empty_current() -> None:
    """Both prev and current empty → no decisions (empty list)."""
    decisions = compute_carry_chain(
        prev_period_projection=None,
        current_period_state={},
        prev_period_key="2026-07",
    )
    assert decisions == []


def test_compute_carry_chain_first_time_carry() -> None:
    """Prev has X(100), current empty → first-time carry (not stale)."""
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("100")},
        current_period_state={},
        prev_period_key="2026-07",
    )
    assert len(decisions) == 1
    assert decisions[0] == OpeningCarryDecision(
        product_id=PROD_X,
        opening_qty=Decimal("100.0000"),
        is_stale=False,
        recompute=False,
        prev_period_key="2026-07",
    )


def test_compute_carry_chain_stale_value_recompute() -> None:
    """Prev has X(80), current has X(50 stale) → recompute=True."""
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("80")},
        current_period_state={PROD_X: Decimal("50")},
        prev_period_key="2026-07",
    )
    assert len(decisions) == 1
    assert decisions[0].opening_qty == Decimal("80.0000")
    assert decisions[0].is_stale is True
    assert decisions[0].recompute is True


def test_compute_carry_chain_matching_value_not_stale() -> None:
    """Prev has X(100), current has X(100) → no drift, is_stale=False."""
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("100")},
        current_period_state={PROD_X: Decimal("100")},
        prev_period_key="2026-07",
    )
    assert len(decisions) == 1
    assert decisions[0].is_stale is False
    assert decisions[0].recompute is False


def test_compute_carry_chain_multi_product_sorted() -> None:
    """Multi-product → sorted by product_id for determinism."""
    decisions = compute_carry_chain(
        prev_period_projection={
            PROD_Y: Decimal("50"),
            PROD_X: Decimal("100"),
            PROD_Z: Decimal("200"),
        },
        current_period_state={},
        prev_period_key="2026-07",
    )
    assert [d.product_id for d in decisions] == [PROD_X, PROD_Y, PROD_Z]


def test_compute_carry_chain_prev_empty_current_exists() -> None:
    """Prev empty + current has X → reset to 0, is_stale=True."""
    decisions = compute_carry_chain(
        prev_period_projection={},
        current_period_state={PROD_X: Decimal("50")},
        prev_period_key="2026-07",
    )
    assert len(decisions) == 1
    assert decisions[0].opening_qty == Decimal("0.0000")
    assert decisions[0].is_stale is True
    assert decisions[0].recompute is False  # prev empty → no recompute


def test_compute_carry_chain_idempotent_re_call() -> None:
    """Same input 100× → byte-identical output (AD-16 determinism)."""
    prev = {PROD_X: Decimal("100"), PROD_Y: Decimal("50")}
    current = {}
    first = compute_carry_chain(
        prev_period_projection=prev,
        current_period_state=current,
        prev_period_key="2026-07",
    )
    for _ in range(100):
        again = compute_carry_chain(
            prev_period_projection=prev,
            current_period_state=current,
            prev_period_key="2026-07",
        )
        assert again == first


def test_compute_carry_chain_bankers_rounding_parity() -> None:
    """Banker's rounding: 0.00005 → 0.0000 (5th=5, 4th=0 even → down).

    CR 0-4 lesson: TS/Python ROUND_HALF_EVEN parity pinning.
    QTY_QUANTUM = 0.0001 (4dp). Banker's rounding visible when
    rounding boundary is at 0.5 of next unit.
    """
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("0.00005")},
        current_period_state={},
        prev_period_key="2026-07",
    )
    # 0.00005 → 4th decimal is 0 (even) → round down → 0.0000
    assert decisions[0].opening_qty == Decimal("0.0000")


def test_compute_carry_chain_bankers_rounding_parity_odd() -> None:
    """Banker's rounding: 0.00015 → 0.0002 (5th=5, 4th=1 odd → up)."""
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("0.00015")},
        current_period_state={},
        prev_period_key="2026-07",
    )
    # 0.00015 → 4th decimal is 1 (odd) → round up → 0.0002
    assert decisions[0].opening_qty == Decimal("0.0002")


# ─────────────────────────────────────────────────────────────
# resolve_opening_balance
# ─────────────────────────────────────────────────────────────

def test_resolve_opening_balance_carry_replaces() -> None:
    """Carry result → final opening balance."""
    decisions = [
        OpeningCarryDecision(
            product_id=PROD_X,
            opening_qty=Decimal("100.0000"),
            is_stale=False,
            recompute=False,
            prev_period_key="2026-07",
        ),
    ]
    out = resolve_opening_balance(
        current_opening_jsonb={},
        carry_chain_result=decisions,
    )
    assert out == {PROD_X: Decimal("100.0000")}


def test_resolve_opening_balance_multi_product_sorted() -> None:
    """Multi-product carry → sorted dict output."""
    decisions = [
        OpeningCarryDecision(
            product_id=PROD_Y,
            opening_qty=Decimal("50.0000"),
            is_stale=False,
            recompute=False,
            prev_period_key="2026-07",
        ),
        OpeningCarryDecision(
            product_id=PROD_X,
            opening_qty=Decimal("100.0000"),
            is_stale=False,
            recompute=False,
            prev_period_key="2026-07",
        ),
    ]
    out = resolve_opening_balance(
        current_opening_jsonb={},
        carry_chain_result=decisions,
    )
    assert list(out.keys()) == [PROD_X, PROD_Y]


def test_resolve_opening_balance_empty_carry_empty() -> None:
    """Empty carry + empty current → empty dict."""
    out = resolve_opening_balance(
        current_opening_jsonb={},
        carry_chain_result=[],
    )
    assert out == {}


# ─────────────────────────────────────────────────────────────
# lock_opening_after_first_row
# ─────────────────────────────────────────────────────────────

def test_lock_opening_after_first_row_basic() -> None:
    """Lock marker added to opening dict."""
    state = {PROD_X: Decimal("100")}
    locked = lock_opening_after_first_row(state)
    assert locked["_locked"] is True
    assert locked["_lock_reason_ko"] == "전월 기말 자동 이월"
    assert locked[PROD_X] == Decimal("100")


def test_lock_opening_after_first_row_idempotent() -> None:
    """Re-lock → no-op (same shape)."""
    state = {PROD_X: Decimal("100")}
    first = lock_opening_after_first_row(state)
    second = lock_opening_after_first_row(first)
    assert second == first


def test_lock_opening_after_first_row_custom_reason() -> None:
    """Custom lock_reason_ko override."""
    state = {PROD_X: Decimal("100")}
    locked = lock_opening_after_first_row(
        state, lock_reason_ko="마감 후 잠금"
    )
    assert locked["_lock_reason_ko"] == "마감 후 잠금"


# ─────────────────────────────────────────────────────────────
# validate_opening_lock_consistency
# ─────────────────────────────────────────────────────────────

def test_validate_opening_lock_consistency_empty_ok() -> None:
    """Empty period_state → OK (no raise)."""
    validate_opening_lock_consistency({})


def test_validate_opening_lock_consistency_valid_shape() -> None:
    """Valid JSONB shape → no raise."""
    state = {
        str(PROD_X): Decimal("100"),
        str(PROD_Y): Decimal("50"),
        "_locked": True,
        "_lock_reason_ko": "전월 기말 자동 이월",
    }
    validate_opening_lock_consistency(state)  # no raise


def test_validate_opening_lock_consistency_locked_no_reason_raises() -> None:
    """locked=True without lock_reason_ko → raise."""
    state = {
        str(PROD_X): Decimal("100"),
        "_locked": True,
    }
    with pytest.raises(MonthlyInputOpeningLockViolationError):
        validate_opening_lock_consistency(state)


def test_validate_opening_lock_consistency_invalid_uuid_raises() -> None:
    """Non-UUID product key → raise."""
    state = {
        "not-a-uuid": Decimal("100"),
    }
    with pytest.raises(MonthlyInputOpeningLockViolationError):
        validate_opening_lock_consistency(state)


def test_validate_opening_lock_consistency_unlocked_ok() -> None:
    """_locked=False or absent → OK (no reason required)."""
    state = {str(PROD_X): Decimal("100")}
    validate_opening_lock_consistency(state)  # no raise


# ─────────────────────────────────────────────────────────────
# Integration: compute_carry_chain → resolve pipeline
# ─────────────────────────────────────────────────────────────

def test_carry_chain_to_resolve_pipeline_first_time() -> None:
    """End-to-end: carry chain → resolve produces final opening balance."""
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("100"), PROD_Y: Decimal("50")},
        current_period_state={},
        prev_period_key="2026-07",
    )
    final = resolve_opening_balance(
        current_opening_jsonb={},
        carry_chain_result=decisions,
    )
    assert final == {PROD_X: Decimal("100.0000"), PROD_Y: Decimal("50.0000")}


def test_carry_chain_to_resolve_pipeline_stale_overwrite() -> None:
    """End-to-end: stale value silently overwritten by carry."""
    decisions = compute_carry_chain(
        prev_period_projection={PROD_X: Decimal("80")},
        current_period_state={PROD_X: Decimal("50")},
        prev_period_key="2026-07",
    )
    assert decisions[0].is_stale is True
    final = resolve_opening_balance(
        current_opening_jsonb={str(PROD_X): "50"},
        carry_chain_result=decisions,
    )
    assert final == {PROD_X: Decimal("80.0000")}  # stale overwritten
