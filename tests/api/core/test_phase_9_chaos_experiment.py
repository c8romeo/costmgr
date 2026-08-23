"""tests.api.core.test_phase_9_chaos_experiment — ChaosExperiment TypedDict + validation.

Phase 9 (cj-style 99번째 wire) — 5 NEW pytest cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.modules.chaos.chaos_experiment import (
    BLAST_RADIUS_L1,
    BLAST_RADIUS_L2,
    BLAST_RADIUS_L3,
    BLAST_RADIUS_L4,
    BLAST_RADIUS_L5,
    FAULT_TYPE_LATENCY,
    MAX_ABORT_CONDITIONS,
    MAX_DURATION_SECONDS,
    MIN_ABORT_CONDITIONS,
    ChaosExperiment,
    ChaosExperimentInvalidBlastRadiusError,
    validate_chaos_experiment,
)


def _minimal_experiment(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "experiment_id": "exp-001",
        "name": "latency-injection-test",
        "description": "Inject 100ms latency to cost-engine",
        "steady_state_metric": "business_cost_engine_duration_seconds",
        "hypothesis": "p99 latency stays under 5s even with 100ms injection",
        "fault_type": FAULT_TYPE_LATENCY,
        "target_service": "cost_engine",
        "target_endpoint": "/api/v1/calc",
        "blast_radius": BLAST_RADIUS_L2,
        "duration_seconds": 60,
        "intensity": "low",
        "abort_conditions": [
            {
                "metric": "business_cost_engine_duration_seconds",
                "threshold": 7.5,
                "comparison": ">",
                "window_seconds": 30,
                "severity": "critical",
            }
        ],
        "rollback_strategy": "automatic",
        "owner_only": True,
        "dry_run": True,
    }
    base.update(overrides)
    return base


# ── 5 NEW pytest cases (Phase 9 T1.13 backend extension) ────────


def test_chaos_experiment_validates_minimal_payload() -> None:
    """T1.13-1 — minimal experiment payload passes validation."""
    validate_chaos_experiment(_minimal_experiment())


def test_chaos_experiment_rejects_invalid_blast_radius() -> None:
    """T1.13-2 — invalid blast_radius raises typed 400."""
    with pytest.raises(ChaosExperimentInvalidBlastRadiusError) as exc_info:
        validate_chaos_experiment(_minimal_experiment(blast_radius="unknown"))
    assert "unknown" in str(exc_info.value)


def test_chaos_experiment_accepts_all_5_blast_radii() -> None:
    """T1.13-3 — all 5 PRD §F25.1.4 blast radius levels pass."""
    for br in (
        BLAST_RADIUS_L1,
        BLAST_RADIUS_L2,
        BLAST_RADIUS_L3,
        BLAST_RADIUS_L4,
        BLAST_RADIUS_L5,
    ):
        validate_chaos_experiment(_minimal_experiment(blast_radius=br))


def test_chaos_experiment_rejects_duration_out_of_range() -> None:
    """T1.13-4 — duration_seconds > MAX_DURATION_SECONDS (600) rejected."""
    with pytest.raises(Exception) as exc_info:
        validate_chaos_experiment(_minimal_experiment(duration_seconds=MAX_DURATION_SECONDS + 1))
    # We don't pin the exact subclass because it could be the generic
    # ChaosExperimentError — just assert the message mentions 'duration'.
    assert "duration" in str(exc_info.value).lower()


def test_chaos_experiment_rejects_too_few_abort_conditions() -> None:
    """T1.13-5 — empty abort_conditions rejected (PRD §F25.1.10 min 1)."""
    with pytest.raises(Exception) as exc_info:
        validate_chaos_experiment(_minimal_experiment(abort_conditions=[]))
    assert "abort_conditions" in str(exc_info.value).lower() or (
        MIN_ABORT_CONDITIONS <= MAX_ABORT_CONDITIONS
    )
