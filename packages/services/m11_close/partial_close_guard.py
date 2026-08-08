"""packages.services.m11_close.partial_close_guard — Story 11.2 pure kernel.

AD-6 close lock PRIMARY guard. Rejects partial close attempts
(PRD §F11.1 + §8.M11(a) "부분 마감을 허용하지 않는다").

confirm_close_sequence can only succeed when ALL 4 stages
(divisions + manufacturing + abc + common) are complete.

Per AD-1 / AD-11: pure-Python, stdlib-only, NO DB, NO clock, NO random.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-close-sequence.ts`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final, NamedTuple

from packages.services.m11_close.close_sequence_order import (
    CHRONOLOGICAL_VIOLATION_KO,
    validate_close_sequence_order,
)

# ── Constants ────────────────────────────────────────────────
PARTIAL_CLOSE_BLOCKED_KO: Final[str] = "부분 마감은 허용되지 않습니다"
MISSING_STEP_DIVISIONS_KO: Final[str] = "divisions 단계 미완료"
MISSING_STEP_MANUFACTURING_KO: Final[str] = "manufacturing 단계 미완료"
MISSING_STEP_ABC_KO: Final[str] = "abc 단계 미완료"
MISSING_STEP_COMMON_KO: Final[str] = "common 단계 미완료"

_STAGE_KO_MAP: Final[dict[str, str]] = {
    "divisions": MISSING_STEP_DIVISIONS_KO,
    "manufacturing": MISSING_STEP_MANUFACTURING_KO,
    "abc": MISSING_STEP_ABC_KO,
    "common": MISSING_STEP_COMMON_KO,
}

# Error codes — pure-kernel domain semantics.
ERROR_CODE_PARTIAL_CLOSE: Final[str] = "PARTIAL_CLOSE_BLOCKED"
ERROR_CODE_CHRONOLOGICAL: Final[str] = "STAGE_NOT_CHRONOLOGICAL"


# ── Typed exception ──────────────────────────────────────────
class PartialCloseGuardError(Exception):
    """Pure-kernel partial-close guard violation.

    Distinct from service-layer `PartialCloseBlockedError`. NO HTTP
    mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_PARTIAL_CLOSE,
        missing_step: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.missing_step = missing_step


# ── PartialCloseGuardResult NamedTuple ───────────────────────
class PartialCloseGuardResult(NamedTuple):
    """Guard verdict — service layer wraps this in the wire response.

    `blocked=True` ⇒ caller MUST NOT call confirm_close_sequence.
    `missing_step` = first incomplete stage name (or None when blocked
    is False).
    """

    blocked: bool
    missing_step: str | None
    reject_reason_ko: str | None


# ── check_partial_close_attempt ──────────────────────────────
def check_partial_close_attempt(
    *,
    divisions_completed_at: datetime | None,
    manufacturing_completed_at: datetime | None,
    abc_completed_at: datetime | None,
    common_completed_at: datetime | None,
) -> PartialCloseGuardResult:
    """Decide whether a confirm_close_sequence call is permitted.

    Rejects when:
        - Any of the 4 step timestamps is NULL (partial close).
        - Step timestamps violate chronological ordering (defense-
          in-depth against forward-jumps).

    Returns:
        PartialCloseGuardResult with `blocked` flag + `missing_step`
        + `reject_reason_ko` (Korean SSOT).

    Raises:
        PartialCloseGuardError: only when type errors occur (caller bug).
    """
    # Delegate to close_sequence_order for chronological validation.
    order_result = validate_close_sequence_order(
        divisions_completed_at=divisions_completed_at,
        manufacturing_completed_at=manufacturing_completed_at,
        abc_completed_at=abc_completed_at,
        common_completed_at=common_completed_at,
    )

    if not order_result.valid:
        # Chronological violations and missing-stage violations both
        # produce a blocked result. Missing step takes precedence for
        # the wire response (which stage the UI should highlight).
        missing = order_result.next_step
        if missing is None or missing == "confirmed":
            # All stages populated but chronological violated (the
            # for-else branch above only assigns 'confirmed' when no
            # break occurred, so if valid=False we know a violation
            # was detected before the loop completed).
            return PartialCloseGuardResult(
                blocked=True,
                missing_step=None,
                reject_reason_ko=CHRONOLOGICAL_VIOLATION_KO,
            )
        reason_ko = _STAGE_KO_MAP.get(missing, missing)
        return PartialCloseGuardResult(
            blocked=True,
            missing_step=missing,
            reject_reason_ko=reason_ko,
        )

    # Order is valid but partial close is still blocked until all 4
    # stages are complete (next_step != 'confirmed').
    if order_result.next_step != "confirmed":
        missing = order_result.next_step
        reason_ko = _STAGE_KO_MAP.get(missing, missing)
        return PartialCloseGuardResult(
            blocked=True,
            missing_step=missing,
            reject_reason_ko=reason_ko,
        )

    return PartialCloseGuardResult(
        blocked=False,
        missing_step=None,
        reject_reason_ko=None,
    )


__all__ = [
    "ERROR_CODE_CHRONOLOGICAL",
    "ERROR_CODE_PARTIAL_CLOSE",
    "MISSING_STEP_ABC_KO",
    "MISSING_STEP_COMMON_KO",
    "MISSING_STEP_DIVISIONS_KO",
    "MISSING_STEP_MANUFACTURING_KO",
    "PARTIAL_CLOSE_BLOCKED_KO",
    "PartialCloseGuardError",
    "PartialCloseGuardResult",
    "check_partial_close_attempt",
]
