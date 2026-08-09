"""apps.api.modules.m11_close.exceptions — Story 11.3 typed exception classes.

4 NEW exception types for AD-20 snapshot persistence + AD-22 reversal
execute + W2 reopen flow. Each exception carries the minimum context
required for the corresponding handler in `apps/api/main.py` to
produce a deterministic AD-15 §4 envelope.

Error code contract:
  - SnapshotAlreadyCommittedError          → 409 SNAPSHOT_ALREADY_COMMITTED
  - ReversalSnapshotMismatchError           → 422 REVERSAL_SNAPSHOT_MISMATCH
  - ReopenOperatorActionInvalidError        → 422 REOPEN_OPERATOR_ACTION_INVALID
  - ReopenAuditEmitFailedError              → 500 REOPEN_AUDIT_EMIT_FAILED

Korean SSOT (AD-15 §11) is supplied by the handler, not the exception
itself — keeps the exception module free of presentation strings.
"""

from __future__ import annotations

import uuid


# ── 1. SnapshotAlreadyCommittedError ─────────────────────────
class SnapshotAlreadyCommittedError(Exception):
    """409 SNAPSHOT_ALREADY_COMMITTED — fiscal_period_snapshots.state != 'verified'.

    AD-20 state machine: draft → verified → committed → reversed.
    `commit_snapshot_persistence` only fires on `state='verified'`;
    a re-commit attempt (state='committed' or 'reversed') raises this
    error so callers can distinguish idempotent no-op from a true
    double-commit.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        snapshot_id: uuid.UUID,
        period_key: str,
        current_state: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"snapshot {snapshot_id} already in state={current_state!r}, "
            f"commit rejected (expected 'verified')"
        )
        self.tenant_id = tenant_id
        self.snapshot_id = snapshot_id
        self.period_key = period_key
        self.current_state = current_state
        self.trace_id = trace_id


# ── 2. ReversalSnapshotMismatchError ──────────────────────────
class ReversalSnapshotMismatchError(Exception):
    """422 REVERSAL_SNAPSHOT_MISMATCH — target_event's snapshot_id != committed.

    AD-22 reversal requires the underlying fiscal_period_snapshots.state
    to be `committed` (3-tier guard introduced in 11-3). If a reversal
    is attempted while the snapshot is `verified` or `reversed`, this
    error fires so the caller can drive a clean recovery (commit the
    snapshot first, or pick a different reversal target).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        target_event_id: uuid.UUID,
        snapshot_id: uuid.UUID | None,
        current_state: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"reversal target {target_event_id} references snapshot "
            f"{snapshot_id} in state={current_state!r} (expected 'committed')"
        )
        self.tenant_id = tenant_id
        self.target_event_id = target_event_id
        self.snapshot_id = snapshot_id
        self.current_state = current_state
        self.trace_id = trace_id


# ── 3. ReopenOperatorActionInvalidError ──────────────────────
class ReopenOperatorActionInvalidError(Exception):
    """422 REOPEN_OPERATOR_ACTION_INVALID — operator_action not in 4-value enum.

    W2 reopen flow: `operator_action` must be one of
    `{operator_reopen, audit_finding, legal_compliance, data_correction}`
    AND `reason` must satisfy length 20-500 (AD-10 owner-only + AD-15
    audit-justification). This exception covers BOTH invalid enum and
    invalid length cases.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        fiscal_period_id: uuid.UUID,
        operator_action: str,
        reason_length: int,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"reopen operator_action={operator_action!r} invalid "
            f"(reason length={reason_length}, expected 20-500 chars)"
        )
        self.tenant_id = tenant_id
        self.fiscal_period_id = fiscal_period_id
        self.operator_action = operator_action
        self.reason_length = reason_length
        self.trace_id = trace_id


# ── 4. ReopenAuditEmitFailedError ────────────────────────────
class ReopenAuditEmitFailedError(Exception):
    """500 REOPEN_AUDIT_EMIT_FAILED — audit-first emit failed on reopen.

    The reopen flow is audit-first (CR 1.1 invariant). If the audit row
    fails to persist, the data write is rolled back and this error fires.
    Distinct from ClosingSequenceAuditEmitError so M11 reopen gets its
    own observability bucket.
    """

    def __init__(self, *, message: str, trace_id: str) -> None:
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id


__all__ = [
    "ReopenAuditEmitFailedError",
    "ReopenOperatorActionInvalidError",
    "ReversalSnapshotMismatchError",
    "SnapshotAlreadyCommittedError",
]