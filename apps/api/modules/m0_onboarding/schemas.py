"""apps.api.modules.m0_onboarding.schemas — Pydantic models for M0 onboarding API.

Story 1.1 — Task 2.3. Pydantic v2 models that wire the pure domain
(`packages.services.m0_onboarding.industry_menu`) to the FastAPI layer.

Per AD-15: snake_case field names. Per AD-23: the response shape uses
`tenant_settings.onboarding.industry` JSONB naming convention (one
canonical key per namespace).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.services.m0_onboarding.industry_menu import (
    Industry,
    get_menu_labels,
)


# ── Request bodies ──────────────────────────────────────────
class IndustryUpdateRequest(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/industry.

    The `industry` field is validated against the `Industry` enum — invalid
    values return 422 (AC #1 anti-pattern guard).
    """

    model_config = ConfigDict(extra="forbid")

    industry: Industry = Field(
        ...,
        description="PRD §4.1 4지선다 (manufacturing / service / manufacturing_service / manufacturing_service_other)",
    )


# ── Response bodies ─────────────────────────────────────────
class IndustryUpdateResponse(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/industry.

    `menu` is the Korean-label list the frontend renders directly.
    `is_initial` reflects the post-write state (True on the very first write;
    False after any subsequent change — see `SettingsService.update_industry`).
    `trace_id` correlates the success envelope with the audit row + the
    X-Trace-Id response header (F-43).
    """

    model_config = ConfigDict(extra="forbid")

    industry: Industry
    menu: list[str] = Field(
        default_factory=list,
        description="Korean menu labels (ordered). The frontend renders these directly.",
    )
    settings_version: int = Field(
        ..., description="Post-write optimistic-concurrency version (AD-23)."
    )
    is_initial: bool = Field(
        ...,
        description="True only on the very first onboarding selection; False thereafter (F-2).",
    )
    selected_at: datetime = Field(
        ..., description="UTC ISO-8601 timestamp of the (latest) industry write."
    )
    trace_id: str = Field(
        ..., description="Server-generated UUID for audit correlation (F-43)."
    )

    @classmethod
    def from_industry(
        cls,
        industry: Industry,
        *,
        settings_version: int,
        is_initial: bool,
        selected_at: datetime,
        trace_id: str,
    ) -> IndustryUpdateResponse:
        """Helper — build the response with the canonical menu labels."""
        return cls(
            industry=industry,
            menu=get_menu_labels(industry),
            settings_version=settings_version,
            is_initial=is_initial,
            selected_at=selected_at,
            trace_id=trace_id,
        )


class TenantSettingsResponse(BaseModel):
    """Body of GET /api/v1/tenant-settings.

    Aggregates all four JSONB namespaces (onboarding / baseline / abc / ai)
    plus `industry` (sugar for `onboarding.industry`) and `settings_version`
    for the frontend's optimistic-concurrency loop.
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    industry: Industry | None = Field(
        default=None,
        description="Sugar for `onboarding.industry`. Null when M0 onboarding is incomplete.",
    )
    settings_version: int
    onboarding: dict[str, Any] = Field(default_factory=dict)
    baseline: dict[str, Any] = Field(default_factory=dict)
    abc: dict[str, Any] = Field(default_factory=dict)
    ai: dict[str, Any] = Field(default_factory=dict)


# ── Error payloads (AD-15 contract) ─────────────────────────
class IndustryLockedError(BaseModel):
    """409 INDUSTRY_LOCKED payload — A7 전진법 enforcement (AC #4)."""

    model_config = ConfigDict(extra="forbid")

    code: str = "INDUSTRY_LOCKED"
    message_ko: str = "업종 변경은 다음 회계연도부터 가능합니다 (A7 전진법)"
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Carries {current_industry, next_fiscal_year_start}.",
    )
    trace_id: str


class ForbiddenRoleError(BaseModel):
    """403 FORBIDDEN_ROLE payload — only `owner` may change industry."""

    model_config = ConfigDict(extra="forbid")

    code: str = "FORBIDDEN_ROLE"
    message_ko: str = "업종 변경은 owner 역할만 가능합니다"
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


# ── Story 1.2 — Settings Wizard field request/response models ──
class FiscalYearStartField(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/fiscal-year-start.

    A1 / AD-24: stored as `YYYY-MM`. MM ∈ 01..12.
    """

    model_config = ConfigDict(extra="forbid")

    fiscal_year_start: Annotated[
        str,
        Field(
            pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
            description="YYYY-MM (e.g. 2026-01). A1 / AD-24 period key prefix.",
        ),
    ]


class CurrencyField(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/currency.

    A6 / AD-8: KRW is integer, USD is NUMERIC(18,2). MVP supports both.
    """

    model_config = ConfigDict(extra="forbid")

    currency: Literal["KRW", "USD"]


class LanguageField(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/language.

    NFR-18: MVP is ko-KR only (ux-locked-decisions §4).
    """

    model_config = ConfigDict(extra="forbid")

    language: Literal["ko-KR"]


class AllocationCriteriaUpdateRequest(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/allocation-criteria.

    Each save increments the criterion's `count` and marks `completed=true`.
    A7: after first calculation, the count cannot decrease.
    """

    model_config = ConfigDict(extra="forbid")

    criterion: Literal["direct_indirect", "fixed_variable", "drivers"]
    count: int = Field(ge=1, description="≥1 row registered for this criterion.")


class OnboardingFieldSavedResponse(BaseModel):
    """Body of POST /api/v1/tenant-settings/onboarding/<field>.

    `is_complete` is the **post-write** completion status so the frontend
    can flip the [계산] button state without a second round-trip.
    `trace_id` correlates with the audit row (F-43 pattern, mirrored from 1.1).
    """

    model_config = ConfigDict(extra="forbid")

    field: Literal[
        "fiscal_year_start",
        "currency",
        "language",
        "allocation_criteria",
    ]
    value: Any
    settings_version: int
    is_complete: bool = False
    missing: list[str] = Field(default_factory=list)
    trace_id: str


class CompletionStatusResponse(BaseModel):
    """Body of GET /api/v1/tenant-settings/completion.

    Mirrors `packages.services.m0_onboarding.settings_completion.CompletionStatus`.
    `missing` is the user-facing list (Korean labels) consumed directly by
    the disabled-button tooltip.

    F-7: `fiscal_year_start_value` / `currency_value` / `industry` carry the
    **actual** stored values so the wizard can seed its pickers on first
    render without an extra GET round-trip. `last_calc_date` is included
    so the UI can surface the A7 warning before the user clicks save (F-34).
    """

    model_config = ConfigDict(extra="forbid")

    fiscal_year_start_completed: bool
    currency_completed: bool
    language_completed: bool
    allocation_criteria_completed: bool
    direct_indirect_count: int
    fixed_variable_count: int
    drivers_count: int
    drivers_required: bool = Field(
        ..., description="False when industry=manufacturing (no ABC engine)."
    )
    is_complete: bool
    missing: list[str]
    trace_id: str
    # F-7 value-bearing fields — None for not-yet-saved tenants.
    fiscal_year_start_value: str | None = None
    currency_value: Literal["KRW", "USD"] | None = None
    industry: Industry | None = None
    # F-34: A7 lock signal — when set, fiscal_year_start / currency changes
    # are blocked at the backend. UI surfaces this to warn before save.
    last_calc_date: str | None = Field(
        default=None,
        description="ISO-8601 date (YYYY-MM-DD). None while no calc has run.",
    )


class FiscalYearLockedError(BaseModel):
    """409 FISCAL_YEAR_LOCKED — A7 전진법 after first calc (Story 1.2 AC #3)."""

    model_config = ConfigDict(extra="forbid")

    code: str = "FISCAL_YEAR_LOCKED"
    message_ko: str = "회계연도 시작월 변경은 다음 회계연도부터 가능합니다 (A7 전진법)"
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class CurrencyLockedError(BaseModel):
    """409 CURRENCY_LOCKED — A7 전진법 after first calc."""

    model_config = ConfigDict(extra="forbid")

    code: str = "CURRENCY_LOCKED"
    message_ko: str = "통화 변경은 다음 회계연도부터 가능합니다 (A7 전진법)"
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class JsonbSchemaViolationError(BaseModel):
    """400 JSONB_SCHEMA_VIOLATION — onboarding JSONB is malformed."""

    model_config = ConfigDict(extra="forbid")

    code: str = "JSONB_SCHEMA_VIOLATION"
    message_ko: str = "온보딩 데이터 형식이 올바르지 않습니다"
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str
