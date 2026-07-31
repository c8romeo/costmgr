"""tests.api.test_confidence — REVIEW_THRESHOLD boundary tests (Story 1.3 — Task 1.1).

Single-source-of-truth: `apps/api/core/confidence.py::REVIEW_THRESHOLD` is the
ONLY place that decides whether an AI-extracted field requires human review.

The 0.70 cutoff is a **heuristic**, not a calibrated probability — the model
self-rates confidence 0.00-1.00 and we treat anything below threshold as
"review_required". Document this caveat in `docs/ai-document-extraction.md`
§"Confidence semantics".

Boundary table (AC #5.1):
- 0.00     → review_required (red ⚠ 확인 필요)
- 0.49     → review_required
- 0.50     → review_required (still below threshold)
- 0.69     → review_required (last sub-threshold value)
- 0.70     → auto_input (gray ✓ 자동 입력 — first value at or above threshold)
- 0.999    → auto_input
- 1.00     → auto_input
- None     → review_required (missing confidence is NEVER auto-approved)

Also tested:
- `badge_for()` mirrors `is_review_required()` — single source of truth.
- `REVIEW_THRESHOLD` is `Decimal("0.70")` exactly (not float 0.7).
- `Badge` enum exposes the two canonical values.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.api.core.confidence import (
    BADGE_AUTO_INPUT,
    BADGE_REVIEW_REQUIRED,
    REVIEW_THRESHOLD,
    Badge,
    badge_for,
    is_review_required,
)


# ── Threshold constant is locked ─────────────────────────────
def test_review_threshold_exact_decimal() -> None:
    """REVIEW_THRESHOLD is Decimal("0.70") — not float, not string."""
    assert REVIEW_THRESHOLD == Decimal("0.70")
    assert isinstance(REVIEW_THRESHOLD, Decimal)


def test_review_threshold_is_less_than_one() -> None:
    """Sanity guard: threshold must be strictly less than 1.0 so 1.0 is auto."""
    assert REVIEW_THRESHOLD < Decimal("1.0")


def test_review_threshold_is_strictly_positive() -> None:
    """Sanity guard: threshold must be > 0 so 0.0 is review_required."""
    assert REVIEW_THRESHOLD > Decimal("0")


# ── is_review_required — boundary table ──────────────────────
@pytest.mark.parametrize(
    "confidence,expected",
    [
        # Sub-threshold values — review required.
        (Decimal("0.00"), True),
        (Decimal("0.49"), True),
        (Decimal("0.50"), True),  # still below 0.70
        (Decimal("0.69"), True),  # last value strictly below threshold
        # At-or-above threshold values — auto input.
        (Decimal("0.70"), False),  # boundary: exactly the threshold
        (Decimal("0.71"), False),
        (Decimal("0.999"), False),
        (Decimal("1.00"), False),
    ],
)
def test_is_review_required_boundary_table(
    confidence: Decimal, expected: bool
) -> None:
    """0.69 → True, 0.70 → False. The boundary is inclusive at threshold.

    Implemented as `confidence < REVIEW_THRESHOLD` so the threshold itself
    is the first value that passes. This matches the AC: ">=70% → ✓ 자동 입력".
    """
    assert is_review_required(confidence) is expected


def test_is_review_required_none_is_true() -> None:
    """Missing confidence (model returned no value) is ALWAYS review_required.

    Per spec Task 1.2: `confidence IS NULL OR confidence < REVIEW_THRESHOLD`
    maps to `review_required`. A NULL field cannot be auto-approved even if
    the model "forgot" to score it.
    """
    assert is_review_required(None) is True


def test_is_review_required_accepts_float_and_decimal() -> None:
    """The helper accepts float for convenience (UI/JSON path).

    Decimal is preferred internally (AD-8 cross-language parity), but the
    helper coerces to Decimal so float callers (JSON deserialization, web
    form values) get the same answer.
    """
    # 0.69 as float → just below threshold → True.
    assert is_review_required(0.69) is True
    # 0.70 as float → at threshold → False.
    assert is_review_required(0.70) is False
    # 0.50 as float → below → True.
    assert is_review_required(0.50) is True


def test_is_review_required_out_of_range_rejected() -> None:
    """Values outside [0, 1] raise ValueError (fail-closed).

    The model is supposed to self-rate 0.00-1.00. Anything outside that range
    means the response is malformed and should NOT be auto-classified.
    Captured by the extraction service which records confidence=NULL and
    surfaces the field as review_required.
    """
    with pytest.raises(ValueError, match="confidence"):
        is_review_required(Decimal("1.01"))
    with pytest.raises(ValueError, match="confidence"):
        is_review_required(Decimal("-0.01"))


# ── badge_for — mirrors is_review_required ───────────────────
def test_badge_for_review_required() -> None:
    """Sub-threshold or NULL → Badge.REVIEW_REQUIRED (red ⚠ 확인 필요)."""
    assert badge_for(Decimal("0.50")) is Badge.REVIEW_REQUIRED
    assert badge_for(Decimal("0.00")) is Badge.REVIEW_REQUIRED
    assert badge_for(Decimal("0.699")) is Badge.REVIEW_REQUIRED
    assert badge_for(None) is Badge.REVIEW_REQUIRED


def test_badge_for_auto_input() -> None:
    """At or above threshold → Badge.AUTO_INPUT (gray ✓ 자동 입력)."""
    assert badge_for(Decimal("0.70")) is Badge.AUTO_INPUT
    assert badge_for(Decimal("0.95")) is Badge.AUTO_INPUT
    assert badge_for(Decimal("1.00")) is Badge.AUTO_INPUT


def test_badge_string_values_are_stable_contract() -> None:
    """The badge string constants are part of the API contract (AD-15 §4).

    Frontend TypeScript mirrors these via the integration parity test.
    Renaming them is a breaking change for the JSON contract.
    """
    assert BADGE_REVIEW_REQUIRED == "review_required"
    assert BADGE_AUTO_INPUT == "auto_input"
    assert Badge.REVIEW_REQUIRED.value == "review_required"
    assert Badge.AUTO_INPUT.value == "auto_input"


def test_badge_string_consistency_for_all_inputs() -> None:
    """Every (confidence, is_review_required) pair maps to matching badge strings.

    Single-source-of-truth invariant — the badge string and the boolean
    review_required must NEVER diverge for the same input.
    """
    samples = [
        Decimal("0.00"),
        Decimal("0.50"),
        Decimal("0.69"),
        Decimal("0.70"),
        Decimal("0.95"),
        Decimal("1.00"),
        None,
    ]
    for conf in samples:
        review_required = is_review_required(conf)
        badge = badge_for(conf)
        if review_required:
            assert badge is Badge.REVIEW_REQUIRED
        else:
            assert badge is Badge.AUTO_INPUT