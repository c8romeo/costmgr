"""packages.services.m2_input.labor_conversion — Story 3.2 FTE precision.

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical labor-conversion kernel consumed by
`apps/api/modules/m2_input/services/monthly_input_service.py` AND
mirrored by `apps/web/lib/l2-input-fte.ts` (drift caught by
`tests/integration/test_m2_input_label_consistency.py`).

The module answers:
- "Given `tenant_settings.payroll.*` (partial) + PRD defaults, what's the
  effective payroll settings?" → `merge_payroll_settings`
- "Given pay_type='monthly' + breakdown 5 fields, what's the FTE wage?"
  → `compute_pay_type_breakdown`
- "Given pay_type='daily' + workers/days/daily_wage, what's the FTE wage
  via direct sum?" → `compute_fte_wage_for_daily` (NOT multiplied by
  `monthly_salary_basis_krw` — that's only for monthly-mode 환산)
- "Given mode='daily' + 31 per-day FTE values, what's the month rollup?"
  → `rollup_daily_fte` (sum, not average)
- "Given all of the above, what's the [인원] tab read-only display?"
  → `build_fte_display` (single composition function called by service)

PRD §6.1 인건비 구성:
- 기본급 (base) · 시간외 (overtime) · 복리후생 (welfare) · 상여 (bonus) ·
  퇴직충당금 (retirement_reserve) × 회사부담임률 (company_burden_rate)
- pay_type='monthly' → 정규화 완료 (fte_headcount = workers as-is)
- pay_type='daily' → FTE 환산 (fte_headcount = workers × days / workdays)

AD-15 cross-language parity: snake_case ↔ camelCase TS; banker's rounding
(ROUND_HALF_EVEN) on both sides — TS implements `roundHalfEven`
explicitly because `Math.round` is half-away-from-zero. Decimal ↔ string
at API boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum
from typing import Final, NamedTuple


class PayType(str, Enum):
    """PRD §6.1 인건비 pay_type — backend canonical enum values (snake_case)."""

    MONTHLY = "monthly"  # 정규직 (월급)
    DAILY = "daily"  # 일용직 (일급)


# ── Payroll settings (PRD §6.1 defaults + per-tenant override) ─
class PayrollSettings(NamedTuple):
    """Effective payroll settings (override applied via `merge_payroll_settings`).

    All fields are final-shape values that flow into the FTE calculation.
    Per-field override semantics: any individual field can be replaced
    while others keep the PRD default. See `merge_payroll_settings`.

    `standard_monthly_hours`: a single full-time worker's monthly hours.
    Used by the 730h 시나리오 (PRD §6.1 원본 hr 로직):
        fte_from_hours = total_work_hours / standard_monthly_hours
    Default 228 (= 22 workdays × ~10.4h/day incl. overtime).
    """

    monthly_salary_basis_krw: int
    workdays_in_month: int
    standard_monthly_hours: int
    company_burden_rate: Decimal


DEFAULT_PAYROLL: Final[PayrollSettings] = PayrollSettings(
    monthly_salary_basis_krw=2_500_000,
    workdays_in_month=22,
    standard_monthly_hours=228,
    company_burden_rate=Decimal("0.115"),
)


def merge_payroll_settings(
    override: dict | None,
    base: PayrollSettings = DEFAULT_PAYROLL,
) -> PayrollSettings:
    """Apply a partial `tenant_settings.payroll.*` override on top of `base`.

    Per-field fallback semantics: any missing key keeps the base value.
    Raises `ValueError` on out-of-range numeric values (defense-in-depth
    before reaching the service layer — Pydantic catches most, but the
    pure layer must be self-protective when called from tests directly).

    Args:
        override: Optional dict with any subset of:
            `monthly_salary_basis_krw`, `workdays_in_month`,
            `standard_monthly_hours`, `company_burden_rate`.
            Keys with `None` value are treated as missing.
        base: Defaults to `DEFAULT_PAYROLL` (PRD §6.1). Tests may pass
            a custom base.

    Returns:
        A new `PayrollSettings` NamedTuple with overrides applied.
    """
    if not override:
        return base

    monthly_salary_basis_krw = override.get(
        "monthly_salary_basis_krw", base.monthly_salary_basis_krw
    )
    if monthly_salary_basis_krw is None:
        monthly_salary_basis_krw = base.monthly_salary_basis_krw
    if not isinstance(monthly_salary_basis_krw, int) or monthly_salary_basis_krw < 0:
        raise ValueError(
            f"monthly_salary_basis_krw must be a non-negative int, "
            f"got {monthly_salary_basis_krw!r}"
        )

    workdays_in_month = override.get("workdays_in_month", base.workdays_in_month)
    if workdays_in_month is None:
        workdays_in_month = base.workdays_in_month
    if not isinstance(workdays_in_month, int) or workdays_in_month < 1 or workdays_in_month > 31:
        raise ValueError(f"workdays_in_month must be 1..31, got {workdays_in_month!r}")

    standard_monthly_hours = override.get("standard_monthly_hours", base.standard_monthly_hours)
    if standard_monthly_hours is None:
        standard_monthly_hours = base.standard_monthly_hours
    if not isinstance(standard_monthly_hours, int) or standard_monthly_hours < 1:
        raise ValueError(
            f"standard_monthly_hours must be a positive int, " f"got {standard_monthly_hours!r}"
        )

    company_burden_rate = override.get("company_burden_rate", base.company_burden_rate)
    if company_burden_rate is None:
        company_burden_rate = base.company_burden_rate
    if isinstance(company_burden_rate, int | float | str):
        company_burden_rate = Decimal(str(company_burden_rate))
    if not isinstance(company_burden_rate, Decimal):
        raise ValueError(
            f"company_burden_rate must be Decimal-compatible, "
            f"got {type(company_burden_rate).__name__}"
        )
    if company_burden_rate < 0 or company_burden_rate > 1:
        raise ValueError(f"company_burden_rate must be in [0, 1], got {company_burden_rate}")

    return PayrollSettings(
        monthly_salary_basis_krw=monthly_salary_basis_krw,
        workdays_in_month=workdays_in_month,
        standard_monthly_hours=standard_monthly_hours,
        company_burden_rate=company_burden_rate,
    )


# ── Breakdown aggregator (PRD §6.1) ──────────────────────────
@dataclass(frozen=True)
class PayTypeBreakdown:
    """PRD §6.1 인건비 5-field breakdown for pay_type='monthly' rows.

    Returned by `compute_pay_type_breakdown` for UI echo + audit logging.
    `retirement_burden_krw` is the COMPANY-BURDEN portion of
    `retirement_reserve_krw` (= `retirement_reserve_krw × company_burden_rate`).
    The user-entered `retirement_reserve_krw` is the employee-side reserve.
    """

    base_krw: int
    overtime_krw: int
    welfare_krw: int
    bonus_krw: int
    retirement_reserve_krw: int
    retirement_burden_krw: int
    company_burden_rate: Decimal
    total_krw: int


def compute_pay_type_breakdown(
    monthly_salary_basis_krw: int,
    overtime_krw: int,
    welfare_krw: int,
    bonus_krw: int,
    retirement_reserve_krw: int,
    company_burden_rate: Decimal,
) -> PayTypeBreakdown:
    """Compute PRD §6.1 인건비 breakdown (pay_type='monthly' rows).

    Formula (PRD §6.1):
        total_krw = base_krw + overtime_krw + welfare_krw + bonus_krw
                  + retirement_reserve_krw × company_burden_rate

    Args:
        monthly_salary_basis_krw: Base monthly salary in KRW (>= 0).
        overtime_krw: Overtime pay in KRW (>= 0).
        welfare_krw: Welfare benefits in KRW (>= 0).
        bonus_krw: Bonus in KRW (>= 0).
        retirement_reserve_krw: Employee-side retirement reserve (>= 0).
        company_burden_rate: Decimal in [0, 1] — 4대보험·퇴직 회사부담 비율.

    Returns:
        `PayTypeBreakdown` with all fields populated + `total_krw` rounded
        to integer KRW (ROUND_HALF_EVEN).

    Raises:
        ValueError: any KRW input is negative or `company_burden_rate`
        is outside [0, 1].
    """
    for name, val in (
        ("monthly_salary_basis_krw", monthly_salary_basis_krw),
        ("overtime_krw", overtime_krw),
        ("welfare_krw", welfare_krw),
        ("bonus_krw", bonus_krw),
        ("retirement_reserve_krw", retirement_reserve_krw),
    ):
        if not isinstance(val, int) or val < 0:
            raise ValueError(f"{name} must be a non-negative int, got {val!r}")
    if not isinstance(company_burden_rate, Decimal):
        company_burden_rate = Decimal(str(company_burden_rate))
    if company_burden_rate < 0 or company_burden_rate > 1:
        raise ValueError(f"company_burden_rate must be in [0, 1], got {company_burden_rate}")

    retirement_burden_raw = Decimal(retirement_reserve_krw) * company_burden_rate
    retirement_burden_krw = int(
        retirement_burden_raw.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    )
    total_raw = (
        Decimal(monthly_salary_basis_krw)
        + Decimal(overtime_krw)
        + Decimal(welfare_krw)
        + Decimal(bonus_krw)
        + retirement_burden_raw
    )
    total_krw = int(total_raw.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))

    return PayTypeBreakdown(
        base_krw=monthly_salary_basis_krw,
        overtime_krw=overtime_krw,
        welfare_krw=welfare_krw,
        bonus_krw=bonus_krw,
        retirement_reserve_krw=retirement_reserve_krw,
        retirement_burden_krw=retirement_burden_krw,
        company_burden_rate=company_burden_rate,
        total_krw=total_krw,
    )


# ── FTE computation (re-exported from stream_completion with payroll) ─
def compute_fte_for_daily(
    workers: int,
    days_per_worker: int,
    payroll: PayrollSettings = DEFAULT_PAYROLL,
) -> Decimal:
    """FTE headcount for pay_type='daily' rows.

    Formula: `workers × days_per_worker / payroll.workdays_in_month`,
    rounded to 2 dp with `ROUND_HALF_EVEN`. Wraps `stream_completion.format_fte_headcount`
    with `payroll.workdays_in_month` injected so a tenant override takes
    effect without changing the lower-level pure function.

    Args:
        workers: Number of 일용직 workers (>= 0).
        days_per_worker: Days each worker worked (>= 0).
        payroll: Effective payroll settings (defaults to PRD).

    Returns:
        Decimal rounded to 2 places. `Decimal("0.00")` if any input is 0/negative.
    """
    if workers <= 0 or days_per_worker <= 0 or payroll.workdays_in_month <= 0:
        return Decimal("0.00")
    raw = Decimal(workers) * Decimal(days_per_worker) / Decimal(payroll.workdays_in_month)
    return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def compute_fte_for_monthly(workers: int) -> Decimal:
    """FTE headcount for pay_type='monthly' rows.

    Monthly mode is already normalized (정규직 = 정직원); FTE = workers as-is.
    No 환산 applied. Rounded to 2 dp (consistency with daily path).

    Args:
        workers: Number of 정규직 workers (>= 0).

    Returns:
        Decimal("X.00") rounded. `Decimal("0.00")` if workers <= 0.
    """
    if workers <= 0:
        return Decimal("0.00")
    return Decimal(workers).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def compute_fte_wage_for_daily(
    daily_wage_krw: int,
    workers: int,
    days_per_worker: int,
) -> int:
    """FTE wage for pay_type='daily' rows — DIRECT SUM (NOT basis 환산).

    Formula: `daily_wage_krw × workers × days_per_worker` (rounded to integer
    KRW, ROUND_HALF_EVEN). This is **DIFFERENT from Story 3.1's
    `compute_fte_wage_krw`** which multiplied `fte_headcount ×
    monthly_salary_basis_krw` (basis 환산, used for monthly mode only).

    The daily path uses the user's actual daily wage directly. The monthly
    basis 환산 is reserved for monthly mode where there's no natural
    per-day wage to multiply.

    Args:
        daily_wage_krw: Per-day wage per worker (>= 0).
        workers: Number of 일용직 workers (>= 0).
        days_per_worker: Days each worker worked (>= 0).

    Returns:
        Integer KRW (>= 0). `0` if any input is 0/negative.

    Raises:
        ValueError: any input is negative (defense vs `_compute_fte_for_daily`
        which silently returns 0).
    """
    if any(v < 0 for v in (daily_wage_krw, workers, days_per_worker)):
        raise ValueError(
            f"daily_wage_krw/workers/days_per_worker must be non-negative, "
            f"got ({daily_wage_krw}, {workers}, {days_per_worker})"
        )
    if daily_wage_krw == 0 or workers == 0 or days_per_worker == 0:
        return 0
    raw = Decimal(daily_wage_krw) * Decimal(workers) * Decimal(days_per_worker)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def compute_fte_wage_for_monthly(
    workers: int,
    breakdown: PayTypeBreakdown,
) -> int:
    """FTE wage for pay_type='monthly' rows.

    Formula: `workers × breakdown.total_krw` (basis 환산). The breakdown
    already aggregates the per-worker monthly cost, so multiplying by
    `workers` gives the total monthly wage.

    Args:
        workers: Number of 정규직 workers (>= 0).
        breakdown: Output of `compute_pay_type_breakdown`.

    Returns:
        Integer KRW (>= 0). `0` if workers == 0.
    """
    if workers <= 0:
        return 0
    raw = Decimal(workers) * Decimal(breakdown.total_krw)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


# ── Daily-mode rollup ───────────────────────────────────────
def rollup_daily_fte(
    per_day: list[tuple[Decimal, int]],
) -> tuple[Decimal, int]:
    """Roll up per-day FTE values to month-total (sum, NOT average).

    Used when `mode='daily'` — reads all 31 `day_no` rows and sums.

    Args:
        per_day: List of `(fte_headcount, fte_wage_krw)` per day.
            Empty list is allowed (returns zeros).

    Returns:
        `(total_fte, total_wage)` — both summed, no rounding adjustment
        (per-day values are already rounded by their respective callers).
    """
    total_fte = sum((d[0] for d in per_day), Decimal("0"))
    total_wage = sum((d[1] for d in per_day), 0)
    # Ensure result is 2 dp quantized for consistency.
    total_fte = total_fte.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return total_fte, total_wage


# ── Composition ──────────────────────────────────────────────
@dataclass(frozen=True)
class FteDisplay:
    """Read-only display payload for the [인원] tab.

    Echoed back by the API in `MonthlyInputStateResponse.fte_display`.
    `source_rows` makes the daily-rollup vs month-total-mode visible to
    the frontend (and to Epic 4 calc engine consumers).

    `breakdown` is populated only for pay_type='monthly' rows.
    For pay_type='daily' rows, `breakdown` is None (the direct sum path
    doesn't need the per-field breakdown).
    """

    pay_type: PayType
    fte_headcount: Decimal
    fte_wage_krw: int
    breakdown: dict[str, int] | None
    source_rows: int  # 1 for month_total mode, 1..31 for daily mode


def build_fte_display(
    pay_type: PayType,
    workers: int,
    days_per_worker: int | None,
    daily_wage_krw: int | None,
    monthly_salary_basis_krw: int | None,
    overtime_krw: int | None,
    welfare_krw: int | None,
    bonus_krw: int | None,
    retirement_reserve_krw: int | None,
    company_burden_rate: Decimal | None,
    payroll: PayrollSettings,
    source_rows: int,
) -> FteDisplay:
    """Compose `FteDisplay` from raw row inputs.

    Dispatches by `pay_type`:
    - 'monthly' → breakdown path (5 fields + company_burden_rate)
    - 'daily' → direct-sum path (3 fields)

    Returns an `FteDisplay` ready for the API response.

    Args:
        pay_type: 'monthly' or 'daily'.
        workers: Number of workers (>= 0).
        days_per_worker: For 'daily' (>= 0); None for 'monthly'.
        daily_wage_krw: For 'daily' (>= 0); None for 'monthly'.
        monthly_salary_basis_krw: For 'monthly' (>= 0); None for 'daily'.
        overtime_krw/welfare_krw/bonus_krw/retirement_reserve_krw:
            For 'monthly' (>= 0); None for 'daily'.
        company_burden_rate: For 'monthly'; None for 'daily'.
        payroll: Effective payroll settings.
        source_rows: 1 for month_total mode, 1..31 for daily mode.

    Returns:
        `FteDisplay` instance.

    Raises:
        ValueError: on negative inputs (defense).
    """
    if workers < 0:
        raise ValueError(f"workers must be non-negative, got {workers}")

    if pay_type == PayType.DAILY:
        if days_per_worker is None or days_per_worker < 0:
            raise ValueError(f"days_per_worker required for daily, got {days_per_worker}")
        if daily_wage_krw is None or daily_wage_krw < 0:
            raise ValueError(f"daily_wage_krw required for daily, got {daily_wage_krw}")
        fte_headcount = compute_fte_for_daily(workers, days_per_worker, payroll)
        fte_wage_krw = compute_fte_wage_for_daily(daily_wage_krw, workers, days_per_worker)
        return FteDisplay(
            pay_type=PayType.DAILY,
            fte_headcount=fte_headcount,
            fte_wage_krw=fte_wage_krw,
            breakdown=None,
            source_rows=source_rows,
        )

    if pay_type == PayType.MONTHLY:
        if monthly_salary_basis_krw is None or monthly_salary_basis_krw < 0:
            raise ValueError(
                f"monthly_salary_basis_krw required for monthly, " f"got {monthly_salary_basis_krw}"
            )
        rate = (
            company_burden_rate if company_burden_rate is not None else payroll.company_burden_rate
        )
        breakdown = compute_pay_type_breakdown(
            monthly_salary_basis_krw=monthly_salary_basis_krw,
            overtime_krw=overtime_krw or 0,
            welfare_krw=welfare_krw or 0,
            bonus_krw=bonus_krw or 0,
            retirement_reserve_krw=retirement_reserve_krw or 0,
            company_burden_rate=rate,
        )
        fte_headcount = compute_fte_for_monthly(workers)
        fte_wage_krw = compute_fte_wage_for_monthly(workers, breakdown)
        return FteDisplay(
            pay_type=PayType.MONTHLY,
            fte_headcount=fte_headcount,
            fte_wage_krw=fte_wage_krw,
            breakdown={
                "base_krw": breakdown.base_krw,
                "overtime_krw": breakdown.overtime_krw,
                "welfare_krw": breakdown.welfare_krw,
                "bonus_krw": breakdown.bonus_krw,
                "retirement_reserve_krw": breakdown.retirement_reserve_krw,
                "retirement_burden_krw": breakdown.retirement_burden_krw,
                "total_krw": breakdown.total_krw,
            },
            source_rows=source_rows,
        )

    raise ValueError(f"Unknown pay_type: {pay_type!r}")
