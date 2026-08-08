"""tests.services.m11_close.test_partial_close_guard — Story 11.2 pure kernel #2.

~15 tests covering:
- 0/1/2/3/4 stages complete (4단계 모두 완료 → allowed)
- 3/2/1/0 stages complete (partial close → blocked)
- chronological invariant delegation
- Korean SSOT constants
"""

from __future__ import annotations

from datetime import datetime, timedelta

from packages.services.m11_close.partial_close_guard import (
    ERROR_CODE_PARTIAL_CLOSE,
    MISSING_STEP_ABC_KO,
    MISSING_STEP_COMMON_KO,
    MISSING_STEP_DIVISIONS_KO,
    MISSING_STEP_MANUFACTURING_KO,
    PARTIAL_CLOSE_BLOCKED_KO,
    PartialCloseGuardError,
    check_partial_close_attempt,
)

_BASE_TS = datetime(2026, 8, 1, 0, 0, 0)


def _ts(offset_minutes: int = 0) -> datetime:
    return _BASE_TS + timedelta(minutes=offset_minutes)


# ── Module surface ──────────────────────────────────────────
def test_module_exports_partial_close_blocked_ko() -> None:
    assert PARTIAL_CLOSE_BLOCKED_KO == "부분 마감은 허용되지 않습니다"


def test_module_exports_missing_step_ko_constants() -> None:
    assert MISSING_STEP_DIVISIONS_KO == "divisions 단계 미완료"
    assert MISSING_STEP_MANUFACTURING_KO == "manufacturing 단계 미완료"
    assert MISSING_STEP_ABC_KO == "abc 단계 미완료"
    assert MISSING_STEP_COMMON_KO == "common 단계 미완료"


def test_module_exports_error_code() -> None:
    assert ERROR_CODE_PARTIAL_CLOSE == "PARTIAL_CLOSE_BLOCKED"


# ── 4 stages complete → allowed ─────────────────────────────
def test_all_four_stages_complete_allows_confirm() -> None:
    result = check_partial_close_attempt(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=_ts(30),
    )
    assert result.blocked is False
    assert result.missing_step is None
    assert result.reject_reason_ko is None


# ── 3 stages complete → blocked, missing common ─────────────
def test_three_stages_complete_blocks_missing_common() -> None:
    result = check_partial_close_attempt(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=None,
    )
    assert result.blocked is True
    assert result.missing_step == "common"
    assert result.reject_reason_ko == MISSING_STEP_COMMON_KO


# ── 2 stages complete → blocked, missing abc ────────────────
def test_two_stages_complete_blocks_missing_abc() -> None:
    result = check_partial_close_attempt(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.blocked is True
    assert result.missing_step == "abc"
    assert result.reject_reason_ko == MISSING_STEP_ABC_KO


# ── 1 stage complete → blocked, missing manufacturing ───────
def test_one_stage_complete_blocks_missing_manufacturing() -> None:
    result = check_partial_close_attempt(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.blocked is True
    assert result.missing_step == "manufacturing"
    assert result.reject_reason_ko == MISSING_STEP_MANUFACTURING_KO


# ── 0 stages complete → blocked, missing divisions ──────────
def test_zero_stages_complete_blocks_missing_divisions() -> None:
    result = check_partial_close_attempt(
        divisions_completed_at=None,
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.blocked is True
    assert result.missing_step == "divisions"
    assert result.reject_reason_ko == MISSING_STEP_DIVISIONS_KO


# ── Chronological violation ─────────────────────────────────
def test_chronological_violation_blocks_with_violation_message() -> None:
    """Reverse-chronological timestamps produce blocked verdict."""
    result = check_partial_close_attempt(
        divisions_completed_at=_ts(20),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.blocked is True
    # Either forward-jump or chronological-violation message;
    # close_sequence_order detects both — the first missing step wins.
    assert result.reject_reason_ko is not None


# ── Forward-jump (skipping stage) ───────────────────────────
def test_forward_jump_blocks_missing_intermediate_stage() -> None:
    """abc populated but manufacturing NULL → forward-jump blocked."""
    result = check_partial_close_attempt(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=None,
        abc_completed_at=_ts(20),
        common_completed_at=None,
    )
    assert result.blocked is True
    assert result.missing_step == "manufacturing"
    assert result.reject_reason_ko == MISSING_STEP_MANUFACTURING_KO


# ── Korean SSOT verbatim ───────────────────────────────────
def test_reject_reason_ko_uses_korean_specific_messages() -> None:
    """Each missing step has its own Korean message."""
    assert (
        check_partial_close_attempt(
            divisions_completed_at=None,
            manufacturing_completed_at=None,
            abc_completed_at=None,
            common_completed_at=None,
        ).reject_reason_ko
        == MISSING_STEP_DIVISIONS_KO
    )
    assert (
        check_partial_close_attempt(
            divisions_completed_at=_ts(0),
            manufacturing_completed_at=None,
            abc_completed_at=None,
            common_completed_at=None,
        ).reject_reason_ko
        == MISSING_STEP_MANUFACTURING_KO
    )


# ── Idempotency ─────────────────────────────────────────────
def test_repeated_calls_return_same_verdict() -> None:
    args = {
        "divisions_completed_at": _ts(0),
        "manufacturing_completed_at": _ts(10),
        "abc_completed_at": None,
        "common_completed_at": None,
    }
    first = check_partial_close_attempt(**args)
    second = check_partial_close_attempt(**args)
    assert first == second


# ── Pure-kernel error class surface ────────────────────────
def test_partial_close_guard_error_class() -> None:
    err = PartialCloseGuardError(
        message="test",
        error_code=ERROR_CODE_PARTIAL_CLOSE,
        missing_step="common",
    )
    assert err.error_code == "PARTIAL_CLOSE_BLOCKED"
    assert err.missing_step == "common"
