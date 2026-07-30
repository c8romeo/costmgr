#!/usr/bin/env python3
"""Integration tests for stack-pin-check scripts (Story 0.3).

Verifies:
- The script exits 0 on the current repo (all pins match).
- Drift in a pinned file (apps/web/package.json next version) → exit 1.
- [STACK BUMP] / STACK_BUMP=1 → drift is authorized, exit 0.
- Drift output reports the drifted package name.

These are end-to-end tests that invoke the actual scripts. They assume the
repo is checked out and the script files exist.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_CHECK = REPO_ROOT / "scripts" / "check_stack_pin.mjs"
PY_CHECK = REPO_ROOT / "scripts" / "check_stack_pin.py"


def _run_node(extra_env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("CI", "true")  # suppress any interactive prompts
    # Force UTF-8 so the script's unicode markers (✗ / ✓ / ⚠) decode on
    # legacy Windows consoles (cp949) without raising UnicodeDecodeError
    # in pytest's stdout/stderr capture thread.
    env["PYTHONIOENCODING"] = "utf-8"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["node", str(NODE_CHECK)],
        cwd=cwd or REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


def _run_py(extra_env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    if extra_env:
        env.update(extra_env)
    # Pass STACK_PIN_ROOT so the Python script reads files relative to cwd
    if cwd:
        env["STACK_PIN_ROOT"] = str(cwd)
    return subprocess.run(
        [sys.executable, str(PY_CHECK)],
        cwd=cwd or REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


@pytest.mark.architecture
def test_node_check_passes_when_pinned() -> None:
    """No drift: current repo matches STACK_PIN.yaml."""
    result = _run_node()
    assert result.returncode == 0, (
        f"check_stack_pin.mjs failed on clean repo:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.architecture
def test_py_check_passes_when_pinned() -> None:
    """Python equivalent also passes on clean repo."""
    result = _run_py()
    assert result.returncode == 0, (
        f"check_stack_pin.py failed on clean repo:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.architecture
def test_check_fails_on_drift(tmp_path: Path) -> None:
    """When apps/web/package.json next version drifts, exit code = 1."""
    # Build an isolated copy of the repo
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
        "_bmad-output/implementation-artifacts/.memlog.md",
    ))

    # Bump next in apps/web/package.json
    pkg_path = work / "apps" / "web" / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    original_next = pkg["dependencies"]["next"]
    pkg["dependencies"]["next"] = "999.0.0"
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

    result = _run_node(cwd=work)
    assert result.returncode == 1, (
        f"expected exit 1 on drift, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # Output should mention next
    combined = result.stdout + result.stderr
    assert "next" in combined, f"output should report drifted package 'next':\n{combined}"

    # Restore for cleanliness (tmp_path is auto-cleaned, but be tidy)
    pkg["dependencies"]["next"] = original_next
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")


@pytest.mark.architecture
def test_check_passes_with_bump_tag_env(tmp_path: Path) -> None:
    """STACK_BUMP=1 env var authorizes drift → exit 0."""
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
    ))

    pkg_path = work / "apps" / "web" / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    pkg["dependencies"]["next"] = "999.0.0"
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

    result = _run_node(cwd=work, extra_env={"STACK_BUMP": "1"})
    assert result.returncode == 0, (
        f"STACK_BUMP=1 should authorize drift, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "STACK BUMP" in result.stdout or "STACK_BUMP" in result.stdout


@pytest.mark.architecture
def test_check_passes_with_bump_commit_tag(tmp_path: Path) -> None:
    """A [STACK BUMP] tag in HEAD commit authorizes drift → exit 0.

    This test creates a git repo in tmp_path, commits with the tag, and runs
    the script there.
    """
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
        ".git",  # start with no git history
    ))

    # Init git repo + set local user + commit with [STACK BUMP] tag
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=work, check=True)
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "[STACK BUMP] bump next to 999.0.0"],
        cwd=work,
        check=True,
    )

    # Bump next AFTER the commit (so drift is real)
    pkg_path = work / "apps" / "web" / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    pkg["dependencies"]["next"] = "999.0.0"
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

    result = _run_node(cwd=work)
    assert result.returncode == 0, (
        f"[STACK BUMP] tag should authorize drift, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "[STACK BUMP]" in result.stdout


@pytest.mark.architecture
def test_check_reports_drifted_packages(tmp_path: Path) -> None:
    """Drift output lists each drifted package by name."""
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
    ))

    # Drift two packages
    pkg_path = work / "apps" / "web" / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    pkg["dependencies"]["next"] = "999.0.0"
    pkg["dependencies"]["react"] = "999.0.0"
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")

    result = _run_node(cwd=work)
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "next" in combined
    assert "react" in combined


# ── TEST-1 (CR 2026-07-25): STACK_PIN.yaml edge cases ──────────────────────


@pytest.mark.architecture
def test_check_handles_missing_pin_yaml(tmp_path: Path) -> None:
    """Missing STACK_PIN.yaml → both checks return exit 2 (config error)."""
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
        ".git",
    ))
    (work / "docs" / "STACK_PIN.yaml").unlink()

    result_node = _run_node(cwd=work)
    assert result_node.returncode == 2, (
        f"Node check should exit 2 on missing yaml, got {result_node.returncode}\n"
        f"stdout: {result_node.stdout}\nstderr: {result_node.stderr}"
    )

    result_py = _run_py(cwd=work)
    assert result_py.returncode == 2, (
        f"Python check should exit 2 on missing yaml, got {result_py.returncode}\n"
        f"stdout: {result_py.stdout}\nstderr: {result_py.stderr}"
    )


@pytest.mark.architecture
def test_check_handles_empty_pin_yaml(tmp_path: Path) -> None:
    """Empty STACK_PIN.yaml → both checks exit 0 (no pins to verify)."""
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
        ".git",
    ))
    (work / "docs" / "STACK_PIN.yaml").write_text("", encoding="utf-8")

    result_node = _run_node(cwd=work)
    assert result_node.returncode == 0, (
        f"Node check on empty yaml should pass:\n{result_node.stdout}\n{result_node.stderr}"
    )

    result_py = _run_py(cwd=work)
    assert result_py.returncode == 0, (
        f"Python check on empty yaml should pass:\n{result_py.stdout}\n{result_py.stderr}"
    )


@pytest.mark.architecture
def test_check_handles_bom_prefixed_yaml(tmp_path: Path) -> None:
    """BOM-prefixed STACK_PIN.yaml → both checks pass (CASCADE-1 regression)."""
    work = tmp_path / "repo"
    shutil.copytree(REPO_ROOT, work, ignore=shutil.ignore_patterns(
        "node_modules", ".venv", ".next", "__pycache__", ".pytest_cache",
        ".git",
    ))
    # Read original yaml and re-write with UTF-8 BOM prefix
    original = (work / "docs" / "STACK_PIN.yaml").read_bytes()
    (work / "docs" / "STACK_PIN.yaml").write_bytes(b"\xef\xbb\xbf" + original)

    result_node = _run_node(cwd=work)
    assert result_node.returncode == 0, (
        f"Node check on BOM yaml should pass (js-yaml handles BOM):\n"
        f"{result_node.stdout}\n{result_node.stderr}"
    )

    result_py = _run_py(cwd=work)
    assert result_py.returncode == 0, (
        f"Python check on BOM yaml should pass (PyYAML handles BOM):\n"
        f"{result_py.stdout}\n{result_py.stderr}"
    )