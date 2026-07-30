"""API-calls-only-ports boundary test.

AD-1, AD-11:
  - apps.api may import packages.cost_engine.ports (typed contracts).
  - apps.api MUST NOT import packages.cost_engine.core (engine internals).

The test parses every .py under apps/api/ and ensures no import walks into
packages.cost_engine.core. imports into packages.cost_engine.ports ARE allowed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
FORBIDDEN_PATTERNS = (
    "packages.cost_engine.core",
    "packages.cost_engine.adapters",
)


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _imports_in_file(path: Path) -> list[tuple[int, str]]:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:  # pragma: no cover
        return [(e.lineno or 0, f"<SYNTAX_ERROR:{e.msg}>")]
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            out.append((node.lineno, node.module))
    return out


@pytest.mark.architecture
def test_api_does_not_import_engine_core_or_adapters() -> None:
    """apps.api MUST call engine only through packages.cost_engine.ports (AD-11)."""
    assert API_ROOT.is_dir(), f"Missing API root: {API_ROOT}"

    violations: list[str] = []
    for py_file in _iter_python_files(API_ROOT):
        for lineno, module in _imports_in_file(py_file):
            for forbidden in FORBIDDEN_PATTERNS:
                if module == forbidden or module.startswith(forbidden + "."):
                    rel = py_file.relative_to(ROOT)
                    violations.append(
                        f"{rel}:{lineno} imports `{module}` — "
                        f"forbidden (AD-1/AD-11). Use `packages.cost_engine.ports` instead."
                    )

    assert not violations, (
        "apps/api must not import packages.cost_engine.core or .adapters directly.\n"
        "Use packages.cost_engine.ports (typed Protocol contracts) only.\n\n"
        + "\n".join(violations)
    )


@pytest.mark.architecture
def test_api_root_does_not_import_services() -> None:
    """apps.api MUST NOT import packages.services (wrong direction, AD-11).

    EXCEPTION (Story 1.1, 2026-07-29): `packages.services.m0_onboarding.*`
    is a SHARED DOMAIN-DATA module (Industry / MenuItem enums + pure
    functions) consumed by BOTH `apps.api` (Pydantic schemas) and the TS
    mirror at `apps/web/lib/menu-config.ts`. It contains NO orchestration,
    NO engine I/O, NO ports — it is structurally a `packages.ports`-style
    shared vocabulary, not an orchestration service like
    `calc_orchestrator` or `verification_runner`. Drift between Python and
    TS is caught by `tests/integration/test_menu_config_consistency.py`.

    Future shared-data additions should land under the same prefix
    (`packages.services.m<N>_<name>.*`) and update this allowlist alongside.
    """
    # Allowlist of shared-domain submodules under packages.services.
    # Add a new entry only after the new module passes the "no orchestration,
    # no engine I/O, no ports, only enums + pure functions" check.
    ALLOWED_SERVICE_SUBMODULES = frozenset(
        {
            "packages.services.m0_onboarding.industry_menu",
            "packages.services.m0_onboarding.settings_completion",
            "packages.services.m0_onboarding",
        }
    )

    violations: list[str] = []
    for py_file in _iter_python_files(API_ROOT):
        for lineno, module in _imports_in_file(py_file):
            if module == "packages.services" or module.startswith("packages.services."):
                if module in ALLOWED_SERVICE_SUBMODULES:
                    continue
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel}:{lineno} imports `{module}` — "
                    f"services are an internal layer; API talks to engine through ports."
                )
    assert not violations, "apps.api must not import packages.services directly.\n\n" + "\n".join(violations)


@pytest.mark.architecture
def test_apps_api_has_no_unintended_dunder_imports_at_module_load() -> None:
    """Smoke check: importing apps.api.main does not pull in packages.cost_engine.core.

    This is a runtime check, complementing the AST checks above. It validates
    that the actual import graph (not just static analysis) keeps the boundary.
    """
    import importlib
    import sys

    # Pre-clean any cached engine imports
    for mod_name in list(sys.modules):
        if mod_name.startswith("packages.cost_engine"):
            del sys.modules[mod_name]

    if "apps.api.main" in sys.modules:
        del sys.modules["apps.api.main"]

    # If FastAPI is unavailable (very minimal env), skip rather than fail
    try:
        importlib.import_module("apps.api.main")
    except ModuleNotFoundError as e:
        if "fastapi" in str(e):
            pytest.skip(f"FastAPI not installed in this environment: {e}")
        raise

    core_imports = [
        name for name in sys.modules
        if name.startswith("packages.cost_engine.core")
    ]
    # Note: ports are allowed; core is not.
    # If a developer (or AI) breaks the boundary, this list will be non-empty.
    assert not core_imports, (
        "Importing apps.api.main pulled in engine internals: " + ", ".join(core_imports)
    )
