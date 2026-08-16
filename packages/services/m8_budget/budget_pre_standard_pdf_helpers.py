"""packages.services.m8_budget.budget_pre_standard_pdf_helpers — Story 8.3 PDF envelope.

Budget pre-standard cost PDF envelope builder for Epic 6 M5 PDF generator
reuse (READ-ONLY pattern, no audit emit). PDF wire는 8-3 atomic wire에서
활성화 — 8-2 honestly DEFER placeholder 해소 (§9 #20 8-2 DEFER 해소).

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m8_budget.budget_pre_standard_pdf_helpers`
registered in `tests/architecture/test_api_calls_only_ports.py` (T3 wire).
"""

from __future__ import annotations

from packages.cost_engine.budget_pre_standard import PreStandardCost
from packages.cost_engine.budget_variance import compute_abcd_disabled_badge
from packages.services.m8_budget.budget_variance_serializers import (
    serialize_abcd_disabled_badge,
)


def serialize_budget_pre_standard_pdf_envelope(
    *,
    period_key: str,
    scenario_index: int,
    pre_standard_cost: PreStandardCost,
    generated_at_kst: str,
) -> dict[str, object]:
    """Build PRD §F8.3 + Epic 6 M5 envelope for pre-standard cost PDF.

    Epic 6 M5 PDF generator reuse pattern (READ-ONLY, no audit emit).
    envelope 형식:
      {
        "report_code": "BUDGET_PRE_STANDARD",
        "title": "예산 사전 표준원가 명세서",
        "period_key": str,
        "scenario_index": int,
        "material_cost": str,
        "labor_cost": str,
        "overhead_cost": str,
        "manufacturing_cost": str,
        "engine_type": str,
        "abcd_disabled_badge": serialized ABCDDisabledBadge,
        "abcd_disabled_note": str,
        "generated_at_kst": str,
        "_pdf_format": "A4 portrait + KRW integer + ko-KR only (NFR18)",
      }

    PDF 형식 (8-3 atomic wire):
      - A4 portrait + KRW 정수 (AD-17 BigInteger parity) + ko-KR only (NFR18)
      - 4컬럼 (직접재료 / 직접노무 / 제조경비 / 제조원가 합계) + ABCD 회색 배지
      - 비고란 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]"

    8-3 wire: envelope SSOT + abcd_disabled_badge placeholder 제공.
    PDF byte stream wire는 service layer에서 처리.
    """
    badge = compute_abcd_disabled_badge(variant="variance")
    return {
        "report_code": "BUDGET_PRE_STANDARD",
        "title": "예산 사전 표준원가 명세서",
        "period_key": str(period_key),
        "scenario_index": int(scenario_index),
        "material_cost": str(pre_standard_cost.material_cost),
        "labor_cost": str(pre_standard_cost.labor_cost),
        "overhead_cost": str(pre_standard_cost.overhead_cost),
        "manufacturing_cost": str(pre_standard_cost.manufacturing_cost),
        "engine_type": str(pre_standard_cost.engine_type),
        "abcd_disabled_badge": serialize_abcd_disabled_badge(badge),
        "abcd_disabled_note": "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]",
        "generated_at_kst": str(generated_at_kst),
        "_pdf_format": "A4 portrait + KRW integer + ko-KR only (NFR18)",
    }


__all__ = [
    "serialize_budget_pre_standard_pdf_envelope",
]