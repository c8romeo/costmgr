"""tests.services.m11_close.test_close_sequence_order — Story 11.2 pure kernel #1.

~20 tests covering:
- 4-stage ordering all 4 progress patterns (0/1/2/3/4 steps complete)
- chronological ordering validation (forward-jump detection)
- next_step transition through all 4 stages + confirmed
- violation cases + Korean SSOT constants
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from packages.services.m11_close.close_sequence_order import (
    ABC_MISSING_KO,
    ALL_STAGES_REQUIRED_KO,
    CHRONOLOGICAL_VIOLATION_KO,
    CLOSE_SEQUENCE_STAGES,
    COMMON_MISSING_KO,
    CloseSequenceOrderError,
    DIVISIONS_MISSING_KO,
    MANUFACTURING_MISSING_KO,
    STEP_TIMESTAMP_ATTRS,
    validate_close_sequence_order,
)


_BASE_TS = datetime(2026, 8, 1, 0, 0, 0)


def _ts(offset_minutes: int = 0) -> datetime:
    return _BASE_TS + timedelta(minutes=offset_minutes)


# ── Module surface ──────────────────────────────────────────
def test_module_exports_close_sequence_stages_constant() -> None:
    assert CLOSE_SEQUENCE_STAGES == (
        "divisions",
        "manufacturing",
        "abc",
        "common",
        "confirmed",
    )


def test_module_exports_step_timestamp_attrs_constant() -> None:
    assert STEP_TIMESTAMP_ATTRS == (
        "divisions_completed_at",
        "manufacturing_completed_at",
        "abc_completed_at",
        "common_completed_at",
    )


# ── Korean SSOT constants verbatim ──────────────────────────
def test_korean_constants_divisions_missing() -> None:
    assert DIVISIONS_MISSING_KO == "divisions 단계 미완료"


def test_korean_constants_manufacturing_missing() -> None:
    assert MANUFACTURING_MISSING_KO == "manufacturing 단계 미완료"


def test_korean_constants_abc_missing() -> None:
    assert ABC_MISSING_KO == "abc 단계 미완료"


def test_korean_constants_common_missing() -> None:
    assert COMMON_MISSING_KO == "common 단계 미완료"


def test_korean_constants_all_stages_required() -> None:
    assert ALL_STAGES_REQUIRED_KO == "4단계 모두 완료 후 마감 가능"


def test_korean_constants_chronological_violation() -> None:
    assert CHRONOLOGICAL_VIOLATION_KO == "단계 완료 시각이 순서대로여야 합니다"


# ── 0 stages complete (initial state) ──────────────────────
def test_zero_steps_complete_is_valid_with_next_divisions() -> None:
    result = validate_close_sequence_order(
        divisions_completed_at=None,
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.valid is True
    assert result.violations == ()
    assert result.next_step == "divisions"
    assert result.reject_reason_ko is None


# ── 1 stage complete ────────────────────────────────────────
def test_one_step_divisions_complete_advances_to_manufacturing() -> None:
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.valid is True
    assert result.next_step == "manufacturing"


# ── 2 stages complete ───────────────────────────────────────
def test_two_steps_complete_advances_to_abc() -> None:
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.valid is True
    assert result.next_step == "abc"


# ── 3 stages complete ───────────────────────────────────────
def test_three_steps_complete_advances_to_common() -> None:
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=None,
    )
    assert result.valid is True
    assert result.next_step == "common"


# ── 4 stages complete ───────────────────────────────────────
def test_four_steps_complete_reaches_confirmed() -> None:
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=_ts(20),
        common_completed_at=_ts(30),
    )
    assert result.valid is True
    assert result.next_step == "confirmed"


# ── Forward-jump detection (defense-in-depth) ───────────────
def test_forward_jump_manufacturing_without_divisions_violation() -> None:
    """manufacturing populated, divisions NULL → violation."""
    result = validate_close_sequence_order(
        divisions_completed_at=None,
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.valid is False
    assert any("divisions" in v for v in result.violations)
    assert result.next_step == "divisions"


def test_forward_jump_abc_without_manufacturing_violation() -> None:
    """abc populated, manufacturing NULL → violation."""
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=None,
        abc_completed_at=_ts(20),
        common_completed_at=None,
    )
    assert result.valid is False
    assert any("manufacturing" in v for v in result.violations)


def test_forward_jump_common_without_abc_violation() -> None:
    """common populated, abc NULL → violation."""
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=_ts(30),
    )
    assert result.valid is False
    assert any("abc" in v for v in result.violations)


# ── Chronological violation ─────────────────────────────────
def test_chronological_violation_reversed_timestamps() -> None:
    """manufacturing earlier than divisions → chronological violation."""
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(20),
        manufacturing_completed_at=_ts(10),
        abc_completed_at=None,
        common_completed_at=None,
    )
    assert result.valid is False
    assert CHRONOLOGICAL_VIOLATION_KO in result.violations


def test_chronological_violation_abc_before_manufacturing() -> None:
    result = validate_close_sequence_order(
        divisions_completed_at=_ts(0),
        manufacturing_completed_at=_ts(20),
        abc_completed_at=_ts(10),
        common_completed_at=None,
    )
    assert result.valid is False
    assert CHRONOLOGICAL_VIOLATION_KO in result.violations


# ── Equal timestamps allowed (non-decreasing) ──────────────
def test_equal_timestamps_chronologically_valid() -> None:
    """Same instant is allowed (race-condition guard)."""
    same = _ts(0)
    result = validate_close_sequence_order(
        divisions_completed_at=same,
        manufacturing_completed_at=same,
        abc_completed_at=same,
        common_completed_at=None,
    )
    assert result.valid is True


# ── Type error ──────────────────────────────────────────────
def test_invalid_timestamp_type_raises_error() -> None:
    with pytest.raises(CloseSequenceOrderError) as exc_info:
        validate_close_sequence_order(
            divisions_completed_at="not-a-datetime",  # type: ignore[arg-type]
            manufacturing_completed_at=None,
            abc_completed_at=None,
            common_completed_at=None,
        )
    assert exc_info.value.error_code == "UNKNOWN_STAGE_NAME"


# ── next_step always returned ──────────────────────────────
def test_next_step_returned_for_all_invalid_cases() -> None:
    """Even with multiple violations, next_step is set."""
    result = validate_close_sequence_order(
        divisions_completed_at=None,
        manufacturing_completed_at=None,
        abc_completed_at=None,
        common_completed_at=_ts(30),
    )
    assert result.valid is False
    assert result.next_step == "divisions"