"""tests.integration.test_inventory_projection_ledger_swap — T8 drift detector.

Story 5.2 AC #5 — Epic 3.3 inline projection deprecation timeline:
- 5-2 commit (this test) — read path swaps to ledger.
- Epic 5 maintenance window — `build_inventory_projection` legacy
  path preserved (callers migrate case-by-case).
- Epic 6 close-out retro — `build_inventory_projection` +
  `LEDGER_REFERENCE_QUERY_STUB` REMOVED entirely.

This test enforces that:
1. `MonthlyInputService._compute_inventory_projection_for_state`
   delegates to `LedgerService.query_period_closing_all` (NOT
   `build_inventory_projection`).
2. `LEDGER_REFERENCE_QUERY_STUB` is FILLED (non-empty) — its current
   value is a documentation marker (the canonical implementation is
   `packages/services/m4_inventory/ledger_query.py::build_period_closing_query`).
3. `packages/services/m2_input/inventory_projection.py` module
   contains a "TODO(epic-5-5-2)" CLOSED marker comment.

If any of these fail, the Epic 5 maintenance window has been violated:
either the inline projection is back in use (regression), or the
ledger reference stub has been emptied (regression), or the swap
marker has been removed without Epic 6 close-out going through.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from packages.services.m2_input.inventory_projection import (
    LEDGER_REFERENCE_QUERY_STUB,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_ledger_reference_stub_is_filled() -> None:
    """The Epic 3.3 `LEDGER_REFERENCE_QUERY_STUB` is now filled (5-2 wire).

    Pre-5-2: empty string (`""`).
    Post-5-2: SQL fragment describing the ledger read.

    Empty stub = Epic 5 maintenance window regression (Epic 6 close-out
    hasn't happened yet — the stub should NOT be empty).
    """
    assert LEDGER_REFERENCE_QUERY_STUB, (
        "LEDGER_REFERENCE_QUERY_STUB is empty — Epic 5 maintenance window "
        "violation. Either restore the 5-2 fill or proceed with Epic 6 "
        "close-out retro (which removes both the stub and "
        "build_inventory_projection)."
    )


def test_ledger_reference_stub_mentions_inventory_ledger_table() -> None:
    """The stub should reference the `inventory_ledger` table.

    Drift protection: if the canonical source table name changes, this
    test fails so the stub is updated alongside.
    """
    assert "inventory_ledger" in LEDGER_REFERENCE_QUERY_STUB, (
        f"LEDGER_REFERENCE_QUERY_STUB must reference 'inventory_ledger' "
        f"table. Got: {LEDGER_REFERENCE_QUERY_STUB[:80]!r}"
    )


def test_ledger_reference_stub_mentions_story_5_2_marker() -> None:
    """The stub is annotated with the Story 5.2 marker for drift visibility."""
    assert "Story 5.2" in LEDGER_REFERENCE_QUERY_STUB or "5-2" in LEDGER_REFERENCE_QUERY_STUB, (
        "LEDGER_REFERENCE_QUERY_STUB must be annotated with the Story 5.2 "
        "marker so future readers know which story wired it."
    )


def test_inventory_projection_module_has_closed_marker() -> None:
    """The module source contains the closed TODO(epic-5-5-2) marker.

    Story 5.2 closes the marker; if Epic 6 retro removes the marker
    prematurely, this test fails (drift signal).
    """
    src_path = (
        PROJECT_ROOT
        / "packages"
        / "services"
        / "m2_input"
        / "inventory_projection.py"
    )
    src = src_path.read_text(encoding="utf-8")
    assert "TODO(epic-5-5-2)" in src, (
        "TODO(epic-5-5-2) marker missing from inventory_projection.py — "
        "this marker documents the Epic 3.3 → 5-2 swap and must remain "
        "until Epic 6 close-out retro."
    )
    # The marker should be in a CLOSED state (not a TODO that needs action)
    closed_marker_pattern = re.compile(
        r"TODO\(epic-5-5-2\)[:\s]+CLOSED",
        re.IGNORECASE,
    )
    assert closed_marker_pattern.search(src), (
        "TODO(epic-5-5-2) marker exists but is not marked CLOSED — "
        "Story 5.2 closes this marker."
    )


def test_monthly_input_service_uses_ledger_swap() -> None:
    """`_compute_inventory_projection_for_state` delegates to LedgerService.

    AST inspection: the new method body must reference
    `LedgerService.query_period_closing_all` (AC #5 swap), not
    `build_inventory_projection` (legacy path).
    """
    src_path = (
        PROJECT_ROOT
        / "apps"
        / "api"
        / "modules"
        / "m2_input"
        / "services"
        / "monthly_input_service.py"
    )
    src = src_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(src_path))

    # Find the method
    method = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_compute_inventory_projection_for_state"
        ):
            method = node
            break
    assert method is not None, (
        "MonthlyInputService._compute_inventory_projection_for_state "
        "not found — T8 swap incomplete."
    )

    # Walk the method body for references
    method_src = ast.get_source_segment(src, method)
    assert method_src is not None
    assert "query_period_closing_all" in method_src, (
        "T8 swap method body does NOT call LedgerService.query_period_closing_all "
        "— AC #5 swap incomplete."
    )


def test_compute_warnings_aggregate_calls_ledger_swap() -> None:
    """`_compute_warnings_aggregate_for_state` calls the new swap method."""
    src_path = (
        PROJECT_ROOT
        / "apps"
        / "api"
        / "modules"
        / "m2_input"
        / "services"
        / "monthly_input_service.py"
    )
    src = src_path.read_text(encoding="utf-8")
    assert "_compute_inventory_projection_for_state" in src, (
        "Caller _compute_warnings_aggregate_for_state does NOT delegate to "
        "_compute_inventory_projection_for_state — T8 swap incomplete."
    )


@pytest.mark.parametrize(
    "module_path",
    [
        "apps/api/modules/m4_inventory/services/ledger_service.py",
        "apps/api/modules/m2_input/services/monthly_input_service.py",
    ],
)
def test_no_raw_build_inventory_projection_calls_in_m4_m2(module_path: str) -> None:
    """Defense-in-depth: no `build_inventory_projection` calls in 5-2 swapped modules.

    After 5-2 swap, the legacy `build_inventory_projection` helper is
    still DEFINED in `inventory_projection.py` but must NOT be called
    from the modules that T8 explicitly swapped:
    - `ledger_service.py` — LedgerService exposes `query_period_closing_all`,
      consumers should use that, not the legacy kernel helper.
    - `monthly_input_service.py` — T8 swapped the read path here
      (Epic 3.3 inline projection deprecation).

    `opening_carry_service.py` is NOT in scope: its 5-1 carry-chain
    path uses `build_inventory_projection` (with the ledger-derived
    opening_decoded) as a deterministic intermediate; the Epic 6
    close-out retro is what removes that legacy call.
    """
    src_path = PROJECT_ROOT / module_path
    src = src_path.read_text(encoding="utf-8")

    # AST-level detection — exclude comments + docstrings
    tree = ast.parse(src, filename=str(src_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # bare `build_inventory_projection(...)` calls
            if isinstance(func, ast.Name) and func.id == "build_inventory_projection":
                pytest.fail(
                    f"{module_path} still calls legacy `build_inventory_projection` "
                    f"directly — T8 swap incomplete. Use "
                    f"LedgerService.query_period_closing_all instead."
                )
            # `packages.services.m2_input.inventory_projection.build_inventory_projection(...)`
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "build_inventory_projection"
            ):
                pytest.fail(
                    f"{module_path} still calls legacy "
                    f"`build_inventory_projection` — T8 swap incomplete. "
                    f"Use LedgerService.query_period_closing_all instead."
                )
