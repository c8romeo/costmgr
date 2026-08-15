"""apps.api.modules.m8_budget.schemas — Story 8.1 Pydantic v2 schemas.

AD-15 §1 request/response shape — snake_case fields, Decimal-as-string
for monetary precision parity (AD-8).

3 NEW schemas:
  - CreateBudgetScenarioRequest — POST /budget/scenarios body
    (real_period_key validator matches AD-24 real pattern)
  - BudgetScenarioResponse — single scenario response (POST + GET by id)
  - BudgetScenarioListResponse — list scenarios response (GET)
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
