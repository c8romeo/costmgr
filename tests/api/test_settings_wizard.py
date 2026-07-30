"""tests.api.test_settings_wizard — service-layer tests for the Settings Wizard.

Story 1.2 — Task 7.1 / 7.6. Pure-logic + DB-backed coverage for:

  - `SettingsService.update_onboarding_field()` for the 4 wizard fields
    (fiscal_year_start / currency / language / allocation_criteria).
  - `SettingsService.get_completion()` returning the post-write status.
  - A7 전진법 lock semantics (Task 7.6 — fiscal year + currency cannot change
    after the first calculation; mirrors Story 1.1 industry lock pattern).
  - Pydantic-level rejection of invalid values (caller-side, no DB needed).
  - Role gate (Decision §3: owner only) — mirrors `test_industry_selector.py`.

DB-backed tests are gated on `CI=true` / `RLS_RUN_LOCAL=1` (Decision 2 —
Docker CI-only enforcement). Locally they `pytest.skip` with a clear message.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from apps.api.core.jsonb_schemas import OnboardingField
from apps.api.modules.m0_onboarding.schemas import (
    AllocationCriteriaUpdateRequest,
    CurrencyField,
    FiscalYearStartField,
    LanguageField,
)
from apps.api.modules.m0_onboarding.services.settings_service import (
    CurrencyLockedError,
    FiscalYearLockedError,
    ForbiddenRoleError,
    SettingsService,
)

_DB_AVAILABLE = os.environ.get("CI", "").lower() == "true" or os.environ.get(
    "RLS_RUN_LOCAL", ""
) == "1"


# ── Pydantic schema validation (no DB, no service) ──────────
def test_fiscal_year_start_valid_pattern_passes() -> None:
    """A1 / AD-24: YYYY-MM with month 01..12 is accepted."""
    body = FiscalYearStartField(fiscal_year_start="2026-01")
    assert body.fiscal_year_start == "2026-01"


def test_fiscal_year_start_invalid_month_rejected() -> None:
    """Month > 12 must 422 at the Pydantic layer."""
    with pytest.raises(ValidationError):
        FiscalYearStartField(fiscal_year_start="2026-13")


def test_fiscal_year_start_invalid_year_rejected() -> None:
    """Non-numeric year must 422 at the Pydantic layer."""
    with pytest.raises(ValidationError):
        FiscalYearStartField(fiscal_year_start="abcd-01")


def test_currency_krw_accepted() -> None:
    body = CurrencyField(currency="KRW")
    assert body.currency == "KRW"


def test_currency_usd_accepted() -> None:
    body = CurrencyField(currency="USD")
    assert body.currency == "USD"


def test_currency_other_rejected() -> None:
    """A6: only KRW/USD supported in MVP — EUR/JPY must 422."""
    with pytest.raises(ValidationError):
        CurrencyField(currency="EUR")


def test_language_ko_kr_only() -> None:
    """NFR-18: MVP language is ko-KR only."""
    body = LanguageField(language="ko-KR")
    assert body.language == "ko-KR"


def test_language_other_rejected() -> None:
    with pytest.raises(ValidationError):
        LanguageField(language="en-US")


def test_allocation_criteria_count_must_be_positive() -> None:
    """Task 7.1: count=0 → 422 (≥1 row required)."""
    with pytest.raises(ValidationError):
        AllocationCriteriaUpdateRequest(criterion="direct_indirect", count=0)


def test_allocation_criteria_unknown_criterion_rejected() -> None:
    """Task 7.1: criterion must be in {direct_indirect, fixed_variable, drivers}."""
    with pytest.raises(ValidationError):
        AllocationCriteriaUpdateRequest(criterion="unknown", count=1)  # type: ignore[arg-type]


# ── Service-layer role gate (no DB) ─────────────────────────
def test_update_onboarding_field_forbids_member_role() -> None:
    """Decision §3 — only `owner` may change onboarding fields."""
    service = SettingsService(session=MagicMock(), trace_id="test")  # type: ignore[arg-type]
    with pytest.raises(ForbiddenRoleError):
        asyncio.run(
            service.update_onboarding_field(
                tenant_id=uuid.uuid4(),
                field=OnboardingField.FISCAL_YEAR_START,
                value="2026-01",
                actor_id=uuid.uuid4(),
                role="member",
            )
        )


def test_update_onboarding_field_forbids_viewer_role() -> None:
    service = SettingsService(session=MagicMock(), trace_id="test")  # type: ignore[arg-type]
    with pytest.raises(ForbiddenRoleError):
        asyncio.run(
            service.update_onboarding_field(
                tenant_id=uuid.uuid4(),
                field=OnboardingField.CURRENCY,
                value="KRW",
                actor_id=uuid.uuid4(),
                role="viewer",
            )
        )


# ── A7 전진법 lock after first calc (no DB) ─────────────────
def test_fiscal_year_lock_after_first_calc_raises() -> None:
    """Task 7.6: `last_calc_date` set → POST fiscal_year_start → 409 FiscalYearLockedError.

    Mocks the SELECT FOR UPDATE + completion read so the lock check fires
    before the audit/write path. Validates the typed exception shape.
    """
    tenant_id = uuid.uuid4()
    last_calc = (datetime.now(tz=UTC) - timedelta(days=30)).isoformat()
    onboarding = {
        "industry": "manufacturing",
        "selected_at": (datetime.now(tz=UTC) - timedelta(days=120)).isoformat(),
        "fiscal_year_start": "2026-01",
        "last_calc_date": last_calc,
    }
    row = _mock_settings_row(tenant_id=tenant_id, onboarding=onboarding)
    session = _mock_session_with_row(row)
    service = SettingsService(session, trace_id="test")

    with pytest.raises(FiscalYearLockedError) as exc_info:
        asyncio.run(
            service.update_onboarding_field(
                tenant_id=tenant_id,
                field=OnboardingField.FISCAL_YEAR_START,
                value="2026-07",
                actor_id=uuid.uuid4(),
                role="owner",
            )
        )
    assert exc_info.value.trace_id == "test"


def test_currency_lock_after_first_calc_raises() -> None:
    """Task 7.6: currency must 409 once last_calc_date is set."""
    tenant_id = uuid.uuid4()
    last_calc = (datetime.now(tz=UTC) - timedelta(days=30)).isoformat()
    onboarding = {
        "industry": "manufacturing",
        "selected_at": (datetime.now(tz=UTC) - timedelta(days=120)).isoformat(),
        "currency": "KRW",
        "last_calc_date": last_calc,
    }
    row = _mock_settings_row(tenant_id=tenant_id, onboarding=onboarding)
    session = _mock_session_with_row(row)
    service = SettingsService(session, trace_id="test")

    with pytest.raises(CurrencyLockedError):
        asyncio.run(
            service.update_onboarding_field(
                tenant_id=tenant_id,
                field=OnboardingField.CURRENCY,
                value="USD",
                actor_id=uuid.uuid4(),
                role="owner",
            )
        )


def test_fiscal_year_within_grace_succeeds_when_no_calc() -> None:
    """Task 7.6: no last_calc_date + within 7-day grace → no lock."""
    tenant_id = uuid.uuid4()
    recent = (datetime.now(tz=UTC) - timedelta(days=3)).isoformat()
    onboarding = {
        "industry": "manufacturing",
        "selected_at": recent,
        "fiscal_year_start": "2026-01",
        "fiscal_year_start_selected_at": recent,
    }
    row = _mock_settings_row(tenant_id=tenant_id, onboarding=onboarding)
    session = _mock_session_with_row(row)
    service = SettingsService(session, trace_id="test")

    result = asyncio.run(
        service.update_onboarding_field(
            tenant_id=tenant_id,
            field=OnboardingField.FISCAL_YEAR_START,
            value="2026-07",
            actor_id=uuid.uuid4(),
            role="owner",
        )
    )
    field, value, version, completion, trace = result
    assert field == OnboardingField.FISCAL_YEAR_START
    assert value == "2026-07"
    assert version == 1  # bumped from 0
    assert completion is not None
    assert trace == "test"


# ── Mock helpers (mirrors tests/api/test_industry_selector.py) ──
def _mock_settings_row(
    *, tenant_id: uuid.UUID, onboarding: dict[str, Any]
) -> MagicMock:
    row = MagicMock()
    row.tenant_id = tenant_id
    row.settings_version = 0
    row.onboarding = onboarding
    row.baseline = {}
    row.abc = {}
    row.ai = {}
    row.updated_at = datetime.now(tz=UTC)
    return row


def _mock_session_with_row(row: MagicMock) -> AsyncMock:
    """AsyncMock session that yields `row` for SELECT FOR UPDATE, then no-op
    flush/commit. Mirrors `_mock_session_with_row` from
    `test_industry_selector.py`.
    """
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = row
    session.execute.return_value = execute_result
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# ── DB-backed tests (CI-only) ───────────────────────────────
@pytest.fixture
def rls_enabled() -> bool:
    return _DB_AVAILABLE


@pytest.mark.xfail(
    reason="DB fixture re-export pending — Story 0.5 wires rls_db fixtures "
    "from tests/rls/conftest.py into tests/api/. Strict=False so a passing "
    "run after the wire-up is reported as XPASS rather than failing CI.",
    strict=False,
)
def test_save_fiscal_year_start_writes_audit_and_bumps_version(
    rls_enabled: bool,
) -> None:
    """AC #1: each save writes audit_logs + bumps settings_version."""
    if not rls_enabled:
        pytest.skip(
            "DB-backed test — set CI=true or RLS_RUN_LOCAL=1 (Decision 2: CI-only)."
        )
    pytest.fail("Story 0.5 fixture re-export still pending")


@pytest.mark.xfail(
    reason="DB fixture re-export pending — Story 0.5 wires rls_db fixtures "
    "from tests/rls/conftest.py into tests/api/. Strict=False so a passing "
    "run after the wire-up is reported as XPASS rather than failing CI.",
    strict=False,
)
def test_get_completion_all_empty_returns_four_missing(rls_enabled: bool) -> None:
    """AC #2: all-empty JSONB → missing=4 fields, is_complete=False."""
    if not rls_enabled:
        pytest.skip(
            "DB-backed test — set CI=true or RLS_RUN_LOCAL=1 (Decision 2: CI-only)."
        )
    pytest.fail("Story 0.5 fixture re-export still pending")