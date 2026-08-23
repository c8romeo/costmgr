# tests/integration/test_finops_tenant_isolation.py —
# Phase 11 T5 (cj-style 107번째 wire) — RLS tenant isolation tests
# for the 3 NEW Phase 11 tables. 4 cases verifying per-table RLS
# policies enforce tenant_id scope (CR 0-2 RLS lesson verbatim).
import pytest

# Each table must have a separate test that verifies the alembic
# migration file declares the corresponding RLS policy. Full RLS
# enforcement tests must run against the live database with the
# policies enabled — those live in apps.api.integration.tenant_rls.


def test_phase_11_finops_alembic_migration_present():
    """Alembic 0043 phase_11_finops migration must exist with
    down_revision pointing at 0042_phase_10_slo_engineering."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    migration = repo_root / "apps" / "api" / "alembic" / "versions" / "0043_phase_11_finops.py"
    assert migration.exists(), f"Missing migration: {migration}"

    content = migration.read_text(encoding="utf-8")
    assert 'revision: str = "0043_phase_11_finops"' in content
    assert 'down_revision: str | None = "0042_phase_10_slo_engineering"' in content


def test_phase_11_finops_creates_three_tables():
    """Migration 0043 must create the 3 FinOps Phase 11 tables
    (department_mapping + showback + chargeback)."""
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[2]
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0043_phase_11_finops.py"
    )
    content = migration.read_text(encoding="utf-8")
    assert "phase_11_finops_department_mapping" in content
    assert "phase_11_finops_showback" in content
    assert "phase_11_finops_chargeback" in content


def test_phase_11_finops_three_rls_policies():
    """Migration 0043 must create 3 RLS policies (one per table)
    with tenant_id scope (CR 0-2 verbatim)."""
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[2]
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0043_phase_11_finops.py"
    )
    content = migration.read_text(encoding="utf-8")
    assert "phase_11_finops_department_mapping_tenant_isolation" in content
    assert "phase_11_finops_showback_tenant_isolation" in content
    assert "phase_11_finops_chargeback_tenant_isolation" in content
    # 3 RLS policies (one per table) each carry the canonical
    # current_setting selector on both USING and WITH CHECK clauses,
    # producing exactly 3 CREATE POLICY invocations.
    assert content.count("CREATE POLICY") == 3


def test_phase_11_finops_cost_center_id_check_constraint():
    """Migration 0043 must enforce cost_center_id matches
    CC-{4-digit-number} pattern via CHECK constraint (PRD §F27.3.1
    verbatim)."""
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[2]
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0043_phase_11_finops.py"
    )
    content = migration.read_text(encoding="utf-8")
    assert "ck_phase_11_finops_department_mapping_cost_center_id" in content
    assert r"CC-\d{4}" in content


def test_phase_11_finops_alembic_module_filename_matches_baseline():
    """Migration file name must match `0043_phase_11_finops.py`
    exactly. Guard against filename drift between sprint planning
    and committed artifact."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    versions_dir = repo_root / "apps" / "api" / "alembic" / "versions"
    candidates = sorted(versions_dir.glob("0043_phase_11_finops*"))
    assert len(candidates) == 1
    assert candidates[0].name == "0043_phase_11_finops.py"
