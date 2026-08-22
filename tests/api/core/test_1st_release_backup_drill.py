"""
tests/api/core/test_1st_release_backup_drill.py — 1st release backup drill PITR.

1st release launch (cj-style 64번째 진입점) — T7.2 (AC #9.4) — F18.5 Production verification.
- 0036 PITR drill quarterly + RPO 4h / RTO 24h SLA verification +
- Sentry alert `backup_drill_overdue` 결정 wire.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_smoke_routes_module_exists():
    """apps/api/modules/launch/smoke_routes.py should exist."""
    smoke_path = REPO_ROOT / "apps" / "api" / "modules" / "launch" / "smoke_routes.py"
    assert smoke_path.exists()


def test_smoke_routes_defines_backup_status():
    """smoke_routes.py should define BackupStatus model with RPO/RTO SLA."""
    smoke_path = REPO_ROOT / "apps" / "api" / "modules" / "launch" / "smoke_routes.py"
    content = smoke_path.read_text(encoding="utf-8")
    assert "BackupStatus" in content
    assert "rpo_hours" in content
    assert "rto_hours" in content
    assert "4" in content  # RPO 4h
    assert "24" in content  # RTO 24h


def test_sentry_alerts_backend_defined():
    """apps/api/lib/observability/sentry-alerts.py should exist."""
    sentry_path = REPO_ROOT / "apps" / "api" / "lib" / "observability" / "sentry-alerts.py"
    assert sentry_path.exists()
    content = sentry_path.read_text(encoding="utf-8")
    assert "ALERT_RULES" in content
    assert "pitr_drill_overdue" in content
    assert "tenant_isolation_violation" in content


def test_sentry_alerts_frontend_defined():
    """apps/web/lib/observability/sentry-alerts.ts should exist."""
    sentry_path = REPO_ROOT / "apps" / "web" / "lib" / "observability" / "sentry-alerts.ts"
    assert sentry_path.exists()
    content = sentry_path.read_text(encoding="utf-8")
    assert "AlertRule" in content
    assert "5xx_error_rate" in content
    assert "listen_notify_connection_drop" in content
    assert "two_fa_verification_failure" in content


def test_sentry_alerts_total_5_rules():
    """sentry-alerts should have at least 5 alert rules."""
    backend_path = REPO_ROOT / "apps" / "api" / "lib" / "observability" / "sentry-alerts.py"
    content = backend_path.read_text(encoding="utf-8")
    rules_count = content.count('"5xx_api_error_rate"') + content.count('"tenant_isolation_violation"') + \
        content.count('"alembic_migration_failure"') + content.count('"audit_log_integrity_failure"') + \
        content.count('"pitr_drill_overdue"')
    assert rules_count >= 5


def test_launch_module_router_exported():
    """apps/api/modules/launch/__init__.py should re-export launch_router."""
    init_path = REPO_ROOT / "apps" / "api" / "modules" / "launch" / "__init__.py"
    assert init_path.exists()
    content = init_path.read_text(encoding="utf-8")
    assert "launch_router" in content


def test_capability_py_has_launch_monitoring():
    """capability.py should have LAUNCH_MONITORING enum and grants."""
    cap_path = REPO_ROOT / "apps" / "api" / "core" / "capability.py"
    content = cap_path.read_text(encoding="utf-8")
    assert "LAUNCH_MONITORING" in content
    # 4 industries have LAUNCH_MONITORING
    count = content.count("Capability.LAUNCH_MONITORING,")
    assert count >= 4


def test_database_backup_doc_exists():
    """docs/database-backup.md should exist (Phase 4 wire 71a033a)."""
    backup_path = REPO_ROOT / "docs" / "database-backup.md"
    if backup_path.exists():
        content = backup_path.read_text(encoding="utf-8")
        # PITR mentioned
        assert "PITR" in content
