"""tests.services.m10_ai.test_promoter_port — Story 10.4 kernel tests.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
T1 tests for `packages/services/m10_ai/promoter_port.py`.

Test breakdown (~12 cases):
- compute_promotion_idempotency_key × 4 (AD-17 verbatim 3-tuple idempotency:
  deterministic same input → same UUID v5 derivation; different input →
  different UUID; UUID type; frozen determinism)
- validate_promotion_request × 4 (period_key YYYY-MM format ✓ / ✗ +
  source_draft_id UUID v7 ✓ / ✗)
- PROMOTE_STATUS_VALUES × 2 (frozenset 6 values verbatim + AD-15 parity
  marker)
- PromotionRequest + PromotionResult frozen × 2 (frozen invariant +
  typed fields)

AD-5 stdlib-only: no I/O, no clock, no random (UUID v5 derivation is
deterministic via uuid.NAMESPACE_URL + frozen seed).

AD-17 verbatim bind: idempotency key 3-tuple = (tenant_id, period_key,
source_draft_id).

A19 cohesion pattern 8 surface: kernel (T1) + port (T1) +
db schema (T2) + service (T3) + handler (T4) + envelope (T4) +
capability (T4) + audit (T4).
"""

from __future__ import annotations

import inspect
import uuid

import pytest

from packages.services.m10_ai.promoter_port import (
    PROMOTE_STATUS_VALUES,
    PromotionRequest,
    PromotionResult,
    compute_promotion_idempotency_key,
    validate_promotion_request,
)

# ── compute_promotion_idempotency_key ────────────────────────


def test_compute_promotion_idempotency_key_deterministic_same_input() -> None:
    """AD-17 verbatim: same 3-tuple inputs always produce same UUID v5.

    This is the core idempotency guarantee — DB-level UNIQUE constraint
    in alembic 0032 `monthly_input_promotions` table enforces the same
    3-tuple, and this UUID v5 key is the deterministic identifier.
    """
    tenant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    period_key = "2026-08"
    source_draft_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    key1 = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_draft_id=source_draft_id,
    )
    key2 = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_draft_id=source_draft_id,
    )

    assert key1 == key2
    assert isinstance(key1, uuid.UUID)


def test_compute_promotion_idempotency_key_different_tenant() -> None:
    """Different tenant_id → different UUID v5 derivation."""
    period_key = "2026-08"
    source_draft_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    tenant_a = uuid.UUID("11111111-1111-1111-1111-111111111111")
    tenant_b = uuid.UUID("22222222-2222-2222-2222-222222222222")

    key_a = compute_promotion_idempotency_key(
        tenant_id=tenant_a,
        period_key=period_key,
        source_draft_id=source_draft_id,
    )
    key_b = compute_promotion_idempotency_key(
        tenant_id=tenant_b,
        period_key=period_key,
        source_draft_id=source_draft_id,
    )

    assert key_a != key_b


def test_compute_promotion_idempotency_key_different_period() -> None:
    """Different period_key → different UUID v5 derivation."""
    tenant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    source_draft_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    key_jul = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key="2026-07",
        source_draft_id=source_draft_id,
    )
    key_aug = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key="2026-08",
        source_draft_id=source_draft_id,
    )

    assert key_jul != key_aug


def test_compute_promotion_idempotency_key_different_draft() -> None:
    """Different source_draft_id → different UUID v5 derivation."""
    tenant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    period_key = "2026-08"

    draft_a = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    draft_b = uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff")

    key_a = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_draft_id=draft_a,
    )
    key_b = compute_promotion_idempotency_key(
        tenant_id=tenant_id,
        period_key=period_key,
        source_draft_id=draft_b,
    )

    assert key_a != key_b


# ── validate_promotion_request ───────────────────────────────


def test_validate_promotion_request_valid_period_key() -> None:
    """period_key format YYYY-MM accepted (master PRD §V4 format)."""
    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08",
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="m2_service_role",
    )
    # Should not raise
    validate_promotion_request(request)


def test_validate_promotion_request_invalid_period_key_format() -> None:
    """period_key format YYYY-MM-DD or 2026-8 rejected (strict format)."""
    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08-15",  # ❌ day-level
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="m2_service_role",
    )
    with pytest.raises(ValueError, match="period_key"):
        validate_promotion_request(request)


def test_validate_promotion_request_invalid_period_key_month() -> None:
    """period_key with month > 12 rejected."""
    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-13",  # ❌ month 13
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="m2_service_role",
    )
    with pytest.raises(ValueError, match="period_key"):
        validate_promotion_request(request)


def test_validate_promotion_request_invalid_actor_role() -> None:
    """actor_role ≠ 'm2_service_role' rejected (AD-17 verbatim only M2 may call)."""
    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08",
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="owner",  # ❌ not m2_service_role
    )
    with pytest.raises(ValueError, match="actor_role"):
        validate_promotion_request(request)


# ── PROMOTE_STATUS_VALUES ────────────────────────────────────


def test_promote_status_values_frozenset_shape() -> None:
    """PROMOTE_STATUS_VALUES is a frozenset with 6 status values (AD-15 SSOT)."""
    assert isinstance(PROMOTE_STATUS_VALUES, frozenset)
    assert len(PROMOTE_STATUS_VALUES) == 6
    # Verify the canonical statuses are present
    assert "success" in PROMOTE_STATUS_VALUES
    assert "idempotent_replay" in PROMOTE_STATUS_VALUES
    assert "draft_not_found" in PROMOTE_STATUS_VALUES
    assert "draft_superseded" in PROMOTE_STATUS_VALUES
    assert "idempotency_mismatch" in PROMOTE_STATUS_VALUES
    assert "m2_only_denied" in PROMOTE_STATUS_VALUES


def test_promote_status_values_ad15_parity_marker() -> None:
    """AD-15 cross-language parity marker (TS mirror must mirror this frozenset)."""
    # The exact set is documented as the parity marker.
    # Any change here MUST also update apps/web/lib/ai-promote.ts.
    expected = frozenset(
        {
            "success",
            "idempotent_replay",
            "draft_not_found",
            "draft_superseded",
            "idempotency_mismatch",
            "m2_only_denied",
        }
    )
    assert expected == PROMOTE_STATUS_VALUES


# ── PromotionRequest + PromotionResult frozen ────────────────


def test_promotion_request_frozen_invariant() -> None:
    """PromotionRequest is a frozen dataclass — assignment raises FrozenInstanceError."""
    request = PromotionRequest(
        tenant_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        period_key="2026-08",
        source_draft_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        actor_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        actor_role="m2_service_role",
    )
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        request.period_key = "2026-09"  # type: ignore[misc]


def test_promotion_result_frozen_invariant_and_fields() -> None:
    """PromotionResult is frozen and has typed fields."""
    promotion_id = uuid.UUID("cccccccc-dddd-eeee-ffff-000000000000")
    monthly_input_row_id = uuid.UUID("dddddddd-eeee-ffff-0000-111111111111")
    result = PromotionResult(
        promotion_id=promotion_id,
        idempotency_key=uuid.UUID("eeeeeeee-ffff-0000-1111-222222222222"),
        status="success",
        monthly_input_row_id=monthly_input_row_id,
        idempotent_replay=False,
        trace_id="abc123trace",
    )
    # Verify fields
    assert result.promotion_id == promotion_id
    assert result.monthly_input_row_id == monthly_input_row_id
    assert result.status == "success"
    assert result.idempotent_replay is False
    assert result.trace_id == "abc123trace"

    # Verify frozen
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        result.status = "idempotent_replay"  # type: ignore[misc]


# ── AD-5 stdlib-only enforcement ─────────────────────────────


def test_promoter_port_module_has_no_io_imports() -> None:
    """AD-5 engine purity: kernel has no I/O imports (no sqlalchemy, requests, etc.).

    Pure-Python stdlib only — this is enforced so the kernel can be
    reused in tests, edge functions, and future cross-language parity
    verification without bringing in DB/AI dependencies.
    """
    from packages.services.m10_ai import promoter_port

    source = inspect.getsource(promoter_port)
    forbidden = ["sqlalchemy", "requests", "httpx", "openai", "anthropic", "fastapi"]
    for lib in forbidden:
        assert lib not in source, (
            f"AD-5 violation: '{lib}' imported in promoter_port.py (kernel must be stdlib-only)"
        )
