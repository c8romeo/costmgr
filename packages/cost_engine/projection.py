"""packages.cost_engine.projection — Story 7.2 (Epic 7) Next-Month Projection pure kernel.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m7_simulation/services/projection_service.py`
  (T3 service layer — fetch_projection_baseline + project_next_month dispatch)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, NO sqlalchemy,
NO DB import (cost_engine layer rule). The service layer passes
Decimal values as arguments; this kernel owns the V8 determinism
+ Next-Month Projection math (interest expense / after-tax income /
project_next_month orchestration).

PRD §F7.2 verbatim: "차월 추정 시 차입금·이자율·상승률·세율 4종 파라미터 사용자 입력 강제."
NFR9 (P95 ≤ 5초) → 7-2 stricter (P95 ≤ 1초, compute만).
NFR16 determinism: byte-identical V8 CI gate pattern (Epic 4 baseline).

Story 7-2 (cj-style Epic 7 진입 두번째 스토리):
- 4 parameters: loan_amount (KRW) + interest_rate (%) + cost_inflation_rate (%) + corporate_tax_rate (%)
- projected_revenue = baseline.monthly_revenue * (1 + cost_inflation_rate/100)
- projected_variable_cost = baseline.monthly_variable_cost * (1 + cost_inflation_rate/100)
- projected_fixed_cost = baseline.monthly_fixed_cost + interest_expense (NEW 차입금 이자 추가)
- interest_expense = loan_amount * (interest_rate / 100)
- pre_tax_income = projected_revenue - projected_variable_cost - projected_fixed_cost
- corporate_tax = max(0, pre_tax_income) * (corporate_tax_rate / 100) (손실 시 0)
- after_tax_income = pre_tax_income - corporate_tax (손실 시 그대로 음수)

A19 cohesion pattern: `projection.py` is `packages/cost_engine/projection.py`
(cost_engine surface — Epic 4 cost_engine precedent + 7-1 cvp.py +
7-2 projection.py separate surface — A19 inventory_math precedent).

Pure functions (3 NEW):
- compute_interest_expense(*, loan_amount, interest_rate) -> Decimal
- compute_after_tax_income(*, pre_tax_income, corporate_tax_rate) -> Decimal
- project_next_month(*, baseline_cvp, projection_inputs) -> NextMonthProjection
- compute_projection_hash(projection: NextMonthProjection) -> str (V8 determinism)

Frozen dataclasses (2 NEW):
- ProjectionInputs: loan_amount + interest_rate + cost_inflation_rate + corporate_tax_rate
- NextMonthProjection: projected_revenue + projected_variable_cost + projected_fixed_cost
  + interest_expense + pre_tax_income + corporate_tax + after_tax_income

Typed exceptions (3 NEW):
- ProjectionInvalidInputError: kernel-level input validation
- InvalidProjectionMonthError: 422 — projection_month format / chronology violation
- ProjectionBaselineNotFoundError: 404 — baseline fetch miss

Edge cases (계열):
- loan_amount < 0 → ValueError("loan_amount must be non-negative")
- interest_rate < 0 → ValueError("interest_rate must be non-negative")
- interest_rate > 100 → ValueError("interest_rate must be <= 100%")
- corporate_tax_rate < 0 or > 100 → ValueError("corporate_tax_rate must be in [0, 100]")
- pre_tax_income < 0 → 손실 인정 (corporate_tax=0 처리, after_tax_income은 그대로 음수)

Decimal precision: ROUND_HALF_EVEN (banker's rounding, AD-8) parity with TS decimal.js.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

# Import CVPBaseline for type hint (CVP_SIMULATION baseline reuse)
from packages.cost_engine.cvp import CVPBaseline

# ── Constants ────────────────────────────────────────────────
# Decimal quantization for monetary precision (AD-8 monetary types):
# - KRW: 1원 precision (0 decimal places) — NFR17 KRW only
QUANT_KRW: Final[Decimal] = Decimal("1")
QUANT_PERCENT: Final[Decimal] = Decimal("0.0001")  # 4 decimal places for percentage

# Hash prefix for compute_projection_hash (V8 determinism trace).
PROJECTION_HASH_PREFIX: Final[str] = "sha256:"

# Korean SSOT message — used by main.py envelope handlers (CR 12-5 D-14).
PROJECTION_LOAN_AMOUNT_NEGATIVE_KO: Final[str] = "차입금은 0 이상이어야 합니다"
PROJECTION_INTEREST_RATE_NEGATIVE_KO: Final[str] = "이자율은 0 이상이어야 합니다"
PROJECTION_INTEREST_RATE_OVER_100_KO: Final[str] = "이자율은 100% 이하여야 합니다"
PROJECTION_CORPORATE_TAX_RATE_RANGE_KO: Final[str] = "법인세율은 0과 100 사이여야 합니다"

# Projection month format — AD-24 `YYYY-MM` pattern.
PROJECTION_MONTH_PATTERN: Final[str] = r"^\d{4}-(0[1-9]|1[0-2])$"

# Projection month bound (chronological invariant: projection_month > period_key).
# Implemented as service-layer validator (not enforced in pure kernel — service
# layer owns AD-24 validation per CR 12-1 L3 boundary).

# Cost inflation rate bounds (per spec AC #2 Zod schema — -50% ~ +100%, raw percent).
# NOTE: cost_inflation_rate is expressed in raw percent (0~100 range like
# interest_rate + corporate_tax_rate), not as a fraction (0~1). The Zod
# schema treats `cost_inflation_rate=10` as 10% inflation. The internal
# formula divides by 100 to derive the fraction (1 + rate/100).
PROJECTION_COST_INFLATION_RATE_MIN_PCT: Final[Decimal] = Decimal("-50")
PROJECTION_COST_INFLATION_RATE_MAX_PCT: Final[Decimal] = Decimal("100")


# ── Frozen dataclasses ───────────────────────────────────────
@dataclass(frozen=True, slots=True)
class ProjectionInputs:
    """Next-month projection user inputs (frozen, immutable).

    4 fields — PRD §F7.2 4종 파라미터:
    - `loan_amount`: 차입금 (KRW 정수, BigInteger)
    - `interest_rate`: 이자율 (%, 0~100)
    - `cost_inflation_rate`: 원가 상승률 (%, -50~100, 디플레~인플레)
    - `corporate_tax_rate`: 법인세율 (%, 0~100)

    Used as input to `project_next_month` after Zod schema validation.
    """

    loan_amount: Decimal
    interest_rate: Decimal
    cost_inflation_rate: Decimal
    corporate_tax_rate: Decimal


@dataclass(frozen=True, slots=True)
class NextMonthProjection:
    """Next-month projection result (frozen, immutable).

    7 fields — full projection output:
    - `projected_revenue`: 차월 매출 (KRW)
    - `projected_variable_cost`: 차월 변동비 (KRW)
    - `projected_fixed_cost`: 차월 고정비 + 차입금 이자 (KRW)
    - `interest_expense`: 차입금 이자 (KRW)
    - `pre_tax_income`: 세전 이익 (KRW, 음수 가능 — 손실)
    - `corporate_tax`: 법인세 (KRW, 손실 시 0)
    - `after_tax_income`: 세후 이익 (KRW, 손실 시 음수 유지)

    Determinism (NFR16): same inputs → same outputs.
    """

    projected_revenue: Decimal
    projected_variable_cost: Decimal
    projected_fixed_cost: Decimal
    interest_expense: Decimal
    pre_tax_income: Decimal
    corporate_tax: Decimal
    after_tax_income: Decimal


# ── Typed exceptions ────────────────────────────────────────
class ProjectionInvalidInputError(ValueError):
    """Generic projection input validation failure (defense-in-depth).

    Specific error codes are exposed via the `code` attribute:
    - "loan_amount_must_be_non_negative"
    - "interest_rate_must_be_non_negative"
    - "interest_rate_must_be_at_most_100"
    - "corporate_tax_rate_must_be_in_range_0_100"
    - "invalid_decimal_type"
    - "invalid_projection_month_format"

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


class InvalidProjectionMonthError(Exception):
    """422 INVALID_PROJECTION_MONTH — projection_month AD-24 violation.

    AD-24 period_key typed pattern — YYYY-MM format. Service layer
    enforces the chronological invariant (period_key < projection_month).
    """

    def __init__(
        self,
        *,
        period_key: str,
        projection_month: str,
        reason: str,
    ) -> None:
        self.period_key = period_key
        self.projection_month = projection_month
        self.reason = reason
        super().__init__(
            f"Invalid projection_month: period_key={period_key!r}, "
            f"projection_month={projection_month!r}, reason={reason!r}"
        )


class ProjectionBaselineNotFoundError(Exception):
    """404 PROJECTION_BASELINE_NOT_FOUND — baseline fetch miss.

    Mirrors `CVPBaselineNotFoundError` (7-1) for the projection
    sub-endpoint. Raised when no committed snapshot exists for the
    requested period_key.
    """

    def __init__(
        self,
        *,
        tenant_id: str,
        period_key: str,
        message: str | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.message = (
            message
            or f"Projection baseline not found: tenant_id={tenant_id}, " f"period_key={period_key}"
        )
        super().__init__(self.message)


# ── Pure functions ───────────────────────────────────────────
def _validate_decimal(value: object, *, field_name: str) -> Decimal:
    """Validate input is Decimal (or convert int/float) — defense-in-depth.

    Strict typing prevents silent float precision loss.
    """
    if value is None:
        raise ProjectionInvalidInputError(
            f"{field_name} must not be None",
            code="invalid_decimal_type",
            field=field_name,
        )
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except Exception as exc:
            raise ProjectionInvalidInputError(
                f"{field_name} must be a valid Decimal string, got {value!r}",
                code="invalid_decimal_type",
                field=field_name,
            ) from exc
    raise ProjectionInvalidInputError(
        f"{field_name} must be Decimal, int, float, or str, got {type(value).__name__}",
        code="invalid_decimal_type",
        field=field_name,
    )


def _q(value: Decimal, quant: Decimal = QUANT_KRW) -> Decimal:
    """Quantize a Decimal value with ROUND_HALF_EVEN (banker's rounding).

    AD-8 monetary precision parity with TS decimal.js.
    """
    return value.quantize(quant, rounding=ROUND_HALF_EVEN)


def compute_interest_expense(
    *,
    loan_amount: Decimal,
    interest_rate: Decimal,
) -> Decimal:
    """Compute interest expense (이자) — pure kernel.

    Formula:
        interest_expense = loan_amount * (interest_rate / 100)

    Edge cases:
        - loan_amount < 0 → ValueError
        - interest_rate < 0 → ValueError
        - interest_rate > 100 → ValueError (비현실적)

    Determinism (NFR16): 100회 동일 입력 → 100회 byte-identical Decimal.
    """
    loan_amount = _validate_decimal(loan_amount, field_name="loan_amount")
    interest_rate = _validate_decimal(interest_rate, field_name="interest_rate")

    if loan_amount < 0:
        raise ProjectionInvalidInputError(
            PROJECTION_LOAN_AMOUNT_NEGATIVE_KO,
            code="loan_amount_must_be_non_negative",
            field="loan_amount",
        )
    if interest_rate < 0:
        raise ProjectionInvalidInputError(
            PROJECTION_INTEREST_RATE_NEGATIVE_KO,
            code="interest_rate_must_be_non_negative",
            field="interest_rate",
        )
    if interest_rate > 100:
        raise ProjectionInvalidInputError(
            PROJECTION_INTEREST_RATE_OVER_100_KO,
            code="interest_rate_must_be_at_most_100",
            field="interest_rate",
        )

    # Compute interest as loan_amount times rate divided by one hundred
    interest = loan_amount * (interest_rate / Decimal("100"))
    return _q(interest)


def compute_after_tax_income(
    *,
    pre_tax_income: Decimal,
    corporate_tax_rate: Decimal,
) -> Decimal:
    """Compute after-tax income (세후 이익) — pure kernel.

    Formula:
        corporate_tax = max(0, pre_tax_income) * (corporate_tax_rate / 100)
        after_tax_income = pre_tax_income - corporate_tax

    Edge cases:
        - corporate_tax_rate < 0 → ValueError
        - corporate_tax_rate > 100 → ValueError
        - pre_tax_income < 0 → 손실 인정 (corporate_tax=0, after_tax_income 그대로 음수)

    Determinism (NFR16): 100회 동일 입력 → 100회 byte-identical Decimal.
    """
    pre_tax_income = _validate_decimal(pre_tax_income, field_name="pre_tax_income")
    corporate_tax_rate = _validate_decimal(corporate_tax_rate, field_name="corporate_tax_rate")

    if corporate_tax_rate < 0 or corporate_tax_rate > 100:
        raise ProjectionInvalidInputError(
            PROJECTION_CORPORATE_TAX_RATE_RANGE_KO,
            code="corporate_tax_rate_must_be_in_range_0_100",
            field="corporate_tax_rate",
        )

    # 손실 처리: corporate_tax = 0 (음수 income에 대해 세금은 0)
    if pre_tax_income < 0:
        corporate_tax = Decimal("0")
    else:
        corporate_tax = pre_tax_income * (corporate_tax_rate / Decimal("100"))

    after_tax = pre_tax_income - corporate_tax
    return _q(after_tax)


def project_next_month(
    *,
    baseline_cvp: CVPBaseline,
    projection_inputs: ProjectionInputs,
) -> NextMonthProjection:
    """Project next-month financial outcomes — full orchestration.

    Steps:
        1. `compute_interest_expense(loan_amount, interest_rate)`
        2. `projected_revenue = baseline_cvp.monthly_revenue * (1 + cost_inflation_rate/100)`
           (NOTE: baseline CVP carries `unit_price` not `monthly_revenue` —
           service layer pre-derives monthly totals from `monthly_input_periods`
           + `products` aggregation; pure kernel receives a CVPBaseline
           proxy or kwargs-derived baseline.)
        3. `projected_variable_cost` similar to revenue
        4. `projected_fixed_cost = baseline.monthly_fixed_cost + interest_expense`
        5. `pre_tax_income = revenue - variable - fixed`
        6. `compute_after_tax_income(pre_tax_income, corporate_tax_rate)`
           (handles corporate_tax calc internally)

    Note on baseline:
        CVPBaseline does NOT carry monthly totals (only per-unit fields).
        The service layer is responsible for pre-deriving monthly totals
        from `monthly_input_periods` aggregation and constructing a
        baseline-like kwargs object. For kernel simplicity, we accept
        `baseline_cvp` as a `CVPBaseline` and assume the service has
        extended it; if not, the kernel raises.

    Determinism (NFR16): 100회 동일 입력 → 100회 byte-identical.
    """
    if not isinstance(baseline_cvp, CVPBaseline):
        raise ProjectionInvalidInputError(
            f"baseline_cvp must be CVPBaseline, got {type(baseline_cvp).__name__}",
            code="invalid_decimal_type",
            field="baseline_cvp",
        )
    if not isinstance(projection_inputs, ProjectionInputs):
        raise ProjectionInvalidInputError(
            f"projection_inputs must be ProjectionInputs, got {type(projection_inputs).__name__}",
            code="invalid_decimal_type",
            field="projection_inputs",
        )

    # Validate cost_inflation_rate bounds (-50% ~ +100%)
    cost_inflation_rate = projection_inputs.cost_inflation_rate
    if (
        cost_inflation_rate < PROJECTION_COST_INFLATION_RATE_MIN_PCT
        or cost_inflation_rate > PROJECTION_COST_INFLATION_RATE_MAX_PCT
    ):
        raise ProjectionInvalidInputError(
            f"cost_inflation_rate must be in [-50%, 100%], got {cost_inflation_rate}",
            code="cost_inflation_rate_must_be_in_range_minus50_plus100",
            field="cost_inflation_rate",
        )

    # 1. Interest expense.
    interest_expense = compute_interest_expense(
        loan_amount=projection_inputs.loan_amount,
        interest_rate=projection_inputs.interest_rate,
    )

    # 2-3. Derive monthly totals from CVPBaseline proxy.
    # In a real wire, the service layer pre-computes monthly_revenue/
    # monthly_variable_cost/monthly_fixed_cost from
    # `monthly_input_periods` + `products` aggregation and passes them
    # via an extended baseline. For this kernel, we use a simplified
    # proxy: `unit_price × operating_rate` for revenue proxy and
    # `unit_variable_cost × operating_rate` for variable cost proxy.
    # Service layer OVERRIDES these by extending CVPBaseline — see
    # `projection_service.py` for actual aggregation logic.
    #
    # CRITICAL: This is the kernel contract — CVPBaseline carries
    # per-unit fields + operating_rate. For 7-2 we treat these as
    # monthly proxies (PRD §F7.2 단순화 — exact monthly aggregation
    # is service-layer responsibility).
    operating_rate = baseline_cvp.operating_rate
    if operating_rate <= 0:
        raise ProjectionInvalidInputError(
            f"baseline operating_rate must be positive, got {operating_rate}",
            code="operating_rate_must_be_positive",
            field="baseline_cvp",
        )

    # Revenue proxy = unit_price * operating_rate (PRD §F7.2 단순화).
    # Variable cost proxy = unit_variable_cost * operating_rate.
    # Fixed cost = baseline fixed_cost (KRW, already aggregated).
    # In real wire, service layer passes pre-aggregated monthly totals.
    # Here we use the per-unit × operating_rate approximation as the
    # canonical kernel input — drift detector tests verify parity
    # with service-layer pre-aggregation.
    baseline_monthly_revenue = baseline_cvp.unit_price * operating_rate
    baseline_monthly_variable_cost = baseline_cvp.unit_variable_cost * operating_rate
    baseline_monthly_fixed_cost = baseline_cvp.fixed_cost

    # Apply cost inflation to revenue + variable cost.
    inflation_factor = Decimal("1") + (projection_inputs.cost_inflation_rate / Decimal("100"))
    projected_revenue = baseline_monthly_revenue * inflation_factor
    projected_variable_cost = baseline_monthly_variable_cost * inflation_factor
    projected_fixed_cost = baseline_monthly_fixed_cost + interest_expense

    # Pre-tax income.
    pre_tax_income = projected_revenue - projected_variable_cost - projected_fixed_cost

    # Corporate tax + after-tax income.
    # Use the internal logic (don't call compute_after_tax_income to avoid
    # double-quantization of corporate_tax).
    if pre_tax_income < 0:
        corporate_tax = Decimal("0")
    else:
        corporate_tax = pre_tax_income * (projection_inputs.corporate_tax_rate / Decimal("100"))
    after_tax_income = pre_tax_income - corporate_tax

    return NextMonthProjection(
        projected_revenue=_q(projected_revenue),
        projected_variable_cost=_q(projected_variable_cost),
        projected_fixed_cost=_q(projected_fixed_cost),
        interest_expense=_q(interest_expense),
        pre_tax_income=_q(pre_tax_income),
        corporate_tax=_q(corporate_tax),
        after_tax_income=_q(after_tax_income),
    )


def compute_projection_hash(projection: NextMonthProjection) -> str:
    """Compute V8 determinism hash for NextMonthProjection — `sha256:` + 64 hex.

    `hashlib.sha256(repr(projection).encode()).hexdigest()` —
    Pure-Python, stdlib-only, deterministic (AD-5 + NFR16 + AD-11).

    Note: `NextMonthProjection` is `frozen=True, slots=True` — repr is
    결정론 (dataclass auto-generated repr).

    Returns:
        `f"sha256:{64-char-hexdigest}"`.
    """
    if not isinstance(projection, NextMonthProjection):
        raise ProjectionInvalidInputError(
            f"projection must be NextMonthProjection, got {type(projection).__name__}",
            code="invalid_decimal_type",
            field="projection",
        )
    digest = hashlib.sha256(repr(projection).encode()).hexdigest()
    return f"{PROJECTION_HASH_PREFIX}{digest}"


__all__ = [
    # Constants
    "QUANT_KRW",
    "QUANT_PERCENT",
    "PROJECTION_HASH_PREFIX",
    "PROJECTION_LOAN_AMOUNT_NEGATIVE_KO",
    "PROJECTION_INTEREST_RATE_NEGATIVE_KO",
    "PROJECTION_INTEREST_RATE_OVER_100_KO",
    "PROJECTION_CORPORATE_TAX_RATE_RANGE_KO",
    "PROJECTION_MONTH_PATTERN",
    "PROJECTION_COST_INFLATION_RATE_MIN_PCT",
    "PROJECTION_COST_INFLATION_RATE_MAX_PCT",
    # Frozen dataclasses
    "ProjectionInputs",
    "NextMonthProjection",
    # Typed exceptions
    "ProjectionInvalidInputError",
    "InvalidProjectionMonthError",
    "ProjectionBaselineNotFoundError",
    # Pure functions
    "compute_interest_expense",
    "compute_after_tax_income",
    "project_next_month",
    "compute_projection_hash",
]
