"""V8 byte-identical determinism tests for Story 9.1 abc_engine.py.

PRD §F9.1 + NFR16 + V8 determinism invariant: same input → byte-identical
hash across 100+ iterations.

Coverage:
  - `compute_validation_hash` 100회 반복 hash 동일성 (6 cases)
  - Decimal precision stability (TS decimal.js parity)
  - Repr 결정론 (frozen=True, slots=True)
  - hash format = "sha256:" + 64 hex chars
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    VALIDATION_HASH_PREFIX,
    ActivityValidation,
    CostPoolValidation,
    DriverValidation,
    compute_validation_hash,
    validate_activity,
    validate_cost_pool,
    validate_driver,
)


@pytest.mark.engine
def test_validate_cost_pool_100x_byte_identical_hash() -> None:
    """PRD §F9.1 100% 가드 100회 반복 → 동일 hash (V8 determinism)."""
    pcts = [Decimal("25"), Decimal("25"), Decimal("25"), Decimal("25")]
    expected_hash = validate_cost_pool(
        department_id="dept-001",
        allocation_pcts=pcts,
    ).hash

    for _ in range(100):
        result = validate_cost_pool(
            department_id="dept-001",
            allocation_pcts=pcts,
        )
        assert result.hash == expected_hash


@pytest.mark.engine
def test_validate_activity_100x_byte_identical_hash() -> None:
    """활동 100회 반복 → 동일 hash."""
    pcts = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    expected_hash = validate_activity(
        cost_pool_id="pool-001",
        activity_pcts=pcts,
    ).hash

    for _ in range(100):
        result = validate_activity(
            cost_pool_id="pool-001",
            activity_pcts=pcts,
        )
        assert result.hash == expected_hash


@pytest.mark.engine
def test_validate_driver_100x_byte_identical_hash() -> None:
    """동인 100회 반복 → 동일 hash."""
    pcts = [Decimal("60"), Decimal("40")]
    expected_hash = validate_driver(
        activity_id="act-001",
        driver_pcts=pcts,
    ).hash

    for _ in range(100):
        result = validate_driver(
            activity_id="act-001",
            driver_pcts=pcts,
        )
        assert result.hash == expected_hash


@pytest.mark.engine
def test_compute_validation_hash_format_invariant() -> None:
    """Hash format = `sha256:` + 64 hex chars (V8 invariant)."""
    state = CostPoolValidation(
        department_id="dept-001",
        sum_pct=Decimal("100"),
        department_count=4,
        is_valid=True,
        hash="",
    )
    digest = compute_validation_hash(validation_state=state)
    # Total length: 7 (sha256:) + 64 (hex) = 71.
    assert len(digest) == 7 + 64
    # hex-only after prefix.
    hex_part = digest.split(":", 1)[1]
    assert all(c in "0123456789abcdef" for c in hex_part), (
        f"hash contains non-hex chars: {hex_part!r}"
    )
    # Prefix exact.
    assert digest.startswith(VALIDATION_HASH_PREFIX)


@pytest.mark.engine
def test_compute_validation_hash_repr_determinism() -> None:
    """Repr 결정론 — 동일 dataclass 내용 → 동일 repr → 동일 hash."""
    state_a = ActivityValidation(
        cost_pool_id="pool-001",
        sum_pct=Decimal("100.00"),
        activity_count=3,
        is_valid=True,
        hash="",  # placeholder 동일
    )
    state_b = ActivityValidation(
        cost_pool_id="pool-001",
        sum_pct=Decimal("100.00"),
        activity_count=3,
        is_valid=True,
        hash="",  # placeholder 동일
    )
    h_a = compute_validation_hash(validation_state=state_a)
    h_b = compute_validation_hash(validation_state=state_b)
    assert h_a == h_b
    assert repr(state_a) == repr(state_b)


@pytest.mark.engine
def test_compute_validation_hash_3_types_same_prefix() -> None:
    """3 dataclass type 모두 동일 prefix (`sha256:`) 사용."""
    cp = CostPoolValidation(
        department_id="d1",
        sum_pct=Decimal("100"),
        department_count=2,
        is_valid=True,
        hash="",
    )
    av = ActivityValidation(
        cost_pool_id="p1",
        sum_pct=Decimal("100"),
        activity_count=2,
        is_valid=True,
        hash="",
    )
    dv = DriverValidation(
        activity_id="a1",
        sum_pct=Decimal("100"),
        driver_count=2,
        is_valid=True,
        hash="",
    )
    h_cp = compute_validation_hash(validation_state=cp)
    h_av = compute_validation_hash(validation_state=av)
    h_dv = compute_validation_hash(validation_state=dv)
    assert h_cp.startswith(VALIDATION_HASH_PREFIX)
    assert h_av.startswith(VALIDATION_HASH_PREFIX)
    assert h_dv.startswith(VALIDATION_HASH_PREFIX)
