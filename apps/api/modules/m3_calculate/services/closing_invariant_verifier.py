"""apps.api.modules.m3_calculate.services.closing_invariant_verifier — Story 5.3 T5.

V3 verification slot fill — closing ≥ 0 invariant.

Service-layer wrapper around `ClosingGuardService.validate_closing_invariant_against_active_products`
for the calc orchestrator's V3 pre-load path. Lives in M3_calculate
(M6 was folded into Epic 4 per the architecture file-churn decision).

Layering (AD-11):
- Pure kernel #1: `packages/services/m4_inventory/closing_guard.py` (T1)
- Pure kernel #2: `packages/cost_engine/closing_invariant_check.py` (T2)
- Service layer #1: `apps/api/modules/m4_inventory/services/closing_guard_service.py` (T4)
- Service layer #2: this file — V3 slot pre-load bridge.

Why a separate verifier class instead of inlining into ClosingGuardService:
- ClosingGuardService owns guard evaluation (read-only invariant) + close-time
  gate (additive over 4-2 is_blocked) + production reconciliation. Adding
  pre-load verification for the calc orchestrator would mix responsibilities.
- ClosingInvariantVerifier is the bridge between M3_calculate orchestrator
  and M4_inventory ClosingGuardService for V3 verdict pre-load + audit-first.

A5 forward-lock:
- Audit rows route to `verification_log` (ActionClass.VERIFICATION) via
  `emit_audit_typed()`. The pre-load verdict itself does NOT emit (CR 1.1
  — idempotent no-op skip on identical payload). ClosingGuardService
  already emits `v3_closing_invariant_verified` (audit_logs) when called
  by the verifier.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.modules.m4_inventory.services.closing_guard_service import (
    ClosingGuardService,
)
from packages.services.m0_onboarding.industry_menu import Industry


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


class ClosingInvariantVerifier:
    """Story 5.3 — V3 closing invariant pre-load bridge for calc orchestrator.

    The orchestrator calls `verify_v3_closing_invariant()` BEFORE
    `VerificationRunner.run_all(...)`. The returned V3Verdict TypedDict
    is injected into `RuleInput.closing_invariant_verdict` so the V3
    rule kernel (which is pure per AD-5) can consume it.

    Usage:
        verifier = ClosingInvariantVerifier(
            session, tenant_id=tenant_id, industry=industry, trace_id=trace_id
        )
        verdict = await verifier.verify_v3_closing_invariant(period_key=period_key)
        # verdict = V3Verdict TypedDict — inject into RuleInput.
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
        self._guard_service = ClosingGuardService(
            session,
            tenant_id=tenant_id,
            industry=industry,
            trace_id=trace_id,
        )

    async def verify_v3_closing_invariant(
        self,
        *,
        period_key: str,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Pre-load V3 verdict for the calc orchestrator's run_all path.

        Delegates to `ClosingGuardService.validate_closing_invariant_against_active_products`
        which:
        1. Reads ledger aggregate via LedgerService (5-2 SSOT)
        2. Reads active product whitelist via RLS-scoped query
        3. Calls pure V3 kernel `verify_closing_invariant`
        4. Emits audit-first `v3_closing_invariant_verified` (action_class=CLOSING_GUARD)
        5. Returns V3Verdict TypedDict (passed/failed/skipped)

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            actor_id: actor who triggered; None for system cron.

        Returns:
            V3Verdict TypedDict (cost_engine shape):
            - status: 'passed' | 'failed' | 'skipped'
            - code: 'V3'
            - failures: list[V3Failure] (empty when passed/skipped)
            - verified_at: ISO8601 UTC string
            - product_whitelist_size: int
            - skip_reason_ko: str | None

        Raises:
            ClosingGuardInvalidPeriodKeyError: malformed period_key.
            ClosingGuardServiceOnlyTenantError: service-only tenant (auto-skips).
        """
        return await self._guard_service.validate_closing_invariant_against_active_products(
            period_key=period_key,
            actor_id=actor_id,
        )


__all__ = ["ClosingInvariantVerifier"]
