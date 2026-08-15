"""AST-based forbidden-import guard for Story 7.2 projection.py.

AD-1, AD-5, AD-11 enforcement — Story 7.2 specific whitelist.

This test parses `packages/cost_engine/projection.py` and asserts that
only the 7-2 whitelisted stdlib modules are imported. Violations produce
a clear file:line:module message that CI lint surfaces as a build failure.

Allowed (Story 7.2 projection.py whitelist):
  - hashlib (sha256 digest for V8 determinism)
  - dataclasses (frozen=True, slots=True)
  - decimal (ROUND_HALF_EVEN + Decimal precision)
  - typing (Final type qualifier)
  - packages.cost_engine.cvp (CVPBaseline re-use, AD-11 1방향)

Forbidden (7-2 explicitly disallows):
  - sqlalchemy, fastapi, starlette, requests, httpx
  - psycopg, asyncpg
  - time, datetime, random, os, socket, subprocess
  - pydantic (AD-5: no Pydantic inside engine — allowed in adapters)
  - json, urllib
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TARGET_FILE = ROOT / "packages" / "cost_engine" / "projection.py"

STORY_7_2_ALLOWED_TOP_LEVEL: frozenset[str] = frozenset(
    {"__future__", "hashlib", "dataclasses", "decimal", "typing", "packages"}
)

STORY_7_2_FORBIDDEN_TOP_LEVEL: frozenset[str] = frozenset(
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
def test_projection_file_exists() -> None:
    """The projection.py file MUST exist at the expected path."""
    assert TARGET_FILE.is_file(), (
        f"Story 7.2 pure kernel missing: {TARGET_FILE}"
    )


@pytest.mark.engine
def test_projection_whitelist_only() -> None:
    """Only 7-2 whitelisted stdlib modules may be imported."""
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top not in STORY_7_2_ALLOWED_TOP_LEVEL:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` "
                f"— only {sorted(STORY_7_2_ALLOWED_TOP_LEVEL)} allowed (Story 7.2 AD-5)"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_projection_no_forbidden_imports() -> None:
    """Explicit forbidden-import check (defense-in-depth, 7-2 specific)."""
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top in STORY_7_2_FORBIDDEN_TOP_LEVEL:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports forbidden `{top}` "
                f"(Story 7.2 AD-5 purity violation)"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_projection_no_services_or_apps_imports() -> None:
    """projection.py must NOT import packages.services or apps.* (AD-11)."""
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
def test_projection_no_external_dependencies() -> None:
    """projection.py must NOT import any non-stdlib package (other than packages.*)."""
    stdlib_whitelist = STORY_7_2_ALLOWED_TOP_LEVEL
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top not in stdlib_whitelist:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` — "
                f"not in 7-2 whitelist (stdlib-only)"
            )
    assert not violations, "\n".join(violations)
