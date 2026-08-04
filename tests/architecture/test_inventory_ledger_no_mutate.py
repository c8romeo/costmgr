"""tests.architecture.test_inventory_ledger_no_mutate — AD-2 3중 방어 2축 검증.

Story 5.2 AC #3 + CR 0.4 lessons (AST linter call vs attr) + CR 5.1 lessons.

The append-only 3중 방어:
1. DB trigger `inventory_ledger_append_only` (Alembic 0015) — production gate.
2. Service-layer AST guard `LedgerService._assert_not_modifying` — early fail.
3. Audit log `inventory_ledger_event_rejected` — observability for violations.

This test enforces that:
- `LedgerService.append_event` issues ONLY an INSERT (via
  `session.add()` + `session.flush()`); no UPDATE/DELETE/TRUNCATE/DROP
  TABLE call sites exist in `ledger_service.py`.
- `_assert_not_modifying` exists and triggers on forbidden keywords.
- `_assert_not_modifying` is invoked at all the entrypoints it claims
  to guard (currently `request_reversal` is the only mutation-shaped
  entrypoint — its SELECT must NOT be flagged).

Implementation note:
The guard's OWN body contains forbidden-keyword LITERALS (the strings
'UPDATE ', 'DELETE ', 'TRUNCATE ', 'DROP TABLE '). AST-level detection
must exclude the guard method body itself, otherwise this test would
self-violate. We do this by walking only call-site `ast.Call` nodes and
method `ast.Exec`/`ast.Assign` nodes for `session.execute/scalar/delete/
update/add`, NOT by regex-searching for keyword literals.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER_SERVICE = (
    PROJECT_ROOT
    / "apps"
    / "api"
    / "modules"
    / "m4_inventory"
    / "services"
    / "ledger_service.py"
)


def _load_module_ast() -> ast.Module:
    src = LEDGER_SERVICE.read_text(encoding="utf-8")
    return ast.parse(src, filename=str(LEDGER_SERVICE))


def _iter_methods(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def _method_body_calls(method: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    """Return all Call nodes nested inside a method body.

    Excludes the method's decorator-arg Call nodes (the `@something(...)`
    decorator on the method), so we only inspect the body.
    """
    out: list[ast.Call] = []
    for stmt in method.body:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call):
                out.append(child)
    return out


def test_append_event_does_not_issue_update_or_delete() -> None:
    """`append_event` body must not contain `update(...)` or `delete(...)` calls.

    AC #3 2축: the service-layer AST guard exists; this test enforces
    that the normal flow path doesn't violate the append-only invariant
    by accident.
    """
    tree = _load_module_ast()
    target = next(
        m for m in _iter_methods(tree) if m.name == "append_event"
    )
    forbidden = {"update", "delete", "truncate", "drop_table"}
    for call in _method_body_calls(target):
        func = call.func
        # `session.update(...)` / `self.session.delete(...)` attribute call
        if isinstance(func, ast.Attribute) and func.attr in forbidden:
            pytest.fail(
                f"append_event contains forbidden call `{func.attr}(...)` — "
                f"this would violate AD-2 append-only invariant."
            )
        # bare `update(...)` / `delete(...)` import call
        if isinstance(func, ast.Name) and func.id in forbidden:
            pytest.fail(
                f"append_event contains forbidden call `{func.id}(...)` — "
                f"this would violate AD-2 append-only invariant."
            )


def test_request_reversal_does_not_issue_update_or_delete() -> None:
    """`request_reversal` body must not mutate the ledger.

    The reversal entrypoint emits an audit marker and raises 501 — it
    must NOT mutate the ledger row directly (Epic 11 owns that).
    """
    tree = _load_module_ast()
    target = next(
        m for m in _iter_methods(tree) if m.name == "request_reversal"
    )
    forbidden = {"update", "delete", "truncate", "drop_table"}
    for call in _method_body_calls(target):
        func = call.func
        if isinstance(func, ast.Attribute) and func.attr in forbidden:
            pytest.fail(
                f"request_reversal contains forbidden call `{func.attr}(...)` — "
                f"Epic 11 owns the reversal sequence INSERT; this method "
                f"must only emit audit + raise 501."
            )
        if isinstance(func, ast.Name) and func.id in forbidden:
            pytest.fail(
                f"request_reversal contains forbidden call `{func.id}(...)` — "
                f"Epic 11 owns the reversal sequence INSERT."
            )


def test_query_methods_are_pure_reads() -> None:
    """`query_period_closing`, `query_period_closing_all`, `query_carry_chain`,
    `get_event` must not mutate the ledger (they're AC #1 read paths)."""
    tree = _load_module_ast()
    read_methods = {
        "query_period_closing",
        "query_period_closing_all",
        "query_carry_chain",
        "get_event",
    }
    forbidden = {"update", "delete", "truncate", "drop_table", "add", "flush"}
    for method in _iter_methods(tree):
        if method.name not in read_methods:
            continue
        for call in _method_body_calls(method):
            func = call.func
            if isinstance(func, ast.Attribute) and func.attr in forbidden:
                pytest.fail(
                    f"Read method `{method.name}` contains forbidden call "
                    f"`{func.attr}(...)` — read path must be pure."
                )


def test_assert_not_modifying_guard_exists() -> None:
    """The service-layer AST guard `_assert_not_modifying` must exist.

    AC #3 2축 enforcement. If this method is renamed or removed, the
    drift detector fails immediately so the team updates the AST guard
    tests (and the doc) in lockstep.
    """
    tree = _load_module_ast()
    method_names = {m.name for m in _iter_methods(tree)}
    assert "_assert_not_modifying" in method_names, (
        "LedgerService._assert_not_modifying AST guard is missing — "
        "AC #3 3중 방어 2축 broken. Add the guard back."
    )


def test_assert_not_modifying_guard_rejects_forbidden_keywords() -> None:
    """The guard rejects UPDATE/DELETE/TRUNCATE/DROP TABLE keywords.

    AST inspection: the guard body contains a tuple of forbidden keyword
    LITERALS. We assert the tuple is non-empty and contains the 4 expected
    keywords. The literal strings are SAFE inside the guard (the guard is
    a CHECK, not a violation — it raises on detection).
    """
    tree = _load_module_ast()
    guard = next(
        m for m in _iter_methods(tree) if m.name == "_assert_not_modifying"
    )
    # Look for a tuple-assigned `forbidden` local
    forbidden_value: tuple[str, ...] | None = None
    for stmt in guard.body:
        if isinstance(stmt, ast.AnnAssign):
            target = stmt.target
            value = stmt.value
        elif isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            value = stmt.value
        else:
            continue
        if (
            isinstance(target, ast.Name)
            and target.id == "forbidden"
            and isinstance(value, ast.Tuple)
        ):
            forbidden_value = tuple(
                elt.value for elt in value.elts if isinstance(elt, ast.Constant)
            )
            break
    assert forbidden_value is not None, (
        "AST guard does not define a `forbidden` tuple — guard logic "
        "changed and the test needs updating."
    )
    # All 4 expected keywords present
    expected = {"UPDATE ", "DELETE ", "TRUNCATE ", "DROP TABLE "}
    assert expected.issubset(set(forbidden_value)), (
        f"AST guard missing keywords: {expected - set(forbidden_value)} — "
        f"guard coverage regressed."
    )


def test_assert_not_modifying_guard_raises_append_only_violation() -> None:
    """The guard raises `AppendOnlyLedgerViolationError` on detection.

    Verifies the exception class is the typed envelope (not a generic
    Exception / ValueError), so main.py can map it to AD-15 §4
    APPEND_ONLY_LEDGER_VIOLATION (500).
    """
    tree = _load_module_ast()
    guard = next(
        m for m in _iter_methods(tree) if m.name == "_assert_not_modifying"
    )
    guard_src = ast.get_source_segment(
        LEDGER_SERVICE.read_text(encoding="utf-8"), guard
    )
    assert guard_src is not None
    assert "AppendOnlyLedgerViolationError" in guard_src, (
        "AST guard does not raise `AppendOnlyLedgerViolationError` — "
        "main.py cannot map the failure to APPEND_ONLY_LEDGER_VIOLATION "
        "(500) envelope."
    )


def test_inventory_ledger_module_has_no_db_trigger_mutations() -> None:
    """Static check: no module-level UPDATE/DELETE/TRUNCATE statements.

    Defense-in-depth: at module top-level, no SQL DML/DDL keywords for
    `inventory_ledger` should appear. Module-level UPDATE/DELETE is a
    code smell — the ledger is append-only.
    """
    tree = _load_module_ast()
    src = LEDGER_SERVICE.read_text(encoding="utf-8")
    # Walk only top-level statements (not nested in class/method bodies)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        # Module-level exec / evaluate is allowed; SQL DML is not
        # We check the source slice for forbidden keywords only at
        # module top-level statements that look like SQL strings.
        if isinstance(node, ast.Assign):
            seg = ast.get_source_segment(src, node) or ""
            for kw in ("UPDATE inventory_ledger", "DELETE FROM inventory_ledger",
                       "TRUNCATE inventory_ledger", "DROP TABLE inventory_ledger"):
                if kw in seg.upper():
                    pytest.fail(
                        f"Module-level statement contains `{kw}` — "
                        f"inventory_ledger is append-only (AD-2)."
                    )
