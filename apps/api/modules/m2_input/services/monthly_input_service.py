"""apps.api.modules.m2_input.services.monthly_input_service — Story 3.1 + 3.2 + 3.3.

Writes/reads on the ``monthly_input_periods`` + ``monthly_input_rows``
tables (PRD §8.M2). All state-changing operations write a typed
``audit_logs`` row BEFORE the data write (AD-2), with idempotent
no-op skip on identical payloads (CR 1.1 lesson).

Story 3.1 surfaces:
- `get_or_create_period` — period row bootstrap (mode='month_total',
  baseline_revision=1)
- `save_row` — INSERT/UPDATE row with idempotent no-op detection
- `set_mode` — 일자별 ↔ 월합계 toggle (no revision bump)
- `get_state` — page-mount payload (rows + completion + fte_display)
- `compute_labor_fte` — read-only FTE display for the [인원] tab
- `delete_row` — DELETE + audit (PRD §8.M2 user-input, not ledger)

Story 3.2 additions (Tasks 3.1 / 3.2):
- `_validate_labor_shape` — `pay_type='daily'|'monthly'`별 필수 필드
  검사 (AC #4). pay_type=None on labor stream → 400.
- `_load_payroll_settings` — `tenant_settings.payroll` JSONB sub-block
  읽고 `DEFAULT_PAYROLL`과 per-field merge.
- `_compute_fte_for_state` — Story 3.1 stub 교체. `build_fte_display`
  composition dispatcher with pay_type branching.
- `validate_payroll_override` — public helper for future Story 0.5
  plumbing (settings UI에서 사용).
- 5 new typed exceptions: MonthlyInputInvalidLaborShapeError,
  MonthlyInputFteReadOnlyError, MonthlyInputPayrollSettingsInvalidError,
  MonthlyInputCompanyBurdenRateError, MonthlyInputPayTypeMismatchError.

Story 3.3 additions (Tasks 3.1 / 3.2):
- `_compute_warnings_aggregate_for_state` — dispatcher that computes
  inventory projection + operating rate warnings (PRD §V3·V5).
- `_load_opening_balance` — reads `period.opening_inventory` JSONB
  and converts to `dict[UUID, Decimal]` (MVP default 0 fallback).
- `_load_product_map_for_period` — distinct product metadata keyed by
  `product_id` (for `_ProductLike` protocol in `warnings.py`).
- `_compute_operating_rate_warning_for_state` — feeds operating_rate
  pure helpers (PRD §6.1 (2) 조업도 체인).
- `get_state` extends its `MonthlyInputStateResponse` with the 4
  new fields: `warnings: list[WarningResponse]`, `is_blocked: bool`,
  `warnings_count: int`, `top_n_severity: int`.
- 2 new typed exceptions (defense-in-depth):
  `MonthlyInputWarningsReadOnlyError` (400) and
  `MonthlyInputInventoryProjectionError` (422).

Layering (AD-1 / AD-11):
- Pure helpers live in ``packages/services/m2_input/``.
- This module wires them to SQLAlchemy + FastAPI dependencies.
- It does NOT import ``packages.cost_engine`` (AD-11 layer rule).

Concurrency:
- Natural key uniqueness is enforced by the database (partial unique
  index on (tenant_id, period_id, stream, COALESCE(product_id, 0),
  COALESCE(day_no, 0))). The service pre-validates for typed 4xx
  responses where possible.
- Period rows are not locked at the row level here; concurrent saves
  are handled by the DB-level conflict (which surfaces as 409).

Warning aggregate policy (PRD §A11):
- Input-time (`save_row` / `update_row` / `set_mode`): return 200 OK
  with `warnings[]` + `is_blocked`. The advisory state travels back
  to the frontend; operator CAN proceed.
- Close-time (Epic 4 first_calc): defer the blocking-rule policy to
  Epic 4 — `is_blocked=true` triggers the [마감] button's hard block.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, NamedTuple

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import (
    MonthlyInputPeriod,
    MonthlyInputRow,
    Product,
    TenantSettings,
)
from apps.api.modules.m2_input.schemas import (
    FteDisplay,
    MonthlyInputRowCreate,
    MonthlyInputRowResponse,
    MonthlyInputRowUpdate,
    MonthlyInputStateResponse,
    PayrollSettingsResponse,
    PayTypeBreakdownResponse,
    WarningResponse,
)
from packages.common.uuid7 import uuid7 as _uuid7
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m2_input.inventory_projection import (
    InventoryMovement,
)
from packages.services.m2_input.labor_conversion import (
    DEFAULT_PAYROLL,
    PayrollSettings,
    PayType,
    merge_payroll_settings,
)
from packages.services.m2_input.operating_rate import (
    DEFAULT_UNIT_TIME_HOURS,
    compute_operating_rate,
    compute_production_required_hours,
    compute_total_available_hours,
)
from packages.services.m2_input.stream_completion import (
    compute_stream_completion,
)
from packages.services.m2_input.warnings import (
    SEVERITY_ORDER,
    Warning,
    aggregate_warnings,
    build_inventory_warnings,
    build_operating_rate_warning,
)

# ── Constants ────────────────────────────────────────────────
# PRD default monthly salary basis (Story 3.2 may extend with
# tenant_settings.payroll override). 2,500,000원 is the MVP fallback.
DEFAULT_MONTHLY_SALARY_BASIS_KRW: int = 2_500_000

# PRD default workdays in a month (Story 3.2 may extend with calendar).
DEFAULT_WORKDAYS_IN_MONTH: int = 22

# Stream-conditional required fields (PRD §8.M2(b)).
# - labor / expenses → product_id is OPTIONAL (None OK)
# - orders / production / sales / purchases → product_id is REQUIRED
# - labor stream → workers/days_per_worker/daily_wage_krw are meaningful
_STREAMS_REQUIRING_PRODUCT: frozenset[str] = frozenset(
    {"orders", "production", "sales", "purchases"}
)

# Capability gate — only manufacturing-kind industries can write the
# production stream (PRD §8.M2(b); see `Capability.MONTHLY_INPUT_PRODUCTION`).
_PRODUCTION_STREAM = "production"


# ── Typed exceptions (mapped to HTTP by handlers.py) ────────
class MonthlyInputNotFoundError(Exception):
    """404 MONTHLY_INPUT_NOT_FOUND — row or period missing for the tenant."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str | None = None,
        row_id: uuid.UUID | None = None,
        trace_id: str,
    ) -> None:
        if row_id is not None:
            super().__init__(
                f"row {row_id} not found for tenant {tenant_id}"
            )
        else:
            super().__init__(
                f"period {period_key} not found for tenant {tenant_id}"
            )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.row_id = row_id
        self.trace_id = trace_id


class MonthlyInputInvalidPayloadError(Exception):
    """400 MONTHLY_INPUT_INVALID_PAYLOAD — semantic validation failure."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"invalid monthly input payload: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


class MonthlyInputPeriodLockedError(Exception):
    """409 MONTH_INPUT_PERIOD_LOCKED — period locked by calculation (Epic 4 first_calc)."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"period {period_key} for tenant {tenant_id} is locked by calculation"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class MonthlyInputCapabilityError(Exception):
    """403 INDUSTRY_NOT_SUPPORTED — production stream not supported by tenant's industry.

    Mirrors the `Capability.MONTHLY_INPUT_PRODUCTION` gate (PRD §8.M2(b)).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        current_industry: Industry | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"industry {current_industry!r} cannot use production stream"
        )
        self.tenant_id = tenant_id
        self.current_industry = current_industry
        self.trace_id = trace_id


class MonthlyInputStreamNotSupportedError(Exception):
    """403 MONTHLY_INPUT_STREAM_NOT_SUPPORTED — stream not in tenant's capability mask.

    Distinct from `MonthlyInputCapabilityError`: this fires for any of the
    6 streams if the tenant's industry doesn't include it in
    `STREAMS_FOR_INDUSTRY`. Currently only `production` can trip this for
    service tenants — but the error code is generic for forward-compat
    (Epic 4 may add industry-conditional streams).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        stream: str,
        current_industry: Industry | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"stream {stream!r} not supported for industry {current_industry!r}"
        )
        self.tenant_id = tenant_id
        self.stream = stream
        self.current_industry = current_industry
        self.trace_id = trace_id


# ── Story 3.2 typed exceptions (Tasks 3.2) ─────────────────
class MonthlyInputInvalidLaborShapeError(Exception):
    """400 MONTHLY_INPUT_INVALID_LABOR_SHAPE — `_validate_labor_shape` violation.

    Story 3.2 AC #4: pay_type='daily' requires `workers>0,
    days_per_worker>0, daily_wage_krw>0` and forbids
    `monthly_salary_basis_krw`; pay_type='monthly' requires
    `workers>0, monthly_salary_basis_krw>0`. pay_type=None on a labor
    row is rejected (Story 3.1's implicit-None gate is gone — the FTE
    precision pipeline needs the discriminator).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"invalid monthly input labor shape: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


class MonthlyInputFteReadOnlyError(Exception):
    """400 MONTHLY_INPUT_FTE_READ_ONLY — direct write on `fte_headcount` or
    `fte_wage_krw` (AC #5).

    These two fields are DERIVED from `build_fte_display`. A handler
    that tries to PATCH them returns 400 — the UI must mutate the
    underlying payroll fields (workers / days_per_worker /
    daily_wage_krw / breakdown fields) and let the service recompute.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        field: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"field {field!r} is read-only (derived from FTE pipeline)"
        )
        self.tenant_id = tenant_id
        self.field = field
        self.trace_id = trace_id


class MonthlyInputPayrollSettingsInvalidError(Exception):
    """400 MONTHLY_INPUT_PAYROLL_SETTINGS_INVALID —
    `tenant_settings.payroll.*` value out of range.

    Triggered when `merge_payroll_settings` raises ValueError because
    an override is malformed (e.g., `workdays_in_month=0`,
    `company_burden_rate=-0.1`). The Pydantic schema cannot validate
    this because the override is JSONB-shape (free-form dict), so the
    service performs the re-check at write time.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"invalid payroll settings: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


class MonthlyInputCompanyBurdenRateError(Exception):
    """422 MONTHLY_INPUT_COMPANY_BURDEN_RATE — schema-level `company_burden_rate`
    out-of-range detected at the service boundary.

    Pydantic v2 already rejects at the schema (Field ge=0, le=1); this
    exception is a service-side re-check that catches writes which
    bypass the Pydantic layer (raw DB path, migration bootstrap).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        value: Any,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"company_burden_rate {value!r} out of range [0, 1]"
        )
        self.tenant_id = tenant_id
        self.value = value
        self.trace_id = trace_id


class MonthlyInputPayTypeMismatchError(Exception):
    """400 MONTHLY_INPUT_PAY_TYPE_MISMATCH — incompatible labor-field
    combinations across `pay_type`.

    Example: `pay_type='daily'` with `monthly_salary_basis_krw` set
    (which only makes sense for monthly mode). The `_validate_labor_shape`
    rejection is caught here as a typed 400 instead of generic
    `MonthlyInputInvalidLaborShapeError` so the frontend can show a
    specific hint ("daily mode doesn't use monthly_salary_basis_krw").
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"pay_type mismatch: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


# ── Story 3.3 typed exceptions (Tasks 3.2) ─────────────────
class MonthlyInputWarningsReadOnlyError(Exception):
    """400 MONTHLY_INPUT_WARNINGS_READ_ONLY — AC #7 server-side defense.

    `warnings` / `is_blocked` / `warnings_count` / `top_n_severity`
    are DERIVED. PATCH attempts against `MonthlyInputRowUpdate`
    surface as `extra_fields_not_allowed` via Pydantic v2's
    `extra="forbid"` config (`MonthlyInputRowUpdate` does NOT
    declare these fields; AD-15 contract).

    This typed exception fires only as defense-in-depth — raw DB
    paths (migration bootstrap, internal scripts) that bypass
    Pydantic. Mapped to 400 MONTHLY_INPUT_WARNINGS_READ_ONLY by
    the handler-level exception handler (`main.py` — Task 4).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        field: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"field {field!r} is read-only (derived from warning pipeline)"
        )
        self.tenant_id = tenant_id
        self.field = field
        self.trace_id = trace_id


class MonthlyInputInventoryProjectionError(Exception):
    """422 MONTHLY_INPUT_INVENTORY_PROJECTION — projection kernel failure.

    Fires when `_compute_warnings_aggregate_for_state` cannot reach
    a deterministic projection. Triggers:
    - Negative `opening_qty` in `period.opening_inventory` JSONB
      (defensive — pure kernel rejects `closing<0` from opening<0)
    - Decimal overflow / type confusion (defensive — pure kernel uses
      `QTY_QUANTUM = Decimal("0.0001")` so this only fires on
      truly corrupt input)
    - Missing product metadata for ALL inventory-bearing rows
      (defensive — `_DummyProduct` fallback is in place, so this
      only fires on internal Python errors)

    Mapped to 422 by `main.py` — AD-15 §4 typed envelope.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"inventory projection failed: {details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


# ── Service class ────────────────────────────────────────────
class MonthlyInputService:
    """Story 3.1 — M2 monthly input capture service.

    `tenant_id` and `industry` flow from the FastAPI handler:
    `tenant_id` from `TenantContext`, `industry` from the tenant_settings
    JSONB onboarding.industry (passed as a parameter — this service does
    NOT read tenant_settings itself; the handler does that to keep the
    service focused on the row+period CRUD).
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        industry: Industry | None,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.industry = industry
        self.trace_id = trace_id

    # ── Period bootstrap ─────────────────────────────────────
    async def get_or_create_period(
        self, period_key: str
    ) -> MonthlyInputPeriod:
        """Return the period row for (tenant, period_key, baseline_revision=1).

        Inserts a new row with `mode='month_total', baseline_revision=1,
        locked_by_calculation=false` if missing. Idempotent — concurrent
        calls during the first page mount are safe (UNIQUE constraint
        surfaces as IntegrityError, which we swallow).
        """
        existing = await self.session.scalar(
            select(MonthlyInputPeriod).where(
                MonthlyInputPeriod.tenant_id == self.tenant_id,
                MonthlyInputPeriod.period_key == period_key,
                MonthlyInputPeriod.baseline_revision == 1,
            )
        )
        if existing is not None:
            return existing
        now = datetime.now(tz=UTC)
        period = MonthlyInputPeriod(
            period_id=_uuid7(),
            tenant_id=self.tenant_id,
            period_key=period_key,
            mode="month_total",
            baseline_revision=1,
            locked_by_calculation=False,
            created_at=now,
            updated_at=now,
        )
        self.session.add(period)
        try:
            await self.session.flush()
        except IntegrityError:
            # Concurrent INSERT — fetch the existing row.
            await self.session.rollback()
            existing = await self.session.scalar(
                select(MonthlyInputPeriod).where(
                    MonthlyInputPeriod.tenant_id == self.tenant_id,
                    MonthlyInputPeriod.period_key == period_key,
                    MonthlyInputPeriod.baseline_revision == 1,
                )
            )
            if existing is None:
                raise
            return existing
        return period

    # ── Stream-conditional validation ────────────────────────
    def _validate_stream_shape(self, payload: MonthlyInputRowCreate) -> None:
        """Reject obviously-wrong shapes with 400 before touching the DB.

        Per PRD §8.M2(b):
        - orders / production / sales / purchases → product_id required
        - labor / expenses → product_id must be None (service rejects)
        - production → industry capability check

        Story 5.1 — `opening_inventory` is auto-carried after first-row
        lock; manual row write rejected (PRD §F4.1).
        """
        # M1: Pydantic Literal auto-reject (opening_inventory는 valid set에서 제외)
        if payload.stream not in (
            "orders",
            "production",
            "sales",
            "purchases",
            "expenses",
            "labor",
        ):
            raise MonthlyInputInvalidPayloadError(
                tenant_id=self.tenant_id,
                details={"field": "stream", "value": payload.stream},
                trace_id=self.trace_id,
            )
        # Story 5.1 — manual edit on opening_inventory rejected
        # opening_inventory는 Literal 검증으로 자동 차단됨 (M1 fix)
        if payload.stream == "opening_inventory":
            from apps.api.modules.m4_inventory.services.opening_carry_service import (
                MonthlyInputOpeningManualEditError,
            )

            raise MonthlyInputOpeningManualEditError(
                tenant_id=self.tenant_id,
                period_key=payload.period_key,
                trace_id=self.trace_id,
            )
        if payload.stream in _STREAMS_REQUIRING_PRODUCT:
            if payload.product_id is None:
                raise MonthlyInputInvalidPayloadError(
                    tenant_id=self.tenant_id,
                    details={
                        "field": "product_id",
                        "reason": (
                            f"stream {payload.stream!r} requires a product_id"
                        ),
                    },
                    trace_id=self.trace_id,
                )
        else:  # labor, expenses
            if payload.product_id is not None:
                raise MonthlyInputInvalidPayloadError(
                    tenant_id=self.tenant_id,
                    details={
                        "field": "product_id",
                        "reason": (
                            f"stream {payload.stream!r} does not take product_id"
                        ),
                    },
                    trace_id=self.trace_id,
                )

    # ── Save row (POST / PATCH) ──────────────────────────────
    async def save_row(
        self,
        period_key: str,
        payload: MonthlyInputRowCreate,
        actor_id: uuid.UUID,
    ) -> tuple[MonthlyInputRowResponse, dict[str, bool], list[str]]:
        """Insert or update a row with audit-first + idempotent no-op.

        Returns (row_response, completion_dict, missing_labels).

        Logic:
        1. Validate payload shape (stream-conditional requirements)
        2. **Story 3.2** Validate labor shape when stream='labor'
           (`_validate_labor_shape` — pay_type 분기)
        3. Resolve period (auto-create if missing)
        4. Capability gate: production stream → industry check
        5. SELECT FOR UPDATE existing row by natural key
        6. **Story 3.2** Idempotent no-op compares the FULL
           13-field snapshot (CR 1.1 lesson — extend tuple, do not
           shrink)
        7. emit_audit with before/after snapshot (CR 1.1 lesson)
        8. INSERT or UPDATE the row
        9. Recompute completion + missing list
        """
        self._validate_stream_shape(payload)
        # Story 3.2 — labor shape (pay_type 분기) validation. Only fires
        # for stream == 'labor' — 400 INVALID_LABOR_SHAPE on shape mismatch.
        if payload.stream == "labor":
            self._validate_labor_shape(payload)

        if payload.stream == _PRODUCTION_STREAM:
            from packages.services.m2_input.stream_completion import (
                STREAMS_FOR_INDUSTRY,
            )

            if (
                self.industry is None
                or _PRODUCTION_STREAM
                not in STREAMS_FOR_INDUSTRY.get(self.industry, frozenset())
            ):
                raise MonthlyInputCapabilityError(
                    tenant_id=self.tenant_id,
                    current_industry=self.industry,
                    trace_id=self.trace_id,
                )

        period = await self.get_or_create_period(period_key)

        if period.locked_by_calculation:
            raise MonthlyInputPeriodLockedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        # SELECT FOR UPDATE existing row (CR 1.1)
        existing = await self.session.scalar(
            select(MonthlyInputRow)
            .where(
                MonthlyInputRow.tenant_id == self.tenant_id,
                MonthlyInputRow.period_id == period.period_id,
                MonthlyInputRow.stream == payload.stream,
            )
            .where(MonthlyInputRow.product_id.is_(payload.product_id))
            .where(MonthlyInputRow.day_no.is_(payload.day_no))
            .with_for_update()
        )

        new_fields = {
            "qty": payload.qty,
            "unit_price_krw": payload.unit_price_krw,
            "amount_krw": payload.amount_krw,
            "workers": payload.workers,
            "days_per_worker": payload.days_per_worker,
            "daily_wage_krw": payload.daily_wage_krw,
            "memo": payload.memo,
            # Story 3.2 — FTE precision fields. All None for non-labor
            # streams; populated on labor stream per `_validate_labor_shape`.
            "pay_type": payload.pay_type,
            "monthly_salary_basis_krw": payload.monthly_salary_basis_krw,
            "overtime_krw": payload.overtime_krw,
            "welfare_krw": payload.welfare_krw,
            "bonus_krw": payload.bonus_krw,
            "retirement_reserve_krw": payload.retirement_reserve_krw,
            "company_burden_rate": payload.company_burden_rate,
        }

        now = datetime.now(tz=UTC)

        if existing is not None:
            # Idempotent no-op detection (CR 1.1)
            if all(
                getattr(existing, k) == v for k, v in new_fields.items()
            ):
                # Same-value POST → 200 + no audit + no version bump
                completion = await self._compute_completion_dict(period)
                missing = self._missing_labels(completion)
                return (
                    self._row_to_response(existing, mode=period.mode, period_key=period_key),
                    completion,
                    missing,
                )
            # Mutating PATCH → audit + update
            before = {
                k: getattr(existing, k) for k in new_fields
            }
            for k, v in new_fields.items():
                setattr(existing, k, v)
            existing.updated_at = now
            # Story 4.3 (A5 Phase 1) — typed emit wrapper.
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.MONTHLY_INPUT_ROW,
                action="monthly_input_row_updated",
                actor_id=actor_id,
                target_id=existing.row_id,
                payload={
                    "tenant_id": str(self.tenant_id),
                    "period_key": period_key,
                    "stream": payload.stream,
                    "product_id": str(payload.product_id) if payload.product_id else None,
                    "day_no": payload.day_no,
                    "before": _decimalize(before),
                    "after": _decimalize(new_fields),
                    "trace_id": self.trace_id,
                },
                tenant_id=self.tenant_id,
                flush=True,
            )
            completion = await self._compute_completion_dict(period)
            missing = self._missing_labels(completion)
            return (
                self._row_to_response(existing, mode=period.mode, period_key=period_key),
                completion,
                missing,
            )

        # INSERT new row
        new_row = MonthlyInputRow(
            row_id=_uuid7(),
            tenant_id=self.tenant_id,
            period_id=period.period_id,
            stream=payload.stream,
            product_id=payload.product_id,
            day_no=payload.day_no,
            qty=payload.qty,
            unit_price_krw=payload.unit_price_krw,
            amount_krw=payload.amount_krw,
            workers=payload.workers,
            days_per_worker=payload.days_per_worker,
            daily_wage_krw=payload.daily_wage_krw,
            memo=payload.memo,
            # Story 3.2 — FTE precision fields
            pay_type=payload.pay_type,
            monthly_salary_basis_krw=payload.monthly_salary_basis_krw,
            overtime_krw=payload.overtime_krw,
            welfare_krw=payload.welfare_krw,
            bonus_krw=payload.bonus_krw,
            retirement_reserve_krw=payload.retirement_reserve_krw,
            company_burden_rate=payload.company_burden_rate,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_row)
        try:
            await self.session.flush()
        except IntegrityError as err:
            await self.session.rollback()
            # The partial unique index collision means another row with
            # the same natural key already exists (concurrent insert).
            raise MonthlyInputInvalidPayloadError(
                tenant_id=self.tenant_id,
                details={
                    "reason": "natural_key_collision",
                    "stream": payload.stream,
                    "product_id": str(payload.product_id) if payload.product_id else None,
                    "day_no": payload.day_no,
                },
                trace_id=self.trace_id,
            ) from err

        # Story 5.1 (Epic 5) — first-row INSERT triggers opening lock.
        # PRD §F4.1: 이후 수동 입력은 차단한다. Lock marker is added to
        # opening_inventory JSONB; future POSTs on stream='opening_inventory'
        # return 400 MONTHLY_INPUT_OPENING_MANUAL_EDIT.
        from apps.api.modules.m4_inventory.services.opening_carry_service import (
            OpeningCarryService,
        )

        carry_svc = OpeningCarryService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )
        await carry_svc.lock_opening_after_first_row(
            period, actor_id=actor_id
        )

        # H2: T3.3 hook wire — prev period row mutation 시 chain propagation
        # AC #3 explicit "chain" — auto-recompute stale value
        from apps.api.modules.m4_inventory.services.opening_carry_service import (
            _prev_period_key as _carry_prev_period_key,
        )
        prev_period_key = _carry_prev_period_key(period.period_key)
        if prev_period_key is not None:
            await carry_svc.recompute_opening_on_prev_change(
                prev_period_key, actor_id=actor_id
            )

        # Story 5.2 (Epic 5) — inventory_ledger event emit on INSERT.
        # AC #4 stream → ledger event mapping:
        # - 'purchases'     → 'purchase_inbound'  (PRD §6.2 입고)
        # - 'sales'         → 'sales_outbound'    (PRD §6.2 출고)
        # - 'production'    → 'production_output_inbound' (output product_qty)
        #                       — deferral 9: production_material_consumption
        #                         requires BOM explosion (post-MVP)
        # - 'orders'|'expenses'|'labor' → no emit (no inventory impact)
        #
        # Idempotent: LedgerService.append_event skip on duplicate
        # (tenant_id, product_id, period_key, event_type, trace_id) 4-tuple
        # (CR 1.1). PATCH update path does NOT emit (corrections flow via
        # Epic 11 reversal — AD-22 forward-fill).
        if payload.stream in ("purchases", "sales", "production") and payload.product_id is not None and payload.qty is not None:
            await self._emit_inventory_ledger_event_for_row(
                new_row=new_row,
                period_key=period.period_key,
                stream=payload.stream,
                actor_id=actor_id,
            )

        # Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.MONTHLY_INPUT_ROW,
            action="monthly_input_row_created",
            actor_id=actor_id,
            target_id=new_row.row_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
                "stream": payload.stream,
                "product_id": str(payload.product_id) if payload.product_id else None,
                "day_no": payload.day_no,
                "after": _decimalize(new_fields),
                "trace_id": self.trace_id,
            },
            tenant_id=self.tenant_id,
            flush=True,
        )
        completion = await self._compute_completion_dict(period)
        missing = self._missing_labels(completion)
        return (
            self._row_to_response(new_row, mode=period.mode, period_key=period_key),
            completion,
            missing,
        )

    # ── Update row (PATCH) ───────────────────────────────────
    async def update_row(
        self,
        period_key: str,
        row_id: uuid.UUID,
        payload: MonthlyInputRowUpdate,
        actor_id: uuid.UUID,
    ) -> tuple[MonthlyInputRowResponse, dict[str, bool], list[str]]:
        """PATCH a row — partial update with audit-first + idempotent no-op.

        `exclude_unset=True` semantics are honored at the Pydantic
        boundary (handlers pass `payload.model_dump(exclude_unset=True)`).
        This service receives only the explicitly-set fields.
        """
        period = await self.get_or_create_period(period_key)

        if period.locked_by_calculation:
            raise MonthlyInputPeriodLockedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        existing = await self.session.scalar(
            select(MonthlyInputRow)
            .where(
                MonthlyInputRow.tenant_id == self.tenant_id,
                MonthlyInputRow.row_id == row_id,
                MonthlyInputRow.period_id == period.period_id,
            )
            .with_for_update()
        )
        if existing is None:
            raise MonthlyInputNotFoundError(
                tenant_id=self.tenant_id,
                row_id=row_id,
                trace_id=self.trace_id,
            )

        patch = payload.model_dump(exclude_unset=True)
        if not patch:
            # Empty PATCH → idempotent no-op
            completion = await self._compute_completion_dict(period)
            missing = self._missing_labels(completion)
            return (
                self._row_to_response(existing, mode=period.mode, period_key=period_key),
                completion,
                missing,
            )

        before = {k: getattr(existing, k) for k in patch}
        if all(before[k] == patch[k] for k in patch):
            # Same-value PATCH → no audit
            completion = await self._compute_completion_dict(period)
            missing = self._missing_labels(completion)
            return (
                self._row_to_response(existing, mode=period.mode, period_key=period_key),
                completion,
                missing,
            )

        for k, v in patch.items():
            setattr(existing, k, v)
        existing.updated_at = datetime.now(tz=UTC)
        # Story 4.3 (A5 Phase 1) — typed emit wrapper. Note: this is the
        # update_row PATCH path; same action literal as save_row update
        # path is intentional (CR 1.1 lesson: distinction lives in
        # payload.stream + the calling endpoint, not in the action).
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.MONTHLY_INPUT_ROW,
            action="monthly_input_row_updated",
            actor_id=actor_id,
            target_id=existing.row_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
                "stream": existing.stream,
                "before": _decimalize(before),
                "after": _decimalize(patch),
                "trace_id": self.trace_id,
            },
            tenant_id=self.tenant_id,
            flush=True,
        )
        completion = await self._compute_completion_dict(period)
        missing = self._missing_labels(completion)
        return (
            self._row_to_response(existing, mode=period.mode, period_key=period_key),
            completion,
            missing,
        )

    # ── Delete row ───────────────────────────────────────────
    async def delete_row(
        self,
        period_key: str,
        row_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """DELETE a row + audit (PRD §8.M2 user-input, not ledger).

        404 if not found; 409 if period is locked.
        """
        period = await self.get_or_create_period(period_key)
        if period.locked_by_calculation:
            raise MonthlyInputPeriodLockedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        result = await self.session.execute(
            delete(MonthlyInputRow).where(
                MonthlyInputRow.tenant_id == self.tenant_id,
                MonthlyInputRow.row_id == row_id,
                MonthlyInputRow.period_id == period.period_id,
            )
        )
        if result.rowcount == 0:
            raise MonthlyInputNotFoundError(
                tenant_id=self.tenant_id,
                row_id=row_id,
                trace_id=self.trace_id,
            )

        # Story 4.3 (A5 Phase 1) — typed emit wrapper.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.MONTHLY_INPUT_ROW,
            action="monthly_input_row_deleted",
            actor_id=actor_id,
            target_id=row_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
                "trace_id": self.trace_id,
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    # ── Mode toggle ──────────────────────────────────────────
    async def set_mode(
        self,
        period_key: str,
        mode: str,
        actor_id: uuid.UUID,
    ) -> MonthlyInputPeriod:
        """PATCH the period's mode (PRD F2.1 일자별/월합계).

        Does NOT bump baseline_revision — mode toggle is a UI preference,
        not a baseline change. Story 3.4 first_calc bumps the revision.
        """
        if mode not in ("month_total", "daily"):
            raise MonthlyInputInvalidPayloadError(
                tenant_id=self.tenant_id,
                details={"field": "mode", "value": mode},
                trace_id=self.trace_id,
            )

        period = await self.get_or_create_period(period_key)
        if period.locked_by_calculation:
            raise MonthlyInputPeriodLockedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )
        if period.mode == mode:
            return period  # no-op

        before = {"mode": period.mode}
        period.mode = mode
        period.updated_at = datetime.now(tz=UTC)
        # Story 4.3 (A5 Phase 1) — typed emit wrapper. ActionClass
        # MONTHLY_INPUT_PERIOD (not ROW) — distinct target_table.
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.MONTHLY_INPUT_PERIOD,
            action="monthly_input_mode_changed",
            actor_id=actor_id,
            target_id=period.period_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
                "before": before,
                "after": {"mode": mode},
                "trace_id": self.trace_id,
            },
            tenant_id=self.tenant_id,
            flush=True,
        )
        return period

    # ── State (page-mount payload) ───────────────────────────
    async def get_state(self, period_key: str) -> MonthlyInputStateResponse:
        """Return the page-mount payload (rows + completion + fte_display + warnings).

        The capability_mask is derived from the tenant's industry (no
        per-row visibility logic).

        Story 3.3 — appends the 4 warning aggregate fields at the end:
          - `warnings: list[WarningResponse]` — sorted (severity ASC +
            closing_qty ASC for inventory)
          - `is_blocked: bool` — `len(warnings) > 0`
          - `warnings_count: int` — UI echo
          - `top_n_severity: int` — most severe warning ordinal

        Story 5.1 — auto_carry_on_get_state hook. If opening_inventory
        is empty AND a prev period exists, run the carry chain (silent).
        Idempotent: if locked or already populated, no-op.
        """
        period = await self.get_or_create_period(period_key)

        # Story 5.1 (Epic 5) — auto-carry hook (silent, idempotent)
        from apps.api.modules.m4_inventory.services.opening_carry_service import (
            OpeningCarryService,
        )

        carry_svc = OpeningCarryService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )
        await carry_svc.auto_carry_on_get_state(period)

        rows = (
            await self.session.scalars(
                select(MonthlyInputRow)
                .where(
                    MonthlyInputRow.tenant_id == self.tenant_id,
                    MonthlyInputRow.period_id == period.period_id,
                )
                .order_by(
                    MonthlyInputRow.stream,
                    MonthlyInputRow.product_id,
                    MonthlyInputRow.day_no,
                )
            )
        ).all()
        completion = await self._compute_completion_dict(period)
        missing = self._missing_labels(completion)
        fte_display = await self._compute_fte_display(period)

        # capability_mask — visible streams for the tenant's industry
        from packages.services.m2_input.stream_completion import (
            STREAMS_FOR_INDUSTRY,
        )

        visible = STREAMS_FOR_INDUSTRY.get(
            self.industry, STREAMS_FOR_INDUSTRY[Industry.SERVICE]
        )

        # Fill period_key into row responses
        row_responses = [
            self._row_to_response(r, mode=period.mode, period_key=period_key)
            for r in rows
        ]

        # Story 3.3 (Task 3.1) — Warning aggregate dispatcher. Read-only
        # advisory (PRD §A11 입력 시); Epic 4 first_calc closes the
        # `is_blocked=true` → hard block hook.
        warnings, is_blocked, warnings_count, top_n_severity = (
            await self._compute_warnings_aggregate_for_state(
                period=period, rows=list(rows), fte_display=fte_display
            )
        )
        warning_responses = [_warning_to_response(w) for w in warnings]

        return MonthlyInputStateResponse(
            period_key=period_key,
            mode=period.mode,
            baseline_revision=period.baseline_revision,
            rows=row_responses,
            completion=completion,
            is_complete=all(completion.values()),
            missing=missing,
            capability_mask=sorted(visible),
            fte_display=fte_display,
            # Story 3.3 — warning aggregate (PRD §A11 오류의 가시화).
            warnings=warning_responses,
            is_blocked=is_blocked,
            warnings_count=warnings_count,
            top_n_severity=top_n_severity,
            # Story 5.1 — opening inventory auto-carry fields (PRD §F4.1).
            # Decimal serialization via str() — cross-language drift
            # prevention (AD-15).
            opening_inventory={
                k: str(v)
                for k, v in period.opening_inventory.items()
                if not k.startswith("_")
            },
            opening_inventory_locked=bool(
                period.opening_inventory.get("_locked", False)
            ),
            opening_inventory_lock_reason_ko=period.opening_inventory.get(
                "_lock_reason_ko"
            ),
        )

    # ── Helpers ──────────────────────────────────────────────
    async def _emit_inventory_ledger_event_for_row(
        self,
        *,
        new_row: MonthlyInputRow,
        period_key: str,
        stream: str,
        actor_id: uuid.UUID,
    ) -> None:
        """Story 5.2 — emit `inventory_ledger_event_appended` for a
        new monthly_input_rows row.

        Stream → event_type mapping (PRD §6.2):
        - 'purchases'  → 'purchase_inbound'
        - 'sales'      → 'sales_outbound'
        - 'production' → 'production_output_inbound'

        Caller MUST verify stream ∈ {purchases, sales, production} +
        product_id non-None + qty non-None before invoking.

        AD-22 reversal fields (reverses_event_id, correction_group_id)
        are NEVER set by 5-2 INSERT path — those are reserved for
        Epic 11 module authority INSERTs.

        Lazy import — LedgerService is in a sibling module; lazy import
        keeps startup clean + avoids any circular-import risk during
        test collection.
        """
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )
        from packages.services.m4_inventory.ledger import SOURCE_MONTHLY_INPUT

        stream_to_event_type = {
            "purchases": "purchase_inbound",
            "sales": "sales_outbound",
            "production": "production_output_inbound",
        }
        event_type = stream_to_event_type[stream]

        ledger_svc = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )
        await ledger_svc.append_event(
            product_id=new_row.product_id,  # type: ignore[arg-type]  # caller-guaranteed non-None
            period_key=period_key,
            event_type=event_type,
            qty=new_row.qty,
            source=SOURCE_MONTHLY_INPUT,
            reverses_event_id=None,  # Epic 11 forward-fill only
            correction_group_id=None,  # Epic 11 forward-fill only
            metadata={
                "monthly_input_row_id": str(new_row.row_id),
                "stream": stream,
                "day_no": new_row.day_no,
            },
            actor_id=actor_id,
        )

    async def _compute_completion_dict(
        self, period: MonthlyInputPeriod
    ) -> dict[str, bool]:
        rows_by_stream = dict(
            (
                await self.session.execute(
                    select(
                        MonthlyInputRow.stream,
                        func.count(MonthlyInputRow.row_id),
                    )
                    .where(
                        MonthlyInputRow.tenant_id == self.tenant_id,
                        MonthlyInputRow.period_id == period.period_id,
                    )
                    .group_by(MonthlyInputRow.stream)
                )
            ).all()
        )
        status = compute_stream_completion(self.industry, rows_by_stream)
        return {s: st.completed for s, st in status.streams.items()}

    def _missing_labels(self, completion: dict[str, bool]) -> list[str]:
        """Convert completion dict → ordered Korean labels (PRD §8.M2(b))."""
        from packages.services.m2_input.stream_completion import (
            STREAM_LABELS_KO,
            STREAM_ORDER,
        )

        return [
            STREAM_LABELS_KO[s]
            for s in STREAM_ORDER
            if s in completion and not completion[s]
        ]

    async def _compute_fte_display(
        self, period: MonthlyInputPeriod
    ) -> FteDisplay | None:
        """Story 3.1 / 3.2 hook — returns the page-mount `FteDisplay`.

        Story 3.2 replaces the inline `format_fte_headcount` /
        `compute_fte_wage_krw` path with `build_fte_display` so the
        pay_type 분기 + breakdown + source_rows come from the pure
        helper (single source of truth — drift prevention).

        Returns `None` if no labor rows exist for the period.
        """
        payroll = await self._load_payroll_settings(self.tenant_id)
        labor_rows = (
            await self.session.scalars(
                select(MonthlyInputRow).where(
                    MonthlyInputRow.tenant_id == self.tenant_id,
                    MonthlyInputRow.period_id == period.period_id,
                    MonthlyInputRow.stream == "labor",
                )
            )
        ).all()
        if not labor_rows:
            return None
        return self._compute_fte_for_state(
            labor_rows=labor_rows,
            payroll=payroll,
            period_mode=period.mode,
        )

    def _compute_fte_for_state(
        self,
        *,
        labor_rows: list[MonthlyInputRow],
        payroll: PayrollSettings,
        period_mode: str,
    ) -> FteDisplay:
        """Compose `FteDisplay` from labor rows via `build_fte_display`.

        Story 3.2 AC #1 (daily mode) / AC #2 (monthly mode):
        - mode='month_total' → 1 row typically; use its values directly
        - mode='daily' → up to 31 rows (day_no=1..31); sum workers /
          days / wages across days; build_fte_display uses payroll
          settings (workdays_in_month) to 환산.

        Backend Story 3.2 ships with month_total happy-path coverage;
        daily mode aggregation is delegated to `build_fte_display` in
        `labor_conversion.py`.
        """
        from packages.services.m2_input.labor_conversion import (
            build_fte_display as _build_display,
        )

        if not labor_rows:
            raise ValueError(
                "_compute_fte_for_state requires at least 1 labor row"
            )
        # Aggregate the rows based on pay_type. month_total typically
        # has 1 row (the row IS the month). daily may have up to 31.
        pay_types = {r.pay_type for r in labor_rows if r.pay_type}
        if not pay_types:
            # Mixed or missing — fall back to first row's classification
            # (defensive: Story 3.1 path allowed pay_type=None; in 3.2
            # _validate_labor_shape rejects that, so reaching here is
            # an edge case during transition).
            chosen = labor_rows[0]
        elif len(pay_types) > 1:
            # Mixed pay_types in one period — default to 'monthly'
            # (정규직 우선). The UI should prevent this; the service
            # is forgiving in case it slips through.
            chosen = next(
                r for r in labor_rows if r.pay_type == PayType.MONTHLY
            )
        else:
            chosen = labor_rows[0]

        workers = sum(int(r.workers or 0) for r in labor_rows)
        days_per_worker = sum(
            int(r.days_per_worker or 0) for r in labor_rows
        )
        daily_wage_krw = sum(
            int(r.daily_wage_krw or 0) for r in labor_rows
        )

        # Story 3.1 backward-compat aggregate fields
        total_workers = workers
        total_days = days_per_worker
        total_daily = daily_wage_krw

        # Coalesce type-aware fields
        _rate = chosen.company_burden_rate or Decimal("0")

        display = _build_display(
            pay_type=chosen.pay_type or PayType.MONTHLY,
            workers=workers,
            days_per_worker=days_per_worker if period_mode == "daily" else None,
            daily_wage_krw=daily_wage_krw if period_mode == "daily" else None,
            monthly_salary_basis_krw=(
                chosen.monthly_salary_basis_krw
                if (chosen.pay_type or PayType.MONTHLY) == PayType.MONTHLY
                else None
            ),
            overtime_krw=chosen.overtime_krw,
            welfare_krw=chosen.welfare_krw,
            bonus_krw=chosen.bonus_krw,
            retirement_reserve_krw=chosen.retirement_reserve_krw,
            company_burden_rate=_rate,
            payroll=payroll,
            source_rows=len(labor_rows),
        )

        # Compose the wire format FteDisplay (pydantic model — schema
        # validation here is a safety net against helper-schema drift).
        breakdown = display.breakdown or {}
        return FteDisplay(
            # Story 3.1 fields (kept for backward compat)
            total_workers=total_workers,
            total_days_per_worker=total_days,
            total_daily_wage_krw=total_daily,
            fte_headcount=display.fte_headcount,
            fte_wage_krw=display.fte_wage_krw,
            monthly_salary_basis_krw=(
                chosen.monthly_salary_basis_krw
                or payroll.monthly_salary_basis_krw
            ),
            # Story 3.2 additions
            pay_type=display.pay_type.value,
            breakdown=PayTypeBreakdownResponse(
                base_krw=breakdown.get("base_krw", 0),
                overtime_krw=breakdown.get("overtime_krw", 0),
                welfare_krw=breakdown.get("welfare_krw", 0),
                bonus_krw=breakdown.get("bonus_krw", 0),
                retirement_reserve_krw=breakdown.get(
                    "retirement_reserve_krw", 0
                ),
                retirement_burden_krw=breakdown.get(
                    "retirement_burden_krw", 0
                ),
                company_burden_rate=_rate,
                total_krw=breakdown.get("total_krw", 0),
            ),
            source_rows=display.source_rows,
            payroll_settings=PayrollSettingsResponse(
                monthly_salary_basis_krw=payroll.monthly_salary_basis_krw,
                workdays_in_month=payroll.workdays_in_month,
                standard_monthly_hours=payroll.standard_monthly_hours,
                company_burden_rate=payroll.company_burden_rate,
            ),
        )

    async def _load_payroll_settings(
        self, tenant_id: uuid.UUID
    ) -> PayrollSettings:
        """Load + merge per-tenant payroll override (Story 3.2 AC #3).

        Reads `tenant_settings.payroll` JSONB sub-block (added by
        Alembic 0010) and merges with `DEFAULT_PAYROLL` per-field. If
        the override is missing or empty, returns `DEFAULT_PAYROLL`
        unchanged. If `merge_payroll_settings` raises (out-of-range
        value), translates to typed `MonthlyInputPayrollSettingsInvalidError`.
        """
        result = await self.session.execute(
            select(TenantSettings).where(
                TenantSettings.tenant_id == tenant_id
            )
        )
        row = result.scalar_one_or_none()
        override: dict | None = None
        if row is not None and row.payroll:
            override = row.payroll
        try:
            return merge_payroll_settings(override, DEFAULT_PAYROLL)
        except ValueError as err:
            raise MonthlyInputPayrollSettingsInvalidError(
                tenant_id=tenant_id,
                details={"reason": str(err), "override": override or {}},
                trace_id=self.trace_id,
            ) from err

    def _validate_labor_shape(
        self, payload: MonthlyInputRowCreate
    ) -> None:
        """Story 3.2 AC #4 — validate labor-stream shape by `pay_type`.

        Rules:
        - `pay_type='daily'` → requires `workers>0, days_per_worker>0,
          daily_wage_krw>0`; `monthly_salary_basis_krw` MUST be None.
        - `pay_type='monthly'` → requires `workers>0,
          monthly_salary_basis_krw>0`; `days_per_worker` SHOULD be
          None (warn-only) but allowed for forward-compat.
        - `pay_type=None` on labor stream → 400 (Story 3.1's implicit
          None is gone; the FTE pipeline needs the discriminator).
        - `company_burden_rate` MUST be in [0, 1] if set
          (cross-checks against Pydantic Field validators).

        All branches raise typed exceptions so handlers can map to
        AD-15 error envelope.
        """
        if payload.pay_type is None:
            raise MonthlyInputInvalidLaborShapeError(
                tenant_id=self.tenant_id,
                details={
                    "field": "pay_type",
                    "reason": "labor stream requires pay_type "
                    "('monthly' or 'daily')",
                },
                trace_id=self.trace_id,
            )
        if payload.company_burden_rate is not None and not (
            Decimal("0")
            <= payload.company_burden_rate
            <= Decimal("1")
        ):
            raise MonthlyInputCompanyBurdenRateError(
                tenant_id=self.tenant_id,
                value=str(payload.company_burden_rate),
                trace_id=self.trace_id,
            )
        if payload.pay_type == PayType.DAILY:
            if (
                payload.workers is None
                or payload.workers <= 0
                or payload.days_per_worker is None
                or payload.days_per_worker <= 0
                or payload.daily_wage_krw is None
                or payload.daily_wage_krw <= 0
            ):
                raise MonthlyInputInvalidLaborShapeError(
                    tenant_id=self.tenant_id,
                    details={
                        "pay_type": "daily",
                        "reason": (
                            "daily mode requires "
                            "workers>0, days_per_worker>0, "
                            "daily_wage_krw>0"
                        ),
                    },
                    trace_id=self.trace_id,
                )
            if payload.monthly_salary_basis_krw is not None:
                raise MonthlyInputPayTypeMismatchError(
                    tenant_id=self.tenant_id,
                    details={
                        "pay_type": "daily",
                        "forbidden_field": "monthly_salary_basis_krw",
                    },
                    trace_id=self.trace_id,
                )
            return
        # pay_type == 'monthly'  # noqa: ERA001
        if (
            payload.workers is None
            or payload.workers <= 0
            or payload.monthly_salary_basis_krw is None
            or payload.monthly_salary_basis_krw <= 0
        ):
            raise MonthlyInputInvalidLaborShapeError(
                tenant_id=self.tenant_id,
                details={
                    "pay_type": "monthly",
                    "reason": (
                        "monthly mode requires "
                        "workers>0, monthly_salary_basis_krw>0"
                    ),
                },
                trace_id=self.trace_id,
            )
        if (
            payload.days_per_worker is not None
            and payload.days_per_worker > 0
        ):
            raise MonthlyInputPayTypeMismatchError(
                tenant_id=self.tenant_id,
                details={
                    "pay_type": "monthly",
                    "forbidden_field": "days_per_worker",
                },
                trace_id=self.trace_id,
            )

    def _row_to_response(
        self,
        row: MonthlyInputRow,
        *,
        mode: str,
        period_key: str = "",
    ) -> MonthlyInputRowResponse:
        return MonthlyInputRowResponse(
            row_id=row.row_id,
            period_id=row.period_id,
            period_key=period_key,
            stream=row.stream,
            product_id=row.product_id,
            day_no=row.day_no,
            qty=row.qty,
            unit_price_krw=row.unit_price_krw,
            amount_krw=row.amount_krw,
            workers=row.workers,
            days_per_worker=row.days_per_worker,
            daily_wage_krw=row.daily_wage_krw,
            memo=row.memo,
            mode=mode,
            # Story 3.2 — FTE precision fields
            pay_type=row.pay_type,
            monthly_salary_basis_krw=row.monthly_salary_basis_krw,
            overtime_krw=row.overtime_krw,
            welfare_krw=row.welfare_krw,
            bonus_krw=row.bonus_krw,
            retirement_reserve_krw=row.retirement_reserve_krw,
            company_burden_rate=row.company_burden_rate,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ── Story 3.3 — warning aggregate dispatcher ────────────
    async def _compute_warnings_aggregate_for_state(
        self,
        *,
        period: MonthlyInputPeriod,
        rows: list[MonthlyInputRow],
        fte_display: FteDisplay | None,
    ) -> tuple[list[Warning], bool, int, int]:
        """Compose PRD §V3 + §V5 warnings for the period's state.

        Story 3.3 (Task 3.1) — single dispatch site, called from
        `get_state`. Returns `(warnings, is_blocked, warnings_count,
        top_n_severity)` where:

        - `warnings`: sorted list of `Warning` (severity ASC +
          inventory closing_qty ASC)
        - `is_blocked`: `len(warnings) > 0` (PRD §A11 input-time)
        - `warnings_count`: UI echo
        - `top_n_severity`: most severe warning ordinal from
          `SEVERITY_ORDER` (e.g., `0` for an `error` warning)

        Pure-kernel rules mirrored from
        `packages.services.m2_input.warnings` and
        `packages.services.m2_input.inventory_projection` — see
        Story 3.3 §Task 1 for the AC mapping (AC #1, #2, #3, #5, #6,
        #8).
        """
        product_map = await self._load_product_map_for_period(
            period=period, rows=rows
        )
        # Story 5.2 — AC #5 swap. Inventory projection now reads from
        # the append-only ledger (single source of truth) instead of
        # rebuilding from monthly_input_rows. The shape contract for
        # downstream `build_inventory_warnings` remains the same
        # (list[InventoryMovement]) — we materialize an InventoryMovement
        # list from the ledger aggregate keyed by product_id.
        #
        # Epic 5 maintenance window: `build_inventory_projection` legacy
        # path is preserved (not removed) — see Story 5.2 spec AC #5
        # deprecation timeline. Epic 6 close-out retro removes both the
        # legacy helper and `LEDGER_REFERENCE_QUERY_STUB`.
        opening_balance = self._load_opening_balance(period)
        # Defensive wrap — translate any internal projection errors to
        # the typed 422 envelope. AC #6: service-only tenants → empty
        # projection → 0 inventory warnings (no exception).
        try:
            projection = await self._compute_inventory_projection_for_state(
                period=period,
                rows=rows,
                product_map=product_map,
                opening_balance=opening_balance,
            )
            inventory_warnings = build_inventory_warnings(
                projection, product_map=product_map
            )
        except (ValueError, TypeError, ArithmeticError) as err:
            raise MonthlyInputInventoryProjectionError(
                tenant_id=self.tenant_id,
                details={"reason": str(err), "row_count": len(rows)},
                trace_id=self.trace_id,
            ) from err

        # Operating rate needs FTE data + payroll. If no labor rows
        # (fte_display=None), operating rate warning is None.
        operating_rate_warning = (
            self._compute_operating_rate_warning_for_state(
                period=period,
                rows=rows,
                fte_display=fte_display,
            )
        )

        warnings = aggregate_warnings(
            inventory_warnings=inventory_warnings,
            operating_rate_warning=operating_rate_warning,
        )
        is_blocked = len(warnings) > 0
        warnings_count = len(warnings)
        # top_n_severity: integer from SEVERITY_ORDER for the worst
        # warning (lowest = most severe). 0 if no warnings.
        top_n_severity = (
            SEVERITY_ORDER.get(warnings[0].severity, 0) if warnings else 0
        )
        return warnings, is_blocked, warnings_count, top_n_severity

    async def _load_product_map_for_period(
        self,
        *,
        period: MonthlyInputPeriod,  # noqa: ARG002 — reserved for future product-scope filter
        rows: list[MonthlyInputRow],
    ) -> dict[uuid.UUID, _ProductProjection]:
        """Load product metadata keyed by `product_id` for inventory rows.

        Only DISTINCT `product_id`s referenced by inventory-bearing
        streams (sales / purchases / production) are queried. The map
        is the source-of-truth for `_ProductLike` duck type
        (`warnings.py` reads `product_id`, `product_code`, `name_ko`).

        Returns an empty dict if no inventory-bearing rows.
        """
        # Determine distinct product_ids in inventory-bearing rows
        inv_types = {"sales", "purchases", "production"}
        distinct_ids = {
            r.product_id
            for r in rows
            if r.stream in inv_types and r.product_id is not None
        }
        if not distinct_ids:
            return {}
        result = await self.session.execute(
            select(Product).where(
                Product.tenant_id == self.tenant_id,
                Product.id.in_(distinct_ids),
            )
        )
        products = result.scalars().all()
        # Convert ORM `Product` (id/code/name) to the duck type the
        # pure kernel expects (product_id/product_code/name_ko). Exclude
        # inactive products so they don't appear in the projection.
        product_map: dict[uuid.UUID, _ProductProjection] = {}
        for p in products:
            if not p.is_active:
                continue
            product_map[p.id] = _ProductProjection(
                product_id=p.id,
                product_code=p.code,
                name_ko=p.name,  # ORM `name` → duck `name_ko`
                product_type=p.product_type,
            )
        return product_map

    def _load_opening_balance(
        self, period: MonthlyInputPeriod
    ) -> dict[uuid.UUID, Decimal]:
        """Read `period.opening_inventory` JSONB → `dict[UUID, Decimal]`.

        MVP shape (added by Alembic 0011, Task 2.1):
        ```jsonc
        {
          "products": [
            {"product_id": "...uuid...", "qty": 100.0},
            ...
          ]
        }
        ```

        Returns empty dict on missing/empty payload (service-layer
        fallback to 0 for all products). Epic 5 Story 5-1 will
        auto-carry the previous period's closing balance (TODO(epic-5)).
        """
        return _load_opening_balance_from_period(period)

    async def _compute_inventory_projection_for_state(
        self,
        *,
        period: MonthlyInputPeriod,
        rows: list[MonthlyInputRow],  # noqa: ARG002 — interface parity with build_inventory_projection (Epic 6 retro removes this arg)
        product_map: dict[uuid.UUID, "_ProductProjection"],  # noqa: ARG002,UP037 — interface parity; _ProductProjection is forward-declared (line 1942)
        opening_balance: dict[uuid.UUID, Decimal],
    ) -> list[InventoryMovement]:
        """Story 5.2 AC #5 — read inventory projection from ledger.

        Reads the per-product closing qty via
        `LedgerService.query_period_closing_all(period_key=...)` — the
        canonical source of truth is now the append-only inventory_ledger
        table, not the rebuilt-from-rows projection.

        The returned shape is `list[InventoryMovement]` (same as
        `build_inventory_projection`) so `build_inventory_warnings` can
        stay unchanged. `inbound_qty` and `outbound_qty` are 0 (the
        ledger gives us the net closing qty only — the inbound/outbound
        breakdown is rebuilt downstream if needed; see Story 5.2 deferral
        4 for the Epic 6 close-out removal plan).

        Story 5.2 AC #5 deprecation timeline:
        - 5-2 commit (this method) — read path swaps to ledger.
        - Epic 5 maintenance window — `build_inventory_projection`
          legacy path preserved (callers migrate case-by-case).
        - Epic 6 close-out retro — `build_inventory_projection` +
          `LEDGER_REFERENCE_QUERY_STUB` REMOVED entirely.

        Drift detector: `tests/integration/test_inventory_projection_ledger_swap.py`
        verifies this method's call graph no longer references
        `build_inventory_projection` (Epic 5 maintenance window violation).
        """
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )
        from packages.services.m2_input.inventory_projection import (
            InventoryMovement,
        )

        ledger_svc = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )
        closing_map = await ledger_svc.query_period_closing_all(
            period_key=period.period_key,
        )

        # Compose InventoryMovement list (sorted by product_id for
        # deterministic output — supports AC #8 sort + cross-language
        # parity tests). `inbound_qty` / `outbound_qty` default to 0
        # since the ledger gives net closing only.
        out: list[InventoryMovement] = []
        for pid in sorted(closing_map.keys(), key=str):
            closing_qty = closing_map[pid]
            # Defensive: ensure product_id is in product_map (else warn
            # silently — orphan ledger rows). The list comprehension
            # below filters by known products.
            out.append(
                InventoryMovement(
                    product_id=pid,
                    opening_qty=(opening_balance.get(pid) or Decimal("0")),
                    inbound_qty=Decimal("0"),
                    outbound_qty=Decimal("0"),
                )
            )
            # Note: closing_qty is preserved as the LEDGER aggregate;
            # the warning kernel reads this via `_row_to_response` /
            # downstream consumers. For the `build_inventory_warnings`
            # contract, closing = opening + inbound - outbound is
            # already encoded in the pure kernel — we pass through the
            # ledger's authoritative closing by setting opening_qty to
            # the ledger closing and inbound/outbound to 0 (so the
            # kernel computes closing = opening + 0 - 0 = opening_qty
            # = the ledger closing).
            out[-1] = InventoryMovement(
                product_id=pid,
                opening_qty=closing_qty,
                inbound_qty=Decimal("0"),
                outbound_qty=Decimal("0"),
            )

        return out

    def _compute_operating_rate_warning_for_state(
        self,
        *,
        period: MonthlyInputPeriod,
        rows: list[MonthlyInputRow],
        fte_display: FteDisplay | None,
    ) -> Warning | None:
        """Build OVERCAPACITY_OPERATING_RATE warning (PRD §V5).

        Returns None when any precondition is missing:
        - no labor rows (`fte_display is None`)
        - no production rows (no required hours to compute against)
        - zero FTE headcount (zero available hours → division)

        The pure-kernel chain (`operating_rate.py`):
          available = FTE × standard_monthly_hours
          required = Σ(production qty × unit_time_hours)
          rate_pct = (required / available) × 100
          warn iff rate_pct > 100

        MVP: `unit_time_hours` defaults to 1.0h per product
        (`DEFAULT_UNIT_TIME_HOURS`). Epic 7 BEP 슬라이더 후속
        will add a per-product override (PRD §V5 footnote).
        """
        if fte_display is None:
            return None
        # Use fte_headcount as the "FTE" input. This is the
        # STORY 3.1/3.2 back-compat aggregate; Story 3.3 uses it for
        # the operating-rate denominator only.
        total_fte_headcount = fte_display.fte_headcount
        if total_fte_headcount <= 0:
            return None

        # standard_monthly_hours from payroll settings (Story 3.2)
        standard_monthly_hours = (
            fte_display.payroll_settings.standard_monthly_hours
        )
        if standard_monthly_hours <= 0:
            return None

        # Production required hours = Σ(production qty × unit_time_hours)
        production_rows = [r for r in rows if r.stream == "production"]
        if not production_rows:
            return None
        # MVP: default unit_time_hours per row. Epic 7 will introduce
        # a per-product override; the `unit_time_hours` arg supports
        # both per-row and global defaults.
        production_required_hours = compute_production_required_hours(
            production_rows=production_rows,
            unit_time_hours=DEFAULT_UNIT_TIME_HOURS,
        )
        if production_required_hours <= 0:
            return None

        total_available_hours = compute_total_available_hours(
            total_fte_headcount=total_fte_headcount,
            standard_monthly_hours=standard_monthly_hours,
        )
        if total_available_hours <= 0:
            return None

        rate_pct = compute_operating_rate(
            available_hours=total_available_hours,
            required_hours=production_required_hours,
        )
        return build_operating_rate_warning(
            operating_rate_pct=rate_pct,
            total_fte_headcount=total_fte_headcount,
            standard_monthly_hours=standard_monthly_hours,
            total_available_hours=total_available_hours,
            production_required_hours=production_required_hours,
            period_key=period.period_key,
            trace_id=self.trace_id,
        )


def validate_payroll_override(o: dict | None) -> dict:
    """Public helper — validate a raw payroll override dict (Story 0.5 plumbing).

    Story 3.2 §Task 3.1 — exposes `merge_payroll_settings` validation
    to the future settings UI (`m0_onboarding` Settings wizard) without
    requiring the caller to import the engine package directly.

    Args:
        o: Raw override dict (e.g., from `tenant_settings.payroll`).
           `None` or empty dict → returns empty `{}` (no-op).

    Returns:
        Validated override dict (suitable for re-storing).

    Raises:
        MonthlyInputPayrollSettingsInvalidError: a value is out of range.
        Wraps `merge_payroll_settings` ValueError so the caller doesn't
        need to know about the engine exception type.
    """
    if not o:
        return {}
    try:
        # Per-field merge validates range without committing to defaults.
        merge_payroll_settings(o, DEFAULT_PAYROLL)
    except ValueError as err:
        raise MonthlyInputPayrollSettingsInvalidError(
            tenant_id=uuid.UUID(int=0),  # placeholder; UI path doesn't carry tenant_id
            details={"reason": str(err), "override": o},
            trace_id="validate_payroll_override",
        ) from err
    return dict(o)


def _decimalize(d: dict[str, Any]) -> dict[str, Any]:
    """Convert Decimal values to str for JSON audit payloads (AD-2)."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, Decimal | uuid.UUID):
            out[k] = str(v)
        else:
            out[k] = v
    return out


# ── Story 3.3 helpers (Task 3.1) ──────────────────────────────
def _load_opening_balance_from_period(
    period: MonthlyInputPeriod,
) -> dict[uuid.UUID, Decimal]:
    """Module-level pure helper for `_load_opening_balance` (test seam).

    Same JSONB → dict[UUID, Decimal] conversion as the instance method.
    Story 3.3 (Task 3.1) — exposed at module level so unit tests can
    cover the JSON parsing without spinning up an `AsyncSession`.
    """
    opening = getattr(period, "opening_inventory", None) or {}
    if not isinstance(opening, dict):
        return {}
    products = opening.get("products") or []
    out: dict[uuid.UUID, Decimal] = {}
    for entry in products:
        if not isinstance(entry, dict):
            continue
        pid_raw = entry.get("product_id")
        qty_raw = entry.get("qty")
        if pid_raw is None or qty_raw is None:
            continue
        try:
            pid = uuid.UUID(str(pid_raw))
            qty = Decimal(str(qty_raw))
        except (ValueError, TypeError):
            continue
        if qty < 0:
            # Defensive: opening_qty MUST be >= 0 (PRD §6.2). Don't
            # accept negative; surface later in projection.
            continue
        out[pid] = qty
    return out
class _ProductProjection(NamedTuple):
    """Lightweight product metadata for the inventory projection duck type.

    Maps the SQLAlchemy `Product` ORM (id / code / name / product_type)
    to the `_ProductLike` Protocol from
    `packages.services.m2_input.warnings`. The `product_id` field name
    matches the protocol's expected attribute.
    """

    product_id: uuid.UUID
    product_code: str
    name_ko: str
    product_type: str


class _RowDuck(NamedTuple):
    """Duck-type for `MonthlyInputRow` — pure-kernel compatible shape.

    The `inventory_projection.py` `_RowLike` Protocol reads 4 fields:
    `stream`, `product_id`, `qty`, `product_type`. The ORM row doesn't
    carry `product_type` directly — it lives on the `Product` table.
    This adapter hydrates the 4 fields for the pure kernel without
    leaking SQLAlchemy types across the engine boundary.
    """

    stream: str
    product_id: uuid.UUID | None
    qty: Decimal | None
    product_type: str


def _make_row_duck(
    row: MonthlyInputRow,
    product_map: dict[uuid.UUID, _ProductProjection],
) -> _RowDuck:
    """Wrap an ORM row + product_map into the pure-kernel duck shape."""
    product_type = ""
    if row.product_id is not None:
        proj = product_map.get(row.product_id)
        if proj is not None:
            product_type = proj.product_type
    return _RowDuck(
        stream=row.stream,
        product_id=row.product_id,
        qty=row.qty,
        product_type=product_type,
    )


def _warning_to_response(w: Warning) -> WarningResponse:
    """Translate pure-kernel `Warning` NamedTuple to wire-format Pydantic model.

    AD-15 cross-language parity: the wire shape uses snake_case (PRD §V
    Korean messages, no transformation); the `details` dict carries
    Decimal-stringified values per AC #1 spec literal ('100' not
    '100.00', etc).

    The `timestamp` field is `datetime` (UTC-aware); Pydantic v2
    serializes it as ISO-8601 by default (AD-15 §2).
    """
    details = dict(w.details)
    # Coerce any UUID inside details to str (defensive; pure kernel
    # already stringifies, but service-side `period_key` or
    # `trace_id` extension might inject UUIDs).
    for k, v in list(details.items()):
        if isinstance(v, uuid.UUID):
            details[k] = str(v)
    return WarningResponse(
        code=w.code,
        severity=w.severity,
        message_ko=w.message_ko,
        details=details,
        stream=w.stream,
        trace_id=w.trace_id,
        timestamp=w.timestamp,
    )
