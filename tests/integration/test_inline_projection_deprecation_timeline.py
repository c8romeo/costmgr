"""tests.integration.test_inline_projection_deprecation_timeline — Story 6.3 T5.2.

Validates the A8 inline projection deprecation timeline invariants
documented in docs/closing-period.md §8:

1. 5-2 wire: inline projection 보존 (Layer 1 input warning 보존).
2. 5-3 wire: inline projection 보존 (production_consumption 보존).
3. 6-1 wire: inline projection 보존 (closing_period snapshot = ledger aggregate).
4. 6-2 wire: inline projection 보존 (read-only monthly closing report).
5. 6-3 wire: inline projection 보존 (PDF export + ko-KR labels only).

The Epic 6 close-out 시점에 fold-in vs deprecate 결정 보류 — Epic 11
reversal 진입 시 inline projection 완전 제거 (A8 timeline).

These tests are guard tests — they verify the deprecation invariant
HOLDS through 6-3 wire, and FAIL if any wire inadvertently removes
the inline projection path before Epic 6 close-out + Epic 11 reversal.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── Scenario 1: 5-2 ledger_service 보존 ───────────────────────
@pytest.mark.engine
def test_5_2_inline_projection_wire_preserved():
    """5-2 wire — ledger_service inline projection swap (AC #5) 보존."""
    src = _read(ROOT / "apps/api/modules/m4_inventory/services/ledger_service.py")
    # Epic 3.3 inline projection swap reference 보존
    assert "inline projection" in src or "inline_projection" in src, (
        "5-2 ledger_service inline projection path MUST be preserved until "
        "Epic 6 close-out + Epic 11 reversal (A8 timeline)"
    )


# ── Scenario 2: 5-3 production_consumption 보존 ────────────────
@pytest.mark.engine
def test_5_3_inline_projection_wire_preserved():
    """5-3 wire — production_consumption + inline projection 동시 활용 보존.

    The inline projection path lives in `ledger_service.py` (5-2 wire
    Epic 3.3 swap). 5-3 closing_period_service wraps it via
    `LedgerService.query_period_closing_all` (5-2 SSOT).
    """
    # closing_period_service.py must reference LedgerService (5-2 SSOT entrypoint)
    closing_period_src = _read(ROOT / "apps/api/modules/m4_inventory/services/closing_period_service.py")
    assert "LedgerService" in closing_period_src, (
        "5-3 closing_period_service MUST reference LedgerService (5-2 SSOT) — "
        "inline projection path 보존 invariant"
    )
    # monthly_closing_report_service must also reference LedgerService
    report_src = _read(ROOT / "apps/api/modules/m4_inventory/services/monthly_closing_report_service.py")
    assert "LedgerService" in report_src or "ledger_aggregate" in report_src, (
        "5-3 monthly_closing_report_service MUST use ledger aggregate (5-2 SSOT) — "
        "inline projection path 보존 invariant"
    )


# ── Scenario 3: 6-1 wire timeline 문서화 ──────────────────────
@pytest.mark.engine
def test_6_1_inline_projection_timeline_documented():
    """6-1 wire 시점 — A8 timeline §8 6-1 wire marker 보존."""
    src = _read(ROOT / "docs/closing-period.md")
    # §8 section must exist and reference 6-1 wire
    assert "## 8. A8 Inline Projection Deprecation Timeline" in src
    assert "6-1 wire 시점" in src, "6-1 wire marker MUST be in §8 timeline"


# ── Scenario 4: 6-2 wire timeline 문서화 ──────────────────────
@pytest.mark.engine
def test_6_2_inline_projection_timeline_documented():
    """6-2 wire 시점 — A8 timeline §8 6-2 wire marker 보존."""
    src = _read(ROOT / "docs/closing-period.md")
    # §8 section must reference 6-2 wire
    assert "6-2 wire" in src, "6-2 wire marker MUST be in §8 timeline"


# ── Scenario 5: 6-3 wire timeline + test guard ───────────────
@pytest.mark.engine
def test_6_3_inline_projection_timeline_guard_test():
    """6-3 wire 시점 — A8 timeline §8 6-3 marker + this test file 보존."""
    src = _read(ROOT / "docs/closing-period.md")
    # §8 section must reference 6-3 wire + this test file
    assert "6-3 wire" in src, "6-3 wire marker MUST be in §8 timeline"
    assert "test_inline_projection_deprecation_timeline" in src, (
        "this test file MUST be referenced as T5.2 guard test"
    )


# ── Scenario 6: NO 6-3 wire removes inline projection ─────────
@pytest.mark.engine
def test_no_6_3_wire_removes_inline_projection():
    """6-3 wire (PDF export + ko-KR labels) MUST NOT remove inline projection path.

    Invariant: ledger_service.py MUST still contain "inline projection swap"
    marker (Epic 3.3). This is the single source of truth for the inline
    projection path. closing_period_service delegates to LedgerService via
    5-2 SSOT entrypoint (query_period_closing_all).
    """
    ledger_src = _read(ROOT / "apps/api/modules/m4_inventory/services/ledger_service.py")
    assert "inline projection" in ledger_src, (
        "ledger_service inline projection swap MUST be preserved "
        "(Epic 3.3 AC #5 — A8 timeline invariant)"
    )
    # closing_period_service delegates to LedgerService
    closing_src = _read(ROOT / "apps/api/modules/m4_inventory/services/closing_period_service.py")
    assert "LedgerService" in closing_src, (
        "closing_period_service MUST delegate to LedgerService (5-2 SSOT)"
    )


# ── Scenario 7: A8 timeline section structure ──────────────────
@pytest.mark.engine
def test_a8_timeline_section_structure():
    """§8 section MUST contain Epic 5 retro + Epic 6 close-out + Epic 11 references."""
    src = _read(ROOT / "docs/closing-period.md")
    # Find §8 section
    match = re.search(
        r"## 8\. A8 Inline Projection Deprecation Timeline.*?(?=^## 9\.)",
        src,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "§8 A8 Inline Projection section MUST exist"
    section = match.group(0)
    # Must mention Epic 5 retro origin + Epic 6 close-out 결정 + Epic 11 reversal
    assert "Epic 5 retro" in section or "Epic 5 §7" in section, (
        "§8 MUST reference Epic 5 retro origin (A8)"
    )
    assert "Epic 6 close-out" in section, "§8 MUST reference Epic 6 close-out 결정 시점"
    assert "Epic 11" in section, "§8 MUST reference Epic 11 reversal 완전 제거"
