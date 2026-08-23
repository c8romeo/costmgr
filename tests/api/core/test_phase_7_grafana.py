"""tests/api/core/test_phase_7_grafana.py — Phase 7 Grafana dashboards documentation tests.

Phase 7 (cj-style 91번째 wire) — T7a backend pytest tests.
PRD §F23.2 + AC #2 + AD-34 (b) verbatim.

Drift detector enforces:
1. docs/grafana-dashboards.md exists.
2. Document specifies 4 NEW dashboards (signups / cost-engine-performance
   / auth-flow / audit-log-purge).
3. Document includes label cardinality invariant note.
"""
from __future__ import annotations

from pathlib import Path


def test_grafana_dashboards_doc_exists() -> None:
    """docs/grafana-dashboards.md exists (Phase 7 deliverable)."""
    doc = Path("docs/grafana-dashboards.md")
    assert doc.exists()


def test_grafana_dashboards_doc_has_4_dashboards() -> None:
    """docs/grafana-dashboards.md mentions 4 NEW dashboards."""
    doc = Path("docs/grafana-dashboards.md")
    content = doc.read_text(encoding="utf-8")
    assert "business-signups" in content
    assert "cost-engine-performance" in content
    assert "auth-flow" in content
    assert "audit-log-purge" in content


def test_grafana_dashboards_doc_has_label_cardinality_invariant() -> None:
    """docs/grafana-dashboards.md has the label cardinality invariant note."""
    doc = Path("docs/grafana-dashboards.md")
    content = doc.read_text(encoding="utf-8")
    assert "cardinality" in content.lower()
    # Free-form tenant_id labels are FORBIDDEN.
    assert "tenant_id" in content
    assert "FORBIDDEN" in content or "forbidden" in content.lower()
