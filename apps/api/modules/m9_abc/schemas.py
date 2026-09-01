"""apps.api.modules.m9_abc.schemas — M9 ABC Pydantic models (Story 1.2 + 9.1).

Story 1.2 scaffold: `DriverRequest` + `DriverCountResponse`.
Story 9.1 EXTENSION: 5 NEW Pydantic v2 models for ABC 100% validation
endpoints (PRD §F9.1 verbatim + AD-15 §1 cross-language parity).

Schemas:
  - CostPoolValidationRequest: POST /api/v1/abc/cost-pools body
  - ActivityValidationRequest: POST /api/v1/abc/activities body
  - DriverValidationRequest: POST /api/v1/abc/drivers body (1.2 wire 확장)
  - ValidateRequest: POST /api/v1/abc/validate body (9-1 main entry point)
  - ValidationResponse: 200 OK response (3-layer guard summary)

All schemas use `extra="forbid"` per AD-15 §1.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DriverRequest(BaseModel):
    """Body of POST /api/v1/abc/drivers (Story 1.2 scaffold).

    Story 1.2 Task 4.2 — scaffold endpoint that the wizard calls to register
    a cost-driver. Story 9.1 EXTENSION: same shape — service layer dispatches
    to validation guard if `validate=true` query param.
    """

    model_config = ConfigDict(extra="forbid")

    driver_name: str = Field(..., min_length=1, max_length=120)
    unit: str = Field(..., min_length=1, max_length=40)
    practical_capacity_hours: int = Field(..., ge=0)


class DriverCountResponse(BaseModel):
    """Body of GET /api/v1/abc/drivers."""

    model_config = ConfigDict(extra="forbid")

    driver_count: int = Field(..., description="Number of drivers registered.")


# ── Story 9.1 NEW Pydantic v2 schemas (PRD §F9.1 + AD-15 §1) ──


class CostPoolValidationRequest(BaseModel):
    """Body of POST /api/v1/abc/cost-pools (Story 9.1).

    `department_id` 식별자 + `allocation_pcts` (0~100, Decimal-as-string).
    예: 4개 부서 각 25% → `["25", "25", "25", "25"]`.
    """

    model_config = ConfigDict(extra="forbid")

    department_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="원가풀 부서 식별자 (UUID-as-string).",
    )
    allocation_pcts: list[Decimal] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="부서별 allocation 퍼센트 리스트 (0~100, KRW integer).",
    )


class ActivityValidationRequest(BaseModel):
    """Body of POST /api/v1/abc/activities (Story 9.1)."""

    model_config = ConfigDict(extra="forbid")

    cost_pool_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="원가풀 식별자 (UUID-as-string).",
    )
    activity_pcts: list[Decimal] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="활동별 시간 배분 퍼센트 리스트 (0~100).",
    )


class DriverValidationRequest(BaseModel):
    """Body of POST /api/v1/abc/drivers when validate=true (Story 9.1).

    1.2 wire의 `DriverRequest` 와 별도 — 9-1 wire 전용 검증 endpoint body.
    """

    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="활동 식별자 (UUID-as-string).",
    )
    driver_pcts: list[Decimal] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="동인별 사용량 퍼센트 리스트 (0~100).",
    )


class ValidateRequest(BaseModel):
    """Body of POST /api/v1/abc/validate (Story 9.1 main entry point).

    3-layer guard 동시 검증 — cost_pool + activities + drivers 한 번에.
    모든 layer valid → all_valid=True (계산 활성화).
    """

    model_config = ConfigDict(extra="forbid")

    cost_pool_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="원가풀 식별자.",
    )
    activity_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="활동 식별자.",
    )
    cost_pool: list[Decimal] | None = Field(
        default=None,
        description="원가풀 allocation_pcts (선택).",
    )
    activities: list[Decimal] | None = Field(
        default=None,
        description="활동 activity_pcts (선택).",
    )
    drivers: list[Decimal] | None = Field(
        default=None,
        description="동인 driver_pcts (선택).",
    )


# Discriminated literal for response `target` field (envelope SSOT).
ValidationTarget = Literal["cost_pool", "activity", "driver"]


class ValidationLayerState(BaseModel):
    """Per-layer validation state in ValidationResponse (Story 9.1)."""

    model_config = ConfigDict(extra="forbid")

    target: ValidationTarget = Field(..., description="검증 대상.")
    sum_pct: str = Field(..., description="합계 퍼센트 (Decimal-as-string).")
    count: int = Field(..., description="항목 개수.")
    is_valid: bool = Field(..., description="100% 가드 통과 여부.")
    hash: str = Field(..., description="V8 determinism hash (sha256:64-hex).")
    message_ko: str | None = Field(
        default=None,
        description="가드 실패 시 한글 메시지 (PRD §F9.1 verbatim '원가풀 행 합 ≠ 100% (현재 105%)' format).",
    )


class ValidationResponse(BaseModel):
    """Response of POST /api/v1/abc/validate (Story 9.1 main entry point)."""

    model_config = ConfigDict(extra="forbid")

    cost_pool_id: str = Field(..., description="원가풀 식별자.")
    activity_id: str = Field(..., description="활동 식별자.")
    all_valid: bool = Field(
        ...,
        description="3 layer 모두 valid 시 True (계산 활성화 신호).",
    )
    layers: list[ValidationLayerState] = Field(
        default_factory=list,
        description="3 layer (cost_pool + activity + driver) 별 검증 상태.",
    )


# ── Story 9.2 NEW Pydantic v2 schemas (PRD §F9.2 + AD-15 §1) ──
#
# NOTE: 9-2 wire = NO public endpoint (AD-18 + AD-19). These schemas are
# defined for future 9-3 wire (A29 forward-lock) and for service-layer
# internal contracts when called via M3 dispatch. They mirror the schema
# shape used in compute-only service calls (in-memory AllocationResult).
# M9 owns no public endpoint for 9-2 wire — see 9-2-abc-allocation-engine-...md.


class CcrComputeRequest(BaseModel):
    """Body for in-memory CCR compute call (Story 9.2 service-layer internal).

    9-2 wire: this schema is NOT exposed via a public endpoint (AD-19 +
    AD-21). It mirrors the in-memory CCR compute shape used by the
    service layer when called via future M3 dispatch (A29 forward-lock 후
    9-3 wire).

    `department_id` 식별자 + `department_cost` (KRW 정수) +
    `practical_capacity_hours` (실제 조업능력 시간).
    """

    model_config = ConfigDict(extra="forbid")

    department_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="부서 식별자 (UUID-as-string).",
    )
    department_cost: Decimal = Field(
        ...,
        ge=0,
        description="부서 원가 (KRW 정수, AD-8 Decimal-as-string).",
    )
    practical_capacity_hours: Decimal = Field(
        ...,
        gt=0,
        description="실제 조업능력 시간 (Decimal, > 0).",
    )


class CcrResultResponse(BaseModel):
    """Response for in-memory CCR compute call (Story 9.2 service-layer internal).

    Mirrors `CCRResult` frozen dataclass shape with Decimal-as-string
    serialization (AD-15 §1 cross-language parity with TS mirror
    `apps/web/lib/m9-abc-allocation.ts`).
    """

    model_config = ConfigDict(extra="forbid")

    department_id: str = Field(..., description="부서 식별자.")
    department_cost: str = Field(..., description="부서 원가 (KRW 정수, Decimal-as-string).")
    practical_capacity_hours: str = Field(
        ..., description="실제 조업능력 시간 (Decimal-as-string)."
    )
    ccr_per_hour: str = Field(
        ..., description="CCR 시간당 자원동인율 (KRW 정수, Decimal-as-string)."
    )
    hash: str = Field(..., description="V8 determinism hash (sha256:64-hex).")
    message_ko: str | None = Field(
        default=None,
        description="CCR compute 실패 시 한글 메시지 (ko-KR.json SSOT).",
    )


class AllocationRequest(BaseModel):
    """Body for in-memory ABC allocation call (Story 9.2 service-layer internal).

    Mirrors AllocationResult compute input shape. Lists of `activity_mapping`
    + `cost_object_breakdown` are JSON-serializable dicts (TS mirror parity).
    """

    model_config = ConfigDict(extra="forbid")

    department_id: str = Field(..., min_length=1, max_length=64)
    department_cost: Decimal = Field(..., ge=0)
    practical_capacity_hours: Decimal = Field(..., gt=0)
    used_hours: Decimal = Field(..., ge=0, description="사용 시간 (Decimal-as-string).")
    activity_mappings: list[dict[str, str | int]] = Field(
        default_factory=list,
        description="활동별 매핑 리스트 (activity_id + hours + ccr_amount_krw).",
    )
    cost_object_breakdown: list[dict[str, str | int]] = Field(
        default_factory=list,
        description=(
            "원가대상별 4컬럼 (product_id + activity_id + driver_id + " "allocated_krw) 리스트."
        ),
    )


class AllocationResponse(BaseModel):
    """Response for in-memory ABC allocation call (Story 9.2 service-layer internal).

    Mirrors AllocationResult frozen dataclass shape. Decimal-as-string
    serialization (AD-15 §1 cross-language parity).
    """

    model_config = ConfigDict(extra="forbid")

    department_id: str = Field(..., description="부서 식별자.")
    department_cost: str = Field(..., description="부서 원가 (KRW 정수).")
    ccr_per_hour: str = Field(..., description="CCR 시간당 자원동인율 (KRW 정수).")
    total_breakdown_sum: str = Field(..., description="Σ 원가대상별 배부액 (KRW 정수).")
    unused_hours: str = Field(..., description="미사용 시간 (Decimal-as-string).")
    unused_cost_krw: str = Field(..., description="미사용 원가 (KRW 정수).")
    is_balanced: bool = Field(..., description="V7 ABC 무결성 1원 단위 만족 여부.")
    activity_mappings: list[dict[str, str | int]] = Field(default_factory=list)
    cost_object_breakdown: list[dict[str, str | int]] = Field(default_factory=list)
    ccr_hash: str = Field(..., description="V8 hash for CCR.")
    allocation_hash: str = Field(..., description="V8 hash for Allocation.")
    message_ko: str | None = Field(
        default=None,
        description="V7 불균형 시 한글 메시지 (ko-KR.json SSOT).",
    )
    unused_message_ko: str | None = Field(
        default=None,
        description="미사용능력 한글 메시지 (PRD §A9 '미사용능력 X,XXX원').",
    )
