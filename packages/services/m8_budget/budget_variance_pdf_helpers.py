"""packages.services.m8_budget.budget_variance_pdf_helpers — Story 8.2 PDF envelope.

Budget-actual variance PDF envelope builder for Epic 6 M5 PDF generator
reuse (READ-ONLY pattern, no audit emit). PDF wire는 8-3 honestly DEFER
(sprint-scale) — 본 모듈은 envelope SSOT + placeholder만 제공.

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m8_budget.budget_variance_pdf_helpers`
registered in `tests/architecture/test_api_calls_only_ports.py` (T7 wire).
"""

from __future__ import annotations

from packages.cost_engine.budget_variance import (
    ABCD_DISABLED_NOTE,
    compute_abcd_disabled_badge,
)
from packages.services.m8_budget.budget_variance_serializers import (
    serialize_abcd_disabled_badge,
    serialize_variance_row,
    serialize_variance_total,
)


def serialize_budget_variance_pdf_envelope(
    *,
    period_key: str,
    scenario_index: int,
    rows: list,
    total_row,
    generated_at_kst: str,
) -> dict[str, object]:
    """Build PRD §F8.2 + Epic 6 M5 envelope for variance PDF (8-3 honestly DEFER).

    Epic 6 M5 PDF generator reuse pattern (READ-ONLY, no audit emit).
    envelope 형식:
      {
        "report_code": "BUDGET_VARIANCE",
        "title": "예산-실적 대조표",
        "period_key": str,
        "scenario_index": int,
        "rows": [serialized variance rows],
        "total_row": serialized total row,
        "abcd_disabled_badge": serialized ABCDDisabledBadge,
        "abcd_disabled_note": str,
        "generated_at_kst": str,
      }

    PDF 형식 (8-3 follow-up sprint):
      - A4 portrait + KRW 정수 (AD-17 BigInteger parity) + ko-KR only (NFR18)
      - 4컬럼 (예산 / 실적 / 차액 / 차이율 %) + 5번째 ABCD 회색 배지
      - 비고란 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]"

    8-2 wire: envelope SSOT + abcd_disabled_badge placeholder만.
    8-3 follow-up sprint: generate_budget_variance_pdf() 메소드 wire.
    """
    badge = compute_abcd_disabled_badge(variant="variance")
    return {
        "report_code": "BUDGET_VARIANCE",
        "title": "예산-실적 대조표",
        "period_key": str(period_key),
        "scenario_index": int(scenario_index),
        "rows": [serialize_variance_row(r) for r in rows],
        "total_row": serialize_variance_total(total_row),
        "abcd_disabled_badge": serialize_abcd_disabled_badge(badge),
        "abcd_disabled_note": ABCD_DISABLED_NOTE,
        "generated_at_kst": str(generated_at_kst),
        # Epic 6 M5 PDF generator reuse hint (8-3 follow-up)
        "_pdf_format": "A4 portrait + KRW integer + ko-KR only (NFR18)",
    }


__all__ = [
    "serialize_budget_variance_pdf_envelope",
]
