"""tests.integration.test_m7_simulation_projection_no_db_writes — Story 7.2.

CR 1.1 honest-DEFER discipline — projection simulation is a read-only operation.
Verified by:
- No `audit_logs` rows emitted after projection.
- No `fiscal_period_snapshots` / `monthly_input_periods` UPDATE queries.
- Service layer does NOT import `emit_audit_typed` (audit-first guard).

This is a static-import-based verifier (no DB transaction needed).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Story 7.2 files that MUST remain read-only (no audit emit).
PROJECTION_FILES = [
    ROOT
    / "apps"
    / "api"
    / "modules"
    / "m7_simulation"
    / "services"
    / "projection_service.py",
    ROOT / "apps" / "api" / "modules" / "m7_simulation" / "handlers.py",
    ROOT / "packages" / "services" / "m7_simulation" / "projection_serializers.py",
    ROOT / "packages" / "services" / "m7_simulation" / "projection_pdf_helpers.py",
    ROOT / "packages" / "cost_engine" / "projection.py",
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


@pytest.mark.parametrize(
    "path", PROJECTION_FILES, ids=lambda p: str(p.relative_to(ROOT))
)
def test_projection_files_exist(path: Path) -> None:
    """All 7-2 service/helper files MUST exist."""
    assert path.is_file(), f"Story 7.2 file missing: {path}"


def test_projection_service_does_not_import_audit_emit() -> None:
    """ProjectionService MUST NOT import `emit_audit_typed` (read-only)."""
    service_file = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m7_simulation"
        / "services"
        / "projection_service.py"
    )
    imports = _imports_in_file(service_file)
    forbidden = {
        "emit_audit_typed",
        "emit_audit",
        "audit_action.emit_audit_typed",
    }
    has_audit_import = any(any(f in imp for f in forbidden) for imp in imports)
    assert not has_audit_import, (
        "ProjectionService imports audit emit (CR 1.1 violation — "
        "projection is read-only, no audit_logs row expected)"
    )


def test_projection_handlers_does_not_import_db_writes() -> None:
    """Projection handlers MUST NOT import DB write modules directly."""
    handlers_file = (
        ROOT / "apps" / "api" / "modules" / "m7_simulation" / "handlers.py"
    )
    src = handlers_file.read_text(encoding="utf-8")
    forbidden_patterns = [
        "session.add",
        "session.commit",
        "session.flush",
        ".execute(update",
        ".execute(insert",
        ".execute(delete",
    ]
    violations = [p for p in forbidden_patterns if p in src]
    assert not violations, (
        f"Projection handlers contain DB write patterns: {violations}"
    )


def test_projection_serializers_does_not_import_db() -> None:
    """7-2 projection serializers MUST NOT import sqlalchemy / DB modules."""
    serializer_file = (
        ROOT / "packages" / "services" / "m7_simulation" / "projection_serializers.py"
    )
    imports = _imports_in_file(serializer_file)
    forbidden_prefixes = (
        "sqlalchemy",
        "psycopg",
        "asyncpg",
        "apps.api.core.db_models",
    )
    violations = [
        imp for imp in imports if any(imp.startswith(f) for f in forbidden_prefixes)
    ]
    assert not violations, (
        f"m7_simulation projection_serializers import DB modules: {violations}"
    )


def test_projection_pdf_helpers_is_pure() -> None:
    """7-2 projection_pdf_helpers MUST be pure (no I/O, no DB)."""
    pdf_file = (
        ROOT
        / "packages"
        / "services"
        / "m7_simulation"
        / "projection_pdf_helpers.py"
    )
    imports = _imports_in_file(pdf_file)
    forbidden = {"sqlalchemy", "psycopg", "asyncpg", "requests", "httpx", "fastapi"}
    violations = [imp for imp in imports if any(imp == f for f in forbidden)]
    assert not violations, f"m7_simulation projection_pdf_helpers import I/O: {violations}"


def test_projection_capability_in_capability_py() -> None:
    """Capability.CVP_SIMULATION MUST be registered in apps/api/core/capability.py
    (reused — no NEW capability for projection)."""
    capability_file = ROOT / "apps" / "api" / "core" / "capability.py"
    src = capability_file.read_text(encoding="utf-8")
    assert "CVP_SIMULATION" in src, "Capability.CVP_SIMULATION missing from capability.py"
    assert "cvp_simulation" in src, "CVP_SIMULATION enum value missing"
