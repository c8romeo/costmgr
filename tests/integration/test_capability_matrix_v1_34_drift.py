"""tests.integration.test_capability_matrix_v1_34_drift — Capability matrix v1.34 drift detector.

4 NEW pytest cases PASS (Phase 9 cj-style 99번째 wire backend tests).
Mirrors Phase 5 v1.29 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 +
Phase 8 v1.33 drift detector pattern verbatim.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from apps.api.core.capability import (
    Capability,
    _INDUSTRY_CAPABILITIES,
)
from packages.services.m0_onboarding.industry_menu import Industry


CAPABILITY_MATRIX_DOC_PATH = Path(
    __file__).parent.parent.parent / "docs" / "capability-matrix.md"


# ── 4 NEW pytest cases (Phase 9 T6.4) ──────────────────────────


def test_capability_matrix_at_v1_34() -> None:
    """T6.4-1 — capability-matrix.md is at v1.34 (Phase 9 EXTENSION)."""
    content = CAPABILITY_MATRIX_DOC_PATH.read_text(encoding="utf-8")
    assert "v1.34" in content, "capability matrix must be at v1.34"


def test_chaos_engineering_capability_in_all_4_industries() -> None:
    """T6.4-2 — CHAOS_ENGINEERING granted to all 4 industries (CR 12-1 L4)."""
    assert hasattr(Capability, "CHAOS_ENGINEERING")
    for industry in Industry:
        caps = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
        assert Capability.CHAOS_ENGINEERING in caps, (
            f"{industry.value} missing CHAOS_ENGINEERING"
        )


def test_capability_matrix_preserves_v1_29_to_v1_33() -> None:
    """T6.4-3 — v1.29 (Phase 5) + v1.30 (Epic 17) + v1.31 (Phase 6) +
    v1.32 (Phase 7) + v1.33 (Phase 8) all preserved in the matrix
    changelog.
    """
    content = CAPABILITY_MATRIX_DOC_PATH.read_text(encoding="utf-8")
    for v in ("v1.29", "v1.30", "v1.31", "v1.32", "v1.33", "v1.34"):
        assert v in content, f"missing {v} reference in capability matrix changelog"


def test_chaos_engineering_capability_table_row_present() -> None:
    """T6.4-4 — CHAOS_ENGINEERING row present in the Industry × Capability table."""
    content = CAPABILITY_MATRIX_DOC_PATH.read_text(encoding="utf-8")
    assert "CHAOS_ENGINEERING" in content, "CHAOS_ENGINEERING missing from matrix"
    # And it should be listed alongside other Phase N rows
    assert "Phase 9" in content, "Phase 9 reference missing from matrix"
