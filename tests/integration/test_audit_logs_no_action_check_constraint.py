"""tests.integration.test_audit_logs_no_action_check_constraint — Story 12.4 pin.

CR 11-2/11-3/12-1 lessons + spec-vs-reality divergence pinning.

The Story 12.4 spec suggested creating an Alembic 0023 migration to add
a CHECK constraint on `audit_logs.action` mirroring the new
`ActionClass.TWO_FACTOR_AUTH` 6 values. **That migration is intentionally
NOT created**, because the underlying premise is wrong:

  - `audit_logs.action` has NO CHECK constraint (verified by reading
    `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py`).
  - The 3-way A5 drift detector in
    `tests/integration/test_audit_action_consistency.py` EXPLICITLY
    excludes `audit_logs` from its ActionClass↔DB CHECK gate (see
    `class_to_table` map + the comment "audit_logs does not have an
    action CHECK").
  - Adding a 6-value CHECK would block every other ActionClass's audit
    writes (20 ActionClass × varying action counts > 6).

This test pins the invariant so any future migration that accidentally
adds a CHECK constraint to audit_logs.action will fail loudly.

References:
  - apps/api/alembic/versions/0001_tenants_users_memberships_settings.py
    (audit_logs table definition — action TEXT NOT NULL, no CHECK)
  - apps/api/core/audit_action.py:584-602 (TWO_FACTOR_AUTH → audit_logs)
  - tests/integration/test_audit_action_consistency.py:126-205
    (A5 3-way gate; explicit audit_logs exclusion)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module_from_path(rel_path: str) -> object:
    """Load a Python module from a repo-relative path via importlib.

    Some source files (Alembic migrations, RLS fixtures) live outside
    the apps.api. package layout, so importlib is the only portable
    loader.
    """
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / rel_path
    spec = importlib.util.spec_from_file_location(target.stem, target)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_alembic_0022_does_not_exist() -> None:
    """Migration 0022 is the users.totp_* wire — confirm the filename.

    Defense against accidental misnumbering. The 0022 file must exist
    (Story 12.4 wire). The 0023 file MUST NOT exist (audit_logs CHECK
    extension was rejected per this test module's docstring).
    """
    repo_root = Path(__file__).resolve().parents[2]
    versions_dir = repo_root / "apps" / "api" / "alembic" / "versions"
    assert (versions_dir / "0022_users_totp_columns.py").exists(), (
        "Story 12.4 wire missing: 0022_users_totp_columns.py must exist"
    )
    assert not (versions_dir / "0023_audit_logs_action_check.py").exists(), (
        "audit_logs CHECK extension migration 0023 must NOT be created — "
        "the audit_logs.action column is intentionally CHECK-less per "
        "A5 drift detector design (tests/integration/test_audit_action_consistency.py)"
    )
    # NOTE (CR 11-3 lesson 2026-08-20): Do NOT glob `0023_*.py` here. The
    # specific filename pin above is the ONLY invariant we care about —
    # audit_logs must remain CHECK-less. Other 0023 migrations are
    # LEGITIMATE (e.g. `0023_used_challenge_tokens.py` from Story 12.4
    # 2FA TOTP wire, which has nothing to do with audit_logs).
    # The original over-broad glob assertion incorrectly rejected any
    # 0023 file. Removed; the specific filename check is sufficient.


def test_alembic_0001_audit_logs_action_has_no_check_constraint() -> None:
    """audit_logs.action column is plain TEXT NOT NULL — no CHECK.

    This is the source of truth. Read the 0001 migration and confirm
    the audit_logs CREATE TABLE statement does NOT include a CHECK
    constraint on the `action` column.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0001_tenants_users_memberships_settings.py"
    ).read_text(encoding="utf-8")

    # Sanity: the audit_logs table is created somewhere in the file.
    assert "audit_logs" in src, "audit_logs table not found in 0001 migration"
    # Defense: no CHECK constraint applied to audit_logs.action.
    # If someone added `CHECK (action IN (...))` here, this assertion fails.
    assert "CHECK (action" not in src, (
        "audit_logs.action has a CHECK constraint in 0001 — "
        "this is forbidden per A5 drift detector design"
    )
    # Positive pin: action is plain TEXT NOT NULL.
    # 0001 uses multi-space column alignment (action␣␣␣␣␣␣␣␣TEXT NOT NULL),
    # so we match via regex to tolerate whitespace variation.
    import re
    assert re.search(r"\baction\s+TEXT\s+NOT\s+NULL\b", src), (
        "audit_logs.action should be plain TEXT NOT NULL"
    )


def test_a5_drift_detector_explicitly_excludes_audit_logs() -> None:
    """The A5 3-way gate explicitly skips audit_logs in its class_to_table map.

    `tests/integration/test_audit_action_consistency.py` is the canonical
    A5 drift detector. Its `class_to_table` map contains only CALC_LOG,
    VERIFICATION_LOG, VERIFICATION — proving TWO_FACTOR_AUTH (and every
    other ActionClass) is intentionally out of scope for the DB-CHECK
    gate because audit_logs.action has no CHECK constraint.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "tests"
        / "integration"
        / "test_audit_action_consistency.py"
    ).read_text(encoding="utf-8")

    # The exclusion comment must be present in the source.
    assert (
        "audit_logs does not have an action CHECK" in src
    ), "A5 drift detector must document the audit_logs exclusion"


def test_two_factor_auth_routes_to_audit_logs() -> None:
    """ActionClass.TWO_FACTOR_AUTH → audit_logs (NOT a separate ledger).

    Pin the registry entry in audit_action.py:584-602. This is the
    reason the audit_logs CHECK-less invariant MUST be preserved — the
    TWO_FACTOR_AUTH 6 actions (two_factor_setup_initiated, etc.) flow
    through the same audit_logs table that every other ActionClass
    writes to.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root / "apps" / "api" / "core" / "audit_action.py"
    ).read_text(encoding="utf-8")

    # The registry entry must name audit_logs as the destination table.
    assert "ActionClass.TWO_FACTOR_AUTH" in src
    # Search for the line mapping TWO_FACTOR_AUTH → "audit_logs".
    # We tolerate any whitespace/formatting inside the tuple body.
    assert (
        'ActionClass.TWO_FACTOR_AUTH: (\n            "audit_logs"' in src
        or 'ActionClass.TWO_FACTOR_AUTH: ("audit_logs"' in src
    ), (
        "ActionClass.TWO_FACTOR_AUTH must route to audit_logs (not a "
        "separate two_factor_auth_log table)"
    )

    # The 6 typed TwoFactorAuthAction values must be present.
    for action in (
        "two_factor_setup_initiated",
        "two_factor_setup_completed",
        "two_factor_challenge_passed",
        "two_factor_challenge_failed",
        "two_factor_recovery_consumed",
        "two_factor_disabled",
    ):
        assert action in src, (
            f"AuditAction {action!r} missing from audit_action.py — "
            "the 6-value enum is the SSOT for TWO_FACTOR_AUTH"
        )
