"""tests.services.test_settings_completion — pure-function tests for SettingsCompletion.

Story 1.2 — Task 2.3.

Pure Python tests (no DB, no async). Verifies the `compute_completion()`
domain function against the spec scenarios:
- empty → missing=4
- partial fiscal year → missing=3
- manufacturing skips drivers
- service requires drivers
- ③ / ④ require all three
"""

from __future__ import annotations

import pytest

from packages.services.m0_onboarding import settings_completion as sc
from packages.services.m0_onboarding.industry_menu import Industry


def test_completion_all_empty_returns_six_missing_fields() -> None:
    """Industry=None, no onboarding, no counts → only top-level fields missing.

    With industry=None the drivers requirement is True by default
    (`_DRIVERS_REQUIRED` fallback), so missing lists 6 items when
    allocation_criteria is also empty.
    """
    result = sc.compute_completion(None, {}, {})

    assert result.fiscal_year_start.completed is False
    assert result.currency.completed is False
    assert result.language.completed is False
    assert result.direct_indirect.completed is False
    assert result.fixed_variable.completed is False
    assert result.drivers_required is True  # industry=None defaults to required
    assert result.drivers.completed is False
    assert result.is_complete is False
    # 4 top-level fields + 2 criteria (direct_indirect + fixed_variable).
    # Drivers is NOT in missing because it isn't required when industry=None?
    # Actually with drivers_required=True, drivers IS in missing.
    assert sc.LABEL_FISCAL_YEAR_START in result.missing
    assert sc.LABEL_CURRENCY in result.missing
    assert sc.LABEL_LANGUAGE in result.missing
    assert sc.LABEL_DIRECT_INDIRECT in result.missing
    assert sc.LABEL_FIXED_VARIABLE in result.missing


def test_completion_fiscal_year_set_drops_one_missing() -> None:
    """A1 fiscal_year_start set → 5 remaining (industry=None, no criteria)."""
    result = sc.compute_completion(
        None,
        {"fiscal_year_start": "2026-01"},
        {},
    )

    assert result.fiscal_year_start.completed is True
    assert sc.LABEL_FISCAL_YEAR_START not in result.missing
    assert sc.LABEL_CURRENCY in result.missing


def test_completion_all_top_level_set_only_criteria_missing() -> None:
    """All top-level fields set, no criteria → missing=[direct_indirect, fixed_variable]."""
    result = sc.compute_completion(
        None,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {},
    )

    assert result.fiscal_year_start.completed is True
    assert result.currency.completed is True
    assert result.language.completed is True
    assert result.direct_indirect.completed is False
    assert result.fixed_variable.completed is False
    assert result.is_complete is False
    # drivers is required when industry=None, so it appears.
    assert sc.LABEL_DIRECT_INDIRECT in result.missing
    assert sc.LABEL_FIXED_VARIABLE in result.missing
    assert sc.LABEL_DRIVERS in result.missing


def test_completion_manufacturing_skips_drivers() -> None:
    """PRD §8.M0(b): manufacturing industry skips drivers (no ABC engine)."""
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 0},
    )

    assert result.drivers_required is False
    assert result.drivers.completed is True  # auto-completed for manufacturing
    assert sc.LABEL_DRIVERS not in result.missing
    assert result.is_complete is True


def test_completion_service_requires_drivers() -> None:
    """Service industry needs drivers even when 0 rows are registered."""
    result = sc.compute_completion(
        Industry.SERVICE,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 0},
    )

    assert result.drivers_required is True
    assert result.drivers.completed is False
    assert sc.LABEL_DRIVERS in result.missing
    assert result.is_complete is False


def test_completion_manufacturing_service_full_set() -> None:
    """③ manufacturing_service — all 4 + 3 criteria ≥1 → complete."""
    result = sc.compute_completion(
        Industry.MANUFACTURING_SERVICE,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 3},
    )

    assert result.drivers_required is True
    assert result.is_complete is True
    assert result.missing == []


def test_completion_manufacturing_service_other_full_set() -> None:
    """④ manufacturing_service_other — same as ③ for completion purposes."""
    result = sc.compute_completion(
        Industry.MANUFACTURING_SERVICE_OTHER,
        {
            "fiscal_year_start": "2026-01",
            "currency": "USD",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 5, "drivers": 3},
    )

    assert result.is_complete is True


def test_completion_allocation_criteria_partial() -> None:
    """AC #3 — direct_indirect set, fixed_variable + drivers missing."""
    result = sc.compute_completion(
        Industry.SERVICE,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 5, "fixed_variable": 0, "drivers": 0},
    )

    assert result.direct_indirect.completed is True
    assert result.fixed_variable.completed is False
    assert result.drivers.completed is False
    assert result.is_complete is False
    assert sc.LABEL_FIXED_VARIABLE in result.missing
    assert sc.LABEL_DRIVERS in result.missing
    assert sc.LABEL_DIRECT_INDIRECT not in result.missing


def test_completion_count_zero_does_not_complete() -> None:
    """Spec AC: `count ≥ 1` to be complete. Count=0 stays incomplete."""
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {
            "fiscal_year_start": "2026-01",
            "currency": "KRW",
            "language": "ko-KR",
        },
        {"direct_indirect": 1, "fixed_variable": 1, "drivers": 0},
    )

    # Manufacturing skips drivers → completed regardless.
    assert result.is_complete is True


def test_completion_handles_none_inputs() -> None:
    """Defensive: None inputs treated as {}."""
    result = sc.compute_completion(None, None, None)

    assert result.is_complete is False
    assert result.fiscal_year_start.completed is False
    assert result.direct_indirect.completed is False


def test_completion_missing_reason_precise() -> None:
    """missing_reason field carries precise Korean copy for the API detail."""
    result = sc.compute_completion(None, {}, {"drivers": 0})

    assert result.fiscal_year_start.missing_reason == "회계연도 시작월 미입력"
    assert result.currency.missing_reason == "통화 미선택"
    assert result.language.missing_reason == "언어 미선택"
    assert result.direct_indirect.missing_reason == "직접/간접 계정 분류 0행"


@pytest.mark.parametrize(
    "industry,drivers_required",
    [
        (Industry.MANUFACTURING, False),
        (Industry.SERVICE, True),
        (Industry.MANUFACTURING_SERVICE, True),
        (Industry.MANUFACTURING_SERVICE_OTHER, True),
    ],
)
def test_drivers_required_matrix(
    industry: Industry, drivers_required: bool
) -> None:
    """Verify the industry → drivers_required map exhaustively."""
    result = sc.compute_completion(industry, {}, {})
    assert result.drivers_required is drivers_required


def test_canonical_fields_order() -> None:
    """The `missing` list preserves the PRD §8.M0(b) sequence."""
    assert sc.CANONICAL_FIELDS == (
        "fiscal_year_start",
        "currency",
        "language",
        "direct_indirect",
        "fixed_variable",
        "drivers",
    )


# ── F-7: stored-value fields for wizard first-render seeding ──────
def test_value_fields_none_for_empty_tenant() -> None:
    """New tenant — all value fields are None (no defaults invented)."""
    result = sc.compute_completion(None, {}, {})
    assert result.fiscal_year_start_value is None
    assert result.currency_value is None
    assert result.industry is None


def test_fiscal_year_value_surfaces_stored_format() -> None:
    """Stored YYYY-MM round-trips through CompletionStatus unchanged."""
    result = sc.compute_completion(
        Industry.SERVICE,
        {"fiscal_year_start": "2026-03", "currency": "KRW", "language": "ko-KR"},
        {"direct_indirect": 1, "fixed_variable": 1, "drivers": 1},
    )
    assert result.fiscal_year_start_value == "2026-03"


def test_currency_value_rejects_unknown_strings() -> None:
    """An unknown currency value is surfaced as None (defensive)."""
    result = sc.compute_completion(
        None,
        {"currency": "EUR"},
        {},
    )
    assert result.currency_value is None


def test_industry_value_carries_enum_or_none() -> None:
    """Industry passed in as a separate arg → flows through as enum."""
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {},
        {},
    )
    assert result.industry is Industry.MANUFACTURING

    result_none = sc.compute_completion(None, {}, {})
    assert result_none.industry is None


# ── Story 1.3 — pending_extractions parameter (pre-1.3 prerequisite merge) ──


def test_pending_extractions_empty_keeps_full_completion_when_wizard_complete() -> None:
    """pending_extractions=[] (no AI documents uploaded yet) does not block [계산].

    When the tenant has never uploaded a document, there are no drafts.
    The wizard alone decides completion. Regression guard: a tenant who
    skipped AI extraction entirely must still reach is_complete=True.
    """
    full_industry = Industry.SERVICE  # drivers required
    full_settings = {
        "fiscal_year_start": "2026-01",
        "currency": "KRW",
        "language": "ko-KR",
    }
    full_counts = {"direct_indirect": 5, "fixed_variable": 3, "drivers": 2}

    result = sc.compute_completion(
        full_industry,
        full_settings,
        full_counts,
        pending_extractions=[],
    )
    assert result.is_complete is True
    assert result.pending_extractions_count == 0
    assert result.missing == []


def test_pending_extractions_none_treated_as_empty_list() -> None:
    """pending_extractions=None is the default and treated as [].

    Callers that don't know about AI extraction (Story 1.2 code paths,
    backward-compat shims) get the same answer as pending_extractions=[].
    """
    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {"fiscal_year_start": "2026-01", "currency": "KRW", "language": "ko-KR"},
        {"direct_indirect": 3, "fixed_variable": 2},  # manufacturing skips drivers
    )
    assert result.is_complete is True
    assert result.pending_extractions_count == 0


def test_single_review_required_draft_blocks_completion() -> None:
    """One low-confidence AI extraction blocks [계산] even when wizard is full.

    Scenario: tenant has completed the 4-field wizard AND uploaded a PDF
    that the AI extracted with confidence 0.55 (below 0.70 threshold). The
    user has not yet reviewed the "사업자등록번호" field. [계산] must stay
    disabled until the user confirms.
    """
    full_industry = Industry.MANUFACTURING  # drivers skipped
    full_settings = {
        "fiscal_year_start": "2026-01",
        "currency": "KRW",
        "language": "ko-KR",
    }
    full_counts = {"direct_indirect": 3, "fixed_variable": 2}

    pending = [
        sc.DraftSummary(
            field_name="사업자등록번호",
            review_required=True,
            confidence=0.55,
        ),
    ]

    result = sc.compute_completion(
        full_industry,
        full_settings,
        full_counts,
        pending_extractions=pending,
    )

    assert result.is_complete is False
    assert result.pending_extractions_count == 1
    assert "AI 추출 미확정: 사업자등록번호" in result.missing


def test_high_confidence_draft_does_not_block_completion() -> None:
    """A draft with confidence >= 0.70 (auto-review passed) does NOT block.

    The badge helper at the API layer marks the draft as review_required=False
    when confidence >= REVIEW_THRESHOLD. compute_completion trusts that flag
    and does NOT inspect confidence itself (separation of concerns).
    """
    pending = [
        sc.DraftSummary(
            field_name="회사명",
            review_required=False,  # API already decided 0.92 >= 0.70
            confidence=0.92,
        ),
        sc.DraftSummary(
            field_name="대표자명",
            review_required=False,  # 0.81 >= 0.70
            confidence=0.81,
        ),
    ]

    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {"fiscal_year_start": "2026-01", "currency": "KRW", "language": "ko-KR"},
        {"direct_indirect": 3, "fixed_variable": 2},
        pending_extractions=pending,
    )

    assert result.is_complete is True
    assert result.pending_extractions_count == 0
    assert result.missing == []


def test_null_confidence_treated_as_review_required() -> None:
    """A DraftSummary with confidence=None but review_required=True blocks.

    The API layer maps confidence IS NULL → review_required=True. The
    completion function therefore sees review_required=True and blocks.
    """
    pending = [
        sc.DraftSummary(
            field_name="주소",
            review_required=True,
            confidence=None,  # model returned no confidence → review required
        ),
    ]

    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {"fiscal_year_start": "2026-01", "currency": "KRW", "language": "ko-KR"},
        {"direct_indirect": 3, "fixed_variable": 2},
        pending_extractions=pending,
    )

    assert result.is_complete is False
    assert result.pending_extractions_count == 1
    assert "AI 추출 미확정: 주소" in result.missing


def test_multiple_review_required_drafts_all_listed() -> None:
    """Two review-required drafts surface both field names in missing[].

    Tooltip rendering relies on this list to tell the user exactly which
    fields to revisit. Order matches the input list order (stable for
    tooltip deduplication by the UI).
    """
    pending = [
        sc.DraftSummary(field_name="사업자등록번호", review_required=True, confidence=0.50),
        sc.DraftSummary(field_name="대표자명", review_required=True, confidence=0.45),
        sc.DraftSummary(field_name="회사명", review_required=False, confidence=0.88),
    ]

    result = sc.compute_completion(
        Industry.MANUFACTURING,
        {"fiscal_year_start": "2026-01", "currency": "KRW", "language": "ko-KR"},
        {"direct_indirect": 3, "fixed_variable": 2},
        pending_extractions=pending,
    )

    assert result.is_complete is False
    assert result.pending_extractions_count == 2
    # Wizard fields come first (PRD §8.M0(b) order), AI fields appended.
    assert "AI 추출 미확정: 사업자등록번호" in result.missing
    assert "AI 추출 미확정: 대표자명" in result.missing
    assert "AI 추출 미확정: 회사명" not in result.missing  # review_required=False


def test_pending_extractions_appended_after_wizard_missing() -> None:
    """missing[] preserves PRD §8.M0(b) wizard order at the top, then AI fields.

    Regression guard: if wizard fields are still missing AND AI fields are
    review-required, the wizard ones must appear first. The UI tooltip
    relies on this ordering so users see what to fill out before AI review.
    """
    pending = [
        sc.DraftSummary(field_name="사업자등록번호", review_required=True, confidence=0.40),
    ]

    result = sc.compute_completion(
        None,  # no industry → drivers_required default True
        {"fiscal_year_start": "2026-01"},  # only fiscal_year set
        {},  # 0 allocation rows
        pending_extractions=pending,
    )

    # Wizard order first.
    assert result.missing.index("통화") < result.missing.index("언어")
    assert result.missing.index("언어") < result.missing.index("직접/간접 계정 분류")
    assert result.missing.index("직접/간접 계정 분류") < result.missing.index("고정/변동 분류")
    assert result.missing.index("고정/변동 분류") < result.missing.index("동인 정의")
    # AI field appended last.
    assert result.missing[-1] == "AI 추출 미확정: 사업자등록번호"
    # Total = 5 wizard (currency, language, direct_indirect, fixed_variable,
    # drivers — drivers_required defaults True when industry=None) + 1 AI = 6.
    assert len(result.missing) == 6


def test_draft_summary_dataclass_is_frozen() -> None:
    """DraftSummary is frozen — callers must construct new instances.

    Prevents accidental mutation after construction (e.g., a service layer
    mutating `confidence` while serializing). Frozen also makes the
    dataclass hashable so it can be used in sets if needed.
    """
    draft = sc.DraftSummary(field_name="X", review_required=True, confidence=0.5)

    with pytest.raises((AttributeError, Exception)):  # FrozenInstanceError subclass
        draft.review_required = False  # type: ignore[misc]
