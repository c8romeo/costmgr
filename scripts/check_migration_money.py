#!/usr/bin/env python3
"""check_migration_money.py — AD-8 migration monetary-type linter.

Walks every Alembic migration under `apps/api/alembic/versions/` and flags
violations of AD-8 monetary types:

  - `sa.Float` as a column type (any context) — forbidden (float is lossy)
  - `sa.Column("name", sa.Float)`            — forbidden
  - Money columns (KRW suffix):
      - `sa.Numeric(...)`                     — forbidden (must use `sa.BigInteger`)
  - Money columns (USD suffix or generic money keywords):
      - `sa.Numeric(precision != 18 | scale != 2)` — forbidden (must be NUMERIC(18,2))
  - Non-money columns (percentages, scores, ratios):
      - `sa.Numeric(...)`                     — allowed (not AD-8 scoped)
  - `sa.BigInteger` (KRW)                    — allowed

AD-8 (`docs/conventions.md §5`) mandates:
  - KRW → `sa.BigInteger` (1원 정밀도)
  - USD → `sa.Numeric(18, 2)`

Money column detection uses a substring match on the column name (first
positional arg of `sa.Column`). Patterns cover explicit currency suffixes
(`_krw` / `_usd`) and generic money keywords (`_budget`, `_cost`,
`_savings`, `_spend`, `_amount`, `_on_demand_cost`, `_commit_cost`,
`_projected_*`, `_realized_savings`, `_potential_savings`, etc.).

Non-money columns (percentages, scores, ratios) follow their own
conventions — e.g. BOM ratios use `NUMERIC(7,4)` (§5.1), ML scores use
`NUMERIC(8,4)`. These are out of scope for the AD-8 money linter.

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

# Money column name patterns. Matched as case-insensitive substrings against
# the column name (first positional arg of `sa.Column`).
#
# KRW columns: name contains `_krw`. Per AD-8, KRW MUST be `sa.BigInteger`
# (1원 정밀도 정수 통화) — `sa.Numeric` is forbidden.
#
# USD / generic-money columns: name contains any of `_usd`, `_budget`,
# `_spend`, `_cost`, `_savings`, `_amount`, `_on_demand_cost`,
# `_commit_cost`, `_projected_*`, `_realized_savings`,
# `_potential_savings`, `_predicted_end_period`, `_cost_per_month`,
# `_upfront_cost`. Per AD-8, USD MUST be `sa.Numeric(18, 2)`.
_MONEY_KRW_PATTERNS: tuple[str, ...] = ("_krw",)

_MONEY_GENERIC_PATTERNS: tuple[str, ...] = (
    "_usd",
    "_budget",
    "_spend",
    "_savings",
    "_amount",
    "_cost",
    "_cost_per_month",
    "_on_demand_cost",
    "_commit_cost",
    "_projected_commit",
    "_projected_savings",
    "_current_cost",
    "_recommended_cost",
    "_upfront_cost",
    "_realized_savings",
    "_potential_savings",
    "_predicted_end_period",
    "_burn_rate",
)

# Non-money column suffixes — these signal the column is a percentage,
# score, or ratio, NOT a money value. AD-8 does not apply to these
# (BOM ratios follow §5.1 NUMERIC(7,4); ML scores use NUMERIC(8,4)).
_NON_MONEY_SUFFIXES: tuple[str, ...] = ("_pct", "_score", "_ratio")


def _is_non_money_column(name: str) -> bool:
    """True if `name` ends with a non-money suffix (_pct/_score/_ratio).

    These columns follow their own precision/scale conventions (BOM
    ratios = NUMERIC(7,4), ML scores = NUMERIC(8,4), etc.) and are
    out of scope for the AD-8 money linter.

    Returns True ONLY when the suffix is at a word boundary — e.g.
    `projected_savings_pct` ends with `_pct`, but `cpcthreshold` would
    not match (we substring-check after the leading underscore pattern
    by requiring the suffix to appear at the END of the name OR be
    followed by `_` for compound names).
    """
    n = name.lower()
    for suffix in _NON_MONEY_SUFFIXES:
        if n.endswith(suffix):
            return True
        # Compound: `_pct_` / `_score_` (e.g., `forecast_pct_change`)
        if f"{suffix}_" in n:
            return True
    return False


def _is_krw_column(name: str) -> bool:
    """True if `name` looks like a KRW money column (AD-8 BigInteger)."""
    n = name.lower()
    return any(p in n for p in _MONEY_KRW_PATTERNS)


def _is_money_column(name: str) -> bool:
    """True if `name` looks like any kind of money column (AD-8 scoped).

    Non-money columns (percentages, scores, ratios — `_pct`, `_score`,
    `_ratio` suffixes) are excluded even if they contain money
    keywords like `_savings` (e.g., `projected_savings_pct`).
    """
    n = name.lower()
    if _is_non_money_column(n):
        return False
    if _is_krw_column(n):
        return True
    return any(p in n for p in _MONEY_GENERIC_PATTERNS)


def _is_float_type_expr(node: ast.AST) -> bool:
    """True if `node` is `sa.Float` or `sa.Float(...)` or `Float` (any form).

    Covers both bare class references (`sa.Column("cost", sa.Float)`) and
    instantiated calls (`sa.Column("cost", sa.Float())`).
    """
    if isinstance(node, ast.Attribute) and node.attr == "Float":
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "Float":
        return True
    return isinstance(node, ast.Name) and node.id == "Float"


def _extract_numeric_info(node: ast.AST) -> tuple[int, int] | None:
    """Return `(precision, scale)` if `node` is `sa.Numeric(...)`, else None.

    Supports both positional args (`sa.Numeric(18, 2)`) and keyword args
    (`sa.Numeric(precision=18, scale=2)`).
    """
    if not isinstance(node, ast.Call):
        return None
    if not (isinstance(node.func, ast.Attribute) and node.func.attr == "Numeric"):
        return None

    precision: int | None = None
    scale: int | None = None

    # Positional args: sa.Numeric(precision, scale)
    if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, int):
        precision = node.args[0].value
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, int):
        scale = node.args[1].value

    # Keyword args: sa.Numeric(precision=..., scale=...)
    for kw in node.keywords:
        if kw.arg == "precision" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
            precision = kw.value.value
        elif kw.arg == "scale" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
            scale = kw.value.value

    if precision is None or scale is None:
        return None
    return (precision, scale)


def _get_column_name(node: ast.Call) -> str | None:
    """Extract the column name (first positional str arg) from `sa.Column(...)`."""
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return None


def _get_column_type(node: ast.Call) -> ast.AST | None:
    """Extract the column type expression from `sa.Column(...)`.

    Second positional arg takes precedence over `type=` keyword arg.
    Returns None if neither is present.
    """
    if len(node.args) >= 2:
        return node.args[1]
    for kw in node.keywords:
        if kw.arg == "type":
            return kw.value
    return None


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

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        # Rule 1: standalone `sa.Float(...)` — always forbidden (AD-8).
        if isinstance(func, ast.Attribute) and func.attr == "Float":
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `sa.Float` "
                f"(line `{ast.unparse(node) if hasattr(ast, 'unparse') else '<expr>'}`). "
                f"Use `sa.BigInteger` (KRW) or `sa.Numeric(18,2)` (USD)."
            )
            continue

        # Rule 2: `sa.Column(...)` — inspect type against the column name.
        if not (isinstance(func, ast.Attribute) and func.attr == "Column"):
            continue

        col_name = _get_column_name(node)
        col_type = _get_column_type(node)
        if col_name is None or col_type is None:
            continue

        # (a) `sa.Float` as column type — always forbidden.
        if _is_float_type_expr(col_type):
            col_name_disp = col_name or "?"
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `sa.Float` for column `{col_name_disp}`. "
                f"Use `sa.BigInteger` (KRW) or `sa.Numeric(18,2)` (USD)."
            )
            continue

        # (b) `sa.Numeric(...)` with precision/scale — only check money columns.
        numeric_info = _extract_numeric_info(col_type)
        if numeric_info is None:
            # Type is non-Numeric (e.g., sa.BigInteger, sa.Integer, sa.Text) — OK.
            continue

        if not _is_money_column(col_name):
            # Non-money column (percentage, score, ratio) — AD-8 does not apply.
            continue

        precision, scale = numeric_info

        # KRW columns: `sa.Numeric` is forbidden. AD-8 mandates `sa.BigInteger`.
        if _is_krw_column(col_name):
            violations.append(
                f"{path}:{node.lineno}: AD-8 forbids `sa.Numeric` for KRW column `{col_name}`. "
                f"Use `sa.BigInteger` (1원 정밀도 정수 통화)."
            )
            continue

        # USD / generic-money columns: must use `sa.Numeric(18, 2)`.
        if precision != ALLOWED_NUMERIC_PRECISION or scale != ALLOWED_NUMERIC_SCALE:
            violations.append(
                f"{path}:{node.lineno}: AD-8 requires `sa.Numeric(18,2)` for money column `{col_name}` "
                f"(got precision={precision}, scale={scale})."
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
