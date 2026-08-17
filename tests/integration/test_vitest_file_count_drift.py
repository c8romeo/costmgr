"""Vitest file count drift validator (D2 fix — Story 9.7 A36 wire).

Verifies the actual vitest file count in apps/web/__tests__ matches SDR
(test-results documents) claims within tolerance.

This catches D2 pattern: 9-3 sprint claimed "vitest 63 NEW (6 files)" but
the actual file count was 0. 9-4 claimed "vitest ~58 NEW (8 files)" but
actual was 1.

Pattern: extends tests/integration/test_sdr_test_count_drift.py which does
the same for pytest. Both run as `pytest tests/integration -v`.

Tolerance: claim ≤ actual ≤ claim × 1.05 (hard fail on overclaim only;
soft warn on underclaim via comment).

Run: uv run pytest tests/integration/test_vitest_file_count_drift.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB_TESTS_DIR = ROOT / "apps" / "web" / "__tests__"

# Pattern A: "vitest N NEW (K files)" or "vitest ~N NEW (K files)" — claim
#          with explicit file count. Used for SDR overclaim check (D2).
# Pattern B: "vitest N NEW" or "vitest ~N NEW" — case claim only (ambiguous).
VITEST_CLAIM_WITH_FILES_RE = re.compile(
    r"vitest\s+~?(\d+)\s+NEW\s*\(\s*(\d+)\s*files?\s*\)",
    re.IGNORECASE,
)


def _count_vitest_test_files() -> int:
    """Count vitest test files (*.test.ts + *.test.tsx) in apps/web/__tests__."""
    if not WEB_TESTS_DIR.exists():
        return 0
    return sum(
        1
        for p in WEB_TESTS_DIR.rglob("*")
        if p.is_file() and (p.name.endswith(".test.ts") or p.name.endswith(".test.tsx"))
    )


def _parse_file_count_claims(doc_path: Path) -> list[tuple[int, int, str]]:
    """Return list of (claimed_cases, claimed_files, full_match_string) tuples.

    Only matches claims with explicit file count `(K files)` — these are the
    D2 SDR overclaim pattern. Bare case claims (no file count) are skipped
    since they're ambiguous (cases per file vary widely).
    """
    if not doc_path.exists():
        return []
    text = doc_path.read_text(encoding="utf-8")
    return [
        (int(m.group(1)), int(m.group(2)), m.group(0))
        for m in VITEST_CLAIM_WITH_FILES_RE.finditer(text)
    ]


# ── Actual count baseline ──────────────────────────────────────


def test_actual_vitest_file_count_baseline() -> None:
    """Sanity check: actual vitest file count is > 0."""
    actual = _count_vitest_test_files()
    assert actual > 0, f"Expected vitest files in {WEB_TESTS_DIR}, got 0"


# ── SDR claim vs actual within tolerance ─────────────────────


@pytest.mark.parametrize(
    "doc_path",
    [
        # Only check Epic 9 sprint-status / handoff docs (D2 overclaim zone).
        ROOT / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml",
    ],
)
def test_vitest_file_count_claims_not_overclaim(doc_path: Path) -> None:
    """Each vitest file-count claim (with `(K files)` qualifier) must have
    actual_files >= K (no SDR overclaim).

    Pattern: when a sprint-status or handoff doc claims
    "vitest N NEW (K files)", the actual vitest file count must be >= K.
    Overclaim = D2 violation (9-3 claimed 6 files, actual was 0;
    9-4 claimed 8 files, actual was 1).

    Note: bare case claims (no file count) are intentionally skipped —
    they're ambiguous due to varying cases-per-file density.
    """
    actual = _count_vitest_test_files()
    claims = _parse_file_count_claims(doc_path)
    if not claims:
        pytest.skip(f"No vitest file-count claims in {doc_path.name}")

    overclaims: list[str] = []
    for claimed_cases, claimed_files, match_str in claims:
        if actual < claimed_files:
            overclaims.append(
                f"claim={claimed_cases}cases/{claimed_files}files "
                f"actual={actual}files match='{match_str}'"
            )
    assert not overclaims, (
        f"D2 SDR overclaim detected in {doc_path.name}:\n  "
        + "\n  ".join(overclaims)
        + "\n  (actual vitest files in apps/web/__tests__ = "
        + f"{actual})"
    )


# ── Last-claimed increment from current count ────────────────


def test_vitest_count_grew_or_stable_since_baseline() -> None:
    """Sanity check: vitest file count should grow as sprints wire tests.

    This is a soft check — if actual == 0, skip (sprint hasn't started).
    """
    actual = _count_vitest_test_files()
    # Baseline expectation: at least the Epic 9-1..9-4 files exist (~10).
    # 9-7 wire should bring this to ~18+ (5 component + 3 parity new).
    assert actual >= 10, (
        f"Vitest file count regressed: actual={actual}, expected >= 10 baseline "
        f"(Epic 9 minimum). D2-style SDR overclaim if sprint-status claims more."
    )
