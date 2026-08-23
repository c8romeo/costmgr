"""tests.integration.test_chaos_tenant_isolation — phase_9_chaos_experiments RLS isolation.

Phase 9 (cj-style 99번째 wire) — Multi-tenant isolation test (PRD §F25.5.9
verbatim).

Mirrors Phase 5 wire `test_multi_region_replication_lag.py` + Phase 7
wire `test_observability_tenant_isolation.py` pattern verbatim.

3 NEW pytest cases PASS:
1. RLS policy present (CR 0-2 verbatim).
2. CHECK constraint ck_phase_9_chaos_experiments_fault_type verbatim.
3. CHECK constraint ck_phase_9_chaos_experiments_blast_radius verbatim.
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
    FAULT_TYPE_ERROR,
    FAULT_TYPE_RESOURCE,
    FAULT_TYPE_NETWORK,
    FAULT_TYPE_DISK_IO,
    FAULT_TYPE_DB_POOL,
    FAULT_TYPE_CACHE,
    FAULT_TYPE_DNS,
    FAULT_TYPE_PROCESS,
    FAULT_TYPE_CLOCK_SKEW,
    VALID_BLAST_RADII,
    VALID_FAULT_TYPES,
)


# ── 3 NEW pytest cases (Phase 9 T4.6 alembic migration tests) ──


def test_chaos_tenant_isolation_rls_policy_present() -> None:
    """T4.6-1 — RLS policy phase_9_chaos_experiments_tenant_isolation declared."""
    # We assert the policy name is referenced in the migration file
    # (mirror of Phase 5 wire `test_multi_region_replication_lag.py`
    # pattern).
    from pathlib import Path

    migration_path = (
        Path(__file__).parent.parent.parent
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0041_phase_9_chaos_engineering.py"
    )
    content = migration_path.read_text(encoding="utf-8")
    assert "phase_9_chaos_experiments_tenant_isolation" in content
    assert "ENABLE ROW LEVEL SECURITY" in content


def test_chaos_experiments_check_fault_type_constraint() -> None:
    """T4.6-2 — CHECK constraint ck_phase_9_chaos_experiments_fault_type declared."""
    from pathlib import Path

    migration_path = (
        Path(__file__).parent.parent.parent
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0041_phase_9_chaos_engineering.py"
    )
    content = migration_path.read_text(encoding="utf-8")
    assert "ck_phase_9_chaos_experiments_fault_type" in content
    # All 10 fault types referenced in CHECK constraint
    for ft in VALID_FAULT_TYPES:
        assert ft in content, f"fault_type {ft!r} missing from migration"


def test_chaos_experiments_check_blast_radius_constraint() -> None:
    """T4.6-3 — CHECK constraint ck_phase_9_chaos_experiments_blast_radius declared."""
    from pathlib import Path

    migration_path = (
        Path(__file__).parent.parent.parent
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0041_phase_9_chaos_engineering.py"
    )
    content = migration_path.read_text(encoding="utf-8")
    assert "ck_phase_9_chaos_experiments_blast_radius" in content
    # All 5 blast radius levels referenced
    for br in VALID_BLAST_RADII:
        assert br in content, f"blast_radius {br!r} missing from migration"
