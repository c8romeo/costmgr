"""tests.api.core.test_phase_9_continuous_chaos — continuous chaos job smoke test.

Phase 9 (cj-style 99번째 wire) — 4 NEW pytest cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.jobs.continuous_chaos import (
    MAX_AUTO_ROLLBACK_SECONDS,
    MAX_DURATION_SECONDS,
    MAX_TRAFFIC_PERCENT,
    PRODUCTION_SAFE_EXPERIMENTS,
)
from apps.api.modules.chaos.chaos_experiment import (
    BLAST_RADIUS_L1,
    ContinuousChaosProductionUnsafeError,
)


# ── 4 NEW pytest cases (Phase 9 T3.8) ─────────────────────────


def test_continuous_chaos_production_safe_constants() -> None:
    """T3.8-1 — production-safe guard constants (PRD §F25.4.4 verbatim)."""
    assert MAX_TRAFFIC_PERCENT == 5.0
    assert MAX_DURATION_SECONDS == 60
    assert MAX_AUTO_ROLLBACK_SECONDS == 30


def test_production_safe_experiment_candidates_count() -> None:
    """T3.8-2 — 4 production-safe experiment candidates (PRD §F25.4.2 verbatim)."""
    assert len(PRODUCTION_SAFE_EXPERIMENTS) == 4
    assert "cost-engine-latency-injection-100ms" in PRODUCTION_SAFE_EXPERIMENTS
    assert "auth-error-injection-1pct" in PRODUCTION_SAFE_EXPERIMENTS
    assert "audit-log-query-latency-injection-50ms" in PRODUCTION_SAFE_EXPERIMENTS
    assert "multi-region-replication-lag-injection" in PRODUCTION_SAFE_EXPERIMENTS


def test_continuous_chaos_guard_rejects_high_percentage() -> None:
    """T3.8-3 — percentage > MAX_TRAFFIC_PERCENT raises 422."""
    from apps.api.jobs.continuous_chaos import _validate_production_safe_guard

    with pytest.raises(ContinuousChaosProductionUnsafeError):
        _validate_production_safe_guard(
            blast_radius=BLAST_RADIUS_L1,
            intensity="low",
            percentage=10.0,  # > 5%
            duration_seconds=30,
            auto_rollback_seconds=10,
        )


def test_continuous_chaos_guard_rejects_long_duration() -> None:
    """T3.8-4 — duration > 60s raises 422."""
    from apps.api.jobs.continuous_chaos import _validate_production_safe_guard

    with pytest.raises(ContinuousChaosProductionUnsafeError):
        _validate_production_safe_guard(
            blast_radius=BLAST_RADIUS_L1,
            intensity="low",
            percentage=5.0,
            duration_seconds=120,  # > 60s
            auto_rollback_seconds=10,
        )
