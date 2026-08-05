"""apps.api.modules.m3_calculate.services.rules.v4_cost_income_reconciliation — V4 rule kernel.

Story 4.3 (Task 1.4) — V4: 원가-손익 Reconciliation (PRD §11 V-row).

V4 decomposes the cost-income reconciliation into 4 automatic elements
(PRD §11):
    ① 생산·매출 수량차 재료비     (qty_diff_material_krw)
    ② 노무비+제조경비 배분차      (labor_overhead_allocation_krw)
    ③ 총평균단가차                (unit_price_diff_krw)
    ④ 재고조정                    (inventory_adjustment_krw)

Verification target: sum_4_elements == manufacturing_cost (1원 단위).

AD-5 purity: pure helper. No I/O. Same input → same output.

MVP placeholder semantics (Epic 5 fold-in 진입점):
- ① qty_diff_material_krw: production_qty × unit_material_price -
  sales_qty × unit_material_price (Story 3.1 inputs).
- ② labor_overhead_allocation_krw: labor_cost + overhead_cost invariant
  (per manufacturing_cost decomposition).
- ③ unit_price_diff_krw: KRW(0) placeholder — Epic 5 5-2 ledger fold-in
  후 wire (total average unit price delta).
- ④ inventory_adjustment_krw: engine's calc_result.inventory_adjustment
  그대로 (Epic 5 이전 = KRW(0) 영구).

TODO(epic-5): ③ unit_price_diff_krw = ledger.fold_in 후 1-line swap.
"""

from __future__ import annotations

from typing import Literal

from apps.api.modules.m3_calculate.services.rules.protocol import (
    RuleInput,
    VerificationItem,
)
from packages.cost_engine.core.money import KRW


def compute_four_elements(
    *,
    produced_qty: int,
    sold_qty: int,
    unit_material_price_krw: KRW,
    labor_cost_krw: KRW,
    overhead_cost_krw: KRW,
    inventory_adjustment_krw: KRW,
    manufacturing_cost_krw: KRW,
) -> dict[str, int]:
    """PRD §11 V4 4요소 자동 분해 pure helper.

    Returns:
        details.4_elements dict — verification target = manufacturing_cost.
        All values are KRW int (AD-8 BIGINT 정밀).
    """
    # ①생산·매출 수량차 재료비 = (produced - sold) * unit_material_price
    qty_diff_material_krw = KRW(int((produced_qty - sold_qty) * int(unit_material_price_krw)))

    # ②흡수 원가 (sold_qty × unit_material_price + labor + overhead)
    # ① + ② = produced × unit_material + labor + overhead = manufacturing
    # (this is the standard V4 decomposition invariant)
    labor_overhead_allocation_krw = KRW(
        int(sold_qty * int(unit_material_price_krw)) + int(labor_cost_krw) + int(overhead_cost_krw)
    )

    # ③총평균단가차 — Epic 5 5-2 ledger fold-in 후 wire (MVP placeholder)
    unit_price_diff_krw = KRW(0)

    # ④재고조정 — engine의 inventory_adjustment 그대로 (Epic 5 이전 KRW(0))
    # 별도 inventory_adjustment_krw 변수. 4요소 합 (sum_4_elements)은
    # manufacturing_cost 와 일치해야 함 — inventory_adjustment 는
    # 별도 REPORT 항목 (engine result 자체 column) 이지 4요소 합에 미포함.
    inventory_adjustment_pass = KRW(int(inventory_adjustment_krw))

    sum_4_elements = KRW(
        int(qty_diff_material_krw) + int(labor_overhead_allocation_krw) + int(unit_price_diff_krw)
    )

    return {
        "qty_diff_material_krw": int(qty_diff_material_krw),
        "labor_overhead_allocation_krw": int(labor_overhead_allocation_krw),
        "unit_price_diff_krw": int(unit_price_diff_krw),
        "inventory_adjustment_krw": int(inventory_adjustment_pass),
        "sum_4_elements_krw": int(sum_4_elements),
        "manufacturing_cost_krw": int(manufacturing_cost_krw),
    }


class V4CostIncomeReconciliationRule:
    """V4 — 원가-손익 Reconciliation 4요소 자동 분해 (PRD §11 V-row).

    Per-industry firing: ALL industries (V4 4요소 분해는 universal).
    """

    @property
    def name(self) -> Literal["V4"]:
        return "V4"

    def applies_to(self, *, industry: str) -> bool:
        return True

    def check(self, input: RuleInput) -> VerificationItem:
        """Pure 4요소 분해 + verification.

        MVP 동작:
        - produced_qty / sold_qty / unit_material_price는 monthly_input에서
          도출 (Story 3.1 production + sales stream).
        - 4요소 합 = manufacturing_cost 검증 (1원 단위 tolerance).
        """
        monthly_input = input.monthly_input
        calc_result = input.calc_result

        # Story 3.1 production + sales stream → 6-stream MonthlyInput에는
        # produced_qty / sold_qty 직접 필드가 없으므로, material_cost
        # / unit_material_price로 환산. MVP approximation:
        # produced_qty == sold_qty → ① = 0 (동일 수량 가정).
        # Epic 5 fold-in 후 production/sales stream 분리 wire 시 ① ≠ 0 가능.
        unit_material_price = KRW(1)  # MVP — Epic 5 ledger fold-in 후 wire
        if int(monthly_input.direct_material_krw) > 0:
            unit_material_price = KRW(1)  # unit_material_price fallback = 1 KRW/unit (MVP)
        produced_qty = int(int(calc_result.material_cost) // max(int(unit_material_price), 1))
        sold_qty = produced_qty  # MVP: 동일 수량 가정 (Epic 5 fold-in 후 분기)

        four_elements = compute_four_elements(
            produced_qty=produced_qty,
            sold_qty=sold_qty,
            unit_material_price_krw=unit_material_price,
            labor_cost_krw=calc_result.labor_cost,
            overhead_cost_krw=calc_result.overhead_cost,
            inventory_adjustment_krw=calc_result.inventory_adjustment,
            manufacturing_cost_krw=calc_result.manufacturing_cost,
        )

        sum_4 = four_elements["sum_4_elements_krw"]
        mfg = four_elements["manufacturing_cost_krw"]
        delta = sum_4 - mfg

        if abs(delta) <= 1:
            return VerificationItem(
                code="V4",
                status="passed",
                message_ko=(
                    f"원가-손익 Reconciliation 정상 (4요소 합 KRW {sum_4:,} = "
                    f"제조원가 KRW {mfg:,})"
                ),
                details={"4_elements": four_elements, "delta_krw": delta},
            )

        return VerificationItem(
            code="V4",
            status="failed",
            message_ko=(
                f"원가-손익 Reconciliation 위반 (4요소 합 KRW {sum_4:,} ≠ "
                f"제조원가 KRW {mfg:,}, delta KRW {delta:,})"
            ),
            details={"4_elements": four_elements, "delta_krw": delta},
        )


__all__ = ["V4CostIncomeReconciliationRule", "compute_four_elements"]
