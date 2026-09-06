"""Story 30.1 CSV + 30.2 PDF export schemas (cj-282a + cj-293 wire sprints).

Pydantic schemas for Story 30.1 CSV export + Story 30.2 PDF export endpoints.

cj-282a wire sprint (cj-style 283번째) — Story 30.1 CSV export schemas 결정 wire.
cj-293 wire sprint (cj-style 293번째) — Story 30.2 PDF export schemas EXTENSION
결정 wire (CsvExportRequest mirror pattern verbatim).

- AD bind 3/3: AD-2 (audit-first INSERT) + AD-10 (identity/2FA via owner-only RBAC) +
  AD-12 (verify-first capability gate, in-route)
- NFR bind 2/7 active: NFR5 (streaming response P95 ≤ 5s) + NFR18 (ko-KR SSOT)
- 4 OQ 결정 wire 2/4 (cj-293 본 sprint):
  - ✅ OQ-EPIC30+-1 weasyprint vs reportlab = reportlab (pure Python)
  - ⏳ OQ-EPIC30+-2 SMTP 인프라 외부 의존 = Story 30.3 결정 wire 보류
  - ⏳ OQ-EPIC30+-3 APScheduler vs Celery beat vs cron = Story 30.4 결정 wire 보류
  - ✅ OQ-EPIC30+-4 chart library = matplotlib (pure Python)
- capability matrix v1.53 → v1.54 EXTENSION 보존 (cj-285)
- 2 OQ 결정 wire 2/4 → 본 sprint 적용 (cj-293)

CR 11-3 honest-DEFER 233번째 epic 연속 정직 회복 (cj-292 cycle 의 229~232번째
+ cj-293 의 233번째 결정 wire 진입).

Mirrors the canonical Pydantic schema pattern from `apps/api/schemas/audit_log_schemas.py`
(verbatim) for `BaseModel` + `Field` + `UUID4` + `Literal` typing. NFR18 ko-KR SSOT applies
to error messages only (this schema is request-shape, not user-facing UI).
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator


class CsvExportRequest(BaseModel):
    """Story 30.1 CSV export request schema.

    Used by GET /api/v1/exports/csv?type=...&period=...&tenant_id=...

    Fields:
        type: export type. cost-records (Story 30.1 first slice) or bom (level 1 only;
            full BOM tree = separate epic per cj-282 PRD entry out-of-scope 결정 wire).
        period: target period in YYYY-MM format (KST 기준). 정규식 검증.
        tenant_id: tenant UUID (cross-tenant 차단 via tenant context).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "cost-records",
                "period": "2026-08",
                "tenant_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            }
        },
    )

    type: Literal["cost-records", "bom"] = Field(
        ...,
        description="export type — cost-records (cost_records 테이블) | bom (BOM level 1)",
    )
    period: str = Field(
        ...,
        description="YYYY-MM format (KST 기준 monthly period)",
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    tenant_id: UUID4 = Field(
        ...,
        description="tenant UUID — cross-tenant 차단 via tenant context (CR 0-2 RLS)",
    )

    @field_validator("period")
    @classmethod
    def _validate_period_format(cls, v: str) -> str:
        """NFR18 ko-KR SSOT 결정 wire 보존 — period 정규식 추가 검증.

        YYYY-MM 형식 검증 (예: 2026-08, 2026-12). 윤년/월말 등 도메인 검증은 backend
        service 레이어에서 결정 wire 진입 (cj-style 284+ 결정 보류).
        """
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError(
                "period는 YYYY-MM 형식이어야 합니다 (예: 2026-08). " "월은 01~12 범위."
            )
        return v


class PdfExportRequest(BaseModel):
    """Story 30.2 PDF export request schema (cj-293 wire sprint).

    Used by GET /api/v1/exports/pdf?type=...&period=...&tenant_id=...

    Fields:
        type: export type. cost-records (Story 30.2 first slice) or bom (level 1 only;
            full BOM tree = separate epic per cj-282 PRD entry out-of-scope 결정 wire).
        period: target period in YYYY-MM format (KST 기준). 정규식 검증.
        tenant_id: tenant UUID (cross-tenant 차단 via tenant context).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "cost-records",
                "period": "2026-08",
                "tenant_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            }
        },
    )

    type: Literal["cost-records", "bom"] = Field(
        ...,
        description="export type — cost-records (cost_records 테이블) | bom (BOM level 1)",
    )
    period: str = Field(
        ...,
        description="YYYY-MM format (KST 기준 monthly period)",
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    tenant_id: UUID4 = Field(
        ...,
        description="tenant UUID — cross-tenant 차단 via tenant context (CR 0-2 RLS)",
    )

    @field_validator("period")
    @classmethod
    def _validate_period_format(cls, v: str) -> str:
        """NFR18 ko-KR SSOT 결정 wire 보존 — period 정규식 추가 검증."""
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("period는 YYYY-MM 형식이어야 합니다 (예: 2026-08). 월은 01~12 범위.")
        return v


__all__ = ["CsvExportRequest", "PdfExportRequest"]
