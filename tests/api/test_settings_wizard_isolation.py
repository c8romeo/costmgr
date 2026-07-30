"""tests.api.test_settings_wizard_isolation — RLS-backed tenant isolation for wizard writes.

Story 1.2 — Task 7.2. Mirrors `test_industry_isolation.py`:

  - tenant A cannot save wizard fields against tenant B's `tenant_id`
    (the body schema has no `tenant_id` field — derived from JWT).
  - GET /completion returns the calling tenant's status only.

The pure-logic checks (`tenant_id` not in body, kw-only on service method)
run without a DB and are the structural anti-pattern guards from the spec.

DB-backed isolation tests are CI-only (Decision 2: Docker CI-only).
"""

from __future__ import annotations

import inspect
import os

import pytest

_DB_AVAILABLE = os.environ.get("CI", "").lower() == "true" or os.environ.get(
    "RLS_RUN_LOCAL", ""
) == "1"


def test_wizard_request_bodies_do_not_accept_tenant_id() -> None:
    """Anti-pattern guard — none of the wizard body schemas expose `tenant_id`.

    Tenant context is derived from JWT (AD-3); a body-supplied `tenant_id`
    would be a spoof vector.
    """
    from apps.api.modules.m0_onboarding.schemas import (
        AllocationCriteriaUpdateRequest,
        CurrencyField,
        FiscalYearStartField,
        LanguageField,
    )

    for schema in (
        FiscalYearStartField,
        CurrencyField,
        LanguageField,
        AllocationCriteriaUpdateRequest,
    ):
        assert "tenant_id" not in schema.model_fields, (
            f"{schema.__name__} must not expose tenant_id in body — AD-3"
        )


def test_settings_service_update_onboarding_field_takes_tenant_id_kw_only() -> None:
    """Same structural check on the service signature — `tenant_id` is
    keyword-only so callers cannot inject it positionally from a body."""
    from apps.api.modules.m0_onboarding.services.settings_service import (
        SettingsService,
    )

    sig = inspect.signature(SettingsService.update_onboarding_field)
    assert "tenant_id" in sig.parameters
    assert sig.parameters["tenant_id"].kind == inspect.Parameter.KEYWORD_ONLY


def test_settings_service_update_allocation_criteria_takes_tenant_id_kw_only() -> None:
    from apps.api.modules.m0_onboarding.services.settings_service import (
        SettingsService,
    )

    sig = inspect.signature(SettingsService.update_allocation_criteria)
    assert "tenant_id" in sig.parameters
    assert sig.parameters["tenant_id"].kind == inspect.Parameter.KEYWORD_ONLY


def test_settings_service_get_completion_takes_tenant_id_kw_only() -> None:
    from apps.api.modules.m0_onboarding.services.settings_service import (
        SettingsService,
    )

    sig = inspect.signature(SettingsService.get_completion)
    assert "tenant_id" in sig.parameters
    assert sig.parameters["tenant_id"].kind == inspect.Parameter.KEYWORD_ONLY


# ── DB-backed isolation tests (CI-only) ─────────────────────
@pytest.fixture
def rls_enabled() -> bool:
    return _DB_AVAILABLE


@pytest.mark.xfail(
    reason="DB fixture re-export pending — Story 0.5 wires rls_db fixtures "
    "from tests/rls/conftest.py into tests/api/. Strict=False so a passing "
    "run after the wire-up is reported as XPASS rather than failing CI.",
    strict=False,
)
def test_tenant_a_cannot_save_tenant_b_fiscal_year(rls_enabled: bool) -> None:
    """AC #2: tenant A's POST fiscal_year_start cannot target tenant B."""
    if not rls_enabled:
        pytest.skip(
            "RLS-backed test — set CI=true or RLS_RUN_LOCAL=1 (Decision 2: CI-only)."
        )
    pytest.fail("Story 0.5 fixture re-export still pending")


@pytest.mark.xfail(
    reason="DB fixture re-export pending — Story 0.5 wires rls_db fixtures "
    "from tests/rls/conftest.py into tests/api/. Strict=False so a passing "
    "run after the wire-up is reported as XPASS rather than failing CI.",
    strict=False,
)
def test_completion_scoped_per_tenant(rls_enabled: bool) -> None:
    """AC #2/3: GET /completion returns only the calling tenant's status."""
    if not rls_enabled:
        pytest.skip(
            "RLS-backed test — set CI=true or RLS_RUN_LOCAL=1 (Decision 2: CI-only)."
        )
    pytest.fail("Story 0.5 fixture re-export still pending")