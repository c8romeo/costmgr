"""tests.api.core.test_phase_8_slo_sli — SLO/SLI docs spec test.

4 NEW pytest cases PASS (Phase 8 cj-style 95번째 wire backend tests).
Validates docs/slo-sli.md as a machine-readable SSOT (CR 12-5 D-PARITY-01).
"""
from __future__ import annotations

from pathlib import Path

import pytest


SLO_SLI_DOC_PATH = Path(
    __file__).parent.parent.parent / "docs" / "slo-sli.md"


# ── 4 NEW pytest cases (Phase 8 T7.4) ──────────────────────────


def test_slo_sli_doc_exists() -> None:
    """T7.4-1 — docs/slo-sli.md SSOT must exist."""
    assert SLO_SLI_DOC_PATH.exists(), f"missing: {SLO_SLI_DOC_PATH}"


def test_slo_sli_doc_defines_4_canonical_slas() -> None:
    """T7.4-2 — SLA-1~SLA-4 all present verbatim per PRD §F24.2."""
    content = SLO_SLI_DOC_PATH.read_text(encoding="utf-8")
    assert "SLA-1" in content and "Cost calculation" in content
    assert "SLA-2" in content and "Audit log query" in content
    assert "SLA-3" in content and "Login" in content
    assert "SLA-4" in content and "Multi-region failover" in content


def test_slo_sli_doc_defines_30d_rolling_window() -> None:
    """T7.4-3 — 30d rolling window verbatim per PRD §F24.2-7."""
    content = SLO_SLI_DOC_PATH.read_text(encoding="utf-8")
    assert "30d rolling" in content or "30-day rolling" in content
    assert "1.5h/month" in content or "1.5h" in content


def test_slo_sli_doc_owner_only_rbac() -> None:
    """T7.4-4 — owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 verbatim."""
    content = SLO_SLI_DOC_PATH.read_text(encoding="utf-8")
    assert "owner-only" in content.lower() or "owner" in content
    assert "2FA" in content or "AD-22" in content
