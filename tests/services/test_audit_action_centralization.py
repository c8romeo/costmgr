"""A5 audit-action centralization drift detector (F-6 review).

Story 4.3 (Epic 4 close-out retro A5 spike Phase 1+2) — Drift guard.

CR 1.1 lesson, 4-epic recurrence pattern: audit log call sites
(emit_audit, _emit_calc_log, _write_verification_log) drifted between
str-literal actions and the polymorphic destination-table routing.
A5 spike introduced `apps/api/core/audit_action.py` (ActionClass enum +
AuditAction Literal union + emit_audit_typed) and migrated 17+ call
sites to use it.

This test pins the drift in a forward direction: any future code path
that calls the legacy `emit_audit()` / `logs.append()` pattern (instead
of `emit_audit_typed()` / typed registry helpers) FAILS the gate.

Per AD-11: drift detector lives in `tests/services/` — cross-module
architecture gate, not a single rule test.

Per CR 1.1: zero-drift enforcement. If this test fails, the contributor
must (a) add a new entry to `apps/api/core/audit_action.py` registry,
then (b) update the call site to use it. Direct str-literal action
strings forbidden.

Excluded: this very file (test_audit_action_centralization.py) +
apps/api/core/audit_action.py (the SSOT file itself).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Modules / packages to scan for legacy call patterns.
_SCAN_ROOTS: tuple[str, ...] = (
    "apps/api/modules/",
    "apps/api/jobs/",
)

# Files where `emit_audit(` is LEGITIMATE (the SSOT + adapter imports).
_EXCLUDE_FILES: frozenset[str] = frozenset(
    {
        # SSOT itself
        "apps/api/core/audit_action.py",
        # This test
        "tests/services/test_audit_action_centralization.py",
    }
)

# Forbidden legacy patterns:
#   - `emit_audit(` followed by a non-typed call (excluding import lines)
#   - `from apps.api.core.audit_action import emit_audit` (must use the typed variant only)
# We only flag actual call sites, not imports.
_LEGACY_CALL_RE: re.Pattern[str] = re.compile(
    r"^\s*emit_audit\s*\(", re.MULTILINE
)


@pytest.mark.engine
def test_no_legacy_emit_audit_call_sites() -> None:
    """A5 drift guard: no direct `emit_audit(` calls outside audit_action.py.

    Scans all `.py` files under `apps/api/modules/` and `apps/api/jobs/`
    for legacy `emit_audit(` patterns. If any are found, this is the
    5th epic of CR 1.1 drift — must fix by migrating to the typed
    registry (ActionClass + AuditAction enum).

    Excludes:
    - `apps/api/core/audit_action.py` (the SSOT itself)
    - This test file
    """
    repo_root = Path(__file__).resolve().parents[2]
    violations: list[str] = []

    for scan_root in _SCAN_ROOTS:
        root_path = repo_root / scan_root
        if not root_path.exists():
            continue
        for py_file in root_path.rglob("*.py"):
            rel = py_file.relative_to(repo_root).as_posix()
            if rel in _EXCLUDE_FILES:
                continue
            content = py_file.read_text(encoding="utf-8")
            if _LEGACY_CALL_RE.search(content):
                violations.append(rel)

    assert not violations, (
        "A5 drift: legacy `emit_audit(` call(s) detected. "
        "Migrate to emit_audit_typed() — see apps/api/core/audit_action.py. "
        "Offending files:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


@pytest.mark.engine
def test_audit_action_module_exports_emit_audit_typed() -> None:
    """A5 SSOT: `emit_audit_typed` symbol must exist in audit_action.py.

    If a contributor replaces or removes the typed wrapper, this gate
    fires. Mirrors CR 1.1 audit-first invariant.
    """
    from apps.api.core import audit_action

    assert hasattr(audit_action, "emit_audit_typed"), (
        "audit_action.py missing `emit_audit_typed` — A5 SSOT broken."
    )
    assert hasattr(audit_action, "ActionClass"), (
        "audit_action.py missing `ActionClass` enum — A5 SSOT broken."
    )
    assert hasattr(audit_action, "AuditAction"), (
        "audit_action.py missing `AuditAction` Literal — A5 SSOT broken."
    )
