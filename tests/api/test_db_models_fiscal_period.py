"""tests.api.test_db_models_fiscal_period — Story 11.2 ORM model tests.

6 cases verifying the FiscalPeriod SQLAlchemy 2.x ORM model surface:
- Table name + primary key
- Status CHECK constraint (4-state 1-way)
- close_sequence_state CHECK constraint (5-state)
- 3 stage-ordering CHECK constraints (defense-in-depth)
- 2 consistency CHECK constraints (confirmed/closed invariants)
- UNIQUE (tenant_id, period_key) constraint
"""

from __future__ import annotations

import pytest

from apps.api.core.db_models import FiscalPeriod


def test_fiscal_period_table_name() -> None:
    assert FiscalPeriod.__tablename__ == "fiscal_periods"


def test_fiscal_period_status_default_is_open() -> None:
    """AD-6 1-way state machine — initial state is 'open'."""
    # Default value is set at the column default, not at instantiation
    # time (SQLAlchemy applies it on flush). Verify the column default.
    from sqlalchemy import inspect

    mapper = inspect(FiscalPeriod)
    status_col = mapper.columns["status"]
    assert status_col.default.arg == "open"


def test_fiscal_period_close_sequence_state_default() -> None:
    """Initial close_sequence_state is 'divisions' (PRD §F11.1)."""
    from sqlalchemy import inspect

    mapper = inspect(FiscalPeriod)
    state_col = mapper.columns["close_sequence_state"]
    assert state_col.default.arg == "divisions"


def test_fiscal_period_check_constraints_cover_5_required_invariants() -> None:
    """All 7 CHECK constraints are present (status + state + 3 ordering + 2 consistency)."""
    check_names = {
        ck.name
        for ck in FiscalPeriod.__table_args__
        if hasattr(ck, "name") and ck.name is not None
    }
    expected = {
        "fiscal_periods_status_check",
        "fiscal_periods_close_sequence_state_check",
        "fiscal_periods_divisions_ordering_check",
        "fiscal_periods_manufacturing_ordering_check",
        "fiscal_periods_abc_ordering_check",
        "fiscal_periods_confirmed_requires_closed_check",
        "fiscal_periods_closed_requires_closed_at_check",
        "fiscal_periods_period_key_format_check",
    }
    assert expected.issubset(check_names), (
        f"Missing CHECK constraints: {expected - check_names}"
    )


def test_fiscal_period_unique_tenant_period() -> None:
    """UNIQUE (tenant_id, period_key) constraint is registered."""
    from sqlalchemy import UniqueConstraint

    unique_constraints = [
        c for c in FiscalPeriod.__table_args__ if isinstance(c, UniqueConstraint)
    ]
    assert any(
        "tenant_id" in (c.columns or []) and "period_key" in (c.columns or [])
        for c in unique_constraints
    ), "UNIQUE (tenant_id, period_key) constraint missing"


def test_fiscal_period_period_key_format_check() -> None:
    """AD-24 typed period_key CHECK constraint matches '\\d{4}-(0[1-9]|1[0-2])'."""
    from sqlalchemy import CheckConstraint, inspect

    mapper = inspect(FiscalPeriod)
    # Reference the column to assert it is reachable through mapper.columns.
    assert "period_key" in mapper.columns
    # Find the CHECK constraint that references period_key
    found_format_check = False
    for ck in FiscalPeriod.__table_args__:
        if isinstance(ck, CheckConstraint) and ck.sqltext is not None:
            text = str(ck.sqltext)
            if "period_key" in text and "\\d{4}-" in text:
                found_format_check = True
                break
    assert found_format_check, "AD-24 period_key format CHECK constraint missing"


def test_fiscal_period_status_check_constraint_text() -> None:
    """status CHECK includes all 4 expected values."""
    from sqlalchemy import CheckConstraint

    for ck in FiscalPeriod.__table_args__:
        if not isinstance(ck, CheckConstraint) or ck.sqltext is None:
            continue
        text = str(ck.sqltext)
        if "status IN" in text and "open" in text:
            for value in ("open", "closing", "closed", "reversed"):
                assert value in text, f"status CHECK missing value {value}"
            return
    pytest.fail("status CHECK constraint not found")


def test_fiscal_period_close_sequence_state_check_constraint_text() -> None:
    """close_sequence_state CHECK includes all 5 expected values."""
    from sqlalchemy import CheckConstraint

    for ck in FiscalPeriod.__table_args__:
        if not isinstance(ck, CheckConstraint) or ck.sqltext is None:
            continue
        text = str(ck.sqltext)
        if "close_sequence_state IN" in text:
            for value in (
                "divisions",
                "manufacturing",
                "abc",
                "common",
                "confirmed",
            ):
                assert value in text, f"state CHECK missing value {value}"
            return
    pytest.fail("close_sequence_state CHECK constraint not found")


def test_fiscal_period_confirmed_requires_closed_check_text() -> None:
    """consistency CHECK: close_sequence_state='confirmed' → status='closed'."""
    from sqlalchemy import CheckConstraint

    for ck in FiscalPeriod.__table_args__:
        if not isinstance(ck, CheckConstraint) or ck.sqltext is None:
            continue
        text = str(ck.sqltext)
        if (
            "close_sequence_state" in text
            and "confirmed" in text
            and "status" in text
            and "closed" in text
        ):
            # Anti-pattern: state='confirmed' AND status != 'closed' blocked.
            assert "!=" in text or "OR" in text.upper()
            return
    pytest.fail("confirmed-requires-closed CHECK constraint not found")
