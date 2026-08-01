"""apps.api.modules.m2_input.services.monthly_input_service — Story 3.1 backend.

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
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.db_models import (
    MonthlyInputPeriod,
    MonthlyInputRow,
    Product,
)
from apps.api.modules.m2_input.schemas import (
    FteDisplay,
    MonthlyInputRowCreate,
    MonthlyInputRowResponse,
    MonthlyInputRowUpdate,
    MonthlyInputStateResponse,
)
from packages.common.uuid7 import uuid7 as _uuid7
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m2_input.stream_completion import (
    compute_fte_wage_krw,
    compute_stream_completion,
    format_fte_headcount,
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
        """
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
        2. Resolve period (auto-create if missing)
        3. Capability gate: production stream → industry check
        4. SELECT FOR UPDATE existing row by natural key
        5. Idempotent no-op: if existing row identical → 200 + no audit
        6. emit_audit with before/after snapshot (CR 1.1 lesson)
        7. INSERT or UPDATE the row
        8. Recompute completion + missing list
        """
        self._validate_stream_shape(payload)

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
            await emit_audit(
                self.session,
                actor_id=actor_id,
                action="monthly_input_row_updated",
                target_table="monthly_input_rows",
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

        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="monthly_input_row_created",
            target_table="monthly_input_rows",
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
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="monthly_input_row_updated",
            target_table="monthly_input_rows",
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

        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="monthly_input_row_deleted",
            target_table="monthly_input_rows",
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
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="monthly_input_mode_changed",
            target_table="monthly_input_periods",
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
        """Return the page-mount payload (rows + completion + fte_display).

        The capability_mask is derived from the tenant's industry (no
        per-row visibility logic).
        """
        period = await self.get_or_create_period(period_key)
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
        )

    # ── Helpers ──────────────────────────────────────────────
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
        """Read-only FTE display for the [인원] tab (Story 3.2 hook surface).

        Returns None if no labor rows exist (no display until user enters
        at least one row). Sums all labor rows for the period (PRD §8.M2
        keeps MVP simple — single aggregated value).
        """
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
        total_workers = sum(int(r.workers or 0) for r in labor_rows)
        total_days = sum(int(r.days_per_worker or 0) for r in labor_rows)
        total_daily = sum(int(r.daily_wage_krw or 0) for r in labor_rows)
        fte_headcount = format_fte_headcount(
            total_workers, total_days, DEFAULT_WORKDAYS_IN_MONTH
        )
        fte_wage = compute_fte_wage_krw(
            fte_headcount, DEFAULT_MONTHLY_SALARY_BASIS_KRW
        )
        return FteDisplay(
            total_workers=total_workers,
            total_days_per_worker=total_days,
            total_daily_wage_krw=total_daily,
            fte_headcount=fte_headcount,
            fte_wage_krw=fte_wage,
            monthly_salary_basis_krw=DEFAULT_MONTHLY_SALARY_BASIS_KRW,
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
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


def _decimalize(d: dict[str, Any]) -> dict[str, Any]:
    """Convert Decimal values to str for JSON audit payloads (AD-2)."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, Decimal):
            out[k] = str(v)
        elif isinstance(v, uuid.UUID):
            out[k] = str(v)
        else:
            out[k] = v
    return out