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
