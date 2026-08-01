"""tests.services.test_product_references — pure-Python reference-count tests.

Story 2.3 — Task 1.2 / Task 6.1.

Pure-function tests for `packages.services.m1_baseline.product_references`.
No DB, no clock, no random — matches the AD-1 / AD-5 purity contract.

Coverage:
- count_bom_references: zero, parent-only, child-only, both sides, negative → raises
- count_ledger_references: stub returns 0 (Epic 5 placeholder)
- total_references: sum, with ledger stub, negative → raises
- BOM_REFERENCE_QUERY constant: structure, placeholders, OR clause
- story 2.3 invariants: ledger_count stub identity, total > 0 reject signal

Post-review changes (2026-08-01):
- `hash_references` removed (dead code, never called).
- `LEDGER_REFERENCE_QUERY_STUB` removed (decorative noise).
- Negative-input defense now RAISES ValueError (was clamping to 0 — masked
  caller bugs).
"""

from __future__ import annotations

import pytest

from packages.services.m1_baseline.product_references import (
    BOM_REFERENCE_QUERY,
    count_bom_references,
    count_ledger_references,
    total_references,
)


# ── count_bom_references ─────────────────────────────────────────
def test_count_bom_references_zero() -> None:
    """Both sides zero → 0. Type change allowed (no references)."""
    assert count_bom_references(0, 0) == 0


def test_count_bom_references_parent_only() -> None:
    """Parent side N, child side 0 → N. AC #4: parent-side counts."""
    assert count_bom_references(5, 0) == 5


def test_count_bom_references_child_only() -> None:
    """Parent side 0, child side N → N. AC #1: child-side counts."""
    assert count_bom_references(0, 3) == 3


def test_count_bom_references_both_sides_union() -> None:
    """Both sides sum. AC #4: union rule — either side counts."""
    assert count_bom_references(2, 7) == 9


def test_count_bom_references_negative_raises() -> None:
    """Defense-in-depth: negative input → ValueError (post-review)."""
    with pytest.raises(ValueError, match="must be non-negative"):
        count_bom_references(-1, 0)
    with pytest.raises(ValueError, match="must be non-negative"):
        count_bom_references(0, -5)
    with pytest.raises(ValueError, match="must be non-negative"):
        count_bom_references(-3, -7)


# ── count_ledger_references (stub) ────────────────────────────────
def test_count_ledger_references_stub_returns_zero() -> None:
    """Epic 5 placeholder — always returns 0."""
    assert count_ledger_references() == 0


def test_count_ledger_references_stub_is_idempotent() -> None:
    """Stub determinism — repeated calls return 0."""
    assert count_ledger_references() == 0
    assert count_ledger_references() == 0
    assert count_ledger_references() == 0


# ── total_references ─────────────────────────────────────────────
def test_total_references_sum() -> None:
    """bom + ledger = total."""
    assert total_references(3, 0) == 3


def test_total_references_with_ledger_stub() -> None:
    """With ledger stub, total == bom_count. Epic 5 will fold ledger in."""
    assert total_references(3, 0) == 3
    assert total_references(0, 0) == 0


def test_total_references_negative_raises() -> None:
    """Defense-in-depth — same as count_bom_references (post-review)."""
    with pytest.raises(ValueError, match="must be non-negative"):
        total_references(-1, 0)
    with pytest.raises(ValueError, match="must be non-negative"):
        total_references(3, -5)


def test_total_references_greater_than_zero_signals_reject() -> None:
    """Return value > 0 → service must raise ProductTypeHasReferencesError."""
    # The service layer's contract is "if total > 0 → reject".
    # This test asserts the helper's output carries that signal.
    assert total_references(1, 0) > 0
    assert total_references(0, 1) > 0  # hypothetical Epic 5 scenario
    assert total_references(0, 0) == 0  # zero → allow


# ── BOM_REFERENCE_QUERY constant ─────────────────────────────────
def test_bom_reference_query_selects_count() -> None:
    """The constant is a SELECT COUNT(*) statement."""
    assert "SELECT COUNT(*)" in BOM_REFERENCE_QUERY
    assert "FROM bom_lines" in BOM_REFERENCE_QUERY


def test_bom_reference_query_filters_tenant_id() -> None:
    """Tenant-scoped query: AD-3 RLS + explicit tenant_id WHERE."""
    assert "tenant_id = :tenant_id" in BOM_REFERENCE_QUERY


def test_bom_reference_query_uses_or_for_both_sides() -> None:
    """AC #4: parent + child sides EITHER count. The SQL uses OR."""
    assert "parent_product_id = :product_id" in BOM_REFERENCE_QUERY
    assert "child_product_id = :product_id" in BOM_REFERENCE_QUERY
    assert " OR " in BOM_REFERENCE_QUERY


def test_bom_reference_query_uses_bind_parameters() -> None:
    """SQL injection prevention — bind params (:name), not %s or f-string."""
    # No f-string interpolation markers
    assert "{tenant_id}" not in BOM_REFERENCE_QUERY
    assert "{product_id}" not in BOM_REFERENCE_QUERY
    # Named bind params present
    assert ":tenant_id" in BOM_REFERENCE_QUERY
    assert ":product_id" in BOM_REFERENCE_QUERY


def test_bom_reference_query_no_string_concat_injection() -> None:
    """No %s placeholder would indicate Python-side string formatting."""
    assert "%s" not in BOM_REFERENCE_QUERY
    assert "%(" not in BOM_REFERENCE_QUERY


# ── Story 2.3 invariants ────────────────────────────────────────
def test_story_2_3_invariant_bom_count_zero_allows_change() -> None:
    """PRD §6.1: BOM 0건 + 수불 0건 → type change allowed."""
    bom_count = count_bom_references(0, 0)
    ledger_count = count_ledger_references()  # stub = 0
    total = total_references(bom_count, ledger_count)
    assert total == 0  # service: total == 0 → allow


def test_story_2_3_invariant_bom_count_nonzero_rejects_change() -> None:
    """PRD §6.1: BOM N건 → service raises ProductTypeHasReferencesError."""
    bom_count = count_bom_references(0, 3)  # 3 BOMs as child
    ledger_count = count_ledger_references()  # stub = 0
    total = total_references(bom_count, ledger_count)
    assert total == 3  # service: total > 0 → 409 reject


def test_story_2_3_invariant_parent_side_also_counts() -> None:
    """PRD §6.1 conservative: parent-side references also block change."""
    # Pure product (top of BOM) is referenced as parent in 5 BOMs.
    bom_count = count_bom_references(5, 0)
    ledger_count = count_ledger_references()
    total = total_references(bom_count, ledger_count)
    assert total == 5  # rejected


# ── Parametrized: total = 0 cases (allowed) ──────────────────────
@pytest.mark.parametrize(
    ("parent", "child", "expected_total"),
    [
        (0, 0, 0),
        (1, 0, 1),
        (0, 1, 1),
        (5, 3, 8),
        (10, 10, 20),
    ],
)
def test_total_references_parametrized(parent: int, child: int, expected_total: int) -> None:
    """Parametrized: total = parent + child + ledger_stub(0)."""
    bom_count = count_bom_references(parent, child)
    ledger_count = count_ledger_references()
    assert total_references(bom_count, ledger_count) == expected_total
