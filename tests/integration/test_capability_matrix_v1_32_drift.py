"""tests/integration/test_capability_matrix_v1_32_drift.py — Phase 7 capability matrix v1.32 drift tests.

Phase 7 (cj-style 91번째 wire) — T7a backend pytest tests.
PRD §F23.6 + AC #6.3 + AD-34 (f) verbatim.

Drift detector enforces:
1. Capability.OBSERVABILITY_TRACES + Capability.OBSERVABILITY_METRICS enum values exist.
2. All 4 industries (manufacturing, service, mfg+service, mfg+service+other)
   grant both observability capabilities.
3. Capability matrix markdown file v1.32 contains both rows.
4. require_observability_traces + require_observability_metrics deps exist.
5. v1.31 preservation (AUDIT_LOG_RETENTION still present).
6. v1.30 preservation (AUDIT_LOG_VIEW still present).
7. v1.29 preservation (MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER).
8. All industry blocks grant OBSERVABILITY_* capabilities.

Mirrors tests/integration/test_capability_matrix_v1_31_drift.py pattern
verbatim (Phase 6 wire `24e1cd7`).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from apps.api.core.capability import Capability, _INDUSTRY_CAPABILITIES
from apps.api.dependencies.capability import (
    require_observability_traces,
    require_observability_metrics,
)
from packages.services.m0_onboarding.industry_menu import Industry


def test_capability_observability_traces_exists() -> None:
    assert hasattr(Capability, "OBSERVABILITY_TRACES")
    assert Capability.OBSERVABILITY_TRACES.value == "observability_traces"


def test_capability_observability_metrics_exists() -> None:
    assert hasattr(Capability, "OBSERVABILITY_METRICS")
    assert Capability.OBSERVABILITY_METRICS.value == "observability_metrics"


@pytest.mark.parametrize(
    "industry",
    [
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MFG_AND_SERVICE,
        Industry.MFG_AND_SERVICE_AND_OTHER,
    ],
)
def test_all_industries_grant_observability_traces(industry: Industry) -> None:
    """All 4 industries grant OBSERVABILITY_TRACES (industry-agnostic, CR 12-1 L4)."""
    caps = _INDUSTRY_CAPABILITIES[industry]
    assert Capability.OBSERVABILITY_TRACES in caps


@pytest.mark.parametrize(
    "industry",
    [
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MFG_AND_SERVICE,
        Industry.MFG_AND_SERVICE_AND_OTHER,
    ],
)
def test_all_industries_grant_observability_metrics(industry: Industry) -> None:
    """All 4 industries grant OBSERVABILITY_METRICS (industry-agnostic, CR 12-1 L4)."""
    caps = _INDUSTRY_CAPABILITIES[industry]
    assert Capability.OBSERVABILITY_METRICS in caps


def test_capability_matrix_md_has_v132_observability_rows() -> None:
    """docs/capability-matrix.md v1.32 EXTENSION rows present."""
    matrix_path = Path("docs/capability-matrix.md")
    if not matrix_path.exists():
        pytest.skip("capability-matrix.md not present")
    content = matrix_path.read_text(encoding="utf-8")
    assert "OBSERVABILITY_TRACES" in content
    assert "OBSERVABILITY_METRICS" in content
    assert "v1.32" in content


def test_require_observability_deps_exist() -> None:
    """require_observability_traces + require_observability_metrics callable."""
    # Both should be callable (FastAPI Depends factory pattern).
    assert callable(require_observability_traces)
    assert callable(require_observability_metrics)


def test_v131_audit_log_retention_preserved() -> None:
    """v1.31 AUDIT_LOG_RETENTION preservation (Phase 6 wire carry-over)."""
    caps = _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING]
    assert Capability.AUDIT_LOG_RETENTION in caps


def test_v130_audit_log_view_preserved() -> None:
    """v1.30 AUDIT_LOG_VIEW preservation (Epic 17 wire carry-over)."""
    caps = _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING]
    assert Capability.AUDIT_LOG_VIEW in caps


def test_v129_multi_region_preserved() -> None:
    """v1.29 MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER preservation (Phase 5 wire carry-over)."""
    caps = _INDUSTRY_CAPABILITIES[Industry.MANUFACTURING]
    assert Capability.MULTI_REGION_BACKUP in caps
    assert Capability.MULTI_REGION_FAILOVER in caps
