"""apps.api.modules.m8_budget.schemas — Story 8.1 + 8.2 Pydantic v2 schemas.

AD-15 §1 request/response shape — snake_case fields, Decimal-as-string
for monetary precision parity (AD-8).

Story 8.1 (3 NEW):
  - CreateBudgetScenarioRequest — POST /budget/scenarios body
    (real_period_key validator matches AD-24 real pattern)
  - BudgetScenarioResponse — single scenario response (POST + GET by id)
  - BudgetScenarioListResponse — list scenarios response (GET)

Story 8.2 (4 NEW):
  - VarianceRowSerialized — single variance row (PRD §F8.2 + NFR18)
  - VarianceTableResponse — GET /budget/variance/{period_key} envelope
  - BudgetVariancePdfResponse — GET /budget/variance/{period_key}/pdf (8-3 DEFER)
  - ABCDDisabledBadgeSerialized — A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.cost_engine.budget_period_key import REAL_PERIOD_KEY_PATTERN


class CreateBudgetScenarioRequest(BaseModel):
    """POST /api/v1/budget/scenarios request body.

    AD-24 §6.1 real period pattern `^\\d{4}-(0[1-9]|1[0-2])$` validator.
    1차 MVP = scenario_index=1 (only) — derived in service layer via
    `derive_budget_period_key(real_period_key, scenario_index=1)`.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    real_period_key: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 real fiscal period key — YYYY-MM",
    )

    @field_validator("real_period_key")
    @classmethod
    def _validate_real_period_key(cls, v: str) -> str:
        import re

        if not re.match(REAL_PERIOD_KEY_PATTERN, v):
            raise ValueError("real_period_key must match YYYY-MM (AD-24)")
        return v


class BudgetScenarioSerialized(BaseModel):
    """Single scenario serialized response shape (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., description="UUID v7")
    tenant_id: str = Field(..., description="UUID")
    period_key: str = Field(..., description="AD-24 virtual: YYYY-MM#B<n>")
    real_period_key: str = Field(..., description="AD-24 real: YYYY-MM")
    scenario_index: int = Field(..., ge=1, description="1차 MVP = 1 only")
    scenario_hash: str = Field(..., description="V8 determinism sha256 digest")
    created_by: str = Field(..., description="UUID")
    created_at_kst: str = Field(..., description="ISO 8601 KST timestamp")


class BudgetScenarioResponse(BaseModel):
    """POST + GET-by-period_key response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario: BudgetScenarioSerialized


class BudgetScenarioListResponse(BaseModel):
    """GET /api/v1/budget/scenarios response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scenarios: list[BudgetScenarioSerialized]
    total_count: int = Field(..., ge=0, le=1, description="1차 MVP 한도 = 1")
    trace_id: str | None = None


# ── Story 8.2 variance schemas (PRD §F8.2 + NFR18 ko-KR lock) ──────


class ABCDDisabledBadgeSerialized(BaseModel):
    """A×B×C×D 회색 배지 placeholder response (PRD §15 NON-GOAL #1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    variant: str = Field(
        ..., description="Literal 'variance' | 'trend' | 'sensitivity'"
    )
    label: str = Field(
        ..., description="회색 배지 라벨 (ko-KR lock, NFR18)"
    )
    tooltip: str = Field(
        ..., description="회색 배지 tooltip (PRD §F8.2 verbatim)"
    )
    disabled: bool = Field(
        ..., description="always true (1차 MVP = disabled, 2차 engine 예정)"
    )


class VarianceRowSerialized(BaseModel):
    """Single variance row response shape (PRD §F8.2 + AD-8/AD-15).

    Decimal-as-string for monetary precision parity (AD-8).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(
        ..., description="항목명 (예: '직접재료', '직접노무', '제조경비')"
    )
    budget_value: str = Field(
        ..., description="예산 (KRW integer, Decimal-as-string)"
    )
    actual_value: str = Field(
        ..., description="실적 (KRW integer, Decimal-as-string)"
    )
    difference: str = Field(
        ..., description="차액 = actual - budget (Decimal-as-string)"
    )
    variance_pct: str = Field(
        ..., description="차이율 % = diff/budget*100 (4 decimal places)"
    )
    severity: str = Field(
        ...,
        description="Literal 'normal' | 'warning' | 'critical' (PRD §F8.2)",
    )
    color: str = Field(
        ..., description="Literal 'gray' | 'yellow' | 'red' (PRD §F8.2)"
    )


class VarianceTableResponse(BaseModel):
    """GET /api/v1/budget/variance/{period_key} response envelope.

    rows + 합계 row + A×B×C×D 회색 배지 placeholder (PRD §F8.2 + §15 NON-GOAL).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    period_key: str = Field(
        ..., description="AD-24 virtual YYYY-MM#B<n> (8-1 wire)"
    )
    scenario_index: int = Field(
        ..., ge=1, le=1, description="1차 MVP = 1 only"
    )
    rows: list[VarianceRowSerialized] = Field(
        ..., description="예산-실적 대조 행 목록 (PRD §F8.2)"
    )
    total_row: VarianceRowSerialized = Field(
        ..., description="합계 행 (테이블 하단, 항상 1행)"
    )
    abcd_disabled_badge: ABCDDisabledBadgeSerialized = Field(
        ..., description="A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL)"
    )
    abcd_disabled_note: str = Field(
        ..., description="A×B×C×D 미구현 비고 (PRD §15 NON-GOAL)"
    )
    trace_id: str | None = None


class BudgetVariancePdfResponse(BaseModel):
    """GET /api/v1/budget/variance/{period_key}/pdf response envelope (8-3 DEFER).

    8-2 atomic wire: returns envelope only (PDF body honestly DEFER to 8-3).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    period_key: str = Field(
        ..., description="AD-24 virtual YYYY-MM#B<n> (8-1 wire)"
    )
    scenario_index: int = Field(
        ..., ge=1, le=1, description="1차 MVP = 1 only"
    )
    pdf_bytes_b64: str = Field(
        ...,
        description="base64-encoded PDF (8-3 follow-up sprint, currently empty)",
    )
    envelope: dict = Field(
        ...,
        description="Epic 6 M5 PDF envelope SSOT (READ-ONLY pattern)",
    )
    trace_id: str | None = None
