"""tests.services.m11_close.test_commit_snapshot_persistence — Story 11.3 pure kernel.

20 cases per AC #3 spec — verify the AD-20 verified → committed
transition kernel:
- Valid state transitions
- Idempotent no-op on 'committed' state
- Terminal rejection on 'reversed' state
- Non-committable 'draft' state
- Invalid input shape (non-UUID, unknown state)
- Korean SSOT constants
- AUTHORIZABLE_TARGET_EVENT_TYPES layering
"""

from __future__ import annotations

import uuid

import pytest

from packages.services.m11_close.commit_snapshot_persistence import (
    ERROR_CODE_ALREADY_REVERSED,
    ERROR_CODE_DRAFT_NOT_COMMITTABLE,
    ERROR_CODE_INVALID_INPUT,
    IDEMPOTENT_NOOP_STATE,
    NON_COMMITTABLE_FROM_STATE,
    SNAPSHOT_COMMIT_DRAFT_REJECT_KO,
    SNAPSHOT_COMMIT_IDEMPOTENT_KO,
    SNAPSHOT_COMMIT_OK_KO,
    SNAPSHOT_COMMIT_REVERSED_REJECT_KO,
    TERMINAL_STATE,
    VALID_COMMIT_FROM_STATE,
    CommitSnapshotPersistenceError,
    CommitSnapshotPersistenceResult,
    validate_commit_snapshot_persistence,
)


# ── Common fixtures ──────────────────────────────────────────
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def snapshot_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def actor_id() -> uuid.UUID:
    return uuid.uuid4()


# ── 1. Constants — AD-20 lifecycle sets ─────────────────────
def test_valid_commit_from_state_is_verified_only() -> None:
    """VALID_COMMIT_FROM_STATE = {verified} only."""
    assert VALID_COMMIT_FROM_STATE == frozenset({"verified"})


def test_idempotent_noop_state_is_committed_only() -> None:
    """IDEMPOTENT_NOOP_STATE = {committed} only."""
    assert IDEMPOTENT_NOOP_STATE == frozenset({"committed"})


def test_terminal_state_is_reversed_only() -> None:
    """TERMINAL_STATE = {reversed} only — terminal AD-20 state."""
    assert TERMINAL_STATE == frozenset({"reversed"})


def test_non_committable_from_state_is_draft_only() -> None:
    """NON_COMMITTABLE_FROM_STATE = {draft} only — pre-verifier state."""
    assert NON_COMMITTABLE_FROM_STATE == frozenset({"draft"})


# ── 2. Korean constants (AD-15 §11 SSOT) ───────────────────
def test_korean_ssot_commit_ok() -> None:
    """SNAPSHOT_COMMIT_OK_KO must match the SSOT string verbatim."""
    assert SNAPSHOT_COMMIT_OK_KO == "스냅샷 영구화 완료"


def test_korean_ssot_idempotent() -> None:
    """SNAPSHOT_COMMIT_IDEMPOTENT_KO must match the SSOT string."""
    assert SNAPSHOT_COMMIT_IDEMPOTENT_KO == "스냅샷 이미 영구화됨 — 멱등 처리"


def test_korean_ssot_draft_reject() -> None:
    """SNAPSHOT_COMMIT_DRAFT_REJECT_KO must match the SSOT string."""
    assert SNAPSHOT_COMMIT_DRAFT_REJECT_KO == (
        "스냅샷이 검증 전 상태 — 영구화 불가"
    )


def test_korean_ssot_reversed_reject() -> None:
    """SNAPSHOT_COMMIT_REVERSED_REJECT_KO must match the SSOT string."""
    assert SNAPSHOT_COMMIT_REVERSED_REJECT_KO == (
        "스냅샷이 이미 역분개됨 — 영구화 불가"
    )


# ── 3. Error code constants ─────────────────────────────────
def test_error_code_draft_not_committable() -> None:
    """ERROR_CODE_DRAFT_NOT_COMMITTABLE is the stable identifier."""
    assert ERROR_CODE_DRAFT_NOT_COMMITTABLE == "SNAPSHOT_DRAFT_NOT_COMMITTABLE"


def test_error_code_already_reversed() -> None:
    """ERROR_CODE_ALREADY_REVERSED is the stable identifier."""
    assert ERROR_CODE_ALREADY_REVERSED == "SNAPSHOT_ALREADY_REVERSED"


def test_error_code_invalid_input() -> None:
    """ERROR_CODE_INVALID_INPUT is the stable identifier."""
    assert ERROR_CODE_INVALID_INPUT == "INVALID_COMMIT_INPUT"


# ── 4. Valid transition (verified → committed) ──────────────
def test_valid_transition_verified_to_committed(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """state='verified' → authorized=True, idempotent_ok=False."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-08",
        current_state="verified",
        actor_id=actor_id,
    )
    assert isinstance(result, CommitSnapshotPersistenceResult)
    assert result.authorized is True
    assert result.idempotent_ok is False
    assert result.terminal_rejected is False
    assert result.commit_from_state == "verified"
    assert result.snapshot_id == snapshot_id
    assert result.period_key == "2026-08"
    assert result.actor_id == actor_id
    assert result.tenant_id == tenant_id


# ── 5. Idempotent no-op (committed state) ───────────────────
def test_idempotent_noop_on_committed_state(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """state='committed' → authorized=True, idempotent_ok=True (CR 1.1)."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-08",
        current_state="committed",
        actor_id=actor_id,
    )
    assert result.authorized is True
    assert result.idempotent_ok is True
    assert result.terminal_rejected is False


# ── 6. Terminal rejection (reversed state) ─────────────────
def test_terminal_rejection_on_reversed_state(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """state='reversed' → authorized=False, terminal_rejected=True."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-08",
        current_state="reversed",
        actor_id=actor_id,
    )
    assert result.authorized is False
    assert result.idempotent_ok is False
    assert result.terminal_rejected is True


# ── 7. Non-committable rejection (draft state) ─────────────
def test_non_committable_rejection_on_draft_state(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """state='draft' → authorized=False (verifiers not yet passed)."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-08",
        current_state="draft",
        actor_id=actor_id,
    )
    assert result.authorized is False
    assert result.idempotent_ok is False
    assert result.terminal_rejected is False


# ── 8. Invalid input shape — non-UUID actor ────────────────
def test_invalid_input_non_uuid_actor(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
) -> None:
    """Non-UUID actor_id raises CommitSnapshotPersistenceError."""
    with pytest.raises(CommitSnapshotPersistenceError) as exc_info:
        validate_commit_snapshot_persistence(
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            period_key="2026-08",
            current_state="verified",
            actor_id="not-a-uuid",  # type: ignore[arg-type]
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_INPUT


# ── 9. Invalid input shape — non-UUID tenant ────────────────
def test_invalid_input_non_uuid_tenant(
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Non-UUID tenant_id raises CommitSnapshotPersistenceError."""
    with pytest.raises(CommitSnapshotPersistenceError) as exc_info:
        validate_commit_snapshot_persistence(
            tenant_id="not-a-uuid",  # type: ignore[arg-type]
            snapshot_id=snapshot_id,
            period_key="2026-08",
            current_state="verified",
            actor_id=actor_id,
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_INPUT


# ── 10. Invalid input shape — non-UUID snapshot ────────────
def test_invalid_input_non_uuid_snapshot(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Non-UUID snapshot_id raises CommitSnapshotPersistenceError."""
    with pytest.raises(CommitSnapshotPersistenceError) as exc_info:
        validate_commit_snapshot_persistence(
            tenant_id=tenant_id,
            snapshot_id="not-a-uuid",  # type: ignore[arg-type]
            period_key="2026-08",
            current_state="verified",
            actor_id=actor_id,
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_INPUT


# ── 11. Invalid input shape — empty period_key ─────────────
def test_invalid_input_empty_period_key(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Empty period_key raises CommitSnapshotPersistenceError."""
    with pytest.raises(CommitSnapshotPersistenceError) as exc_info:
        validate_commit_snapshot_persistence(
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            period_key="",
            current_state="verified",
            actor_id=actor_id,
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_INPUT


# ── 12. Invalid input shape — unknown state ────────────────
def test_invalid_input_unknown_state(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Unknown current_state raises CommitSnapshotPersistenceError."""
    with pytest.raises(CommitSnapshotPersistenceError) as exc_info:
        validate_commit_snapshot_persistence(
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            period_key="2026-08",
            current_state="not_a_state",
            actor_id=actor_id,
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_INPUT
    assert exc_info.value.snapshot_id == snapshot_id
    assert exc_info.value.current_state == "not_a_state"


# ── 13. Exception attributes ──────────────────────────────
def test_exception_attributes_propagate(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """CommitSnapshotPersistenceError carries snapshot_id + current_state."""
    with pytest.raises(CommitSnapshotPersistenceError) as exc_info:
        validate_commit_snapshot_persistence(
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            period_key="2026-08",
            current_state="future_state",
            actor_id=actor_id,
        )
    assert exc_info.value.snapshot_id == snapshot_id
    assert exc_info.value.current_state == "future_state"


# ── 14. Period key propagation ────────────────────────────
def test_period_key_propagates_to_result(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """period_key is propagated to the result for downstream cache invalidation."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-12",
        current_state="verified",
        actor_id=actor_id,
    )
    assert result.period_key == "2026-12"


# ── 15. Result is a NamedTuple ────────────────────────────
def test_result_is_named_tuple(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """CommitSnapshotPersistenceResult is a NamedTuple (immutable + indexable)."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-08",
        current_state="verified",
        actor_id=actor_id,
    )
    # NamedTuple fields are indexable.
    assert result[0] is True or result[0] is False  # authorized
    # NamedTuple fields are immutable.
    with pytest.raises(AttributeError):
        result.authorized = False  # type: ignore[misc]


# ── 16. All 4 AD-20 states covered ────────────────────────
@pytest.mark.parametrize("state", ["draft", "verified", "committed", "reversed"])
def test_all_4_ad_20_states_handled(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    state: str,
) -> None:
    """All 4 AD-20 states must be handled without raising."""
    result = validate_commit_snapshot_persistence(
        tenant_id=tenant_id,
        snapshot_id=snapshot_id,
        period_key="2026-08",
        current_state=state,
        actor_id=actor_id,
    )
    assert isinstance(result, CommitSnapshotPersistenceResult)
    # authorized must be bool
    assert isinstance(result.authorized, bool)


# ── 17. Korean SSOT string constants exist ────────────────
def test_korean_constants_exist() -> None:
    """All 4 Korean constants must exist (defense-in-depth)."""
    assert SNAPSHOT_COMMIT_OK_KO
    assert SNAPSHOT_COMMIT_IDEMPOTENT_KO
    assert SNAPSHOT_COMMIT_DRAFT_REJECT_KO
    assert SNAPSHOT_COMMIT_REVERSED_REJECT_KO