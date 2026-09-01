"""apps.api.modules.m9_abc.services.abc_validation_service — Story 9.1.

Service-layer orchestration for ABC 100% validation guard (PRD §F9.1).

Pure kernel lives at `packages.cost_engine.abc_engine.py` (4 NEW pure
functions + 3 frozen dataclasses + 4 typed exceptions, A19 cohesion
pattern 6번째). Service layer wraps the kernel with JSON-safe envelope
mapping + tenant_settings.abc.drivers JSONB storage I/O (Story 1.2
scaffold pattern reuse — drivers stored in tenant_settings JSONB for
1차 MVP, 9-2 진입 시점에 dedicated table로 lift).

AD-22 ledger append-only: 9-1 = validation only (no INSERT, read-mostly).
CR 1.1 invariant — no audit emit. A5 forward-lock 변경 0 (CR 11-3 D-2
즉시 sweep 회피).

Architecture (matches 8-1 BudgetScenarioService + 8-2 BudgetVarianceService):
  - handler → service → engine (pure kernel)
  - `_to_validation_state` ORM→kernel boundary (CR 12-1 L3 precedent)
  - 3-layer defense (CR 12-5 L3): route @require_capability(ABC_CALCULATION)
    + service validate_abc_pct_list + frontend disabled signal (UI layer)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
)
from apps.api.modules.m9_abc.exceptions import (
    ABC_ACTIVITY_INVALID_SUM_KO,
    ABC_COST_POOL_INVALID_SUM_KO,
    ABC_DRIVER_INVALID_SUM_KO,
    ABC_VALIDATION_NOT_FOUND_KO,
)
from packages.cost_engine.abc_engine import (
    AbcValidationNotFoundError,
    ActivityValidation,
    ActivityValidationError,
    CostPoolValidation,
    CostPoolValidationError,
    DriverValidation,
    DriverValidationError,
    ValidationState,
    compute_validation_hash,
    validate_100_percent_guard,
    validate_activity,
    validate_cost_pool,
    validate_driver,
)
from packages.services.m9_abc.abc_validation_serializers import (
    serialize_validation_state,
)

# V8 determinism + idempotency — 9-1 = validation only (no INSERT, read-mostly).
ABC_VALIDATION_INDUSTRY_AGNOSTIC: bool = True


@dataclass(frozen=True, slots=True)
class AbcValidationState:
    """Service-layer DTO for ABC validation summary (CR 12-1 L3 boundary).

    Combines the 3 pure-kernel validation states (CostPoolValidation +
    ActivityValidation + DriverValidation) + all_valid bool + per-layer
    Korean error messages consumed by handlers (ko-KR.json SSOT CR 11-4
    D-002 fallback to hardcoded constant).

    `cost_pool_message_ko` / `activity_message_ko` / `driver_message_ko` are
    the Korean hints shown when each layer's validation fails (PRD §F9.1
    "원가풀 행 합 ≠ 100% (현재 105%)" message format).
    """

    cost_pool: CostPoolValidation | None
    activity: ActivityValidation | None
    driver: DriverValidation | None
    all_valid: bool
    cost_pool_message_ko: str | None
    activity_message_ko: str | None
    driver_message_ko: str | None


def _to_validation_state(
    guard_result: dict[str, Any],
) -> AbcValidationState:
    """Pure kernel → service-layer DTO boundary (CR 12-1 L3 precedent).

    `validate_100_percent_guard` result dict → `AbcValidationState`
    service-layer DTO with Korean error messages pre-computed.

    Pure function — no DB I/O. Called by `AbcValidationService`.
    """
    cost_pool = guard_result.get("cost_pool")
    activity = guard_result.get("activity")
    driver = guard_result.get("driver")
    all_valid = bool(guard_result.get("all_valid", False))

    cost_pool_msg: str | None = None
    if cost_pool is not None and not cost_pool.is_valid:
        cost_pool_msg = f"{ABC_COST_POOL_INVALID_SUM_KO} (현재 {cost_pool.sum_pct}%)"

    activity_msg: str | None = None
    if activity is not None and not activity.is_valid:
        activity_msg = f"{ABC_ACTIVITY_INVALID_SUM_KO} (현재 {activity.sum_pct}%)"

    driver_msg: str | None = None
    if driver is not None and not driver.is_valid:
        driver_msg = f"{ABC_DRIVER_INVALID_SUM_KO} (현재 {driver.sum_pct}%)"

    return AbcValidationState(
        cost_pool=cost_pool,
        activity=activity,
        driver=driver,
        all_valid=all_valid,
        cost_pool_message_ko=cost_pool_msg,
        activity_message_ko=activity_msg,
        driver_message_ko=driver_msg,
    )


def validate_abc_pct_list(
    *,
    allocation_pcts: list[Decimal],
    target: str,  # "cost_pool" | "activity" | "driver"
    target_id: str,
) -> None:
    """CR 12-5 L3 3-layer defense — service-layer pre-validation guard.

    Validates allocation_pcts list non-empty + each value is Decimal in
    [0, 100]. Raises typed exceptions on violation.

    Pure kernel delegation (AD-5 + AD-11). Called by handlers BEFORE
    invoking the kernel validate_* functions to surface a clearer Korean
    envelope.
    """
    if not allocation_pcts:
        raise AbcValidationNotFoundError(
            ABC_VALIDATION_NOT_FOUND_KO,
            target=target,
            target_id=target_id,
        )

    for idx, value in enumerate(allocation_pcts):
        if not isinstance(value, Decimal):
            if target == "cost_pool":
                raise CostPoolValidationError(
                    f"원가풀 항목은 0 이상 100 이하의 숫자여야 합니다 (행 {idx})",
                    department_id=f"{target}[{idx}]",
                    sum_pct=Decimal("0"),
                    reason="type_mismatch",
                )
            if target == "activity":
                raise ActivityValidationError(
                    f"활동 항목은 0 이상 100 이하의 숫자여야 합니다 (행 {idx})",
                    cost_pool_id=f"{target}[{idx}]",
                    sum_pct=Decimal("0"),
                    reason="type_mismatch",
                )
            raise DriverValidationError(
                f"동인 항목은 0 이상 100 이하의 숫자여야 합니다 (행 {idx})",
                activity_id=f"{target}[{idx}]",
                sum_pct=Decimal("0"),
                reason="type_mismatch",
            )

        if value < Decimal("0") or value > Decimal("100"):
            if target == "cost_pool":
                raise CostPoolValidationError(
                    f"원가풀 항목은 0 이상 100 이하여야 합니다 (행 {idx})",
                    department_id=f"{target}[{idx}]",
                    sum_pct=Decimal("0"),
                    reason="out_of_range",
                )
            if target == "activity":
                raise ActivityValidationError(
                    f"활동 항목은 0 이상 100 이하여야 합니다 (행 {idx})",
                    cost_pool_id=f"{target}[{idx}]",
                    sum_pct=Decimal("0"),
                    reason="out_of_range",
                )
            raise DriverValidationError(
                f"동인 항목은 0 이상 100 이하여야 합니다 (행 {idx})",
                activity_id=f"{target}[{idx}]",
                sum_pct=Decimal("0"),
                reason="out_of_range",
            )


class AbcValidationService:
    """Story 9.1 — PRD §F9.1 ABC 100% validation orchestrator.

    Thin orchestration wrapper around `packages.cost_engine.abc_engine`
    pure kernel. tenant_settings.abc.drivers JSONB storage I/O (1차 MVP
    scaffold per Story 1.2) lives here; pure logic lives in the kernel.

    9-1 is VALIDATION-ONLY (no INSERT/UPDATE/DELETE on fiscal_period_snapshots).
    CR 1.1 invariant — no audit emit.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.trace_id = trace_id

    async def validate_100_percent_guard(
        self,
        *,
        cost_pool: list[Decimal] | None = None,
        activities: list[Decimal] | None = None,
        drivers: list[Decimal] | None = None,
        cost_pool_id: str = "<unknown>",
        activity_id: str = "<unknown>",
    ) -> AbcValidationState:
        """PRD §F9.1 verbatim 3-layer 100% guard orchestrator.

        1. Service-layer pre-validation (CR 12-5 L3 3-layer defense).
        2. Delegate to kernel `validate_100_percent_guard` (pure).
        3. Convert to AbcValidationState DTO (CR 12-1 L3 boundary).
        4. Return state (does NOT raise on is_valid=False — frontend
           disabled signal uses is_valid=False directly).

        Raises:
          CostPoolValidationError — invalid cost pool input (422).
          ActivityValidationError — invalid activity input (422).
          DriverValidationError — invalid driver input (422).
          AbcValidationNotFoundError — empty input list (404).
        """
        # 1. Service-layer pre-validation (CR 12-5 L3 3-layer defense).
        if cost_pool is not None:
            validate_abc_pct_list(
                allocation_pcts=cost_pool,
                target="cost_pool",
                target_id=cost_pool_id,
            )
        if activities is not None:
            validate_abc_pct_list(
                allocation_pcts=activities,
                target="activity",
                target_id=cost_pool_id,
            )
        if drivers is not None:
            validate_abc_pct_list(
                allocation_pcts=drivers,
                target="driver",
                target_id=activity_id,
            )

        # 2. Delegate to kernel (pure).
        guard_result = validate_100_percent_guard(
            cost_pool=cost_pool,
            activities=activities,
            drivers=drivers,
            cost_pool_id=cost_pool_id,
            activity_id=activity_id,
        )

        # 3. Convert to DTO (CR 12-1 L3 boundary).
        return _to_validation_state(guard_result)

    async def validate_cost_pool_only(
        self,
        *,
        department_id: str,
        allocation_pcts: list[Decimal],
    ) -> CostPoolValidation:
        """Validate cost pool 100% 가드 (단일 layer, 1차 MVP endpoint).

        1. Service-layer pre-validation (CR 12-5 L3).
        2. Delegate to kernel `validate_cost_pool`.
        3. Return CostPoolValidation (does NOT raise on is_valid=False).

        Raises:
          CostPoolValidationError — invalid input (422).
          AbcValidationNotFoundError — empty input (404).
        """
        validate_abc_pct_list(
            allocation_pcts=allocation_pcts,
            target="cost_pool",
            target_id=department_id,
        )
        return validate_cost_pool(
            department_id=department_id,
            allocation_pcts=allocation_pcts,
        )

    async def validate_activity_only(
        self,
        *,
        cost_pool_id: str,
        activity_pcts: list[Decimal],
    ) -> ActivityValidation:
        """Validate activity 100% 가드 (단일 layer, 1차 MVP endpoint)."""
        validate_abc_pct_list(
            allocation_pcts=activity_pcts,
            target="activity",
            target_id=cost_pool_id,
        )
        return validate_activity(
            cost_pool_id=cost_pool_id,
            activity_pcts=activity_pcts,
        )

    async def validate_driver_only(
        self,
        *,
        activity_id: str,
        driver_pcts: list[Decimal],
    ) -> DriverValidation:
        """Validate driver 100% 가드 (단일 layer, 1차 MVP endpoint)."""
        validate_abc_pct_list(
            allocation_pcts=driver_pcts,
            target="driver",
            target_id=activity_id,
        )
        return validate_driver(
            activity_id=activity_id,
            driver_pcts=driver_pcts,
        )

    async def compute_validation_hash_for_state(
        self,
        *,
        validation_state: ValidationState,
    ) -> str:
        """V8 determinism hash for any ValidationState (convenience wrapper)."""
        return compute_validation_hash(validation_state=validation_state)

    async def fetch_tenant_abc_drivers(self) -> list[dict[str, Any]]:
        """Fetch tenant_settings.abc.drivers JSONB list (Story 1.2 scaffold).

        Read-only — no audit emit per CR 1.1 invariant.

        Returns:
          list of dict (driver_name, unit, practical_capacity_hours).
        """
        settings = await SettingsService(self.session).get_tenant_settings(
            tenant_id=self.tenant_id,
        )
        abc = dict(settings.abc or {})
        drivers: list[dict[str, Any]] = list(abc.get("drivers") or [])
        return drivers


# Serialization helper (CR 11-4 D-002 ko-KR.json SSOT — re-export).
serialize_validation_state_for_api = serialize_validation_state
