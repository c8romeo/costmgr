"""apps.api.modules.m7_simulation.schemas — Story 7.1 Pydantic v2 schemas.

AD-15 §1 request/response shape — snake_case fields, Decimal-as-string
for monetary precision parity (AD-8).

3 NEW schemas:
  - CVPSimulationRequest — POST /simulation/cvp/compute body
    (period_key + delta)
  - CVPBaselineResponse — GET /simulation/cvp/baseline response
  - CVPSimulationResponse — POST /simulation/cvp/compute response
    (baseline + delta + result + latency_ms)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CVPDeltaRequest(BaseModel):
    """CVP delta request body (4 percentage deltas, all 0 by default).

    AD-15 §1 + AD-8 Decimal-as-string (TS mirror parity).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    unit_price_delta_pct: str = Field(
        default="0",
        description="AD-15 Decimal-as-string — 단가 변동률 (-0.5 ~ 0.5)",
    )
    unit_variable_cost_delta_pct: str = Field(
        default="0",
        description="단위변동비 변동률 (-0.5 ~ 0.5)",
    )
    fixed_cost_delta_pct: str = Field(
        default="0",
        description="고정비 변동률 (-0.3 ~ 0.3)",
    )
    operating_rate_delta_pct: str = Field(
        default="0",
        description="조업도 변동률 (-0.5 ~ 0.5)",
    )

    @field_validator(
        "unit_price_delta_pct",
        "unit_variable_cost_delta_pct",
        "fixed_cost_delta_pct",
        "operating_rate_delta_pct",
    )
    @classmethod
    def _validate_decimal_str(cls, v: str) -> str:
        from decimal import Decimal, InvalidOperation

        try:
            Decimal(v)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"must be a valid Decimal string, got {v!r}") from exc
        return v


class CVPSimulationRequest(BaseModel):
    """POST /api/v1/simulation/cvp/compute request body.

    Carries `period_key` (AD-24 YYYY-MM) + `delta` (4 percentage deltas).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    period_key: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 fiscal period key — YYYY-MM",
    )
    delta: CVPDeltaRequest = Field(
        default_factory=CVPDeltaRequest,
        description="CVP delta (4 percentage deltas, all 0 by default)",
    )

    @field_validator("period_key")
    @classmethod
    def _validate_period_key(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("period_key must match YYYY-MM (AD-24)")
        return v


class CVPBaselineSerialized(BaseModel):
    """CVP baseline serialized response (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixed_cost: str
    unit_variable_cost: str
    unit_price: str
    operating_rate: str
    target_profit: str


class CVPDeltaSerialized(BaseModel):
    """CVP delta serialized response (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit_price_delta_pct: str
    unit_variable_cost_delta_pct: str
    fixed_cost_delta_pct: str
    operating_rate_delta_pct: str


class CVPBEPResultSerialized(BaseModel):
    """BEPResult serialized response (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bep_quantity: str
    bep_revenue: str
    contribution_margin_per_unit: str
    contribution_margin_ratio: str


class CVPTargetProfitResultSerialized(BaseModel):
    """TargetProfitResult serialized response (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_quantity: str
    target_revenue: str


class CVPResultSerialized(BaseModel):
    """CVPResult serialized response (Decimal-as-string + nested)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    simulated_bep: CVPBEPResultSerialized
    simulated_target_profit: CVPTargetProfitResultSerialized
    baseline_bep: CVPBEPResultSerialized
    baseline_target_profit: CVPTargetProfitResultSerialized
    delta_summary: dict[str, str]


class CVPSimulationResponse(BaseModel):
    """POST /api/v1/simulation/cvp/compute response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline: CVPBaselineSerialized
    delta: CVPDeltaSerialized
    result: CVPResultSerialized
    latency_ms: int = Field(..., ge=0, description="서버 계산 latency (ms)")
    trace_id: str | None = None


class CVPBaselineResponse(BaseModel):
    """GET /api/v1/simulation/cvp/baseline response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline: CVPBaselineSerialized
    period_key: str
    source_period_key: str = Field(
        ...,
        description="베이스라인 추출 출처 period_key (latest committed snapshot)",
    )
    fiscal_period_state: str = Field(
        ...,
        description="fiscal_period_snapshots.state (verified|committed|reversed)",
    )
    trace_id: str | None = None
