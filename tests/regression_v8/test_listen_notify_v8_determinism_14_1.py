"""V8 regression test 14.1 EXTENSION — cross_tenant_fanout payload byte-identical determinism.

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): T6 EXTENSION.

CR 4-4 + F13.3 + F14.3 verbatim: cross_tenant_fanout payload JSON MUST
be byte-identical for the same input across reruns. The 7-key
alphabetical ordering (channel, correction_group_id, invalidation_id,
period_key, source_tenant_id, target_tenant_ids, trace_id) is the
V8 determinism contract.

Tests:
- 7-key alphabetical ordering (channel, correction_group_id,
  invalidation_id, period_key, source_tenant_id, target_tenant_ids,
  trace_id)
- target_tenant_ids array 결정적 직렬화 (JSON array 순서 보존)
- byte-identical across reruns
- 5+ channels routing payload shape 결정적
"""

from __future__ import annotations

import json
import uuid


# ── Test helpers ─────────────────────────────────────────────
def _make_cross_tenant_payload(
    *,
    source_tenant_id: str | None = None,
    target_tenant_ids: list[str] | None = None,
    invalidation_id: str | None = None,
    correction_group_id: str | None = None,
    period_key: str = "2026-08",
    trace_id: str = "trace-v8-determinism-14-1",
) -> dict[str, object]:
    """Build a valid 7-key payload for cross_tenant_fanout channel."""
    return {
        "channel": "cross_tenant_fanout",
        "correction_group_id": (
            correction_group_id or str(uuid.uuid4())
        ),
        "invalidation_id": invalidation_id or str(uuid.uuid4()),
        "period_key": period_key,
        "source_tenant_id": source_tenant_id or str(uuid.uuid4()),
        "target_tenant_ids": target_tenant_ids
        or [str(uuid.uuid4()) for _ in range(3)],
        "trace_id": trace_id,
    }


# ── Test V8 determinism (cross_tenant_fanout) ────────────────
class TestV8DeterminismCrossTenantFanout:
    """cross_tenant_fanout payload V8 determinism (7 keys alphabetical)."""

    def test_serialize_7_keys_alphabetical_ordering(self) -> None:
        """JSON keys output in alphabetical order (7 keys)."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        payload = _make_cross_tenant_payload()
        result = serialize_payload_for_v8(payload)
        # Verify alphabetical order.
        idx_channel = result.index('"channel"')
        idx_corr = result.index('"correction_group_id"')
        idx_inv = result.index('"invalidation_id"')
        idx_period = result.index('"period_key"')
        idx_source = result.index('"source_tenant_id"')
        idx_targets = result.index('"target_tenant_ids"')
        idx_trace = result.index('"trace_id"')
        assert (
            idx_channel
            < idx_corr
            < idx_inv
            < idx_period
            < idx_source
            < idx_targets
            < idx_trace
        )

    def test_serialize_no_whitespace(self) -> None:
        """No spaces, no newlines in serialized JSON."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        payload = _make_cross_tenant_payload()
        result = serialize_payload_for_v8(payload)
        assert " " not in result
        assert "\n" not in result
        assert "\t" not in result

    def test_serialize_uses_compact_separator(self) -> None:
        """Separators = (',', ':') — no space after comma or colon."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        payload = _make_cross_tenant_payload()
        result = serialize_payload_for_v8(payload)
        assert ": " not in result
        assert ", " not in result

    def test_serialize_byte_identical_across_reruns(self) -> None:
        """Same input → same output bytes (multiple iterations)."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        payload = _make_cross_tenant_payload()
        results = [serialize_payload_for_v8(payload) for _ in range(10)]
        # All iterations produce byte-identical output.
        for i in range(1, len(results)):
            assert results[i] == results[0]

    def test_target_tenant_ids_array_order_preserved(self) -> None:
        """target_tenant_ids array element order preserved (V8 determinism)."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        ids = [f"tenant-{i:03d}" for i in range(5)]
        payload = _make_cross_tenant_payload(
            target_tenant_ids=ids,
        )
        result = serialize_payload_for_v8(payload)
        parsed = json.loads(result)
        assert parsed["target_tenant_ids"] == ids

    def test_serialize_canonical_form_roundtrip(self) -> None:
        """Roundtrip serialize → parse → serialize produces identical bytes."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        payload = _make_cross_tenant_payload()
        first = serialize_payload_for_v8(payload)
        # Parse and re-serialize.
        reparsed = json.loads(first)
        second = serialize_payload_for_v8(reparsed)
        assert first == second

    def test_target_tenant_ids_canonical_for_uuid(self) -> None:
        """UUID strings in target_tenant_ids are preserved verbatim."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        uuids = [str(uuid.uuid4()) for _ in range(4)]
        payload = _make_cross_tenant_payload(
            target_tenant_ids=uuids,
        )
        result = serialize_payload_for_v8(payload)
        parsed = json.loads(result)
        assert parsed["target_tenant_ids"] == uuids

    def test_alphabetical_key_order_matches_payload(self) -> None:
        """Alphabetical key order matches expected 7-key order."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8,
        )

        payload = _make_cross_tenant_payload()
        result = serialize_payload_for_v8(payload)
        keys_in_order = list(json.loads(result).keys())
        expected = sorted(keys_in_order)
        assert keys_in_order == expected


class TestV8DeterminismAllChannels:
    """All 5+ channels payload shape 결정적 (V8 determinism contract)."""

    def test_5_channels_parseable(self) -> None:
        """All 5 channels (4 보존 + cross_tenant_fanout 추가) parseable."""
        from apps.api.core.cache_invalidation_listener import parse_payload

        for channel in (
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
            "cross_tenant_fanout",
        ):
            if channel == "cross_tenant_fanout":
                payload = _make_cross_tenant_payload()
            else:
                payload = {
                    "channel": channel,
                    "correction_group_id": str(uuid.uuid4()),
                    "period_key": "2026-08",
                    "tenant_id": str(uuid.uuid4()),
                    "trace_id": f"trace-{channel}",
                }
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            parsed = parse_payload(raw)
            assert parsed.channel == channel
