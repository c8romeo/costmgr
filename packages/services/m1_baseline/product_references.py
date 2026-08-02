"""packages.services.m1_baseline.product_references — pure reference-count helpers (Story 2.3).

Pure-Python, stdlib-only module (AD-1 / AD-5). NO DB, NO clock, NO random.

Holds the **pure** arithmetic for the type-change integrity guard:

- `BOM_REFERENCE_QUERY` — SQL fragment template the service layer executes
  (one OR-merged query; mirrors `apps/api/modules/m1_baseline/services/
  product_service.py:_count_product_references`).
- `count_bom_references` — pure helper: parent + child sums.
- `count_ledger_references` — pure stub returning `0`. The `inventory_ledger`
  table is deferred to Epic 5 / Story 5.2. When that lands, **the Epic 5
  developer changes only this function** (no signature change). The error
  envelope already includes `ledger_count: 0` for forward-compatibility.
- `total_references` — `bom_count + ledger_count`.

Why this lives in `packages/services/` (not `apps/api/`):
- Mirrors the Story 2.2 `bom_validation.py` placement.
- AD-11 layer rule — `apps/api/core/` may NOT import from `packages.cost_engine`.
- Both API and (future) web consumption need a stable, testable contract.

Update-history:
- 2026-08-01 (initial) — pure helpers.
- 2026-08-01 (post-review) — removed `hash_references` (dead code),
  removed `LEDGER_REFERENCE_QUERY_STUB` (decorative noise). Negative-input
  defense now raises `ValueError` instead of clamping to 0 (post-review).
"""

from __future__ import annotations

from typing import Final

# ── BOM reference SQL fragment template ──────────────────────────
# This is the SQL the service layer executes to count references
# (bom_lines rows where the product appears as parent OR child).
# Stored as a constant so tests can pin the query shape.
#
# Both sides count because PRD §6.1 is silent on which side; the
# conservative rule treats EITHER side as a reference (changing a
# product's type affects both "what BOMs it roots" and "what BOMs
# consume it").
#
# Placeholders: `{tenant_id}`, `{product_id}` — must be substituted
# by the service layer with the bind parameters (NOT via string
# interpolation — bind params block SQL injection).
BOM_REFERENCE_QUERY: Final[str] = (
    "SELECT COUNT(*) FROM bom_lines "
    "WHERE tenant_id = :tenant_id "
    "AND (parent_product_id = :product_id OR child_product_id = :product_id)"
)

# Epic 5 / Story 5.2 fold-in marker — search for `TODO(epic-5): REPLACE_LEDGER_STUB`
# to locate the swap point when the `inventory_ledger` table lands.
# (The marker is documentation-only — runtime code does not consult any flag.)


# ── Public helpers ────────────────────────────────────────────
def count_bom_references(parent_count: int, child_count: int) -> int:
    """Pure: total BOM rows referencing the product.

    Args:
        parent_count: Number of bom_lines where the product is the parent.
        child_count: Number of bom_lines where the product is the child.

    Returns:
        `parent_count + child_count` (Epic 2 — bom_lines only).

    Raises:
        ValueError: If either count is negative (defense-in-depth — the
            service layer should never pass a negative value from a
            `SELECT COUNT(*)` query).
    """
    if parent_count < 0 or child_count < 0:
        raise ValueError(
            f"bom counts must be non-negative — received parent={parent_count}, child={child_count}"
        )
    return parent_count + child_count


def count_ledger_references() -> int:
    """Pure stub: number of inventory_ledger rows referencing the product.

    Returns `0` always until Epic 5 / Story 5.2 implements the
    `inventory_ledger` table. The function signature is zero-argument
    so the Epic 5 swap is a one-line change (add `tenant_id`, `product_id`
    kwargs + a real DB query).

    Story 2.3 establishes the contract; Epic 5 fulfils it.

    Returns:
        `0` (stub).
    """
    return 0


def total_references(bom_count: int, ledger_count: int) -> int:
    """Pure: total references across all sources.

    Args:
        bom_count: From `count_bom_references`.
        ledger_count: From `count_ledger_references` (always 0 until Epic 5).

    Returns:
        `bom_count + ledger_count`. If `> 0`, the type change is rejected.

    Raises:
        ValueError: If either count is negative.
    """
    if bom_count < 0 or ledger_count < 0:
        raise ValueError(
            f"reference counts must be non-negative — received bom={bom_count}, ledger={ledger_count}"
        )
    return bom_count + ledger_count


# ── Typed errors (mapped to HTTP by handlers.py) ──────────────
# None at this layer — the service raises `ProductTypeHasReferencesError`
# from `apps/api/modules/m1_baseline/services/product_service.py`. The
# pure helpers are arithmetic; they raise `ValueError` for invariant
# violations (negative counts) — caller-side bug, not user input.


# Re-exports — keep the public API flat.
__all__ = [
    "BOM_REFERENCE_QUERY",
    "count_bom_references",
    "count_ledger_references",
    "total_references",
]
