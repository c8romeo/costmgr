"""packages.cost_engine.core.period_cost — §6.1 원가 산식 체인 pure kernel.

AD-1:  Hexagonal core. Pure domain logic; ports for inbound; adapters at boundary.
AD-5:  Engine purity — no I/O, no DB, no clock, no random, no global state, no logs.
AD-8:  Monetary types — KRW = `int` (BIGINT in DB); USD = `Decimal` 2dp; `float` forbidden.
AD-11: `core` MUST NOT import `packages.cost_engine.adapters`. Enforced by import-linter.
AD-15: snake_case, ROUND_HALF_EVEN banker's rounding on KRW arithmetic.
AD-16: result_hash = sha256(stable_json_dumps(immutable_input_snapshot)) — V8 1원 단위 회귀.
AD-22: append-only-leaning — engine returns `state="draft"` ONLY. Service layer owns
       `verified`/`committed`/`reversed` transitions via append-only events. Engine
       NEVER writes to DB; engine NEVER authorizes reversal (M11 owns, Epic 11).

Pure kernel. NO writes, NO reads, NO clock. State transitions live in
`apps/api/modules/m3_calculate/services/calc_orchestrator.py` (Story 4-2).

8-stage 산식 체인 (PRD §6.1 (1)~(8)) — 각 stage는 명명 helper:
  - _stage1_material / _stage2_labor / _stage3_overhead
  - _stage4_material_pct / _stage5_labor_pct / _stage6_overhead_pct
  - _stage7_inventory_adjustment / _stage8_manufacturing_cost
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING, Final
from uuid import UUID

from packages.cost_engine.core.money import KRW
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput

if TYPE_CHECKING:
    pass  # Baseline is defined here; no forward refs needed.


# ── Constants ────────────────────────────────────────────────
# AD-15: Period key format YYYY-MM (AD-24 typed period key).
_PERIOD_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Banker's rounding decimal place for KRW final output (int precision).
_QUANTIZE_KRW: Final[Decimal] = Decimal("1")

# Info-only percentage decimal place (Stage 4-6, V4 verification source).
_QUANTIZE_PCT: Final[Decimal] = Decimal("0.01")

# Deterministic state invariant — engine ALWAYS returns draft (AD-22).
_DRAFT_STATE: Final[str] = "draft"


# ── Baseline ────────────────────────────────────────────────
@dataclass(frozen=True)
class Baseline:
    """Pure input value object for the calculation gate (PRD §F0.2 / §F1.1).

    `bom_ratio_validated`:  True iff BOM matrix for all relevant products
        sums to 100% (Story 2.2 gate). Engine rejects if False.
    `allocation_basis_set`: True iff 3 allocation basis (직접/간접 계정,
        고정/변동 분류, 동인 정의) are registered (Story 1.2 gate).
        Engine rejects if False.

    The engine is defense-in-depth: service layer is the canonical
    validator, but the engine also rejects to make the invariant
    explicit in pure-function tests.
    """

    fiscal_period: str  # YYYY-MM (same as monthly_input.period_key)
    standard_monthly_hours: int  # PRD §6.1 (2) — FTE 환산 분모
    bom_ratio_validated: bool = True
    allocation_basis_set: bool = True


# ── 8-stage 산식 체인 ────────────────────────────────────────
def _stage1_material(direct_material_krw: KRW, baseline: Baseline) -> KRW:
    """PRD §6.1 (1) 직접재료 — BOM 100% 검증 통과 시 그대로 사용."""
    if not baseline.bom_ratio_validated:
        raise ValueError("BOM 비중 합 100% 검증 실패 — [계산] 잠금 상태 (PRD §F1.1)")
    return direct_material_krw


def _stage2_labor(direct_labor_krw: KRW, fte_headcount: Decimal, baseline: Baseline) -> KRW:
    """PRD §6.1 (2) 직접노무 — direct_labor × fte_headcount 환산.

    `standard_monthly_hours`는 baseline에 보존되지만 본 stage에서는 사용 안 함
    (Story 3.2의 FTE 환산이 이미 standard_monthly_hours를 흡수). service layer가
    `_load_baseline()`에서 fte_headcount 계산 시 `tenant_settings.payroll.*`
    override 활용 (Story 3.2 패턴).
    """
    _ = baseline  # 명시적 unused — 시그니처 일관성
    product = (Decimal(direct_labor_krw) * fte_headcount).quantize(
        _QUANTIZE_KRW, rounding=ROUND_HALF_EVEN
    )
    if product != int(product):
        # ROUND_HALF_EVEN이 int 보장하지만 safety net
        raise ValueError(f"labor_cost not int after quantize: {product}")
    return KRW(int(product))


def _stage3_overhead(indirect_krw: KRW, baseline: Baseline) -> KRW:
    """PRD §6.1 (3) 제조간접 — 배부기준 3종 검증 후 그대로 사용."""
    if not baseline.allocation_basis_set:
        raise ValueError("배부기준 3종 미완료 — [계산] 잠금 상태 (PRD §F0.2)")
    return indirect_krw


def _stage4_material_pct(material_cost: KRW, mfg_cost: KRW) -> Decimal:
    """PRD §6.1 (4) 직접재료 비율 — material_cost / mfg_cost × 100."""
    if mfg_cost == 0:
        return Decimal("0.00")
    return (Decimal(material_cost) / Decimal(mfg_cost) * Decimal("100")).quantize(
        _QUANTIZE_PCT, rounding=ROUND_HALF_EVEN
    )


def _stage5_labor_pct(labor_cost: KRW, mfg_cost: KRW) -> Decimal:
    """PRD §6.1 (5) 직접노무 비율 — labor_cost / mfg_cost × 100."""
    if mfg_cost == 0:
        return Decimal("0.00")
    return (Decimal(labor_cost) / Decimal(mfg_cost) * Decimal("100")).quantize(
        _QUANTIZE_PCT, rounding=ROUND_HALF_EVEN
    )


def _stage6_overhead_pct(overhead_cost: KRW, mfg_cost: KRW) -> Decimal:
    """PRD §6.1 (6) 제조간접 비율 — overhead_cost / mfg_cost × 100."""
    if mfg_cost == 0:
        return Decimal("0.00")
    return (Decimal(overhead_cost) / Decimal(mfg_cost) * Decimal("100")).quantize(
        _QUANTIZE_PCT, rounding=ROUND_HALF_EVEN
    )


def _stage7_inventory_adjustment() -> KRW:
    """PRD §6.1 (7) 기말재고 조정 — Epic 5 inventory_ledger fold-in 진입점.

    본 Story 4.1 범위: KRW(0) 고정 반환 + TODO(epic-5) marker.
    Epic 5 Story 5-1 (auto-carry) + 5-2 (append-only ledger) 진입 시
    `LEDGER_REFERENCE_QUERY_STUB` swap + `monthly_input_periods.opening_inventory`
    활용 방식으로 교체. Epic 3.3 inline projection 패턴 그대로.
    """
    # TODO(epic-5): swap to ledger-driven adjustment once inventory_ledger lands.
    return KRW(0)


def _stage8_manufacturing_cost(material_cost: KRW, labor_cost: KRW, overhead_cost: KRW) -> KRW:
    """PRD §6.1 (8) 제조원가 합계 — 정수 합 (이미 모두 KRW int)."""
    return KRW(int(material_cost) + int(labor_cost) + int(overhead_cost))


# ── Stable JSON for result_hash ─────────────────────────────
def _stable_json_dumps(obj: object) -> str:
    """Stable JSON serialize — key sort, Decimal → str (full precision).

    CR 1.1 lesson — immutable input snapshot must hash identically across
    runs / Python versions / OS platforms.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _compute_result_hash(
    *,
    tenant_id: UUID,
    period_key: str,
    baseline: Baseline,
    material_cost: int,
    labor_cost: int,
    overhead_cost: int,
    manufacturing_cost: int,
) -> str:
    """SHA-256 hex 64자 — V8 1원 단위 회귀 가능 결정론.

    Inventory_adjustment은 Epic 5 fold-in 전(hash 제외)이라 snapshot 미포함.
    hash에 포함: tenant_id + period_key + fiscal_period + standard_monthly_hours
    + 4개 cost 필드 (모두 int KRW).
    """
    snapshot = {
        "tenant_id": str(tenant_id),
        "period_key": period_key,
        "fiscal_period": baseline.fiscal_period,
        "standard_monthly_hours": baseline.standard_monthly_hours,
        "material_cost": material_cost,
        "labor_cost": labor_cost,
        "overhead_cost": overhead_cost,
        "manufacturing_cost": manufacturing_cost,
    }
    return hashlib.sha256(_stable_json_dumps(snapshot).encode("utf-8")).hexdigest()


# ── Input validation ─────────────────────────────────────────
def _validate_inputs(monthly_input: MonthlyInput, baseline: Baseline) -> None:
    """Engine-side defense-in-depth for input invariants.

    Service layer is the canonical validator. Engine re-checks to make
    invariants explicit in pure-function tests (Story 4.1 spec T1.4 +
    T2.1 test_negative_input_rejected).
    """
    if int(monthly_input.direct_material_krw) < 0:
        raise ValueError(
            f"direct_material_krw must be >= 0, got {monthly_input.direct_material_krw}"
        )
    if int(monthly_input.direct_labor_krw) < 0:
        raise ValueError(f"direct_labor_krw must be >= 0, got {monthly_input.direct_labor_krw}")
    if int(monthly_input.indirect_krw) < 0:
        raise ValueError(f"indirect_krw must be >= 0, got {monthly_input.indirect_krw}")
    if monthly_input.fte_headcount < Decimal("0"):
        raise ValueError(f"fte_headcount must be >= 0, got {monthly_input.fte_headcount}")
    if not _PERIOD_KEY_PATTERN.match(monthly_input.period_key):
        raise ValueError(f"period_key must match YYYY-MM (AD-24), got {monthly_input.period_key!r}")
    if not _PERIOD_KEY_PATTERN.match(baseline.fiscal_period):
        raise ValueError(
            f"baseline.fiscal_period must match YYYY-MM (AD-24), got {baseline.fiscal_period!r}"
        )
    if baseline.standard_monthly_hours <= 0:
        raise ValueError(
            f"baseline.standard_monthly_hours must be > 0, got {baseline.standard_monthly_hours}"
        )


# ── Public entry point ───────────────────────────────────────
def compute_period_cost(monthly_input: MonthlyInput, baseline: Baseline) -> CalcResult:
    """§6.1 8단계 산식 체인 pure function.

    AD-5 invariants:
      - Same (monthly_input, baseline) → byte-identical CalcResult 100/100 (V8).
      - NO I/O, NO DB, NO clock, NO random, NO global state.
      - `state` is ALWAYS `"draft"` (AD-22 — service layer owns transitions).

    Args:
        monthly_input: Tenant-scoped monthly state from M2 input adapter.
            Contains: tenant_id, period_key, direct_material/labor/indirect_krw,
            fte_headcount (Story 3.2).
        baseline: Tenant-scoped calculation gate (PRD §F0.2 + §F1.1).
            Contains: fiscal_period, standard_monthly_hours, BOM validation
            flag, allocation basis flag.

    Returns:
        CalcResult with all KRW fields as `int`, `result_hash` as 64-char
        hex SHA-256, `state="draft"` invariant.

    Raises:
        ValueError: On negative KRW, invalid period_key, BOM / allocation
            gate failure, or non-positive standard_monthly_hours.
    """
    _validate_inputs(monthly_input, baseline)

    # 8-stage 산식 체인
    material_cost = _stage1_material(monthly_input.direct_material_krw, baseline)
    labor_cost = _stage2_labor(
        monthly_input.direct_labor_krw, monthly_input.fte_headcount, baseline
    )
    overhead_cost = _stage3_overhead(monthly_input.indirect_krw, baseline)
    inventory_adjustment = _stage7_inventory_adjustment()
    manufacturing_cost = _stage8_manufacturing_cost(material_cost, labor_cost, overhead_cost)

    # Info-only percentages (V4 verification source — not in CalcResult schema)
    # 명시적 호출하여 V4 검증 시점에 동일 결과 보장
    _ = (
        _stage4_material_pct(material_cost, manufacturing_cost),
        _stage5_labor_pct(labor_cost, manufacturing_cost),
        _stage6_overhead_pct(overhead_cost, manufacturing_cost),
    )

    result_hash = _compute_result_hash(
        tenant_id=monthly_input.tenant_id,
        period_key=monthly_input.period_key,
        baseline=baseline,
        material_cost=int(material_cost),
        labor_cost=int(labor_cost),
        overhead_cost=int(overhead_cost),
        manufacturing_cost=int(manufacturing_cost),
    )

    return CalcResult(
        tenant_id=monthly_input.tenant_id,
        period_key=monthly_input.period_key,
        material_cost=material_cost,
        labor_cost=labor_cost,
        overhead_cost=overhead_cost,
        manufacturing_cost=manufacturing_cost,
        inventory_adjustment=inventory_adjustment,
        result_hash=result_hash,
        state=_DRAFT_STATE,  # AD-22 invariant — engine returns draft ONLY
    )
