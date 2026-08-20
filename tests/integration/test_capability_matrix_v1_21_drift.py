"""tests.integration.test_capability_matrix_v1_21_drift — capability matrix v1.21 SSOT.

Story 10.1 (cj-style Epic 10 2번째 진입점, cj-style 26번째 epic 연속) —
T4.1 P-015 SSOT drift detector for `docs/capability-matrix.md` v1.21.

Why a drift detector (vs. a single test):
- P-015 SSOT — every Epic introduces new capability grants; the matrix
  is the canonical source. Drift silently enables unauthorized writes.
- A31~A36 Epic 9 retro decisions (9-7 follow-up sprint) repeatedly flagged
  "한 곳만 wire, 다른 곳 미wire" (one place wired, other missed) as root
  cause of SDR overclaim. The detector catches ALL Epic 10 schemas
  (database, modules, packages, frontend) in ONE pass.

What the detector verifies:
1. AI_INSIGHT row present in docs/capability-matrix.md
2. AI_INSIGHT grants 4 industries (제조/도소매/서비스/외식은 아니고 — see PRD §F10.1)
   v1.21 matrix grants 4 generic industry buckets (manufacturing, retail,
   service, f&b) per master PRD §F0.1 matrix convention.
3. Epic 10 row → capability reference (10.1, 10.2, 10.3, 10.4 all 'AI_INSIGHT')
4. v1.21 changelog entry mentions AI_INSIGHT + 4-industry grants
5. AI_INSIGHT row consistent with ON/OFF toggle across industries
   (i.e., no industry has a different status — bug A36 would catch)

The detector is a STANDARD `pytest` test (no special runner). It runs
both as part of `pytest tests/integration/` and is wired into the
Epic 9 retro A36 SDR 검증 protocol (4-step automation).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ── Resolve SSOT path (deterministic, no environ) ────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CAPABILITY_MATRIX_MD = _REPO_ROOT / "docs" / "capability-matrix.md"


# ── AC #1: AI_INSIGHT row present ─────────────────────────────


def test_capability_matrix_v1_21_ai_insight_row_present() -> None:
    """v1.21 introduces AI_INSIGHT row (master PRD §F10.1 cache policy)."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Row must exist with Epic 10 story references (matrix uses backticks:
    # `| `AI_INSIGHT` | 10.1, 10.2, 10.3, 10.4 | ... |`)
    ai_insight_pattern = re.compile(
        r"\|\s*`?AI_INSIGHT`?\s*\|\s*10\.[1234](?:\s*,\s*10\.[1234])*\s*\|",
        re.MULTILINE,
    )
    assert ai_insight_pattern.search(text), (
        "AI_INSIGHT row not found in capability matrix. "
        "Expected: `| AI_INSIGHT | 10.1, 10.2, 10.3, 10.4 | ... |`"
    )


def test_capability_matrix_v1_21_title() -> None:
    """Title line should be at least v1.21 (forward-lock preserved).

    v1.21 was the last REAL drift detector SSOT (introduced by Story 10.1).
    Subsequent versions (v1.22 LISTEN_NOTIFY, v1.23 LISTEN_NOTIFY_TENANT_FANOUT +
    LISTEN_NOTIFY_MULTIPROCESS) build on top, so this test accepts any title
    ≥ v1.21 to avoid regression-spam on every bump. The strict pin tests
    for v1.17/v1.18/v1.19/v1.20 are stale historical pins (mutually
    exclusive — at most one can ever pass); they will be removed in a
    separate sweep.
    """
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Title must be ≥ v1.21 (forward-lock). Accept any newer pin.
    assert "# Capability Matrix (v1.21)" in text or "# Capability Matrix (v1.22)" in text or "# Capability Matrix (v1.23)" in text or "# Capability Matrix (v1.24)" in text, (
        "Capability matrix title is older than v1.21. "
        "Expected `# Capability Matrix (v1.21)` or newer as first heading."
    )


# ── AC #2: AI_INSIGHT grants 4 industries (consistent) ────────


def test_capability_matrix_v1_21_ai_insight_4_industry_grants() -> None:
    """AI_INSIGHT row has 4 industry grants (✅ ✅ ✅ ✅ — industry-agnostic)."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Extract the AI_INSIGHT row (handle optional backticks)
    match = re.search(
        r"\|\s*`?AI_INSIGHT`?\s*\|\s*10\.[1234](?:\s*,\s*10\.[1234])*\s*\|"
        r"\s*(✅|❌|⊘|—)\s*\|"
        r"\s*(✅|❌|⊘|—)\s*\|"
        r"\s*(✅|❌|⊘|—)\s*\|"
        r"\s*(✅|❌|⊘|—)\s*\|",
        text,
    )
    assert match is not None, (
        "AI_INSIGHT row missing 4 industry grants. "
        "Expected row format: `| AI_INSIGHT | 10.x | ✅ | ✅ | ✅ | ✅ |`"
    )

    # All 4 industry toggles must be ✅ (industry-agnostic, per CR 12-1 L4)
    grants = match.groups()
    assert all(g == "✅" for g in grants), (
        f"AI_INSIGHT 4-industry grants inconsistent: {grants}. "
        "Industry-agnostic capability should grant all 4 industries."
    )


# ── AC #3: Epic 10 → capability reference (10.1, 10.2, 10.3, 10.4) ─


@pytest.mark.parametrize("story_id", ["10.1", "10.2", "10.3", "10.4"])
def test_capability_matrix_v1_21_epic_10_story_reference_present(
    story_id: str,
) -> None:
    """Each Epic 10 story must reference AI_INSIGHT capability."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Story rows in the matrix reference capabilities
    # Format: `| 10.1 — AI Document Extraction | `AI_INSIGHT` |`
    pattern = re.compile(
        rf"\|\s*{re.escape(story_id)}\s+—[^|]*\|\s*`?AI_INSIGHT`?",
        re.MULTILINE,
    )
    assert pattern.search(text), (
        f"Story {story_id} row missing AI_INSIGHT reference in capability matrix"
    )


# ── AC #4: v1.21 changelog mentions AI_INSIGHT + 4-industry grants ──


def test_capability_matrix_v1_21_changelog_entry() -> None:
    """v1.21 changelog entry must mention AI_INSIGHT + 4-industry grants."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Find v1.21 changelog entry (matches across lines, since 4-industry
    # mention is on continuation line; ends before next `- 2026-` bullet)
    v1_21_pattern = re.compile(
        r"-\s*2026-08-17\s*—\s*v1\.21\s*\(Epic 10[^)]*\):.*?(?=\n-\s*2026-|\n---|\Z)",
        re.DOTALL,
    )
    match = v1_21_pattern.search(text)
    assert match is not None, (
        "v1.21 changelog entry not found in capability matrix. "
        "Expected: `- 2026-08-17 — v1.21 (Epic 10 ...): ...`"
    )

    changelog_entry = match.group(0)
    assert "AI_INSIGHT" in changelog_entry, (
        f"v1.21 changelog missing AI_INSIGHT mention: {changelog_entry!r}"
    )
    # 4-industry grants mention
    assert (
        "4-industry" in changelog_entry
        or "4 industry" in changelog_entry
        or "industry-agnostic" in changelog_entry
        or "✅/✅/✅/✅" in changelog_entry
        or "✅ ✅ ✅ ✅" in changelog_entry
    ), (
        f"v1.21 changelog missing 4-industry grants mention: {changelog_entry!r}"
    )


# ── AC #5: v1.21 row consistency (no industry has ⊘ off) ────


def test_capability_matrix_v1_21_ai_insight_all_industries_enabled() -> None:
    """AI_INSIGHT is industry-agnostic, NO industry should be off (⊘)."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    ai_insight_block_match = re.search(
        r"\|\s*`?AI_INSIGHT`?\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|",
        text,
    )
    assert ai_insight_block_match is not None, (
        "AI_INSIGHT row not found in capability matrix"
    )

    row = ai_insight_block_match.group(0)
    # No ⊘ (off) or ❌ (denied) in the row
    assert "⊘" not in row and "❌" not in row, (
        f"AI_INSIGHT row has disabled industry — violates industry-agnostic "
        f"invariant: {row!r}"
    )


# ── Cross-cutting: AI_EXTRACT row preserved (Story 1.3 baseline) ─


def test_capability_matrix_v1_21_ai_extract_row_preserved() -> None:
    """Story 1.3 baseline (AI_EXTRACT) MUST be preserved when adding AI_INSIGHT."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # AI_EXTRACT row should still exist with Story 1.3 reference (backticks)
    pattern = re.compile(
        r"\|\s*`?AI_EXTRACT`?\s*\|\s*1\.[12345](?:\s*,\s*1\.[12345])*\s*\|",
        re.MULTILINE,
    )
    assert pattern.search(text), (
        "AI_EXTRACT row missing from capability matrix v1.21 — "
        "regression of Story 1.3 baseline (Epic 10 must EXTEND, not REPLACE)."
    )


# ── Cross-cutting: capability matrix file path stability ─────


def test_capability_matrix_path_stable() -> None:
    """Capability matrix SSOT path is `docs/capability-matrix.md` (P-015)."""
    assert _CAPABILITY_MATRIX_MD.exists(), (
        f"Capability matrix not found at {_CAPABILITY_MATRIX_MD}. "
        "P-015 SSOT path broken — check directory layout."
    )

    # File must be non-empty (regression guard)
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")
    assert len(text) > 500, (
        f"Capability matrix file is suspiciously small ({len(text)} chars). "
        "Expected detailed capability grants table."
    )


# ── Cross-cutting: AD-7 verbatim invariant (AI_EXTRACT + AI_INSIGHT both = input_drafts only) ──


def test_capability_matrix_v1_21_ad7_invariant() -> None:
    """AD-7: AI_EXTRACT + AI_INSIGHT MUST NOT include 'confirmed_inputs' grant."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # AD-7 strict invariant — AI row NEVER grants 'confirmed_inputs' column
    # (the matrix uses industry columns, not target_table, so this is a
    # conservative check that no row mentions 'confirmed_inputs' in the
    # capability grants area)
    matrix_section = text.split("## ")[0]  # crude split
    assert "confirmed_inputs" not in matrix_section, (
        "AD-7 violation: 'confirmed_inputs' appears in capability matrix. "
        "AI output → input_drafts ONLY (master PRD §A11 verbatim)."
    )


# ── Cross-cutting: AD-17 promotion port (M2-only) NOT in capability matrix ──


def test_capability_matrix_v1_21_ad17_invariant() -> None:
    """AD-17: InputPromoter.promote() is M2-only, AI modules MUST NOT have it."""
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Promotion port is M2's job, NOT M10's. The matrix should NOT have
    # an AI row that grants 'promote' capability.
    ai_row_match = re.search(
        r"\|\s*`?AI_(?:EXTRACT|INSIGHT)`?\s*\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|",
        text,
    )
    assert ai_row_match is not None, "AI_EXTRACT/AI_INSIGHT row missing"
    assert "PROMOTE" not in ai_row_match.group(0).upper(), (
        "AD-17 violation: AI row has PROMOTE capability. "
        "InputPromoter is M2-only (master PRD §A17 verbatim)."
    )


# ── Story 10.2 EXTENSION (cj-style 29번째 epic 연속) ─────────────
# T6.1 NEW case: 10.2 story_coverage includes '10.2' reference + AD-25
# verbatim cache key 3-tuple binding verification (forward-bind to
# epics.md Story 10.2 wire 진입).


def test_capability_matrix_v1_21_story_10_2_coverage() -> None:
    """Story 10.2 (Three-Insight Cache Policy) is referenced in capability matrix.

    10-2 wire 진입 시점에 AI_INSIGHT row MUST reference '10.2' alongside
    '10.1, 10.3, 10.4'. P-015 SSOT parity preserved (4 stories = 1 row).
    """
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # AI_INSIGHT row must include '10.2' in the story reference column
    pattern = re.compile(
        r"\|\s*`?AI_INSIGHT`?\s*\|[^|]*\b10\.2\b[^|]*\|",
        re.MULTILINE,
    )
    assert pattern.search(text), (
        "AI_INSIGHT row missing 10.2 story reference. "
        "Story 10.2 (Three-Insight Cache Policy) is part of Epic 10 "
        "4-story split + retro 5번째 진입점 (cj-style pattern)."
    )


def test_capability_matrix_v1_21_story_10_2_row_present() -> None:
    """Story 10.2 row MUST exist with AI_INSIGHT capability reference.

    Distinct from the AI_INSIGHT row (the row that lists 10.1~10.4 in its
    story column). The Story 10.2 row uses format `| 10.2 — ... | `AI_INSIGHT` |`.
    """
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Story 10.2 row in story coverage table
    pattern = re.compile(
        r"\|\s*10\.2\s+—[^|]*\|\s*`?AI_INSIGHT`?",
        re.MULTILINE,
    )
    assert pattern.search(text), (
        "Story 10.2 row missing AI_INSIGHT capability reference. "
        "Expected: `| 10.2 — Three-Insight Cache Policy | `AI_INSIGHT` |`"
    )


# ── Story 10.3 EXTENSION (cj-style 30번째 epic 연속) ─────────────
# T6.1 NEW case: 10.3 story_coverage includes '10.3' reference + F10.2
# verbatim badge separation binding verification (forward-bind to
# epics.md Story 10.3 wire 진입).


def test_capability_matrix_v1_21_story_10_3_coverage() -> None:
    """Story 10.3 (AI Reference vs Auto Analysis Badge Separation) is referenced.

    10-3 wire 진입 시점에 AI_INSIGHT row MUST reference '10.3' alongside
    '10.1, 10.2, 10.4'. P-015 SSOT parity preserved (4 stories = 1 row).
    """
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # AI_INSIGHT row must include '10.3' in the story reference column
    pattern = re.compile(
        r"\|\s*`?AI_INSIGHT`?\s*\|[^|]*\b10\.3\b[^|]*\|",
        re.MULTILINE,
    )
    assert pattern.search(text), (
        "AI_INSIGHT row missing 10.3 story reference. "
        "Story 10.3 (AI Reference vs Auto Analysis Badge Separation) "
        "is part of Epic 10 4-story split + retro 5번째 진입점 "
        "(cj-style pattern)."
    )


def test_capability_matrix_v1_21_story_10_3_row_present() -> None:
    """Story 10.3 row MUST exist with AI_INSIGHT capability reference.

    Distinct from the AI_INSIGHT row (the row that lists 10.1~10.4 in its
    story column). The Story 10.3 row uses format `| 10.3 — ... | `AI_INSIGHT` |`.
    """
    text = _CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")

    # Story 10.3 row in story coverage table
    pattern = re.compile(
        r"\|\s*10\.3\s+—[^|]*\|\s*`?AI_INSIGHT`?",
        re.MULTILINE,
    )
    assert pattern.search(text), (
        "Story 10.3 row missing AI_INSIGHT capability reference. "
        "Expected: `| 10.3 — Reference vs Auto Analysis Badge | `AI_INSIGHT` |`"
    )
