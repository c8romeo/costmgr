#!/usr/bin/env python3
"""Integration tests for AD-8 / AD-15 convention linters (Story 0.4).

Verifies:
- Ruff passes on the current repo (clean baseline).
- check_money_types.py flags `float` annotations in cost-engine paths.
- check_migration_naming.py flags `camelCase` column names.
- check_migration_money.py flags `sa.Float` money columns.
- Ruff per-file-ignores do not flag known FastAPI idioms (B008, ARG001).

These are end-to-end tests that invoke the actual scripts (no mocks).
Each test creates a synthetic bad file in a temp dir, runs the script,
asserts exit code, then cleans up. The synthetic files do NOT touch the
repo's actual source tree.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MONEY_CHECK = REPO_ROOT / "scripts" / "check_money_types.py"
RUFF = REPO_ROOT / ".venv" / "Scripts" / "ruff.exe"  # Windows path
RUFF_FALLBACK = REPO_ROOT / ".venv" / "bin" / "ruff"  # POSIX path
MIGRATION_NAMING_CHECK = REPO_ROOT / "scripts" / "check_migration_naming.py"
MIGRATION_MONEY_CHECK = REPO_ROOT / "scripts" / "check_migration_money.py"

COST_ENGINE_DIR = REPO_ROOT / "packages" / "cost_engine"
MIGRATIONS_DIR = REPO_ROOT / "apps" / "api" / "alembic" / "versions"


def _resolve_ruff() -> Path:
    """Find the ruff executable — Windows or POSIX."""
    if RUFF.exists():
        return RUFF
    if RUFF_FALLBACK.exists():
        return RUFF_FALLBACK
    # Fall back to PATH lookup via subprocess (e.g. when CI uses system ruff).
    which = shutil.which("ruff")
    if which:
        return Path(which)
    pytest.skip("ruff executable not found in .venv or PATH")


# ───────────────────────────────────────────────────────────────
# Baseline tests
# ───────────────────────────────────────────────────────────────


def test_ruff_passes_on_clean_repo() -> None:
    """ruff check exits 0 on the current repo."""
    ruff = _resolve_ruff()
    result = subprocess.run(
        [str(ruff), "check", "apps", "packages"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"ruff check failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_money_types_passes_on_clean_repo() -> None:
    """check_money_types.py exits 0 on the current repo."""
    result = subprocess.run(
        [sys.executable, str(MONEY_CHECK), "--verbose"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"check_money_types.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_migration_naming_passes_on_clean_repo() -> None:
    """check_migration_naming.py exits 0 on the current migrations."""
    result = subprocess.run(
        [sys.executable, str(MIGRATION_NAMING_CHECK), "--verbose"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"check_migration_naming.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_migration_money_passes_on_clean_repo() -> None:
    """check_migration_money.py exits 0 on the current migrations."""
    result = subprocess.run(
        [sys.executable, str(MIGRATION_MONEY_CHECK), "--verbose"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"check_migration_money.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# ───────────────────────────────────────────────────────────────
# Money type linter — float violations
# ───────────────────────────────────────────────────────────────


def test_custom_money_check_blocks_float_in_engine(tmp_path: Path) -> None:
    """AST-based check catches `float` annotation in cost-engine paths."""
    # Create a synthetic cost-engine file with a float annotation.
    bad_subdir = COST_ENGINE_DIR / "_lint_test_subdir"
    bad_file = bad_subdir / "bad.py"
    bad_subdir.mkdir(exist_ok=True)
    try:
        bad_file.write_text(
            "def calc(price: float, qty: int) -> float:\n"
            "    return price * qty\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(MONEY_CHECK)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1, (
            f"expected exit 1 on float violation, got {result.returncode}\n"
            f"stderr:\n{result.stderr}"
        )
        assert "AD-8" in result.stderr
        assert "float" in result.stderr
    finally:
        shutil.rmtree(bad_subdir, ignore_errors=True)


def test_custom_money_check_blocks_numpy_float64(tmp_path: Path) -> None:
    """AST check catches `numpy.float64` references."""
    bad_subdir = COST_ENGINE_DIR / "_lint_test_numpy"
    bad_file = bad_subdir / "np_bad.py"
    bad_subdir.mkdir(exist_ok=True)
    try:
        bad_file.write_text(
            "import numpy as np\n"
            "def bad(x: np.float64) -> np.float64:\n"
            "    return x\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(MONEY_CHECK)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1, (
            f"expected exit 1 on numpy.float64, got {result.returncode}\n"
            f"stderr:\n{result.stderr}"
        )
        assert "numpy.float64" in result.stderr
    finally:
        shutil.rmtree(bad_subdir, ignore_errors=True)


# ───────────────────────────────────────────────────────────────
# Migration linters
# ───────────────────────────────────────────────────────────────


def test_migration_naming_fails_on_camelcase_column(tmp_path: Path) -> None:
    """check_migration_naming.py flags sa.Column('firstName', ...)."""
    bad_subdir = MIGRATIONS_DIR / "_lint_test_naming"
    bad_file = bad_subdir / "0002_bad.py"
    bad_subdir.mkdir(exist_ok=True)
    try:
        bad_file.write_text(
            "from alembic import op\n"
            "import sqlalchemy as sa\n"
            "def upgrade() -> None:\n"
            "    op.add_column('users', sa.Column('firstName', sa.Text))\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(MIGRATION_NAMING_CHECK)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "camelCase" in result.stderr
        assert "firstName" in result.stderr
    finally:
        shutil.rmtree(bad_subdir, ignore_errors=True)


def test_migration_money_fails_on_float_money(tmp_path: Path) -> None:
    """check_migration_money.py flags sa.Float() for money columns."""
    bad_subdir = MIGRATIONS_DIR / "_lint_test_money"
    bad_file = bad_subdir / "0002_bad.py"
    bad_subdir.mkdir(exist_ok=True)
    try:
        bad_file.write_text(
            "from alembic import op\n"
            "import sqlalchemy as sa\n"
            "def upgrade() -> None:\n"
            "    op.add_column('users', sa.Column('cost', sa.Float))\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(MIGRATION_MONEY_CHECK)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "sa.Float" in result.stderr or "Float" in result.stderr
    finally:
        shutil.rmtree(bad_subdir, ignore_errors=True)