"""apps.api.core.confidence — REVIEW_THRESHOLD + badge mapping (Story 1.3 — Task 1.1).

This module is the **single source of truth** for whether an AI-extracted
field requires human review. Both the API service layer (when building
the draft response payload) and the TypeScript mirror (when rendering the
badge in the wizard) read from these constants.

Why a separate module:
- The 0.70 cutoff is **a heuristic, not a calibrated probability**. The model
  self-rates confidence 0.00-1.00 and we treat anything below threshold as
  "review_required". This is documented in `docs/ai-document-extraction.md`
  §"Confidence semantics" so users understand "✓ 자동 입력" means "model
  rated itself ≥70% confident", NOT "verified by an independent oracle".
- Decimals, not floats: matches AD-8 cross-language parity (Decimal is the
  Python truth source; TS mirrors with a fixed-precision number per AD-15).
  Float 0.7 is actually 0.7000000000000001 — comparing confidence scores
  with `< 0.7` against float inputs would produce 0.6999999... → True.

Cross-language parity:
- This module is the Python truth source for `tests/integration/test_badge_consistency.py`.
- The TypeScript mirror lives in `apps/web/lib/confidence.ts` (Story 1.3
  Task 4) and MUST keep `REVIEW_THRESHOLD = 0.70` and the same badge strings.

Anti-pattern guards:
- Do NOT scatter `0.70` or `0.7` elsewhere. Search the codebase before
  adding a new comparison.
- Do NOT split the boolean `is_review_required` and the badge string into
  separate fields — they are derived from the same condition. The single
  source lives here.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Final

# AD-8 / AD-15 — Decimal is the canonical money-adjacent numeric type.
# Locked to Decimal("0.70") exactly. Use this constant in every comparison;
# do NOT inline `Decimal("0.70")` or `0.70` elsewhere.
REVIEW_THRESHOLD: Final[Decimal] = Decimal("0.70")


# ── Badge enum + string constants (API contract) ──────────────
class Badge(str, Enum):
    """Canonical badge strings returned by the M10 review/draft endpoints.

    The frontend renders one of two badge styles:
    - `REVIEW_REQUIRED` → red ⚠ 확인 필요 (low confidence / NULL)
    - `AUTO_INPUT`      → gray ✓ 자동 입력 (≥ threshold)

    Both the badge string and the boolean `is_review_required(confidence)`
    are derived from the same condition in `is_review_required()` and
    `badge_for()`. Single source of truth — no duplicate boolean field on
    the wire (Story 1.3 spec §3.2 / C8 resolution).
    """

    REVIEW_REQUIRED = "review_required"
    AUTO_INPUT = "auto_input"


# Exposed as module-level constants so other modules can import them
# directly without going through the enum (e.g. f-string formatting).
BADGE_REVIEW_REQUIRED: Final[str] = Badge.REVIEW_REQUIRED.value
BADGE_AUTO_INPUT: Final[str] = Badge.AUTO_INPUT.value


# ── Pure helpers ──────────────────────────────────────────────
def is_review_required(confidence: Decimal | float | int | None) -> bool:
    """Decide whether an AI-extracted field needs human review.

    The decision rule is:
        confidence IS NULL OR confidence < REVIEW_THRESHOLD → review_required

    Args:
        confidence: A value in `[0, 1]` (Decimal preferred — AD-8 parity),
            or None for "model returned no score". Float/int inputs are
            coerced to Decimal so callers from the JSON deserialization
            path get the same answer.

    Returns:
        True iff the field is sub-threshold or unscored and must be
        surfaced to the user for explicit confirmation.

    Raises:
        ValueError: When `confidence` is outside `[0, 1]`. The caller
            (extraction service) treats this as "malformed provider output"
            and records `confidence = NULL` on the draft row (which then
            classifies as review_required via this helper).
    """
    if confidence is None:
        return True
    if isinstance(confidence, int | float):
        confidence = Decimal(str(confidence))
    if not isinstance(confidence, Decimal):
        # Pydantic / numpy / other — be strict, do not coerce silently.
        raise ValueError(
            f"confidence must be Decimal, float, int, or None — got {type(confidence).__name__}"
        )
    if confidence < Decimal("0") or confidence > Decimal("1"):
        raise ValueError(
            f"confidence must be in [0, 1] — got {confidence!s}"
        )
    return confidence < REVIEW_THRESHOLD


def badge_for(confidence: Decimal | float | int | None) -> Badge:
    """Return the canonical Badge for a given confidence value.

    Convenience wrapper over `is_review_required()`. The badge string is
    returned in the API response (AD-15 §4 contract) and mirrored in the
    TS badge component (Story 1.3 Task 4.3).

    Single source of truth: this function NEVER inspects confidence
    independently of `is_review_required()`. If you change the threshold
    or the rule, change it in one place.
    """
    if is_review_required(confidence):
        return Badge.REVIEW_REQUIRED
    return Badge.AUTO_INPUT
