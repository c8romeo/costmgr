"""AST-based forbidden-import guard for packages.cost_engine.

AD-1, AD-5, AD-11 enforcement at the engine boundary.

This test parses every .py under packages/cost_engine/ and asserts that no
forbidden module is imported. Violations produce a clear file:line:module
message that the CI lint step surfaces as a build failure.

Forbidden (any appearance in any .py under packages/cost_engine/):
  - sqlalchemy, fastapi, starlette, requests, httpx
  - psycopg, asyncpg
  - time (the module — not the built-in), random, os.environ
  - socket, subprocess, datetime.datetime.now

Allowed (engine may import):
  - decimal (stdlib), typing, uuid, dataclasses, enum
  - protocols.Protocol (from typing)
  - collections.abc
  - packages.cost_engine.ports (internal — typed contracts only)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = ROOT / "packages" / "cost_engine"

FORBIDDEN_TOP_LEVEL = {
    "sqlalchemy",
    "fastapi",
    "starlette",
    "requests",
    "httpx",
    "psycopg",
    "asyncpg",
    "time",          # the module — `import time` is forbidden (use explicit datetime)
    "datetime",      # AD-5: `datetime.datetime.now()` would also leak the wall clock
    "random",        # AD-5: no randomness
    "socket",
    "subprocess",
    "pydantic",      # AD-5: no Pydantic inside engine (allowed in adapters)
}

# `os.environ` is forbidden as a bare `os.environ` attribute access.
# We can't easily AST-detect attribute access patterns; we forbid `import os` too
# because the engine must receive config via constructor injection.
FORBIDDEN_TOP_LEVEL.add("os")


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _imports_in_file(path: Path) -> list[tuple[int, str]]:
    """Return a list of (line_no, top_level_module) for every import in the file."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:  # pragma: no cover
        return [(e.lineno or 0, f"<SYNTAX_ERROR:{e.msg}>")]

    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                found.append((node.lineno, top))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                # relative import: from .x import y — root is ""; allowed
                continue
            top = node.module.split(".")[0]
            found.append((node.lineno, top))
    return found


@pytest.mark.engine
def test_no_forbidden_imports_in_engine() -> None:
    violations: list[str] = []
    for py_file in _iter_python_files(ENGINE_ROOT):
        for lineno, top in _imports_in_file(py_file):
            if top in FORBIDDEN_TOP_LEVEL:
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel}:{lineno} imports forbidden top-level `{top}` "
                    f"(violates AD-1/AD-5/AD-11 — engine is pure)"
                )

    assert not violations, (
        "packages.cost_engine contains forbidden imports.\n"
        "Engine must be pure: no I/O, no DB, no web, no clock, no random.\n\n"
        + "\n".join(violations)
    )


@pytest.mark.engine
def test_engine_core_does_not_import_adapters() -> None:
    """AD-11: core MUST NOT import adapters (the reverse direction is fine)."""
    core_root = ENGINE_ROOT / "core"
    assert core_root.is_dir(), f"Missing engine core dir: {core_root}"

    violations: list[str] = []
    for py_file in _iter_python_files(core_root):
        for lineno, top in _imports_in_file(py_file):
            # Any import path that walks through the adapters package
            if top == "adapters" or top.startswith("adapters.") or top == "packages.cost_engine.adapters" or top.startswith("packages.cost_engine.adapters."):
                rel = py_file.relative_to(ROOT)
                violations.append(f"{rel}:{lineno} imports `{top}` — forbidden (AD-11)")

    assert not violations, (
        "packages.cost_engine.core must NOT import packages.cost_engine.adapters.\n\n"
        + "\n".join(violations)
    )


@pytest.mark.engine
def test_engine_money_module_is_stdlib_only() -> None:
    """The canonical money types file uses only decimal + typing (AD-5)."""
    money_file = ENGINE_ROOT / "core" / "money.py"
    assert money_file.is_file(), "packages/cost_engine/core/money.py must exist"

    allowed = {"decimal", "typing"}
    for lineno, top in _imports_in_file(money_file):
        assert top in allowed, (
            f"packages/cost_engine/core/money.py:{lineno} imports `{top}` "
            f"— only {sorted(allowed)} are allowed (AD-5 pure stdlib)"
        )


# ─────────────────────────────────────────────────────────────
# Story 4.1 — AD-22 + AD-11 strengthening cases
# Engine NEVER writes to DB; engine NEVER authorizes reversal (M11 owns).
# ─────────────────────────────────────────────────────────────


@pytest.mark.engine
def test_engine_does_not_import_sqlalchemy_orm() -> None:
    """Story 4.1 — AD-22 boundary: engine NEVER writes to DB.

    `sqlalchemy.orm` write-side APIs (Session, Mapper, etc.) are forbidden
    inside the engine. The adapter layer (apps/api/) is the only place
    where ORM session operations live.
    """
    forbidden = {"sqlalchemy"}
    violations: list[str] = []
    for py_file in _iter_python_files(ENGINE_ROOT):
        for lineno, top in _imports_in_file(py_file):
            if top in forbidden:
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel}:{lineno} imports `{top}` — engine MUST NOT "
                    f"depend on ORM (AD-22 — DB writes live in adapters)"
                )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_engine_does_not_import_reversal_authorization() -> None:
    """Story 4.1 — AD-22: engine NEVER authorizes reversal.

    `M11 reversal` is Epic 11 (audit lock + reversal request). The engine
    only COMPUTES `state="draft"`; reversal authorization is a service
    concern (apps/api). This test guards against accidental reverse
    import of M11 / m11 reversal modules.
    """
    forbidden_substrings = ("m11_reversal", "reversal_auth", "reverse_authorization")
    violations: list[str] = []
    for py_file in _iter_python_files(ENGINE_ROOT):
        src = py_file.read_text(encoding="utf-8")
        for needle in forbidden_substrings:
            if needle in src:
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel} contains `{needle}` — engine MUST NOT authorize "
                    f"reversal (AD-22 — M11 owns)"
                )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_engine_state_transitions_only_draft() -> None:
    """Story 4.1 — AD-22 invariant: engine writes ONLY `state="draft"`.

    Source scan: any literal string `"verified"`, `"committed"`, or
    `"reversed"` inside a return statement is a violation. (Test pattern
    mirrors CR 1.1's `apps/api/core/` scan.)
    """
    forbidden_states = ("verified", "committed", "reversed")
    violations: list[str] = []
    for py_file in _iter_python_files(ENGINE_ROOT):
        src = py_file.read_text(encoding="utf-8")
        for state in forbidden_states:
            # Match return statements that look like `state=<state>` or
            # `state = <state>` with a quoted literal.
            pattern = rf"state\s*=\s*[\"']{state}[\"']"
            if re.search(pattern, src):
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel} sets `state='{state}'` — engine returns "
                    f"`state='draft'` ONLY (AD-22)"
                )
    assert not violations, "\n".join(violations)


@pytest.mark.engine
def test_engine_no_global_state_or_module_level_writes() -> None:
    """Story 4.1 — AD-5: engine has no global mutable state.

    Module-level `d = {}`, `d = []`, `d = set()` are forbidden. Constants
    (frozen dict, Final tuple, frozenset) are allowed.
    """
    forbidden_patterns = (
        re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\s*=\s*\{\}\s*$", re.MULTILINE),
        re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\s*=\s*\[\]\s*$", re.MULTILINE),
        re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\s*=\s*set\(\)\s*$", re.MULTILINE),
    )
    violations: list[str] = []
    for py_file in _iter_python_files(ENGINE_ROOT):
        src = py_file.read_text(encoding="utf-8")
        for pat in forbidden_patterns:
            for m in pat.finditer(src):
                # Line number by counting newlines up to the match.
                line_no = src[: m.start()].count("\n") + 1
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel}:{line_no} declares module-level mutable container "
                    f"— engine has NO global state (AD-5)"
                )
    assert not violations, "\n".join(violations)
