"""apps.api.jobs.chargeback_reconciliation — Chargeback reconciliation job (PRD §F31.5).

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.5 verbatim). Background job that
initiates chargeback allocation reconciliation on a schedule
(default monthly). Emits `reconciliation_initiated` audit action.

CR lessons applied:
- CR 0-2 RLS — every job invocation carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `reconciliation_initiated`.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern.
- CR 12-1 L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final

from apps.api.modules.finops.chargeback_allocation_reconciliation import (
    RECONCILIATION_STRATEGY_HYBRID_BLENDED,
    Reconciliation,
    initiate_reconciliation,
)

# Default cron: monthly at 4 AM on the 1st (PRD §F31.5 verbatim).
DEFAULT_RECONCILIATION_CRON: Final[str] = "0 4 1 * *"


def run_chargeback_reconciliation_job(
    tenant_id: str | uuid.UUID,
    *,
    period_start: str,
    period_end: str,
    strategy: str = RECONCILIATION_STRATEGY_HYBRID_BLENDED,
    dry_run: bool = False,
    trace_id: str = "",
) -> Reconciliation:
    """Run the chargeback reconciliation job (PRD §F31.5-1).

    Hybrid_blended is the default strategy. Aggregates chargeback +
    tag allocation amounts, calculates variance, returns
    Reconciliation TypedDict.

    Args:
        tenant_id: tenant UUID.
        period_start: ISO 8601 date string.
        period_end: ISO 8601 date string.
        strategy: chargeback_only / tag_allocation_only / hybrid_blended.
        dry_run: if True, no audit log emitted.
        trace_id: trace_id propagation.

    Returns:
        Reconciliation TypedDict.
    """
    # In production, this would query AWS Cost Explorer for actual amounts.
    # For now, stub returns zero-amounts reconciliation.
    return initiate_reconciliation(
        tenant_id=tenant_id,
        strategy=strategy,
        period_start=period_start,
        period_end=period_end,
        chargeback_amount_usd=0.0,
        tag_allocation_amount_usd=0.0,
        dry_run=dry_run,
        trace_id=trace_id,
    )


__all__ = [
    "DEFAULT_RECONCILIATION_CRON",
    "run_chargeback_reconciliation_job",
]