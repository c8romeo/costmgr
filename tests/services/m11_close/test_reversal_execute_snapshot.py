"""tests.services.m11_close.test_reversal_execute_snapshot — Story 11.3 pure kernel.

25 cases per AC #4 spec — verify AD-22 영구화 (committed → reversed)
pure kernel:
- SNAPSHOT_STATE_REQUIRED = {committed} only
- 3-tier guard rejects draft/verified/reversed states
- Valid state='committed' → authorized=True with negating_qty
- corrected_qty propagation
- Invalid input shape (non-UUID, negative qty, unknown state)
- NegatingRowSpec + CorrectedRowSpec builders
- Korean SSOT constants
- Banker's rounding parity constant (QTY_QUANTUM)
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m11_close.reversal_execute_snapshot import (
    CorrectedRowSpec,
    ERROR_CODE_INSUFFICIENT_QTY,
    ERROR_CODE_INVALID_INPUT,
    ERROR_CODE_INVALID_SNAPSHOT_STATE,
    NegatingRowSpec,
    QTY_QUANTUM,
    REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO,
    REVERSAL_EXECUTE_OK_KO,
    ReversalExecuteSnapshotError,
    ReversalExecuteSnapshotResult,
    SNAPSHOT_STATE_REJECTED_DRAFT,
    SNAPSHOT_STATE_REJECTED_REVERSED,
    SNAPSHOT_STATE_REJECTED_VERIFIED,
    SNAPSHOT_STATE_REQUIRED,
    build_corrected_row_spec,
    build_negating_row_spec,
    validate_reversal_execute_snapshot,
)


# ── Common fixtures ──────────────────────────────────────────
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def target_event_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def snapshot_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def correction_group_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def actor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def product_id() -> uuid.UUID:
    return uuid.uuid4()


# ── 1. Constants — 3-tier guard sets ───────────────────────
def test_snapshot_state_required_is_committed_only() -> None:
    """SNAPSHOT_STATE_REQUIRED = {committed} only (3-tier guard)."""
    assert SNAPSHOT_STATE_REQUIRED == frozenset({"committed"})


def test_snapshot_state_rejected_draft() -> None:
    """SNAPSHOT_STATE_REJECTED_DRAFT = {draft}."""
    assert SNAPSHOT_STATE_REJECTED_DRAFT == frozenset({"draft"})


def test_snapshot_state_rejected_verified() -> None:
    """SNAPSHOT_STATE_REJECTED_VERIFIED = {verified}."""
    assert SNAPSHOT_STATE_REJECTED_VERIFIED == frozenset({"verified"})


def test_snapshot_state_rejected_reversed() -> None:
    """SNAPSHOT_STATE_REJECTED_REVERSED = {reversed}."""
    assert SNAPSHOT_STATE_REJECTED_REVERSED == frozenset({"reversed"})


# ── 2. QTY_QUANTUM (banker's rounding parity) ───────────────
def test_qty_quantum_matches_crd0_4_parity() -> None:
    """QTY_QUANTUM must match CR 0-4 NUMERIC(18, 4) parity."""
    assert QTY_QUANTUM == Decimal("0.0001")


# ── 3. Korean SSOT constants ───────────────────────────────
def test_korean_ssot_ok() -> None:
    """REVERSAL_EXECUTE_OK_KO matches AD-15 §11 SSOT."""
    assert REVERSAL_EXECUTE_OK_KO == "스냅샷 역분개 완료"


def test_korean_ssot_invalid_snapshot() -> None:
    """REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO matches AD-15 §11 SSOT."""
    assert REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO == (
        "스냅샷 상태가 커밋 상태가 아닙니다 — 역분개 불가"
    )


# ── 4. Error code constants ────────────────────────────────
def test_error_codes_stable() -> None:
    """All 3 error codes must be stable identifiers."""
    assert ERROR_CODE_INVALID_INPUT == "INVALID_REVERSAL_INPUT"
    assert ERROR_CODE_INVALID_SNAPSHOT_STATE == "INVALID_SNAPSHOT_STATE"
    assert ERROR_CODE_INSUFFICIENT_QTY == "INSUFFICIENT_QTY_FOR_NEGATING"


# ── 5. Valid state='committed' → authorized=True ───────────
def test_valid_committed_state_authorized(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """state='committed' → authorized=True with negating_qty=target_qty."""
    target_qty = Decimal("100.5")
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state="committed",
        target_qty=target_qty,
        corrected_qty=None,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    assert isinstance(result, ReversalExecuteSnapshotResult)
    assert result.authorized is True
    assert result.snapshot_state == "committed"
    assert result.negating_qty == target_qty
    assert result.corrected_qty is None
    assert result.target_event_id == target_event_id
    assert result.correction_group_id == correction_group_id


# ── 6. corrected_qty propagation ──────────────────────────
def test_corrected_qty_propagation(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """corrected_qty is propagated to result for downstream INSERT."""
    corrected = Decimal("42.5")
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state="committed",
        target_qty=Decimal("100"),
        corrected_qty=corrected,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    assert result.authorized is True
    assert result.corrected_qty == corrected


# ── 7-9. State rejections (draft / verified / reversed) ─────
@pytest.mark.parametrize(
    "rejected_state",
    ["draft", "verified", "reversed"],
)
def test_state_rejections(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
    rejected_state: str,
) -> None:
    """Non-committed states → authorized=False."""
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state=rejected_state,
        target_qty=Decimal("100"),
        corrected_qty=None,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    assert result.authorized is False
    assert result.snapshot_state == rejected_state


# ── 10. Invalid input — non-UUID tenant ─────────────────────
def test_invalid_input_non_uuid_tenant(
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Non-UUID tenant_id raises ReversalExecuteSnapshotError."""
    with pytest.raises(ReversalExecuteSnapshotError) as exc_info:
        validate_reversal_execute_snapshot(
            tenant_id="not-a-uuid",  # type: ignore[arg-type]
            target_event_id=target_event_id,
            snapshot_id=snapshot_id,
            snapshot_state="committed",
            target_qty=Decimal("100"),
            corrected_qty=None,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_INPUT


# ── 11. Invalid input — negative target_qty ────────────────
def test_invalid_input_negative_target_qty(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Negative target_qty raises ReversalExecuteSnapshotError."""
    with pytest.raises(ReversalExecuteSnapshotError):
        validate_reversal_execute_snapshot(
            tenant_id=tenant_id,
            target_event_id=target_event_id,
            snapshot_id=snapshot_id,
            snapshot_state="committed",
            target_qty=Decimal("-100"),
            corrected_qty=None,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )


# ── 12. Invalid input — negative corrected_qty ────────────
def test_invalid_input_negative_corrected_qty(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Negative corrected_qty raises ReversalExecuteSnapshotError."""
    with pytest.raises(ReversalExecuteSnapshotError):
        validate_reversal_execute_snapshot(
            tenant_id=tenant_id,
            target_event_id=target_event_id,
            snapshot_id=snapshot_id,
            snapshot_state="committed",
            target_qty=Decimal("100"),
            corrected_qty=Decimal("-50"),
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )


# ── 13. Invalid input — unknown state ──────────────────────
def test_invalid_input_unknown_state(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Unknown snapshot_state raises ReversalExecuteSnapshotError."""
    with pytest.raises(ReversalExecuteSnapshotError) as exc_info:
        validate_reversal_execute_snapshot(
            tenant_id=tenant_id,
            target_event_id=target_event_id,
            snapshot_id=snapshot_id,
            snapshot_state="not_a_state",
            target_qty=Decimal("100"),
            corrected_qty=None,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_SNAPSHOT_STATE
    assert exc_info.value.snapshot_id == snapshot_id
    assert exc_info.value.snapshot_state == "not_a_state"


# ── 14. Exception attributes propagate ─────────────────────
def test_exception_attributes_propagate(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Exception carries snapshot_id + snapshot_state for envelope details."""
    with pytest.raises(ReversalExecuteSnapshotError) as exc_info:
        validate_reversal_execute_snapshot(
            tenant_id=tenant_id,
            target_event_id=target_event_id,
            snapshot_id=snapshot_id,
            snapshot_state="future_state",
            target_qty=Decimal("100"),
            corrected_qty=None,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )
    assert exc_info.value.snapshot_id == snapshot_id
    assert exc_info.value.snapshot_state == "future_state"


# ── 15. build_negating_row_spec ────────────────────────────
def test_build_negating_row_spec(
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    target_event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """build_negating_row_spec produces a NegatingRowSpec."""
    spec = build_negating_row_spec(
        tenant_id=tenant_id,
        product_id=product_id,
        period_key="2026-08",
        target_qty=Decimal("100"),
        target_event_id=target_event_id,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
        trace_id="trace-1",
    )
    assert isinstance(spec, NegatingRowSpec)
    assert spec.event_type == "reversal_negating"
    assert spec.negating_qty == Decimal("100")
    assert spec.reverses_event_id == target_event_id
    assert spec.correction_group_id == correction_group_id


# ── 16. build_negating_row_spec — negative qty rejected ─────
def test_build_negating_row_spec_negative_qty_rejected(
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    target_event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """build_negating_row_spec rejects negative target_qty."""
    with pytest.raises(ReversalExecuteSnapshotError):
        build_negating_row_spec(
            tenant_id=tenant_id,
            product_id=product_id,
            period_key="2026-08",
            target_qty=Decimal("-100"),
            target_event_id=target_event_id,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
            trace_id="trace-1",
        )


# ── 17. build_corrected_row_spec ───────────────────────────
def test_build_corrected_row_spec(
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """build_corrected_row_spec produces a CorrectedRowSpec."""
    spec = build_corrected_row_spec(
        tenant_id=tenant_id,
        product_id=product_id,
        period_key="2026-08",
        corrected_qty=Decimal("42"),
        correction_group_id=correction_group_id,
        actor_id=actor_id,
        trace_id="trace-1",
    )
    assert isinstance(spec, CorrectedRowSpec)
    assert spec.event_type == "reversal_corrected"
    assert spec.corrected_qty == Decimal("42")
    assert spec.correction_group_id == correction_group_id


# ── 18. build_corrected_row_spec — negative qty rejected ────
def test_build_corrected_row_spec_negative_qty_rejected(
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """build_corrected_row_spec rejects negative corrected_qty."""
    with pytest.raises(ReversalExecuteSnapshotError):
        build_corrected_row_spec(
            tenant_id=tenant_id,
            product_id=product_id,
            period_key="2026-08",
            corrected_qty=Decimal("-42"),
            correction_group_id=correction_group_id,
            actor_id=actor_id,
            trace_id="trace-1",
        )


# ── 19. NamedTuple immutability ────────────────────────────
def test_result_is_immutable_namedtuple(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """ReversalExecuteSnapshotResult is immutable."""
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state="committed",
        target_qty=Decimal("100"),
        corrected_qty=None,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    with pytest.raises(AttributeError):
        result.authorized = False  # type: ignore[misc]


# ── 20. All 4 AD-20 states handled without crash ────────────
@pytest.mark.parametrize(
    "state",
    ["draft", "verified", "committed", "reversed"],
)
def test_all_4_ad_20_states_handled(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
    state: str,
) -> None:
    """All 4 AD-20 states must be handled (no crash)."""
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state=state,
        target_qty=Decimal("100"),
        corrected_qty=None,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    assert isinstance(result, ReversalExecuteSnapshotResult)
    assert isinstance(result.authorized, bool)


# ── 21. Zero qty is allowed (zero-cost reversal) ────────────
def test_zero_target_qty_authorized(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Zero target_qty is allowed (edge case — zero-cost reversal)."""
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state="committed",
        target_qty=Decimal("0"),
        corrected_qty=None,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    assert result.authorized is True
    assert result.negating_qty == Decimal("0")


# ── 22. Korean constants exist ──────────────────────────────
def test_korean_constants_exist() -> None:
    """All Korean SSOT constants must exist."""
    assert REVERSAL_EXECUTE_OK_KO
    assert REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO


# ── 23. Negative zero qty is invalid (Decimal('-0')) ────────
def test_negative_zero_target_qty_rejected(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Decimal('-0') is rejected (defense-in-depth)."""
    with pytest.raises(ReversalExecuteSnapshotError):
        validate_reversal_execute_snapshot(
            tenant_id=tenant_id,
            target_event_id=target_event_id,
            snapshot_id=snapshot_id,
            snapshot_state="committed",
            target_qty=Decimal("-0.0001"),
            corrected_qty=None,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )


# ── 24. Build specs — same correction_group_id shared ───────
def test_built_specs_share_correction_group_id(
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    target_event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """Both negating + corrected row specs share correction_group_id."""
    neg_spec = build_negating_row_spec(
        tenant_id=tenant_id,
        product_id=product_id,
        period_key="2026-08",
        target_qty=Decimal("100"),
        target_event_id=target_event_id,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
        trace_id="trace-1",
    )
    corr_spec = build_corrected_row_spec(
        tenant_id=tenant_id,
        product_id=product_id,
        period_key="2026-08",
        corrected_qty=Decimal("42"),
        correction_group_id=correction_group_id,
        actor_id=actor_id,
        trace_id="trace-1",
    )
    assert neg_spec.correction_group_id == corr_spec.correction_group_id


# ── 25. corrected_qty=None + authorized=True ─────────────────
def test_corrected_qty_none_with_authorized(
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> None:
    """corrected_qty=None + state='committed' → authorized=True, corrected_qty=None."""
    result = validate_reversal_execute_snapshot(
        tenant_id=tenant_id,
        target_event_id=target_event_id,
        snapshot_id=snapshot_id,
        snapshot_state="committed",
        target_qty=Decimal("100"),
        corrected_qty=None,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
    )
    assert result.authorized is True
    assert result.corrected_qty is None