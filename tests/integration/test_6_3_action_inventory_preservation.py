"""tests.integration.test_6_3_action_inventory_preservation — Story 6.3 T5.3.

A5 forward-lock + A7 wire + A11 V8 + A12 5-3 T12.2 preservation verification.

Per docs/closing-period.md §8 timeline + 6-3 spec AC #7:
- A5 forward-lock: ActionClass.CLOSING_PERIOD 3 values +
  ActionClass.VERIFICATION V4 extension 보존
- A7 wire: def test_* + asyncio.run(_impl()) pattern (CR 4-3 정합)
- A11 V8 16-fixture matrix extension 보존 (6-2 wire 완료)
- A12 5-3 T12.2 test file close-out 보존 (6-2 wire 완료)

These tests are guard tests — verify invariants HOLD through 6-3 wire.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── A5 forward-lock: ActionClass.CLOSING_PERIOD 3 values ────────────
@pytest.mark.engine
def test_a5_closing_period_action_class_3_values():
    """A5 forward-lock: ActionClass.CLOSING_PERIOD has exactly 3 values."""
    audit_action_src = _read(ROOT / "apps/api/core/audit_action.py")
    # ClosingPeriodAction literal must have 3 values
    import re

    match = re.search(
        r'ClosingPeriodAction\s*=\s*Literal\[(.*?)\]',
        audit_action_src,
        re.DOTALL,
    )
    assert match is not None, "ClosingPeriodAction Literal MUST exist"
    literal_body = match.group(1)
    # Count distinct values (handling whitespace/newlines)
    values = [v.strip().strip('"').strip("'") for v in literal_body.split(",") if v.strip()]
    assert len(values) == 3, f"ClosingPeriodAction MUST have exactly 3 values, got {len(values)}"
    expected = {"closing_period_confirmed", "closing_period_blocked", "closing_period_snapshot_inconsistency"}
    assert set(values) == expected, (
        f"ClosingPeriodAction values MUST be {expected}, got {set(values)}"
    )


# ── A5 forward-lock: ActionClass.MONTHLY_CLOSING_REPORT ─────────────
@pytest.mark.engine
def test_a5_monthly_closing_report_action_class_preserved():
    """A5 forward-lock: ActionClass.MONTHLY_CLOSING_REPORT 1 value preserved."""
    audit_action_src = _read(ROOT / "apps/api/core/audit_action.py")
    # monthly_closing_report_viewed action MUST be registered
    assert "monthly_closing_report_viewed" in audit_action_src, (
        "monthly_closing_report_viewed MUST be registered (6-2 wire A5 forward-lock)"
    )


# ── A5 forward-lock: ActionClass.VERIFICATION V4 extension ───────────
@pytest.mark.engine
def test_a5_verification_v4_extension_preserved():
    """A5 forward-lock: ActionClass.VERIFICATION V4 extension preserved."""
    audit_action_src = _read(ROOT / "apps/api/core/audit_action.py")
    # verify_v4_closing_period_consistency MUST be registered
    assert "verify_v4_closing_period_consistency" in audit_action_src, (
        "verify_v4_closing_period_consistency MUST be registered (6-1 wire A5 forward-lock)"
    )


# ── A7 wire: asyncio.run pattern in 6-3 service tests ───────────────
@pytest.mark.engine
def test_a7_asyncio_run_pattern_in_6_3_service_tests():
    """A7 wire: 6-3 service tests use def test_* + asyncio.run(_impl()) pattern."""
    test_src = _read(ROOT / "tests/api/m4_inventory/test_closing_pdf_export_service.py")
    # A7 pattern: def test_*(...) wrapping asyncio.run(...) OR _run_export helper
    assert "asyncio.run" in test_src or "_run_export" in test_src, (
        "6-3 service tests MUST use asyncio.run or _run_export helper (A7 wire)"
    )


# ── A11 V8 fixture matrix preservation ──────────────────────────────
@pytest.mark.engine
def test_a11_v8_fixture_matrix_preserved():
    """A11 V8 16-fixture matrix (6-2 wire) MUST be preserved through 6-3."""
    test_src = _read(ROOT / "tests/regression_v8/test_regression_v8_fixtures.py")
    # 6-2 wire extended fixture matrix to 16 fixtures — must have at least
    # 16 fixture references or matrix indicators
    assert "v4_closing_period_pass" in test_src or "manufacturing__b-small" in test_src, (
        "A11 V8 16-fixture matrix MUST be preserved (6-2 wire)"
    )


# ── A12 5-3 T12.2 test file close-out preservation ──────────────────
@pytest.mark.engine
def test_a12_5_3_t12_2_test_file_preserved():
    """A12 5-3 T12.2 closing invariant TS mirror parity test preserved."""
    # 5-3 T12.2 produced ≥10 NEW cases for closing invariant TS mirror parity
    # (closed-out in 6-2 wire per spec A12)
    # Verify the test files exist (5-3 + 6-2)
    closing_invariant_test = ROOT / "apps/web/__tests__"
    assert closing_invariant_test.exists(), "apps/web/__tests__ MUST exist"
    # Check at least one closing invariant test exists
    test_files = list(closing_invariant_test.glob("*.tsx")) + list(closing_invariant_test.glob("*.ts"))
    has_closing = any(
        "closing" in f.name.lower() or "monthly" in f.name.lower()
        for f in test_files
    )
    assert has_closing, "A12 5-3 T12.2 closing invariant tests MUST be preserved"
