"""packages.services.m11_close.commit_snapshot_persistence — Story 11.3 pure kernel.

AD-20 state machine: `draft` → `verified` → `committed` → `reversed`.

This kernel validates the `verified → committed` transition (the
"commit_snapshot_persistence" step) — the FIRST AD-20 transition that
the M11 owner (Epic 11) controls. Earlier transitions
(`draft → verified`) are owned by Epic 4 + V1·V4·V7·V8 verifiers; this
kernel is the M11 handoff for sealing a verified snapshot as
immutable summary record.

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Service layer passes all inputs explicitly.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-snapshot.ts`.

Story 11.3 wire:
- valid state for commit: "verified" (only).
- invalid states: "draft" (V1·V4·V7·V8 not yet passed),
  "committed" (idempotent no-op → return idempotent_ok=True), and
  "reversed" (terminal state — cannot re-commit a reversed snapshot).
- idempotent no-op: re-commit on "committed" returns success without
  raising (CR 1.1 audit-first invariant).
- The reverse transition "committed → reversed" lives in the
  `reversal_execute_snapshot` kernel (Story 11.3 T4).
"""

from __future__ import annotations

import uuid
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# AD-20 4-state lifecycle: draft → verified → committed → reversed.
VALID_COMMIT_FROM_STATE: Final[frozenset[str]] = frozenset({"verified"})
IDEMPOTENT_NOOP_STATE: Final[frozenset[str]] = frozenset({"committed"})
TERMINAL_STATE: Final[frozenset[str]] = frozenset({"reversed"})
NON_COMMITTABLE_FROM_STATE: Final[frozenset[str]] = frozenset({"draft"})

# Error codes — pure-kernel domain semantics.
ERROR_CODE_INVALID_INPUT: Final[str] = "INVALID_COMMIT_INPUT"
ERROR_CODE_DRAFT_NOT_COMMITTABLE: Final[str] = "SNAPSHOT_DRAFT_NOT_COMMITTABLE"
ERROR_CODE_ALREADY_REVERSED: Final[str] = "SNAPSHOT_ALREADY_REVERSED"

# Korean constants — AD-15 §11 SSOT.
SNAPSHOT_COMMIT_OK_KO: Final[str] = "스냅샷 영구화 완료"
SNAPSHOT_COMMIT_IDEMPOTENT_KO: Final[str] = "스냅샷 이미 영구화됨 — 멱등 처리"
SNAPSHOT_COMMIT_DRAFT_REJECT_KO: Final[str] = "스냅샷이 검증 전 상태 — 영구화 불가"
SNAPSHOT_COMMIT_REVERSED_REJECT_KO: Final[str] = "스냅샷이 이미 역분개됨 — 영구화 불가"


# ── Typed exception ──────────────────────────────────────────
class CommitSnapshotPersistenceError(Exception):
    """Pure-kernel commit_snapshot_persistence violation.

    Distinct from service-layer `SnapshotAlreadyCommittedError`. NO
    HTTP mapping; service layer wraps with envelope details.

    Service-layer dispatch uses `err.error_code` (stable Literal).
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str,
        snapshot_id: uuid.UUID | None = None,
        current_state: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.snapshot_id = snapshot_id
        self.current_state = current_state


# ── CommitSnapshotPersistenceResult NamedTuple ──────────────
class CommitSnapshotPersistenceResult(NamedTuple):
    """Authorization + idempotency decision for AD-20 commit transition.

    Service layer wraps this in the wire response + audit payload.

    Fields:
    - authorized: True if the commit transition is permitted (or
        idempotent no-op).
    - idempotent_ok: True if the snapshot was already in 'committed'
        state (no-op path). Distinct from a fresh commit.
    - terminal_rejected: True if the snapshot was in 'reversed' state
        (cannot re-commit a reversed snapshot).
    - commit_from_state: The state the snapshot WAS in before the
        commit (for audit trail).
    - snapshot_id: The snapshot being committed.
    - period_key: The period_key for downstream cache invalidation.
    - actor_id: The actor who initiated the commit (audit attribution).
    - tenant_id: The owning tenant (audit attribution).
    """

    authorized: bool
    idempotent_ok: bool
    terminal_rejected: bool
    commit_from_state: str
    snapshot_id: uuid.UUID
    period_key: str
    actor_id: uuid.UUID
    tenant_id: uuid.UUID


# ── validate_commit_snapshot_persistence ────────────────────
def validate_commit_snapshot_persistence(
    *,
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    period_key: str,
    current_state: str,
    actor_id: uuid.UUID,
) -> CommitSnapshotPersistenceResult:
    """Decide whether AD-20 verified → committed transition is permitted.

    Story 11.3 PRIMARY. The commit_snapshot_persistence step seals a
    verified snapshot as immutable summary record. After this transition,
    only AD-22 reversal (Story 11.3 T4) can mutate the snapshot
    (committed → reversed).

    Args:
        tenant_id: Owning tenant (audit attribution).
        snapshot_id: fiscal_period_snapshots.snapshot_id.
        period_key: AD-24 typed 'YYYY-MM' format.
        current_state: The snapshot's current state (one of
            'draft' / 'verified' / 'committed' / 'reversed').
        actor_id: UUID of the commit initiator.

    Returns:
        CommitSnapshotPersistenceResult with `authorized` flag +
        `idempotent_ok` (true on no-op) + `terminal_rejected` (true on
        reversed state).

    Raises:
        CommitSnapshotPersistenceError: On invalid input shape
            (non-UUID actor / tenant, unknown current_state).
            Caller bugs — should not surface at runtime.
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise CommitSnapshotPersistenceError(
            message=f"tenant_id must be UUID, got {type(tenant_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(snapshot_id, uuid.UUID):
        raise CommitSnapshotPersistenceError(
            message=f"snapshot_id must be UUID, got {type(snapshot_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(actor_id, uuid.UUID):
        raise CommitSnapshotPersistenceError(
            message=f"actor_id must be UUID, got {type(actor_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(period_key, str) or not period_key:
        raise CommitSnapshotPersistenceError(
            message=(f"period_key must be non-empty str, got " f"{type(period_key).__name__!r}"),
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if current_state not in (
        VALID_COMMIT_FROM_STATE
        | IDEMPOTENT_NOOP_STATE
        | TERMINAL_STATE
        | NON_COMMITTABLE_FROM_STATE
    ):
        raise CommitSnapshotPersistenceError(
            message=(
                f"current_state {current_state!r} is not in the known "
                f"AD-20 lifecycle "
                f"({sorted(VALID_COMMIT_FROM_STATE | IDEMPOTENT_NOOP_STATE | TERMINAL_STATE | NON_COMMITTABLE_FROM_STATE)})"
            ),
            error_code=ERROR_CODE_INVALID_INPUT,
            snapshot_id=snapshot_id,
            current_state=current_state,
        )

    # Idempotent no-op: snapshot already committed.
    if current_state in IDEMPOTENT_NOOP_STATE:
        return CommitSnapshotPersistenceResult(
            authorized=True,
            idempotent_ok=True,
            terminal_rejected=False,
            commit_from_state=current_state,
            snapshot_id=snapshot_id,
            period_key=period_key,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Terminal state: cannot re-commit a reversed snapshot.
    if current_state in TERMINAL_STATE:
        return CommitSnapshotPersistenceResult(
            authorized=False,
            idempotent_ok=False,
            terminal_rejected=True,
            commit_from_state=current_state,
            snapshot_id=snapshot_id,
            period_key=period_key,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Non-committable state: 'draft' (V1·V4·V7·V8 not yet passed).
    if current_state in NON_COMMITTABLE_FROM_STATE:
        return CommitSnapshotPersistenceResult(
            authorized=False,
            idempotent_ok=False,
            terminal_rejected=False,
            commit_from_state=current_state,
            snapshot_id=snapshot_id,
            period_key=period_key,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Valid: state='verified' → authorized commit transition.
    return CommitSnapshotPersistenceResult(
        authorized=True,
        idempotent_ok=False,
        terminal_rejected=False,
        commit_from_state=current_state,
        snapshot_id=snapshot_id,
        period_key=period_key,
        actor_id=actor_id,
        tenant_id=tenant_id,
    )


__all__ = [
    "ERROR_CODE_ALREADY_REVERSED",
    "ERROR_CODE_DRAFT_NOT_COMMITTABLE",
    "ERROR_CODE_INVALID_INPUT",
    "IDEMPOTENT_NOOP_STATE",
    "NON_COMMITTABLE_FROM_STATE",
    "SNAPSHOT_COMMIT_DRAFT_REJECT_KO",
    "SNAPSHOT_COMMIT_IDEMPOTENT_KO",
    "SNAPSHOT_COMMIT_OK_KO",
    "SNAPSHOT_COMMIT_REVERSED_REJECT_KO",
    "TERMINAL_STATE",
    "VALID_COMMIT_FROM_STATE",
    "CommitSnapshotPersistenceError",
    "CommitSnapshotPersistenceResult",
    "validate_commit_snapshot_persistence",
]
