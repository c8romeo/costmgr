"""packages.cost_engine.cvp — Story 7.1 (Epic 7) CVP/BEP Simulation pure kernel.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m7_simulation/services/cvp_simulation_service.py`
  (T3 service layer — fetch_cvp_baseline + simulate_cvp dispatch)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes
Decimal values as arguments; this kernel owns the V8 determinism
+ CVP math (BEP / target profit / delta apply / simulate orchestration).

PRD §F7.1 verbatim: "슬라이더 변경 시 BEP 수량·목표이익을 1초 이내 재계산."
NFR9 (P95 ≤ 5초) → 7-1 stricter (P95 ≤ 1초).
NFR16 determinism: byte-identical V8 CI gate pattern (Epic 4 baseline).

Story 7-1 (cj-style Epic 7 진입 첫 스토리):
- BEP 수량 = fixed_cost / (unit_price - unit_variable_cost)
- BEP 매출 = BEP 수량 * unit_price
- 기여이익 = unit_price - unit_variable_cost
- 목표이익 수량 = (fixed_cost + target_profit) / (unit_price - unit_variable_cost)

A19 cohesion pattern: `cvp.py` is `packages/cost_engine/cvp.py`
(cost_engine surface — Epic 4 cost_engine precedent + 7-1 cvp.py +
7-2 projection.py separate surface — A19 inventory_math precedent).

Pure functions (5 NEW):
- compute_bep(*, fixed_cost, unit_variable_cost, unit_price) -> BEPResult
- compute_target_profit(*, target_profit, fixed_cost, unit_variable_cost, unit_price) -> TargetProfitResult
- apply_delta(baseline: CVPBaseline, delta: CVPDelta) -> CVPBaseline (immutable)
- simulate_cvp(*, baseline: CVPBaseline, delta: CVPDelta) -> CVPResult
- compute_bep_hash(result: BEPResult | CVPResult) -> str (V8 determinism)

Frozen dataclasses (5 NEW):
- BEPResult: bep_quantity + bep_revenue + contribution_margin_per_unit + contribution_margin_ratio
- TargetProfitResult: target_quantity + target_revenue
- CVPBaseline: fixed_cost + unit_variable_cost + unit_price + operating_rate + target_profit
- CVPDelta: unit_price_delta_pct + unit_variable_cost_delta_pct + fixed_cost_delta_pct + operating_rate_delta_pct
- CVPResult: simulated_bep + simulated_target_profit + baseline_bep + baseline_target_profit + delta_summary

Edge cases (3종 ValueError):
- unit_price <= unit_variable_cost → "unit_price must exceed unit_variable_cost"
- fixed_cost < 0 → "fixed_cost must be non-negative"
- target_profit < 0 → "target_profit must be non-negative"

Decimal precision: ROUND_HALF_EVEN (banker's rounding, AD-8) parity with TS decimal.js.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

# ── Constants ────────────────────────────────────────────────
# Decimal quantization for monetary precision (AD-8 monetary types):
# - KRW: 1원 precision (0 decimal places) — NFR17 KRW only
# - Ratio: 4 decimal places precision (e.g., 33.3333%)
QUANT_KRW: Final[Decimal] = Decimal("1")
QUANT_RATIO: Final[Decimal] = Decimal("0.0001")
QUANT_QUANTITY: Final[Decimal] = Decimal("0.01")  # 2 decimal places for bep_quantity

# Hash prefix for compute_bep_hash (V8 determinism trace).
BEP_HASH_PREFIX: Final[str] = "sha256:"

# Korean SSOT message — used by main.py envelope handlers (CR 12-5 D-14).
BEP_INVALID_PRICE_MESSAGE_KO: Final[str] = "단가는 단위변동비보다 커야 합니다 (정상범위 외)"
BEP_INVALID_FIXED_COST_MESSAGE_KO: Final[str] = "고정비는 0 이상이어야 합니다"
BEP_INVALID_TARGET_PROFIT_MESSAGE_KO: Final[str] = "목표이익은 0 이상이어야 합니다"

# Delta percentage bounds (sliders min/max enforcement):
# - unit_price / unit_variable_cost: ±50% (PRD §F7.1)
# - fixed_cost: ±30%
# - operating_rate: 50% ~ 150% (operating rate slider range)
DELTA_UNIT_PRICE_MIN_PCT: Final[Decimal] = Decimal("-0.5")
DELTA_UNIT_PRICE_MAX_PCT: Final[Decimal] = Decimal("0.5")
DELTA_VARIABLE_COST_MIN_PCT: Final[Decimal] = Decimal("-0.5")
DELTA_VARIABLE_COST_MAX_PCT: Final[Decimal] = Decimal("0.5")
DELTA_FIXED_COST_MIN_PCT: Final[Decimal] = Decimal("-0.3")
DELTA_FIXED_COST_MAX_PCT: Final[Decimal] = Decimal("0.3")
DELTA_OPERATING_RATE_MIN_PCT: Final[Decimal] = Decimal("-0.5")
DELTA_OPERATING_RATE_MAX_PCT: Final[Decimal] = Decimal("0.5")

# Tuple bounds for delta_helpers (Pythonic iterable form).
PRICE_DELTA_PCT_BOUNDS: Final[tuple[Decimal, Decimal]] = (
    DELTA_UNIT_PRICE_MIN_PCT,
    DELTA_UNIT_PRICE_MAX_PCT,
)
FIXED_COST_DELTA_PCT_BOUNDS: Final[tuple[Decimal, Decimal]] = (
    DELTA_FIXED_COST_MIN_PCT,
    DELTA_FIXED_COST_MAX_PCT,
)
OPERATING_RATE_DELTA_PCT_BOUNDS: Final[tuple[Decimal, Decimal]] = (
    DELTA_OPERATING_RATE_MIN_PCT,
    DELTA_OPERATING_RATE_MAX_PCT,
)

# Operating rate absolute bounds (PRD §F7.1 — 슬라이더 50%~150%).
OPERATING_RATE_MIN: Final[Decimal] = Decimal("0.5")
OPERATING_RATE_MAX: Final[Decimal] = Decimal("1.5")

# Default operating rate (1.0 = 100% capacity).
DEFAULT_OPERATING_RATE: Final[Decimal] = Decimal("1.0")

# Default target profit baseline (0 KRW — no profit target set).
DEFAULT_TARGET_PROFIT: Final[Decimal] = Decimal("0")


# ── Frozen dataclasses ───────────────────────────────────────
@dataclass(frozen=True, slots=True)
class BEPResult:
    """Break-Even Point calculation result (frozen).

    `bep_quantity`: BEP 수량 (개)
    `bep_revenue`: BEP 매출 (원)
    `contribution_margin_per_unit`: 단위당 공헌이익 (원/개)
    `contribution_margin_ratio`: 공헌이익률 (0~1, Decimal 분수)

    Determinism: same inputs → same outputs (NFR16).
    """

    bep_quantity: Decimal
    bep_revenue: Decimal
    contribution_margin_per_unit: Decimal
    contribution_margin_ratio: Decimal


@dataclass(frozen=True, slots=True)
class TargetProfitResult:
    """Target profit calculation result (frozen).

    `target_quantity`: 목표이익 달성 수량 (개)
    `target_revenue`: 목표이익 달성 매출 (원)
    """

    target_quantity: Decimal
    target_revenue: Decimal


@dataclass(frozen=True, slots=True)
class CVPBaseline:
    """CVP baseline (frozen, immutable).

    5 fields — the baseline CVP state extracted from latest
    fiscal_period_snapshots + monthly_input_periods (service layer
    responsibility).

    `operating_rate`: 조업도 (0.5 ~ 1.5)
    `target_profit`: 목표이익 (KRW, default 0)
    """

    fixed_cost: Decimal
    unit_variable_cost: Decimal
    unit_price: Decimal
    operating_rate: Decimal = DEFAULT_OPERATING_RATE
    target_profit: Decimal = DEFAULT_TARGET_PROFIT


@dataclass(frozen=True, slots=True)
class CVPDelta:
    """CVP simulation delta (frozen, percentage-based).

    4 fields, all percentage deltas (Decimal 0~1). Defaults to 0
    (no change from baseline).

    `unit_price_delta_pct`: 단가 변동률 (±50%)
    `unit_variable_cost_delta_pct`: 단위변동비 변동률 (±50%)
    `fixed_cost_delta_pct`: 고정비 변동률 (±30%)
    `operating_rate_delta_pct`: 조업도 변동률 (±50%)
    """

    unit_price_delta_pct: Decimal = Decimal("0")
    unit_variable_cost_delta_pct: Decimal = Decimal("0")
    fixed_cost_delta_pct: Decimal = Decimal("0")
    operating_rate_delta_pct: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class CVPResult:
    """CVP simulation full result (frozen).

    Contains both simulated and baseline BEP / target_profit + delta_summary
    (4 variables' percentage deltas applied).

    `simulated_bep` / `baseline_bep`: BEPResult 비교
    `simulated_target_profit` / `baseline_target_profit`: TargetProfitResult 비교
    `delta_summary`: dict[str, Decimal] with 4 NEW delta percentages
    """

    simulated_bep: BEPResult
    simulated_target_profit: TargetProfitResult
    baseline_bep: BEPResult
    baseline_target_profit: TargetProfitResult
    delta_summary: dict[str, Decimal] = field(default_factory=dict)


# ── Typed exceptions ────────────────────────────────────────
class CVPInvalidInputError(ValueError):
    """Generic CVP input validation failure (defense-in-depth).

    Specific error codes are exposed via the `code` attribute:
    - "unit_price_must_exceed_variable_cost"
    - "fixed_cost_must_be_non_negative"
    - "target_profit_must_be_non_negative"
    - "invalid_decimal_type"
    - "operating_rate_out_of_bounds"
    - "delta_pct_out_of_bounds"

    CR 12-5 D-14 typed contract — main.py envelope handlers will map
    these to typed 422 INVALID_INPUT responses.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field


# ── Pure functions ───────────────────────────────────────────
def _validate_decimal(value: object, *, field_name: str, _allow_zero: bool = True) -> Decimal:
    """Validate input is Decimal (or convert int/float) — defense-in-depth.

    Strict typing prevents silent float precision loss.
    """
    if value is None:
        raise CVPInvalidInputError(
            f"{field_name} must not be None",
            code="invalid_decimal_type",
            field=field_name,
        )
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # Float → Decimal via string conversion to avoid float precision artifacts.
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except Exception as exc:
            raise CVPInvalidInputError(
                f"{field_name} must be a valid Decimal string, got {value!r}",
                code="invalid_decimal_type",
                field=field_name,
            ) from exc
    raise CVPInvalidInputError(
        f"{field_name} must be Decimal, int, float, or str, got {type(value).__name__}",
        code="invalid_decimal_type",
        field=field_name,
    )


def _q(value: Decimal, quant: Decimal = QUANT_KRW) -> Decimal:
    """Quantize a Decimal value with ROUND_HALF_EVEN (banker's rounding).

    AD-8 monetary precision parity with TS decimal.js.
    """
    return value.quantize(quant, rounding=ROUND_HALF_EVEN)


def compute_bep(
    *,
    fixed_cost: Decimal,
    unit_variable_cost: Decimal,
    unit_price: Decimal,
) -> BEPResult:
    """Compute Break-Even Point (BEP) — pure kernel.

    Formula:
        contribution_margin_per_unit = unit_price - unit_variable_cost
        bep_quantity = fixed_cost / contribution_margin_per_unit
        bep_revenue = bep_quantity * unit_price
        contribution_margin_ratio = contribution_margin_per_unit / unit_price

    Edge cases:
        - unit_price <= unit_variable_cost → ValueError (정상범위 외)
        - fixed_cost < 0 → ValueError (0 이상)
        - fixed_cost == 0 → bep_quantity = 0, bep_revenue = 0 (trivially break-even)

    Determinism (NFR16): 100회 동일 입력 → 100회 byte-identical BEPResult.
    """
    fixed_cost = _validate_decimal(fixed_cost, field_name="fixed_cost")
    unit_variable_cost = _validate_decimal(unit_variable_cost, field_name="unit_variable_cost")
    unit_price = _validate_decimal(unit_price, field_name="unit_price")

    if unit_price <= unit_variable_cost:
        raise CVPInvalidInputError(
            BEP_INVALID_PRICE_MESSAGE_KO,
            code="unit_price_must_exceed_variable_cost",
            field="unit_price",
        )
    if fixed_cost < 0:
        raise CVPInvalidInputError(
            BEP_INVALID_FIXED_COST_MESSAGE_KO,
            code="fixed_cost_must_be_non_negative",
            field="fixed_cost",
        )

    contribution_margin_per_unit = unit_price - unit_variable_cost

    if fixed_cost == 0:
        # Trivially break-even at 0 units sold.
        return BEPResult(
            bep_quantity=_q(Decimal("0"), QUANT_QUANTITY),
            bep_revenue=_q(Decimal("0")),
            contribution_margin_per_unit=_q(contribution_margin_per_unit),
            contribution_margin_ratio=_q(contribution_margin_per_unit / unit_price, QUANT_RATIO),
        )

    bep_quantity = fixed_cost / contribution_margin_per_unit
    bep_revenue = bep_quantity * unit_price
    contribution_margin_ratio = contribution_margin_per_unit / unit_price

    return BEPResult(
        bep_quantity=_q(bep_quantity, QUANT_QUANTITY),
        bep_revenue=_q(bep_revenue),
        contribution_margin_per_unit=_q(contribution_margin_per_unit),
        contribution_margin_ratio=_q(contribution_margin_ratio, QUANT_RATIO),
    )


def compute_target_profit(
    *,
    target_profit: Decimal,
    fixed_cost: Decimal,
    unit_variable_cost: Decimal,
    unit_price: Decimal,
) -> TargetProfitResult:
    """Compute target profit break-even — pure kernel.

    Formula:
        contribution_margin_per_unit = unit_price - unit_variable_cost
        target_quantity = (fixed_cost + target_profit) / contribution_margin_per_unit
        target_revenue = target_quantity * unit_price

    Edge cases (동일):
        - unit_price <= unit_variable_cost → ValueError
        - target_profit < 0 → ValueError (목표이익 0 이상)
        - fixed_cost < 0 → ValueError
        - target_profit == 0 → 동일 `compute_bep` 결과

    Determinism (NFR16): 100회 동일 입력 → 100회 byte-identical.
    """
    target_profit = _validate_decimal(target_profit, field_name="target_profit")
    fixed_cost = _validate_decimal(fixed_cost, field_name="fixed_cost")
    unit_variable_cost = _validate_decimal(unit_variable_cost, field_name="unit_variable_cost")
    unit_price = _validate_decimal(unit_price, field_name="unit_price")

    if unit_price <= unit_variable_cost:
        raise CVPInvalidInputError(
            BEP_INVALID_PRICE_MESSAGE_KO,
            code="unit_price_must_exceed_variable_cost",
            field="unit_price",
        )
    if target_profit < 0:
        raise CVPInvalidInputError(
            BEP_INVALID_TARGET_PROFIT_MESSAGE_KO,
            code="target_profit_must_be_non_negative",
            field="target_profit",
        )
    if fixed_cost < 0:
        raise CVPInvalidInputError(
            BEP_INVALID_FIXED_COST_MESSAGE_KO,
            code="fixed_cost_must_be_non_negative",
            field="fixed_cost",
        )

    contribution_margin_per_unit = unit_price - unit_variable_cost
    total_required = fixed_cost + target_profit

    if total_required == 0:
        return TargetProfitResult(
            target_quantity=_q(Decimal("0"), QUANT_QUANTITY),
            target_revenue=_q(Decimal("0")),
        )

    target_quantity = total_required / contribution_margin_per_unit
    target_revenue = target_quantity * unit_price

    return TargetProfitResult(
        target_quantity=_q(target_quantity, QUANT_QUANTITY),
        target_revenue=_q(target_revenue),
    )


def apply_delta(baseline: CVPBaseline, delta: CVPDelta) -> CVPBaseline:
    """Apply 4-variable delta to baseline — return new (immutable) CVPBaseline.

    Formulas:
        simulated_unit_price = baseline_unit_price * (1 + unit_price_delta_pct)
        simulated_unit_variable_cost = baseline_unit_variable_cost * (1 + unit_variable_cost_delta_pct)
        simulated_fixed_cost = baseline_fixed_cost * (1 + fixed_cost_delta_pct)
        simulated_operating_rate = baseline_operating_rate * (1 + operating_rate_delta_pct)

    Edge cases (CVPInvalidInputError):
        - operating_rate result out of bounds (0.5 ~ 1.5)

    Note: `baseline` is NOT mutated (frozen=True + return new instance).
    Determinism: 100회 동일 입력 → 100회 byte-identical CVPBaseline.
    """
    if not isinstance(baseline, CVPBaseline):
        raise CVPInvalidInputError(
            f"baseline must be CVPBaseline, got {type(baseline).__name__}",
            code="invalid_decimal_type",
            field="baseline",
        )
    if not isinstance(delta, CVPDelta):
        raise CVPInvalidInputError(
            f"delta must be CVPDelta, got {type(delta).__name__}",
            code="invalid_decimal_type",
            field="delta",
        )

    simulated_unit_price = baseline.unit_price * (Decimal("1") + delta.unit_price_delta_pct)
    simulated_unit_variable_cost = baseline.unit_variable_cost * (
        Decimal("1") + delta.unit_variable_cost_delta_pct
    )
    simulated_fixed_cost = baseline.fixed_cost * (Decimal("1") + delta.fixed_cost_delta_pct)
    simulated_operating_rate = baseline.operating_rate * (
        Decimal("1") + delta.operating_rate_delta_pct
    )

    # Validate operating_rate stays in bounds (PRD §F7.1 슬라이더 50%~150%).
    if (
        simulated_operating_rate < OPERATING_RATE_MIN
        or simulated_operating_rate > OPERATING_RATE_MAX
    ):
        raise CVPInvalidInputError(
            f"simulated_operating_rate {simulated_operating_rate} out of bounds "
            f"({OPERATING_RATE_MIN} ~ {OPERATING_RATE_MAX})",
            code="operating_rate_out_of_bounds",
            field="operating_rate",
        )

    return CVPBaseline(
        fixed_cost=_q(simulated_fixed_cost),
        unit_variable_cost=_q(simulated_unit_variable_cost),
        unit_price=_q(simulated_unit_price),
        operating_rate=_q(simulated_operating_rate, QUANT_RATIO),
        target_profit=baseline.target_profit,
    )


def simulate_cvp(
    *,
    baseline: CVPBaseline,
    delta: CVPDelta,
) -> CVPResult:
    """Simulate CVP with delta applied — full orchestration.

    Steps:
        1. `apply_delta(baseline, delta)` → simulated CVPBaseline
        2. `compute_bep(simulated)` → simulated_bep
        3. `compute_target_profit(simulated, target_profit=baseline.target_profit)` → simulated_target_profit
        4. `compute_bep(baseline)` → baseline_bep
        5. `compute_target_profit(baseline, target_profit=baseline.target_profit)` → baseline_target_profit
        6. delta_summary = dict of 4 NEW delta percentages

    Determinism: 100회 동일 입력 → 100회 byte-identical CVPResult.
    """
    if not isinstance(baseline, CVPBaseline):
        raise CVPInvalidInputError(
            f"baseline must be CVPBaseline, got {type(baseline).__name__}",
            code="invalid_decimal_type",
            field="baseline",
        )
    if not isinstance(delta, CVPDelta):
        raise CVPInvalidInputError(
            f"delta must be CVPDelta, got {type(delta).__name__}",
            code="invalid_decimal_type",
            field="delta",
        )

    # 1. Apply delta to baseline → simulated.
    simulated = apply_delta(baseline, delta)

    # 2. Simulated BEP.
    simulated_bep = compute_bep(
        fixed_cost=simulated.fixed_cost,
        unit_variable_cost=simulated.unit_variable_cost,
        unit_price=simulated.unit_price,
    )

    # 3. Simulated target profit (using baseline target_profit — unchanged).
    simulated_target_profit = compute_target_profit(
        target_profit=baseline.target_profit,
        fixed_cost=simulated.fixed_cost,
        unit_variable_cost=simulated.unit_variable_cost,
        unit_price=simulated.unit_price,
    )

    # 4. Baseline BEP.
    baseline_bep = compute_bep(
        fixed_cost=baseline.fixed_cost,
        unit_variable_cost=baseline.unit_variable_cost,
        unit_price=baseline.unit_price,
    )

    # 5. Baseline target profit.
    baseline_target_profit = compute_target_profit(
        target_profit=baseline.target_profit,
        fixed_cost=baseline.fixed_cost,
        unit_variable_cost=baseline.unit_variable_cost,
        unit_price=baseline.unit_price,
    )

    # 6. Delta summary — 4 variables' effective percentage deltas (after quantize).
    delta_summary = {
        "unit_price_delta_pct": _q(delta.unit_price_delta_pct, QUANT_RATIO),
        "unit_variable_cost_delta_pct": _q(delta.unit_variable_cost_delta_pct, QUANT_RATIO),
        "fixed_cost_delta_pct": _q(delta.fixed_cost_delta_pct, QUANT_RATIO),
        "operating_rate_delta_pct": _q(delta.operating_rate_delta_pct, QUANT_RATIO),
    }

    return CVPResult(
        simulated_bep=simulated_bep,
        simulated_target_profit=simulated_target_profit,
        baseline_bep=baseline_bep,
        baseline_target_profit=baseline_target_profit,
        delta_summary=delta_summary,
    )


def compute_bep_hash(result: BEPResult | CVPResult | TargetProfitResult) -> str:
    """Compute V8 determinism hash for CVP result — `sha256:` + 64 hex.

    `hashlib.sha256(repr(result).encode()).hexdigest()` —
    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `BEPResult` / `CVPResult` / `TargetProfitResult` are
    `frozen=True, slots=True` — repr은 결정론 (dataclass auto-generated repr).

    Returns:
        `f"sha256:{64-char-hexdigest}"`.
    """
    if not isinstance(result, BEPResult | CVPResult | TargetProfitResult):
        raise CVPInvalidInputError(
            f"result must be BEPResult, CVPResult, or TargetProfitResult, "
            f"got {type(result).__name__}",
            code="invalid_decimal_type",
            field="result",
        )
    digest = hashlib.sha256(repr(result).encode()).hexdigest()
    return f"{BEP_HASH_PREFIX}{digest}"


__all__ = [
    # Constants
    "QUANT_KRW",
    "QUANT_RATIO",
    "QUANT_QUANTITY",
    "BEP_HASH_PREFIX",
    "BEP_INVALID_PRICE_MESSAGE_KO",
    "BEP_INVALID_FIXED_COST_MESSAGE_KO",
    "BEP_INVALID_TARGET_PROFIT_MESSAGE_KO",
    "DELTA_UNIT_PRICE_MIN_PCT",
    "DELTA_UNIT_PRICE_MAX_PCT",
    "DELTA_VARIABLE_COST_MIN_PCT",
    "DELTA_VARIABLE_COST_MAX_PCT",
    "DELTA_FIXED_COST_MIN_PCT",
    "DELTA_FIXED_COST_MAX_PCT",
    "DELTA_OPERATING_RATE_MIN_PCT",
    "DELTA_OPERATING_RATE_MAX_PCT",
    "PRICE_DELTA_PCT_BOUNDS",
    "FIXED_COST_DELTA_PCT_BOUNDS",
    "OPERATING_RATE_DELTA_PCT_BOUNDS",
    "OPERATING_RATE_MIN",
    "OPERATING_RATE_MAX",
    "DEFAULT_OPERATING_RATE",
    "DEFAULT_TARGET_PROFIT",
    # Frozen dataclasses
    "BEPResult",
    "TargetProfitResult",
    "CVPBaseline",
    "CVPDelta",
    "CVPResult",
    # Typed exceptions
    "CVPInvalidInputError",
    # Pure functions
    "compute_bep",
    "compute_target_profit",
    "apply_delta",
    "simulate_cvp",
    "compute_bep_hash",
]
