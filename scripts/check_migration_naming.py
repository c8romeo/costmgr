#!/usr/bin/env python3
"""check_migration_naming.py — AD-15 migration naming linter.

Walks every Alembic migration under `apps/api/alembic/versions/` and flags
violations of AD-15 cross-language naming conventions:

  - `sa.Column("camelCase", ...)`  — column names must be `snake_case`
  - Table names inside raw SQL CREATE TABLE statements must also be `snake_case`.

Exits 0 if clean, 1 with file + line + AD-15 violation message otherwise.

Note: this script is for migrations only. Application code uses
Python-side `snake_case` enforced by ruff `N` rules.

Usage:
    uv run python scripts/check_migration_naming.py
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


MIGRATIONS_DIR = Path("apps/api/alembic/versions")

# Snake-case: lowercase letters, digits, underscores. Must start with letter/underscore.
_SNAKE_CASE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _is_snake_case(name: str) -> bool:
    return bool(_SNAKE_CASE_RE.match(name))


def _check_sa_column_string_args(node: ast.Call, path: Path) -> list[str]:
    """Inspect sa.Column(...) positional args for snake_case strings."""
    violations: list[str] = []
    for arg in node.args:
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
            continue
        name = arg.value
        if not _is_snake_case(name):
            violations.append(
                f"{path}:{arg.lineno}: AD-15 forbids `camelCase` column name `{name}` "
                f"in sa.Column(). Use snake_case."
            )
    return violations


def _check_create_table_statements(source: str, path: Path) -> list[str]:
    """Find raw SQL `CREATE TABLE [IF NOT EXISTS] <name>` lines; verify snake_case.

    Handles both direct `CREATE TABLE foo (...)` lines and embedded SQL
    inside `op.execute("CREATE TABLE foo (...)")` calls — the regex finds
    `CREATE TABLE` anywhere in the line.
    """
    violations: list[str] = []
    for i, line in enumerate(source.splitlines(), start=1):
        lower = line.lower()
        if "create table" not in lower:
            continue
        # Find the first occurrence of CREATE TABLE [IF NOT EXISTS] and capture the name.
        m = re.search(
            r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(?:\"([^\"]+)\"|([a-zA-Z_][a-zA-Z0-9_]*))",
            line,
            re.IGNORECASE,
        )
        if not m:
            continue
        name = m.group(1) or m.group(2)
        if not _is_snake_case(name):
            violations.append(
                f"{path}:{i}: AD-15 forbids `camelCase` table name `{name}` "
                f"in CREATE TABLE. Use snake_case."
            )
    return violations


def _check_file(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}:0: E999 cannot read file ({e})"]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [f"{path}:{e.lineno}:{e.offset or 0}: E999 syntax error ({e.msg})"]

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "Column":
            violations.extend(_check_sa_column_string_args(node, path))

    violations.extend(_check_create_table_statements(source, path))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="AD-15 migration naming linter")
    parser.add_argument("--verbose", action="store_true", help="Print pass/fail per file")
    args = parser.parse_args()

    if not MIGRATIONS_DIR.exists():
        print(f"[migration-naming] no migrations dir at {MIGRATIONS_DIR}", file=sys.stderr)
        return 0

    files = sorted(p for p in MIGRATIONS_DIR.rglob("*.py") if p.is_file())
    if not files:
        if args.verbose:
            print(f"[migration-naming] no migrations in {MIGRATIONS_DIR}")
        return 0

    all_violations: list[str] = []
    for f in files:
        v = _check_file(f)
        if args.verbose:
            status = "OK" if not v else "FAIL"
            print(f"[migration-naming] {status} {f}")
        all_violations.extend(v)

    if all_violations:
        print(
            "CONVENTION_VIOLATION: AD-15 naming in migrations. "
            "Use snake_case for column and table names.",
            file=sys.stderr,
        )
        for v in all_violations:
            print(v, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())