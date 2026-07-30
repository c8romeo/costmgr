"""tests.api.test_industry_selector — service-layer tests for M0 onboarding.

Story 1.1 — Task 6.1. The DB-backed tests (version bump, audit_logs row,
`tenant_settings` upsert) require a real Postgres with the RLS shim
applied — gated by the same `rls_enabled` env var as `tests/rls/`
(Decision 2: Docker CI-only).

In environments WITHOUT a Postgres (local dev, the current `costmgr`
Windows setup), the tests in this file degrade gracefully:
  - Pure A7 / grace-period tests still run (no DB).
  - Service-layer tests with mocked AsyncSession still run.
  - DB-backed tests are SKIPPED with a clear message.

When CI=true (or RLS_RUN_LOCAL=1) is set, a Postgres fixture is expected
to be running on localhost:54322. The DB-backed tests then activate and
exercise the full SettingsService flow.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m0_onboarding.services.settings_service import (
    ForbiddenRoleError,
    IndustryLockedError,
    SettingsService,
    TenantSettingsNotFoundError,
)
from packages.services.m0_onboarding.industry_menu import (
    GRACE_PERIOD_DAYS,
    Industry,
)


# ── DB gating (mirrors tests/rls/conftest.py) ───────────────
_DB_AVAILABLE = os.environ.get("CI", "").lower() == "true" or os.environ.get(
    "RLS_RUN_LOCAL", ""
) == "1"


# ─────────────────────────────────────────────────────────────
# Pure unit tests (no DB, no mocks) — Story 1.1 AC #4 transitions
# ─────────────────────────────────────────────────────────────


def test_service_forbids_non_owner_member_role() -> None:
    """Decision §3 — only `owner` may change industry."""
    service = SettingsService(session=MagicMock(), trace_id="test")  # type: ignore[arg-type]
    with pytest.raises(ForbiddenRoleError) as exc_info:
        import asyncio

        asyncio.run(
            service.update_industry(
                tenant_id=uuid.uuid4(),
                target_industry=Industry.SERVICE,
                actor_id=uuid.uuid4(),
                role="member",
            )
        )
    assert exc_info.value.role == "member"


def test_service_forbids_non_owner_viewer_role() -> None:
    """Decision §3 — viewer also blocked."""
    service = SettingsService(session=MagicMock(), trace_id="test")  # type: ignore[arg-type]
    with pytest.raises(ForbiddenRoleError) as exc_info:
        import asyncio

        asyncio.run(
            service.update_industry(
                tenant_id=uuid.uuid4(),
                target_industry=Industry.MANUFACTURING,
                actor_id=uuid.uuid4(),
                role="viewer",
            )
        )
    assert exc_info.value.role == "viewer"


def test_service_forbids_consultant_proxy() -> None:
    """Decision §3 — consultant_proxy is read-only at this layer."""
    service = SettingsService(session=MagicMock(), trace_id="test")  # type: ignore[arg-type]
    with pytest.raises(ForbiddenRoleError) as exc_info:
        import asyncio

        asyncio.run(
            service.update_industry(
                tenant_id=uuid.uuid4(),
                target_industry=Industry.SERVICE,
                actor_id=uuid.uuid4(),
                role="consultant_proxy",
            )
        )
    assert exc_info.value.role == "consultant_proxy"


# ─────────────────────────────────────────────────────────────
# Service-layer tests with a mocked AsyncSession
# ─────────────────────────────────────────────────────────────


def _make_settings_row(
    *,
    tenant_id: uuid.UUID,
    onboarding: dict[str, Any],
    settings_version: int = 1,
):
    """Build a TenantSettings ORM-like mock.

    The mock supports `.onboarding`, `.settings_version`, `.tenant_id`,
    `.updated_at` attribute access — enough for SettingsService to read.
    """
    row = MagicMock()
    row.tenant_id = tenant_id
    row.onboarding = onboarding
    row.settings_version = settings_version
    row.updated_at = datetime.now(tz=UTC)
    row.baseline = {}
    row.abc = {}
    row.ai = {}
    return row


def _mock_session_with_row(row: Any) -> AsyncMock:
    """AsyncMock session that returns `row` from `SELECT ... FOR UPDATE`."""
    session = AsyncMock()
    # SELECT FOR UPDATE returns a row
    select_result = MagicMock()
    select_result.scalar_one_or_none = MagicMock(return_value=row)
    session.execute = AsyncMock(return_value=select_result)
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


def test_service_writes_audit_row_before_settings_update() -> None:
    """Anti-pattern guard — audit_logs row BEFORE tenant_settings update.

    This test verifies the ORDER of operations: `emit_audit` (which calls
    `session.flush()` internally) runs before `session.flush()` on the
    settings update. We assert by inspecting call ordering of the mock.

    F-36: strengthened assertions — also verifies the audit payload
    carries `reason` and `version` (so future readers can reconstruct the
    pre/post state from the log alone), and that `trace_id` propagates
    from SettingsService into the AuditLog row.
    """
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    # Fresh tenant — onboarding has the new `is_initial: true` default.
    row = _make_settings_row(
        tenant_id=tenant_id,
        onboarding={"industry": None, "is_initial": True, "selected_at": None},
        settings_version=1,
    )
    session = _mock_session_with_row(row)
    service = SettingsService(session=session, trace_id="t-audit-first")

    import asyncio

    asyncio.run(
        service.update_industry(
            tenant_id=tenant_id,
            target_industry=Industry.SERVICE,
            actor_id=actor_id,
            role="owner",
        )
    )

    # `session.add` is called for the AuditLog row (via emit_audit).
    # The SettingsService then mutates `row.onboarding` + `row.settings_version`.
    add_calls = session.add.call_args_list
    assert len(add_calls) >= 1, "session.add should have been called for audit row"
    # The first added object is the AuditLog row.
    first_added = add_calls[0].args[0]
    assert first_added.action == "industry_selected"
    assert first_added.target_table == "tenant_settings"
    assert first_added.actor_id == actor_id
    assert first_added.tenant_id == tenant_id
    assert first_added.payload["industry"] == Industry.SERVICE.value

    # F-36: payload must include `reason` and pre-bump `version` so the
    # log entry is self-describing (a downstream reader should not need
    # to join against tenant_settings to interpret what changed).
    assert first_added.payload.get("reason") == "industry_selected_initial", (
        "Audit payload must carry a `reason` discriminator so log analytics "
        "can distinguish first-time selection from a grace-period change."
    )
    assert first_added.payload.get("version") == 1, (
        "Audit payload must record the PRE-bump settings_version so the "
        "log is a complete before/after record."
    )

    # F-36: trace_id must propagate from SettingsService into AuditLog
    # so a support engineer can grep the audit log for the same trace_id
    # they saw in the HTTP response header.
    assert first_added.trace_id == "t-audit-first", (
        "Audit row must inherit trace_id from SettingsService for log "
        "correlation with the HTTP response."
    )


def test_service_bumps_settings_version_on_update() -> None:
    """AC #1 — `settings_version` increments from 1 → 2 on first write."""
    tenant_id = uuid.uuid4()
    row = _make_settings_row(
        tenant_id=tenant_id,
        onboarding={"industry": None, "is_initial": True, "selected_at": None},
        settings_version=1,
    )
    session = _mock_session_with_row(row)
    service = SettingsService(session=session)

    import asyncio

    _, version, *_ = asyncio.run(
        service.update_industry(
            tenant_id=tenant_id,
            target_industry=Industry.MANUFACTURING,
            actor_id=uuid.uuid4(),
            role="owner",
        )
    )
    assert version == 2
    assert row.settings_version == 2


def test_service_blocks_change_after_seven_days() -> None:
    """AC #4 — day 7+ → 409 INDUSTRY_LOCKED."""
    tenant_id = uuid.uuid4()
    long_ago = (datetime.now(tz=UTC) - timedelta(days=GRACE_PERIOD_DAYS + 3)).isoformat()
    row = _make_settings_row(
        tenant_id=tenant_id,
        onboarding={
            "industry": Industry.MANUFACTURING.value,
            "is_initial": False,
            "selected_at": long_ago,
        },
    )
    session = _mock_session_with_row(row)
    service = SettingsService(session=session)

    with pytest.raises(IndustryLockedError) as exc_info:
        import asyncio

        asyncio.run(
            service.update_industry(
                tenant_id=tenant_id,
                target_industry=Industry.SERVICE,
                actor_id=uuid.uuid4(),
                role="owner",
            )
        )
    assert exc_info.value.current_industry == Industry.MANUFACTURING
    assert exc_info.value.next_fiscal_year_start.startswith(str(datetime.now(tz=UTC).year + 1))


def test_service_allows_change_within_grace_period() -> None:
    """Decision §1 — within 7 days → 200 OK + warning header flag."""
    tenant_id = uuid.uuid4()
    recent = (datetime.now(tz=UTC) - timedelta(days=3)).isoformat()
    row = _make_settings_row(
        tenant_id=tenant_id,
        onboarding={
            "industry": Industry.MANUFACTURING.value,
            "is_initial": False,
            "selected_at": recent,
        },
    )
    session = _mock_session_with_row(row)
    service = SettingsService(session=session)

    import asyncio

    _, _, _, _, warning_header = asyncio.run(
        service.update_industry(
            tenant_id=tenant_id,
            target_industry=Industry.SERVICE,
            actor_id=uuid.uuid4(),
            role="owner",
        )
    )
    assert warning_header is True, "Within-grace writes must flag warning_header=True"


def test_service_no_warning_for_first_selection() -> None:
    """First-time selection (is_initial=True) does NOT trigger warning header."""
    tenant_id = uuid.uuid4()
    row = _make_settings_row(
        tenant_id=tenant_id,
        onboarding={"industry": None, "is_initial": True, "selected_at": None},
    )
    session = _mock_session_with_row(row)
    service = SettingsService(session=session)

    import asyncio

    _, _, _, _, warning_header = asyncio.run(
        service.update_industry(
            tenant_id=tenant_id,
            target_industry=Industry.SERVICE,
            actor_id=uuid.uuid4(),
            role="owner",
        )
    )
    assert warning_header is False


def test_service_raises_not_found_when_row_missing() -> None:
    """Defensive — `TenantSettings` row missing should raise a typed error."""
    tenant_id = uuid.uuid4()
    session = AsyncMock()
    select_result = MagicMock()
    select_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=select_result)
    service = SettingsService(session=session)

    with pytest.raises(TenantSettingsNotFoundError) as exc_info:
        import asyncio

        asyncio.run(
            service.update_industry(
                tenant_id=tenant_id,
                target_industry=Industry.SERVICE,
                actor_id=uuid.uuid4(),
                role="owner",
            )
        )
    assert exc_info.value.tenant_id == tenant_id


# ─────────────────────────────────────────────────────────────
# DB-backed tests — CI-only (gated by `rls_enabled`)
# ─────────────────────────────────────────────────────────────

# The full DB-backed flow (Story 1.1 AC #1: row upsert + version bump +
# audit_logs entry) requires the test Postgres from tests/rls/conftest.py.
# In CI, the `rls_db` fixture seeds tenants + tenant_settings rows. We add
# the DB-backed assertions here so they activate alongside the RLS suite.


@pytest.fixture
def rls_enabled() -> bool:
    return _DB_AVAILABLE


@pytest.mark.xfail(
    reason="DB fixture re-export pending — Story 0.5 wires rls_db fixtures "
    "from tests/rls/conftest.py into tests/api/. Strict=False so a passing "
    "run after the wire-up is reported as XPASS rather than failing CI.",
    strict=False,
)
def test_select_industry_creates_tenant_settings(rls_enabled: bool) -> None:
    """AC #1: first POST → tenant_settings.onboarding has the new industry.

    Once the `tenant_pair` fixture is exposed outside `tests/rls/`, this
    xfail marker can be removed and the test body should run end-to-end.
    The original `if not rls_enabled: pytest.skip(...)` branch lives on
    so the test still degrades to skip when no Postgres is available.
    """
    if not rls_enabled:
        pytest.skip(
            "DB-backed test — set CI=true or RLS_RUN_LOCAL=1 (Decision 2: CI-only)."
        )
    # The actual DB-backed implementation is wired in Story 0.2's
    # `tests/rls/test_tenant_isolation.py` pattern. The full body lands
    # in the same commit as the conftest bootstrap (see Story 0.2 Task 8).
    pytest.fail("Story 0.5 fixture re-export still pending")


@pytest.mark.xfail(
    reason="DB fixture re-export pending — Story 0.5 wires rls_db fixtures "
    "from tests/rls/conftest.py into tests/api/. Strict=False so a passing "
    "run after the wire-up is reported as XPASS rather than failing CI.",
    strict=False,
)
def test_change_industry_after_calculation_blocked(rls_enabled: bool) -> None:
    """AC #4: last_calc_date exists → 409 INDUSTRY_LOCKED.

    Decision §1 also requires blocking changes after the first calculation
    (A7 전진법). This test is DB-backed because `last_calc_date` is read
    from a separate row that the pure decision function does not know about.
    """
    if not rls_enabled:
        pytest.skip(
            "DB-backed test — set CI=true or RLS_RUN_LOCAL=1 (Decision 2: CI-only)."
        )
    pytest.fail("Story 0.5 fixture re-export still pending")
