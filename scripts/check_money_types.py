#!/usr/bin/env python3
"""check_money_types.py — AD-8 monetary-type linter.

AD-8 violation scanner for Python cost paths.

Walks `.py` files under:
  - `packages/cost_engine/` (pure engine, stdlib only)
  - `apps/api/modules/m3_calculate/` (calculate module, when present)

Flags:
  - `float` annotations in function signatures, class attributes, or top-level
    variable annotations (these are the canonical "money" cost paths).
  - `numpy.float64` (drift source — AD-8 only permits `Decimal`/`int`).
  - `Decimal` *used* without an `import decimal` / `from decimal import Decimal`
    in the same file (catches copy-paste drift; ensures stdlib source).

Exits 0 if clean, 1 with file + line + AD-8 violation message otherwise.

Usage:
    uv run python scripts/check_money_types.py
    uv run python scripts/check_money_types.py --verbose

Lesson reference: Story 0.4 — ruff `N806`/`PD` cannot express
"float is forbidden in money paths". This AST-based checker fills the gap.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


# ── AD-8: where money cost paths live ────────────────────────────────────────
COST_PATH_ROOTS: tuple[Path, ...] = (
    Path("packages/cost_engine"),
    Path("apps/api/modules/m3_calculate"),
)


def _iter_python_files(root: Path) -> list[Path]:
    """Yield .py files under `root`, skip missing/empty dirs gracefully."""
    if not root.exists():
        return []
    if root.is_file() and root.suffix == ".py":
        return [root]
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _is_float_annotation(node: ast.AST) -> bool:
    """True if `node` is the AST representation of `float`."""
    return (
        isinstance(node, ast.Name)
        and node.id == "float"
        and isinstance(node.ctx, ast.Load)
    )


def _file_has_decimal_import(tree: ast.Module) -> bool:
    """True if the file imports `decimal.Decimal` (any form)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in ("decimal", "decimal.Decimal"):
            return any(alias.name == "Decimal" for alias in node.names)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "decimal" or alias.name.startswith("decimal."):
                    if alias.name == "decimal" or alias.asname == "Decimal":
                        return True
    return False


def _check_file(path: Path) -> list[str]:
    """Return AD-8 violation messages for `path`, empty if clean."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}:{0}:0: E999 cannot read file ({e})"]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}:{e.offset or 0}: E999 syntax error ({e.msg})"]

    violations: list[str] = []

    # 1) `float` annotations on function args, returns, and AnnAssign.
    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and node.annotation and _is_float_annotation(node.annotation):
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `float` in money cost path "
                f"(arg `{node.arg}`). Use `int` (KRW) or `Decimal` (USD)."
            )
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.returns and _is_float_annotation(node.returns):
                violations.append(
                    f"{path}:{node.lineno}: AD-8 forbids `float` return annotation. "
                    f"Use `int` (KRW) or `Decimal` (USD)."
                )
        if isinstance(node, ast.AnnAssign) and _is_float_annotation(node.annotation):
            target = ast.unparse(node.target) if hasattr(ast, "unparse") else "<var>"
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `float` annotation on `{target}`. "
                f"Use `int` (KRW) or `Decimal` (USD)."
            )

    # 2) `numpy.float64` references — drift source.
    # Detect any `.float64` attribute on a Name that points to numpy (any alias).
    # The user wrote `import numpy as np` → `np.float64`. We can't reliably
    # know the alias without scope analysis; flag any `*.float64` reference
    # in cost paths and let the developer confirm it isn't numpy's float64.
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "float64":
            # If parent context is an annotation or call arg on a money path,
            # this is almost certainly numpy.float64 — flag it.
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `.float64` (likely `numpy.float64`) "
                f"in money cost path. Use `Decimal` (USD) or `int` (KRW)."
            )

    # 3) `Decimal(...)` usage without an import — copy-paste drift detector.
    decimal_used = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Decimal"
        for node in ast.walk(tree)
    )
    if decimal_used and not _file_has_decimal_import(tree):
        violations.append(
            f"{path}:1: AD-8 sanity check: `Decimal(...)` used without importing "
            f"`from decimal import Decimal`. stdlib-only engine requires explicit import."
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="AD-8 monetary-type linter")
    parser.add_argument("--verbose", action="store_true", help="Print pass/fail per file")
    args = parser.parse_args()

    files: list[Path] = []
    for root in COST_PATH_ROOTS:
        files.extend(_iter_python_files(root))

    if not files:
        if args.verbose:
            print(f"[money-types] no cost-path files found under {[str(r) for r in COST_PATH_ROOTS]}")
        return 0

    all_violations: list[str] = []
    for f in files:
        violations = _check_file(f)
        if args.verbose:
            status = "OK" if not violations else "FAIL"
            print(f"[money-types] {status} {f}")
        all_violations.extend(violations)

    if all_violations:
        # Header so CR/IDE can surface the AD ref.
        print(
            "CONVENTION_VIOLATION: AD-8 monetary types. "
            "Use `int` for KRW (BIGINT) or `Decimal` for USD (NUMERIC(18,2)).",
            file=sys.stderr,
        )
        for v in all_violations:
            print(v, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())