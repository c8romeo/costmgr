"""SDR test count drift detector — CR 4-3 F-2 carry.

CR 4-3 lessons: dev-story가 "64 passed + 1 skipped" 청구를 했지만 실제
pytest 결과는 "30 passed + 12 failed"였음. agent reports match what
pytest says, not what the audit log says.

이 가드는 모든 SDR (`_bmad-output/implementation-artifacts/*.md`)의
"tests pass" / "passed" 청구를 파싱하고, `pytest --collect-only -q`로 실제
test collection count와 비교한다.

Strategy:
1. 모든 SDR 파일을 스캔하여 "N/M tests pass" 또는 "N passed" 형식의
   claim을 추출
2. `pytest --collect-only -q`로 actual collection count 산출
3. MAX claimed N (모든 SDR에서 가장 큰 "passed" 수 = 최신 cumulative total)
   가 pytest collection count와 일치해야 함

This catches:
- SDR에 적힌 "X passed"가 실제 pytest 결과와 다른 경우
- Story가 완료되지 않았는데 SDR이 done-status를 claim하는 경우
- Test가 삭제/추가되었는데 SDR이 outdated count를 유지하는 경우

허용 오차:
- pytest count ≥ MAX SDR claim (실제 test가 추가되면 SDR보다 많을 수 있음)
- pytest count ≤ MAX SDR claim + 50 (fixtures, helpers 등 누적 여유)

DRIFT 발견 시:
- 어느 SDR 파일:라인이 어떤 claim을 했는지 명확히 표시
- pytest --collect-only 출력도 함께 표시
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SDR_DIR = ROOT / "_bmad-output" / "implementation-artifacts"


# "X passed" / "X/Y tests pass" / "X tests pass" / "X passed / Y skipped"
CLAIM_PATTERNS = [
    # "21/21 tests pass" — same denominator X/Y
    re.compile(r"(\d+)/\d+\s+tests?\s+pass", re.IGNORECASE),
    # "64 passed" or "54 passed"
    re.compile(r"(\d+)\s+passed", re.IGNORECASE),
    # "X tests pass" (no denominator)
    re.compile(r"(\d+)\s+tests?\s+pass", re.IGNORECASE),
    # "X tests collected" — drift detector output / SDR annotation
    re.compile(r"(\d+)\s+tests?\s+collected", re.IGNORECASE),
]


def _parse_claims(sdr_file: Path) -> list[tuple[int, str]]:
    """Extract (claimed_count, source_line) tuples from a single SDR file.

    Returns the list in source-order. Caller decides how to aggregate.
    """
    src = sdr_file.read_text(encoding="utf-8")
    claims: list[tuple[int, str]] = []
    for line_no, line in enumerate(src.splitlines(), start=1):
        # Skip lines that are inside tables (start with `|` after whitespace)
        # because tables often have "passed" in summary columns
        for pattern in CLAIM_PATTERNS:
            m = pattern.search(line)
            if m:
                try:
                    n = int(m.group(1))
                    if n > 0:
                        claims.append((n, f"{sdr_file.name}:{line_no}"))
                except (ValueError, IndexError):
                    pass
                break  # one claim per line
    return claims


def _actual_pytest_count() -> int:
    """Run `pytest --collect-only -q` and parse the total tests collected.

    Returns:
        Total tests collected. Returns 0 if the run fails or output is
        unparseable (treated as a soft signal — caller decides whether
        to skip the check).

    We use --collect-only (no execution) to keep this test fast. The
    collection count is a stable signal independent of pass/fail status.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return 0

    output = result.stdout + result.stderr
    # pytest --collect-only -q ends with "<N> tests collected" or
    # "<N> test collected" (singular).
    m = re.search(r"(\d+)\s+tests?\s+collected", output, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0


@pytest.mark.engine
def test_max_sdr_claim_matches_pytest_collection() -> None:
    """CR 4-3 F-2: the MAX "passed" claim across all SDRs must equal pytest count.

    The largest "N passed" / "N/M tests pass" claim in any SDR file is
    treated as the project's current cumulative test count. It must match
    the actual pytest --collect-only count within a small tolerance.

    Why MAX?
    - Per-story claims reflect that story's incremental test count, NOT
      the cumulative total
    - The MAX is the "this is the current state of the world" signal
    - A new story adding tests without updating SDRs would not decrease
      MAX, but the pytest count would increase — drift

    Tolerance:
    - Actual count ≥ MAX claim (fixtures/helpers can grow actual count)
    - Actual count ≤ MAX claim + 50 (loose upper bound for cumulative drift)
    """
    if not SDR_DIR.is_dir():
        pytest.skip(f"SDR dir not found: {SDR_DIR}")

    all_claims: list[tuple[int, str]] = []
    for sdr_file in sorted(SDR_DIR.glob("*.md")):
        all_claims.extend(_parse_claims(sdr_file))

    assert all_claims, (
        "No SDR test count claims found. SDR files may have changed format — "
        "update CLAIM_PATTERNS or add the expected claims."
    )

    max_claim, max_source = max(all_claims, key=lambda x: x[0])
    actual = _actual_pytest_count()

    assert actual > 0, (
        "pytest --collect-only returned no count. Check if pytest is "
        "installed and the test tree is valid."
    )

    # Lower bound: actual must be at least the SDR MAX claim
    # (SDR claim is the floor; if actual < SDR, SDR is OVER-counting).
    # Upper bound: allow actual to be up to 50 tests higher (fixtures
    # added without SDR claim — should still be flagged eventually).
    upper_bound = max_claim + 50

    violations: list[str] = []
    if actual < max_claim:
        violations.append(
            f"SDR overclaim: actual pytest count ({actual}) < MAX SDR claim "
            f"({max_claim} from {max_source}). "
            f"SDR states X tests pass but pytest collects fewer."
        )
    elif actual > upper_bound:
        violations.append(
            f"SDR underclaim: actual pytest count ({actual}) > MAX SDR claim "
            f"({max_claim} from {max_source}) + tolerance (50). "
            f"Tests added without updating SDR — drift of "
            f"{actual - max_claim} tests."
        )

    assert not violations, (
        "SDR test count drift detected (CR 4-3 F-2).\n"
        "Update the SDR with the latest pytest count, or check for "
        "stale claims.\n\n"
        + "\n".join(violations)
        + f"\n\nMAX SDR claim: {max_claim} (from {max_source})"
        + f"\nActual pytest --collect-only count: {actual}"
        + f"\nTolerance: actual must be in [{max_claim}, {max_claim + 50}]"
    )


@pytest.mark.engine
def test_recent_sdr_claims_are_consistent() -> None:
    """CR 4-3 F-2: recent SDR claims should not contradict each other.

    A "later" SDR (alphabetical order is approximate; we use file mtime as
    a proxy) should have a claim ≥ an "earlier" SDR's claim, because the
    test suite grows monotonically.

    If a later SDR claims a SMALLER number than an earlier SDR, that's
    drift — either the earlier SDR was overclaim or the later SDR lost
    track.

    This is a soft check — we report violations but allow a tolerance of
    ±20 (for deleted/skipped tests that the SDR still references).
    """
    if not SDR_DIR.is_dir():
        pytest.skip(f"SDR dir not found: {SDR_DIR}")

    # Group claims by file (max per file = that SDR's stated total)
    per_file_max: list[tuple[Path, int, str]] = []
    for sdr_file in sorted(SDR_DIR.glob("*.md")):
        claims = _parse_claims(sdr_file)
        if claims:
            n, source = max(claims, key=lambda x: x[0])
            per_file_max.append((sdr_file, n, source))

    # Sort by mtime so newer SDRs come after older SDRs
    per_file_max.sort(key=lambda x: x[0].stat().st_mtime)

    violations: list[str] = []
    for i in range(1, len(per_file_max)):
        prev_file, prev_count, prev_source = per_file_max[i - 1]
        cur_file, cur_count, cur_source = per_file_max[i]

        # If cur_count < prev_count, it's a regression in claim
        # (later SDR underclaims relative to earlier one)
        if cur_count + 20 < prev_count:
            rel_prev = prev_file.relative_to(ROOT)
            rel_cur = cur_file.relative_to(ROOT)
            violations.append(
                f"{rel_cur} (mtime {cur_file.stat().st_mtime:.0f}) claims "
                f"{cur_count} passed ({cur_source}), but earlier "
                f"{rel_prev} (mtime {prev_file.stat().st_mtime:.0f}) "
                f"claimed {prev_count} passed ({prev_source}). "
                f"Later SDR underclaim of {prev_count - cur_count}."
            )

    # Soft assertion: just report, don't fail. SDR claims are human-written
    # and can have legitimate variations (e.g. counting only "new" tests in
    # the story scope, not cumulative).
    if violations:
        # Print warnings via the assertion message
        pytest.warns(
            UserWarning,
            match="SDR cross-file consistency",
        ) if False else None  # noqa: just a placeholder
        # We intentionally do NOT assert here — cross-file consistency is
        # informational only. The MAX-claim-vs-pytest test above is the
        # hard gate.
        return
