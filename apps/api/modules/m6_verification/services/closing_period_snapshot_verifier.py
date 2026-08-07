"""apps.api.modules.m6_verification.services.closing_period_snapshot_verifier — Story 6.1.

V4 verification verifier service layer (m6_verification module).

Wraps the V4 pure kernel in `packages.cost_engine.closing_period_snapshot`
with:

- 1 service operation: `verify_v4_closing_period_consistency` dispatched
  by `VerificationRunner` (5-3 wire) at V4 slot index 2 of 5.

- 1 typed exception: `ClosingPeriodSnapshotInconsistencyError` (409
  CLOSING_PERIOD_SNAPSHOT_INCONSISTENCY) — wraps pure-kernel
  inconsistency exception with HTTP envelope.

- SSOT reads via 5-2 `LedgerService`:
  - `query_period_closing_all` for ledger aggregate.
  - `query_period_closing_snapshot_all` for closing_snapshot
    aggregate (NEW 5-2 event_type='closing_snapshot' filter).

AD-12 ordering preserved:
- V1 → V4 → V3 → V7 → V8 (V4 succeeds V1, precedes V3).
- V4 status='skipped' is OK (service-only tenant, empty aggregate);
  VerificationRunner continues to V3 next slot.
- V4 status='failed' → raise ClosingPeriodSnapshotInconsistencyError;
  VerificationRunner marks the run as failed (no further slots run).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from packages.cost_engine.closing_period_snapshot import (
    V4Verdict,
    verify_closing_period_consistency,
)


def _now_utc_iso() -> str:
    """ISO-8601 UTC timestamp (AD-5: pure kernel no clock)."""
    return datetime.now(tz=UTC).isoformat()


class ClosingPeriodSnapshotInconsistencyError(Exception):
    """409 CLOSING_PERIOD_SNAPSHOT_INCONSISTENCY — V4 fail.

    Mirrors `packages.cost_engine.closing_period_snapshot
    .ClosingPeriodSnapshotInconsistencyError`. Service-layer wrap carries
    tenant_id + period_key + failures for HTTP envelope.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        failures: list[dict[str, str]],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_period_snapshot inconsistency for {period_key} "
            f"(tenant {tenant_id}): {len(failures)} failure(s)"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.failures = failures
        self.trace_id = trace_id


class ClosingPeriodSnapshotVerifier:
    """Story 6.1 — V4 verifier service.

    Constructor:
        session: AsyncSession (per-request).
        tenant_id: tenant UUID (from JWT).
        trace_id: request trace ID.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.trace_id = trace_id

    async def verify_v4_closing_period_consistency(
        self,
        period_key: str,
        *,
        industry: str | None = None,
    ) -> V4Verdict:
        """V4 verification — closing snapshot 일관성.

        Reads ledger aggregate + closing_snapshot aggregate via
        `LedgerService` (5-2 SSOT), then dispatches
        `verify_closing_period_consistency` (T2 pure kernel).

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            industry: Industry SSOT (Story 4-3 wire). 'service' → SKIP.

        Returns:
            V4Verdict TypedDict (verified_at overwritten with
            `datetime.now(UTC).isoformat()` — AD-5 clock injection at
            service layer).

        Raises:
            ClosingPeriodSnapshotInconsistencyError: V4 status='failed'.
            PureV4InconsistencyError: defense-in-depth (pure kernel
                invariant violation).
        """
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )

        ledger_service = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            trace_id=self.trace_id,
        )
        ledger_aggregate = await ledger_service.query_period_closing_all(
            period_key=period_key,
        )
        closing_snapshot_aggregate = await ledger_service.query_period_closing_snapshot_all(
            period_key=period_key,
        )

        # Product whitelist = union of ledger aggregate + closing_snapshot
        # aggregate keys (defense-in-depth: pass both active sets).
        product_whitelist: set[uuid.UUID] = set(ledger_aggregate.keys()) | set(
            closing_snapshot_aggregate.keys()
        )

        # Pure kernel dispatch.
        verdict = verify_closing_period_consistency(
            ledger_aggregate=ledger_aggregate,
            closing_snapshot_aggregate=closing_snapshot_aggregate,
            product_whitelist=product_whitelist,
            industry=industry,
        )

        # Overwrite verified_at with real clock (AD-5).
        verdict["verified_at"] = _now_utc_iso()

        if verdict["status"] == "failed":
            failures = list(verdict["failures"])
            raise ClosingPeriodSnapshotInconsistencyError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                failures=failures,
                trace_id=self.trace_id,
            )

        return verdict


__all__ = [
    "ClosingPeriodSnapshotInconsistencyError",
    "ClosingPeriodSnapshotVerifier",
]
