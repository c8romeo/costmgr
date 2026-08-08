"""packages.services.m11_close.close_sequence_order — Story 11.2 pure kernel.

AD-6 close lock PRIMARY guard. Validates the 4-stage close sequence
order (PRD §F11.1 + §8.M11(a)):

    divisions → manufacturing → abc → common → confirmed

The sequence is 1-way; each step's completion timestamp must be
chronologically ordered (or NULL). Defense-in-depth against
stage-skipping — service layer enforces this for direct SQL writes too.

Per AD-1 / AD-11: pure-Python, stdlib-only, NO DB, NO clock, NO random.
Service layer passes all timestamps explicitly.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-close-sequence.ts`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# Close sequence stages in canonical order. PRD §F11.1.
CLOSE_SEQUENCE_STAGES: Final[tuple[str, ...]] = (
    "divisions",
    "manufacturing",
    "abc",
    "common",
    "confirmed",
)
# Step timestamp columns paired 1:1 with stages[0..3].
# 'confirmed' is reached when ALL four step timestamps are populated
# AND fiscal_periods.status='closed'.
STEP_TIMESTAMP_ATTRS: Final[tuple[str, ...]] = (
    "divisions_completed_at",
    "manufacturing_completed_at",
    "abc_completed_at",
    "common_completed_at",
)

# Error codes — pure-kernel domain semantics.
ERROR_CODE_NON_CHRONOLOGICAL: Final[str] = "STAGE_NOT_CHRONOLOGICAL"
ERROR_CODE_UNKNOWN_STAGE: Final[str] = "UNKNOWN_STAGE_NAME"

# Korean constants — AD-15 §11 SSOT.
DIVISIONS_MISSING_KO: Final[str] = "divisions 단계 미완료"
MANUFACTURING_MISSING_KO: Final[str] = "manufacturing 단계 미완료"
ABC_MISSING_KO: Final[str] = "abc 단계 미완료"
COMMON_MISSING_KO: Final[str] = "common 단계 미완료"
ALL_STAGES_REQUIRED_KO: Final[str] = "4단계 모두 완료 후 마감 가능"
CHRONOLOGICAL_VIOLATION_KO: Final[str] = "단계 완료 시각이 순서대로여야 합니다"


# ── Typed exception ──────────────────────────────────────────
class CloseSequenceOrderError(Exception):
    """Pure-kernel ordering violation.

    Distinct from service-layer `CloseSequenceStepMismatchError`. NO HTTP
    mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_NON_CHRONOLOGICAL,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ── CloseSequenceOrderResult NamedTuple ──────────────────────
class CloseSequenceOrderResult(NamedTuple):
    """Ordering verdict — service layer wraps this in the wire response."""

    valid: bool
    violations: tuple[str, ...]
    next_step: str | None  # first incomplete stage (or 'confirmed')
    reject_reason_ko: str | None


# ── validate_close_sequence_order ────────────────────────────
def validate_close_sequence_order(
    *,
    divisions_completed_at: datetime | None,
    manufacturing_completed_at: datetime | None,
    abc_completed_at: datetime | None,
    common_completed_at: datetime | None,
) -> CloseSequenceOrderResult:
    """Validate the 4-stage close sequence order.

    Rules (PRD §F11.1):
        - Stages are 1-way: divisions → manufacturing → abc → common.
        - Each stage's completion timestamp must be populated if the
          next stage's timestamp is populated (no forward jumps).
        - Completion timestamps must be chronologically non-decreasing
          when both are populated (manufacturing > divisions, abc >
          manufacturing, common > abc).
        - `next_step` = first stage whose completion timestamp is NULL,
          or `'confirmed'` if all 4 are populated.

    Returns:
        CloseSequenceOrderResult with `valid` flag + `violations` tuple
        (Korean SSOT messages) + `next_step` + `reject_reason_ko`.

    Raises:
        CloseSequenceOrderError: on internal type errors. These
            represent caller bugs and should not normally surface at
            runtime.
    """
    timestamps: tuple[tuple[str, datetime | None], ...] = (
        ("divisions", divisions_completed_at),
        ("manufacturing", manufacturing_completed_at),
        ("abc", abc_completed_at),
        ("common", common_completed_at),
    )
    for stage_name, ts in timestamps:
        if ts is not None and not isinstance(ts, datetime):
            raise CloseSequenceOrderError(
                message=(
                    f"{stage_name}_completed_at must be datetime or None, "
                    f"got {type(ts).__name__!r}"
                ),
                error_code=ERROR_CODE_UNKNOWN_STAGE,
            )

    violations: list[str] = []
    # Rule 1: forward-jump detection (chronological ordering).
    for i in range(len(timestamps) - 1):
        prev_name, prev_ts = timestamps[i]
        curr_name, curr_ts = timestamps[i + 1]
        if prev_ts is None and curr_ts is not None:
            violations.append(f"{prev_name} 단계 미완료")
        elif prev_ts is not None and curr_ts is not None and curr_ts < prev_ts:
            violations.append(CHRONOLOGICAL_VIOLATION_KO)

    # Rule 2: next_step = first incomplete stage.
    next_step: str | None = None
    for stage_name, ts in timestamps:
        if ts is None:
            next_step = stage_name
            break
    else:
        # All four stages complete → confirm flow proceeds.
        next_step = "confirmed"

    if violations:
        return CloseSequenceOrderResult(
            valid=False,
            violations=tuple(violations),
            next_step=next_step,
            reject_reason_ko=ALL_STAGES_REQUIRED_KO,
        )

    return CloseSequenceOrderResult(
        valid=True,
        violations=(),
        next_step=next_step,
        reject_reason_ko=None,
    )


__all__ = [
    "ABC_MISSING_KO",
    "ALL_STAGES_REQUIRED_KO",
    "CHRONOLOGICAL_VIOLATION_KO",
    "CLOSE_SEQUENCE_STAGES",
    "COMMON_MISSING_KO",
    "CloseSequenceOrderError",
    "CloseSequenceOrderResult",
    "DIVISIONS_MISSING_KO",
    "ERROR_CODE_NON_CHRONOLOGICAL",
    "ERROR_CODE_UNKNOWN_STAGE",
    "MANUFACTURING_MISSING_KO",
    "STEP_TIMESTAMP_ATTRS",
    "validate_close_sequence_order",
]
