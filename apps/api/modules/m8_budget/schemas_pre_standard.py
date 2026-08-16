"""apps.api.modules.m8_budget.schemas_pre_standard — Story 8.3 Pydantic v2 schemas.

AD-15 §1 request/response shape — snake_case fields, Decimal-as-string
for monetary precision parity (AD-8).

Story 8.3 (3 NEW):
  - BudgetPreStandardRequest — POST /budget/pre-standard body
    (5 input fields + period_key + scenario_index, all Decimal-typed)
  - BudgetPreStandardResponse — single snapshot response (POST + GET)
  - BudgetPreStandardListResponse — list snapshots response (optional)
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.cost_engine.budget_pre_standard import (
    OVERHEAD_RATE_MAX_PCT,
    OVERHEAD_RATE_MIN_PCT,
)


class BudgetPreStandardRequest(BaseModel):
    """POST /api/v1/budget/pre-standard request body (PRD §F8.3).

    5 input fields + period_key + scenario_index:

    - material_unit_cost: KRW 정수 (직접재료 단가)
    - labor_unit_cost: KRW 정수 (직접노무 단가)
    - overhead_rate: 0~100 % (제조경비율)
    - material_qty: KRW 정수 (직접재료 수량)
    - labor_hours: 시간 단위 (직접노무 시간)
    - period_key: AD-24 virtual YYYY-MM#B<n> (8-1 wire)
    - scenario_index: 1차 MVP = 1 only

    AD-8 monetary precision — Decimal-as-string for round-trip parity.
    AD-24 virtual period key — 8-1 wire reuse.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    period_key: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="AD-24 virtual YYYY-MM#B<n> (8-1 wire)",
    )
    scenario_index: int = Field(
        default=1,
        ge=1,
        le=1,
        description="1차 MVP = 1 only (8-1 lock)",
    )
    material_unit_cost: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="KRW 정수 (직접재료 단가, AD-8 BigInteger parity)",
    )
    labor_unit_cost: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="KRW 정수 (직접노무 단가, AD-8 BigInteger parity)",
    )
    overhead_rate: Decimal = Field(
        ...,
        ge=OVERHEAD_RATE_MIN_PCT,
        le=OVERHEAD_RATE_MAX_PCT,
        description="0~100 % (제조경비율, OVERHEAD_RATE_MAX_PCT=100)",
    )
    material_qty: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="KRW 정수 (직접재료 수량, AD-8 BigInteger parity)",
    )
    labor_hours: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="시간 단위 (직접노무 시간)",
    )

    @field_validator("period_key")
    @classmethod
    def _validate_period_key(cls, v: str) -> str:
        """AD-24 virtual pattern `YYYY-MM#B<n>` (8-1 reuse)."""
        from packages.cost_engine.budget_period_key import (
            parse_virtual_budget_period_key,
        )

        try:
            parse_virtual_budget_period_key(period_key=v)
        except ValueError as exc:
            raise ValueError(
                f"period_key must match YYYY-MM#B<n>: {v!r}"
            ) from exc
        return v


class BudgetPreStandardSnapshotSerialized(BaseModel):
    """Single pre-standard snapshot serialized response shape (Decimal-as-string).

    Mirrors 8-1 BudgetScenarioSerialized + 8-2 VarianceRowSerialized pattern.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    material_cost: str = Field(
        ..., description="KRW 정수 (직접재료 합계, AD-8)"
    )
    labor_cost: str = Field(
        ..., description="KRW 정수 (직접노무 합계, AD-8)"
    )
    overhead_cost: str = Field(
        ..., description="KRW 정수 (제조경비 합계, AD-8)"
    )
    manufacturing_cost: str = Field(
        ..., description="KRW 정수 (제조원가 합계, AD-8)"
    )
    period_key: str = Field(
        ..., description="AD-24 virtual YYYY-MM#B<n>"
    )
    scenario_index: int = Field(
        ..., ge=1, le=1, description="1차 MVP = 1 only"
    )
    engine_type: str = Field(
        ..., description="Literal 'budget' (8-3 wire uniqueness)"
    )
    inventory_adjustment: int = Field(
        ..., description="BigInteger (default 0 for pre-standard)"
    )
    result_hash: str = Field(
        ..., description="V8 determinism sha256:64hex"
    )
    state: str = Field(
        ..., description="Literal 'verified' | 'committed' | 'reversed'"
    )
    created_at_kst: str = Field(
        ..., description="ISO 8601 KST timestamp"
    )


class BudgetPreStandardResponse(BaseModel):
    """POST + GET response envelope (PRD §F8.3 + AD-15)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot: BudgetPreStandardSnapshotSerialized
    trace_id: str | None = None
