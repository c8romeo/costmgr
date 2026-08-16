"""tests.cost_engine.test_budget_variance — Story 8.2 pure kernel tests.

Tests for `packages.cost_engine.budget_variance`:
- `compute_variance`: budget_value + actual_value → Variance
  - 정상범위 + 5종 edge cases (negative / non-Decimal / zero budget / zero actual / both zero)
- `compute_variance_color`: variance_pct → Color (gray / yellow / red)
  - 3-tier severity thresholds + Infinity/NaN fallback + non-Decimal
- `compute_variance_hash`: Variance → sha256 digest
  - 결정론 + 100회 byte-identical
- `compute_abcd_disabled_badge`: variant → ABCDDisabledBadge (frozen)
  - 3 variants (variance / trend / sensitivity) + invalid variant
- Severity boundaries (±5% / ±10%) + 부호 보존 + ROUND_HALF_EVEN
- 100회 determinism (V8 회귀 가능)
- AD-8 monetary types parity (TS decimal.js)
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.budget_variance import (
    ABCD_DISABLED_LABEL,
    ABCD_DISABLED_NOTE,
    ABCD_DISABLED_TOOLTIP,
    SEVERITY_THRESHOLD_CRITICAL_PCT,
    SEVERITY_THRESHOLD_WARNING_PCT,
    VARIANCE_HASH_PREFIX,
    VARIANCE_PCT_QUANTUM,
    ABCDDisabledBadge,
    Variance,
    compute_abcd_disabled_badge,
    compute_variance,
    compute_variance_color,
    compute_variance_hash,
)


# ── Constants ────────────────────────────────────────────────
def test_severity_threshold_constants():
    """PRD §F8.2 verbatim threshold constants."""
    assert Decimal("5") == SEVERITY_THRESHOLD_WARNING_PCT
    assert Decimal("10") == SEVERITY_THRESHOLD_CRITICAL_PCT


def test_variance_pct_quantum_constant():
    """Decimal precision quantum = 4 decimal places (AD-8 monetary)."""
    assert Decimal("0.0001") == VARIANCE_PCT_QUANTUM


def test_hash_prefix_constant():
    """Hash format prefix = 'sha256:'."""
    assert VARIANCE_HASH_PREFIX == "sha256:"


def test_abcd_disabled_label_constant():
    """A×B×C×D 회색 배지 label (PRD §10 M8 (b) verbatim)."""
    assert ABCD_DISABLED_LABEL == "A×B×C×D 원가 차이 분석"


def test_abcd_disabled_tooltip_constant():
    """A×B×C×D 회색 배지 tooltip (PRD §15 NON-GOAL #1 verbatim)."""
    assert ABCD_DISABLED_TOOLTIP == (
        "2차 예정 — A×B×C×D 편성 엔진 미구현 (PRD §15 NON-GOAL #1)"
    )


def test_abcd_disabled_note_constant():
    """A×B×C×D 비고란 note (PRD §15 NON-GOAL #1 verbatim)."""
    assert ABCD_DISABLED_NOTE == "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]"


# ── compute_variance — happy path ────────────────────────────
def test_compute_variance_normal_2_percent_under():
    """2% 절감 (normal) → severity = normal."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("980000"),
    )
    assert result.budget_value == Decimal("1000000")
    assert result.actual_value == Decimal("980000")
    assert result.difference == Decimal("-20000")
    assert result.variance_pct == Decimal("-2.0000")
    assert result.severity == "normal"


def test_compute_variance_warning_7_percent_over():
    """7% 초과 (warning) → severity = warning."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1070000"),
    )
    assert result.difference == Decimal("70000")
    assert result.variance_pct == Decimal("7.0000")
    assert result.severity == "warning"


def test_compute_variance_critical_15_percent_over():
    """15% 초과 (critical) → severity = critical."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1150000"),
    )
    assert result.difference == Decimal("150000")
    assert result.variance_pct == Decimal("15.0000")
    assert result.severity == "critical"


def test_compute_variance_sign_preserved_negative():
    """음수 variance (절감) — sign 보존."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("900000"),
    )
    assert result.difference < 0
    assert result.variance_pct < 0
    assert result.variance_pct == Decimal("-10.0000")
    assert result.severity == "critical"


def test_compute_variance_sign_preserved_positive():
    """양수 variance (초과) — sign 보존."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1100000"),
    )
    assert result.difference > 0
    assert result.variance_pct > 0
    assert result.variance_pct == Decimal("10.0000")
    assert result.severity == "critical"


def test_compute_variance_100x_determinism():
    """100회 동일 입력 → 100회 byte-identical 결과 (V8 회귀)."""
    expected = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1070000"),
    )
    for _ in range(100):
        assert compute_variance(
            budget_value=Decimal("1000000"),
            actual_value=Decimal("1070000"),
        ) == expected


# ── compute_variance — edge cases ────────────────────────────
def test_compute_variance_zero_budget_zero_actual():
    """budget=0 AND actual=0 → variance_pct=0 + severity=normal (no variance)."""
    result = compute_variance(
        budget_value=Decimal("0"),
        actual_value=Decimal("0"),
    )
    assert result.difference == Decimal("0")
    assert result.variance_pct == Decimal("0")
    assert result.severity == "normal"


def test_compute_variance_zero_budget_positive_actual():
    """budget=0 AND actual>0 → variance_pct=+Infinity + severity=critical."""
    result = compute_variance(
        budget_value=Decimal("0"),
        actual_value=Decimal("1000000"),
    )
    assert result.difference == Decimal("1000000")
    assert result.variance_pct.is_infinite()
    assert result.variance_pct > 0  # 양수 보존
    assert result.severity == "critical"


def test_compute_variance_positive_budget_zero_actual():
    """budget>0 AND actual=0 → variance_pct=-100 (100% 절감) + severity=critical."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("0"),
    )
    assert result.difference == Decimal("-1000000")
    assert result.variance_pct == Decimal("-100.0000")
    assert result.severity == "critical"


def test_compute_variance_negative_budget_raises():
    """budget<0 → ValueError."""
    with pytest.raises(ValueError, match="budget_value must be non-negative"):
        compute_variance(
            budget_value=Decimal("-1"),
            actual_value=Decimal("1000000"),
        )


def test_compute_variance_negative_actual_raises():
    """actual<0 → ValueError."""
    with pytest.raises(ValueError, match="actual_value must be non-negative"):
        compute_variance(
            budget_value=Decimal("1000000"),
            actual_value=Decimal("-1"),
        )


def test_compute_variance_non_decimal_budget_raises():
    """budget not Decimal → ValueError."""
    with pytest.raises(ValueError, match="budget_value must be Decimal"):
        compute_variance(
            budget_value=1000000,  # type: ignore[arg-type]
            actual_value=Decimal("1000000"),
        )


def test_compute_variance_non_decimal_actual_raises():
    """actual not Decimal → ValueError."""
    with pytest.raises(ValueError, match="actual_value must be Decimal"):
        compute_variance(
            budget_value=Decimal("1000000"),
            actual_value=1000000,  # type: ignore[arg-type]
        )


# ── Severity boundaries ──────────────────────────────────────
def test_severity_boundary_4_99_normal():
    """variance_pct = 4.99% → normal (gray)."""
    result = compute_variance(
        budget_value=Decimal("100"),
        actual_value=Decimal("104.99"),
    )
    assert result.variance_pct == Decimal("4.9900")
    assert result.severity == "normal"


def test_severity_boundary_5_0_warning():
    """variance_pct = 5.0% → warning (yellow)."""
    result = compute_variance(
        budget_value=Decimal("100"),
        actual_value=Decimal("105"),
    )
    assert result.variance_pct == Decimal("5.0000")
    assert result.severity == "warning"


def test_severity_boundary_9_99_warning():
    """variance_pct = 9.99% → warning (yellow)."""
    result = compute_variance(
        budget_value=Decimal("100"),
        actual_value=Decimal("109.99"),
    )
    assert result.variance_pct == Decimal("9.9900")
    assert result.severity == "warning"


def test_severity_boundary_10_0_critical():
    """variance_pct = 10.0% → critical (red)."""
    result = compute_variance(
        budget_value=Decimal("100"),
        actual_value=Decimal("110"),
    )
    assert result.variance_pct == Decimal("10.0000")
    assert result.severity == "critical"


def test_severity_boundary_4_99_negation_normal():
    """variance_pct = -4.99% → normal (sign 보존 + abs < 5)."""
    result = compute_variance(
        budget_value=Decimal("100"),
        actual_value=Decimal("95.01"),
    )
    assert result.variance_pct == Decimal("-4.9900")
    assert result.severity == "normal"


# ── Decimal precision ROUND_HALF_EVEN ────────────────────────
def test_round_half_even_4_decimal_places():
    """ROUND_HALF_EVEN 4 decimal places (AD-8 monetary parity with TS decimal.js)."""
    result = compute_variance(
        budget_value=Decimal("3"),
        actual_value=Decimal("1"),
    )
    # (1 - 3) / 3 * 100 = -66.6666... → quantize to -66.6667 (4 digit rounding)
    assert result.variance_pct == Decimal("-66.6667")


def test_round_half_even_identity_cases():
    """Identity cases — exact integer/half results preserve ROUND_HALF_EVEN."""
    result = compute_variance(
        budget_value=Decimal("200"),
        actual_value=Decimal("103"),
    )
    # (103 - 200) / 200 * 100 = -48.5 → -48.5000 (exact 1 decimal)
    assert result.variance_pct == Decimal("-48.5000")


def test_round_half_even_integer_exact():
    """Integer exact result → 4 decimal trailing zeros preserve."""
    result = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1070000"),
    )
    # 7% → 7.0000
    assert result.variance_pct == Decimal("7.0000")


# ── compute_variance_color ───────────────────────────────────
def test_compute_variance_color_normal_gray():
    """abs(variance_pct) < 5 → gray."""
    assert compute_variance_color(variance_pct=Decimal("0")) == "gray"
    assert compute_variance_color(variance_pct=Decimal("4.99")) == "gray"
    assert compute_variance_color(variance_pct=Decimal("-4.99")) == "gray"


def test_compute_variance_color_warning_yellow():
    """5 <= abs(variance_pct) < 10 → yellow."""
    assert compute_variance_color(variance_pct=Decimal("5")) == "yellow"
    assert compute_variance_color(variance_pct=Decimal("7.5")) == "yellow"
    assert compute_variance_color(variance_pct=Decimal("9.99")) == "yellow"
    assert compute_variance_color(variance_pct=Decimal("-5")) == "yellow"
    assert compute_variance_color(variance_pct=Decimal("-9.99")) == "yellow"


def test_compute_variance_color_critical_red():
    """abs(variance_pct) >= 10 → red."""
    assert compute_variance_color(variance_pct=Decimal("10")) == "red"
    assert compute_variance_color(variance_pct=Decimal("15")) == "red"
    assert compute_variance_color(variance_pct=Decimal("100")) == "red"
    assert compute_variance_color(variance_pct=Decimal("-100")) == "red"


def test_compute_variance_color_infinity_fallback_gray():
    """Infinity → gray (default fallback per AC #1)."""
    assert compute_variance_color(variance_pct=Decimal("Infinity")) == "gray"
    assert compute_variance_color(variance_pct=Decimal("-Infinity")) == "gray"


def test_compute_variance_color_nan_fallback_gray():
    """NaN → gray (default fallback per AC #1)."""
    assert compute_variance_color(variance_pct=Decimal("NaN")) == "gray"


def test_compute_variance_color_non_decimal_raises():
    """variance_pct not Decimal → ValueError."""
    with pytest.raises(ValueError, match="variance_pct must be Decimal"):
        compute_variance_color(variance_pct=5.0)  # type: ignore[arg-type]


# ── compute_variance_hash ────────────────────────────────────
def _make_variance() -> Variance:
    return compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1070000"),
    )


def test_compute_variance_hash_format():
    """Hash format: `sha256:` + 64-char hexdigest."""
    variance = _make_variance()
    digest = compute_variance_hash(variance=variance)
    assert digest.startswith("sha256:")
    hex_part = digest[len("sha256:"):]
    assert len(hex_part) == 64
    int(hex_part, 16)  # hex validation


def test_compute_variance_hash_determinism():
    """동일 입력 → 동일 hash (NFR16 determinism)."""
    variance = _make_variance()
    h1 = compute_variance_hash(variance=variance)
    h2 = compute_variance_hash(variance=variance)
    assert h1 == h2


def test_compute_variance_hash_100x_byte_identical():
    """100회 동일 입력 → 100회 byte-identical (V8 회귀)."""
    variance = _make_variance()
    expected = compute_variance_hash(variance=variance)
    for _ in range(100):
        assert compute_variance_hash(variance=variance) == expected


def test_compute_variance_hash_different_input_different_hash():
    """다른 actual_value → 다른 hash (변경 감지)."""
    v1 = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1070000"),
    )
    v2 = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1080000"),
    )
    assert compute_variance_hash(variance=v1) != compute_variance_hash(variance=v2)


def test_compute_variance_hash_non_variance_raises():
    """variance not Variance → ValueError."""
    with pytest.raises(ValueError, match="variance must be Variance"):
        compute_variance_hash(variance={"budget_value": Decimal("0")})  # type: ignore[arg-type]


# ── compute_abcd_disabled_badge ──────────────────────────────
def test_compute_abcd_disabled_badge_default_variant():
    """Default variant = 'variance'."""
    badge = compute_abcd_disabled_badge()
    assert badge.variant == "variance"
    assert badge.label == ABCD_DISABLED_LABEL
    assert badge.tooltip == ABCD_DISABLED_TOOLTIP
    assert badge.disabled is True


def test_compute_abcd_disabled_badge_variant_trend():
    """variant='trend' → trend placeholder."""
    badge = compute_abcd_disabled_badge(variant="trend")
    assert badge.variant == "trend"
    assert badge.disabled is True


def test_compute_abcd_disabled_badge_variant_sensitivity():
    """variant='sensitivity' → sensitivity placeholder."""
    badge = compute_abcd_disabled_badge(variant="sensitivity")
    assert badge.variant == "sensitivity"
    assert badge.disabled is True


def test_compute_abcd_disabled_badge_invalid_variant_raises():
    """invalid variant → ValueError."""
    with pytest.raises(ValueError, match="variant must be one of"):
        compute_abcd_disabled_badge(variant="invalid")  # type: ignore[arg-type]


# ── Frozen dataclass enforcement ─────────────────────────────
def test_variance_is_frozen():
    """Variance is frozen=True + slots=True — mutation 시 FrozenInstanceError."""
    variance = _make_variance()
    with pytest.raises(dataclasses.FrozenInstanceError):
        variance.severity = "normal"  # type: ignore[misc]


def test_variance_row_is_frozen():
    """VarianceRow is frozen=True — mutation 시 FrozenInstanceError."""
    from packages.cost_engine.budget_variance import VarianceRow

    row = VarianceRow(
        label="직접재료",
        variance=_make_variance(),
        color="yellow",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.label = "직접노무"  # type: ignore[misc]


def test_abcd_disabled_badge_is_frozen():
    """ABCDDisabledBadge is frozen=True — mutation 시 FrozenInstanceError."""
    badge = compute_abcd_disabled_badge()
    assert isinstance(badge, ABCDDisabledBadge)
    with pytest.raises(dataclasses.FrozenInstanceError):
        badge.disabled = False  # type: ignore[misc]


# ── Cross-function consistency ───────────────────────────────
def test_compute_variance_then_color_consistency():
    """compute_variance severity → compute_variance_color consistent."""
    # variance_pct=7% → warning → yellow
    v = compute_variance(
        budget_value=Decimal("100"),
        actual_value=Decimal("107"),
    )
    color = compute_variance_color(variance_pct=v.variance_pct)
    assert v.severity == "warning"
    assert color == "yellow"


def test_compute_variance_then_hash_consistency():
    """compute_variance → compute_variance_hash consistent."""
    v = compute_variance(
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1070000"),
    )
    h = compute_variance_hash(variance=v)
    assert h.startswith("sha256:")


def test_compute_variance_severity_color_mapping_table():
    """전체 severity → color mapping 일관성 (PRD §F8.2 verbatim)."""
    table = [
        (Decimal("0"), "normal", "gray"),
        (Decimal("2"), "normal", "gray"),
        (Decimal("4.99"), "normal", "gray"),
        (Decimal("5"), "warning", "yellow"),
        (Decimal("7.5"), "warning", "yellow"),
        (Decimal("9.99"), "warning", "yellow"),
        (Decimal("10"), "critical", "red"),
        (Decimal("15"), "critical", "red"),
        (Decimal("100"), "critical", "red"),
    ]
    for variance_pct, expected_severity, expected_color in table:
        v = compute_variance(
            budget_value=Decimal("100"),
            actual_value=Decimal("100") + Decimal("100") * variance_pct / 100,
        )
        assert v.variance_pct == variance_pct.quantize(Decimal("0.0001")), (
            f"variance_pct mismatch: {v.variance_pct} != {variance_pct.quantize(Decimal('0.0001'))}"
        )
        assert v.severity == expected_severity, (
            f"severity mismatch for {variance_pct}: {v.severity} != {expected_severity}"
        )
        color = compute_variance_color(variance_pct=v.variance_pct)
        assert color == expected_color, (
            f"color mismatch for {variance_pct}: {color} != {expected_color}"
        )


# ── Public API export ────────────────────────────────────────
def test_variance_exported():
    """Public API export — `Variance` importable from packages.cost_engine."""
    from packages.cost_engine import Variance as Exported

    assert Exported is Variance


def test_variance_row_exported():
    """Public API export — `VarianceRow` importable from packages.cost_engine."""
    from packages.cost_engine import VarianceRow as Exported

    assert Exported.__name__ == "VarianceRow"


def test_abcd_disabled_badge_exported():
    """Public API export — `ABCDDisabledBadge` importable."""
    from packages.cost_engine import ABCDDisabledBadge as Exported

    assert Exported is ABCDDisabledBadge


def test_compute_variance_exported():
    """Public API export — `compute_variance` importable."""
    from packages.cost_engine import compute_variance as Exported  # noqa: N812

    assert Exported is compute_variance


def test_compute_variance_color_exported():
    """Public API export — `compute_variance_color` importable."""
    from packages.cost_engine import compute_variance_color as Exported  # noqa: N812

    assert Exported is compute_variance_color


def test_compute_variance_hash_exported():
    """Public API export — `compute_variance_hash` importable."""
    from packages.cost_engine import compute_variance_hash as Exported  # noqa: N812

    assert Exported is compute_variance_hash


def test_compute_abcd_disabled_badge_exported():
    """Public API export — `compute_abcd_disabled_badge` importable."""
    from packages.cost_engine import compute_abcd_disabled_badge as Exported  # noqa: N812

    assert Exported is compute_abcd_disabled_badge
