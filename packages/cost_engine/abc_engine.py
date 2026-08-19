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

Story 9.3 EXTENSION: 5 NEW pure functions + 5 frozen dataclasses
(V7Verdict + MultiDepartmentCcrResult + DispatchState + DepartmentAllocation +
UnusedCapacitySubRow) + 2 typed exceptions (EmptyDepartmentsError +
TooManyDepartmentsError) + 3 NEW constants (V7_BALANCE_TOLERANCE_KRW +
MAX_DEPARTMENT_COUNT=50 + ABC_HASH_PREFIX) — V7 balance verify + multi-
department CCR aggregation + dispatch orchestration (PRD §F9.3 + AD-19 dual-
route + A29 forward-lock).

Story 9.4 EXTENSION: 2 NEW pure functions (compute_report21_hash +
compute_report_pdf_hash) + 1 frozen dataclass (Report21Summary) + 1 typed
exception (Report21InconsistentStateError) + 1 NEW constant
(REPORT_PDF_HASH_PREFIX) — Report #21 (Cost Object Breakdown) hash
determinism + PDF byte-equality determinism (PRD §9 #21 + §7.3 + §V7 +
§V8 verbatim, A30 forward-lock SHARED PDF generator 결정 wire = Story 9.4
본 진입점 + Report #15 후속).

Story 11.6 EXTENSION: 1 NEW pure function (compute_report15_hash) + 2 frozen
dataclasses (ActivityCostRow + Report15Summary) + 1 typed exception
(Report15InconsistentStateError) + 1 NEW constant (REPORT15_HASH_PREFIX) —
Report #15 (활동원가 내역서 — 활동별 원가·동인 단가) hash determinism
(PRD §9 #15 verbatim + §7.1 ABC Step 0~3 + §9 공통 규격, A33 forward-lock
A19 cohesion 9 surface 진입 + A32 forward-lock A30 SHARED factory reuse
1st case + A31 forward-lock Report #15 wire schedule 결정 wire 진입).

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m9_abc/services/abc_validation_service.py`
  (Story 9.1 T2 service layer — validate_100_percent_guard orchestrator)
- `apps/api/modules/m9_abc/services/abc_allocation_service.py`
  (Story 9.2 T2 service layer — CCRPort.compute 호출자 ONLY, AD-21
  단일 소유 + compute_allocation + produce_unused_capacity_row)
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py`
  (Story 9.3 dispatch_abc_path — AD-19 dual-route 결정)
- `apps/api/modules/m5_reports/services/report21_service.py`
  (Story 9.4 T3 service layer — Report21Service.build_report21 ONLY,
  compute_report21_hash + compute_report_pdf_hash 호출자)

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

PRD §9 #21 + §7.3 (법인세법 시행규칙 제76조 2기준) — 원가대상별 원가 집계:
- 9-4 wire = `Report21Summary` (frozen dataclass, product_count +
  total_allocated_krw + total_unused_krw + hash) — `compute_report21_hash`
  가 cost_object_breakdown + unused_capacity_breakdown + period_key +
  v7_verdict envelope 일관성 검증.
- 9-4 wire = `compute_report_pdf_hash` — PDF bytes byte-equality
  (V8 determinism, REUSE 0 NEW handlers, CR 12-5 D-14).
- A30 SHARED PDF generator = `packages/services/m5_reports/pdf_generator.py`
  (Story 9.4 NEW SHARED factory, Discriminated union `report_id: Literal[
 15, 16, 17, 18, 19, 20, 21]`, Report #21 본 진입점 + Report #15 후속).

PRD §A9: 유휴(미사용)능력 원가의 별도 관리 — 전통·ABC 공통.
PRD §A6: 완전배부와 대차평형 (Zero-Leak 원칙) — V7 ABC 무결성.
PRD §V7: ABC 무결성 — Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가).

PRD §14.B Non-Goal #1 verbatim: "제조부문 ABC 미구현" (1차 MVP 회색 배지
placeholder).

V8 determinism: `compute_validation_hash` + `compute_ccr_hash` =
hashlib.sha256 결정론 digest — 동일 입력 → byte-identical hash
(Epic 4 baseline + 7-1/7-2/8-1/8-2/8-3 패턴). hash format =
`sha256:` + 64-char hexdigest (32 bytes).

A19 cohesion pattern 8 surface (9-2 EXTENSION 누적 + 11-6 forward-compat):
  1: `inventory_math.py` (Epic 5)
  2: `cvp.py` (7-1)
  3: `projection.py` (7-2)
  4: `budget_period_key.py` (8-1)
  5: `budget_variance.py` (8-2)
  6: `budget_pre_standard.py` (8-3)
  7: `abc_engine.py` (9-1 + 9-2 + 9-3 + 9-4 EXTENSION — A26 Option A 채택, NO
     cross-import with other A19 surfaces, 동일 surface 누적 wire).

Story 11.6 A19 cohesion 9 surface 진입 — A33 forward-lock 결정 wire:
  8: `pdf_generator.py` (A30 SHARED factory, packages/services/m5_reports/) —
     11-6 EXTENSION 시점에 `_compose_report15_pdf` 본체 wire + Report #15
     payload invariants.

AD-21 CCRPort.compute 단일 소유 — M9 service layer ONLY. 9-3 진입 시점에
A29 M3 dispatch ↔ M9 dispatch dual-route 결정 후 9-3 wire (forward-lock).

PRD §9 #15 verbatim — 활동원가 내역서 (활동별 원가·동인 단가):
- 11-6 wire = `ActivityCostRow` (frozen dataclass, 활동별 행 — activity_id +
  activity_name_ko + activity_name_en + total_cost_krw + total_cost_usd +
  driver_count + cost_per_driver_krw + cost_per_driver_usd + allocated_krw +
  allocated_usd + hash) — 활동별 원가·동인 단가 envelope.
- 11-6 wire = `Report15Summary` (frozen dataclass — activity_count +
  total_cost_krw + total_cost_usd + total_driver_count + hash) — Report #15
  KPI envelope (9-4 Report21Summary 패턴 미러).
- 11-6 wire = `compute_report15_hash` — activity_breakdown + period_key +
  v7_verdict envelope 일관성 검증 + V8 byte-identical determinism.
- 11-6 wire = `Report15InconsistentStateError` — `main.py` envelope REUSE
  0 NEW handlers, CR 12-5 D-14 verbatim (Report #21 동일 pattern).
- PRD §A6 verbatim "완전배부·대차평형 1원 단위" + §A9 verbatim "미사용능력
  별도 관리" + §V7 (ABC 무결성) + §V8 (byte-identical determinism) 모두
  Report #15 wire 진입 시점에 그대로 보존 (9-1 + 9-2 + 9-3 + 9-4 wire
  시점에 이미 wire).
- A30 SHARED factory = `packages/services/m5_reports/pdf_generator.py`
  (Story 9.4 NEW SHARED factory, Discriminated union `report_id: Literal[
  15, 16, 17, 18, 19, 20, 21]`, Report #21 본 진입점 + Report #15 1st
  reuse case — A32 forward-lock 결정 wire 진입).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, Literal

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


# ── Story 9.3 NEW constants (PRD §F9.3 + §A6 + §V7 + AD-19 dual-route) ────
# V7 balance tolerance (PRD §A6 verbatim "완전배부·대차평형 1원 단위").
# Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) — 1원 단위 검증.
# 9-2 ABC_PRECISION_KRW_TOLERANCE 와 동일 quantum (CR 12-1 reuse).
V7_BALANCE_TOLERANCE_KRW: Final[Decimal] = Decimal("0.01")

# Multi-department CCR aggregation limit (PRD §7.2 + §A29 forward-lock).
# `tenant.industry == 'service'` 시 compute_and_persist 가 1 ≤ N ≤
# MAX_DEPARTMENT_COUNT 개 부서를 일괄 compute (D-9-2-DEFER-2 해소).
MAX_DEPARTMENT_COUNT: Final[int] = 50

# Hash prefix for compute_abc_allocation_hash (V8 determinism trace).
# 9-1 VALIDATION_HASH_PREFIX + 9-2 CCR_HASH_PREFIX 와 동일 prefix 재사용.
ABC_HASH_PREFIX: Final[str] = "sha256:"


# ── Story 9.4 NEW constants (PRD §9 #21 + §V8 byte-equality) ────
# Hash prefix for compute_report_pdf_hash (Report #21 PDF byte-equality,
# V8 determinism trace). 9-1 VALIDATION_HASH_PREFIX + 9-2 CCR_HASH_PREFIX
# + 9-3 ABC_HASH_PREFIX 와 동일 prefix 재사용 — cross-language TS mirror
# parity (CR 11-3 cross-language fixture).
REPORT_PDF_HASH_PREFIX: Final[str] = "sha256:"


# ── Story 11.6 NEW constant (PRD §9 #15 + §V8 byte-identical determinism) ────
# Hash prefix for compute_report15_hash (Report #15 activity cost detail
# hash determinism, V8 trace). 9-1 VALIDATION_HASH_PREFIX + 9-2 CCR_HASH_PREFIX
# + 9-3 ABC_HASH_PREFIX + 9-4 REPORT_PDF_HASH_PREFIX 와 동일 prefix 재사용
# — cross-language TS mirror parity (CR 11-3 cross-language fixture).
REPORT15_HASH_PREFIX: Final[str] = "sha256:"


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
        CostPoolValidation | ActivityValidation | DriverValidation,
    ):
        raise ValueError(  # noqa: ERA001 — pre-existing in 9-1 wire
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


# ── Story 9.3 EXTENSION — frozen dataclasses (PRD §F9.3 + §A29 + §V7) ─────
@dataclass(frozen=True, slots=True)
class V7Verdict:
    """Frozen V7 ABC 무결성 verdict (PRD §F9.3 + §A6 + §V7 verbatim).

    `verify_v7_balance` 결과 — 1-Won precision invariant
    (Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가)) 만족 여부.

    `is_balanced` = (|breakdown_sum + unused_cost - department_cost| ≤
    V7_BALANCE_TOLERANCE_KRW) 일 때 True
    `breakdown_sum` = Decimal (Σ cost_object_breakdown.allocated_krw)
    `unused_cost` = Decimal (Σ unused_capacity.unused_cost_krw)
    `expected_sum` = Decimal (Σ department_cost)
    `delta_krw` = Decimal (절대 오차 = breakdown_sum + unused_cost - expected_sum)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    is_balanced: bool
    breakdown_sum: Decimal
    unused_cost: Decimal
    expected_sum: Decimal
    delta_krw: Decimal
    hash: str


@dataclass(frozen=True, slots=True)
class MultiDepartmentCcrResult:
    """Frozen multi-department CCR aggregation result (PRD §F9.3 + §7.2).

    `aggregate_multi_department_ccr` 결과 — N개 부서 CCR 일괄 compute.

    `department_count` = int (1 ≤ N ≤ MAX_DEPARTMENT_COUNT, validate_department_count)
    `total_ccr_sum` = Decimal (Σ CCRResult.ccr_per_hour × practical_capacity_hours)
    `per_dept_results` = tuple[CCRResult] (부서별 결과, 9-2 compute_ccr 재사용)
    `aggregate_hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    department_count: int
    total_ccr_sum: Decimal
    per_dept_results: tuple[CCRResult, ...]
    aggregate_hash: str


@dataclass(frozen=True, slots=True)
class DispatchState:
    """Frozen M3 dispatch 상태 (PRD §F9.3 + AD-19 dual-route).

    `dispatch_abc_path` 결과 — tenant.industry discriminator decision.

    `tenant_industry` = str (tenant.industry, 예: 'service' | 'manufacturing' | 'mixed')
    `resolved_engine_type` = Literal["trad", "abc"] (engine_type tag discriminator)
    `dispatch_reason` = str (human-readable Korean reason, CR 11-4 D-002)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    tenant_industry: str
    resolved_engine_type: Literal["trad", "abc"]
    dispatch_reason: str
    hash: str


@dataclass(frozen=True, slots=True)
class DepartmentAllocation:
    """Frozen 부서별 ABC allocation 집계 (PRD §F9.3 + §A6 + §V7).

    `compute_and_persist` 11-step pipeline 의 per-department step 결과.

    `department_id` = str (부서 식별자)
    `ccr` = CCRResult (9-2 compute_ccr 재사용)
    `allocation` = AllocationResult (9-2 compute_allocation 재사용)
    `v7_verdict` = V7Verdict (verify_v7_balance 결과)
    """

    department_id: str
    ccr: CCRResult
    allocation: AllocationResult
    v7_verdict: V7Verdict


@dataclass(frozen=True, slots=True)
class UnusedCapacitySubRow:
    """Frozen 부서별 미사용능력 sub-row (PRD §A9 + §F9.3 + §9 #18).

    `compute_and_persist` 11-step pipeline 의 per-department unused step.

    `department_id` = str (부서 식별자)
    `unused_hours` = Decimal (미사용 시간)
    `unused_cost_krw` = Decimal (KRW 정수, 미사용 원가, 1-Won precision)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    department_id: str
    unused_hours: Decimal
    unused_cost_krw: Decimal
    hash: str


# ── Story 9.3 EXTENSION — typed exceptions (CR 12-5 D-14 envelope main.py) ──
class EmptyDepartmentsError(ValueError):
    """PRD §F9.3 + AD-15 envelope — multi-department CCR aggregation 입력 부재.

    HTTP 422 EMPTY_DEPARTMENTS envelope (CR 12-5 D-14).
    `aggregate_multi_department_ccr` / `validate_department_count` 호출
    시점에 `department_ids` 빈 경우 raise.

    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.reason = reason


class TooManyDepartmentsError(ValueError):
    """PRD §F9.3 + AD-15 envelope — multi-department CCR aggregation 한도 초과.

    HTTP 422 TOO_MANY_DEPARTMENTS envelope (CR 12-5 D-14).
    `validate_department_count` 호출 시점에 `len(department_ids) >
    MAX_DEPARTMENT_COUNT` (50) 경우 raise.

    `department_count` is the actual count (machine code),
    `max_count` = MAX_DEPARTMENT_COUNT (constant),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        department_count: int,
        max_count: int,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.department_count = department_count
        self.max_count = max_count
        self.reason = reason


# ── Story 9.3 EXTENSION — pure functions (PRD §F9.3 + §A29 + §V7 + AD-19) ──
def _validate_department_count_inputs(
    *,
    department_ids: list[str],
) -> None:
    """Internal helper — department_ids 검증 (PRD §F9.3 + AD-8).

    Edge cases (각 typed exception raise):
      - empty department_ids → `EmptyDepartmentsError(reason="empty_departments")`
      - len(department_ids) > MAX_DEPARTMENT_COUNT → `TooManyDepartmentsError`
    """
    if not department_ids:
        raise EmptyDepartmentsError(
            "department_ids must be non-empty for multi-department CCR aggregation",
            reason="empty_departments",
        )
    if len(department_ids) > MAX_DEPARTMENT_COUNT:
        raise TooManyDepartmentsError(
            (
                f"department_count ({len(department_ids)}) exceeds "
                f"MAX_DEPARTMENT_COUNT ({MAX_DEPARTMENT_COUNT})"
            ),
            department_count=len(department_ids),
            max_count=MAX_DEPARTMENT_COUNT,
            reason="exceeds_max",
        )


def validate_department_count(
    *,
    department_ids: list[str],
    max_count: int = MAX_DEPARTMENT_COUNT,
) -> int:
    """PRD §F9.3 + §7.2 verbatim — multi-department CCR aggregation department count.

    Validates 1 ≤ len(department_ids) ≤ max_count (default `MAX_DEPARTMENT_COUNT=50`).

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-11).

    Args:
      department_ids: 부서 식별자 리스트 (tenant-relative UUID-as-string).
      max_count: 한도 (default `MAX_DEPARTMENT_COUNT=50`).

    Returns:
      int (len(department_ids), == max_count guard pass).

    Edge cases (typed exception raise):
      - empty department_ids → `EmptyDepartmentsError(reason="empty_departments")`
      - len > max_count → `TooManyDepartmentsError(...)`

    AD-5 stdlib-only, AD-8 Decimal-as-string, AD-11 layer rule.
    """
    if not department_ids:
        raise EmptyDepartmentsError(
            "department_ids must be non-empty for multi-department CCR aggregation",
            reason="empty_departments",
        )
    if len(department_ids) > max_count:
        raise TooManyDepartmentsError(
            (
                f"department_count ({len(department_ids)}) exceeds "
                f"max_count ({max_count})"
            ),
            department_count=len(department_ids),
            max_count=max_count,
            reason="exceeds_max",
        )
    return len(department_ids)


def aggregate_multi_department_ccr(
    *,
    ccr_results: list[CCRResult],
) -> MultiDepartmentCcrResult:
    """PRD §F9.3 + §7.2 verbatim — N개 부서 CCR 일괄 compute aggregation.

    공식:
      - `department_count = validate_department_count(department_ids)` (1 ≤ N ≤ 50)
      - `total_ccr_sum = Σ(ccr_results[i].ccr_per_hour × ccr.practical_capacity_hours)`
        (KRW 정수, 1-Won precision)
      - `per_dept_results = tuple(ccr_results)`

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Args:
      ccr_results: 부서별 CCRResult 리스트 (9-2 compute_ccr 재사용).

    Returns:
      MultiDepartmentCcrResult(department_count, total_ccr_sum,
                                per_dept_results, aggregate_hash).

    Edge cases:
      - empty ccr_results → `EmptyDepartmentsError(reason="empty_departments")`
      - len > MAX_DEPARTMENT_COUNT → `TooManyDepartmentsError(...)`

    V8 determinism: 동일 ccr_results → byte-identical aggregate_hash.

    D-9-2-DEFER-2 (multi-department CCR) 해소.
    """
    department_ids = [ccr.department_id for ccr in ccr_results]
    _validate_department_count_inputs(department_ids=department_ids)

    total_ccr_sum = sum(
        (ccr.ccr_per_hour * ccr.practical_capacity_hours for ccr in ccr_results),
        Decimal("0"),
    ).quantize(CCR_KRW_QUANTUM, rounding=ROUND_HALF_EVEN)

    # Compute placeholder for hash (V8 determinism pre-compute).
    result = MultiDepartmentCcrResult(
        department_count=len(ccr_results),
        total_ccr_sum=total_ccr_sum,
        per_dept_results=tuple(ccr_results),
        aggregate_hash="",  # placeholder
    )
    digest = hashlib.sha256(repr(result).encode()).hexdigest()
    return MultiDepartmentCcrResult(
        department_count=len(ccr_results),
        total_ccr_sum=total_ccr_sum,
        per_dept_results=tuple(ccr_results),
        aggregate_hash=f"{ABC_HASH_PREFIX}{digest}",
    )


def verify_v7_balance(
    *,
    total_breakdown_sum: Decimal,
    unused_cost: Decimal,
    department_cost: Decimal,
    tolerance: Decimal = V7_BALANCE_TOLERANCE_KRW,
) -> V7Verdict:
    """PRD §F9.3 + §A6 + §V7 verbatim — V7 ABC 무결성 1-Won precision 검증.

    공식:
      - `delta_krw = breakdown_sum + unused_cost - department_cost`
      - `is_balanced = |delta_krw| ≤ tolerance`

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Args:
      total_breakdown_sum: Σ cost_object_breakdown.allocated_krw
                            (KRW 정수, 1-Won precision).
      unused_cost: Σ unused_capacity.unused_cost_krw
                    (KRW 정수, 1-Won precision).
      department_cost: Σ 부서 원가 (KRW 정수, 1-Won precision).
      tolerance: V7_BALANCE_TOLERANCE_KRW (default `Decimal("0.01")`).

    Returns:
      V7Verdict(is_balanced, breakdown_sum, unused_cost, expected_sum,
                delta_krw, hash).

    Edge cases:
      - `is_balanced=False` → frontend disabled signal (compute_and_persist
        11-step pipeline 에서 AllocationBalanceError raise 후 main.py envelope
        REUSE 0 NEW handlers, CR 12-5 D-14 verbatim).

    V8 determinism: 동일 3 inputs → byte-identical verdict hash.

    D-9-2-DEFER-3 (Cost Object Breakdown backend persistence) 검증.
    """
    delta_krw = total_breakdown_sum + unused_cost - department_cost
    is_balanced = abs(delta_krw) <= tolerance

    verdict = V7Verdict(
        is_balanced=is_balanced,
        breakdown_sum=total_breakdown_sum,
        unused_cost=unused_cost,
        expected_sum=department_cost,
        delta_krw=delta_krw,
        hash="",  # placeholder
    )
    digest = hashlib.sha256(repr(verdict).encode()).hexdigest()
    return V7Verdict(
        is_balanced=is_balanced,
        breakdown_sum=total_breakdown_sum,
        unused_cost=unused_cost,
        expected_sum=department_cost,
        delta_krw=delta_krw,
        hash=f"{ABC_HASH_PREFIX}{digest}",
    )


def dispatch_abc_path(
    *,
    tenant_industry: str,
    requested_engine_type: str | None = None,  # noqa: ARG001 — 9-3 forward-compat param, 9-4 surface preserves signature
) -> DispatchState:
    """PRD §F9.3 + AD-19 dual-route — M3 dispatch EXTENSION.

    공식 (AD-19 dual-route 결정):
      - `tenant_industry == 'service'` → `resolved_engine_type = "abc"`
        (M9 dispatch, AD-21 단일 소유)
      - else (`'manufacturing'`, `'mixed'`, ...) →
        `resolved_engine_type = "trad"` (기존 trad path, AD-18 backward compat)

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-11).

    Args:
      tenant_industry: tenant.industry 문자열 (예: 'service', 'manufacturing').
      requested_engine_type: requested engine_type (optional, currently unused
                              for 9-3 wire but reserved for A30 forward-lock).

    Returns:
      DispatchState(tenant_industry, resolved_engine_type, dispatch_reason,
                    hash).

    Edge cases:
      - Empty tenant_industry → resolved_engine_type="trad" (fallback).

    V8 determinism: 동일 tenant_industry → byte-identical dispatch hash.

    A29 forward-lock dual-route wire 결정 (9-2 handoff).
    """
    if tenant_industry == "service":
        resolved_engine_type: Literal["trad", "abc"] = "abc"
        dispatch_reason = "서비스 업종 → M9 ABC dispatch (AD-19)"
    else:
        resolved_engine_type = "trad"
        dispatch_reason = (
            f"비서비스 업종 ({tenant_industry or 'unknown'}) → "
            "기존 trad path (AD-18 backward compat)"
        )

    state = DispatchState(
        tenant_industry=tenant_industry,
        resolved_engine_type=resolved_engine_type,
        dispatch_reason=dispatch_reason,
        hash="",  # placeholder
    )
    digest = hashlib.sha256(repr(state).encode()).hexdigest()
    return DispatchState(
        tenant_industry=tenant_industry,
        resolved_engine_type=resolved_engine_type,
        dispatch_reason=dispatch_reason,
        hash=f"{ABC_HASH_PREFIX}{digest}",
    )


def compute_abc_allocation_hash(
    *,
    multi_dept_ccr: MultiDepartmentCcrResult,
    per_dept_allocations: list[DepartmentAllocation],
    unused_capacity_breakdown: list[UnusedCapacitySubRow],
) -> str:
    """V8 determinism hash for 9-3 ABC allocation aggregate state.

    `hashlib.sha256(repr(aggregate).encode()).hexdigest()` —
    32 bytes hexdigest (64 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Args:
      multi_dept_ccr: MultiDepartmentCcrResult (aggregate_multi_department_ccr).
      per_dept_allocations: 부서별 DepartmentAllocation 리스트.
      unused_capacity_breakdown: 부서별 UnusedCapacitySubRow 리스트.

    Returns:
      `f"sha256:{64-char-hexdigest}"`.

    Note: 9-3 wire envelope = `{(multi_dept_ccr, per_dept_allocations,
    unused_capacity_breakdown)}` aggregated hash (compute_and_persist
    11-step pipeline 결과).

    Type-safe: each input MUST be the expected type (MultiDepartmentCcrResult
    / tuple[DepartmentAllocation] / tuple[UnusedCapacitySubRow]).
    """
    if not isinstance(multi_dept_ccr, MultiDepartmentCcrResult):
        raise ValueError(
            f"multi_dept_ccr must be MultiDepartmentCcrResult, "
            f"got {type(multi_dept_ccr).__name__}"
        )
    if not all(
        isinstance(alloc, DepartmentAllocation)
        for alloc in per_dept_allocations
    ):
        raise ValueError(
            "per_dept_allocations must be list[DepartmentAllocation]"
        )
    if not all(
        isinstance(row, UnusedCapacitySubRow)
        for row in unused_capacity_breakdown
    ):
        raise ValueError(
            "unused_capacity_breakdown must be list[UnusedCapacitySubRow]"
        )

    aggregate = (
        multi_dept_ccr,
        tuple(per_dept_allocations),
        tuple(unused_capacity_breakdown),
    )
    digest = hashlib.sha256(repr(aggregate).encode()).hexdigest()
    return f"{ABC_HASH_PREFIX}{digest}"


# ── Story 9.4 EXTENSION — frozen dataclass (PRD §9 #21 + §7.3 + §V7) ─────
@dataclass(frozen=True, slots=True)
class Report21Summary:
    """Frozen Report #21 (Cost Object Breakdown) 요약 (PRD §9 #21 + §7.3 + §V7).

    `compute_report21_hash` 결과 — 원가대상별 원가 집계 KPI envelope.
    서비스 layer 가 build_report21 후 assemble.

    `product_count` = int (1 ≤ N, 원가대상 distinct count)
    `total_allocated_krw` = Decimal (Σ cost_object_breakdown.allocated_krw,
                                     KRW 정수, 1-Won precision)
    `total_unused_krw` = Decimal (Σ unused_capacity_breakdown.unused_cost_krw,
                                  KRW 정수, 1-Won precision)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    product_count: int
    total_allocated_krw: Decimal
    total_unused_krw: Decimal
    hash: str


# ── Story 9.4 EXTENSION — typed exception (CR 12-5 D-14 envelope main.py) ──
class Report21InconsistentStateError(ValueError):
    """PRD §V7 envelope — Report #21 Cost Object Breakdown inconsistency.

    HTTP 422 REPORT21_INCONSISTENT_STATE envelope (CR 12-5 D-14).
    `compute_report21_hash` 입력 검증 시 Σ(원가대상별 배부액) +
    미사용능력 ≠ Σ(부서 원가) — V7 ABC 무결성 깨짐 (period 미커밋 또는
    breakdown 부재) 시 raise.

    9-4 wire = `Report21Service.build_report21` 가 V7 verdict 기반으로
    computation 후 raise 가능 — `main.py` envelope REUSE 0 NEW handlers.

    `period_key` identifies which period failed (machine code),
    `expected_sum` is the expected Σ department cost (Decimal-as-string),
    `actual_sum` is the actual breakdown + unused sum (Decimal-as-string),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        expected_sum: Decimal,
        actual_sum: Decimal,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.expected_sum = expected_sum
        self.actual_sum = actual_sum
        self.reason = reason


# ── Story 9.4 EXTENSION — pure functions (PRD §9 #21 + §7.3 + §V8) ──────
def compute_report21_hash(
    *,
    cost_object_breakdown: list[CostObjectRow],
    unused_capacity_breakdown: list[UnusedCapacitySubRow],
    period_key: str,
    v7_verdict: V7Verdict,
) -> str:
    """V8 determinism hash for Report #21 (Cost Object Breakdown, PRD §9 #21).

    `hashlib.sha256(repr(aggregate).encode()).hexdigest()` —
    32 bytes hexdigest (64 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Args:
      cost_object_breakdown: 9-3 `compute_and_persist` 결과의
                                (Σ cost_object_breakdown.allocated_krw) 리스트.
      unused_capacity_breakdown: 9-3 `compute_and_persist` 결과의
                                 (Σ unused_capacity_breakdown.unused_cost_krw)
                                 리스트.
      period_key: 회계 기간 키 (예: "2026-Q1", "2026-08").
      v7_verdict: 9-3 `verify_v7_balance` 결과 (V7 ABC 무결성 verdict).

    Returns:
      `f"sha256:{64-char-hexdigest}"`.

    Edge cases (typed exception raise):
      - empty breakdown + empty unused → `Report21InconsistentStateError(
        reason="no_breakdown")` (period 미커밋 or breakdown 부재).
      - `len(period_key) == 0` → `Report21InconsistentStateError(
        reason="empty_period_key")`.

    V8 determinism: 동일 4 inputs → byte-identical hash.
    """
    if not isinstance(cost_object_breakdown, list):
        raise ValueError(
            f"cost_object_breakdown must be list[CostObjectRow], "
            f"got {type(cost_object_breakdown).__name__}"
        )
    if not all(
        isinstance(row, CostObjectRow) for row in cost_object_breakdown
    ):
        raise ValueError(
            "cost_object_breakdown items must be CostObjectRow"
        )
    if not isinstance(unused_capacity_breakdown, list):
        raise ValueError(
            f"unused_capacity_breakdown must be list[UnusedCapacitySubRow], "
            f"got {type(unused_capacity_breakdown).__name__}"
        )
    if not all(
        isinstance(row, UnusedCapacitySubRow)
        for row in unused_capacity_breakdown
    ):
        raise ValueError(
            "unused_capacity_breakdown items must be UnusedCapacitySubRow"
        )
    if not isinstance(v7_verdict, V7Verdict):
        raise ValueError(
            f"v7_verdict must be V7Verdict, "
            f"got {type(v7_verdict).__name__}"
        )
    if not period_key:
        raise Report21InconsistentStateError(
            "period_key must be non-empty for Report #21 build_report21",
            period_key=period_key or "",
            expected_sum=v7_verdict.expected_sum,
            actual_sum=v7_verdict.breakdown_sum + v7_verdict.unused_cost,
            reason="empty_period_key",
        )
    if (
        not cost_object_breakdown
        and not unused_capacity_breakdown
    ):
        raise Report21InconsistentStateError(
            "Report #21 requires cost_object_breakdown or unused_capacity_breakdown",
            period_key=period_key,
            expected_sum=v7_verdict.expected_sum,
            actual_sum=v7_verdict.breakdown_sum + v7_verdict.unused_cost,
            reason="no_breakdown",
        )

    # Aggregate envelope = (cost_object_breakdown, unused_capacity_breakdown,
    # period_key, v7_verdict). Frozen dataclass + tuple 순서 보존.
    aggregate = (
        tuple(cost_object_breakdown),
        tuple(unused_capacity_breakdown),
        period_key,
        v7_verdict,
    )
    digest = hashlib.sha256(repr(aggregate).encode()).hexdigest()
    return f"{ABC_HASH_PREFIX}{digest}"


def compute_report_pdf_hash(*, pdf_bytes: bytes) -> str:
    """V8 byte-equality hash for Report PDF bytes (PRD §9 #21 + §V8).

    `hashlib.sha256(pdf_bytes).hexdigest()` — PDF bytes byte-equality
    (Report #21 + Report #15 A30 SHARED PDF generator 동일 surface 재사용).

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Args:
      pdf_bytes: reportlab 생성 PDF raw bytes (Report #21 or Report #15).

    Returns:
      `f"sha256:{64-char-hexdigest}"` (PDF byte-equality invariant).

    Edge cases:
      - pdf_bytes not bytes → raise ValueError.
      - empty bytes → 정상 (empty PDF hash, 64-char hexdigest).

    V8 determinism: 동일 pdf_bytes → byte-identical hash.
    """
    if not isinstance(pdf_bytes, bytes):
        raise ValueError(
            f"pdf_bytes must be bytes, "
            f"got {type(pdf_bytes).__name__}"
        )
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    return f"{REPORT_PDF_HASH_PREFIX}{digest}"


# ── Story 11.6 EXTENSION — frozen dataclasses (PRD §9 #15 + §7.1 + §V7 + §A6 + §A9) ─────
@dataclass(frozen=True, slots=True)
class ActivityCostRow:
    """Frozen Report #15 활동별 원가·동인 단가 행 (PRD §9 #15 verbatim).

    활동원가 내역서 — 활동별 행 envelope. KRW + USD 두 통화 모두 지원
    (PRD §9 공통 규격 "KRW·USD 동시 표시"). 동인 단가는 KRW 정수 1-Won precision
    (AD-8 Decimal-as-string).

    `activity_id` = str (활동 식별자 — tenant-relative UUID-as-string)
    `activity_name_ko` = str (활동명 한글, ko-KR.json SSOT, CR 11-4 D-002)
    `activity_name_en` = str (활동명 영문, en-US.json SSOT)
    `total_cost_krw` = Decimal (KRW 정수, 활동별 총 원가, 1-Won precision)
    `total_cost_usd` = Decimal (USD, 환율 적용 AD-23 settings aggregate)
    `driver_count` = int (동인 개수, ≥ 1)
    `cost_per_driver_krw` = Decimal (KRW 정수, 동인당 원가 = total_cost_krw /
                                     driver_count, 1-Won precision)
    `cost_per_driver_usd` = Decimal (USD, 동인당 원가)
    `allocated_krw` = Decimal (KRW 정수, 배부 완료된 원가 = total_cost_krw 와 동일)
    `allocated_usd` = Decimal (USD, 배부 완료된 원가)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)

    AD-23 settings aggregate (KRW/USD 환율) 그대로 보존 — service layer 가
    tenant_settings.currency.exchange_rate_krw_per_usd 적용 후 envelope.
    """

    activity_id: str
    activity_name_ko: str
    activity_name_en: str
    total_cost_krw: Decimal
    total_cost_usd: Decimal
    driver_count: int
    cost_per_driver_krw: Decimal
    cost_per_driver_usd: Decimal
    allocated_krw: Decimal
    allocated_usd: Decimal
    hash: str


@dataclass(frozen=True, slots=True)
class Report15Summary:
    """Frozen Report #15 (활동원가 내역서) 요약 (PRD §9 #15 + §7.1 + §V7).

    `compute_report15_hash` 결과 — 활동별 원가·동인 단가 KPI envelope
    (9-4 Report21Summary 패턴 미러).

    `activity_count` = int (1 ≤ N, 활동 distinct count)
    `total_cost_krw` = Decimal (Σ ActivityCostRow.total_cost_krw,
                                 KRW 정수, 1-Won precision)
    `total_cost_usd` = Decimal (Σ ActivityCostRow.total_cost_usd, USD)
    `total_driver_count` = int (Σ ActivityCostRow.driver_count, ≥ activity_count)
    `hash` = "sha256:" + 64-char hexdigest (V8 byte-identical)
    """

    activity_count: int
    total_cost_krw: Decimal
    total_cost_usd: Decimal
    total_driver_count: int
    hash: str


# ── Story 11.6 EXTENSION — typed exception (CR 12-5 D-14 envelope main.py) ──
class Report15InconsistentStateError(ValueError):
    """PRD §V7 envelope — Report #15 활동원가 내역서 inconsistency.

    HTTP 422 REPORT15_INCONSISTENT_STATE envelope (CR 12-5 D-14).
    `compute_report15_hash` 입력 검증 시 Σ(활동별 원가) ≠ Σ(부서 원가) —
    V7 ABC 무결성 깨짐 (period 미커밋 또는 activity_breakdown 부재) 시 raise.

    11-6 wire = `Report15Service.build_report15` 가 V7 verdict 기반으로
    computation 후 raise 가능 — `main.py` envelope REUSE 0 NEW handlers
    (9-4 wire `Report21InconsistentStateError` 패턴 미러, CR 12-5 D-14 verbatim).

    `period_key` identifies which period failed (machine code),
    `expected_sum` is the expected Σ department cost (Decimal-as-string),
    `actual_sum` is the actual activity breakdown sum (Decimal-as-string),
    `reason` is the human-readable Korean reason.
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        expected_sum: Decimal,
        actual_sum: Decimal,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.expected_sum = expected_sum
        self.actual_sum = actual_sum
        self.reason = reason


# ── Story 11.6 EXTENSION — pure function (PRD §9 #15 + §7.1 + §V8) ──────
def compute_report15_hash(
    *,
    activity_breakdown: list[ActivityCostRow],
    period_key: str,
    v7_verdict: V7Verdict,
) -> str:
    """V8 determinism hash for Report #15 (활동원가 내역서, PRD §9 #15 verbatim).

    `hashlib.sha256(repr(aggregate).encode()).hexdigest()` —
    32 bytes hexdigest (64 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Args:
      activity_breakdown: 활동별 원가·동인 단가 행 리스트
                          (ActivityCostRow, build_report15 결과).
      period_key: 회계 기간 키 (예: "2026-Q1", "2026-08").
      v7_verdict: 9-3 `verify_v7_balance` 결과 (V7 ABC 무결성 verdict).

    Returns:
      `f"sha256:{64-char-hexdigest}"`.

    Edge cases (typed exception raise):
      - empty activity_breakdown → `Report15InconsistentStateError(
        reason="no_activity_breakdown")` (period 미커밋 or activity 부재).
      - `len(period_key) == 0` → `Report15InconsistentStateError(
        reason="empty_period_key")`.
      - activity_breakdown items not ActivityCostRow → raise ValueError.
      - v7_verdict not V7Verdict → raise ValueError.

    V8 determinism: 동일 3 inputs → byte-identical hash.

    A32 forward-lock (A30 SHARED factory reuse 1st case) 진입점 결정 wire.
    A33 forward-lock (A19 cohesion 9 surface) 진입점 결정 wire.
    A31 forward-lock (Report #15 wire schedule) 진입점 결정 wire.

    Note: Report #21 `compute_report21_hash` 와 동일 surface pattern 미러
    (cost_object_breakdown + unused_capacity_breakdown + period_key + v7_verdict).
    Report #15 는 activity_breakdown 단일 입력 (unused_capacity 별도 표기
    없음 — Report #15 = 활동별 원가·동인 단가 KPI focus, unused = Report #21
    에서만 별도 행 표시 PRD §A9 verbatim).
    """
    if not isinstance(activity_breakdown, list):
        raise ValueError(
            f"activity_breakdown must be list[ActivityCostRow], "
            f"got {type(activity_breakdown).__name__}"
        )
    if not all(
        isinstance(row, ActivityCostRow) for row in activity_breakdown
    ):
        raise ValueError(
            "activity_breakdown items must be ActivityCostRow"
        )
    if not isinstance(v7_verdict, V7Verdict):
        raise ValueError(
            f"v7_verdict must be V7Verdict, "
            f"got {type(v7_verdict).__name__}"
        )
    if not period_key:
        raise Report15InconsistentStateError(
            "period_key must be non-empty for Report #15 build_report15",
            period_key=period_key or "",
            expected_sum=v7_verdict.expected_sum,
            actual_sum=v7_verdict.breakdown_sum + v7_verdict.unused_cost,
            reason="empty_period_key",
        )
    if not activity_breakdown:
        raise Report15InconsistentStateError(
            "Report #15 requires activity_breakdown",
            period_key=period_key,
            expected_sum=v7_verdict.expected_sum,
            actual_sum=v7_verdict.breakdown_sum + v7_verdict.unused_cost,
            reason="no_activity_breakdown",
        )

    # Aggregate envelope = (activity_breakdown, period_key, v7_verdict).
    # Frozen dataclass + tuple 순서 보존.
    aggregate = (
        tuple(activity_breakdown),
        period_key,
        v7_verdict,
    )
    digest = hashlib.sha256(repr(aggregate).encode()).hexdigest()
    return f"{REPORT15_HASH_PREFIX}{digest}"


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
    # Story 9.3 — Frozen dataclasses (V7 verify + multi-dept CCR + dispatch)
    "V7Verdict",
    "MultiDepartmentCcrResult",
    "DispatchState",
    "DepartmentAllocation",
    "UnusedCapacitySubRow",
    # Story 9.3 — Typed exceptions
    "EmptyDepartmentsError",
    "TooManyDepartmentsError",
    # Story 9.3 — Pure functions
    "verify_v7_balance",
    "aggregate_multi_department_ccr",
    "dispatch_abc_path",
    "validate_department_count",
    "compute_abc_allocation_hash",
    # Story 9.3 — Constants
    "V7_BALANCE_TOLERANCE_KRW",
    "MAX_DEPARTMENT_COUNT",
    "ABC_HASH_PREFIX",
    # Story 9.4 — Frozen dataclass (Report #21 summary)
    "Report21Summary",
    # Story 9.4 — Typed exception
    "Report21InconsistentStateError",
    # Story 9.4 — Pure functions
    "compute_report21_hash",
    "compute_report_pdf_hash",
    # Story 9.4 — Constants
    "REPORT_PDF_HASH_PREFIX",
    # Story 11.6 — Frozen dataclasses (Report #15 activity cost detail)
    "ActivityCostRow",
    "Report15Summary",
    # Story 11.6 — Typed exception
    "Report15InconsistentStateError",
    # Story 11.6 — Pure function
    "compute_report15_hash",
    # Story 11.6 — Constant
    "REPORT15_HASH_PREFIX",
]
