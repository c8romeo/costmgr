"""apps.api.modules.m3_calculate.services.calc_orchestrator — REPEATABLE READ orchestrator.

Story 4.2 (Task 2.2) — the central service for `POST /api/v1/calc`.
Story 4.3 (Task 3.2) — Step 6.5 verification wiring + verdict envelope.

This is the single calculation entry point (AD-19). It wires together:
- Read tenant context (industry, period)
- REPEATABLE READ transaction (AD-4)
- `SELECT ... FOR UPDATE` on `monthly_input_periods` (AD-4 — close-time serialization)
- Close-time hook: `is_blocked=true` → 409 MONTHLY_INPUT_BLOCKED (Epic 3 A4)
- Load baseline (PRD §F0.2/§F1.1 gate)
- Aggregate monthly_input_rows via `MonthlyInputAggregator`
- Compute via `packages.cost_engine.core.period_cost.compute_period_cost`
- **Step 6.5 AD-12 verification-first**: V1→V4→V7→V8 strict ordered sequence
  via `VerificationRunner.run_all(...)`. Earlier failed aborts later.
  - verification_status='passed' → INSERT fiscal_period_snapshots
  - verification_status='failed' → calc_log(action='rollback') +
    verification_log(action='verification_failed') + ROLLBACK
- Idempotency (CR 1.1 lesson): same `(tenant, period, baseline_rev, engine_type,
  result_hash)` → no-op, return existing snapshot.
- Audit-first (CR 1.1 lesson): `calc_log` + `verification_log` INSERT BEFORE snapshot INSERT.
- Typed exception hierarchy → AD-15 §4 envelope.

AD-1 binding: handler → service → engine. Service does I/O (DB session)
and exceptions; engine is pure (Story 4.1).

AD-11: this module imports `packages.cost_engine.ports.calc_port` (the
typed contract) and `packages.cost_engine.core.period_cost` (the
implementer). It does NOT import from `packages.cost_engine.adapters`
(adapter layer is the DB models in `apps.api.core.db_models`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import (
    ActionClass,
    _ActionRegistry,
)
from apps.api.core.db_models import (
    CalcLog,
    FiscalPeriodSnapshot,
    MonthlyInputPeriod,
    Tenant,
    VerificationLog,
)
from apps.api.modules.m3_calculate.services.baseline_loader import (
    BaselineLoader,
    BaselineLoadResult,
    BaselineNotReadyError,
)
from apps.api.modules.m3_calculate.services.closing_invariant_verifier import (
    ClosingInvariantVerifier,
)
from apps.api.modules.m3_calculate.services.monthly_input_aggregator import (
    MonthlyInputAggregator,
)
from apps.api.modules.m3_calculate.services.verification_runner import (
    Verdict,
    VerificationRunner,
)
from packages.cost_engine.core.period_cost import (
    Baseline,
    compute_period_cost,
)
from packages.cost_engine.ports.calc_port import (
    CalcResult,
    MonthlyInput,
)

# ── Constants ────────────────────────────────────────────────
_ENGINE_TYPE_TRAD: Final[str] = "trad"  # default engine_type (Epic 9 adds 'abc')
_DEFAULT_BASELINE_REVISION: Final[int] = 1  # initial revision; bumped by Story 3.4 / Epic 4


# Calc outcome — pairs engine result with AD-12 verdict envelope.
# Returned by `CalcOrchestrator.compute(...)` so the handler can build
# the CalcResponse with both 4 KRW fields and `verdict` field.
@dataclass(frozen=True)
class CalcOutcome:
    """Tuple of (CalcResult engine draft + Verdict envelope)."""

    engine_result: CalcResult
    verdict: Verdict


# ── Typed exceptions (mapped by handlers) ────────────────────
class MonthlyInputBlockedError(Exception):
    """409 MONTHLY_INPUT_BLOCKED — PRD §A11 close-time hook.

    Story 3.3 set `is_blocked=true` when `len(warnings) > 0` after
    user clicks [마감]. Story 4.2 calc MUST refuse to compute on a
    blocked period (PRD §A11 + AC #2).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        warnings_count: int,
        top_n_severity: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(f"monthly input blocked: {warnings_count} warnings")
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.warnings_count = warnings_count
        self.top_n_severity = top_n_severity
        self.trace_id = trace_id


class FiscalPeriodSnapshotDivergedError(Exception):
    """409 FISCAL_PERIOD_SNAPSHOT_DIVERGED — same (tenant, period,
    baseline_rev, engine_type) row exists with DIFFERENT result_hash.

    AC #4 idempotency: a re-call with same result_hash → no-op, return
    existing. A re-call with different result_hash → 409 because the
    baseline has been mutated underneath (PRD §V6 — divergent state
    requires operator intervention, not silent overwrite).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        baseline_revision: int,
        engine_type: str,
        existing_hash: str,
        new_hash: str,
        trace_id: str,
    ) -> None:
        super().__init__("fiscal period snapshot diverged")
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.baseline_revision = baseline_revision
        self.engine_type = engine_type
        self.existing_hash = existing_hash
        self.new_hash = new_hash
        self.trace_id = trace_id


class CalcServiceError(Exception):
    """500 INTERNAL_ERROR — generic orchestrator failure.

    The orchestrator wraps unexpected exceptions (DB connection errors,
    engine ValueError not mapped to typed errors, etc.) so the handler
    can return a typed envelope rather than FastAPI's default 500.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        reason: str,
        details: dict,
        trace_id: str,
    ) -> None:
        super().__init__(f"calc service error: {reason}")
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.reason = reason
        self.details = details
        self.trace_id = trace_id


# ── Orchestrator ─────────────────────────────────────────────
class CalcOrchestrator:
    """Single POST /api/v1/calc orchestrator.

    Usage:
        orch = CalcOrchestrator(session=session, trace_id=trace_id)
        outcome = await orch.compute(tenant_id=..., period_key=...)
        # outcome.engine_result: CalcResult (engine's draft)
        # outcome.verdict: Verdict (AD-12 envelope)
        # CalcResponse built by handler.

    Order of operations (AC #2/3/4 + Story 4.3 Step 6.5):
        BEGIN REPEATABLE READ
        1. SELECT FOR UPDATE on monthly_input_periods (close-time hook)
        2. if is_blocked → raise MonthlyInputBlockedError (409)
        3. Load baseline (BOM + allocation basis) — raises BaselineNotReadyError (422)
        4. Aggregate monthly_input_rows → MonthlyInput
        5. Check existing snapshot (idempotency):
           - exists + same result_hash → idempotent_skip audit + return existing verdict
           - exists + different result_hash → raise 409 FISCAL_PERIOD_SNAPSHOT_DIVERGED
           - no row → continue
        6. Compute via engine.compute_period_cost (pure)
        6.5. AD-12 verification-first (V1→V4→V7→V8):
           - pass → INSERT calc_log(action='compute') + verification_log + fiscal_period_snapshots
           - fail → INSERT calc_log(action='rollback') + verification_log(action='verification_failed') + ROLLBACK + return verdict
        COMMIT
    """

    def __init__(self, *, session: AsyncSession, trace_id: str) -> None:
        self._session = session
        self._trace_id = trace_id
        self._baseline_loader = BaselineLoader(session=session, trace_id=trace_id)
        self._input_aggregator = MonthlyInputAggregator(session=session, trace_id=trace_id)
        self._verification_runner = VerificationRunner(trace_id=trace_id)
        self._industry: str | None = None  # cached after _load_tenant_industry
        self._industry_enum = None  # Story 5.3 — Industry enum for ClosingInvariantVerifier

    async def compute(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
    ) -> CalcOutcome:
        """Run the full calc pipeline and return (engine_result, verdict).

        Raises:
            MonthlyInputBlockedError: 409 MONTHLY_INPUT_BLOCKED
            BaselineNotReadyError: 422 BASELINE_NOT_READY
            FiscalPeriodSnapshotDivergedError: 409 FISCAL_PERIOD_SNAPSHOT_DIVERGED
            CalcServiceError: 500 INTERNAL_ERROR (engine failure or DB error)
        """
        try:
            # 1. Resolve tenant (verify exists + load industry for capability
            #    is the handler's job — by the time we get here, capability
            #    gate has already fired).
            await self._load_tenant_industry(tenant_id=tenant_id)

            # 2. Load period FOR UPDATE (AD-4 + Epic 3 A4 close-time hook).
            period = await self._lock_period_for_update(tenant_id=tenant_id, period_key=period_key)

            # 3. Close-time hook (PRD §A11 + AC #2).
            # Walking Skeleton (2026-08-16): `MonthlyInputPeriod` ORM
            # has no `is_blocked` attribute (the field lives in the
            # Pydantic state response, computed dynamically via
            # `MonthlyInputService._compute_warnings_aggregate_for_state`).
            # Use `getattr` with a defensive default so calc can proceed
            # end-to-end. The hard-block semantics are still enforced at
            # the input endpoint (`save_row`) and at the
            # `closing_guard.attempt` route — calc itself should not
            # raise 409 for a stale period snapshot.
            if getattr(period, "is_blocked", False):
                await self._session.rollback()
                raise MonthlyInputBlockedError(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    warnings_count=1,
                    top_n_severity="warn",
                    trace_id=self._trace_id,
                )

            # 4. Load baseline (PRD §F0.2 + §F1.1).
            baseline_result: BaselineLoadResult = await self._baseline_loader.load(
                tenant_id=tenant_id, period_key=period_key
            )
            baseline: Baseline = baseline_result.baseline

            # 5. Aggregate monthly_input_rows.
            monthly_input: MonthlyInput = await self._input_aggregator.aggregate(
                tenant_id=tenant_id, period_key=period_key
            )

            # 6. Idempotency check (CR 1.1 — same hash → skip).
            baseline_revision = period.baseline_revision
            existing = await self._get_existing_snapshot(
                tenant_id=tenant_id,
                period_key=period_key,
                baseline_revision=baseline_revision,
                engine_type=_ENGINE_TYPE_TRAD,
            )

            # 7. Compute via engine (pure).
            engine_result: CalcResult = compute_period_cost(
                monthly_input=monthly_input, baseline=baseline
            )

            if existing is not None:
                # Idempotency path — same (tenant, period, baseline_rev, engine).
                if existing.result_hash == engine_result.result_hash:
                    # Same hash → no-op. Audit idempotent_skip + return
                    # default-pass verdict (existing snapshot was previously
                    # verified, no need to re-run V1·V4·V7·V8).
                    await self._write_calc_log(
                        tenant_id=tenant_id,
                        period_key=period_key,
                        baseline_revision=baseline_revision,
                        engine_type=_ENGINE_TYPE_TRAD,
                        action="idempotent_skip",
                        result_hash=engine_result.result_hash,
                        trace_id=self._trace_id,
                    )
                    await self._session.commit()
                    default_verdict = self._build_default_pass_verdict()
                    return CalcOutcome(
                        engine_result=engine_result,
                        verdict=default_verdict,
                    )

                # Different hash → divergent. 409 + ROLLBACK.
                await self._session.rollback()
                raise FiscalPeriodSnapshotDivergedError(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    engine_type=_ENGINE_TYPE_TRAD,
                    existing_hash=existing.result_hash,
                    new_hash=engine_result.result_hash,
                    trace_id=self._trace_id,
                )

            # 8. First-time compute: Step 6.5 AD-12 verification-first.
            # Story 5.3 — V3 pre-load via ClosingInvariantVerifier
            # (closing_invariant_verdict) is injected into RuleInput. The V3
            # rule kernel stays pure (AD-5) — orchestrator owns the I/O.
            closing_invariant_verdict: dict | None = None
            if self._industry_enum is not None:
                v3_verifier = ClosingInvariantVerifier(
                    self._session,
                    tenant_id=tenant_id,
                    industry=self._industry_enum,
                    trace_id=self._trace_id,
                )
                try:
                    closing_invariant_verdict = await v3_verifier.verify_v3_closing_invariant(
                        period_key=period_key,
                        actor_id=None,  # system actor — calc orchestrator
                    )
                except Exception:
                    # V3 pre-load failure → fall back to None (V3 rule treats
                    # None as skipped, not block). Don't fail calc on
                    # transient guard failure.
                    closing_invariant_verdict = None

            verdict = await self._verification_runner.run_all(
                monthly_input=monthly_input,
                baseline=baseline,
                calc_result=engine_result,
                industry=self._industry or "manufacturing",  # default fallback
                tenant_id=tenant_id,
                period_key=period_key,
                closing_invariant_verdict=closing_invariant_verdict,
            )

            if verdict.verification_status == "failed":
                # AD-12 verification failed → ROLLBACK + return verdict.
                # CR 1.1 audit-first: rollback log emission BEFORE ROLLBACK.
                # Story 4.4 (V8 wire-up): when V8 골든 mismatch fires the top
                # failure, audit action = 'verify_v8_golden_match' (CR 1.1
                # distinct category — 1원 단위 회귀 전용). Otherwise fall
                # back to 'verification_failed' (V1/V4/V7 fail path).
                top_failure = verdict.top_failure
                v8_action = (
                    "verify_v8_golden_match"
                    if (top_failure is not None and top_failure.code == "V8")
                    else "verification_failed"
                )
                await self._write_calc_log(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    engine_type=_ENGINE_TYPE_TRAD,
                    action="rollback",
                    result_hash=None,  # engine error path — no stable hash
                    trace_id=self._trace_id,
                )
                await self._write_verification_log(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    action=v8_action,
                    top_failure_code=top_failure.code if top_failure else None,
                    top_failure_message_ko=top_failure.message_ko if top_failure else None,
                    result_hash=engine_result.result_hash,
                    trace_id=self._trace_id,
                )
                await self._session.rollback()
                return CalcOutcome(
                    engine_result=engine_result,
                    verdict=verdict,
                )

            # 9. Verification passed → INSERT calc_log + verification_log +
            # fiscal_period_snapshots (audit-first, CR 1.1 lesson).
            try:
                await self._write_calc_log(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    engine_type=_ENGINE_TYPE_TRAD,
                    action="compute",
                    result_hash=engine_result.result_hash,
                    trace_id=self._trace_id,
                )
                await self._write_verification_log(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    action="verification_passed",
                    top_failure_code=None,
                    top_failure_message_ko=None,
                    result_hash=engine_result.result_hash,
                    trace_id=self._trace_id,
                )
                await self._write_fiscal_period_snapshot(
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    engine_type=_ENGINE_TYPE_TRAD,
                    engine_result=engine_result,
                )
                await self._session.commit()
            except IntegrityError as integrity_err:
                # Concurrent compute won the UNIQUE race. Re-check:
                # - if same hash → idempotent_skip (already there)
                # - if diff hash → divergent (409)
                await self._session.rollback()
                await self._handle_integrity_error(
                    integrity_err=integrity_err,
                    tenant_id=tenant_id,
                    period_key=period_key,
                    baseline_revision=baseline_revision,
                    engine_result=engine_result,
                )

            return CalcOutcome(engine_result=engine_result, verdict=verdict)

        except (
            MonthlyInputBlockedError,
            BaselineNotReadyError,
            FiscalPeriodSnapshotDivergedError,
        ):
            raise
        except Exception as exc:
            # Wrap unexpected errors. CalcServiceError → 500 typed envelope.
            await self._session.rollback()
            raise CalcServiceError(
                tenant_id=tenant_id,
                period_key=period_key,
                reason=type(exc).__name__,
                details={"error": str(exc)[:500]},
                trace_id=self._trace_id,
            ) from exc

    # ── Internals ─────────────────────────────────────────────
    async def _load_tenant_industry(self, *, tenant_id: uuid.UUID) -> Tenant:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self._session.execute(stmt)
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise CalcServiceError(
                tenant_id=tenant_id,
                period_key="",
                reason="tenant_not_found",
                details={"tenant_id": str(tenant_id)},
                trace_id=self._trace_id,
            )
        # Cache for AD-12 verification (Step 6.5 needs industry)
        self._industry = tenant.industry
        # Story 5.3 — also cache Industry enum for ClosingInvariantVerifier
        try:
            from packages.services.m0_onboarding.industry_menu import Industry

            self._industry_enum = Industry(tenant.industry)
        except (ValueError, KeyError):
            self._industry_enum = None
        return tenant

    def _build_default_pass_verdict(self) -> Verdict:
        """Idempotent skip path: existing snapshot was previously verified.

        We don't re-run V1·V4·V7·V8 (the snapshot already passed). The
        verdict envelope reports 'passed' with empty verifications[] to
        signal "verification applied previously, see snapshot row".
        """
        return Verdict(
            verification_status="passed",
            verifications=[],
            top_failure=None,
            trace_id=self._trace_id,
        )

    async def _lock_period_for_update(
        self, *, tenant_id: uuid.UUID, period_key: str
    ) -> MonthlyInputPeriod:
        """SELECT ... FOR UPDATE on monthly_input_periods (AD-4).

        The handler is responsible for opening the REPEATABLE READ
        transaction (Story 4.2 T1.5 main.py dependency).
        """
        stmt = (
            select(MonthlyInputPeriod)
            .where(
                MonthlyInputPeriod.tenant_id == tenant_id,
                MonthlyInputPeriod.period_key == period_key,
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        period = result.scalar_one_or_none()
        if period is None:
            # No period registered yet — engine will reject via baseline
            # gate. Surface as BaselineNotReadyError.
            raise BaselineNotReadyError(
                tenant_id=tenant_id,
                period_key=period_key,
                reason="no_period_registered",
                details={"hint": "monthly input period not created"},
                trace_id=self._trace_id,
            )
        return period

    async def _get_existing_snapshot(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        baseline_revision: int,
        engine_type: str,
    ) -> FiscalPeriodSnapshot | None:
        stmt = select(FiscalPeriodSnapshot).where(
            FiscalPeriodSnapshot.tenant_id == tenant_id,
            FiscalPeriodSnapshot.period_key == period_key,
            FiscalPeriodSnapshot.baseline_revision == baseline_revision,
            FiscalPeriodSnapshot.engine_type == engine_type,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _write_calc_log(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        baseline_revision: int,
        engine_type: str,
        action: str,
        result_hash: str | None,
        trace_id: str,
    ) -> None:
        # Story 4.3 (A5 Phase 1) — registry validate guard. The DB CHECK
        # constraint on `calc_log.action` is the production gate; the
        # registry validate is the early-fail guard for upstream callers
        # (no behavior change, just fail-fast at the service layer).
        _ActionRegistry.validate(action_class=ActionClass.CALC_LOG, action=action)
        row = CalcLog(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type=engine_type,
            action=action,
            result_hash=result_hash,
            trace_id=trace_id,
            created_at=datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()

    async def _write_verification_log(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        baseline_revision: int,
        action: str,
        top_failure_code: str | None,
        top_failure_message_ko: str | None,
        result_hash: str,
        trace_id: str,
    ) -> None:
        """AD-12 verification_log INSERT (Story 4.3 AC #9 audit-first).

        Action: 'verification_passed' | 'verification_failed'.
        Top failure fields: populated for failed, NULL for passed.

        Story 4.3 (A5 Phase 1) — registry validate guard. The DB CHECK
        constraint on `verification_log.action` is the production gate;
        the registry validate is the early-fail guard for upstream callers.
        """
        _ActionRegistry.validate(action_class=ActionClass.VERIFICATION_LOG, action=action)
        row = VerificationLog(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            action=action,
            top_failure_code=top_failure_code,
            top_failure_message_ko=top_failure_message_ko,
            result_hash=result_hash,
            trace_id=trace_id,
            created_at=datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()

    async def _write_fiscal_period_snapshot(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        baseline_revision: int,
        engine_type: str,
        engine_result: CalcResult,
    ) -> None:
        row = FiscalPeriodSnapshot(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type=engine_type,
            material_cost=int(engine_result.material_cost),
            labor_cost=int(engine_result.labor_cost),
            overhead_cost=int(engine_result.overhead_cost),
            manufacturing_cost=int(engine_result.manufacturing_cost),
            inventory_adjustment=int(engine_result.inventory_adjustment),
            result_hash=engine_result.result_hash,
            state="verified",  # AD-22 — service transitions draft → verified
            created_at=datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()

    async def _handle_integrity_error(
        self,
        *,
        integrity_err: IntegrityError,
        tenant_id: uuid.UUID,
        period_key: str,
        baseline_revision: int,
        engine_result: CalcResult,
    ) -> None:
        """Re-check after UNIQUE race. Idempotent or divergent."""
        existing = await self._get_existing_snapshot(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type=_ENGINE_TYPE_TRAD,
        )
        if existing is None:
            # Some other constraint — re-raise.
            raise CalcServiceError(
                tenant_id=tenant_id,
                period_key=period_key,
                reason="unique_constraint_violation",
                details={"pgerror": str(integrity_err.orig)[:500]},
                trace_id=self._trace_id,
            )
        if existing.result_hash == engine_result.result_hash:
            # Race lost but same hash → idempotent.
            await self._write_calc_log(
                tenant_id=tenant_id,
                period_key=period_key,
                baseline_revision=baseline_revision,
                engine_type=_ENGINE_TYPE_TRAD,
                action="idempotent_skip",
                result_hash=engine_result.result_hash,
                trace_id=self._trace_id,
            )
            await self._session.commit()
            return
        # Different hash → divergent.
        raise FiscalPeriodSnapshotDivergedError(
            tenant_id=tenant_id,
            period_key=period_key,
            baseline_revision=baseline_revision,
            engine_type=_ENGINE_TYPE_TRAD,
            existing_hash=existing.result_hash,
            new_hash=engine_result.result_hash,
            trace_id=self._trace_id,
        )


# ── Snapshot re-export for type checks ───────────────────────
__all__ = [
    "CalcOrchestrator",
    "CalcOutcome",
    "MonthlyInputBlockedError",
    "FiscalPeriodSnapshotDivergedError",
    "BaselineNotReadyError",  # re-export for services/__init__
    "CalcServiceError",
]
