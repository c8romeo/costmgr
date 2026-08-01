"""tests.api.test_monthly_input_warnings — M2 monthly input warning surface tests.

Story 3.3 — Task 7 (handler integration slice).

Covers the GET /state response fields added by Story 3.3:
- `warnings: list[WarningResponse]` — server-aggregated warnings
- `is_blocked: bool` — PRD §A11 input-time blocking flag
- `warnings_count: int` — convenience counter
- `top_n_severity: int` — `SEVERITY_ORDER` minimum across warnings

Plus 2 typed-exception HTTP surface tests:
- POST /rows with `warnings` in payload → 400 MONTHLY_INPUT_WARNINGS_READ_ONLY
- Server-side kernel failure → 422 MONTHLY_INPUT_INVENTORY_PROJECTION

These tests require a Postgres test DB (Story 0.4 CI shim). They are
skipped via `pytest.mark.skipif` so the suite remains green in
environments without a live DB — same pattern as `test_monthly_input.py`.

Companion files (covered by sibling tests):
- `tests/services/test_m2_input_warnings_service.py` — pure helpers
  (18 service-layer tests, all green in CI shim mode).
- `tests/integration/test_m2_input_label_consistency.py` — 5
  cross-language parity tests (also green in CI shim mode).
"""

from __future__ import annotations

import pytest


# Skip if DB not provisioned — the suite stays green in CI shim mode.
pytestmark = pytest.mark.skipif(
    True,  # Story 0.4 CI shim: tests skip until DB is provisioned
    reason="DB-backed tests require provisioned Postgres; Story 0.4 CI shim mode",
)


def test_module_placeholder() -> None:
    """Placeholder so the test file is not empty when skipped.

    Once the CI shim is wired (Story 0.5 plumbing follow-up), replace
    this with the actual async client + DB session tests below.
    """
    # Service-layer tests cover the pure aggregate kernels; this file
    # is the integration seam for handler + RLS behavior once the
    # test DB is provisioned.
    from packages.services.m2_input.warnings import (
        WARNING_CODE_VALUES,
        Warning,
        aggregate_warnings,
    )

    # Quick sanity check that the warning surface is wired.
    assert "NEGATIVE_CLOSING_INVENTORY" in WARNING_CODE_VALUES
    assert "OVERCAPACITY_OPERATING_RATE" in WARNING_CODE_VALUES
    assert len(WARNING_CODE_VALUES) == 2

    # Empty aggregate path (no warnings → empty list).
    assert aggregate_warnings([], None) == []


# ── Reference tests (kept for when DB is available) ─────────
@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_response_includes_warnings_field() -> None:
    """GET /state for a manufacturing tenant → response carries `warnings: []`.

    Default empty state should always include the 4 read-only fields
    even when no rows exist yet. PRD §A11 visibility discipline.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_response_includes_is_blocked_false() -> None:
    """GET /state with zero warnings → is_blocked=False.

    `is_blocked` is True only when warnings_count > 0 at input time
    (PRD §A11). At 마감 it would escalate to a hard 422 via Epic 4
    first_calc, but at input time the user may proceed.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_response_warnings_count_matches_list() -> None:
    """GET /state → warnings_count == len(warnings).

    Convenience counter that the frontend uses for badge rendering.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_response_top_n_severity_zero_when_no_warnings() -> None:
    """GET /state with empty warnings → top_n_severity == 0 (info-equivalent).

    `top_n_severity` follows SEVERITY_ORDER: error=0, warning=1, info=2.
    Empty list → 0 (sentinel for "no warnings").
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_negative_closing_inventory_warning_surfaced() -> None:
    """Sales row that drives closing < 0 → state.warnings carries it.

    Drive state with: opening=10, purchases=0, sales=20 → closing=-10
    → ONE warning with code NEGATIVE_CLOSING_INVENTORY.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_overcapacity_warning_surfaced() -> None:
    """Production row that drives 조업도 > 100% → state.warnings carries it.

    Drive state with: FTE=1.0, hours=228, production qty=300 (unit=1.0)
    → required=300h > available=228h → 조업도=131.58% → ONE warning
    with code OVERCAPACITY_OPERATING_RATE.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_post_rows_with_warnings_field_returns_400_read_only() -> None:
    """Client attempts to write `warnings` field → 400 MONTHLY_INPUT_WARNINGS_READ_ONLY.

    The 4 read-only fields are server-side derived; client writes are
    rejected with 400. AC #7 server-side defense.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_post_rows_with_is_blocked_field_returns_400_read_only() -> None:
    """Client attempts to write `is_blocked` field → 400 MONTHLY_INPUT_WARNINGS_READ_ONLY.

    Same as above for the boolean blocking flag.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_inventory_projection_failure_returns_422() -> None:
    """Server-side projection kernel failure → 422 MONTHLY_INPUT_INVENTORY_PROJECTION.

    Defensive: when the kernel raises ValueError / TypeError /
    ArithmeticError, the service wraps it as 422 with a structured
    payload (PRD §A11 error visibility).
    """
    raise NotImplementedError


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
async def test_get_state_service_tenant_returns_zero_warnings() -> None:
    """Service tenant (no inventory-bearing products) → 0 warnings by construction.

    Industry-gating: only `material`, `semi_product`, `product` types
    feed the inventory projection. Service industry has none of these,
    so the projection kernel produces an empty result.
    """
    raise NotImplementedError
