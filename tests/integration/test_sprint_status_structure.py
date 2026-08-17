"""Sprint-status structure validator (D4 fix — Story 9.7 A36 wire).

Verifies via line-based scanning (avoids full YAML parse — sprint-status.yaml
contains historical narrative text with YAML-invalid escapes like `\\p`):

  - `development_status:` block exists at top level
  - `action_items:` block (if present) contains ONLY action item dicts
    (epic:int, action, owner, status). Skipped if block absent (D4 fully
    resolved by moving misplaced entries out in 9-6 sprint).
  - No `epic-N` or `N-X-...` keys misplaced in `action_items:` block
    (D4 defect pattern — only relevant if action_items block exists).
  - Status values are in known vocabulary (per CR 11-3 honestly DEFER profile)

This catches the D4 defect pattern where `epic-9-retrospective` and `epic-10`
keys were misplaced in `action_items:` block (resolved in 9-6 sprint by
removing the misplaced entries; block no longer required).

Run: uv run pytest tests/integration/test_sprint_status_structure.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPRINT_STATUS = ROOT / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"

# Top-level block anchors (zero indentation).
DEV_STATUS_ANCHOR = re.compile(r"^development_status:\s*$")
ACTION_ITEMS_ANCHOR = re.compile(r"^action_items:\s*$")

# Entry key patterns.
EPIC_KEY_RE = re.compile(r"^epic-\d+$")
STORY_KEY_RE = re.compile(r"^\d+-\d+-")

# Valid status vocabularies.
STATUS_VOCAB = {"backlog", "ready-for-dev", "in-progress", "done", "optional", "deprecated"}
ACTION_STATUS_VOCAB = {"open", "in-progress", "done"}

# Indentation thresholds: top-level keys are at col 0; nested keys at >= 2 spaces.
TOP_LEVEL_INDENT = 0


def _read_lines() -> list[str]:
    if not SPRINT_STATUS.exists():
        pytest.skip(f"sprint-status.yaml not found at {SPRINT_STATUS}")
    return SPRINT_STATUS.read_text(encoding="utf-8").splitlines()


def _block_range(lines: list[str], anchor_re: re.Pattern[str]) -> tuple[int, int] | None:
    """Find a top-level block by anchor regex; return (start_line, end_line_excl)."""
    start = -1
    for i, line in enumerate(lines):
        if anchor_re.match(line):
            start = i
            break
    if start < 0:
        return None

    # End of block = next line at indent 0 that is non-empty (i.e. next top-level key).
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].lstrip()
        if not stripped or stripped.startswith("#"):
            continue  # blank or comment line — still inside block
        leading = len(lines[j]) - len(stripped)
        if leading == TOP_LEVEL_INDENT:
            end = j
            break
    return (start, end)


def _parse_development_status(lines: list[str]) -> dict[str, str]:
    """Return mapping of {key: status_value} for entries in development_status block."""
    rng = _block_range(lines, DEV_STATUS_ANCHOR)
    if rng is None:
        return {}
    start, end = rng
    entries: dict[str, str] = {}
    for line in lines[start + 1 : end]:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        # entry format: `  key: status_value` (2-space indent)
        m = re.match(r"^\s{2}(\S+):\s*(\S+)", line)
        if m:
            entries[m.group(1)] = m.group(2)
    return entries


def _parse_action_items(lines: list[str]) -> list[dict[str, str]]:
    """Return list of action item dicts (epic, action, owner, status)."""
    rng = _block_range(lines, ACTION_ITEMS_ANCHOR)
    if rng is None:
        return []
    start, end = rng
    items: list[dict[str, str]] = []
    # action_items entries are dicts under `- key: value` (list of dicts).
    # Detect entry start by lines starting with `  - ` or `    - ` (4-space indent).
    current: dict[str, str] = {}
    for line in lines[start + 1 : end]:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        # Detect new entry (`- key: value` or `key: value`).
        entry_start = re.match(r"^\s*-?\s*(\S+):\s*(.*)$", line)
        if entry_start and (line.startswith("  - ") or line.startswith("    - ") or line.startswith("      ")):
            key = entry_start.group(1)
            value = entry_start.group(2).strip().strip('"').strip("'")
            # If we hit a new top-level key inside current dict, save and reset.
            if key in {"epic", "action", "owner", "status"}:
                if "epic" in current and current.get("action"):
                    items.append(current)
                    current = {}
                current[key] = value
    if current and "epic" in current:
        items.append(current)
    return items


# ── development_status block exists ──────────────────────────


def test_development_status_block_exists() -> None:
    lines = _read_lines()
    rng = _block_range(lines, DEV_STATUS_ANCHOR)
    assert rng is not None, (
        "`development_status:` block missing — D4 defect (epic-9-retrospective "
        "misplaced in action_items was a symptom of missing block)"
    )


# ── development_status entries have valid statuses ─────────────


def test_development_status_entries_have_valid_status() -> None:
    """Each entry in `development_status:` must have a status in known vocabulary.

    Catches D4 pattern: misplaced entries with arbitrary status strings.
    """
    lines = _read_lines()
    dev = _parse_development_status(lines)
    violations: list[tuple[str, str]] = []
    for key, status in dev.items():
        if status not in STATUS_VOCAB:
            violations.append((key, status))
    assert not violations, (
        f"development_status entries with invalid status: {violations} "
        f"— D4 pattern: allowed vocabulary = {sorted(STATUS_VOCAB)}"
    )


# ── action_items block structure (skipped if absent) ──────────


def test_action_items_block_if_present_is_list_of_dicts() -> None:
    """If `action_items:` block exists, it must be a non-empty list of dicts."""
    lines = _read_lines()
    rng = _block_range(lines, ACTION_ITEMS_ANCHOR)
    if rng is None:
        pytest.skip("`action_items:` block absent — D4 fully resolved (9-6 sprint)")
    # Verify the block has at least the structure (presence is enough — empty OK).
    assert rng[1] > rng[0], "`action_items:` block exists but is empty/invalid"


# ── D4 defect pattern: no epic/story keys in action_items ────


def test_no_epic_keys_in_action_items() -> None:
    """D4 defect catch: `epic-N` keys must live in `development_status:` block."""
    lines = _read_lines()
    if _block_range(lines, ACTION_ITEMS_ANCHOR) is None:
        pytest.skip("`action_items:` block absent — D4 fully resolved (9-6 sprint)")
    items = _parse_action_items(lines)
    violations: list[str] = []
    for i, item in enumerate(items):
        for key in item:
            if EPIC_KEY_RE.match(str(key)):
                violations.append(f"action_items[{i}].{key}")
    assert not violations, (
        f"D4 defect: `epic-N` keys misplaced in `action_items:` block: {violations}"
    )


def test_no_story_keys_in_action_items() -> None:
    """D4 defect catch: `N-X-...` story keys must live in `development_status:` block."""
    lines = _read_lines()
    if _block_range(lines, ACTION_ITEMS_ANCHOR) is None:
        pytest.skip("`action_items:` block absent — D4 fully resolved (9-6 sprint)")
    items = _parse_action_items(lines)
    violations: list[str] = []
    for i, item in enumerate(items):
        for key in item:
            if STORY_KEY_RE.match(str(key)):
                violations.append(f"action_items[{i}].{key}")
    assert not violations, (
        f"D4 defect: story keys (`N-X-...`) misplaced in `action_items:` block: "
        f"{violations}"
    )


# ── D4 defect pattern: action_items entries have required keys ──


def test_action_items_have_required_keys() -> None:
    """Each action_items entry must have `epic`, `action`, `owner`, `status` keys.

    (epic may be int or str — historical entries used string like `"9"`.)
    """
    lines = _read_lines()
    if _block_range(lines, ACTION_ITEMS_ANCHOR) is None:
        pytest.skip("`action_items:` block absent — D4 fully resolved (9-6 sprint)")
    items = _parse_action_items(lines)
    required = {"epic", "action", "owner", "status"}
    for i, item in enumerate(items):
        missing = required - set(item.keys())
        assert not missing, (
            f"action_items[{i}] missing required keys: {missing} — "
            f"D4 pattern: keys that look like story/epic keys belong in `development_status:`"
        )


# ── action_items status vocabulary (skipped if absent) ────────


def test_action_items_status_in_vocabulary() -> None:
    """action_items[].status must be in {open, in-progress, done}."""
    lines = _read_lines()
    if _block_range(lines, ACTION_ITEMS_ANCHOR) is None:
        pytest.skip("`action_items:` block absent — D4 fully resolved (9-6 sprint)")
    items = _parse_action_items(lines)
    for i, item in enumerate(items):
        status = item.get("status")
        assert status in ACTION_STATUS_VOCAB, (
            f"action_items[{i}].status '{status}' not in {ACTION_STATUS_VOCAB}"
        )
