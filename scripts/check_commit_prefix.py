#!/usr/bin/env python3
"""Commit prefix lint (D5 fix — Story 9.7 A36 wire).

Rejects commits whose subject starts with `@` (the PowerShell here-string
artifact where `@'...'@` in bash context produces `@ @ Story ...` titles).
Mirrors the [STACK BUMP] bypass pattern from scripts/check_stack_pin.py.

Usage:
    uv run python scripts/check_commit_prefix.py
    COMMIT_PREFIX_BYPASS=1 uv run python scripts/check_commit_prefix.py
    COMMIT_PREFIX_BYPASS_PR_HEAD_SHA=<sha> uv run python scripts/check_commit_prefix.py

Exit codes:
    0 — pass (or bypass active)
    1 — violation (commit subject starts with `@`)
    2 — environment error (no git, no commit subject)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

ROOT = Path(os.environ.get("COMMIT_PREFIX_ROOT") or Path(__file__).resolve().parent.parent)

# Pattern: subject starts with `@` (PowerShell here-string artifact).
# Allowed bypass: `[STACK BUMP]` tag in commit subject (mirror check_stack_pin).
PREFIX_VIOLATION_RE = re.compile(r"^\s*@\s")


def get_commit_subject(target: str) -> str | None:
    """Return the subject of the given commit (HEAD by default), or None on error."""
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%s", target],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.decode("utf-8", errors="replace").strip()


def has_commit_tag(tag: str, pr_head_sha: str | None = None) -> bool:
    """Check if `[STACK BUMP]` tag is present in commit subject."""
    target = pr_head_sha or "HEAD"
    subject = get_commit_subject(target)
    if subject is None:
        return False
    return tag.lower() in subject.lower()


def main() -> int:
    pr_head_sha = os.environ.get("COMMIT_PREFIX_BYPASS_PR_HEAD_SHA") or os.environ.get(
        "STACK_BUMP_PR_HEAD_SHA"
    )
    bypass_from_commit = has_commit_tag("[STACK BUMP]", pr_head_sha=pr_head_sha)
    bypass_from_env = os.environ.get("COMMIT_PREFIX_BYPASS") == "1"
    bypass_ok = bypass_from_commit or bypass_from_env

    subject = get_commit_subject(pr_head_sha or "HEAD")
    if subject is None:
        sys.stderr.write("[ERROR] No commit subject available (git log failed)\n")
        return 2

    if bypass_ok:
        print("[COMMIT_PREFIX] bypass active — skipping prefix lint")
        return 0

    if PREFIX_VIOLATION_RE.match(subject):
        print(
            "[COMMIT_PREFIX] FAIL: commit subject starts with `@` (PowerShell here-string artifact):",
            file=sys.stderr,
        )
        print(f"  subject: {subject}", file=sys.stderr)
        print(
            "  Use `git commit -F <file>` instead of PowerShell `@'...'@` here-string.",
            file=sys.stderr,
        )
        print(
            "  To bypass intentionally, add `[STACK BUMP]` to the commit subject.",
            file=sys.stderr,
        )
        return 1

    print("[COMMIT_PREFIX] OK — commit subject does not start with `@`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
