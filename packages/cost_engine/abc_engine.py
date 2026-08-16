"""packages.cost_engine.abc_engine — Story 9.1 ABC 100% Validation pure kernel.

Story 9.1 surface: 4 NEW pure functions + 3 frozen dataclasses + 4 typed
exceptions + 7 constants — 100% 가드 validate_cost_pool / validate_activity /
validate_driver + validate_100_percent_guard orchestrator (PRD §F9.1 verbatim).

Story 9.2 EXTENSION: 3 NEW pure functions + 5 frozen dataclasses
(CCRResult + ActivityMapping + CostObjectRow + AllocationResult +
UnusedCapacityRow) + 2 typed exceptions (CcrComputeError +
AllocationBalanceError) + 3 NEW constants (CCR_KRW_QUANTUM +
ABC_PRECISION_KRW_TOLERANCE + CCR_HASH_PREFIX) — CCR compute + Activity
mapping + Cost Object Breakdown (PRD §F9.2 verbatim + §A9 + §V7).

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m9_abc/services/abc_validation_service.py`
  (Story 9.1 T2 service layer — validate_100_percent_guard orchestrator)
- `apps/api/modules/m9_abc/services/abc_allocation_service.py`
  (Story 9.2 T2 service layer — CCRPort.compute 호출자 ONLY, AD-21
  단일 소유 + compute_allocation + produce_unused_capacity_row)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes input
values fetched from DB (`tenant_settings.abc.drivers` JSONB storage);
this kernel owns the 100% guard math + V8 determinism + ABC cost
pool/activity/driver validation + CCR compute + ABC allocation + V7 ABC
무결성 (Σ breakdown + unused = Σ department cost) logic.

PRD §F9.1 (원가풀 행 합·활동 열 합·동인 합 모두 100% 가드):
- Cost pool row sum MUST equal 100% (allow ±0.01 KRW tolerance for
  Decimal-as-string rounding, AD-15).
- Activity column sum MUST equal 100% (3+ activities per cost pool).
- Driver sum MUST equal 100% (2+ drivers per activity).

PRD §F9.2 (TDABC CCR 부서 원가 ÷ 실제 조업능력 1원 단위):
- `CCR = department_cost ÷ practical_capacity_hours` (KRW 정수, 1-Won precision, AD-8)
- 미사용능력 별도 행 표시 (PRD §A9 verbatim "미사용능력 6,600,000원")
- CCR compute = `CCRPort.compute(tenant_id, period_key, department_id)` 단일 소유 (AD-21)
- M9 owns no public endpoint for 9-2 wire (AD-18 + AD-19 forward-lock)
- 9-3 진입 시점에 M3 dispatch wire (A29 forward-lock 결정 후)

PRD §A9: 유휴(미사용)능력 원가의 별도 관리 — 전통·ABC 공통.
PRD §A6: 완전배부와 대차평형 (Zero-Leak 원칙) — V7 ABC 무결성.
PRD §V7: ABC 무결성 — Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가).

PRD §14.B Non-Goal #1 verbatim: "제조부문 ABC 미구현" (1차 MVP 회색 배지
placeholder).

V8 determinism: `compute_validation_hash` + `compute_ccr_hash` =
hashlib.sha256 결정론 digest — 동일 입력 → byte-identical hash
(Epic 4 baseline + 7-1/7-2/8-1/8-2/8-3 패턴). hash format =
`sha256:` + 64-char hexdigest (32 bytes).

A19 cohesion pattern 7 surface (9-2 EXTENSION 누적):
  1: `inventory_math.py` (Epic 5)
  2: `cvp.py` (7-1)
  3: `projection.py` (7-2)
  4: `budget_period_key.py` (8-1)
  5: `budget_variance.py` (8-2)
  6: `budget_pre_standard.py` (8-3)
  7: `abc_engine.py` (9-1 + 9-2 EXTENSION — A26 Option A 채택, NO
     cross-import with other A19 surfaces, 동일 surface 누적 wire).

AD-21 CCRPort.compute 단일 소유 — M9 service layer ONLY. 9-3 진입 시점에
A29 M3 dispatch ↔ M9 dispatch dual-route 결정 후 9-3 wire (forward-lock).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
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

# ── Story 9.2 NEW constants (PRD §F9.2 + AD-8 1-Won precision) ────
# Decimal quantum for ABC CCR monetary values (PRD §F9.2 + AD-8).
# KRW integer = 0 decimal places (1원 precision, AD-8 BigInteger parity).
# 예: 13,200,000 / 400 = 33,000 → KRW 정수.
CCR_KRW_QUANTUM: Final[Decimal] = Decimal("1")

# ABC allocation tolerance (PRD §A6 verbatim "완전배부·대차평형 1원 단위").
# Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) — 1원 단위 검증.
# tolerance = 0.01 KRW (Decimal quantum precision, 9-1 pattern 동일).
ABC_PRECISION_KRW_TOLERANCE: Final[Decimal] = Decimal("0.01")

# Hash prefix for compute_ccr_hash (V8 determinism trace, 9-1 pattern 동일).
CCR_HASH_PREFIX: Final[str] = "sha256:"


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


# ── Story 9.2 frozen dataclasses (PRD §F9.2 + §A9 + §V7) ───────────
@dataclass(frozen=True, slots=True)
class CCRResult:
    """Frozen CCR compute entity (PRD §F9.2 verbatim).

    `CCR = department_cost ÷ practical_capacity_hours` — KRW 정수,
    1-Won precision (AD-8 Decimal-as-string).

    `department_id` = str (부서 식별자 — tenant-relative UUID-as-string)
    `department_cost` = Decimal (KRW 정수, 부서 원가)
    `practical_capacity_hours` = Decimal (실제 조업능력 시간)
    `ccr_per_hour` = Decimal (KRW 정수, 시간당 자원동인율)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)

    1-Won precision invariant: `ccr_per_hour = quantize(department_cost /
    practical_capacity_hours, KRW_QUANTUM, ROUND_HALF_EVEN)` — KR 정수.
    """

    department_id: str
    department_cost: Decimal
    practical_capacity_hours: Decimal
    ccr_per_hour: Decimal
    hash: str


@dataclass(frozen=True, slots=True)
class ActivityMapping:
    """Frozen activity mapping entity (PRD §F9.2 + §A9 verbatim).

    활동별 시간 배분 × CCR = 활동별 배부액 (1-Won precision).

    `activity_id` = str (활동 식별자)
    `hours` = Decimal (활동 시간 배분, KRW 정수 또는 시간 정수)
    `ccr_amount_krw` = Decimal (KRW 정수, 배부액 = hours × ccr_per_hour)
    """

    activity_id: str
    hours: Decimal
    ccr_amount_krw: Decimal


@dataclass(frozen=True, slots=True)
class CostObjectRow:
    """Frozen Cost Object Breakdown row (PRD §9 #21 + §F9.2).

    `product_id` (원가대상)별 4컬럼 — 원가풀·활동·동인·배부액.

    `product_id` = str (원가대상 식별자)
    `activity_id` = str (활동 식별자)
    `driver_id` = str (동인 식별자)
    `allocated_krw` = Decimal (KRW 정수, 배부액)
    """

    product_id: str
    activity_id: str
    driver_id: str
    allocated_krw: Decimal


@dataclass(frozen=True, slots=True)
class AllocationResult:
    """Frozen ABC Allocation Result (PRD §F9.2 + §A6 + §V7 verbatim).

    V7 ABC 무결성: `Σ(activity_mappings.ccr_amount_krw) +
    unused.unused_cost_krw == department_cost` — 1원 단위 검증.
    `is_balanced = (total_breakdown_sum + unused_cost == department_cost)`
    일 때만 True (PRD §A6 verbatim "완전배부·대차평형").

    `ccr` = CCRResult (CCR compute 결과)
    `activity_mappings` = tuple[ActivityMapping] (활동별 배부)
    `cost_object_breakdown` = tuple[CostObjectRow] (원가대상별 배부)
    `unused_capacity` = UnusedCapacityRow (미사용능력 별도 행)
    `department_cost` = Decimal (Σ 부서 원가)
    `total_breakdown_sum` = Decimal (Σ cost_object_breakdown 배부액)
    `is_balanced` = bool (V7 ABC 무결성 1원 단위 만족 여부)
    """

    ccr: CCRResult
    activity_mappings: tuple[ActivityMapping, ...]
    cost_object_breakdown: tuple[CostObjectRow, ...]
    unused_capacity: UnusedCapacityRow
    department_cost: Decimal
    total_breakdown_sum: Decimal
    is_balanced: bool


@dataclass(frozen=True, slots=True)
class UnusedCapacityRow:
    """Frozen 미사용능력 별도 행 (PRD §A9 verbatim "별도 항목으로 구분 관리").

    예: 부서 실제 조업능력 600h, 사용 400h, 미사용 200h × CCR 33,000원/시간
    = 6,600,000원 — 별도 행 "미사용능력 6,600,000원" 표시 (PRD §A9).

    `unused_hours` = Decimal (미사용 시간)
    `ccr_per_hour` = Decimal (KRW 정수, CCR 시간당 자원동인율)
    `unused_cost_krw` = Decimal (KRW 정수, 미사용 원가)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    unused_hours: Decimal
    ccr_per_hour: Decimal
    unused_cost_krw: Decimal
    hash: str


# Discriminated union for ABC allocation state (TS mirror parity).
AllocationState = CCRResult | ActivityMapping | CostObjectRow | UnusedCapacityRow | AllocationResult


# ── Story 9.2 typed exceptions (CR 12-5 D-14 envelope main.py handler) ──
class CcrComputeError(ValueError):
    """PRD §F9.2 + AD-15 envelope — CCR compute 실패.

    HTTP 422 CCR_INVALID_CAPACITY envelope (CR 12-5 D-14).
    `practical_capacity_hours = 0` (ZeroDivision 회피) 또는 음수 입력 시
    raise. 예: "CCR compute: practical_capacity_hours must be > 0".

    `department_id` identifies which department failed (machine code),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        department_id: str,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.department_id = department_id
        self.reason = reason


class AllocationBalanceError(ValueError):
    """PRD §A6 + §V7 verbatim ABC 무결성 1원 단위 가드 실패.

    HTTP 422 ALLOCATION_BALANCE_ERROR envelope (CR 12-5 D-14).
    `Σ(원가대상별 배부액) + 미사용능력 ≠ Σ(부서 원가)` (V7 invariant 깨짐) 시
    raise. 단, 9-2 wire = `is_balanced=False` return (frontend disabled signal
    사용), raise는 9-3 wire 결정 후 (D-9-3-DEFER candidate).

    `department_id` identifies which department failed (machine code),
    `expected_sum` is the expected department_cost (Decimal-as-string),
    `actual_sum` is the actual breakdown sum (Decimal-as-string),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        department_id: str,
        expected_sum: Decimal,
        actual_sum: Decimal,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.department_id = department_id
        self.expected_sum = expected_sum
        self.actual_sum = actual_sum
        self.reason = reason


# ── Story 9.2 pure functions (PRD §F9.2 + §A9 + §A6 + §V7) ────────
def _validate_ccr_inputs(
    *,
    department_id: str,
    department_cost: Decimal,
    practical_capacity_hours: Decimal,
) -> None:
    """Internal helper — CCR compute 입력 검증 (PRD §F9.2 + AD-8).

    Edge cases (각 typed exception raise):
      - `department_id` empty → `CcrComputeError(reason="empty_department_id")`
      - `department_cost` not Decimal → `CcrComputeError(reason="type_mismatch")`
      - `department_cost` < 0 → `CcrComputeError(reason="negative_cost")`
      - `practical_capacity_hours` not Decimal →
        `CcrComputeError(reason="type_mismatch")`
      - `practical_capacity_hours` ≤ 0 →
        `CcrComputeError(reason="invalid_capacity", code=CCR_INVALID_CAPACITY)`
    """
    if not department_id:
        raise CcrComputeError(
            "department_id must be non-empty",
            department_id=department_id,
            reason="empty_department_id",
        )
    if not isinstance(department_cost, Decimal):
        raise CcrComputeError(
            f"department_cost must be Decimal, got {type(department_cost).__name__}",
            department_id=department_id,
            reason="type_mismatch",
        )
    if department_cost < Decimal("0"):
        raise CcrComputeError(
            "department_cost must be non-negative",
            department_id=department_id,
            reason="negative_cost",
        )
    if not isinstance(practical_capacity_hours, Decimal):
        raise CcrComputeError(
            (
                f"practical_capacity_hours must be Decimal, "
                f"got {type(practical_capacity_hours).__name__}"
            ),
            department_id=department_id,
            reason="type_mismatch",
        )
    if practical_capacity_hours <= Decimal("0"):
        raise CcrComputeError(
            (
                "CCR compute: practical_capacity_hours must be > 0 "
                f"(got {practical_capacity_hours})"
            ),
            department_id=department_id,
            reason="invalid_capacity",
        )


def compute_ccr(
    *,
    department_id: str,
    department_cost: Decimal,
    practical_capacity_hours: Decimal,
) -> CCRResult:
    """PRD §F9.2 verbatim CCR compute — 부서 원가 ÷ 실제 조업능력 1원 단위.

    공식 (PRD §F9.2 + AD-8 ROUND_HALF_EVEN):
      - `ccr_per_hour = quantize(department_cost / practical_capacity_hours, 1)`
        (KRW 정수, 1-Won precision)
      - 예: 13,200,000 / 400 = 33,000 (33,000원/시간)

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Args:
      department_id: 부서 식별자 (tenant-relative UUID-as-string).
      department_cost: 부서 원가 (KRW 정수, Decimal-as-string AD-8).
      practical_capacity_hours: 실제 조업능력 시간 (Decimal).

    Returns:
      CCRResult(department_id, department_cost, practical_capacity_hours,
                  ccr_per_hour, hash).

    Edge cases (CcrComputeError raise):
      - empty department_id → reason="empty_department_id"
      - department_cost not Decimal → reason="type_mismatch"
      - department_cost < 0 → reason="negative_cost"
      - practical_capacity_hours not Decimal → reason="type_mismatch"
      - practical_capacity_hours ≤ 0 → reason="invalid_capacity" (HTTP 422)

    V8 determinism: 동일 3 inputs → byte-identical hash.

    AD-21 `CCRPort.compute` 단일 소유 — M9 service layer ONLY.
    """
    _validate_ccr_inputs(
        department_id=department_id,
        department_cost=department_cost,
        practical_capacity_hours=practical_capacity_hours,
    )

    ccr_per_hour = (department_cost / practical_capacity_hours).quantize(
        CCR_KRW_QUANTUM, rounding=ROUND_HALF_EVEN
    )

    # Compute placeholder for hash (V8 determinism pre-compute).
    result = CCRResult(
        department_id=department_id,
        department_cost=department_cost,
        practical_capacity_hours=practical_capacity_hours,
        ccr_per_hour=ccr_per_hour,
        hash="",  # placeholder, computed below
    )
    digest = hashlib.sha256(repr(result).encode()).hexdigest()
    return CCRResult(
        department_id=department_id,
        department_cost=department_cost,
        practical_capacity_hours=practical_capacity_hours,
        ccr_per_hour=ccr_per_hour,
        hash=f"{CCR_HASH_PREFIX}{digest}",
    )


def compute_ccr_hash(*, ccr_result: CCRResult) -> str:
    """V8 determinism hash for CCRResult (Story 8-3 + 9-1 pattern 동일).

    `hashlib.sha256(repr(ccr_result).encode()).hexdigest()` —
    32 bytes hexdigest (64 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `CCRResult` is `frozen=True, slots=True` — repr은 결정론
    (dataclass auto-generated repr + Decimal repr with full precision).

    Returns:
      `f"sha256:{64-char-hexdigest}"`.

    Type-safe: accepts CCRResult ONLY.
    """
    if not isinstance(ccr_result, CCRResult):
        raise ValueError(
            f"ccr_result must be CCRResult, "
            f"got {type(ccr_result).__name__}"
        )
    digest = hashlib.sha256(repr(ccr_result).encode()).hexdigest()
    return f"{CCR_HASH_PREFIX}{digest}"


def produce_unused_capacity_row(
    *,
    ccr: CCRResult,
    used_hours: Decimal,
) -> UnusedCapacityRow:
    """PRD §A9 verbatim — 미사용능력 별도 행 생성 (1-Won precision).

    공식 (PRD §F9.2 + §A9):
      - `unused_hours = practical_capacity_hours - used_hours`
      - `unused_cost_krw = quantize(unused_hours × ccr_per_hour, 1)`
        (KRW 정수, 1-Won precision)
      - 예: 600 - 400 = 200h × 33,000원/시간 = 6,600,000원

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Args:
      ccr: CCRResult (CCR compute 결과 — ccr_per_hour 사용).
      used_hours: 사용 시간 (Decimal).

    Returns:
      UnusedCapacityRow(unused_hours, ccr_per_hour, unused_cost_krw, hash).

    Edge cases:
      - `used_hours < 0` → `CcrComputeError(reason="negative_used_hours")`
      - `used_hours > practical_capacity_hours` →
        `CcrComputeError(reason="exceeds_capacity")`
      - `unused_hours = 0` → 정상 (KRW 0), 미사용능력 별도 행 "0원" 표시

    V8 determinism: 동일 ccr + used_hours → byte-identical hash.

    Korean SSOT: "미사용능력 {unused_cost_krw}원" (ko-KR.json SSOT, CR 11-4 D-002).
    """
    if not isinstance(used_hours, Decimal):
        raise CcrComputeError(
            f"used_hours must be Decimal, got {type(used_hours).__name__}",
            department_id=ccr.department_id,
            reason="type_mismatch",
        )
    if used_hours < Decimal("0"):
        raise CcrComputeError(
            "used_hours must be non-negative",
            department_id=ccr.department_id,
            reason="negative_used_hours",
        )
    if used_hours > ccr.practical_capacity_hours:
        raise CcrComputeError(
            (
                f"used_hours ({used_hours}) must be <= "
                f"practical_capacity_hours ({ccr.practical_capacity_hours})"
            ),
            department_id=ccr.department_id,
            reason="exceeds_capacity",
        )

    unused_hours = ccr.practical_capacity_hours - used_hours
    unused_cost_krw = (unused_hours * ccr.ccr_per_hour).quantize(
        CCR_KRW_QUANTUM, rounding=ROUND_HALF_EVEN
    )

    # Compute placeholder for hash (V8 determinism pre-compute).
    row = UnusedCapacityRow(
        unused_hours=unused_hours,
        ccr_per_hour=ccr.ccr_per_hour,
        unused_cost_krw=unused_cost_krw,
        hash="",  # placeholder, computed below
    )
    digest = hashlib.sha256(repr(row).encode()).hexdigest()
    return UnusedCapacityRow(
        unused_hours=unused_hours,
        ccr_per_hour=ccr.ccr_per_hour,
        unused_cost_krw=unused_cost_krw,
        hash=f"{CCR_HASH_PREFIX}{digest}",
    )


def _is_allocation_balanced(
    *,
    department_cost: Decimal,
    breakdown_sum: Decimal,
    unused_cost: Decimal,
) -> bool:
    """PRD §A6 + §V7 verbatim — Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가).

    1-Won precision invariant (Decimal-as-string, AD-8):
      `|breakdown_sum + unused_cost - department_cost| ≤ 0.01 KRW`
    """
    return (
        abs(breakdown_sum + unused_cost - department_cost)
        <= ABC_PRECISION_KRW_TOLERANCE
    )


def compute_allocation(
    *,
    ccr: CCRResult,
    activity_mappings: list[ActivityMapping],
    cost_object_breakdown: list[CostObjectRow],
    used_hours: Decimal,
) -> AllocationResult:
    """PRD §F9.2 + §A6 + §V7 verbatim ABC allocation.

    공식:
      - `unused_capacity = produce_unused_capacity_row(ccr, used_hours)`
      - `department_cost = ccr.department_cost` (Σ 부서 원가)
      - `total_breakdown_sum = Σ(cost_object_breakdown[i].allocated_krw)`
      - `is_balanced = _is_allocation_balanced(...)` (V7 ABC 무결성)

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Args:
      ccr: CCRResult (CCR compute 결과).
      activity_mappings: 활동별 매핑 리스트 (활동 시간 배분 × CCR).
      cost_object_breakdown: 원가대상별 배부 리스트 (4컬럼: 원가풀·활동·
                              동인·배부액).
      used_hours: 사용 시간 (Decimal).

    Returns:
      AllocationResult(ccr, activity_mappings, cost_object_breakdown,
                        unused_capacity, department_cost,
                        total_breakdown_sum, is_balanced).

    Edge cases:
      - `is_balanced = False` → service layer returns frontend disabled
        signal; **does NOT raise AllocationBalanceError** at 9-2 wire
        (D-9-3-DEFER candidate — 9-3 wire 결정 후).
      - empty cost_object_breakdown → total_breakdown_sum = 0,
        is_balanced = (0 + unused_cost == department_cost).
      - 빈 activity_mappings → 정상 (KPI 계산 영향 0).

    V8 determinism: 동일 ccr + mappings + breakdown + used_hours →
    byte-identical is_balanced + total_breakdown_sum (V7 invariant).

    AD-21 `CCRPort.compute` 호출자 = M9 service layer ONLY.
    """
    unused_capacity = produce_unused_capacity_row(
        ccr=ccr,
        used_hours=used_hours,
    )
    department_cost = ccr.department_cost
    total_breakdown_sum = sum(
        (row.allocated_krw for row in cost_object_breakdown),
        Decimal("0"),
    )
    is_balanced = _is_allocation_balanced(
        department_cost=department_cost,
        breakdown_sum=total_breakdown_sum,
        unused_cost=unused_capacity.unused_cost_krw,
    )

    return AllocationResult(
        ccr=ccr,
        activity_mappings=tuple(activity_mappings),
        cost_object_breakdown=tuple(cost_object_breakdown),
        unused_capacity=unused_capacity,
        department_cost=department_cost,
        total_breakdown_sum=total_breakdown_sum,
        is_balanced=is_balanced,
    )


def compute_allocation_hash(*, allocation: AllocationResult) -> str:
    """V8 determinism hash for AllocationResult (Story 8-3 + 9-1 pattern 동일).

    `hashlib.sha256(repr(allocation).encode()).hexdigest()` —
    32 bytes hexdigest (64 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `AllocationResult` is `frozen=True, slots=True` (with nested
    frozen dataclasses + tuples) — repr은 결정론 (dataclass auto-generated
    repr + Decimal repr with full precision).

    Returns:
      `f"sha256:{64-char-hexdigest}"`.

    Type-safe: accepts AllocationResult ONLY.
    """
    if not isinstance(allocation, AllocationResult):
        raise ValueError(
            f"allocation must be AllocationResult, "
            f"got {type(allocation).__name__}"
        )
    digest = hashlib.sha256(repr(allocation).encode()).hexdigest()
    return f"{CCR_HASH_PREFIX}{digest}"


__all__ = [
    # Story 9.1 — Frozen dataclasses (100% validation)
    "CostPoolValidation",
    "ActivityValidation",
    "DriverValidation",
    "ValidationState",
    # Story 9.1 — Typed exceptions
    "CostPoolValidationError",
    "ActivityValidationError",
    "DriverValidationError",
    "AbcValidationNotFoundError",
    # Story 9.1 — Pure functions
    "validate_cost_pool",
    "validate_activity",
    "validate_driver",
    "compute_validation_hash",
    "validate_100_percent_guard",
    # Story 9.1 — Constants
    "ABC_VALIDATION_KRW_QUANTUM",
    "ALLOCATION_PCT_MIN",
    "ALLOCATION_PCT_MAX",
    "VALIDATION_100_PCT_TARGET",
    "VALIDATION_TOLERANCE_KRW",
    "VALIDATION_HASH_PREFIX",
    "VALIDATION_DEFAULT_INDUSTRY",
    # Story 9.2 — Frozen dataclasses (CCR + Allocation + Unused)
    "CCRResult",
    "ActivityMapping",
    "CostObjectRow",
    "AllocationResult",
    "UnusedCapacityRow",
    "AllocationState",
    # Story 9.2 — Typed exceptions
    "CcrComputeError",
    "AllocationBalanceError",
    # Story 9.2 — Pure functions
    "compute_ccr",
    "compute_ccr_hash",
    "produce_unused_capacity_row",
    "compute_allocation",
    "compute_allocation_hash",
    # Story 9.2 — Constants
    "CCR_KRW_QUANTUM",
    "ABC_PRECISION_KRW_TOLERANCE",
    "CCR_HASH_PREFIX",
]
