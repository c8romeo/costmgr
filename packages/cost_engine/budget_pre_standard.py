"""packages.cost_engine.budget_pre_standard — Story 8.3 Budget Pre-Standard Cost pure kernel.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m8_budget/services/budget_pre_standard_service.py`
  (T3 service layer — compute_pre_standard_snapshot / fetch_pre_standard_snapshot /
  generate_budget_pre_standard_pdf dispatch)

AD-1 / AD-5 / AD-8 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes input values
fetched from DB; this kernel owns the pre-standard cost math + V8 determinism
+ period_key validation.

PRD §F8.3 (예산 시점의 단가 기준 미리 잠금):
- `material_cost = material_unit_cost * material_qty` (KRW 정수, ROUND_HALF_EVEN)
- `labor_cost = labor_unit_cost * labor_hours` (KRW 정수)
- `overhead_cost = labor_cost * overhead_rate / 100` (KRW 정수, overhead_rate는 %)
- `manufacturing_cost = material_cost + labor_cost + overhead_cost` (합계)
- `fiscal_period_snapshots.engine_type` = `'budget'`, status lifecycle follows AD-22 (engine writes draft, M11 close transitions to verified/committed).

PRD §10 M8 verbatim:
- 1차 시나리오 1개 only (8-1 lock) — `scenario_index = 1` hard-coded
- A×B×C×D 회색 배지 placeholder (8-2 wire — 본 모듈은 무관)

PRD §15 NON-GOAL #1·2 verbatim:
- A×B×C×D 엔진 1차 비구현 (8-2 회색 배지 명시)
- 복수 시나리오 1차 = 1개 (≥5 테넌트 요청 시 trigger)

AD-24 Period Keys (`docs/conventions.md#§6-Period-Keys-(AD-24)`):
- Virtual budget period key `YYYY-MM#B<n>` (8-1 wire) — pre-standard cost preview
  의 period_key 검증은 8-1 `parse_virtual_budget_period_key` reuse.

V8 determinism: `compute_pre_standard_hash` 는 hashlib.sha256 결정론 digest
— 동일 입력 → byte-identical hash (Epic 4 baseline + 7-1/7-2/8-1/8-2 패턴).

A19 cohesion pattern 5번째 검증: `budget_pre_standard.py` 는
`packages/cost_engine/cvp.py` (7-1) + `packages/cost_engine/projection.py`
(7-2) + `packages/cost_engine/budget_period_key.py` (8-1) +
`packages/cost_engine/budget_variance.py` (8-2) 와 surface 분리 — concern
별도 (pre-standard cost compute + V8 determinism 은 budget concern).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, Literal

# ── Constants ────────────────────────────────────────────────
# Decimal precision for monetary values (PRD §F8.3 + AD-8).
# KRW integer = 0 decimal places (1원 precision, AD-8 BigInteger parity).
PRE_STANDARD_KRW_QUANTUM: Final[Decimal] = Decimal("1")

# Overhead rate bounds (PRD §F8.3 + UX safety guard).
OVERHEAD_RATE_MIN_PCT: Final[Decimal] = Decimal("0")
OVERHEAD_RATE_MAX_PCT: Final[Decimal] = Decimal("100")

# Engine type for fiscal_period_snapshots.engine_type column.
# AD-22 ledger append-only — pre-standard cost preview는 engine_type='budget'로 구분.
PRE_STANDARD_ENGINE_TYPE: Final[str] = "budget"

# 1차 MVP scenario 한도 (PRD §F8.1 verbatim + §15 NON-GOAL #2).
# 8-1 wire: scenario_index=1 only.
PRE_STANDARD_DEFAULT_SCENARIO_INDEX: Final[int] = 1

# Hash prefix for compute_pre_standard_hash (V8 determinism trace).
PRE_STANDARD_HASH_PREFIX: Final[str] = "sha256:"

# State value for fiscal_period_snapshots.state column.
# AD-22 + Epic 11 11-3 reverse 가드 동일 적용 — M11 close에서 'committed'로 전이.
PRE_STANDARD_STATE_VERIFIED: Final[str] = "verified"

# Default baseline_revision (4-2 wire — 첫 preview는 baseline_revision=1).
PRE_STANDARD_DEFAULT_BASELINE_REVISION: Final[int] = 1

# Engine type literal — 8-3 wire 시점 유일.
EngineType = Literal["budget"]


# ── Frozen dataclasses ───────────────────────────────────────
@dataclass(frozen=True, slots=True)
class PreStandardCost:
    """Frozen budget pre-standard cost entity (PRD §F8.3 + AD-8 monetary).

    `material_cost` = Decimal (KRW integer, ROUND_HALF_EVEN)
        = `material_unit_cost * material_qty`
    `labor_cost` = Decimal (KRW integer)
        = `labor_unit_cost * labor_hours`
    `overhead_cost` = Decimal (KRW integer)
        = `labor_cost * overhead_rate / 100`
    `manufacturing_cost` = Decimal (KRW integer)
        = `material_cost + labor_cost + overhead_cost`
    `period_key` = AD-24 virtual `YYYY-MM#B<n>` (8-1 wire)
    `scenario_index` = int (1차 MVP = 1)
    `engine_type` = Literal["budget"] (8-3 wire 시점 유일)
    """

    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    manufacturing_cost: Decimal
    period_key: str
    scenario_index: int
    engine_type: EngineType


# ── Typed exceptions ────────────────────────────────────────
class InvalidPreStandardInputError(ValueError):
    """PRD §F8.3 + AD-24 + AD-8 input validation.

    AD-24 period_key 검증 delegate (8-1 `parse_virtual_budget_period_key` reuse) +
    AD-8 monetary bounds 검증 (material_unit_cost, labor_unit_cost, overhead_rate,
    material_qty, labor_hours 모두 >= 0 + overhead_rate <= 100) + scenario_index
    한도 검증 (1차 MVP = 1).

    HTTP 422 INVALID_PRE_STANDARD_INPUT envelope (CR 12-5 D-14).

    Attributes:
      field — 잘못된 field 이름 (`period_key` / `material_unit_cost` / ...)
      reason — 상세 사유
    """

    def __init__(
        self,
        message: str,
        *,
        field: str,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.reason = reason


# ── Pure functions ───────────────────────────────────────────
def _validate_period_key(period_key: str) -> None:
    """AD-24 period_key 검증 — 8-1 `parse_virtual_budget_period_key` reuse.

    `period_key` = `YYYY-MM#B<n>` (virtual pattern) 만 허용. Real fiscal
    key (`2026-07`) 또는 malformed string → `InvalidPreStandardInputError`
    raise.

    Pure kernel delegation (AD-5 + AD-11).
    """
    # Imported lazily to avoid circular import at module load (8-1 / 8-3
    # both import each other's frozen dataclasses for boundary conversion).
    from packages.cost_engine.budget_period_key import (
        InvalidVirtualBudgetPeriodKeyError,
        parse_virtual_budget_period_key,
    )

    try:
        parse_virtual_budget_period_key(period_key=period_key)
    except InvalidVirtualBudgetPeriodKeyError as exc:
        # Translate to 8-3 typed envelope (CR 12-5 D-14).
        raise InvalidPreStandardInputError(
            (
                f"period_key must match YYYY-MM#B<n> for pre-standard cost "
                f"preview: got {period_key!r}"
            ),
            field="period_key",
            reason=exc.message,
        ) from exc


def _validate_decimal_non_negative(*, value: Decimal, field: str) -> None:
    """AD-8 monetary bounds 검증 — value >= 0."""
    if not isinstance(value, Decimal):
        raise InvalidPreStandardInputError(
            f"{field} must be Decimal, got {type(value).__name__}",
            field=field,
            reason="type_mismatch",
        )
    if value < 0:
        raise InvalidPreStandardInputError(
            f"{field} must be non-negative",
            field=field,
            reason="negative_value",
        )


def _validate_overhead_rate(*, overhead_rate: Decimal) -> None:
    """PRD §F8.3 + UX safety guard — overhead_rate 0 <= value <= 100."""
    if not isinstance(overhead_rate, Decimal):
        raise InvalidPreStandardInputError(
            f"overhead_rate must be Decimal, got {type(overhead_rate).__name__}",
            field="overhead_rate",
            reason="type_mismatch",
        )
    if overhead_rate < OVERHEAD_RATE_MIN_PCT:
        raise InvalidPreStandardInputError(
            "overhead_rate must be non-negative",
            field="overhead_rate",
            reason="negative_value",
        )
    if overhead_rate > OVERHEAD_RATE_MAX_PCT:
        raise InvalidPreStandardInputError(
            "overhead_rate must be <= 100",
            field="overhead_rate",
            reason="exceeds_max",
        )


def _validate_scenario_index(*, scenario_index: int) -> None:
    """PRD §F8.1 verbatim + §15 NON-GOAL #2 scenario lock.

    1차 MVP = scenario_index=1 only. 2차 multi-scenario는 honestly DEFER.
    """
    if not isinstance(scenario_index, int):
        raise InvalidPreStandardInputError(
            (f"scenario_index must be int, " f"got {type(scenario_index).__name__}"),
            field="scenario_index",
            reason="type_mismatch",
        )
    if scenario_index != PRE_STANDARD_DEFAULT_SCENARIO_INDEX:
        raise InvalidPreStandardInputError(
            "MVP supports scenario_index=1 only; 2차 예정",
            field="scenario_index",
            reason="mvp_limit",
        )


def compute_pre_standard_cost(
    *,
    material_unit_cost: Decimal,
    labor_unit_cost: Decimal,
    overhead_rate: Decimal,
    material_qty: Decimal,
    labor_hours: Decimal,
    period_key: str = "2026-07#B1",
    scenario_index: int = 1,
) -> PreStandardCost:
    """PRD §F8.3 verbatim pre-standard cost compute.

    공식 (PRD §F8.3 verbatim + AD-8 ROUND_HALF_EVEN):
      - `material_cost = round_half_even(material_unit_cost * material_qty, 0)`
        (KRW 정수)
      - `labor_cost = round_half_even(labor_unit_cost * labor_hours, 0)`
        (KRW 정수)
      - `overhead_cost = round_half_even(labor_cost * overhead_rate / 100, 0)`
        (KRW 정수, overhead_rate는 % 단위)
      - `manufacturing_cost = material_cost + labor_cost + overhead_cost`
        (KRW 정수 합산)

    Pure-Python, stdlib-only, deterministic (AD-5 + AD-8 + AD-11).

    Edge cases (InvalidPreStandardInputError raise):
      - `material_unit_cost < 0` → "material_unit_cost must be non-negative"
      - `labor_unit_cost < 0` → "labor_unit_cost must be non-negative"
      - `overhead_rate < 0` → "overhead_rate must be non-negative"
      - `overhead_rate > 100` → "overhead_rate must be <= 100"
      - `material_qty < 0` → "material_qty must be non-negative"
      - `labor_hours < 0` → "labor_hours must be non-negative"
      - `period_key` invalid virtual pattern → "period_key must match YYYY-MM#B<n>"
      - `scenario_index != 1` → "MVP supports scenario_index=1 only; 2차 예정"

    Edge cases (zero / boundary):
      - `material_qty == 0 AND labor_hours == 0` → `manufacturing_cost = 0`
        (모두 0)
      - `overhead_rate == 0` → `overhead_cost = 0` (overhead 미적용)
      - `overhead_rate == 100` → `overhead_cost = labor_cost`
        (overhead 100%, edge case)

    V8 determinism: 100회 동일 입력 → 100회 byte-identical 결과.
    """
    # 1. AD-24 period_key 검증 (8-1 `parse_virtual_budget_period_key` reuse).
    _validate_period_key(period_key=period_key)

    # 2. AD-8 monetary bounds 검증.
    _validate_decimal_non_negative(value=material_unit_cost, field="material_unit_cost")
    _validate_decimal_non_negative(value=labor_unit_cost, field="labor_unit_cost")
    _validate_overhead_rate(overhead_rate=overhead_rate)
    _validate_decimal_non_negative(value=material_qty, field="material_qty")
    _validate_decimal_non_negative(value=labor_hours, field="labor_hours")

    # 3. PRD §F8.1 scenario 한도 (8-1 wire lock).
    _validate_scenario_index(scenario_index=scenario_index)

    # 4. 공식 적용 (ROUND_HALF_EVEN, AD-8 + banker's rounding parity with TS decimal.js).
    material_cost = (material_unit_cost * material_qty).quantize(
        PRE_STANDARD_KRW_QUANTUM, rounding=ROUND_HALF_EVEN
    )
    labor_cost = (labor_unit_cost * labor_hours).quantize(
        PRE_STANDARD_KRW_QUANTUM, rounding=ROUND_HALF_EVEN
    )
    overhead_cost = (labor_cost * overhead_rate / Decimal("100")).quantize(
        PRE_STANDARD_KRW_QUANTUM, rounding=ROUND_HALF_EVEN
    )
    manufacturing_cost = material_cost + labor_cost + overhead_cost

    return PreStandardCost(
        material_cost=material_cost,
        labor_cost=labor_cost,
        overhead_cost=overhead_cost,
        manufacturing_cost=manufacturing_cost,
        period_key=period_key,
        scenario_index=scenario_index,
        engine_type="budget",
    )


def compute_pre_standard_hash(*, pre_standard_cost: PreStandardCost) -> str:
    """V8 determinism hash for pre-standard cost (Epic 4 baseline + 7-1/7-2/8-1/8-2 pattern).

    `hashlib.sha256(repr(pre_standard_cost).encode()).hexdigest()` —
    16바이트 hexdigest (32 chars), `sha256:` prefix.

    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `PreStandardCost` is `frozen=True, slots=True` — repr은
    결정론 (dataclass auto-generated repr + Decimal repr with full precision).

    Returns:
      `f"sha256:{32-char-hexdigest}"`.
    """
    if not isinstance(pre_standard_cost, PreStandardCost):
        raise ValueError(
            f"pre_standard_cost must be PreStandardCost, " f"got {type(pre_standard_cost).__name__}"
        )
    digest = hashlib.sha256(repr(pre_standard_cost).encode()).hexdigest()
    return f"{PRE_STANDARD_HASH_PREFIX}{digest}"


__all__ = [
    "PreStandardCost",
    "InvalidPreStandardInputError",
    "compute_pre_standard_cost",
    "compute_pre_standard_hash",
    "PRE_STANDARD_KRW_QUANTUM",
    "OVERHEAD_RATE_MIN_PCT",
    "OVERHEAD_RATE_MAX_PCT",
    "PRE_STANDARD_ENGINE_TYPE",
    "PRE_STANDARD_DEFAULT_SCENARIO_INDEX",
    "PRE_STANDARD_HASH_PREFIX",
    "PRE_STANDARD_STATE_VERIFIED",
    "PRE_STANDARD_DEFAULT_BASELINE_REVISION",
    "EngineType",
]
