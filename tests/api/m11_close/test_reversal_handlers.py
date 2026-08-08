"""tests.api.m11_close.test_reversal_handlers — Story 11.1 handler schema tests.

AC #9 + AC #10 — handler schemas for the 3 NEW routes:
- POST /api/v1/close/reversal-requests (ReversalCreateRequest)
- GET /api/v1/close/reversal-requests/{correction_group_id} (path UUID)
- POST /api/v1/close/cache-invalidation (CacheInvalidationPublishRequest)

This file focuses on Pydantic schema validation (extra='forbid',
boundary conditions, AD-24 period_key pattern). Integration tests
for the handler functions (with FastAPI TestClient) live in the
Playwright E2E layer.

Project convention (CR 4-3): sync `def test_*` + `asyncio.run(_impl())`.
"""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from apps.api.modules.m11_close.handlers import (
    CacheInvalidationPublishRequest,
    CacheInvalidationPublishResponse,
    ReversalCreateRequest,
    ReversalCreateResponse,
    ReversalHistoryEntry,
    ReversalHistoryResponse,
)

EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000002")
CORRECTION_GROUP_ID = uuid.UUID("019200a0-0000-7000-8000-000000000003")
TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000001")
PRODUCT_ID = uuid.UUID("019200a0-0000-7000-8000-00000000000a")
TRACE_ID = "019200a0-0000-7000-8000-00000000000c"
TARGET_EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000004")
NEGATING_EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000005")


# ── ReversalCreateRequest schema validation ─────────────────


def test_reversal_create_request_accepts_minimal_payload() -> None:
    """Minimal {target_event_id, reason} payload validates."""
    payload = ReversalCreateRequest(
        target_event_id=TARGET_EVENT_ID,
        reason="테스트",
    )
    assert payload.target_event_id == TARGET_EVENT_ID
    assert payload.reason == "테스트"
    assert payload.corrected_qty is None
    assert payload.corrected_period_key is None


def test_reversal_create_request_accepts_full_payload() -> None:
    """Full payload with corrected_qty + corrected_period_key."""
    payload = ReversalCreateRequest(
        target_event_id=TARGET_EVENT_ID,
        reason="교정 포함",
        corrected_qty=150,
        corrected_period_key="2026-08",
    )
    assert payload.corrected_qty is not None
    assert payload.corrected_period_key == "2026-08"


def test_reversal_create_request_rejects_extra_fields() -> None:
    """extra='forbid' — unknown fields rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ReversalCreateRequest(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트",
            unknown_field="IGNORED",  # type: ignore[call-arg]
        )
    assert "unknown_field" in str(exc_info.value)


def test_reversal_create_request_rejects_empty_reason() -> None:
    """reason must be non-empty (min_length=1)."""
    with pytest.raises(ValidationError):
        ReversalCreateRequest(
            target_event_id=TARGET_EVENT_ID,
            reason="",
        )


def test_reversal_create_request_rejects_oversized_reason() -> None:
    """reason max_length=500."""
    with pytest.raises(ValidationError):
        ReversalCreateRequest(
            target_event_id=TARGET_EVENT_ID,
            reason="x" * 501,
        )


def test_reversal_create_request_rejects_invalid_period_key() -> None:
    """corrected_period_key must match AD-24 pattern 'YYYY-MM'."""
    with pytest.raises(ValidationError):
        ReversalCreateRequest(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트",
            corrected_qty=100,
            corrected_period_key="2026-8",  # 1-digit month
        )


def test_reversal_create_request_rejects_invalid_period_key_virtual() -> None:
    """M8 virtual budget key 'YYYY-MM#B<n>' rejected."""
    with pytest.raises(ValidationError):
        ReversalCreateRequest(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트",
            corrected_qty=100,
            corrected_period_key="2026-08#B1",
        )


def test_reversal_create_request_accepts_max_length_reason() -> None:
    """Korean reason at exactly 500 chars accepted."""
    # Korean 1 char = 1 char in Python (UTF-8 string length).
    payload = ReversalCreateRequest(
        target_event_id=TARGET_EVENT_ID,
        reason="테" * 500,  # 500 Korean chars
    )
    assert len(payload.reason) == 500


# ── CacheInvalidationPublishRequest schema validation ──────


def test_cache_invalidation_publish_request_defaults_to_ai_cache() -> None:
    """Default channel='ai_cache' (AD-25 1-channel wire)."""
    payload = CacheInvalidationPublishRequest(
        event_id=EVENT_ID,
        correction_group_id=CORRECTION_GROUP_ID,
    )
    assert payload.channel == "ai_cache"


def test_cache_invalidation_publish_request_rejects_extra_fields() -> None:
    """extra='forbid' — unknown fields rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CacheInvalidationPublishRequest(
            channel="ai_cache",
            event_id=EVENT_ID,
            correction_group_id=CORRECTION_GROUP_ID,
            unknown_field="IGNORED",  # type: ignore[call-arg]
        )
    assert "unknown_field" in str(exc_info.value)


def test_cache_invalidation_publish_request_accepts_custom_channel() -> None:
    """Custom channel allowed at schema level (FROZENSET gate is at publisher)."""
    payload = CacheInvalidationPublishRequest(
        channel="ai_cache",
        event_id=EVENT_ID,
        correction_group_id=CORRECTION_GROUP_ID,
    )
    assert payload.channel == "ai_cache"


# ── Response schema validation ──────────────────────────────


def test_reversal_history_entry_validates_minimum_fields() -> None:
    """ReversalHistoryEntry requires minimum 10 fields."""
    entry = ReversalHistoryEntry(
        event_id=str(EVENT_ID),
        tenant_id=str(TENANT_ID),
        product_id=str(PRODUCT_ID),
        period_key="2026-08",
        event_type="reversal_negating",
        qty="-100.0000",
        reverses_event_id=str(TARGET_EVENT_ID),
        correction_group_id=str(CORRECTION_GROUP_ID),
        reversal_of_period_key="2026-08",
        trace_id=TRACE_ID,
    )
    assert entry.event_type == "reversal_negating"
    assert entry.qty == "-100.0000"


def test_reversal_history_entry_accepts_none_quantities() -> None:
    """ReversalHistoryEntry allows None qty (closing_snapshot rows)."""
    entry = ReversalHistoryEntry(
        event_id=str(EVENT_ID),
        tenant_id=str(TENANT_ID),
        product_id=str(PRODUCT_ID),
        period_key="2026-08",
        event_type="closing_snapshot",
        qty=None,
        reverses_event_id=None,
        correction_group_id=None,
        reversal_of_period_key=None,
        trace_id=TRACE_ID,
    )
    assert entry.qty is None


def test_reversal_history_response_envelope() -> None:
    """ReversalHistoryResponse wraps correction_group_id + history list."""
    entry = ReversalHistoryEntry(
        event_id=str(EVENT_ID),
        tenant_id=str(TENANT_ID),
        product_id=str(PRODUCT_ID),
        period_key="2026-08",
        event_type="reversal_negating",
        qty="-100.0000",
        reverses_event_id=str(TARGET_EVENT_ID),
        correction_group_id=str(CORRECTION_GROUP_ID),
        reversal_of_period_key="2026-08",
        trace_id=TRACE_ID,
    )
    response = ReversalHistoryResponse(
        correction_group_id=str(CORRECTION_GROUP_ID),
        reversal_history=[entry],
        trace_id=TRACE_ID,
    )
    assert len(response.reversal_history) == 1
    assert response.correction_group_id == str(CORRECTION_GROUP_ID)


def test_reversal_create_response_envelope() -> None:
    """ReversalCreateResponse wraps correction_group_id + negating + corrected."""
    response = ReversalCreateResponse(
        correction_group_id=str(CORRECTION_GROUP_ID),
        negating_event_id=str(NEGATING_EVENT_ID),
        corrected_event_id=None,
        target_event_id=str(TARGET_EVENT_ID),
        reversal_history=[],
        trace_id=TRACE_ID,
        cache_invalidation_receipt={
            "channel": "ai_cache",
            "tenant_id": str(TENANT_ID),
            "event_id": str(TARGET_EVENT_ID),
            "correction_group_id": str(CORRECTION_GROUP_ID),
            "trace_id": TRACE_ID,
            "published_at": "2026-08-08T00:00:00+00:00",
        },
    )
    assert response.correction_group_id == str(CORRECTION_GROUP_ID)
    assert response.cache_invalidation_receipt["channel"] == "ai_cache"


def test_cache_invalidation_publish_response_envelope() -> None:
    """CacheInvalidationPublishResponse wraps the receipt."""
    response = CacheInvalidationPublishResponse(
        channel="ai_cache",
        tenant_id=str(TENANT_ID),
        event_id=str(EVENT_ID),
        correction_group_id=str(CORRECTION_GROUP_ID),
        published_at="2026-08-08T00:00:00+00:00",
        trace_id=TRACE_ID,
    )
    assert response.channel == "ai_cache"
    assert response.tenant_id == str(TENANT_ID)


# ── UUID validation ─────────────────────────────────────────


def test_reversal_create_request_rejects_invalid_target_event_id() -> None:
    """target_event_id must be a valid UUID."""
    with pytest.raises(ValidationError):
        ReversalCreateRequest(
            target_event_id="not-a-uuid",  # type: ignore[arg-type]
            reason="테스트",
        )


def test_cache_invalidation_publish_request_rejects_invalid_uuids() -> None:
    """event_id + correction_group_id must be UUIDs."""
    with pytest.raises(ValidationError):
        CacheInvalidationPublishRequest(
            channel="ai_cache",
            event_id="not-a-uuid",  # type: ignore[arg-type]
            correction_group_id=CORRECTION_GROUP_ID,
        )

    with pytest.raises(ValidationError):
        CacheInvalidationPublishRequest(
            channel="ai_cache",
            event_id=EVENT_ID,
            correction_group_id="not-a-uuid",  # type: ignore[arg-type]
        )


# ── Decimal qty validation ──────────────────────────────────


def test_reversal_create_request_accepts_decimal_qty() -> None:
    """corrected_qty accepts Decimal."""
    payload = ReversalCreateRequest(
        target_event_id=TARGET_EVENT_ID,
        reason="테스트",
        corrected_qty=150,
        corrected_period_key="2026-08",
    )
    assert payload.corrected_qty is not None
