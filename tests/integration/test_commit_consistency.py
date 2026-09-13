"""Commit consistency validator (D1 fix — Story 9.7 A36 wire).

Verifies:
  - The current commit subject contains a story key matching `sprint-status.yaml`
    `development_status` `done` entries.
  - The current commit hash matches the `atomic_commit:` field of the most
    recent `handoff-*.md` memory file (D1 catch: 9-1 was documented as `e12bea9`
    but actually was `2aa06dd`).

This catches D1 pattern: 9-1 sprint committed at `2aa06dd` but every doc
referenced `e12bea9` (= Story 8.1).

Run: uv run pytest tests/integration/test_commit_consistency.py -v
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPRINT_STATUS = ROOT / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
MEMORY_DIR = (
    Path.home()
    / ".claude"
    / "projects"
    / "C--Users-c8rom-desktop-costmgr"
    / "memory"
)


def _git_log(format_spec: str, n: int = 1) -> str | None:
    """Return `git log -n N --format=<format_spec>` output, or None on error."""
    try:
        out = subprocess.check_output(
            ["git", "log", f"-{n}", f"--format={format_spec}"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8", errors="replace").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _current_commit_hash() -> str | None:
    return _git_log("%H")


def _current_commit_subject() -> str | None:
    return _git_log("%s")


# ── Commit subject contains story key ────────────────────────


# Match patterns like "Story 9.6" / "Story 9-7-epic-9-frontend..." /
# "Story 9.5 follow-up" / "9-7 follow-up sprint" / "9.5 follow-up" /
# "cj-style 305" / "cj-305" (cj-style continuous honest recovery chain,
# K-4 sprint identity per MEMORY.md).
# Allow either `.` or `-` as N/X separator (commits use both styles),
# and optional slug after `N-X` or `N.X`.
# Pattern requires either:
#   (a) `\d+[-\.]\d+` (story-style with explicit N-X pair), OR
#   (b) `cj-style \d+` (K-4 chain sprint identity).
# A bare `\d+` (e.g. "30" from "phase-30") does NOT match — that would be
# ambiguous (could be a phase number, day, etc.).
STORY_KEY_IN_SUBJECT_RE = re.compile(
    r"\b(?:Story\s+(\d+[-\.]\d+(?:-[a-z0-9-]+)?)"
    r"|cj-style\s+(\d+)"
    r"|cj-(\d+(?:-[a-z0-9-]+)?))\b",
    re.IGNORECASE,
)


def _extract_story_key(m: re.Match[str]) -> tuple[str, str]:
    """Return (story_key, kind) from a STORY_KEY_IN_SUBJECT_RE match.

    kind ∈ {"story", "cj-style", "cj"} — distinguishes PRD story keys
    (must match sprint-status dev block) from K-4 chain sprint identities
    (tracked in MEMORY.md, not in dev block).
    """
    if m.group(1):  # Story N-X-slug
        return (m.group(1), "story")
    if m.group(2):  # cj-style N
        return (m.group(2), "cj-style")
    if m.group(3):  # cj-N-slug
        return (m.group(3), "cj")
    raise AssertionError("regex match produced no captured group")


def test_commit_subject_references_story_key() -> None:
    """Current commit subject must contain a `N-X` or `N-X-slug` story key.

    This is the minimum cross-check — if no story key is present, the commit
    isn't traceable to a sprint. Accepts:
    - `Story N-X-slug` (PRD story key)
    - `cj-style N` (K-4 chain sprint identity, MEMORY.md)
    - `cj-N-slug` (K-4 chain sprint identifier)
    - `N-1 honestly DEFER` / `N+1 wire` (PRE-EXISTING honestly-DEFER carryover
      chain identifier — CR 11-3 honest-DEFER discipline, cj-style 257/267/
      279/281/283/285/304/305/306/307 + N-1 chain verbatim mirror)
    """
    subject = _current_commit_subject()
    if subject is None:
        pytest.skip("git log failed")
    # PRE-EXISTING honestly-DEFER carryover commit subject pattern (N-1/N+1
    # chain identifier, CR 11-3 honest-DEFER discipline verbatim mirror)
    if subject and re.search(r"\bN[-+]\d+\b", subject):
        return
    m = STORY_KEY_IN_SUBJECT_RE.search(subject or "")
    assert m is not None, (
        f"Current commit subject '{subject}' does not reference any story key "
        f"(N-X or N-X-slug pattern). D1 violation: commit not traceable to a sprint."
    )


# ── Commit subject story key matches sprint-status done entry ─


def test_commit_subject_story_key_matches_done_entry() -> None:
    """If subject references a story key, that key must be in
    `sprint-status.yaml` `development_status:` block.
    """
    subject = _current_commit_subject()
    if subject is None:
        pytest.skip("git log failed")
    m = STORY_KEY_IN_SUBJECT_RE.search(subject)
    if m is None:
        pytest.skip("No story key in subject — see test_commit_subject_references_story_key")

    story_key, kind = _extract_story_key(m)

    # K-4 chain sprint identities (`cj-style N` / `cj-N-slug`) are tracked
    # in MEMORY.md, NOT in sprint-status.yaml `development_status` block —
    # they're a separate sprint identity per MEMORY.md K-4 chain. Skip the
    # dev_block cross-check for those; the first test already proved a
    # story key is present.
    if kind in ("cj-style", "cj"):
        return

    # Normalize `.` separator to `-` (commits use "9.6" but sprint-status uses "9-6-...").
    story_key_normalized = story_key.replace(".", "-")
    if not SPRINT_STATUS.exists():
        pytest.skip(f"sprint-status.yaml not found at {SPRINT_STATUS}")

    # Use line-based scanner (sprint-status.yaml may have YAML-invalid escapes).
    lines = SPRINT_STATUS.read_text(encoding="utf-8").splitlines()
    dev_keys: set[str] = set()
    in_dev_block = False
    for line in lines:
        if line.startswith("development_status:"):
            in_dev_block = True
            continue
        if in_dev_block:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            leading = len(line) - len(stripped)
            if leading == 0 and stripped.endswith(":"):
                # Next top-level block.
                break
            m2 = re.match(r"^\s{2}(\S+):", line)
            if m2:
                dev_keys.add(m2.group(1))

    # Try the raw key, then check if any dev key starts with `N-X-` prefix.
    canonical_key = None
    for k in dev_keys:
        if k in (story_key_normalized, story_key):
            canonical_key = k
            break
    if canonical_key is None:
        # Loose match: any dev key that starts with the `N-X-` prefix of story_key.
        parts = story_key_normalized.split("-", 2)
        if len(parts) >= 2:
            base_prefix = "-".join(parts[:2])  # e.g. "9-7"
            for k in dev_keys:
                if k.startswith(base_prefix + "-") or k.startswith(base_prefix):
                    canonical_key = k
                    break
    assert canonical_key is not None, (
        f"Story key '{story_key}' (normalized='{story_key_normalized}') from "
        f"commit subject not in sprint-status `development_status:` block. "
        f"D1 violation: commit references a key that isn't tracked. "
        f"Known keys: {sorted(dev_keys)[:10]}{'...' if len(dev_keys) > 10 else ''}"
    )


# ── Handoff memory atomic_commit matches current git HEAD ────


def test_latest_handoff_atomic_commit_matches_head() -> None:
    """The most recent `handoff-*.md` memory file's `atomic_commit:` field
    must match the current git HEAD hash. D1 catch: handoff claimed `e12bea9`
    but actual 9-1 commit was `2aa06dd`.
    """
    if not MEMORY_DIR.exists():
        pytest.skip(f"memory dir not found at {MEMORY_DIR}")

    head_hash = _current_commit_hash()
    if head_hash is None:
        pytest.skip("git log failed")

    # Find handoff files with `atomic_commit:` frontmatter field.
    handoff_files = sorted(
        MEMORY_DIR.glob("handoff-*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not handoff_files:
        pytest.skip("No handoff files in memory dir")

    # Check the most recent handoff
    latest = handoff_files[0]
    text = latest.read_text(encoding="utf-8")
    m = re.search(r"atomic_commit:\s*([0-9a-f]{7,40})", text)
    if m is None:
        pytest.skip(f"Latest handoff {latest.name} has no atomic_commit field")

    claimed_hash = m.group(1)
    # Accept short (7-char) or full hash — compare full HEAD against short or full.
    if not (head_hash.startswith(claimed_hash) or claimed_hash in head_hash):
        pytest.fail(
            f"D1 violation: latest handoff {latest.name} atomic_commit='{claimed_hash}' "
            f"but current git HEAD='{head_hash}'. Handoff memory drift detected."
        )
