"""AST-based forbidden-decorator guard: no `@pytest.mark.asyncio` in cost_engine tests.

CR 4-3 F-1 carry — dev-story가 `@pytest.mark.asyncio` 데코레이터 + `async def test_*`를
사용했는데 `pyproject.toml`에 pytest-asyncio 플러그인이 install 되어 있지 않아 12 tests
failed. 프로젝트 확립 패턴: sync `def test_x()` + (coroutine 본문 필요 시)
`asyncio.run(_impl())` sync wrapper.

이 가드는 `tests/cost_engine/` 하위 모든 .py 파일을 AST walker로 순회하며,
`@pytest.mark.asyncio` decorator가 붙은 test 함수가 발견되면 fail.

허용:
- `@pytest.mark.engine`, `@pytest.mark.api`, `@pytest.mark.integration` 등
- sync `def test_*` + `asyncio.run(_impl())` 패턴
- `async def _impl()` 같은 private helper (decorator 없음, 직접 await/call 안 됨)

금지:
- `@pytest.mark.asyncio` (어떤 함수든 — test, helper 불문)
- `async def test_*` (sync wrapper 없는 async test)
- `@pytest_asyncio.fixture` (fixture decorator도 금지 — sync fixture 패턴)

CR 4-3 lessons: agent reports match what pytest says, not what the audit log says.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = ROOT / "tests" / "cost_engine"

# Decorator substrings that signal async-test pattern (FORBIDDEN)
# Each entry is a substring of the dotted decorator path. We match against
# `ast.Attribute` chain (e.g. `pytest.mark.asyncio`).
FORBIDDEN_DECORATOR_SUBSTRINGS = (
    "pytest.mark.asyncio",
    "pytest_asyncio.fixture",
    "pytest_asyncio.parametrize",
    "asyncio_mode",
)


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _decorator_chain(node: ast.expr) -> str:
    """Reconstruct the dotted path of a decorator AST node.

    Examples:
    - `pytest.mark.asyncio` → "pytest.mark.asyncio"
    - `@pytest_asyncio.fixture` → "pytest_asyncio.fixture"
    - `@pytest.mark.engine` → "pytest.mark.engine"
    - `@functools.lru_cache` → "functools.lru_cache"
    """
    parts: list[str] = []
    current: ast.expr | None = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _find_forbidden_decorators(path: Path) -> list[tuple[int, str, str]]:
    """Return a list of (line_no, function_name, decorator_chain) for each violation."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:  # pragma: no cover
        return [(e.lineno or 0, "<module>", f"<SYNTAX_ERROR:{e.msg}>")]

    violations: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        # Only check functions/methods (FunctionDef + AsyncFunctionDef both)
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for dec in node.decorator_list:
            chain = _decorator_chain(dec)
            for forbidden in FORBIDDEN_DECORATOR_SUBSTRINGS:
                if forbidden in chain:
                    violations.append((node.lineno, node.name, chain))
                    break
    return violations


@pytest.mark.engine
def test_no_pytest_mark_asyncio_decorator_in_cost_engine_tests() -> None:
    """CR 4-3 F-1: `@pytest.mark.asyncio` is FORBIDDEN in cost_engine tests.

    The project-wide pattern is `def test_x(): asyncio.run(_impl())` (sync
    wrapper). pytest-asyncio plugin is NOT in the dev dependency tree —
    using the decorator crashes collection with
    `async def functions are not natively supported`.

    Scope: this guard covers `tests/cost_engine/` only. The wider guard for
    `tests/` at large is left to a future epic (CR 4-3 lessons call out
    `tests/api/test_calc_orchestrator.py` as the canonical sync-wrapper
    template that the engine tests must follow).

    Violations produce a clear file:line:function:decorator message that the
    CI lint step surfaces as a build failure.
    """
    violations: list[str] = []
    for py_file in _iter_python_files(TEST_ROOT):
        for lineno, func_name, dec in _find_forbidden_decorators(py_file):
            rel = py_file.relative_to(ROOT)
            violations.append(
                f"{rel}:{lineno} `{func_name}` uses forbidden decorator "
                f"`{dec}` — pytest-asyncio is NOT installed. "
                f"Use sync `def test_x()` + `asyncio.run(_impl())` pattern."
            )

    assert not violations, (
        "tests/cost_engine/ uses forbidden async-decorator pattern.\n"
        "Project pattern (CR 4-3): sync `def test_*` + `asyncio.run(_impl())`.\n\n"
        + "\n".join(violations)
    )


@pytest.mark.engine
def test_no_async_def_test_functions_in_cost_engine_tests() -> None:
    """CR 4-3 F-1 belt-and-suspenders: `async def test_*` is also FORBIDDEN.

    Even without `@pytest.mark.asyncio`, an `async def test_*` will be
    collected by pytest and fail with
    `async def functions are not natively supported`.

    This guard catches the case where the decorator is missing but the
    function signature is still async.
    """
    violations: list[str] = []
    for py_file in _iter_python_files(TEST_ROOT):
        src = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_"):
                rel = py_file.relative_to(ROOT)
                violations.append(
                    f"{rel}:{node.lineno} `async def {node.name}` — "
                    f"test functions must be `def` (sync). "
                    f"Use `asyncio.run(_impl())` wrapper pattern."
                )

    assert not violations, (
        "tests/cost_engine/ contains async test functions.\n"
        "Project pattern (CR 4-3): sync `def test_*` only.\n\n"
        + "\n".join(violations)
    )
