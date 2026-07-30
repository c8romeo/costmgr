#!/usr/bin/env python3
"""check_migration_money.py — AD-8 migration monetary-type linter.

Walks every Alembic migration under `apps/api/alembic/versions/` and flags
violations of AD-8 monetary types:

  - `sa.Column(..., type=sa.Float)`        — forbidden (float is lossy)
  - `sa.Float` as a column type            — forbidden
  - `sa.Numeric(precision=18, scale=2)`     — allowed (USD)
  - `sa.BigInteger`                        — allowed (KRW)
  - `sa.Numeric(precision != 18 | scale != 2)` — warning (non-standard)

Exits 0 if clean, 1 with file + line + AD-8 violation message otherwise.

Usage:
    uv run python scripts/check_migration_money.py
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


MIGRATIONS_DIR = Path("apps/api/alembic/versions")
ALLOWED_NUMERIC_PRECISION = 18
ALLOWED_NUMERIC_SCALE = 2


def _is_float_type_expr(node: ast.AST) -> bool:
    """True if `node` is `sa.Float` or `sa.Float(...)` or `Float` (any form).

    Covers both bare class references (`sa.Column("cost", sa.Float)`) and
    instantiated calls (`sa.Column("cost", sa.Float())`).
    """
    # sa.Float (Attribute access, no Call)
    if isinstance(node, ast.Attribute) and node.attr == "Float":
        return True
    # sa.Float(...) (Call)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "Float":
        return True
    # Bare Float (Name reference — unusual but valid in some contexts)
    if isinstance(node, ast.Name) and node.id == "Float":
        return True
    return False


def _check_file(path: Path) -> list[str]:
    """Return AD-8 violation messages for migration `path`."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}:0: E999 cannot read file ({e})"]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}:{e.offset or 0}: E999 syntax error ({e.msg})"]

    violations: list[str] = []

    # We walk all Call nodes and inspect for sa.Column / sa.Float / sa.Numeric / sa.BigInteger.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        # sa.Float(...) — standalone float column type
        if isinstance(func, ast.Attribute) and func.attr == "Float":
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `sa.Float` (line `{ast.unparse(node) if hasattr(ast, 'unparse') else '<expr>'}`). "
                f"Use `sa.BigInteger` for KRW or `sa.Numeric(18,2)` for USD."
            )
            continue

        # sa.Numeric(...) — check precision/scale
        if isinstance(func, ast.Attribute) and func.attr == "Numeric":
            for kw in node.keywords:
                if kw.arg == "precision" and isinstance(kw.value, ast.Constant):
                    if kw.value.value != ALLOWED_NUMERIC_PRECISION:
                        violations.append(
                            f"{path}:{node.lineno}: AD-8 prefers `sa.Numeric(18,2)` for USD "
                            f"(got precision={kw.value.value}). Use NUMERIC(18,2) for USD columns."
                        )
                elif kw.arg == "scale" and isinstance(kw.value, ast.Constant):
                    if kw.value.value != ALLOWED_NUMERIC_SCALE:
                        violations.append(
                            f"{path}:{node.lineno}: AD-8 prefers `sa.Numeric(18,2)` for USD "
                            f"(got scale={kw.value.value}). Use NUMERIC(18,2) for USD columns."
                        )

        # sa.Column(..., type=...) OR sa.Column("name", sa.Float) — flag Float as money column.
        if isinstance(func, ast.Attribute) and func.attr == "Column":
            # (a) keyword: type=sa.Float() or type=sa.Float
            for kw in node.keywords:
                if kw.arg != "type":
                    continue
                if _is_float_type_expr(kw.value):
                    violations.append(
                        f"{path}:{node.lineno}: AD-8 forbids `type=sa.Float` in money columns. "
                        f"Use `type=sa.BigInteger` (KRW) or `type=sa.Numeric(18,2)` (USD)."
                    )
            # (b) positional: sa.Column("name", sa.Float) — second arg is class/type ref
            if len(node.args) >= 2 and _is_float_type_expr(node.args[1]):
                col_name = ast.unparse(node.args[0]) if hasattr(ast, "unparse") else "<name>"
                violations.append(
                    f"{path}:{node.lineno}: AD-8 forbids `sa.Float` as column type for `{col_name}`. "
                    f"Use `sa.BigInteger` (KRW) or `sa.Numeric(18,2)` (USD)."
                )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="AD-8 migration monetary-type linter")
    parser.add_argument("--verbose", action="store_true", help="Print pass/fail per file")
    args = parser.parse_args()

    if not MIGRATIONS_DIR.exists():
        print(f"[migration-money] no migrations dir at {MIGRATIONS_DIR}", file=sys.stderr)
        return 0  # missing dir is not a violation; nothing to lint

    files = sorted(p for p in MIGRATIONS_DIR.rglob("*.py") if p.is_file())
    if not files:
        if args.verbose:
            print(f"[migration-money] no migrations in {MIGRATIONS_DIR}")
        return 0

    all_violations: list[str] = []
    for f in files:
        v = _check_file(f)
        if args.verbose:
            status = "OK" if not v else "FAIL"
            print(f"[migration-money] {status} {f}")
        all_violations.extend(v)

    if all_violations:
        print(
            "CONVENTION_VIOLATION: AD-8 monetary types in migrations. "
            "Use `sa.BigInteger` (KRW) or `sa.Numeric(18,2)` (USD).",
            file=sys.stderr,
        )
        for v in all_violations:
            print(v, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())