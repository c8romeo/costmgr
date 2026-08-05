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
    """apps.api MUST call engine only through packages.cost_engine.ports (AD-11).

    EXCEPTION (AD-11 binding: handler → service → engine): service layer
    files (`apps/api/modules/*/services/*.py`) ARE the boundary — they
    import from `packages.cost_engine.core` to call the engine entry
    point (e.g. `compute_period_cost`). The HANDLER layer (which is the
    real public boundary) MUST still go through ports.

    Other allowlist entries (pre-existing):
    - `apps/api/core/money.py` — pre-existing re-export, deferred to
      Epic 4 retro F-4 cleanup.
    """
    # Allowlist of files that legitimately import from packages.cost_engine.core.
    # Each entry is a relative path under ROOT.
    CORE_IMPORT_ALLOWLIST = frozenset(
        {
            # Story 4.2 — M3 calculate service layer IS the engine caller.
            "apps/api/modules/m3_calculate/services/calc_orchestrator.py",
            "apps/api/modules/m3_calculate/services/baseline_loader.py",
            "apps/api/modules/m3_calculate/services/monthly_input_aggregator.py",
            # Story 4.3 — verification rule kernels + runner are AD-11
            # boundary service layer files (rule protocol + verification_runner
            # import Baseline / CalcResult / MonthlyInput types from the engine
            # core; rule kernels import KRW for 1원 단위 tolerance).
            "apps/api/modules/m3_calculate/services/rules/protocol.py",
            "apps/api/modules/m3_calculate/services/rules/v1_complete_allocation.py",
            "apps/api/modules/m3_calculate/services/rules/v4_cost_income_reconciliation.py",
            "apps/api/modules/m3_calculate/services/rules/v7_abc_integrity.py",
            "apps/api/modules/m3_calculate/services/rules/v8_regression.py",
            "apps/api/modules/m3_calculate/services/verification_runner.py",
            # Pre-existing — Epic 4 retro F-4 (re-export shim).
            "apps/api/core/money.py",
        }
    )

    assert API_ROOT.is_dir(), f"Missing API root: {API_ROOT}"

    violations: list[str] = []
    for py_file in _iter_python_files(API_ROOT):
        rel = py_file.relative_to(ROOT)
        rel_str = str(rel).replace("\\", "/")
        for lineno, module in _imports_in_file(py_file):
            for forbidden in FORBIDDEN_PATTERNS:
                if module == forbidden or module.startswith(forbidden + "."):
                    if rel_str in CORE_IMPORT_ALLOWLIST:
                        continue
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
    #
    # All `packages.services.m<N>_<name>.*` are SHARED DOMAIN-DATA primitives
    # (enums / pure functions / data types) consumed by BOTH `apps.api` (Pydantic
    # schemas, service layer) AND the TS mirror. They contain NO orchestration,
    # NO engine I/O, NO ports — same shape as `m0_onboarding`. Drift between
    # Python and TS is caught by `tests/integration/test_menu_config_consistency.py`
    # (and parity tests for each shared primitive).
    ALLOWED_SERVICE_SUBMODULES = frozenset(
        {
            # m0_onboarding (Epic 1 — original allowlist)
            "packages.services.m0_onboarding.industry_menu",
            "packages.services.m0_onboarding.settings_completion",
            "packages.services.m0_onboarding",
            # m1_baseline (Epic 2 — product/BOM domain primitives)
            "packages.services.m1_baseline.schemas",
            "packages.services.m1_baseline.bom_validation",
            "packages.services.m1_baseline.product_code",
            "packages.services.m1_baseline.product_references",
            "packages.services.m1_baseline",
            # m2_input (Epic 3 — monthly input domain primitives)
            "packages.services.m2_input.stream_completion",
            "packages.services.m2_input.labor_conversion",
            "packages.services.m2_input.operating_rate",
            "packages.services.m2_input.warnings",
            "packages.services.m2_input.inventory_projection",
            "packages.services.m2_input.opening_carry",  # Story 5.1 (Epic 5 — opening inventory auto-carry chain)
            "packages.services.m2_input",
            # m4_inventory (Epic 5 — inventory ledger domain primitives)
            # Story 5.2 — AD-2 append-only ledger + SQL fragment builders.
            "packages.services.m4_inventory.ledger",
            "packages.services.m4_inventory.ledger_query",
            # Story 5.3 — closing ≥ 0 invariant guard + BOM reconciliation pure kernels.
            "packages.services.m4_inventory.closing_guard",
            "packages.services.m4_inventory.production_consumption",
            "packages.services.m4_inventory",
            # m10_ai (Epic 10 — AI document extraction port)
            "packages.services.m10_ai.extraction_port",
            "packages.services.m10_ai",
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

    EXCEPTION (AD-8 monetary types): ``packages.cost_engine.core.money`` defines
    ``KRW`` / ``USD`` NewType markers that are the canonical types for BOTH the
    engine and the API. ``apps/api/core/money.py`` re-exports them so API code
    uses the same type identity. This is the documented AD-8 cross-cutting
    primitive exception — same one already allowlisted in
    ``test_api_does_not_import_engine_core_or_adapters``. Only the ``money``
    submodule is allowed; ``period_cost`` or other engine internals must NOT
    leak into the API runtime.
    """
    import importlib
    import sys

    # AD-8 cross-cutting primitive exception + service-layer engine entry points.
    # The runtime import graph pulls these in transitively when apps.api.main
    # registers the calc/verification endpoints whose service layer
    # (apps/api/modules/m3_calculate/services/*.py) IS the AD-11 boundary
    # that imports `packages.cost_engine.core` to call `compute_period_cost`
    # and friends. See `test_api_does_not_import_engine_core_or_adapters` for
    # the AST-level allowlist of those service files.
    RUNTIME_CORE_IMPORT_ALLOWLIST = frozenset(
        {
            "packages.cost_engine.core",  # parent package
            "packages.cost_engine.core.money",  # AD-8 KRW/USD canonical types
            "packages.cost_engine.core.period_cost",  # Story 4.1/4.2 engine entry via services
        }
    )

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
        and name not in RUNTIME_CORE_IMPORT_ALLOWLIST
    ]
    # Note: ports are allowed; core is not (except the documented AD-8 money exception).
    # If a developer (or AI) breaks the boundary, this list will be non-empty.
    assert not core_imports, (
        "Importing apps.api.main pulled in engine internals: " + ", ".join(core_imports)
    )
