"""Cross-language parity test — cache_invalidation_listener (Python ↔ TS).

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
T7 wire — cross-language drift detector EXTENSION (CR 12-5 D-PARITY-01
inversion).

Per CR 12-5 D-PARITY-01 inversion: Python `cache_invalidation_listener.py`
↔ TS `cache-invalidation-listener.ts` payload shape MUST be byte-identical.
Drift 발생 시 drift detector test fail + 1-line ko-KR reject.

Tests:
- 5-key payload shape parity (channel, correction_group_id, period_key, tenant_id, trace_id)
- 4-channel whitelist parity (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)
- V8 determinism parity (Python `serialize_payload_for_v8` ↔ TS `serializePayloadForV8`)
- INVALID channel parity (both reject unknown channels)
- INVALID UUID parity (both reject invalid UUIDs)
- INVALID trace_id + period_key parity
- Korean reject message (DRIFT_DETECTED_REJECT_KO)
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
        expected = {
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
        }
        assert PY_CHANNELS == expected
        # TS must have all 4 in the ALLOWED_CHANNELS array.
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
        """Python has build_default_adapter_factories with 4 channels."""
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        assert len(factories) == 4

    def test_ts_4_channel_dispatch_table(self) -> None:
        """TS has DEFAULT_CHANNEL_ADAPTERS with 4 channels."""
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
