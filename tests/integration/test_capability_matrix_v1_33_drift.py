"""tests.integration.test_capability_matrix_v1_33_drift — Capability matrix v1.33 drift detector.

3 NEW pytest cases PASS (Phase 8 cj-style 95번째 wire backend tests).
Mirrors Phase 5 v1.29 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32
drift detector pattern verbatim.
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


# ── 3 NEW pytest cases (Phase 8 T7.5) ──────────────────────────


def test_capability_matrix_at_v1_33() -> None:
    """T7.5-1 — capability-matrix.md is at v1.33 (Phase 8 EXTENSION)."""
    content = CAPABILITY_MATRIX_DOC_PATH.read_text(encoding="utf-8")
    assert "v1.33" in content, "capability matrix must be at v1.33"


def test_performance_testing_capability_in_all_4_industries() -> None:
    """T7.5-2 — PERFORMANCE_TESTING granted to all 4 industries (CR 12-1 L4)."""
    assert hasattr(Capability, "PERFORMANCE_TESTING")
    for industry in Industry:
        caps = _INDUSTRY_CAPABILITIES.get(industry, frozenset())
        assert Capability.PERFORMANCE_TESTING in caps, (
            f"{industry.value} missing PERFORMANCE_TESTING"
        )


def test_capability_matrix_preserves_v1_29_to_v1_32() -> None:
    """T7.5-3 — v1.29 (Phase 5) + v1.30 (Epic 17) + v1.31 (Phase 6) + v1.32 (Phase 7)
    all preserved in the matrix changelog.
    """
    content = CAPABILITY_MATRIX_DOC_PATH.read_text(encoding="utf-8")
    for v in ("v1.29", "v1.30", "v1.31", "v1.32", "v1.33"):
        assert v in content, f"missing {v} reference in capability matrix changelog"
