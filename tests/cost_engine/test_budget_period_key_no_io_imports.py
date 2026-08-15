"""AST-based forbidden-import guard for Story 8.1 budget_period_key.py.

AD-1, AD-5, AD-11 enforcement — Story 8.1 specific whitelist.

This test parses `packages/cost_engine/budget_period_key.py` and asserts that
only the 8-1 whitelisted stdlib modules are imported. Violations produce a
clear file:line:module message that CI lint surfaces as a build failure.

Allowed (Story 8.1 budget_period_key.py whitelist):
  - hashlib (sha256 digest)
  - re (regex pattern matching — AD-24 virtual period key)
  - dataclasses (frozen=True, slots=True)
  - typing (Final, Optional)

Forbidden (8-1 explicitly disallows):
  - sqlalchemy, fastapi, starlette, requests, httpx
  - psycopg, asyncpg
  - time, datetime, random, os, socket, subprocess
  - pydantic (AD-5: no Pydantic inside engine — allowed in adapters)
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TARGET_FILE = ROOT / "packages" / "cost_engine" / "budget_period_key.py"

STORY_8_1_ALLOWED_TOP_LEVEL: frozenset[str] = frozenset(
    {"__future__", "hashlib", "re", "dataclasses", "typing"}
)

STORY_8_1_FORBIDDEN_TOP_LEVEL: frozenset[str] = frozenset(
    {
        "sqlalchemy",
        "fastapi",
        "starlette",
        "requests",
        "httpx",
        "psycopg",
        "asyncpg",
        "time",
        "datetime",
        "random",
        "os",
        "socket",
        "subprocess",
        "pydantic",
        "json",
        "urllib",
    }
)


def _imports_in_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (line_no, top_level_module) for every import."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                found.append((node.lineno, top))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = node.module.split(".")[0]
            found.append((node.lineno, top))
    return found


@pytest.mark.engine
def test_budget_period_key_file_exists() -> None:
    """The budget_period_key.py file MUST exist at the expected path."""
    assert TARGET_FILE.is_file(), (
        f"Story 8.1 pure kernel missing: {TARGET_FILE}"
    )


@pytest.mark.engine
def test_budget_period_key_whitelist_only() -> None:
    """Only 8-1 whitelisted stdlib modules may be imported."""
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top not in STORY_8_1_ALLOWED_TOP_LEVEL:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` "
                f"— only {sorted(STORY_8_1_ALLOWED_TOP_LEVEL)} allowed (Story 8.1 AD-5)"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_budget_period_key_no_forbidden_imports() -> None:
    """Explicit forbidden-import check (defense-in-depth, 8-1 specific)."""
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top in STORY_8_1_FORBIDDEN_TOP_LEVEL:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports forbidden `{top}` "
                f"(Story 8.1 AD-5 purity violation)"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_budget_period_key_no_packages_services_or_apps_imports() -> None:
    """budget_period_key.py must NOT import packages.services or apps.* (AD-11)."""
    imports = _imports_in_file(TARGET_FILE)
    forbidden_prefixes = ("packages.services", "apps.")
    violations: list[str] = []
    for lineno, top in imports:
        for prefix in forbidden_prefixes:
            if top.startswith(prefix):
                violations.append(
                    f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` — "
                    f"engine MUST NOT depend on services/apps (AD-11 layer rule)"
                )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_budget_period_key_no_external_dependencies() -> None:
    """budget_period_key.py must NOT import any non-stdlib package."""
    stdlib_whitelist = STORY_8_1_ALLOWED_TOP_LEVEL
    imports = _imports_in_file(TARGET_FILE)
    # Anything not in stdlib_whitelist is suspect — engine is stdlib-only.
    violations: list[str] = []
    for lineno, top in imports:
        if top not in stdlib_whitelist:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` — "
                f"not in 8-1 whitelist (stdlib-only)"
            )
    assert not violations, "\n".join(violations)
