"""tests.services.m10_ai.test_comment_source_kind_validator — Story 10.3 validator tests.

Story 10.3 (cj-style Epic 10 4번째 진입점, cj-style 30번째 epic 연속) —
T4-companion tests for `validate_source_kind` + `assert_comment_mutable` pure
helpers in `apps.api.modules.m10_ai.service`.

Test breakdown (~10 cases, no DB):
- validate_source_kind accept × 3 (str auto_analysis / str ai_reference /
  SourceKind enum pass-through)
- validate_source_kind reject × 3 (empty / unknown / non-string non-enum)
- assert_comment_mutable × 2 (deny auto_analysis / allow ai_reference)
- AD-7 strict invariant × 1 (validate_source_kind only accepts kernel SSOT values)
- Korean SSOT message × 1 (rejection preserves message_ko field)

Path note: helpers live in apps/api service layer (10-2 precedent: `extract`
helpers in service.py covered by `tests/services/m10_ai/test_extraction_service.py`).
The "services" test directory is a logical grouping by concern, not file path —
it covers M10 service-layer pure functions including the apps/api ones.
"""

from __future__ import annotations

import inspect

import pytest

from apps.api.modules.m10_ai.service import (
    AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS_KO,
    AI_COMMENT_SOURCE_KIND_INVALID_KO,
    AICommentImmutableAutoAnalysisError,
    AICommentSourceKindInvalidError,
    assert_comment_mutable,
    validate_source_kind,
)
from packages.services.m10_ai.insight_cache_kernel import (
    SOURCE_KIND_VALUES,
    SourceKind,
)


# ── 1. validate_source_kind accept (3 cases) ──────────────────────


def test_validate_source_kind_accepts_auto_analysis_string() -> None:
    """'auto_analysis' string → SourceKind.AUTO_ANALYSIS (F10.2-(a))."""
    result = validate_source_kind("auto_analysis", trace_id="trace-1")
    assert result is SourceKind.AUTO_ANALYSIS


def test_validate_source_kind_accepts_ai_reference_string() -> None:
    """'ai_reference' string → SourceKind.AI_REFERENCE (F10.2-(a))."""
    result = validate_source_kind("ai_reference", trace_id="trace-2")
    assert result is SourceKind.AI_REFERENCE


def test_validate_source_kind_passes_through_source_kind_enum() -> None:
    """SourceKind enum instance → identical enum returned (DRY idempotent)."""
    auto = SourceKind.AUTO_ANALYSIS
    assert validate_source_kind(auto) is auto


# ── 2. validate_source_kind reject (3 cases) ──────────────────────


def test_validate_source_kind_rejects_unknown_string() -> None:
    """Unknown string value → strict reject (F10.2-(b) verbatim)."""
    with pytest.raises(AICommentSourceKindInvalidError) as exc:
        validate_source_kind("user_override", trace_id="trace-r1")
    assert exc.value.received_value == "user_override"
    assert "user_override" in str(exc.value)


def test_validate_source_kind_rejects_non_string_non_enum() -> None:
    """Non-string non-enum (e.g. int, list) → strict reject."""
    with pytest.raises(AICommentSourceKindInvalidError):
        validate_source_kind(12345, trace_id="trace-r2")
    with pytest.raises(AICommentSourceKindInvalidError):
        validate_source_kind(["auto_analysis"], trace_id="trace-r3")


def test_validate_source_kind_rejects_empty_string() -> None:
    """Empty string → strict reject (defense in depth)."""
    with pytest.raises(AICommentSourceKindInvalidError):
        validate_source_kind("", trace_id="trace-r4")


# ── 3. assert_comment_mutable (2 cases) ──────────────────────────


def test_assert_comment_mutable_denies_auto_analysis() -> None:
    """auto_analysis opinions are immutable (F10.2-(c) verbatim)."""
    with pytest.raises(AICommentImmutableAutoAnalysisError) as exc:
        assert_comment_mutable(
            source_kind="auto_analysis",
            comment_id="cmt-xyz",
            trace_id="trace-d1",
        )
    assert exc.value.comment_id == "cmt-xyz"
    assert exc.value.trace_id == "trace-d1"
    assert exc.value.message_ko == AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS_KO


def test_assert_comment_mutable_allows_ai_reference() -> None:
    """ai_reference opinions remain user-editable (F10.2-(c) verbatim)."""
    # MUST NOT raise
    assert_comment_mutable(
        source_kind="ai_reference",
        comment_id="cmt-ok",
        trace_id="trace-a1",
    )


# ── 4. AD-7 strict invariant (1 case) ────────────────────────────


def test_validate_source_kind_only_accepts_kernel_ssot() -> None:
    """validate_source_kind is constrained to SOURCE_KIND_VALUES SSOT."""
    # The function's accept list is exactly the kernel frozenset
    for value in SOURCE_KIND_VALUES:
        assert validate_source_kind(value) is not None
    # Cross-check: no third value can sneak in
    assert len(SOURCE_KIND_VALUES) == 2


# ── 5. Korean SSOT message (1 case) ───────────────────────────────


def test_rejection_envelope_carries_korean_message_ko() -> None:
    """Rejection envelope surfaces message_ko (master PRD §13.1 ko-KR)."""
    with pytest.raises(AICommentSourceKindInvalidError) as exc:
        validate_source_kind(None, trace_id="trace-ko")
    assert exc.value.message_ko == AI_COMMENT_SOURCE_KIND_INVALID_KO
    assert exc.value.message_ko == "분석 의견 출처가 불분명합니다"


# ── 6. Helper purity (1 case — bonus) ─────────────────────────────


def test_validate_source_kind_has_no_io_in_signature() -> None:
    """validate_source_kind is pure (AD-5 engine purity) — no I/O params."""
    sig = inspect.signature(validate_source_kind)
    # Only 2 params: source_kind (positional) + trace_id (keyword-only)
    assert list(sig.parameters.keys()) == ["source_kind", "trace_id"]
    assert sig.parameters["trace_id"].kind == inspect.Parameter.KEYWORD_ONLY