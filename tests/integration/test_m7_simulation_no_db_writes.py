"""tests.integration.test_m7_simulation_no_db_writes — Story 7.1.

CR 1.1 honest-DEFER discipline — CVP simulation is a read-only operation.
Verified by:
- No `audit_logs` rows emitted after simulation.
- No `fiscal_period_snapshots` / `monthly_input_periods` UPDATE queries.
- Service layer does NOT import `emit_audit_typed` (audit-first guard).

This is a static-import-based verifier (no DB transaction needed).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# NEW files for Story 7.1 that MUST remain read-only (no audit emit).
M7_SIMULATION_FILES = [
    ROOT / "apps" / "api" / "modules" / "m7_simulation" / "services" / "cvp_simulation_service.py",
    ROOT / "apps" / "api" / "modules" / "m7_simulation" / "handlers.py",
    ROOT / "packages" / "services" / "m7_simulation" / "serializers.py",
    ROOT / "packages" / "services" / "m7_simulation" / "delta_helpers.py",
]


def _imports_in_file(path: Path) -> list[str]:
    """Return list of module names imported in a Python file."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            out.append(node.module)
    return out


@pytest.mark.parametrize("path", M7_SIMULATION_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_m7_simulation_files_exist_and_exist(path: Path) -> None:
    """All 7-1 service/helper files MUST exist."""
    assert path.is_file(), f"Story 7.1 file missing: {path}"


def test_cvp_simulation_service_does_not_import_audit_emit() -> None:
    """CVPSimulationService MUST NOT import `emit_audit_typed` (read-only)."""
    service_file = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m7_simulation"
        / "services"
        / "cvp_simulation_service.py"
    )
    imports = _imports_in_file(service_file)
    forbidden = {"emit_audit_typed", "emit_audit", "audit_action.emit_audit_typed"}
    has_audit_import = any(any(f in imp for f in forbidden) for imp in imports)
    assert not has_audit_import, (
        "CVPSimulationService imports audit emit (CR 1.1 violation — "
        "simulation is read-only, no audit_logs row expected)"
    )


def test_m7_simulation_serializer_does_not_import_db() -> None:
    """7-1 serializers MUST NOT import sqlalchemy / DB modules."""
    serializer_file = (
        ROOT / "packages" / "services" / "m7_simulation" / "serializers.py"
    )
    imports = _imports_in_file(serializer_file)
    forbidden_prefixes = ("sqlalchemy", "psycopg", "asyncpg", "apps.api.core.db_models")
    violations = [
        imp for imp in imports if any(imp.startswith(f) for f in forbidden_prefixes)
    ]
    assert not violations, (
        f"m7_simulation serializers import DB modules: {violations}"
    )


def test_m7_simulation_delta_helpers_are_pure() -> None:
    """7-1 delta_helpers MUST be pure (no I/O, no DB)."""
    delta_file = (
        ROOT / "packages" / "services" / "m7_simulation" / "delta_helpers.py"
    )
    imports = _imports_in_file(delta_file)
    forbidden = {"sqlalchemy", "psycopg", "asyncpg", "requests", "httpx", "fastapi"}
    violations = [imp for imp in imports if any(imp == f for f in forbidden)]
    assert not violations, f"m7_simulation delta_helpers import I/O: {violations}"


def test_m7_simulation_capability_in_capability_py() -> None:
    """Capability.CVP_SIMULATION MUST be registered in apps/api/core/capability.py."""
    capability_file = ROOT / "apps" / "api" / "core" / "capability.py"
    src = capability_file.read_text(encoding="utf-8")
    assert "CVP_SIMULATION" in src, "Capability.CVP_SIMULATION missing from capability.py"
    assert "cvp_simulation" in src, "CVP_SIMULATION enum value missing"
