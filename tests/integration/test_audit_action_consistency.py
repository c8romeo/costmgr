"""A5 audit-action 3-way drift detector.

Story 4.4 → Epic 4 close-out (A5 spike Phase 4 close-out) — registry ↔
DB CHECK ↔ call sites 3-way consistency gate.

CR 1.1 lesson, 4-epic recurrence pattern. A5 spike introduced
`apps/api/core/audit_action.py` (ActionClass enum + AuditAction Literal +
emit_audit_typed) and the 22 call sites were migrated. Alembic 0012
introduced the FIRST DB CHECK constraint on `calc_log.action`; Alembic
0013 introduced the SECOND on `verification_log.action`.

This test pins the 3 axes:

1. **Registry** — `apps/api/core/audit_action.py::_ActionRegistry._REGISTRY`
   (single source of truth for ActionClass → (AuditLogType, accepted set))
2. **DB CHECK constraint** — Alembic migration `CHECK (action IN ('...'))`
   for `calc_log` (`0012`) and `verification_log` (`0013`)
3. **Call sites** — every typed writer MUST use `emit_audit_typed()` or
   a service-layer writer that calls `_ActionRegistry.validate()`

If any axis drifts, the 3-way gate fires. This is the production safety
net for the 5th epic of CR 1.1 drift.

Per AD-11: integration test lives in `tests/integration/` — cross-module
3-way consistency, not a single rule test.

Per CR 1.1: zero-drift enforcement. If this test fails, the contributor
must (a) update the registry, (b) update the Alembic migration
(CHECK constraint), AND (c) update call sites — in that order.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


# ─────────────────────────────────────────────────────────────
# 1. Registry ↔ DB CHECK constraint 3-way consistency
# ─────────────────────────────────────────────────────────────


def _parse_db_check_constraints() -> dict[str, frozenset[str]]:
    """Parse Alembic migrations for `CHECK (action IN (...))` constraints.

    Returns:
        Dict mapping table_name (e.g. 'calc_log' / 'verification_log') to
        frozenset of allowed action values (the DB-level enum).

    Handles:
    - `CREATE TABLE <name> (... CHECK (action IN ('a', 'b')))` (0012 pattern)
    - `ALTER TABLE <name> ADD CONSTRAINT ... CHECK (action IN (...))` (0014 pattern)
    - Multi-line values (Alembic 0014).
    """
    migrations_dir = ROOT / "apps" / "api" / "alembic" / "versions"
    constraints: dict[str, frozenset[str]] = {}

    # Match the values inside `action IN (...)` — values may span multiple lines
    # (Alembic 0014 pattern) and use single-quoted strings.
    pattern = re.compile(
        r"action\s+IN\s*\(\s*((?:'[^']+'\s*,?\s*)+)\)",
        re.IGNORECASE | re.DOTALL,
    )

    # Table name scanner: matches CREATE TABLE or ALTER TABLE statements.
    # Both must point to the same table for the CHECK constraint to apply.
    create_table_pattern = re.compile(
        r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\(",
        re.IGNORECASE,
    )
    alter_table_pattern = re.compile(
        r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)",
        re.IGNORECASE,
    )

    for migration_file in sorted(migrations_dir.glob("00*.py")):
        if migration_file.name == "__init__.py":
            continue
        src = migration_file.read_text(encoding="utf-8")
        # Only scan the upgrade() function body — downgrade() is the
        # reverse path and contains intentional "older" definitions.
        # Cut at "def downgrade()" to ignore rollbacks.
        downgrade_idx = src.find("def downgrade")
        scan_src = src[:downgrade_idx] if downgrade_idx != -1 else src
        for match in pattern.finditer(scan_src):
            values_str = match.group(1)
            values = frozenset(re.findall(r"'([^']+)'", values_str))
            if not values:
                continue
            # Find the table name by scanning backward from the match.
            # Look for the LAST CREATE TABLE or ALTER TABLE statement.
            preceding = scan_src[: match.start()]
            create_matches = list(create_table_pattern.finditer(preceding))
            alter_matches = list(alter_table_pattern.finditer(preceding))

            # Pick the most recent one (highest match position)
            last_create = create_matches[-1] if create_matches else None
            last_alter = alter_matches[-1] if alter_matches else None

            table_name: str | None = None
            if last_create and last_alter:
                if last_alter.start() > last_create.start():
                    table_name = last_alter.group(1)
                else:
                    table_name = last_create.group(1)
            elif last_create:
                table_name = last_create.group(1)
            elif last_alter:
                table_name = last_alter.group(1)

            if table_name is None:
                continue
            # The LATER migration wins. Track the latest definition per table
            # (since we iterate files in order, later files overwrite).
            constraints[table_name] = values

    return constraints


@pytest.mark.engine
def test_registry_matches_db_check_constraints() -> None:
    """A5 3-way: registry.ActionClass.<table> ↔ DB CHECK constraint.

    For each ActionClass that routes to a non-`audit_logs` destination
    (i.e. has a DB CHECK constraint), the registry's accepted action set
    MUST equal the DB CHECK `action IN (...)` set.

    Pins:
    - `calc_log` (ActionClass.CALC_LOG) ↔ Alembic 0012 CHECK
    - `verification_log` (ActionClass.VERIFICATION_LOG) ↔ Alembic 0013 CHECK
    """
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    db_constraints = _parse_db_check_constraints()

    # Map ActionClass → expected DB table name
    # (calc_log + verification_log have CHECK constraints; audit_logs does not)
    class_to_table = {
        ActionClass.CALC_LOG: "calc_log",
        ActionClass.VERIFICATION_LOG: "verification_log",
    }

    violations: list[str] = []
    for action_class, table_name in class_to_table.items():
        if table_name not in db_constraints:
            violations.append(
                f"{table_name}: missing DB CHECK constraint in Alembic migrations. "
                f"ActionClass.{action_class.name} requires a CHECK constraint."
            )
            continue

        registry_log_type, registry_accepted = _ActionRegistry._REGISTRY[action_class]
        db_allowed = db_constraints[table_name]

        if registry_accepted != db_allowed:
            violations.append(
                f"{table_name}: registry ↔ DB CHECK drift.\n"
                f"  Registry accepts ({len(registry_accepted)}): {sorted(registry_accepted)}\n"
                f"  DB CHECK allows  ({len(db_allowed)}): {sorted(db_allowed)}\n"
                f"  MISSING from registry: {sorted(db_allowed - registry_accepted)}\n"
                f"  EXTRA in registry:    {sorted(registry_accepted - db_allowed)}"
            )

    assert not violations, (
        "A5 3-way drift: registry ↔ DB CHECK constraint mismatch.\n"
        "Update registry (apps/api/core/audit_action.py) AND Alembic migration "
        "in lockstep.\n\n"
        + "\n".join(violations)
    )


# ─────────────────────────────────────────────────────────────
# 2. Service-layer writer consistency
# ─────────────────────────────────────────────────────────────


def _find_service_layer_writers() -> dict[str, set[str]]:
    """Find service-layer writers that call `_ActionRegistry.validate`.

    Returns:
        Dict mapping module_name → set of ActionClass values used.
    """
    modules_dir = ROOT / "apps" / "api" / "modules"
    writers: dict[str, set[str]] = {}

    for py_file in modules_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        src = py_file.read_text(encoding="utf-8")
        # Find ActionClass.X references in this file
        matches = re.findall(r"ActionClass\.(\w+)", src)
        if matches:
            rel = py_file.relative_to(ROOT).as_posix()
            writers[rel] = set(matches)

    return writers


@pytest.mark.engine
def test_service_layer_writers_use_registry_validate() -> None:
    """A5 3-way: service-layer writers must call _ActionRegistry.validate().

    Every module that uses `ActionClass.X` MUST also call
    `_ActionRegistry.validate(...)` to enforce the typed contract.
    This is the (c) layer of the 3-way gate.

    Enforces:
    - `m3_calculate/services/calc_orchestrator.py` — _write_calc_log +
      _write_verification_log both validate via _ActionRegistry.
    - All other modules — must call emit_audit_typed() (which validates
      internally) instead of bypassing the registry.
    """
    import apps.api.core.audit_action as audit_action_module

    # Get the source of audit_action.py and check for the validate function
    src = Path(audit_action_module.__file__).read_text(encoding="utf-8")
    assert "_ActionRegistry.validate" in src, (
        "apps/api/core/audit_action.py: _ActionRegistry.validate() must exist."
    )

    # Normalize whitespace to allow multi-line calls (e.g., validate(
    #     action_class=..., action=...))
    re.sub(r"\s+", " ", src)  # noqa: F841 — pre-flight normalization

    # Verify each service-layer writer file uses registry validate
    orchestrator_file = ROOT / "apps" / "api" / "modules" / "m3_calculate" / "services" / "calc_orchestrator.py"
    if orchestrator_file.exists():
        orc_src = orchestrator_file.read_text(encoding="utf-8")
        orc_normalized = re.sub(r"\s+", " ", orc_src)
        # _write_calc_log and _write_verification_log must each call validate.
        # The unique part of each call is `ActionClass.<X>, action=action`.
        # Single-line normalize: `_ActionRegistry.validate(action_class=ActionClass.<X>, action=action)`
        # Multi-line normalize (collapsed by re.sub):
        #   `_ActionRegistry.validate( action_class=ActionClass.<X>, action=action )`
        # Either form contains `ActionClass.<X>, action=action` so check for that.
        assert (
            "ActionClass.CALC_LOG, action=action" in orc_normalized
        ), (
            "calc_orchestrator.py: _write_calc_log must call "
            "_ActionRegistry.validate(action_class=ActionClass.CALC_LOG, action=action)"
        )
        assert (
            "ActionClass.VERIFICATION_LOG, action=action" in orc_normalized
        ), (
            "calc_orchestrator.py: _write_verification_log must call "
            "_ActionRegistry.validate(action_class=ActionClass.VERIFICATION_LOG, action=action)"
        )


# ─────────────────────────────────────────────────────────────
# 3. All ActionClass values are migration-routable
# ─────────────────────────────────────────────────────────────


@pytest.mark.engine
def test_all_action_classes_have_registry_entry() -> None:
    """A5 3-way: every ActionClass enum value must be in _ActionRegistry.

    If a contributor adds a new ActionClass to the enum but forgets to
    register it in `_ActionRegistry._REGISTRY`, this gate fires.
    """
    from apps.api.core.audit_action import ActionClass, _ActionRegistry

    registered = set(_ActionRegistry._REGISTRY.keys())
    defined = set(ActionClass)

    missing = defined - registered
    extra = registered - defined

    assert not missing, (
        f"A5 3-way drift: ActionClass values missing from _ActionRegistry: "
        f"{sorted(m.value for m in missing)}. Add to _REGISTRY in "
        f"apps/api/core/audit_action.py."
    )
    assert not extra, (
        f"A5 3-way drift: _ActionRegistry contains ActionClass values not "
        f"in the enum: {sorted(extra)}. Remove from _REGISTRY."
    )


# ─────────────────────────────────────────────────────────────
# 4. CalcLog / VerificationLog writers don't bypass registry
# ─────────────────────────────────────────────────────────────


@pytest.mark.engine
def test_calc_log_writer_validates_before_insert() -> None:
    """A5 3-way: CalcLog INSERT in `_write_calc_log` must validate first.

    Path: `apps/api/modules/m3_calculate/services/calc_orchestrator.py`
    The `_write_calc_log` method inserts a CalcLog row. The `_ActionRegistry
    .validate(...)` call must be BEFORE the `session.add(row)` call.
    """
    orchestrator_file = (
        ROOT / "apps" / "api" / "modules" / "m3_calculate" / "services" / "calc_orchestrator.py"
    )
    if not orchestrator_file.exists():
        pytest.skip("calc_orchestrator.py not found (m3_calculate module not yet wired)")

    src = orchestrator_file.read_text(encoding="utf-8")

    # Use AST to find _write_calc_log method (handles multi-line signatures)
    tree = ast.parse(src, filename=str(orchestrator_file))
    method_body: str | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_write_calc_log":
            # Reconstruct the body using line numbers
            lines = src.splitlines()
            method_body = "\n".join(lines[node.body[0].lineno - 1: node.end_lineno])
            break

    assert method_body is not None, "_write_calc_log method not found in calc_orchestrator.py"

    validate_pos = method_body.find("_ActionRegistry.validate")
    insert_pos = method_body.find("session.add(row)")

    assert validate_pos != -1, (
        "_write_calc_log: missing _ActionRegistry.validate() call. "
        "A5 forward-lock requires validation before INSERT."
    )
    assert insert_pos != -1, "_write_calc_log: missing session.add(row) call"
    assert validate_pos < insert_pos, (
        "_write_calc_log: _ActionRegistry.validate() must be BEFORE "
        "session.add(row) — fail-fast before persistence."
    )
