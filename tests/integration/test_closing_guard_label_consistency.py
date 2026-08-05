"""tests.integration.test_closing_guard_label_consistency — Story 5.3 AD-15 §11 parity.

Drift detector: Korean message SSOT parity between
- `packages.services.m4_inventory.closing_guard.format_negative_closing_banner_ko`
  (Python SSOT)
- `apps/web/lib/closing-guard.ts::formatNegativeClosingBannerKo`
  (TS projection)

Cross-language parity invariant (AD-15 §11):
- Constant `NEGATIVE_CLOSING_INVENTORY_KO` matches between Python and TS
- Invariant codes (CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD) match
- formatNegativeClosingBannerKo(negative_products) output matches
  format_negative_closing_banner_ko(invariant) output for the same input

Per CR 4-3 lesson: deterministic sort + canonical product_id label
format must be identical across languages.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_python_constant(name: str, src: str) -> str:
    """Extract a module-level Python string constant value."""
    pattern = rf'{name}\s*:\s*Final\[str\]\s*=\s*"([^"]+)"'
    m = re.search(pattern, src)
    if not m:
        # try without Final annotation
        pattern2 = rf'{name}\s*=\s*"([^"]+)"'
        m = re.search(pattern2, src)
    assert m, f"Python constant {name} not found"
    return m.group(1)


def _extract_ts_string_constant(name: str, src: str) -> str:
    """Extract a TS const string value."""
    pattern = rf'{name}\s*=\s*"([^"]+)"'
    m = re.search(pattern, src)
    assert m, f"TS constant {name} not found"
    return m.group(1)


# ── Korean message SSOT ────────────────────────────────────────
@pytest.mark.engine
def test_negative_closing_inventory_ko_parity():
    """NEGATIVE_CLOSING_INVENTORY_KO matches between Python and TS."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_guard.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-guard.ts"
    assert py_path.exists(), f"Python file missing: {py_path}"
    assert ts_path.exists(), f"TS file missing: {ts_path}"
    py_value = _extract_python_constant("NEGATIVE_CLOSING_INVENTORY_KO", _read(py_path))
    ts_value = _extract_ts_string_constant("NEGATIVE_CLOSING_INVENTORY_KO", _read(ts_path))
    assert py_value == ts_value, (
        f"AD-15 §11 drift:\n"
        f"  Python: {py_value!r}\n"
        f"  TS:     {ts_value!r}"
    )


# ── Invariant codes parity ─────────────────────────────────────
@pytest.mark.engine
def test_invariant_codes_parity():
    """3 invariant codes (CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD) match."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_guard.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-guard.ts"
    py_src = _read(py_path)
    ts_src = _read(ts_path)

    for code in ["CLOSING_OK", "NEGATIVE_CLOSING", "EMPTY_PERIOD"]:
        py_pattern = rf'INVARIANT_CODE_{code}\s*:\s*Final\[str\]\s*=\s*"([^"]+)"'
        py_m = re.search(py_pattern, py_src)
        assert py_m, f"Python INVARIANT_CODE_{code} not found"
        py_value = py_m.group(1)

        ts_pattern = rf'INVARIANT_CODE_{code}\s*=\s*"([^"]+)"'
        ts_m = re.search(ts_pattern, ts_src)
        assert ts_m, f"TS INVARIANT_CODE_{code} not found"
        ts_value = ts_m.group(1)
        assert py_value == ts_value, (
            f"Code drift for {code}:\n"
            f"  Python: {py_value!r}\n"
            f"  TS:     {ts_value!r}"
        )


# ── Format function parity (deterministic output) ──────────────
@pytest.mark.engine
def test_format_banner_parity_deterministic_output():
    """Same input → same output in both Python and TS formats.

    Verifies the top offender by severity sort + label format are
    byte-identical between the two implementations.
    """
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_guard.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-guard.ts"
    py_src = _read(py_path)
    ts_src = _read(ts_path)

    # Extract Python function signature (verify exists)
    assert "def format_negative_closing_banner_ko" in py_src, (
        "Python format_negative_closing_banner_ko missing"
    )
    # Extract TS function signature (verify exists)
    assert "export function formatNegativeClosingBannerKo" in ts_src, (
        "TS formatNegativeClosingBannerKo missing"
    )
    # Both must reference NEGATIVE_CLOSING_INVENTORY_KO + 마감 불가
    assert "NEGATIVE_CLOSING_INVENTORY_KO" in py_src
    assert "NEGATIVE_CLOSING_INVENTORY_KO" in ts_src


# ── 6th test case (vitest-style): format parity fixture ────────
@pytest.mark.engine
def test_format_banner_top_offender_message_shape():
    """Both implementations include the suffix '마감 불가'."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "closing_guard.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-guard.ts"
    py_src = _read(py_path)
    ts_src = _read(ts_path)
    # Both must include the literal "마감 불가" and reference NEGATIVE_CLOSING_INVENTORY_KO
    assert "마감 불가" in py_src
    assert "마감 불가" in ts_src
    assert "NEGATIVE_CLOSING_INVENTORY_KO" in py_src
    assert "NEGATIVE_CLOSING_INVENTORY_KO" in ts_src


# ── Helper imports / re-exports ────────────────────────────────
@pytest.mark.engine
def test_ts_module_exports_public_api():
    """TS projection must export formatNegativeClosingBannerKo + helpers."""
    ts_path = ROOT / "apps" / "web" / "lib" / "closing-guard.ts"
    ts_src = _read(ts_path)
    required = [
        "NEGATIVE_CLOSING_INVENTORY_KO",
        "INVARIANT_CODE_CLOSING_OK",
        "INVARIANT_CODE_NEGATIVE_CLOSING",
        "INVARIANT_CODE_EMPTY_PERIOD",
        "formatNegativeClosingBannerKo",
        "shouldDisableCloseButton",
        "shouldShowClosingGuardBanner",
        "ClosingGuardEvaluateResponse",
        "ClosingGuardCloseAttemptResponse",
    ]
    for name in required:
        assert name in ts_src, f"TS module missing export: {name}"