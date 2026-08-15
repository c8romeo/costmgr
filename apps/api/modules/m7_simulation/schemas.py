"""apps.api.modules.m7_simulation.schemas — Story 7.1 + 7.2 Pydantic v2 schemas.

AD-15 §1 request/response shape — snake_case fields, Decimal-as-string
for monetary precision parity (AD-8).

Story 7.1 CVP schemas:
  - CVPSimulationRequest — POST /simulation/cvp/compute body
    (period_key + delta)
  - CVPBaselineResponse — GET /simulation/cvp/baseline response
  - CVPSimulationResponse — POST /simulation/cvp/compute response
    (baseline + delta + result + latency_ms)

Story 7.2 Projection schemas:
  - ProjectionInputsRequest — 4종 파라미터 (loan_amount, interest_rate,
    cost_inflation_rate, corporate_tax_rate)
  - ProjectionComputeRequest — POST /simulation/projection/compute body
    (period_key + projection_month + 4종 params)
  - ProjectionBaselineResponse — GET /simulation/projection/baseline response
  - ProjectionComputeResponse — POST /simulation/projection/compute response
  - ProjectionPdfRequest — POST /simulation/projection/report/pdf body
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


# ──────────────────────────────────────────────────────────────
# Story 7.2 — Next-Month Projection Pydantic v2 schemas
# (PRD §F7.2 4종 파라미터 강제 + capability gate reuse + 5 routes)
# ──────────────────────────────────────────────────────────────


class ProjectionInputsRequest(BaseModel):
    """4종 projection inputs (loan_amount + interest_rate +
    cost_inflation_rate + corporate_tax_rate).

    AD-15 §1 + AD-8 Decimal-as-string (TS mirror parity).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    loan_amount: str = Field(
        ...,
        description="AD-8 KRW BigInteger — 차입금 (0 이상)",
    )
    interest_rate: str = Field(
        default="0",
        description="이자율 (0~100, 백분율)",
    )
    cost_inflation_rate: str = Field(
        default="0",
        description="원가 상승률 (-50~100, 백분율)",
    )
    corporate_tax_rate: str = Field(
        default="0",
        description="법인세율 (0~100, 백분율)",
    )

    @field_validator(
        "loan_amount",
        "interest_rate",
        "cost_inflation_rate",
        "corporate_tax_rate",
    )
    @classmethod
    def _validate_decimal_str(cls, v: str) -> str:
        from decimal import Decimal, InvalidOperation

        try:
            Decimal(v)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"must be a valid Decimal string, got {v!r}") from exc
        return v


class ProjectionComputeRequest(BaseModel):
    """POST /api/v1/simulation/projection/compute request body.

    Carries `period_key` (AD-24 YYYY-MM) + `projection_month`
    (AD-24 YYYY-MM, must be > period_key) + 4종 `inputs`.
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
    projection_month: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 projection target month — YYYY-MM (must be > period_key)",
    )
    inputs: ProjectionInputsRequest = Field(
        ...,
        description="4종 projection inputs (loan_amount + interest_rate + cost_inflation_rate + corporate_tax_rate)",
    )

    @field_validator("period_key", "projection_month")
    @classmethod
    def _validate_period_key(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("must match YYYY-MM (AD-24)")
        return v


class ProjectionInputsSerialized(BaseModel):
    """ProjectionInputs serialized response (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    loan_amount: str
    interest_rate: str
    cost_inflation_rate: str
    corporate_tax_rate: str


class NextMonthProjectionSerialized(BaseModel):
    """NextMonthProjection serialized response (Decimal-as-string)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projected_revenue: str
    projected_variable_cost: str
    projected_fixed_cost: str
    interest_expense: str
    pre_tax_income: str
    corporate_tax: str
    after_tax_income: str


class ProjectionComputeResponse(BaseModel):
    """POST /api/v1/simulation/projection/compute response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline: CVPBaselineSerialized
    projection_inputs: ProjectionInputsSerialized
    result: NextMonthProjectionSerialized
    latency_ms: int = Field(..., ge=0, description="서버 계산 latency (ms)")
    trace_id: str | None = None


class ProjectionBaselineResponse(BaseModel):
    """GET /api/v1/simulation/projection/baseline response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline: CVPBaselineSerialized
    period_key: str
    projection_month: str
    source_period_key: str = Field(
        ...,
        description="베이스라인 추출 출처 period_key (latest committed snapshot)",
    )
    fiscal_period_state: str = Field(
        ...,
        description="fiscal_period_snapshots.state (verified|committed|reversed)",
    )
    derived_projection_inputs_hint: dict[str, str] = Field(
        default_factory=dict,
        description="4종 projection inputs placeholder hint (frontend form initial values)",
    )
    trace_id: str | None = None


class ProjectionPdfRequest(BaseModel):
    """POST /api/v1/simulation/projection/report/pdf request body."""

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
    projection_month: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 projection target month — YYYY-MM (must be > period_key)",
    )
    inputs: ProjectionInputsRequest = Field(
        ...,
        description="4종 projection inputs",
    )
    format: str = Field(
        default="A4",
        description="PDF format — A4 (only A4 supported per NFR18)",
    )

    @field_validator("period_key", "projection_month")
    @classmethod
    def _validate_period_key(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("must match YYYY-MM (AD-24)")
        return v
