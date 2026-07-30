#!/usr/bin/env python3
"""ruff_check_money.py — thin wrapper for ruff integration.

Acts as a ruff-style plugin entry point that delegates to the canonical
`check_money_types.py` AST checker. The Makefile and any CI hook can call
this script directly; the canonical implementation lives in
`scripts/check_money_types.py`.

Why two scripts?
  - `check_money_types.py` is the AST-based source of truth (handles float,
    numpy.float64, Decimal-import drift).
  - `ruff_check_money.py` is a stable wrapper name kept for AD-15 conformance
    (the rule names live alongside ruff's standard set).

Exit codes:
    0  — clean
    1  — AD-8 violation(s) found
    2  — script failure (missing files, etc.)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    canonical = here / "check_money_types.py"
    if not canonical.exists():
        print(f"ERROR: {canonical} not found", file=sys.stderr)
        return 2

    # Delegate — keep this thin so all logic lives in one place.
    result = subprocess.run(
        [sys.executable, str(canonical), *sys.argv[1:]],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())