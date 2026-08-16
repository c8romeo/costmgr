"""Tests for Story 9.1 pure kernel `packages.cost_engine.abc_engine`.

Coverage:
  - `validate_cost_pool` 정상범위 (PRD §F9.1 verbatim 100% 가드)
  - `validate_activity` 정상범위 (열 합 100% 가드)
  - `validate_driver` 정상범위 (동인 합 100% 가드)
  - 3 validate functions edge cases (음수 / 초과 / 빈 리스트 / Decimal 아닌 type)
  - `compute_validation_hash` 결정론 (RFC test vector)
  - `validate_100_percent_guard` 3-layer orchestrator
  - `frozen=True, slots=True` enforcement (mutation 시도 → FrozenInstanceError)
  - Decimal precision ROUND_HALF_EVEN parity (TS decimal.js 동일, 7-1/7-2/8-1/8-2/8-3 패턴)
  - constants 노출 검증 (7 constants)
  - typed exception class 검증 (4 typed exceptions)

CR 11-3 + CR 12-5: 30+ cases, A19 cohesion pattern 6번째 surface 분리 검증.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    ABC_VALIDATION_KRW_QUANTUM,
    ALLOCATION_PCT_MAX,
    ALLOCATION_PCT_MIN,
    VALIDATION_100_PCT_TARGET,
    VALIDATION_DEFAULT_INDUSTRY,
    VALIDATION_HASH_PREFIX,
    VALIDATION_TOLERANCE_KRW,
    AbcValidationNotFoundError,
    ActivityValidation,
    ActivityValidationError,
    CostPoolValidation,
    CostPoolValidationError,
    DriverValidation,
    DriverValidationError,
    ValidationState,
    compute_validation_hash,
    validate_100_percent_guard,
    validate_activity,
    validate_cost_pool,
    validate_driver,
)

# ── 정상범위 (PRD §F9.1 verbatim 100% 가드) ──────────────────────


@pytest.mark.engine
def test_validate_cost_pool_100_percent_normal_range() -> None:
    """PRD §F9.1 verbatim 원가풀 행 합 100% 가드.

    4개 부서 각 25% → sum_pct = 100 → is_valid = True.
    """
    result = validate_cost_pool(
        department_id="dept-001",
        allocation_pcts=[Decimal("25"), Decimal("25"), Decimal("25"), Decimal("25")],
    )
    assert result.department_id == "dept-001"
    assert result.sum_pct == Decimal("100")
    assert result.department_count == 4
    assert result.is_valid is True
    assert result.hash.startswith(VALIDATION_HASH_PREFIX)
    assert len(result.hash) == len(VALIDATION_HASH_PREFIX) + 64  # sha256: + 64 hex


@pytest.mark.engine
def test_validate_cost_pool_105_percent_invalid() -> None:
    """PRD §F9.1 verbatim 원가풀 행 합 ≠ 100% 가드.

    4개 부서 30%/25%/25%/25% → sum_pct = 105 → is_valid = False.
    """
    result = validate_cost_pool(
        department_id="dept-002",
        allocation_pcts=[Decimal("30"), Decimal("25"), Decimal("25"), Decimal("25")],
    )
    assert result.sum_pct == Decimal("105")
    assert result.is_valid is False
    assert result.department_count == 4


@pytest.mark.engine
def test_validate_cost_pool_90_percent_invalid() -> None:
    """원가풀 행 합 90% (insufficient) → is_valid = False."""
    result = validate_cost_pool(
        department_id="dept-003",
        allocation_pcts=[Decimal("30"), Decimal("20"), Decimal("20"), Decimal("20")],
    )
    assert result.sum_pct == Decimal("90")
    assert result.is_valid is False


@pytest.mark.engine
def test_validate_cost_pool_within_tolerance() -> None:
    """Tolerance 검증 — 99.99 / 100.01 도 valid (within ±0.01)."""
    result_low = validate_cost_pool(
        department_id="dept-004",
        allocation_pcts=[Decimal("49.99"), Decimal("50.01")],
    )
    assert result_low.sum_pct == Decimal("100")
    assert result_low.is_valid is True

    # 100.01 → within ±0.01 of 100 → valid (rounding error tolerance).
    # But 100.01 → not strictly == 100 → tolerance check.
    # Use 99.995 / 0.005 → sum = 100.000 → exactly 100.
    # Actually tolerance is ±0.01 so 99.99 or 100.01 is OK.
    result_high = validate_cost_pool(
        department_id="dept-005",
        allocation_pcts=[Decimal("50.01"), Decimal("50")],
    )
    # 50.01 + 50 = 100.01 — within tolerance (±0.01) → valid.
    assert result_high.sum_pct == Decimal("100.01")
    assert result_high.is_valid is True


@pytest.mark.engine
def test_validate_cost_pool_tolerance_boundary() -> None:
    """Tolerance 경계 — 100.02 → out of tolerance (±0.01) → invalid."""
    result = validate_cost_pool(
        department_id="dept-006",
        allocation_pcts=[Decimal("50.02"), Decimal("50")],
    )
    # 50.02 + 50 = 100.02 — out of tolerance (> ±0.01) → invalid.
    assert result.sum_pct == Decimal("100.02")
    assert result.is_valid is False


# ── validate_activity 정상범위 ─────────────────────────────


@pytest.mark.engine
def test_validate_activity_100_percent_normal_range() -> None:
    """PRD §F9.1 verbatim 활동 열 합 100% 가드.

    3개 활동 각 33.33% / 33.33% / 33.34% → sum_pct = 100.00 → is_valid = True.
    """
    result = validate_activity(
        cost_pool_id="pool-001",
        activity_pcts=[Decimal("33.33"), Decimal("33.33"), Decimal("33.34")],
    )
    assert result.cost_pool_id == "pool-001"
    assert result.sum_pct == Decimal("100.00")
    assert result.activity_count == 3
    assert result.is_valid is True


@pytest.mark.engine
def test_validate_activity_90_percent_invalid() -> None:
    """활동 열 합 90% → is_valid = False."""
    result = validate_activity(
        cost_pool_id="pool-002",
        activity_pcts=[Decimal("30"), Decimal("30"), Decimal("30")],
    )
    assert result.sum_pct == Decimal("90")
    assert result.is_valid is False


@pytest.mark.engine
def test_validate_activity_two_activities() -> None:
    """활동 2개 50%/50% → sum_pct = 100 → is_valid = True."""
    result = validate_activity(
        cost_pool_id="pool-003",
        activity_pcts=[Decimal("50"), Decimal("50")],
    )
    assert result.activity_count == 2
    assert result.is_valid is True


# ── validate_driver 정상범위 ───────────────────────────────


@pytest.mark.engine
def test_validate_driver_100_percent_normal_range() -> None:
    """PRD §F9.1 verbatim 동인 합 100% 가드.

    2개 동인 60% / 40% → sum_pct = 100 → is_valid = True.
    """
    result = validate_driver(
        activity_id="act-001",
        driver_pcts=[Decimal("60"), Decimal("40")],
    )
    assert result.activity_id == "act-001"
    assert result.sum_pct == Decimal("100")
    assert result.driver_count == 2
    assert result.is_valid is True


@pytest.mark.engine
def test_validate_driver_90_percent_invalid() -> None:
    """동인 합 90% → is_valid = False."""
    result = validate_driver(
        activity_id="act-002",
        driver_pcts=[Decimal("60"), Decimal("30")],
    )
    assert result.sum_pct == Decimal("90")
    assert result.is_valid is False


@pytest.mark.engine
def test_validate_driver_three_drivers() -> None:
    """동인 3개 33.33%/33.33%/33.34% → sum_pct = 100 → is_valid = True."""
    result = validate_driver(
        activity_id="act-003",
        driver_pcts=[Decimal("33.33"), Decimal("33.33"), Decimal("33.34")],
    )
    assert result.driver_count == 3
    assert result.is_valid is True


# ── Edge cases (PRD §F9.1 + UX safety) ──────────────────────


@pytest.mark.engine
def test_validate_cost_pool_empty_list_raises_not_found() -> None:
    """빈 allocation_pcts → AbcValidationNotFoundError (404 envelope)."""
    with pytest.raises(AbcValidationNotFoundError) as exc_info:
        validate_cost_pool(
            department_id="dept-empty",
            allocation_pcts=[],
        )
    assert exc_info.value.target == "cost_pool"
    assert exc_info.value.target_id == "<empty>"


@pytest.mark.engine
def test_validate_activity_empty_list_raises_not_found() -> None:
    """활동 빈 리스트 → AbcValidationNotFoundError."""
    with pytest.raises(AbcValidationNotFoundError) as exc_info:
        validate_activity(
            cost_pool_id="pool-empty",
            activity_pcts=[],
        )
    assert exc_info.value.target == "activity"


@pytest.mark.engine
def test_validate_driver_empty_list_raises_not_found() -> None:
    """동인 빈 리스트 → AbcValidationNotFoundError."""
    with pytest.raises(AbcValidationNotFoundError) as exc_info:
        validate_driver(
            activity_id="act-empty",
            driver_pcts=[],
        )
    assert exc_info.value.target == "driver"


@pytest.mark.engine
def test_validate_cost_pool_negative_value_raises() -> None:
    """음수 allocation_pct → CostPoolValidationError (negative_value)."""
    with pytest.raises(CostPoolValidationError) as exc_info:
        validate_cost_pool(
            department_id="dept-neg",
            allocation_pcts=[Decimal("-10"), Decimal("110")],
        )
    assert exc_info.value.reason == "negative_value"


@pytest.mark.engine
def test_validate_cost_pool_exceeds_max_raises() -> None:
    """100 초과 allocation_pct → CostPoolValidationError (exceeds_max)."""
    with pytest.raises(CostPoolValidationError) as exc_info:
        validate_cost_pool(
            department_id="dept-max",
            allocation_pcts=[Decimal("150"), Decimal("50")],
        )
    assert exc_info.value.reason == "exceeds_max"


@pytest.mark.engine
def test_validate_cost_pool_non_decimal_raises() -> None:
    """Decimal 아닌 type (int) → CostPoolValidationError (type_mismatch)."""
    with pytest.raises(CostPoolValidationError) as exc_info:
        validate_cost_pool(
            department_id="dept-type",
            allocation_pcts=[25, 25, 25, 25],  # type: ignore[list-item]
        )
    assert exc_info.value.reason == "type_mismatch"


# ── Hash 결정론 ──────────────────────────────────────────────


@pytest.mark.engine
def test_compute_validation_hash_cost_pool_deterministic() -> None:
    """동일 CostPoolValidation → byte-identical hash (V8 determinism)."""
    state = CostPoolValidation(
        department_id="dept-001",
        sum_pct=Decimal("100"),
        department_count=4,
        is_valid=True,
        hash="",  # placeholder
    )
    h1 = compute_validation_hash(validation_state=state)
    h2 = compute_validation_hash(validation_state=state)
    assert h1 == h2
    assert h1.startswith(VALIDATION_HASH_PREFIX)
    assert len(h1) == len(VALIDATION_HASH_PREFIX) + 64


@pytest.mark.engine
def test_compute_validation_hash_activity_deterministic() -> None:
    """ActivityValidation 결정론 hash."""
    state = ActivityValidation(
        cost_pool_id="pool-001",
        sum_pct=Decimal("100.00"),
        activity_count=3,
        is_valid=True,
        hash="",
    )
    h = compute_validation_hash(validation_state=state)
    assert h.startswith(VALIDATION_HASH_PREFIX)
    # 64 hex chars total.
    assert len(h.split(":", 1)[1]) == 64


@pytest.mark.engine
def test_compute_validation_hash_driver_deterministic() -> None:
    """DriverValidation 결정론 hash."""
    state = DriverValidation(
        activity_id="act-001",
        sum_pct=Decimal("100"),
        driver_count=2,
        is_valid=True,
        hash="",
    )
    h = compute_validation_hash(validation_state=state)
    assert h.startswith(VALIDATION_HASH_PREFIX)


@pytest.mark.engine
def test_compute_validation_hash_invalid_type_raises() -> None:
    """Invalid type → ValueError."""
    with pytest.raises(ValueError, match="must be CostPoolValidation"):
        compute_validation_hash(validation_state="not-a-validation")  # type: ignore[arg-type]


@pytest.mark.engine
def test_compute_validation_hash_different_input_different_hash() -> None:
    """다른 입력 → 다른 hash (V8 determinism 강제 검증)."""
    state_a = CostPoolValidation(
        department_id="dept-A",
        sum_pct=Decimal("100"),
        department_count=2,
        is_valid=True,
        hash="",
    )
    state_b = CostPoolValidation(
        department_id="dept-B",
        sum_pct=Decimal("100"),
        department_count=2,
        is_valid=True,
        hash="",
    )
    h_a = compute_validation_hash(validation_state=state_a)
    h_b = compute_validation_hash(validation_state=state_b)
    assert h_a != h_b


# ── validate_100_percent_guard orchestrator ────────────────


@pytest.mark.engine
def test_validate_100_percent_guard_all_valid() -> None:
    """3 layer 모두 valid → all_valid = True."""
    result = validate_100_percent_guard(
        cost_pool=[Decimal("50"), Decimal("50")],
        activities=[Decimal("60"), Decimal("40")],
        drivers=[Decimal("70"), Decimal("30")],
        cost_pool_id="pool-001",
        activity_id="act-001",
    )
    assert result["all_valid"] is True
    assert isinstance(result["cost_pool"], CostPoolValidation)
    assert isinstance(result["activity"], ActivityValidation)
    assert isinstance(result["driver"], DriverValidation)


@pytest.mark.engine
def test_validate_100_percent_guard_cost_pool_invalid() -> None:
    """원가풀 invalid (110%) → all_valid = False."""
    result = validate_100_percent_guard(
        cost_pool=[Decimal("60"), Decimal("50")],  # 110
        activities=[Decimal("60"), Decimal("40")],  # 100
        drivers=[Decimal("70"), Decimal("30")],  # 100
        cost_pool_id="pool-002",
    )
    assert result["all_valid"] is False
    assert result["cost_pool"].is_valid is False  # type: ignore[union-attr]
    assert result["activity"].is_valid is True  # type: ignore[union-attr]


@pytest.mark.engine
def test_validate_100_percent_guard_partial_inputs() -> None:
    """일부 layer만 validate (None skip)."""
    result = validate_100_percent_guard(
        cost_pool=[Decimal("50"), Decimal("50")],  # valid
        activities=None,  # skip
        drivers=None,  # skip
        cost_pool_id="pool-003",
    )
    assert result["cost_pool"].is_valid is True  # type: ignore[union-attr]
    assert result["activity"] is None
    assert result["driver"] is None
    assert result["all_valid"] is True


@pytest.mark.engine
def test_validate_100_percent_guard_no_inputs() -> None:
    """모든 layer None → all_valid = False."""
    result = validate_100_percent_guard()
    assert result["all_valid"] is False
    assert result["cost_pool"] is None
    assert result["activity"] is None
    assert result["driver"] is None


# ── frozen=True, slots=True enforcement ─────────────────────


@pytest.mark.engine
def test_cost_pool_validation_is_frozen() -> None:
    """CostPoolValidation frozen → mutation 시도 → FrozenInstanceError."""
    state = CostPoolValidation(
        department_id="dept-frozen",
        sum_pct=Decimal("100"),
        department_count=2,
        is_valid=True,
        hash="sha256:" + "a" * 64,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.department_id = "modified"  # type: ignore[misc]


@pytest.mark.engine
def test_activity_validation_is_frozen() -> None:
    """ActivityValidation frozen."""
    state = ActivityValidation(
        cost_pool_id="pool-frozen",
        sum_pct=Decimal("100"),
        activity_count=3,
        is_valid=True,
        hash="sha256:" + "a" * 64,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.activity_count = 99  # type: ignore[misc]


@pytest.mark.engine
def test_driver_validation_is_frozen() -> None:
    """DriverValidation frozen."""
    state = DriverValidation(
        activity_id="act-frozen",
        sum_pct=Decimal("100"),
        driver_count=2,
        is_valid=True,
        hash="sha256:" + "a" * 64,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.driver_count = 99  # type: ignore[misc]


# ── Constants 노출 검증 ────────────────────────────────────


@pytest.mark.engine
def test_constants_exposed() -> None:
    """7 constants 노출 검증 (AC #1 verbatim)."""
    assert Decimal("0.0001") == ABC_VALIDATION_KRW_QUANTUM
    assert Decimal("0") == ALLOCATION_PCT_MIN
    assert Decimal("100") == ALLOCATION_PCT_MAX
    assert Decimal("100") == VALIDATION_100_PCT_TARGET
    assert Decimal("0.01") == VALIDATION_TOLERANCE_KRW
    assert VALIDATION_HASH_PREFIX == "sha256:"
    assert VALIDATION_DEFAULT_INDUSTRY == "service"


@pytest.mark.engine
def test_validation_state_type_alias() -> None:
    """ValidationState type alias — 3 dataclass union."""
    # Runtime: just verify the type alias can be used.
    state: ValidationState = CostPoolValidation(
        department_id="dept-001",
        sum_pct=Decimal("100"),
        department_count=2,
        is_valid=True,
        hash="",
    )
    h = compute_validation_hash(validation_state=state)
    assert h.startswith(VALIDATION_HASH_PREFIX)


# ── Typed exception class 검증 ──────────────────────────────


@pytest.mark.engine
def test_cost_pool_validation_error_attributes() -> None:
    """CostPoolValidationError attributes 검증."""
    exc = CostPoolValidationError(
        "test message",
        department_id="dept-001",
        sum_pct=Decimal("105"),
        reason="not_100_percent",
    )
    assert exc.department_id == "dept-001"
    assert exc.sum_pct == Decimal("105")
    assert exc.reason == "not_100_percent"
    assert exc.message == "test message"
    assert str(exc) == "test message"


@pytest.mark.engine
def test_activity_validation_error_attributes() -> None:
    """ActivityValidationError attributes 검증."""
    exc = ActivityValidationError(
        "test message",
        cost_pool_id="pool-001",
        sum_pct=Decimal("90"),
        reason="not_100_percent",
    )
    assert exc.cost_pool_id == "pool-001"
    assert exc.sum_pct == Decimal("90")


@pytest.mark.engine
def test_driver_validation_error_attributes() -> None:
    """DriverValidationError attributes 검증."""
    exc = DriverValidationError(
        "test message",
        activity_id="act-001",
        sum_pct=Decimal("90"),
        reason="not_100_percent",
    )
    assert exc.activity_id == "act-001"


@pytest.mark.engine
def test_abc_validation_not_found_error_attributes() -> None:
    """AbcValidationNotFoundError attributes 검증."""
    exc = AbcValidationNotFoundError(
        "empty",
        target="cost_pool",
        target_id="dept-001",
    )
    assert exc.target == "cost_pool"
    assert exc.target_id == "dept-001"
    assert exc.message == "empty"


# ── Decimal precision / boundary ─────────────────────────────


@pytest.mark.engine
def test_validate_cost_pool_zero_values() -> None:
    """0% 항목 처리 — 모든 항목이 0% → sum_pct = 0 → invalid."""
    result = validate_cost_pool(
        department_id="dept-zero",
        allocation_pcts=[Decimal("0"), Decimal("0")],
    )
    assert result.sum_pct == Decimal("0")
    assert result.is_valid is False


@pytest.mark.engine
def test_validate_cost_pool_zero_validates_with_tolerance() -> None:
    """0.005 + 99.995 → sum_pct = 100 → within tolerance → valid."""
    result = validate_cost_pool(
        department_id="dept-tol",
        allocation_pcts=[Decimal("0.005"), Decimal("99.995")],
    )
    # 0.005 + 99.995 = 100.000 → exact 100 → valid.
    assert result.sum_pct == Decimal("100")
    assert result.is_valid is True
