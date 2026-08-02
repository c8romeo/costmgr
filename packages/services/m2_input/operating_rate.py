"""packages.services.m2_input.operating_rate — Story 3.3 operating rate (조업도).

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical operating-rate kernel consumed by
`apps/api/modules/m2_input/services/monthly_input_service.py` AND
mirrored by `apps/web/lib/l2-input-warnings.ts` (drift caught by
`tests/integration/test_m2_input_label_consistency.py`).

The module answers:
- "Given total FTE headcount and standard monthly hours, what's the
  total available work hours?" → `compute_total_available_hours`
- "Given production rows (qty per product), what's the required hours?"
  → `compute_production_required_hours` (qty × unit_time_hours)
- "Given available and required hours, what's the operating rate?"
  → `compute_operating_rate` (required / available × 100, 2dp ROUND_HALF_EVEN)

PRD §6.1 (2) 조업도 체인:
    총작업가능시간 = 총 FTE × 표준 월 근로시간
    생산요구시간 = Σ(생산수량 × 단위공수)
    조업도 = (생산요구시간 / 총작업가능시간) × 100

PRD §V5 한도: 조업도 > 100% → OVERCAPACITY_OPERATING_RATE warning.

MVP unit_time_hours:
- Default: 1.0h per product (PRD §6.1 "단위공수: 제품별 정의 우선
  → 생산유형 상속"). Story 2.1 BOM schema has no `unit_time_hours`
  column — Epic 7 BEP slider (Story 7-2) refines this.

AD-15 cross-language parity: snake_case Python ↔ camelCase TS.
Banker's rounding (ROUND_HALF_EVEN) on both sides.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, Protocol

# ── Constants ────────────────────────────────────────────────
# MVP default unit_time_hours per product. Epic 7 BEP (Story 7-2)
# will refine via per-product 단위공수 source.
DEFAULT_UNIT_TIME_HOURS: Final[Decimal] = Decimal("1.0")

# PRD §V5 한도: 100% 초과 시 OVERCAPACITY_OPERATING_RATE warning 발동.
# 100.00% 정확히 일치 (boundary) → no warning.
OPERATING_RATE_LIMIT_PCT: Final[Decimal] = Decimal("100")

# Decimal quantization for operating_rate_pct and hours.
PCT_QUANTUM: Final[Decimal] = Decimal("0.01")
HOURS_QUANTUM: Final[Decimal] = Decimal("0.01")


# ── Production row protocol ──────────────────────────────────
class _ProductionRowLike(Protocol):
    """Duck type for production-stream rows.

    Pure interface — no DB import. SQLAlchemy ORM `MonthlyInputRow`
    with `stream='production'` satisfies this structurally.
    """

    qty: Decimal | None


# ── compute_total_available_hours ────────────────────────────
def compute_total_available_hours(
    total_fte_headcount: Decimal,
    standard_monthly_hours: int,
) -> Decimal:
    """PRD §6.1 (2): total_fte × standard_monthly_hours.

    Args:
        total_fte_headcount: FTE 환산 결과 (Story 3.2 `compute_fte_for_*`).
        standard_monthly_hours: `tenant_settings.payroll.standard_monthly_hours`
            (default 228 per PRD §6.1).

    Returns:
        Decimal hours (2dp ROUND_HALF_EVEN). 0 if any input is 0.
    """
    if total_fte_headcount <= 0 or standard_monthly_hours <= 0:
        return Decimal("0.00")
    raw = total_fte_headcount * Decimal(standard_monthly_hours)
    return raw.quantize(HOURS_QUANTUM, rounding=ROUND_HALF_EVEN)


# ── compute_production_required_hours ────────────────────────
def compute_production_required_hours(
    production_rows: list[_ProductionRowLike],
    unit_time_hours: Decimal = DEFAULT_UNIT_TIME_HOURS,
) -> Decimal:
    """PRD §6.1 (2): Σ(production qty × unit_time_hours).

    Args:
        production_rows: rows where `stream='production'`.
        unit_time_hours: per-product 단위공수 (MVP default 1.0h).
            Epic 7 BEP (Story 7-2) will refine per product.

    Returns:
        Decimal hours (2dp ROUND_HALF_EVEN). 0 if no rows.
    """
    if not production_rows or unit_time_hours <= 0:
        return Decimal("0.00")
    total = sum(
        (row.qty for row in production_rows if row.qty is not None),
        Decimal("0"),
    )
    raw = total * unit_time_hours
    return raw.quantize(HOURS_QUANTUM, rounding=ROUND_HALF_EVEN)


# ── compute_operating_rate ───────────────────────────────────
def compute_operating_rate(
    available_hours: Decimal,
    required_hours: Decimal,
) -> Decimal:
    """PRD §6.1 (2) + §V5: operating_rate_pct = (required / available) × 100.

    Args:
        available_hours: `compute_total_available_hours` output.
        required_hours: `compute_production_required_hours` output.

    Returns:
        Decimal percent (2dp ROUND_HALF_EVEN). 0 if available_hours
        is 0 (defense — no division by zero).

    Note:
        PRD §V5 (합의 검증): 조업도 > 100% → OVERCAPACITY 발동.
        Caller (`build_operating_rate_warning`) is responsible for
        the threshold check, not this function.
    """
    if available_hours <= 0:
        return Decimal("0.00")
    if required_hours <= 0:
        return Decimal("0.00")
    pct = (required_hours / available_hours) * Decimal("100")
    return pct.quantize(PCT_QUANTUM, rounding=ROUND_HALF_EVEN)
