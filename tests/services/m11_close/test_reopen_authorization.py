"""tests.services.m11_close.test_reopen_authorization — Story 11.3 pure kernel.

W2 reopen flow pure kernel tests. Per AC #10 spec:
- REOPEN_OPERATOR_ACTIONS 4-value enum constant
- REOPEN_REASON_MIN_LENGTH=20, REOPEN_REASON_MAX_LENGTH=500
- Happy path: all gates pass → authorized=True
- Rejected: not_owner → NOT_OWNER_ROLE Korean SSOT
- Rejected: capability_granted=False → NO_CAPABILITY
- Rejected: invalid operator_action → INVALID_OPERATOR
- Rejected: reason too short (< 20 chars) → TOO_SHORT
- Rejected: reason too long (> 500 chars) → TOO_LONG
- Korean SSOT constants
- Non-UUID actor/tenant raises
- Operator action enum exhaustive test
"""

from __future__ import annotations

import uuid

import pytest

from packages.services.m11_close.reopen_authorization import (
    ERROR_CODE_INVALID_OPERATOR_ACTION,
    ERROR_CODE_NON_UUID_ACTOR,
    ERROR_CODE_NON_UUID_TENANT,
    ERROR_CODE_NO_CAPABILITY,
    ERROR_CODE_NOT_OWNER,
    REOPEN_AUTHORIZE_OK_KO,
    REOPEN_OPERATOR_ACTIONS,
    REOPEN_REASON_MAX_LENGTH,
    REOPEN_REASON_MIN_LENGTH,
    REOPEN_REJECT_INVALID_OPERATOR_KO,
    REOPEN_REJECT_NO_CAPABILITY_KO,
    REOPEN_REJECT_NOT_OWNER_KO,
    REOPEN_REJECT_REASON_TOO_LONG_KO,
    REOPEN_REJECT_REASON_TOO_SHORT_KO,
    ReopenAuthorizationError,
    authorize_reopen,
)


# ── 1. Constants ────────────────────────────────────────────
def test_reopen_operator_actions_has_4_values() -> None:
    """REOPEN_OPERATOR_ACTIONS has exactly 4 values."""
    assert len(REOPEN_OPERATOR_ACTIONS) == 4
    assert REOPEN_OPERATOR_ACTIONS == frozenset(
        {
            "operator_reopen",
            "audit_finding",
            "legal_compliance",
            "data_correction",
        }
    )


def test_reopen_reason_min_length_is_20() -> None:
    """REOPEN_REASON_MIN_LENGTH = 20 (AD-15 audit-justification)."""
    assert REOPEN_REASON_MIN_LENGTH == 20


def test_reopen_reason_max_length_is_500() -> None:
    """REOPEN_REASON_MAX_LENGTH = 500 (AD-15 audit-justification)."""
    assert REOPEN_REASON_MAX_LENGTH == 500


# ── 2. Korean SSOT constants ──────────────────────────────
def test_korean_ssot_ok() -> None:
    """REOPEN_AUTHORIZE_OK_KO = '재오픈 승인 완료'."""
    assert REOPEN_AUTHORIZE_OK_KO == "재오픈 승인 완료"


def test_korean_ssot_reject_not_owner() -> None:
    """REOPEN_REJECT_NOT_OWNER_KO = '소유자 역할이 아닙니다 — 재오픈 불가'."""
    assert REOPEN_REJECT_NOT_OWNER_KO == "소유자 역할이 아닙니다 — 재오픈 불가"


def test_korean_ssot_reject_no_capability() -> None:
    """REOPEN_REJECT_NO_CAPABILITY_KO = '재오픈 권한 미보유'."""
    assert REOPEN_REJECT_NO_CAPABILITY_KO == "재오픈 권한 미보유"


def test_korean_ssot_reject_invalid_operator() -> None:
    """REOPEN_REJECT_INVALID_OPERATOR_KO Korean SSOT."""
    assert REOPEN_REJECT_INVALID_OPERATOR_KO == (
        "재오픈 사유 분류가 올바르지 않습니다"
    )


def test_korean_ssot_reject_too_short() -> None:
    """REOPEN_REJECT_REASON_TOO_SHORT_KO Korean SSOT."""
    assert REOPEN_REJECT_REASON_TOO_SHORT_KO == (
        "재오픈 사유는 20자 이상이어야 합니다"
    )


def test_korean_ssot_reject_too_long() -> None:
    """REOPEN_REJECT_REASON_TOO_LONG_KO Korean SSOT."""
    assert REOPEN_REJECT_REASON_TOO_LONG_KO == (
        "재오픈 사유는 500자 이하여야 합니다"
    )


# ── 3. Happy path ──────────────────────────────────────────
def test_authorized_when_all_gates_pass() -> None:
    """All gates pass → authorized=True."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 20,  # exactly 20 chars
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is True
    assert result.reject_reason_ko is None
    assert result.operator_action == "operator_reopen"
    assert result.reason_length == 20


# ── 4. Rejected: not owner ────────────────────────────────
def test_rejected_when_not_owner() -> None:
    """is_owner=False → REOPEN_REJECT_NOT_OWNER_KO."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 50,
        capability_granted=True,
        is_owner=False,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_NOT_OWNER_KO


# ── 5. Rejected: no capability ─────────────────────────────
def test_rejected_when_no_capability() -> None:
    """capability_granted=False → REOPEN_REJECT_NO_CAPABILITY_KO."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 50,
        capability_granted=False,
        is_owner=True,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_NO_CAPABILITY_KO


# ── 6. Rejected: invalid operator_action ───────────────────
def test_rejected_when_invalid_operator_action() -> None:
    """operator_action='not_in_enum' → REOPEN_REJECT_INVALID_OPERATOR_KO."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="not_in_enum",
        reason="A" * 50,
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_INVALID_OPERATOR_KO


# ── 7. Rejected: reason too short ─────────────────────────
def test_rejected_when_reason_too_short() -> None:
    """reason < 20 chars → REOPEN_REJECT_REASON_TOO_SHORT_KO."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 19,  # 19 chars (one short)
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_REASON_TOO_SHORT_KO
    assert result.reason_length == 19


# ── 8. Rejected: reason too long ──────────────────────────
def test_rejected_when_reason_too_long() -> None:
    """reason > 500 chars → REOPEN_REJECT_REASON_TOO_LONG_KO."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 501,  # 501 chars (one over)
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_REASON_TOO_LONG_KO
    assert result.reason_length == 501


# ── 9. All 4 operator_action values accepted ──────────────
@pytest.mark.parametrize(
    "operator_action",
    ["operator_reopen", "audit_finding", "legal_compliance", "data_correction"],
)
def test_all_4_operator_actions_authorized(operator_action: str) -> None:
    """All 4 REOPEN_OPERATOR_ACTIONS values are accepted."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action=operator_action,
        reason="A" * 50,
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is True
    assert result.operator_action == operator_action


# ── 10. Non-UUID tenant raises ─────────────────────────────
def test_non_uuid_tenant_raises() -> None:
    """tenant_id non-UUID raises ReopenAuthorizationError."""
    with pytest.raises(ReopenAuthorizationError) as exc_info:
        authorize_reopen(
            tenant_id="not-a-uuid",  # type: ignore[arg-type]
            actor_id=uuid.uuid4(),
            operator_action="operator_reopen",
            reason="A" * 50,
            capability_granted=True,
            is_owner=True,
        )
    assert exc_info.value.error_code == ERROR_CODE_NON_UUID_TENANT


# ── 11. Non-UUID actor raises ─────────────────────────────
def test_non_uuid_actor_raises() -> None:
    """actor_id non-UUID raises ReopenAuthorizationError."""
    with pytest.raises(ReopenAuthorizationError) as exc_info:
        authorize_reopen(
            tenant_id=uuid.uuid4(),
            actor_id="not-a-uuid",  # type: ignore[arg-type]
            operator_action="operator_reopen",
            reason="A" * 50,
            capability_granted=True,
            is_owner=True,
        )
    assert exc_info.value.error_code == ERROR_CODE_NON_UUID_ACTOR


# ── 12. Error codes stable ─────────────────────────────────
def test_error_codes_stable() -> None:
    """All error codes are stable identifiers."""
    assert ERROR_CODE_INVALID_OPERATOR_ACTION == "INVALID_OPERATOR_ACTION"
    assert ERROR_CODE_NO_CAPABILITY == "NO_CAPABILITY"
    assert ERROR_CODE_NOT_OWNER == "NOT_OWNER_ROLE"
    assert ERROR_CODE_NON_UUID_ACTOR == "NON_UUID_ACTOR_ID"
    assert ERROR_CODE_NON_UUID_TENANT == "NON_UUID_TENANT_ID"


# ── 13. Borderline — exactly 20 chars authorized ──────────
def test_borderline_min_length_authorized() -> None:
    """Exactly 20 chars is authorized (boundary check)."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 20,
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is True
    assert result.reason_length == 20


# ── 14. Borderline — exactly 500 chars authorized ─────────
def test_borderline_max_length_authorized() -> None:
    """Exactly 500 chars is authorized (boundary check)."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 500,
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is True
    assert result.reason_length == 500


# ── 15. Result NamedTuple immutable ──────────────────────
def test_result_namedtuple_immutable() -> None:
    """ReopenAuthorizationResult is immutable."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 50,
        capability_granted=True,
        is_owner=True,
    )
    with pytest.raises(AttributeError):
        result.authorized = False  # type: ignore[misc]


# ── 16. Priority — not_owner beats no_capability ──────────
def test_priority_not_owner_beats_no_capability() -> None:
    """not_owner is checked BEFORE capability_granted (gate priority)."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="operator_reopen",
        reason="A" * 50,
        capability_granted=False,  # also fails capability
        is_owner=False,  # also fails owner
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_NOT_OWNER_KO


# ── 17. Priority — operator_action beats reason length ────
def test_priority_operator_action_beats_reason_length() -> None:
    """invalid operator_action is checked BEFORE reason length."""
    result = authorize_reopen(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        operator_action="not_in_enum",
        reason="A" * 5,  # also fails length
        capability_granted=True,
        is_owner=True,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == REOPEN_REJECT_INVALID_OPERATOR_KO