"""tests.services.m10_ai.test_insight_cache_kernel — Story 10.2 kernel tests.

Story 10.2 (cj-style Epic 10 3번째 진입점, cj-style 29번째 epic 연속) —
T1.3 tests for `packages/services/m10_ai/insight_cache_kernel.py`.

Test breakdown (~25 cases):
- compose_insight_cache_key × 6 (AD-25 verbatim 3-tuple + idempotent + UUID/str strict typing)
- make_default_insights × 4 (3 default insights + source_kind='auto_analysis' ONLY + deterministic)
- InsightEntry frozen × 3 (creation + immutable + insight_kind discriminator)
- InsightCacheKey frozen × 3 (creation + immutable + 3-tuple shape AD-25 verbatim)
- InsightCacheKeyShapeError × 3 (attributes + Korean SSOT + ValueError subclass)
- AD-5 stdlib no-I/O × 2 (import scan + pure determinism)
- Constants parity × 2 (INSIGHT_KIND_VALUES 3 + SOURCE_KIND_VALUES 2)
- InsightKind/SourceKind enum × 2 (value sets match frozensets)

P-015 SSOT pattern: drift detector runs in
`tests/integration/test_capability_matrix_v1_21_drift.py` (T6.1).
"""

from __future__ import annotations

import inspect
import uuid

import pytest

from packages.services.m10_ai.insight_cache_kernel import (
    INSIGHT_KIND_VALUES,
    SOURCE_KIND_VALUES,
    InsightCacheKey,
    InsightCacheKeyShapeError,
    InsightEntry,
    InsightKind,
    SourceKind,
    compose_insight_cache_key,
    make_default_insights,
)


# ── compose_insight_cache_key ────────────────────────────────


def test_compose_insight_cache_key_basic() -> None:
    """AD-25 verbatim 3-tuple serialization: basic happy path."""
    tenant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    key = compose_insight_cache_key(
        tenant_id=tenant_id,
        period_key="2026-07",
        calculation_result_hash="abc123def456",
    )
    expected = "12345678-1234-5678-1234-567812345678|2026-07|abc123def456"
    assert key == expected


def test_compose_insight_cache_key_idempotent() -> None:
    """Same inputs always produce same output (AD-5 engine purity)."""
    tenant_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    args = {
        "tenant_id": tenant_id,
        "period_key": "2026-08",
        "calculation_result_hash": "sha256hex",
    }
    assert compose_insight_cache_key(**args) == compose_insight_cache_key(**args)


def test_compose_insight_cache_key_canonical_form() -> None:
    """Canonical form: '|' separator, 3 components in fixed order."""
    tenant_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    key = compose_insight_cache_key(
        tenant_id=tenant_id,
        period_key="2026-01",
        calculation_result_hash="hash",
    )
    parts = key.split("|")
    assert len(parts) == 3
    assert parts[0] == "11111111-2222-3333-4444-555555555555"
    assert parts[1] == "2026-01"
    assert parts[2] == "hash"


def test_compose_insight_cache_key_invalid_tenant_id_type() -> None:
    """tenant_id must be uuid.UUID instance, not str."""
    with pytest.raises(InsightCacheKeyShapeError) as excinfo:
        compose_insight_cache_key(
            tenant_id="not-a-uuid",  # type: ignore[arg-type]
            period_key="2026-07",
            calculation_result_hash="abc",
        )
    assert excinfo.value.component == "tenant_id"


def test_compose_insight_cache_key_empty_period_key() -> None:
    """period_key cannot be empty string."""
    with pytest.raises(InsightCacheKeyShapeError) as excinfo:
        compose_insight_cache_key(
            tenant_id=uuid.uuid4(),
            period_key="",
            calculation_result_hash="abc",
        )
    assert excinfo.value.component == "period_key"
    assert "empty" in excinfo.value.reason


def test_compose_insight_cache_key_empty_calculation_result_hash() -> None:
    """calculation_result_hash cannot be empty string."""
    with pytest.raises(InsightCacheKeyShapeError) as excinfo:
        compose_insight_cache_key(
            tenant_id=uuid.uuid4(),
            period_key="2026-07",
            calculation_result_hash="",
        )
    assert excinfo.value.component == "calculation_result_hash"


# ── make_default_insights ─────────────────────────────────────


def test_make_default_insights_count() -> None:
    """Returns exactly 3 default insights (master PRD §12 verbatim)."""
    insights = make_default_insights("2026-07")
    assert len(insights) == 3


def test_make_default_insights_source_kind_auto_analysis_only() -> None:
    """AD-7 strict invariant: all 3 entries are AUTO_ANALYSIS only.

    ai_reference 항목 추가는 Story 10.3 wire 진입 시점에 detailed wire.
    """
    insights = make_default_insights("2026-07")
    for entry in insights:
        assert entry.source_kind == SourceKind.AUTO_ANALYSIS


def test_make_default_insights_kind_order() -> None:
    """Deterministic order: cost_reduction_candidate, anomaly_pattern, forecast."""
    insights = make_default_insights("2026-07")
    assert insights[0].insight_kind == InsightKind.COST_REDUCTION_CANDIDATE
    assert insights[1].insight_kind == InsightKind.ANOMALY_PATTERN
    assert insights[2].insight_kind == InsightKind.FORECAST


def test_make_default_insights_period_key_interpolation() -> None:
    """period_key appears in question + answer + evidence_ref."""
    insights = make_default_insights("2026-09")
    for entry in insights:
        assert "2026-09" in entry.question
        assert "2026-09" in entry.answer
        assert "2026-09" in (entry.evidence_ref or "")


# ── InsightEntry frozen ──────────────────────────────────────


def test_insight_entry_creation() -> None:
    """InsightEntry can be created with all 6 fields."""
    entry = InsightEntry(
        insight_kind=InsightKind.FORECAST,
        question="예측 질문",
        answer="예측 답변",
        source_kind=SourceKind.AUTO_ANALYSIS,
        evidence_ref="ref",
        generated_at=__import__("datetime").datetime(2026, 1, 1),
    )
    assert entry.insight_kind == InsightKind.FORECAST
    assert entry.question == "예측 질문"
    assert entry.source_kind == SourceKind.AUTO_ANALYSIS
    assert entry.evidence_ref == "ref"


def test_insight_entry_frozen() -> None:
    """Frozen dataclass: cannot mutate fields after creation."""
    entry = InsightEntry(
        insight_kind=InsightKind.ANOMALY_PATTERN,
        question="q",
        answer="a",
        source_kind=SourceKind.AUTO_ANALYSIS,
        evidence_ref=None,
        generated_at=__import__("datetime").datetime(2026, 1, 1),
    )
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        entry.question = "modified"  # type: ignore[misc]


def test_insight_entry_evidence_ref_optional() -> None:
    """evidence_ref can be None."""
    entry = InsightEntry(
        insight_kind=InsightKind.COST_REDUCTION_CANDIDATE,
        question="q",
        answer="a",
        source_kind=SourceKind.AUTO_ANALYSIS,
        evidence_ref=None,
        generated_at=__import__("datetime").datetime(2026, 1, 1),
    )
    assert entry.evidence_ref is None


# ── InsightCacheKey frozen ───────────────────────────────────


def test_insight_cache_key_creation() -> None:
    """InsightCacheKey holds AD-25 verbatim 3-tuple."""
    tenant_id = uuid.uuid4()
    key = InsightCacheKey(
        tenant_id=tenant_id,
        period_key="2026-07",
        calculation_result_hash="sha256hex",
    )
    assert key.tenant_id == tenant_id
    assert key.period_key == "2026-07"
    assert key.calculation_result_hash == "sha256hex"


def test_insight_cache_key_frozen() -> None:
    """Frozen dataclass: cannot mutate AD-25 3-tuple."""
    key = InsightCacheKey(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        calculation_result_hash="hash",
    )
    with pytest.raises(Exception):
        key.period_key = "2099-99"  # type: ignore[misc]


def test_insight_cache_key_three_tuple_shape() -> None:
    """AD-25 verbatim: cache key is (tenant_id, period_key, calculation_result_hash)."""
    key = InsightCacheKey(
        tenant_id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
        period_key="2026-12",
        calculation_result_hash="abcdef",
    )
    assert isinstance(key.tenant_id, uuid.UUID)
    assert isinstance(key.period_key, str)
    assert isinstance(key.calculation_result_hash, str)
    assert len([key.tenant_id, key.period_key, key.calculation_result_hash]) == 3


# ── InsightCacheKeyShapeError ────────────────────────────────


def test_insight_cache_key_shape_error_attributes() -> None:
    """All 3 attributes populated correctly."""
    exc = InsightCacheKeyShapeError(
        component="period_key",
        value="",
        reason="empty",
    )
    assert exc.component == "period_key"
    assert exc.value == ""
    assert exc.reason == "empty"


def test_insight_cache_key_shape_error_is_value_error() -> None:
    """InsightCacheKeyShapeError is ValueError subclass (typing convention)."""
    exc = InsightCacheKeyShapeError(
        component="tenant_id",
        value=None,
        reason="none",
    )
    assert isinstance(exc, ValueError)


def test_insight_cache_key_shape_error_message_contains_component() -> None:
    """Error message includes component name (for log/debug)."""
    exc = InsightCacheKeyShapeError(
        component="calculation_result_hash",
        value="x",
        reason="too short",
    )
    assert "calculation_result_hash" in str(exc)


# ── AD-5 stdlib no-I/O ───────────────────────────────────────


def test_insight_cache_kernel_no_external_imports() -> None:
    """AD-5 engine purity: kernel only imports stdlib + internal modules.

    Uses AST to inspect actual `import` statements, NOT raw source text
    (raw source contains forbidden-lib names in docstrings as anti-pattern guards).
    """
    import ast
    import pathlib

    kernel_path = (
        pathlib.Path(__file__).resolve().parents[3]
        / "packages"
        / "services"
        / "m10_ai"
        / "insight_cache_kernel.py"
    )
    tree = ast.parse(kernel_path.read_text(encoding="utf-8"))

    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module.split(".")[0])

    forbidden = {"pydantic", "fastapi", "sqlalchemy", "alembic", "anthropic"}
    for mod in imported_modules:
        assert mod not in forbidden, f"Forbidden import '{mod}' in kernel"


def test_insight_cache_kernel_pure_determinism() -> None:
    """make_default_insights is deterministic (AD-5 pure)."""
    a = make_default_insights("2026-07")
    b = make_default_insights("2026-07")
    assert a == b


# ── Constants parity ─────────────────────────────────────────


def test_insight_kind_values_set_size() -> None:
    """INSIGHT_KIND_VALUES has exactly 3 values (master PRD §12)."""
    assert len(INSIGHT_KIND_VALUES) == 3


def test_source_kind_values_set_size() -> None:
    """SOURCE_KIND_VALUES has exactly 2 values (AD-7 + 10-3 forward-bind)."""
    assert len(SOURCE_KIND_VALUES) == 2


# ── Enum ↔ frozenset parity ──────────────────────────────────


def test_insight_kind_enum_values_match_frozenset() -> None:
    """InsightKind enum values are subset of INSIGHT_KIND_VALUES (AD-15 SSOT)."""
    enum_values = frozenset(k.value for k in InsightKind)
    assert enum_values == INSIGHT_KIND_VALUES


def test_source_kind_enum_values_match_frozenset() -> None:
    """SourceKind enum values are subset of SOURCE_KIND_VALUES (AD-15 SSOT)."""
    enum_values = frozenset(k.value for k in SourceKind)
    assert enum_values == SOURCE_KIND_VALUES