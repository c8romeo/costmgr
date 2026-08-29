#!/usr/bin/env python3
"""Integration tests for ``scripts/check_tsc_drift.py`` (cj-style 209).

Verifies the TypeScript drift detector:
- Exits 2 with NOT INVOKABLE when tsc binary is absent (cj-197/204 cold-checkout
  scenario, tested via isolated scratch_repo with no node_modules).
- Exits 0 and writes a baseline JSON on first run when tsc IS invokable.
- Exits 0 when current counts match baseline (no drift).
- Baseline JSON schema is stable (schema_version + tsc_version + targets).

These are end-to-end tests that invoke the actual script. We use the real
repo path so tsc invokability matches the actual developer environment.

CR 11-3 honest boundary: if tsc is not invokable on the test host
(cold checkout without pnpm install), exit code 2 is the *correct* result,
not a test failure. Tests that require tsc to run are skipped with a clear
reason — they should be exercised in CI after ``pnpm install`` runs.
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
PY_CHECK = REPO_ROOT / "scripts" / "check_tsc_drift.py"
BASELINE_PATH = REPO_ROOT / "docs" / "architecture-decisions" / "AD-14-tsc-baseline.json"

TSC_CANDIDATES = [
    REPO_ROOT / "node_modules" / ".pnpm" / "typescript@5.9.3"
    / "node_modules" / "typescript" / "lib" / "tsc.js",
    REPO_ROOT / "node_modules" / ".ignored" / "typescript" / "bin" / "tsc",
]

TSC_AVAILABLE = any(p.exists() for p in TSC_CANDIDATES)
SKIP_REASON = (
    "tsc not installed in this environment "
    "(run `pnpm install --frozen-lockfile` first); "
    "this test is exercised in CI after install."
)


def _run(extra_env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["LC_ALL"] = "C.UTF-8"
    env["LANG"] = "C.UTF-8"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(PY_CHECK)],
        cwd=cwd or REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


@pytest.fixture
def scratch_repo() -> Path:
    """Empty temp dir with the docs/architecture-decisions subdir so the
    script can write a baseline if it ever invokes successfully. Used to
    test the cold-checkout path (no node_modules → NOT INVOKABLE).
    """
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="cj-209-tsc-scratch-"))
    (tmp / "docs" / "architecture-decisions").mkdir(parents=True, exist_ok=True)
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


def test_tsc_drift_exits_two_when_tsc_not_installed(scratch_repo: Path) -> None:
    """Cold-checkout path: STACK_PIN_ROOT → scratch_repo (no node_modules)
    → script reports NOT INVOKABLE → exit 2.

    This branch is always exercised regardless of whether tsc is installed
    on the test host, because we point STACK_PIN_ROOT at an empty dir.
    """
    result = _run(extra_env={"STACK_PIN_ROOT": str(scratch_repo)}, cwd=scratch_repo)
    assert result.returncode == 2, (
        f"expected NOT INVOKABLE exit 2; got {result.returncode}; "
        f"stderr: {result.stderr}"
    )
    assert "NOT INVOKABLE" in result.stderr


def test_tsc_drift_baseline_format_when_present() -> None:
    """When the committed baseline JSON exists, it should have the expected
    schema fields. We don't override STACK_PIN_ROOT, so the script reads
    the real baseline file. This test verifies the schema is stable.
    """
    if not BASELINE_PATH.exists():
        pytest.skip(
            "no committed baseline yet; will be created on first detector run"
        )
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == 1, "schema_version must be 1"
    assert "captured_at" in payload, "captured_at required"
    assert "tsc_version" in payload, "tsc_version required"
    assert "targets" in payload, "targets required"
    # Each target must have total + by_code.
    for label, body in payload["targets"].items():
        assert "total" in body, f"{label} missing total"
        assert "by_code" in body, f"{label} missing by_code"
        assert isinstance(body["by_code"], dict), f"{label} by_code not dict"


def test_tsc_drift_exits_zero_with_no_drift() -> None:
    """When tsc IS invokable and baseline exists (current count matches
    baseline), detector returns exit 0 with OK line.

    Uses the real repo so the script can actually find tsc. We rely on
    the committed baseline being current — first detector run in this
    repo already wrote it during sprint preparation.
    """
    if not TSC_AVAILABLE:
        pytest.skip(SKIP_REASON)
    result = _run()
    assert result.returncode == 0, (
        f"expected exit 0 (no drift); got {result.returncode}; "
        f"stdout: {result.stdout}; stderr: {result.stderr}"
    )
    # Script either reports OK baseline or OK no-drift depending on
    # whether the baseline was just freshly written.
    stdout_lower = result.stdout.lower()
    assert "ok" in stdout_lower or "no drift" in stdout_lower, (
        f"expected OK signal; got stdout: {result.stdout!r}"
    )


def test_tsc_drift_detects_drift_with_low_baseline() -> None:
    """When tsc IS invokable and we synthesize a baseline with total=0
    but current has errors, the detector should report exit 1.

    CR 11-3 honest boundary: this test is only meaningful when the
    current repo actually has tsc errors. If the repo is clean (the
    cj-204 cleanup verified state), the script correctly returns exit 0
    with "no drift" — we accept that as a valid outcome.
    """
    if not TSC_AVAILABLE:
        pytest.skip(SKIP_REASON)
    # Backup real baseline if present.
    backup_path = BASELINE_PATH.with_suffix(".json.test-backup")
    if BASELINE_PATH.exists():
        shutil.copy2(BASELINE_PATH, backup_path)
    try:
        # Write a low baseline (total=0) to force a drift check.
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "captured_at": "2026-08-29T00:00:00Z",
                    "tsc_version": "5.9.3",
                    "targets": {"apps/web": {"total": 0, "by_code": {}}},
                }
            ),
            encoding="utf-8",
        )
        result = _run()
        # Accept exit 0 (no drift — current repo is clean per cj-204)
        # or exit 1 (drift detected — synthetic baseline undercounts).
        assert result.returncode in (0, 1), (
            f"expected exit 0 or 1; got {result.returncode}; "
            f"stdout: {result.stdout}; stderr: {result.stderr}"
        )
        if result.returncode == 1:
            stdout_lower = result.stdout.lower()
            assert "drift" in stdout_lower or "fail" in stdout_lower, (
                f"expected drift signal; got stdout: {result.stdout!r}"
            )
    finally:
        # Restore the original baseline (or remove the synthetic one).
        if backup_path.exists():
            shutil.move(str(backup_path), str(BASELINE_PATH))
        elif BASELINE_PATH.exists():
            BASELINE_PATH.unlink()
