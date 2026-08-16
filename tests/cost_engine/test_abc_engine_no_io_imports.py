"""AST-based forbidden-import guard for Story 9.1 + 9.2 abc_engine.py.

AD-1, AD-5, AD-11 enforcement — 9.1+9.2 EXTENSION surface whitelist.

This test parses `packages/cost_engine/abc_engine.py` and asserts that
only the 9.1+9.2 whitelisted stdlib modules are imported. Violations produce a
clear file:line:module message that CI lint surfaces as a build failure.

Allowed (Story 9.1+9.2 abc_engine.py whitelist — stdlib-only AD-5):
  - __future__ (annotations)
  - hashlib (sha256 digest for V8 determinism)
  - dataclasses (frozen=True, slots=True)
  - decimal (Decimal arithmetic + ROUND_HALF_EVEN, 9-2 CCR compute 1-Won precision)
  - typing (Final, Union)

Forbidden (9.1+9.2 explicitly disallows):
  - sqlalchemy, fastapi, starlette, requests, httpx
  - psycopg, asyncpg
  - time, datetime, random, os, socket, subprocess
  - pydantic (AD-5: no Pydantic inside engine — allowed in adapters)
  - re (no pattern matching needed)
  - math (Decimal arithmetic only)
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TARGET_FILE = ROOT / "packages" / "cost_engine" / "abc_engine.py"

# Story 9.1 + Story 9.2 EXTENSION — same surface, no new external deps.
# 9-2 EXTENSION uses decimal.ROUND_HALF_EVEN (in `decimal` stdlib) for 1-Won precision.
STORY_9_1_2_ALLOWED_TOP_LEVEL: frozenset[str] = frozenset(
    {"__future__", "hashlib", "dataclasses", "decimal", "typing"}
)

STORY_9_1_2_FORBIDDEN_TOP_LEVEL: frozenset[str] = frozenset(
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
        "re",
        "math",
        "apps",
        "pytest",
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
def test_abc_engine_file_exists() -> None:
    """The abc_engine.py file MUST exist at the expected path."""
    assert TARGET_FILE.is_file(), f"Story 9.1+9.2 pure kernel missing: {TARGET_FILE}"


@pytest.mark.engine
def test_abc_engine_whitelist_only() -> None:
    """Only 9.1+9.2 whitelisted stdlib modules may be imported."""
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top not in STORY_9_1_2_ALLOWED_TOP_LEVEL:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` "
                f"— only {sorted(STORY_9_1_2_ALLOWED_TOP_LEVEL)} "
                f"allowed (Story 9.1+9.2 AD-5)"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_abc_engine_no_forbidden_imports() -> None:
    """Explicit forbidden-import check (defense-in-depth, 9.1+9.2 specific)."""
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top in STORY_9_1_2_FORBIDDEN_TOP_LEVEL:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports forbidden `{top}` "
                f"(Story 9.1+9.2 AD-5 purity violation)"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_abc_engine_no_packages_services_or_apps_imports() -> None:
    """abc_engine.py must NOT import packages.services or apps.* (AD-11)."""
    imports = _imports_in_file(TARGET_FILE)
    forbidden_prefixes = ("packages.services", "apps.")
    violations: list[str] = []
    for lineno, top in imports:
        for prefix in forbidden_prefixes:
            if top.startswith(prefix):
                violations.append(
                    f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` — "
                    f"engine MUST NOT depend on services/apps "
                    f"(AD-11 layer rule)"
                )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_abc_engine_no_external_dependencies() -> None:
    """abc_engine.py must NOT import any non-stdlib package."""
    stdlib_whitelist = STORY_9_1_2_ALLOWED_TOP_LEVEL
    imports = _imports_in_file(TARGET_FILE)
    violations: list[str] = []
    for lineno, top in imports:
        if top not in stdlib_whitelist:
            violations.append(
                f"{TARGET_FILE.relative_to(ROOT)}:{lineno} imports `{top}` — "
                f"not in 9.1+9.2 whitelist (stdlib-only)"
            )
    assert not violations, "\n".join(violations)


# ── Story 9.2 EXTENSION cases (CCR + Allocation uses ROUND_HALF_EVEN) ──


@pytest.mark.engine
def test_abc_engine_9_2_uses_decimal_only_for_quantum() -> None:
    """9-2 EXTENSION — CCR + Allocation uses decimal stdlib only (no math module)."""
    imports = _imports_in_file(TARGET_FILE)
    found_math = [t for _, t in imports if t == "math"]
    found_decimal = [t for _, t in imports if t == "decimal"]
    assert not found_math, (
        f"abc_engine.py must NOT import `math` — 9-2 EXTENSION uses "
        f"`decimal.ROUND_HALF_EVEN` for 1-Won precision: {found_math}"
    )
    assert found_decimal, (
        "abc_engine.py must import `decimal` for 1-Won precision arithmetic"
    )


@pytest.mark.engine
def test_abc_engine_9_2_no_clock_or_random() -> None:
    """9-2 EXTENSION — no clock or randomness (AD-5 + V8 determinism)."""
    imports = _imports_in_file(TARGET_FILE)
    for _, top in imports:
        assert top not in {"time", "datetime", "random"}, (
            f"abc_engine.py: {top} import forbidden (AD-5 + V8 determinism)"
        )


@pytest.mark.engine
def test_abc_engine_9_2_stdlib_whitelist_count() -> None:
    """9-2 EXTENSION — stdlib whitelist size unchanged."""
    # 9-1 surface had 5 stdlib modules; 9-2 EXTENSION same surface, no new external deps.
    assert len(STORY_9_1_2_ALLOWED_TOP_LEVEL) == 5


@pytest.mark.engine
def test_abc_engine_9_2_decimal_constants_present() -> None:
    """9-2 EXTENSION — `decimal.ROUND_HALF_EVEN` 사용 (1-Won precision).

    AST check: `from decimal import ROUND_HALF_EVEN` 또는 `decimal.ROUND_HALF_EVEN` 표기 검증.
    """
    src = TARGET_FILE.read_text(encoding="utf-8")
    # ROUND_HALF_EVEN either via `from decimal import ROUND_HALF_EVEN`
    # or via `decimal.ROUND_HALF_EVEN` reference
    assert "ROUND_HALF_EVEN" in src, (
        "abc_engine.py must use `ROUND_HALF_EVEN` for 1-Won precision "
        "banker's rounding (Story 9.2)"
    )


@pytest.mark.engine
def test_abc_engine_9_2_krw_quantum_constant() -> None:
    """9-2 EXTENSION — `CCR_KRW_QUANTUM = Decimal("1")` constant present.

    AD-8 1-Won precision + Decimal-as-string cross-language parity.
    """
    src = TARGET_FILE.read_text(encoding="utf-8")
    assert "CCR_KRW_QUANTUM" in src
    assert 'Decimal("1")' in src
