"""tests.api.core.test_phase_5_alembic_0039_multi_region_backup — alembic 0039 shape.

Phase 5 (cj-style 75번째 wire) — AC #1.7 + #3.4 verbatim.
Verifies the alembic 0039_phase_5_multi_region_backup migration creates
both tables + CHECK constraints + indexes verbatim from PRD §F20.1 + §F20.3.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
ALEMBIC_0039 = REPO_ROOT / "apps" / "api" / "alembic" / "versions" / "0039_phase_5_multi_region_backup.py"


@pytest.fixture(scope="module")
def migration_text() -> str:
    assert ALEMBIC_0039.exists(), f"{ALEMBIC_0039} missing"
    return ALEMBIC_0039.read_text(encoding="utf-8")


class TestMigrationShape:
    def test_revision_id(self, migration_text: str) -> None:
        assert 'revision: str = "0039_phase_5_multi_region_backup"' in migration_text

    def test_down_revision(self, migration_text: str) -> None:
        assert 'down_revision: str | None = "0038_epic_16_tenant_idps"' in migration_text


class TestReplicationLagColumns:
    def test_region_column(self, migration_text: str) -> None:
        assert '"region"' in migration_text

    def test_replication_status_column(self, migration_text: str) -> None:
        assert '"replication_status"' in migration_text

    def test_lag_seconds_column(self, migration_text: str) -> None:
        assert '"lag_seconds"' in migration_text

    def test_last_wal_received_at_column(self, migration_text: str) -> None:
        assert '"last_wal_received_at"' in migration_text

    def test_last_health_probe_at_column(self, migration_text: str) -> None:
        assert '"last_health_probe_at"' in migration_text

    def test_recorded_at_column(self, migration_text: str) -> None:
        assert '"recorded_at"' in migration_text


class TestDrDrillResultsColumns:
    def test_drill_quarter_column(self, migration_text: str) -> None:
        assert '"drill_quarter"' in migration_text

    def test_drill_status_column(self, migration_text: str) -> None:
        assert '"drill_status"' in migration_text

    def test_rpo_seconds_column(self, migration_text: str) -> None:
        assert '"rpo_seconds"' in migration_text

    def test_rto_seconds_column(self, migration_text: str) -> None:
        assert '"rto_seconds"' in migration_text


class TestConstraints:
    def test_replication_lag_region_check(self, migration_text: str) -> None:
        assert "ck_phase_5_replication_lag_region" in migration_text

    def test_replication_lag_status_check(self, migration_text: str) -> None:
        assert "ck_phase_5_replication_lag_status" in migration_text

    def test_dr_drill_quarter_check(self, migration_text: str) -> None:
        assert "ck_phase_5_dr_drill_quarter" in migration_text

    def test_dr_drill_status_check(self, migration_text: str) -> None:
        assert "ck_phase_5_dr_drill_status" in migration_text


class TestIndexes:
    def test_replication_lag_region_recorded_index(self, migration_text: str) -> None:
        assert "idx_phase_5_replication_lag_region_recorded" in migration_text

    def test_replication_lag_status_recorded_index(self, migration_text: str) -> None:
        assert "idx_phase_5_replication_lag_status_recorded" in migration_text

    def test_dr_drill_quarter_created_index(self, migration_text: str) -> None:
        assert "idx_phase_5_dr_drill_results_quarter_created" in migration_text


class TestRLS:
    """CR 0-2 RLS lesson: system-only tables have NO RLS."""

    def test_replication_lag_no_rls(self, migration_text: str) -> None:
        # Migration should NOT have ALTER TABLE ... ENABLE ROW LEVEL SECURITY
        # for phase_5_replication_lag.
        replication_lag_block = migration_text.split("phase_5_replication_lag", 1)[1]
        # Look for RLS enable in next ~500 chars after first occurrence.
        assert "ENABLE ROW LEVEL SECURITY" not in replication_lag_block[:2000]

    def test_dr_drill_results_no_rls(self, migration_text: str) -> None:
        # Migration should NOT have ALTER TABLE ... ENABLE ROW LEVEL SECURITY
        # for phase_5_dr_drill_results.
        assert migration_text.count("ENABLE ROW LEVEL SECURITY") == 0


class TestNoDataMigration:
    """PRD §F20.1+§F20.3 verbatim: no seed data — drill + replication_lag
    are populated dynamically by jobs/failover_orchestrator + dr_drill.
    """

    def test_no_seed_insert(self, migration_text: str) -> None:
        # Migration should NOT contain INSERT INTO phase_5_replication_lag
        # or INSERT INTO phase_5_dr_drill_results.
        assert "INSERT INTO public.phase_5_replication_lag" not in migration_text
        assert "INSERT INTO public.phase_5_dr_drill_results" not in migration_text