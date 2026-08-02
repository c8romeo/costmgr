"""apps.api.modules.m3_calculate.services.rules.v1_complete_allocation — V1 rule kernel.

Story 4.3 (Task 1.3) — V1: 완전배부 (PRD §11).

V1 checks that the manufacturing cost equals the sum of the 3 input costs:
    manufacturing_cost == direct_material_krw + direct_labor_krw + indirect_krw

AD-15 banker's rounding tolerance: |delta| ≤ KRW(1) (1원 단위).
Engine's `_stage8_manufacturing_cost` is KRW int sum so the delta
should be exactly 0 in practice. KRW(1) tolerance absorbs any
int↔Decimal boundary effects (defense in depth).

AD-5 purity: no DB, no clock, no I/O. Pure functional kernel.
AD-12 ordering: V1 is first in `_VERIFICATION_RULES`. If V1 fails,
V4·V7·V8 abort (rule registry `_VERIFICATION_RULES` iteration break).
"""

from __future__ import annotations

from typing import Literal

from apps.api.modules.m3_calculate.services.rules.protocol import (
    RuleInput,
    VerificationItem,
)

# AD-15 1원 단위 tolerance — Story 4.3 AC #2.
# Engine produces integer KRW (int + int + int) so the delta SHOULD be
# exactly 0. KRW(1) tolerance absorbs edge cases from decimal→int
# coercion that may emerge if Epic 5 fold-in changes the calc chain.
_V1_DELTA_TOLERANCE_KRW: int = 1


class V1CompleteAllocationRule:
    """V1 — 완전배부 invariant (PRD §11 V-row).

    Per-industry firing: ALL industries (universal 1원 단위 invariant).
    """

    @property
    def name(self) -> Literal["V1"]:
        return "V1"

    def applies_to(self, *, industry: str) -> bool:
        # V1 fires for every industry — the 1원 단위 invariant is universal.
        return True

    def check(self, input: RuleInput) -> VerificationItem:
        """Pure check. Returns passed if `manufacturing_cost - sum(3 inputs)` ≤ 1원."""
        mc = int(input.calc_result.manufacturing_cost)
        material = int(input.calc_result.material_cost)
        labor = int(input.calc_result.labor_cost)
        overhead = int(input.calc_result.overhead_cost)

        delta_krw = mc - (material + labor + overhead)
        tolerance = _V1_DELTA_TOLERANCE_KRW

        if abs(delta_krw) <= tolerance:
            return VerificationItem(
                code="V1",
                status="passed",
                message_ko=(
                    f"완전배부 정상 (제조원가 KRW {mc:,} = "
                    f"재료비 KRW {material:,} + 노무비 KRW {labor:,} + "
                    f"제조경비 KRW {overhead:,})"
                ),
                details={"delta_krw": delta_krw},
            )

        return VerificationItem(
            code="V1",
            status="failed",
            message_ko=(
                f"완전배부 위반 (KRW {delta_krw:,} 차이 — "
                f"제조원가 KRW {mc:,} ≠ "
                f"3요소 합 KRW {material + labor + overhead:,})"
            ),
            details={"delta_krw": delta_krw},
        )


__all__ = ["V1CompleteAllocationRule"]
