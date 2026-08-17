"""apps.api.modules.m5_reports.schemas — M5 reports Pydantic models (Story 9.4).

Story 9.4 (Epic 9 4번째 진입점) Pydantic v2 schemas for Report #21:

  - Report21Request: GET /api/v1/reports/21 query params body
  - Report21Response: GET /api/v1/reports/21 200 OK response
  - Report21PdfRequest: POST /api/v1/reports/21/pdf body
  - Report21PdfResponse: POST /api/v1/reports/21/pdf 200 OK response

All schemas use `extra="forbid"` per AD-15 §1.
PRD §9 #21 + §7.3 (법인세법 시행규칙 제76조 2기준) verbatim wire.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Report #21 GET ──────────────────────────────────────────────


class Report21Request(BaseModel):
    """Query params for GET /api/v1/reports/21 (Story 9.4).

    `period_key` = 회계기간 키 ("YYYY-Q1/Q2/Q3/Q4" or "YYYY-MM").
    PRD §9 #21 + §7.3 — 원가대상별 원가 집계표 GET 진입점.
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(..., min_length=1, max_length=20)


class Report21CostObjectRow(BaseModel):
    """Report #21 Cost Object Breakdown row (PRD §9 #21 + §F9.2).

    `product_id` = 원가대상 식별자
    `activity_id` = 활동 식별자
    `driver_id` = 동인 식별자
    `allocated_krw` = str (Decimal-as-string AD-8)
    """

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(..., min_length=1, max_length=64)
    activity_id: str = Field(..., min_length=1, max_length=64)
    driver_id: str = Field(..., min_length=1, max_length=64)
    allocated_krw: str = Field(..., min_length=1)


class Report21UnusedCapacityRow(BaseModel):
    """Report #21 unused capacity row (PRD §A9 verbatim).

    `department_id` = 부서 식별자
    `unused_hours` = str (Decimal-as-string AD-8)
    `unused_cost_krw` = str (Decimal-as-string AD-8)
    """

    model_config = ConfigDict(extra="forbid")

    department_id: str = Field(..., min_length=1, max_length=64)
    unused_hours: str = Field(..., min_length=1)
    unused_cost_krw: str = Field(..., min_length=1)


class Report21Response(BaseModel):
    """200 OK response for GET /api/v1/reports/21 (Story 9.4).

    `period_key` = 회계기간 키
    `cost_object_breakdown` = list[Report21CostObjectRow]
    `unused_capacity_breakdown` = list[Report21UnusedCapacityRow]
    `v7_verdict_is_balanced` = bool (Σ breakdown + unused = Σ department cost)
    `generation_hash` = "sha256:..." (V8 byte-equality)
    `report_code` = Literal["COST_OBJECT_BREAKDOWN"]
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str
    cost_object_breakdown: list[Report21CostObjectRow]
    unused_capacity_breakdown: list[Report21UnusedCapacityRow]
    v7_verdict_is_balanced: bool
    generation_hash: str = Field(..., min_length=len("sha256:") + 64, max_length=len("sha256:") + 64)
    report_code: Literal["COST_OBJECT_BREAKDOWN"] = "COST_OBJECT_BREAKDOWN"


# ── Report #21 POST PDF ──────────────────────────────────────────


class Report21PdfRequest(BaseModel):
    """Body of POST /api/v1/reports/21/pdf (Story 9.4).

    `period_key` = 회계기간 키 ("YYYY-Q1/Q2/Q3/Q4" or "YYYY-MM").
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(..., min_length=1, max_length=20)


class Report21PdfResponse(BaseModel):
    """200 OK response for POST /api/v1/reports/21/pdf (Story 9.4).

    `period_key` = 회계기간 키
    `pdf_base64` = str (Base64-encoded PDF bytes, AD-15 cross-language)
    `size_bytes` = int (len(pdf_bytes))
    `generation_hash` = "sha256:..." (V8 byte-equality)
    `report_code` = Literal["COST_OBJECT_BREAKDOWN"]
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str
    pdf_base64: str = Field(..., min_length=1)
    size_bytes: int = Field(..., ge=0)
    generation_hash: str = Field(..., min_length=len("sha256:") + 64, max_length=len("sha256:") + 64)
    report_code: Literal["COST_OBJECT_BREAKDOWN"] = "COST_OBJECT_BREAKDOWN"


__all__ = [
    "Report21Request",
    "Report21CostObjectRow",
    "Report21UnusedCapacityRow",
    "Report21Response",
    "Report21PdfRequest",
    "Report21PdfResponse",
]
