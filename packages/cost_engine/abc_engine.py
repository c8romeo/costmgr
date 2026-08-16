"""packages.cost_engine.abc_engine — Story 9.1 ABC 100% Validation pure kernel.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m9_abc/services/abc_validation_service.py`
  (T2 service layer — validate_100_percent_guard orchestrator)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes input
values fetched from DB (`tenant_settings.abc.drivers` JSONB storage);
this kernel owns the 100% guard math + V8 determinism + ABC cost
pool/activity/driver validation logic.

PRD §F9.1 (원가풀 행 합·활동 열 합·동인 합 모두 100% 가드):
- Cost pool row sum MUST equal 100% (allow ±0.01 KRW tolerance for
  Decimal-as-string rounding, AD-15).
- Activity column sum MUST equal 100% (3+ activities per cost pool).
- Driver sum MUST equal 100% (2+ drivers per activity).

PRD §F9.2 (TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위):
- ABC allocation engine honestly DEFER to Story 9-2 (D-9-1-DEFER-1/2).
- 9-1 wires validation guard ONLY — no CCR compute, no allocation.

PRD §14.B Non-Goal #1 verbatim: "제조부문 ABC 미구현" (1차 MVP 회색 배지
placeholder).

V8 determinism: `compute_validation_hash` 는 hashlib.sha256 결정론 digest
— 동일 입력 → byte-identical hash (Epic 4 baseline + 7-1/7-2/8-1/8-2/8-3
패턴). hash format = `sha256:` + 64-char hexdigest (32 bytes).

A19 cohesion pattern 6번째 검증: `abc_engine.py` 는
`packages/cost_engine/cvp.py` (7-1) + `packages/cost_engine/projection.py`
(7-2) + `packages/cost_engine/budget_period_key.py` (8-1) +
`packages/cost_engine/budget_variance.py` (8-2) +
`packages/cost_engine/budget_pre_standard.py` (8-3) 와 surface 분리 —
concern 별도 (ABC validation + 100% guard 는 ABC concern).

A26 forward-lock Option A 결정 wire: abc_engine.py 는 6번째 A19 surface로
신설, projection.py + budget_pre_standard.py + cvp.py + budget_period_key.py
+ budget_variance.py 와 **완전 독립** (no cross-import, 9-2 진입 시점에
A28 forward-lock 결정 후 abc_engine.py 확장 = CCR compute + allocation
engine wire).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

# ── Constants ────────────────────────────────────────────────
# Decimal quantum for ABC validation monetary values (PRD §F9.1 + AD-8).
# Decimal-as-string 4 decimal places ROUND_HALF_EVEN parity with TS decimal.js.
ABC_VALIDATION_KRW_QUANTUM: Final[Decimal] = Decimal("0.0001")

# Allocation percentage bounds (PRD §F9.1 + UX safety guard).
# 각 department/activity/driver 항목의 allocation_pct 는 0 <= value <= 100.
ALLOCATION_PCT_MIN: Final[Decimal] = Decimal("0")
ALLOCATION_PCT_MAX: Final[Decimal] = Decimal("100")

# 100% target — 원가풀 행 합·활동 열 합·동인 합 모두 100% 가드.
# Decimal-as-string AD-8 + AD-15 cross-language conventions.
VALIDATION_100_PCT_TARGET: Final[Decimal] = Decimal("100")

# Tolerance for 100% equality (KRW 0.01 = Decimal quantum precision).
# AD-15 cross-language parity — TS decimal.js 동일 quantum 적용.
VALIDATION_TOLERANCE_KRW: Final[Decimal] = Decimal("0.01")

# Hash prefix for compute_validation_hash (V8 determinism trace).
VALIDATION_HASH_PREFIX: Final[str] = "sha256:"

# Default industry for ABC validation (PRD §9 + §14.B verbatim "service" 1차).
# 9-1 entry point validates cost pool / activity / driver for service
# business only. Manufacturing ABC 회색 배지 placeholder (Epic 8 8-2 ABCD
# 회색 배지 precedent).
VALIDATION_DEFAULT_INDUSTRY: Final[str] = "service"


# ── Frozen dataclasses ───────────────────────────────────────
@dataclass(frozen=True, slots=True)
class CostPoolValidation:
    """Frozen cost pool 100% validation entity (PRD §F9.1).

    `department_id` = str (부서 식별자 — tenant-relative UUID-as-string)
    `sum_pct` = Decimal (allocation_pcts 합계, Decimal-as-string AD-15)
    `department_count` = int (부서 개수, ≥ 1)
    `is_valid` = bool (sum_pct == 100 ± tolerance)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    department_id: str
    sum_pct: Decimal
    department_count: int
    is_valid: bool
    hash: str


@dataclass(frozen=True, slots=True)
class ActivityValidation:
    """Frozen activity column 100% validation entity (PRD §F9.1).

    `cost_pool_id` = str (원가풀 식별자 — tenant-relative UUID-as-string)
    `sum_pct` = Decimal (활동 시간 배분 합계)
    `activity_count` = int (활동 개수, ≥ 1)
    `is_valid` = bool
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    cost_pool_id: str
    sum_pct: Decimal
    activity_count: int
    is_valid: bool
    hash: str


@dataclass(frozen=True, slots=True)
class DriverValidation:
    """Frozen driver 100% validation entity (PRD §F9.1).

    `activity_id` = str (활동 식별자 — tenant-relative UUID-as-string)
    `sum_pct` = Decimal (동인 사용량 합계)
    `driver_count` = int (동인 개수, ≥ 1)
    `is_valid` = bool
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    activity_id: str
    sum_pct: Decimal
    driver_count: int
    is_valid: bool
    hash: str


# Discriminated union for compute_validation_hash (TypeScript mirror parity).
ValidationState = CostPoolValidation | ActivityValidation | DriverValidation


# ── Typed exceptions ────────────────────────────────────────
class CostPoolValidationError(ValueError):
    """PRD §F9.1 + AD-15 envelope — 원가풀 행 합 100% 가드 실패.

    HTTP 422 COST_POOL_INVALID_SUM envelope (CR 12-5 D-14).
    sum_pct ≠ 100% ± tolerance 시 raise (예: 105% → "현재 105%" 메시지).

    `department_id` identifies which cost pool row failed (machine code),
    `sum_pct` is the actual sum (Decimal-as-string AD-15),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        department_id: str,
        sum_pct: Decimal,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.department_id = department_id
        self.sum_pct = sum_pct
        self.reason = reason


class ActivityValidationError(ValueError):
    """PRD §F9.1 + AD-15 envelope — 활동 열 합 100% 가드 실패.

    HTTP 422 ACTIVITY_INVALID_SUM envelope (CR 12-5 D-14).
    sum_pct ≠ 100% ± tolerance 시 raise.
    """

    def __init__(
        self,
        message: str,
        *,
        cost_pool_id: str,
        sum_pct: Decimal,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.cost_pool_id = cost_pool_id
        self.sum_pct = sum_pct
        self.reason = reason


class DriverValidationError(ValueError):
    """PRD §F9.1 + AD-15 envelope — 동인 합 100% 가드 실패.

    HTTP 422 DRIVER_INVALID_SUM envelope (CR 12-5 D-14).
    sum_pct ≠ 100% ± tolerance 시 raise.
    """

    def __init__(
        self,
        message: str,
        *,
        activity_id: str,
        sum_pct: Decimal,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.activity_id = activity_id
        self.sum_pct = sum_pct
        self.reason = reason


class AbcValidationNotFoundError(Exception):
    """PRD §F9.1 + AD-15 envelope — 100% 가드 검증 대상 미존재.

    HTTP 404 ABC_VALIDATION_NOT_FOUND envelope (CR 12-5 D-14).
    validate_100_percent_guard 호출 시점에 cost_pool / activity / driver
    입력이 빈 경우 raise.
    """

    def __init__(
        self,
        message: str,
        *,
        target: str,  # "cost_pool" | "activity" | "driver"
        target_id: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.target = target
        self.target_id = target_id


# ── Pure functions ───────────────────────────────────────────
def _validate_pct_list(
    *,
    allocation_pcts: list[Decimal],
    field_name: str,
) -> None:
    """Internal helper — allocation_pcts 리스트 검증 (PRD §F9.1 + AD-8).

    Edge cases (각 typed exception raise):
      - empty list → `AbcValidationNotFoundError` (target="cost_pool")
      - 각 value not Decimal → `CostPoolValidationError` (type_mismatch)
      - 각 value < ALLOCATION_PCT_MIN 또는 > ALLOCATION_PCT_MAX →
        `CostPoolValidationError` (out_of_range)
    """
    if not allocation_pcts:
        raise AbcValidationNotFoundError(
            f"{field_name} allocation_pcts is empty",
            target=field_name,
            target_id="<empty>",
        )
    for idx, value in enumerate(allocation_pcts):
        if not isinstance(value, Decimal):
            raise CostPoolValidationError(
                f"{field_name}[{idx}] must be Decimal, got "
                f"{type(value).__name__}",
                department_id=f"{field_name}[{idx}]",
                sum_pct=Decimal("0"),
                reason="type_mismatch",
            )
        if value < ALLOCATION_PCT_MIN:
            raise CostPoolValidationError(
                f"{field_name}[{idx}] must be >= 0",
                department_id=f"{field_name}[{idx}]",
                sum_pct=Decimal("0"),
                reason="negative_value",
            )
        if value > ALLOCATION_PCT_MAX:
            raise CostPoolValidationError(
                f"{field_name}[{idx}] must be <= 100",
                department_id=f"{field_name}[{idx}]",
                sum_pct=Decimal("0"),
                reason="exceeds_max",
            )


def _is_100_percent(*, sum_pct: Decimal) -> bool:
    """PRD §F9.1 100% 가드 — sum_pct == 100 ± tolerance."""
    return abs(sum_pct - VALIDATION_100_PCT_TARGET) <= VALIDATION_TOLERANCE_KRW


def validate_cost_pool(
    *,
    department_id: str,
    allocation_pcts: list[Decimal],
) -> CostPoolValidation:
    """PRD §F9.1 verbatim — 원가풀 행 합 100% 가드.

    Args:
      department_id: 부서 식별자 (tenant-relative UUID-as-string).
      allocation_pcts: 각 부서의 allocation 퍼센트 리스트 (Decimal, 0~100).
                       예: 4개 부서 각 25% → [25, 25, 25, 25].

    Returns:
      CostPoolValidation(department_id, sum_pct, department_count,
                          is_valid, hash).

    Edge cases:
      - empty allocation_pcts → `AbcValidationNotFoundError`
      - 각 value 음수 또는 > 100 → `CostPoolValidationError`
      - sum_pct ≠ 100 ± tolerance → `is_valid=False` (return, not raise;
        service layer decide raise). 단, PRD §F9.1 verbatim "100%가 아니면
        [계산]이 잠기는 것" → service layer 는 is_valid=False 면 frontend
        disabled 신호로 사용.

    V8 determinism: 동일 department_id + allocation_pcts → byte-identical hash.

    AD-5 stdlib-only, AD-8 Decimal-as-string, AD-11 layer rule.
    """
    _validate_pct_list(
        allocation_pcts=allocation_pcts,
        field_name="cost_pool",
    )

    sum_pct = sum(allocation_pcts, Decimal("0"))
    is_valid = _is_100_percent(sum_pct=sum_pct)
    department_count = len(allocation_pcts)

    # Compute placeholder for hash (V8 determinism pre-compute).
    validation = CostPoolValidation(
        department_id=department_id,
        sum_pct=sum_pct,
        department_count=department_count,
        is_valid=is_valid,
        hash="",  # placeholder, computed below
    )
    digest = hashlib.sha256(repr(validation).encode()).hexdigest()
    return CostPoolValidation(
        department_id=department_id,
        sum_pct=sum_pct,
        department_count=department_count,
        is_valid=is_valid,
        hash=f"{VALIDATION_HASH_PREFIX}{digest}",
    )


def validate_activity(
    *,
    cost_pool_id: str,
    activity_pcts: list[Decimal],
) -> ActivityValidation:
    """PRD §F9.1 verbatim — 활동 열 합 100% 가드.

    Args:
      cost_pool_id: 원가풀 식별자 (tenant-relative UUID-as-string).
      activity_pcts: 각 활동의 시간 배분 퍼센트 리스트 (Decimal, 0~100).
                     예: 3개 활동 각 33.33% → [33.33, 33.33, 33.34].

    Returns:
      ActivityValidation(cost_pool_id, sum_pct, activity_count, is_valid, hash).

    Edge cases: validate_cost_pool 와 동일 패턴.
    """
    _validate_pct_list(
        allocation_pcts=activity_pcts,
        field_name="activity",
    )

    sum_pct = sum(activity_pcts, Decimal("0"))
    is_valid = _is_100_percent(sum_pct=sum_pct)
    activity_count = len(activity_pcts)

    validation = ActivityValidation(
        cost_pool_id=cost_pool_id,
        sum_pct=sum_pct,
        activity_count=activity_count,
        is_valid=is_valid,
        hash="",  # placeholder
    )
    digest = hashlib.sha256(repr(validation).encode()).hexdigest()
    return ActivityValidation(
        cost_pool_id=cost_pool_id,
        sum_pct=sum_pct,
        activity_count=activity_count,
        is_valid=is_valid,
        hash=f"{VALIDATION_HASH_PREFIX}{digest}",
    )


def validate_driver(
    *,
    activity_id: str,
    driver_pcts: list[Decimal],
) -> DriverValidation:
    """PRD §F9.1 verbatim — 동인 합 100% 가드.

    Args:
      activity_id: 활동 식별자 (tenant-relative UUID-as-string).
      driver_pcts: 각 동인의 사용량 퍼센트 리스트 (Decimal, 0~100).
                   예: 2개 동인 60%/40% → [60, 40].

    Returns:
      DriverValidation(activity_id, sum_pct, driver_count, is_valid, hash).

    Edge cases: validate_cost_pool 와 동일 패턴.
    """
    _validate_pct_list(
        allocation_pcts=driver_pcts,
        field_name="driver",
    )

    sum_pct = sum(driver_pcts, Decimal("0"))
    is_valid = _is_100_percent(sum_pct=sum_pct)
    driver_count = len(driver_pcts)

    validation = DriverValidation(
        activity_id=activity_id,
        sum_pct=sum_pct,
        driver_count=driver_count,
        is_valid=is_valid,
        hash="",  # placeholder
    )
    digest = hashlib.sha256(repr(validation).encode()).hexdigest()
    return DriverValidation(
        activity_id=activity_id,
        sum_pct=sum_pct,
        driver_count=driver_count,
        is_valid=is_valid,
        hash=f"{VALIDATION_HASH_PREFIX}{digest}",
    )


def compute_validation_hash(
    *,
    validation_state: ValidationState,
) -> str:
    """V8 determinism hash for ABC validation state (Epic 4 baseline + 8-3 pattern).

    `hashlib.sha256(repr(validation_state).encode()).hexdigest()` —
    32 chars hexdigest, `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: dataclass `frozen=True, slots=True` → repr은 결정론
    (dataclass auto-generated repr + Decimal repr with full precision).

    Returns:
      `f"sha256:{32-char-hexdigest}"` (= 64 chars hexdigest).

    Type-safe: accepts CostPoolValidation | ActivityValidation | DriverValidation.
    """
    if not isinstance(
        validation_state,
        (CostPoolValidation, ActivityValidation, DriverValidation),
    ):
        raise ValueError(
            f"validation_state must be CostPoolValidation | "
            f"ActivityValidation | DriverValidation, "
            f"got {type(validation_state).__name__}"
        )
    digest = hashlib.sha256(repr(validation_state).encode()).hexdigest()
    return f"{VALIDATION_HASH_PREFIX}{digest}"


def validate_100_percent_guard(
    *,
    cost_pool: list[Decimal] | None = None,
    activities: list[Decimal] | None = None,
    drivers: list[Decimal] | None = None,
    cost_pool_id: str = "<unknown>",
    activity_id: str = "<unknown>",
) -> dict[str, object]:
    """PRD §F9.1 verbatim 3-layer 100% guard orchestrator (service-layer convenience).

    Sequentially validates cost pool → activity → driver. Returns dict
    summarizing each layer's validation state. **Does NOT raise** when
    is_valid=False — frontend disabled signal uses is_valid=False directly.

    Pure kernel delegation (AD-5 + AD-11).

    Args:
      cost_pool: allocation_pcts for departments (optional — None = skip).
      activities: activity_pcts for activities (optional — None = skip).
      drivers: driver_pcts for drivers (optional — None = skip).
      cost_pool_id: 원가풀 ID (validation_state 메타).
      activity_id: 활동 ID (validation_state 메타).

    Returns:
      dict with keys:
        - "cost_pool": CostPoolValidation | None
        - "activity": ActivityValidation | None
        - "driver": DriverValidation | None
        - "all_valid": bool (3 layer 모두 is_valid=True 일 때만 True)

    Edge cases:
      - all inputs None → all_valid=False, all validation_state=None.
      - cost_pool valid BUT activity invalid → all_valid=False, 둘 다 return.
    """
    cost_pool_state: CostPoolValidation | None = None
    activity_state: ActivityValidation | None = None
    driver_state: DriverValidation | None = None

    if cost_pool is not None:
        cost_pool_state = validate_cost_pool(
            department_id=cost_pool_id,
            allocation_pcts=cost_pool,
        )

    if activities is not None:
        activity_state = validate_activity(
            cost_pool_id=cost_pool_id,
            activity_pcts=activities,
        )

    if drivers is not None:
        driver_state = validate_driver(
            activity_id=activity_id,
            driver_pcts=drivers,
        )

    all_valid = all(
        state.is_valid
        for state in (cost_pool_state, activity_state, driver_state)
        if state is not None
    ) and any(
        state is not None
        for state in (cost_pool_state, activity_state, driver_state)
    )

    return {
        "cost_pool": cost_pool_state,
        "activity": activity_state,
        "driver": driver_state,
        "all_valid": all_valid,
    }


__all__ = [
    # Frozen dataclasses
    "CostPoolValidation",
    "ActivityValidation",
    "DriverValidation",
    "ValidationState",
    # Typed exceptions
    "CostPoolValidationError",
    "ActivityValidationError",
    "DriverValidationError",
    "AbcValidationNotFoundError",
    # Pure functions
    "validate_cost_pool",
    "validate_activity",
    "validate_driver",
    "compute_validation_hash",
    "validate_100_percent_guard",
    # Constants
    "ABC_VALIDATION_KRW_QUANTUM",
    "ALLOCATION_PCT_MIN",
    "ALLOCATION_PCT_MAX",
    "VALIDATION_100_PCT_TARGET",
    "VALIDATION_TOLERANCE_KRW",
    "VALIDATION_HASH_PREFIX",
    "VALIDATION_DEFAULT_INDUSTRY",
]
