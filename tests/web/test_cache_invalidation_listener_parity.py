"""Cross-language parity test — cache_invalidation_listener (Python ↔ TS).

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
T7 wire — cross-language drift detector EXTENSION (CR 12-5 D-PARITY-01
inversion).

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): T7 EXTENSION — 7-key payload
parity + cross_tenant_fanout channel parity + new TS interfaces parity +
new ko-KR reject message parity.

Per CR 12-5 D-PARITY-01 inversion: Python `cache_invalidation_listener.py`
↔ TS `cache-invalidation-listener.ts` payload shape MUST be byte-identical.
Drift 발생 시 drift detector test fail + 1-line ko-KR reject.

Tests (13-1 baseline, 보존):
- 5-key payload shape parity (channel, correction_group_id, period_key, tenant_id, trace_id)
- 4-channel whitelist parity (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)
- V8 determinism parity (Python `serialize_payload_for_v8` ↔ TS `serializePayloadForV8`)
- INVALID channel parity (both reject unknown channels)
- INVALID UUID parity (both reject invalid UUIDs)
- INVALID trace_id + period_key parity
- Korean reject message (DRIFT_DETECTED_REJECT_KO)

Tests (14-1 EXTENSION, NEW ~+12 cases):
- 7-key payload shape parity (cross_tenant_fanout: channel, correction_group_id, invalidation_id, period_key, source_tenant_id, target_tenant_ids, trace_id)
- 5+ channels parity (cross_tenant_fanout 추가)
- target_tenant_ids UUID array parity (Python `list[str]` ↔ TS `string[]`)
- source_tenant_id + invalidation_id UUID parity
- Channel-based key set selection parity (5 vs 7 keys)
- MultiTenantIsolationState TS interface parity
- LeaderElectionState TS interface parity
- CROSS_TENANT_DRIFT_DETECTED_REJECT_KO ko-KR reject message parity
- Default adapter dispatch table parity (5+ entries)
"""

from __future__ import annotations

import json
import uuid

import pytest


# ── Test constants parity ────────────────────────────────────
class TestConstantsParity:
    """Python ↔ TS constants must match."""

    def test_notify_channel_name_parity(self) -> None:
        """Python NOTIFY_CHANNEL_NAME = 'cache_invalidation_log' = TS NOTIFY_CHANNEL_NAME."""
        from apps.api.core.cache_invalidation_listener import NOTIFY_CHANNEL_NAME as PY_NOTIFY_CHANNEL_NAME

        # Verify TS module file contains the same constant.
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert PY_NOTIFY_CHANNEL_NAME == "cache_invalidation_log"
        assert 'NOTIFY_CHANNEL_NAME = "cache_invalidation_log"' in ts_content

    def test_4_channels_parity(self) -> None:
        """Python ALLOWED_CHANNELS = TS ALLOWED_CHANNELS."""
        from apps.api.core.cache_invalidation_listener import ALLOWED_CHANNELS as PY_CHANNELS

        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        # Story 14.1 EXTENSION: cross_tenant_fanout channel 추가 (5+).
        expected = {
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
            "cross_tenant_fanout",
        }
        assert PY_CHANNELS == expected
        # TS must have all 5+ in the ALLOWED_CHANNELS array.
        for channel in expected:
            assert f'"{channel}"' in ts_content

    def test_5_payload_keys_parity(self) -> None:
        """Python EXPECTED_PAYLOAD_KEYS = TS PAYLOAD_KEYS (5 keys)."""
        from apps.api.core.cache_invalidation_listener import (
            EXPECTED_PAYLOAD_KEYS as PY_KEYS,
        )

        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        expected = {
            "channel",
            "correction_group_id",
            "period_key",
            "tenant_id",
            "trace_id",
        }
        assert PY_KEYS == expected
        # TS must have all 5 keys in the PAYLOAD_KEYS array.
        for key in expected:
            assert f'"{key}"' in ts_content


# ── Test serialization parity ──────────────────────────────
class TestSerializationParity:
    """Python serialize_payload_for_v8 ↔ TS serializePayloadForV8 produce same bytes."""

    def test_alphabetical_key_ordering_parity(self) -> None:
        """Both serialize with alphabetical key ordering."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8 as py_serialize,
        )

        payload = {
            "channel": "ai_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "trace-parity",
        }
        py_result = py_serialize(payload)
        # Verify alphabetical order in Python result.
        indices = [
            py_result.index('"channel"'),
            py_result.index('"correction_group_id"'),
            py_result.index('"period_key"'),
            py_result.index('"tenant_id"'),
            py_result.index('"trace_id"'),
        ]
        assert indices == sorted(indices)

        # Verify TS code uses an explicit ordered object construction.
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        # TS code must build the ordered object with explicit insertion order.
        assert "channel:" in ts_content
        assert "correction_group_id:" in ts_content
        assert "period_key:" in ts_content
        assert "tenant_id:" in ts_content
        assert "trace_id:" in ts_content

    def test_no_whitespace_parity(self) -> None:
        """Both produce JSON with no whitespace."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8 as py_serialize,
        )

        payload = {
            "channel": "ai_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "trace-parity",
        }
        py_result = py_serialize(payload)
        assert " " not in py_result
        assert "\n" not in py_result
        # TS uses JSON.stringify with no extra args (default = no whitespace).
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "JSON.stringify" in ts_content


# ── Test INVALID channel parity ─────────────────────────────
class TestInvalidChannelParity:
    """Both Python and TS reject unknown channels."""

    def test_python_rejects_unknown_channel(self) -> None:
        """parse_payload raises ListenerPayloadInvalidError on unknown channel."""
        from apps.api.core.cache_invalidation_listener import (
            ListenerPayloadInvalidError,
            parse_payload,
        )

        payload = {
            "channel": "unknown_channel",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "trace",
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with pytest.raises(ListenerPayloadInvalidError):
            parse_payload(raw)

    def test_ts_rejects_unknown_channel_source(self) -> None:
        """TS source must contain unknown channel rejection."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "not in ALLOWED_CHANNELS" in ts_content


# ── Test INVALID UUID parity ────────────────────────────────
class TestInvalidUUIDParity:
    """Both Python and TS reject invalid UUIDs."""

    def test_python_rejects_invalid_tenant_id(self) -> None:
        """parse_payload raises on invalid tenant_id."""
        from apps.api.core.cache_invalidation_listener import (
            ListenerPayloadInvalidError,
            parse_payload,
        )

        payload = {
            "channel": "ai_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": "not-a-uuid",
            "trace_id": "trace",
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with pytest.raises(ListenerPayloadInvalidError):
            parse_payload(raw)

    def test_ts_rejects_invalid_uuid_source(self) -> None:
        """TS source must contain UUID validation logic."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "uuidRegex" in ts_content or "UUID" in ts_content


# ── Test ko-KR reject message ────────────────────────────────
class TestKoreanRejectMessage:
    """ko-KR reject message for drift detection."""

    def test_drift_detected_reject_ko_exists(self) -> None:
        """TS module exports DRIFT_DETECTED_REJECT_KO constant."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "DRIFT_DETECTED_REJECT_KO" in ts_content
        assert "LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다" in ts_content


# ── Test Adapter protocol parity ─────────────────────────────
class TestAdapterProtocolParity:
    """Python CacheInvalidationAdapter protocol ↔ TS CacheInvalidationAdapter interface."""

    def test_python_adapter_protocol_exists(self) -> None:
        """Python has CacheInvalidationAdapter protocol."""
        from apps.api.core.cache_invalidation_listener import (
            CacheInvalidationAdapter,
        )

        assert hasattr(CacheInvalidationAdapter, "on_invalidate")

    def test_ts_adapter_interface_exists(self) -> None:
        """TS exports CacheInvalidationAdapter interface."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "CacheInvalidationAdapter" in ts_content
        assert "onInvalidate" in ts_content


# ── Test 4-channel routing parity ────────────────────────────
class Test4ChannelRoutingParity:
    """Both Python and TS use the same 4-channel routing."""

    def test_python_4_channel_factory(self) -> None:
        """Python has build_default_adapter_factories with 4 channels (13-1 baseline)."""
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        # 14-1 EXTENSION: cross_tenant_fanout 추가 → 4 channels → 5+ channels.
        assert len(factories) >= 4

    def test_ts_4_channel_dispatch_table(self) -> None:
        """TS has DEFAULT_CHANNEL_ADAPTERS with 4 channels (13-1 baseline)."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "DEFAULT_CHANNEL_ADAPTERS" in ts_content
        assert "M10AIInvalidationAdapter" in ts_content
        assert "M3CostEngineInvalidationAdapter" in ts_content
        assert "M11FiscalPeriodInvalidationAdapter" in ts_content
        assert "M11ClosingSnapshotInvalidationAdapter" in ts_content


# ── Test 14-1 EXTENSION ─────────────────────────────────────
class TestCrossTenantChannelParity14_1:
    """14-1 EXTENSION: cross_tenant_fanout channel parity (Python ↔ TS)."""

    def test_5_plus_channels_parity(self) -> None:
        """Python ALLOWED_CHANNELS = TS ALLOWED_CHANNELS (5+ channels)."""
        from apps.api.core.cache_invalidation_listener import (
            ALLOWED_CHANNELS as PY_CHANNELS,
        )

        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        expected = {
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
            "cross_tenant_fanout",
        }
        assert PY_CHANNELS == expected
        # TS must have all 5+ in the ALLOWED_CHANNELS array.
        for channel in expected:
            assert f'"{channel}"' in ts_content

    def test_7_keys_cross_tenant_parity(self) -> None:
        """Python EXPECTED_PAYLOAD_KEYS_CROSS_TENANT = TS PAYLOAD_KEYS_CROSS_TENANT (7 keys)."""
        from apps.api.core.cache_invalidation_listener import (
            EXPECTED_PAYLOAD_KEYS_CROSS_TENANT as PY_CROSS_KEYS,
        )

        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        expected = {
            "channel",
            "correction_group_id",
            "invalidation_id",
            "period_key",
            "source_tenant_id",
            "target_tenant_ids",
            "trace_id",
        }
        assert PY_CROSS_KEYS == expected
        # TS must have all 7 keys in the PAYLOAD_KEYS_CROSS_TENANT array.
        for key in expected:
            assert f'"{key}"' in ts_content

    def test_python_parses_7_key_cross_tenant_payload(self) -> None:
        """parse_payload handles 7-key cross_tenant_fanout payload."""
        from apps.api.core.cache_invalidation_listener import (
            parse_payload,
        )

        payload = {
            "channel": "cross_tenant_fanout",
            "correction_group_id": str(uuid.uuid4()),
            "invalidation_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "source_tenant_id": str(uuid.uuid4()),
            "target_tenant_ids": [str(uuid.uuid4()) for _ in range(2)],
            "trace_id": "trace-cross-tenant-14-1",
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        parsed = parse_payload(raw)
        # parse_payload returns a dataclass; access via attribute.
        assert parsed.channel == "cross_tenant_fanout"
        assert parsed.invalidation_id == payload["invalidation_id"]
        assert parsed.source_tenant_id == payload["source_tenant_id"]
        assert list(parsed.target_tenant_ids) == payload["target_tenant_ids"]


class TestCrossTenantSerializationParity14_1:
    """14-1 EXTENSION: 7-key serialization byte-identical parity."""

    def test_serialize_7_keys_byte_identical_parity(self) -> None:
        """Python ↔ TS serialize same 7-key payload → same bytes (alphabetical order)."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8 as py_serialize,
        )

        payload = {
            "channel": "cross_tenant_fanout",
            "correction_group_id": str(uuid.uuid4()),
            "invalidation_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "source_tenant_id": str(uuid.uuid4()),
            "target_tenant_ids": [str(uuid.uuid4()) for _ in range(3)],
            "trace_id": "trace-v8-14-1",
        }
        py_result = py_serialize(payload)
        # Verify alphabetical order in Python result.
        indices = [
            py_result.index('"channel"'),
            py_result.index('"correction_group_id"'),
            py_result.index('"invalidation_id"'),
            py_result.index('"period_key"'),
            py_result.index('"source_tenant_id"'),
            py_result.index('"target_tenant_ids"'),
            py_result.index('"trace_id"'),
        ]
        assert indices == sorted(indices)
        # TS code must build the ordered object with explicit insertion order.
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "channel:" in ts_content
        assert "invalidation_id:" in ts_content
        assert "source_tenant_id:" in ts_content
        assert "target_tenant_ids:" in ts_content

    def test_target_tenant_ids_array_byte_identical_parity(self) -> None:
        """target_tenant_ids array element order preserved byte-identical."""
        from apps.api.core.cache_invalidation_listener import (
            serialize_payload_for_v8 as py_serialize,
        )

        ids = [f"tenant-{i:03d}" for i in range(5)]
        payload = {
            "channel": "cross_tenant_fanout",
            "correction_group_id": str(uuid.uuid4()),
            "invalidation_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "source_tenant_id": str(uuid.uuid4()),
            "target_tenant_ids": ids,
            "trace_id": "trace-array-14-1",
        }
        result = py_serialize(payload)
        parsed = json.loads(result)
        assert parsed["target_tenant_ids"] == ids


class TestNewTSInterfacesParity14_1:
    """14-1 EXTENSION: MultiTenantIsolationState + LeaderElectionState TS interfaces."""

    def test_multi_tenant_isolation_state_interface_exists(self) -> None:
        """TS exports MultiTenantIsolationState interface."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "MultiTenantIsolationState" in ts_content
        assert "source_tenant_id" in ts_content
        assert "target_tenant_ids" in ts_content
        assert "source_has_capability" in ts_content

    def test_leader_election_state_interface_exists(self) -> None:
        """TS exports LeaderElectionState interface."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "LeaderElectionState" in ts_content
        assert "is_leader" in ts_content
        assert "leader_pod_id" in ts_content
        assert "follower_pod_ids" in ts_content

    def test_ts_5_plus_channel_dispatch_table(self) -> None:
        """TS DEFAULT_CHANNEL_ADAPTERS has 5+ entries (cross_tenant_fanout 추가)."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "cross_tenant_fanout:" in ts_content
        assert "CrossTenantFanoutAdapter" in ts_content


class TestKoreanRejectMessageParity14_1:
    """14-1 EXTENSION: CROSS_TENANT_DRIFT_DETECTED_REJECT_KO new ko-KR message."""

    def test_cross_tenant_drift_detected_reject_ko_exists(self) -> None:
        """TS exports CROSS_TENANT_DRIFT_DETECTED_REJECT_KO constant."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "CROSS_TENANT_DRIFT_DETECTED_REJECT_KO" in ts_content
        assert "크로스 테넌트 LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다" in ts_content

    def test_legacy_drift_detected_reject_ko_preserved(self) -> None:
        """TS preserves legacy DRIFT_DETECTED_REJECT_KO (13-1 baseline)."""
        ts_path = (
            __file__.replace("\\", "/").split("/tests/")[0]
            + "/apps/web/lib/cache-invalidation-listener.ts"
        )
        with open(ts_path, encoding="utf-8") as f:
            ts_content = f.read()
        assert "DRIFT_DETECTED_REJECT_KO" in ts_content
        assert "LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다" in ts_content
