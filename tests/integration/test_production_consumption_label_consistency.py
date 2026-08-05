"""tests.integration.test_production_consumption_label_consistency — Story 5.3 AD-15 §11 parity.

Drift detector: Korean message SSOT parity for production_consumption labels.
- EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND (Python) ↔ TS enum string
- EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION (Python) ↔ TS enum string
- EVENT_TYPE_ADJUSTMENT_POSITIVE (Python) ↔ TS enum string
- INCOMPLETE_BOM_FALLBACK_REASON_KO matches between Python and TS projection

AD-15 §11 cross-language parity invariant.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_py_const(name: str, src: str) -> str:
    """Extract a Python string constant."""
    pattern = rf'{name}\s*:\s*Final\[str\]\s*=\s*"([^"]+)"'
    m = re.search(pattern, src)
    if not m:
        pattern2 = rf'{name}\s*=\s*"([^"]+)"'
        m = re.search(pattern2, src)
    assert m, f"Python constant {name} not found"
    return m.group(1)


def _extract_ts_const(name: str, src: str) -> str:
    """Extract a TS const string value."""
    pattern = rf'{name}\s*=\s*"([^"]+)"'
    m = re.search(pattern, src)
    assert m, f"TS constant {name} not found"
    return m.group(1)


# ── Event type parity ──────────────────────────────────────────
@pytest.mark.engine
def test_event_type_production_output_inbound_parity():
    """EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND matches between Python and TS."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "production_consumption.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "production-consumption.ts"
    assert py_path.exists()
    if not ts_path.exists():
        pytest.skip("TS production-consumption.ts not yet created")
    py_value = _extract_py_const(
        "EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND", _read(py_path)
    )
    ts_value = _extract_ts_const(
        "EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND", _read(ts_path)
    )
    assert py_value == ts_value, (
        f"AD-15 §11 drift:\n  Python: {py_value!r}\n  TS:     {ts_value!r}"
    )


@pytest.mark.engine
def test_event_type_production_material_consumption_parity():
    """EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION matches between Python and TS."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "production_consumption.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "production-consumption.ts"
    assert py_path.exists()
    if not ts_path.exists():
        pytest.skip("TS production-consumption.ts not yet created")
    py_value = _extract_py_const(
        "EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION", _read(py_path)
    )
    ts_value = _extract_ts_const(
        "EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION", _read(ts_path)
    )
    assert py_value == ts_value


@pytest.mark.engine
def test_event_type_adjustment_positive_parity():
    """EVENT_TYPE_ADJUSTMENT_POSITIVE matches between Python and TS."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "production_consumption.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "production-consumption.ts"
    assert py_path.exists()
    if not ts_path.exists():
        pytest.skip("TS production-consumption.ts not yet created")
    py_value = _extract_py_const(
        "EVENT_TYPE_ADJUSTMENT_POSITIVE", _read(py_path)
    )
    ts_value = _extract_ts_const(
        "EVENT_TYPE_ADJUSTMENT_POSITIVE", _read(ts_path)
    )
    assert py_value == ts_value


# ── Korean fallback reason parity ──────────────────────────────
@pytest.mark.engine
def test_incomplete_bom_fallback_reason_parity():
    """INCOMPLETE_BOM_FALLBACK_REASON_KO matches between Python and TS."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "production_consumption.py"
    ts_path = ROOT / "apps" / "web" / "lib" / "production-consumption.ts"
    assert py_path.exists()
    if not ts_path.exists():
        pytest.skip("TS production-consumption.ts not yet created")
    py_value = _extract_py_const(
        "INCOMPLETE_BOM_FALLBACK_REASON_KO", _read(py_path)
    )
    ts_value = _extract_ts_const(
        "INCOMPLETE_BOM_FALLBACK_REASON_KO", _read(ts_path)
    )
    assert py_value == ts_value, (
        f"AD-15 §11 drift:\n  Python: {py_value!r}\n  TS:     {ts_value!r}"
    )


# ── Module shape parity (Python + TS both exist) ───────────────
def test_python_module_exists():
    """Python production_consumption.py exists."""
    py_path = ROOT / "packages" / "services" / "m4_inventory" / "production_consumption.py"
    assert py_path.exists()
    src = _read(py_path)
    # Must export the 3 event types
    for name in (
        "EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND",
        "EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION",
        "EVENT_TYPE_ADJUSTMENT_POSITIVE",
    ):
        assert name in src, f"Python module missing {name}"