"""V8 byte-identical determinism tests for Story 9.2 CCR + Allocation.

V8 1원 단위 회귀 가능 — 동일 inputs → byte-identical hashes (100회 반복).
8-3 + 9-1 + 9-2 surface 모두 동일한 hashlib.sha256 패턴 + AD-8 parity.

CR 11-3 + CR 12-5: 6 cases, A19 cohesion pattern 7번째 surface 분리 검증.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    CCR_HASH_PREFIX,
    ActivityMapping,
    CostObjectRow,
    compute_allocation,
    compute_allocation_hash,
    compute_ccr,
    compute_ccr_hash,
)


@pytest.mark.engine
def test_v8_ccr_hash_100_repeats() -> None:
    """V8 determinism — compute_ccr 100회 반복 → 동일 hash."""
    first_hash: str | None = None
    for _ in range(100):
        result = compute_ccr(
            department_id="dept-v8-ccr",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        if first_hash is None:
            first_hash = result.hash
        assert result.hash == first_hash


@pytest.mark.engine
def test_v8_ccr_hash_detached_function() -> None:
    """compute_ccr_hash standalone → 동일 CCRResult → 동일 hash (100회)."""
    result = compute_ccr(
        department_id="dept-v8-detach",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    first_hash = compute_ccr_hash(ccr_result=result)
    for _ in range(100):
        assert compute_ccr_hash(ccr_result=result) == first_hash


@pytest.mark.engine
def test_v8_allocation_hash_100_repeats() -> None:
    """V8 determinism — compute_allocation 100회 반복 → 동일 hash."""
    ccr = compute_ccr(
        department_id="dept-v8-alloc",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    activity_mappings = [
        ActivityMapping(
            activity_id="act-001",
            hours=Decimal("400"),
            ccr_amount_krw=Decimal("13200000"),
        ),
    ]
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("13200000"),
        ),
    ]
    first_hash: str | None = None
    for _ in range(100):
        result = compute_allocation(
            ccr=ccr,
            activity_mappings=list(activity_mappings),
            cost_object_breakdown=list(cost_object_breakdown),
            used_hours=Decimal("400"),
        )
        h = compute_allocation_hash(allocation=result)
        if first_hash is None:
            first_hash = h
        assert h == first_hash


@pytest.mark.engine
def test_v8_ccr_hash_format_byte_identical() -> None:
    """V8 hash format invariant — sha256: + 64-char hexdigest."""
    result = compute_ccr(
        department_id="dept-format-v8",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    h = compute_ccr_hash(ccr_result=result)
    assert h.startswith(CCR_HASH_PREFIX)
    assert len(h) == len(CCR_HASH_PREFIX) + 64
    hex_part = h[len(CCR_HASH_PREFIX):]
    assert all(c in "0123456789abcdef" for c in hex_part)


@pytest.mark.engine
def test_v8_determinism_different_inputs_different_hashes() -> None:
    """V8 invariant — 다른 inputs → 다른 hashes (구별성)."""
    h_a = compute_ccr(
        department_id="dept-A",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    ).hash
    h_b = compute_ccr(
        department_id="dept-B",
        department_cost=Decimal("13200001"),
        practical_capacity_hours=Decimal("400"),
    ).hash
    assert h_a != h_b


@pytest.mark.engine
def test_v8_decimal_precision_stability() -> None:
    """V8 + AD-8 — Decimal quantum 0 vs 1 vs 4 decimal places 모두 안정."""
    for cost, hours in [
        (Decimal("100"), Decimal("1")),
        (Decimal("1.0000"), Decimal("1")),
        (Decimal("999999999"), Decimal("7")),
    ]:
        first = compute_ccr(
            department_id="dept-stable",
            department_cost=cost,
            practical_capacity_hours=hours,
        )
        for _ in range(50):
            again = compute_ccr(
                department_id="dept-stable",
                department_cost=cost,
                practical_capacity_hours=hours,
            )
            assert compute_ccr_hash(ccr_result=again) == compute_ccr_hash(ccr_result=first)
