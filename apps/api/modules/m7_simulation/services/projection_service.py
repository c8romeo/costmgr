"""apps.api.modules.m7_simulation.services.projection_service — Story 7.2.

Service-layer orchestration for next-month projection (READ-ONLY, no DB writes).

AD-1 / AD-11 binding: handler → service (here) → packages.cost_engine.projection
(pure kernel, stdlib-only). All DB I/O lives here; pure logic lives in the
kernel.

AD-22 ledger append-only: 7-2 is read-only (projection simulation), no audit
emit (CR 1.1 honest-DEFER — read-only operations skip audit). Verified by
`tests/integration/test_m7_projection_no_db_writes.py` (audit_logs
row 0건 + fiscal_period_snapshots/monthly_input_periods no UPDATE).

CR 12-1 L3 precedent: `_to_projection_inputs(baseline, form_data)` ORM→kernel
boundary conversion (mirrors 12-1 `_to_totp_state` + 7-1 `_to_cvp_baseline`).
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m7_simulation.exceptions import (
    InvalidProjectionMonthError,
    ProjectionBaselineNotFoundError,
    ProjectionInputsInvalidError,
)
from packages.cost_engine.cvp import CVPBaseline
from packages.cost_engine.projection import (
    PROJECTION_MONTH_PATTERN,
    NextMonthProjection,
    ProjectionInputs,
    project_next_month,
)


# Re-use 7-1 CVPSimulationService for baseline extraction (CVP_SIMULATION
# capability reuse — no separate baseline fetch logic).
class ProjectionService:
    """Story 7.2 — Next-Month Projection thin orchestrator.

    Thin orchestration wrapper around `packages.cost_engine.projection`
    pure kernel. Baseline extraction reuses `CVPSimulationService.fetch_cvp_baseline`
    (7-1 — same data source: `fiscal_period_snapshots` + `monthly_input_periods`).

    Pure logic lives in the kernel; service layer owns:
    - chronological invariant validation (projection_month > period_key)
    - AD-24 YYYY-MM format validation
    - ORM→kernel boundary conversion (`_to_projection_inputs`)
    - 4-role allow (AD-10) + CVP_SIMULATION capability gate (route layer)
    - READ-ONLY operation guards (no audit emit per CR 1.1)
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

    async def fetch_projection_baseline(
        self,
        *,
        period_key: str,
        projection_month: str,
    ) -> CVPBaseline:
        """Fetch projection baseline via 7-1 CVPSimulationService reuse.

        Validates:
        - AD-24 period_key format (YYYY-MM)
        - AD-24 projection_month format (YYYY-MM)
        - Chronological invariant (projection_month > period_key)

        Args:
            period_key: AD-24 YYYY-MM (baseline source period)
            projection_month: AD-24 YYYY-MM (projection target month, must be > period_key)

        Returns:
            CVPBaseline extracted from 7-1 service

        Raises:
            InvalidProjectionMonthError: format mismatch or chronological violation
            ProjectionBaselineNotFoundError: no committed snapshot for period_key
        """
        # Validate period_key format.
        if not re.match(PROJECTION_MONTH_PATTERN, period_key):
            raise InvalidProjectionMonthError(
                period_key=period_key,
                projection_month=projection_month,
                reason="period_key must match AD-24 YYYY-MM pattern",
            )

        # Validate projection_month format.
        if not re.match(PROJECTION_MONTH_PATTERN, projection_month):
            raise InvalidProjectionMonthError(
                period_key=period_key,
                projection_month=projection_month,
                reason="projection_month must match AD-24 YYYY-MM pattern",
            )

        # Validate chronological invariant.
        if projection_month <= period_key:
            raise InvalidProjectionMonthError(
                period_key=period_key,
                projection_month=projection_month,
                reason="projection_month must be strictly after period_key",
            )

        # Delegate to 7-1 CVPSimulationService.fetch_cvp_baseline.
        # Lazy import to avoid circular dependency.
        from apps.api.modules.m7_simulation.services.cvp_simulation_service import (
            CVPSimulationService,
        )

        cvp_service = CVPSimulationService(
            self.session,
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            trace_id=self.trace_id,
        )
        try:
            baseline, _source_period_key, _state = await cvp_service.fetch_cvp_baseline(
                period_key=period_key
            )
        except Exception as exc:
            # Wrap CVPBaselineNotFoundError → ProjectionBaselineNotFoundError
            # for the projection sub-endpoint context.
            from apps.api.modules.m7_simulation.exceptions import (
                CVPBaselineNotFoundError,
            )

            if isinstance(exc, CVPBaselineNotFoundError):
                raise ProjectionBaselineNotFoundError(
                    tenant_id=str(self.tenant_id),
                    period_key=period_key,
                ) from exc
            raise

        return baseline

    async def project_next_month(
        self,
        *,
        baseline: CVPBaseline,
        projection_inputs: ProjectionInputs,
    ) -> NextMonthProjection:
        """Run projection via pure kernel delegation.

        No DB writes; no audit emit (CR 1.1 honest-DEFER — read-only
        operation skips audit_logs).

        Args:
            baseline: CVPBaseline (snapshot-extracted)
            projection_inputs: 4종 파라미터 user inputs

        Returns:
            NextMonthProjection result

        Raises:
            ProjectionInvalidInputError: kernel-level validation failure
        """
        return project_next_month(baseline_cvp=baseline, projection_inputs=projection_inputs)

    async def compute(
        self,
        *,
        period_key: str,
        projection_month: str,
        projection_inputs: ProjectionInputs,
    ) -> tuple[CVPBaseline, NextMonthProjection]:
        """End-to-end: fetch baseline + project.

        Returns:
            (CVPBaseline, NextMonthProjection) tuple.

        Raises:
            InvalidProjectionMonthError: format/chronological violation
            ProjectionBaselineNotFoundError: no baseline
            ProjectionInputsInvalidError: 4종 파라미터 validation failure (wraps kernel)
        """
        baseline = await self.fetch_projection_baseline(
            period_key=period_key, projection_month=projection_month
        )
        try:
            projection = await self.project_next_month(
                baseline=baseline, projection_inputs=projection_inputs
            )
        except Exception as exc:
            from packages.cost_engine.projection import (
                ProjectionInvalidInputError,
            )

            if isinstance(exc, ProjectionInvalidInputError):
                # Wrap kernel error → service-layer error envelope.
                raise ProjectionInputsInvalidError(
                    tenant_id=str(self.tenant_id),
                    period_key=period_key,
                    field=getattr(exc, "field", None),
                    reason=str(exc),
                ) from exc
            raise
        return baseline, projection


# ── ORM→kernel boundary conversion ───────────────────────────
def _to_projection_inputs(form_data: dict[str, object]) -> ProjectionInputs:
    """ORM/form data → kernel ProjectionInputs (Decimal casting).

    CR 12-1 L3 boundary conversion pattern (mirrors 12-1 `_to_totp_state`
    + 12-3 `_to_deletion_state` + 7-1 `_to_cvp_baseline`).

    Validates 4종 파라미터 ranges (defense-in-depth layer 2 — pure kernel
    is layer 3; route layer Pydantic is layer 1).

    Args:
        form_data: dict with 4 keys — loan_amount, interest_rate,
            cost_inflation_rate, corporate_tax_rate

    Returns:
        ProjectionInputs frozen dataclass

    Raises:
        ProjectionInputsInvalidError: validation failure
    """
    try:
        return ProjectionInputs(
            loan_amount=Decimal(str(form_data["loan_amount"])),
            interest_rate=Decimal(str(form_data["interest_rate"])),
            cost_inflation_rate=Decimal(str(form_data["cost_inflation_rate"])),
            corporate_tax_rate=Decimal(str(form_data["corporate_tax_rate"])),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ProjectionInputsInvalidError(
            tenant_id="<boundary>",
            period_key="<boundary>",
            reason=str(exc),
        ) from exc
    except Exception as exc:
        # Catch-all for `decimal.InvalidOperation` (subclass of ArithmeticError,
        # not caught above) + any kernel-level validation that raises a generic
        # exception during boundary conversion.
        raise ProjectionInputsInvalidError(
            tenant_id="<boundary>",
            period_key="<boundary>",
            reason=str(exc),
        ) from exc


__all__ = [
    "ProjectionService",
    "_to_projection_inputs",
]
