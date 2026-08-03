"""Story 5.2 — inventory_ledger event_type 11-value drift detector.

A5-style 3-way drift detector for the inventory_ledger.event_type enum.
Unlike `test_audit_action_consistency.py` which compares audit action
sets to `action IN (...)` CHECKs, this test pins the 11-value
event_type enum across:

1. **Pure kernel** — `packages.services.m4_inventory.ledger.INVENTORY_LEDGER_EVENT_TYPES`
   (single source of truth for the 11-value enum).
2. **Alembic migration** — `apps/api/alembic/versions/0015_inventory_ledger.py`
   `event_type IN (...)` CHECK constraint.
3. **db_models ORM** — `apps/api/core/db_models.py::InventoryLedger::__table_args__`
   CheckConstraint literal.

If any axis drifts, this gate fires. CR 1.1 lesson applied to a
different column (event_type vs action). Audit action drift is
handled by `test_audit_action_consistency.py` (different axis).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _parse_event_type_check_values(migration_file: Path) -> frozenset[str] | None:
    """Parse `event_type IN ('a', 'b', ...)` from a single migration file.

    Returns None if no event_type CHECK is found.
    """
    if not migration_file.exists():
        return None
    src = migration_file.read_text(encoding="utf-8")
    pattern = re.compile(
        r"event_type\s+IN\s*\(\s*((?:'[^']+'\s*,?\s*)+)\)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(src)
    if match is None:
        return None
    values_str = match.group(1)
    return frozenset(re.findall(r"'([^']+)'", values_str))


def _parse_event_type_check_from_db_models(db_models_file: Path) -> frozenset[str] | None:
    """Parse `event_type IN ('a', 'b', ...)` from db_models.py InventoryLedger.

    The ORM uses a multi-line `CheckConstraint("event_type IN ('a', 'b', ...)", ...)`
    pattern — we look for the 11-value literal in the InventoryLedger block.
    """
    if not db_models_file.exists():
        return None
    src = db_models_file.read_text(encoding="utf-8")
    # Find the InventoryLedger class block.
    class_marker = "class InventoryLedger(Base):"
    class_start = src.find(class_marker)
    if class_start == -1:
        return None
    # Find the InventoryLedger block by searching from class_start forward
    # until the next `class` declaration (end of InventoryLedger).
    next_class = re.search(r"\nclass\s+\w+\(", src[class_start + 1:])
    block_end = (class_start + 1 + next_class.start()) if next_class else len(src)
    block = src[class_start:block_end]
    # The ORM literal may be either single-line or multi-line. Use a
    # balanced-paren scan: find `event_type IN (` then read until matching `)`.
    paren_start = re.search(r"event_type\s+IN\s*\(", block, re.IGNORECASE)
    if paren_start is None:
        return None
    # Walk forward to find the matching closing paren, handling nested parens.
    depth = 0
    start = paren_start.end()
    i = start
    while i < len(block):
        c = block[i]
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                end = i
                break
            depth -= 1
        i += 1
    else:
        return None
    values_str = block[start:end]
    return frozenset(re.findall(r"'([^']+)'", values_str))


@pytest.mark.engine
def test_inventory_ledger_event_type_pure_kernel_matches_migration() -> None:
    """3-way: pure-kernel frozenset ↔ Alembic migration CHECK.

    The 11-value enum is the canonical set; Alembic 0015 must mirror
    exactly.
    """
    from packages.services.m4_inventory.ledger import INVENTORY_LEDGER_EVENT_TYPES

    migration = ROOT / "apps" / "api" / "alembic" / "versions" / "0015_inventory_ledger.py"
    migration_values = _parse_event_type_check_values(migration)
    assert migration_values is not None, (
        "0015_inventory_ledger.py: no `event_type IN (...)` CHECK found. "
        "The 11-value event_type enum must be pinned at the DB layer."
    )
    assert INVENTORY_LEDGER_EVENT_TYPES == migration_values, (
        "Story 5.2 — event_type drift: pure kernel ↔ Alembic migration.\n"
        f"  Pure kernel ({len(INVENTORY_LEDGER_EVENT_TYPES)}): "
        f"{sorted(INVENTORY_LEDGER_EVENT_TYPES)}\n"
        f"  Migration   ({len(migration_values)}): {sorted(migration_values)}\n"
        f"  MISSING from migration: {sorted(INVENTORY_LEDGER_EVENT_TYPES - migration_values)}\n"
        f"  EXTRA in migration:     {sorted(migration_values - INVENTORY_LEDGER_EVENT_TYPES)}"
    )


@pytest.mark.engine
def test_inventory_ledger_event_type_pure_kernel_matches_orm() -> None:
    """3-way: pure-kernel frozenset ↔ db_models InventoryLedger CHECK.

    SQLAlchemy CheckConstraint literal must mirror the pure-kernel
    frozenset (drift detector pins both DB definitions).
    """
    from packages.services.m4_inventory.ledger import INVENTORY_LEDGER_EVENT_TYPES

    db_models = ROOT / "apps" / "api" / "core" / "db_models.py"
    orm_values = _parse_event_type_check_from_db_models(db_models)
    assert orm_values is not None, (
        "apps/api/core/db_models.py: no `event_type IN (...)` CheckConstraint "
        "found inside `class InventoryLedger(Base)`. The 11-value event_type "
        "enum must be pinned at the ORM layer."
    )
    assert INVENTORY_LEDGER_EVENT_TYPES == orm_values, (
        "Story 5.2 — event_type drift: pure kernel ↔ db_models ORM.\n"
        f"  Pure kernel ({len(INVENTORY_LEDGER_EVENT_TYPES)}): "
        f"{sorted(INVENTORY_LEDGER_EVENT_TYPES)}\n"
        f"  ORM         ({len(orm_values)}): {sorted(orm_values)}\n"
        f"  MISSING from ORM: {sorted(INVENTORY_LEDGER_EVENT_TYPES - orm_values)}\n"
        f"  EXTRA in ORM:     {sorted(orm_values - INVENTORY_LEDGER_EVENT_TYPES)}"
    )


@pytest.mark.engine
def test_inventory_ledger_event_type_count_is_11() -> None:
    """OQ3 cj-style default: 11-value enum explicit at 5-2 ship."""
    from packages.services.m4_inventory.ledger import INVENTORY_LEDGER_EVENT_TYPES

    assert len(INVENTORY_LEDGER_EVENT_TYPES) == 11, (
        f"event_type enum has {len(INVENTORY_LEDGER_EVENT_TYPES)} values; "
        f"expected exactly 11. Adjust the 11-value list per OQ3 cj-style default."
    )


@pytest.mark.engine
def test_inventory_ledger_event_type_expected_set() -> None:
    """Explicit pin: the 11 expected event_type values.

    Forces the reader to enumerate the full set when reviewing diffs.
    """
    from packages.services.m4_inventory.ledger import INVENTORY_LEDGER_EVENT_TYPES

    expected = {
        "opening_carried",
        "opening_carried_stale_overwrite",
        "purchase_inbound",
        "sales_outbound",
        "production_output_inbound",
        "production_material_consumption",
        "adjustment_positive",
        "adjustment_negative",
        "reversal_negating",
        "reversal_corrected",
        "closing_snapshot",
    }
    assert INVENTORY_LEDGER_EVENT_TYPES == frozenset(expected)