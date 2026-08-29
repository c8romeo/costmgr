/**
 * apps/web/lib/cache-invalidation-listener.ts — Story 13.1 + 14.1
 * (LISTEN/NOTIFY Consume Trigger EXTENSION + Cross-Tenant Fan-Out +
 * Multi-Process Coordination) TS mirror.
 *
 * Sprint 13-1 (cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속
 * 정직 회복) — T7 wire (cross-language drift detector EXTENSION).
 *
 * Sprint 14-1 (cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속
 * 정직 회복) — T7 wire EXTENSION (cross_tenant_fanout channel + 7-key
 * payload + multi-tenant isolation + leader election state).
 *
 * AD-15 cross-language parity SSOT: this file mirrors the Python schema
 * (`apps/api/core/cache_invalidation_listener.py`) verbatim. Per CR 12-5
 * D-PARITY-01 inversion, the payload shape MUST match between Python and
 * TS — drift detector verifies this byte-for-byte.
 *
 * Payload shape (5 keys for 4 channels, alphabetical order — V8 determinism):
 *   {
 *     "channel":              "ai_cache",
 *     "correction_group_id":  "uuid-string",
 *     "period_key":           "YYYY-MM",
 *     "tenant_id":            "uuid-string",
 *     "trace_id":             "uuid-string"
 *   }
 *
 * Payload shape (7 keys for cross_tenant_fanout channel — V8 determinism EXTENSION):
 *   {
 *     "channel":              "cross_tenant_fanout",
 *     "correction_group_id":  "uuid-string",
 *     "invalidation_id":      "uuid-string",
 *     "period_key":           "YYYY-MM",
 *     "source_tenant_id":     "uuid-string",
 *     "target_tenant_ids":    ["uuid-string-1", "uuid-string-2", ...],
 *     "trace_id":             "uuid-string"
 *   }
 *
 * 5+ channels (AD-25 verbatim EXTENSION):
 *   - "ai_cache"               — M10 AI cache invalidation
 *   - "cost_engine_cache"      — M3 cost engine calculation result cache
 *   - "fiscal_period_cache"    — M11 fiscal_periods + fiscal_period_snapshots
 *   - "closing_snapshot_cache" — M11 closing_snapshot + ledger closing event
 *   - "cross_tenant_fanout"    — cross-tenant invalidation fan-out (14-1 NEW)
 *
 * Drift detection: if the Python ↔ TS payload shape diverges, the
 * `tests/web/test_cache_invalidation_listener_parity.py` test fails
 * with a 1-line ko-KR reject message.
 */

// ── SSOT mirror — Python `apps.api.core.cache_invalidation_listener` ──

/** 5+ channel whitelist (AD-25 verbatim EXTENSION, mirrors `ALLOWED_CHANNELS` in Python). */
export const ALLOWED_CHANNELS = [
  "ai_cache",
  "cost_engine_cache",
  "fiscal_period_cache",
  "closing_snapshot_cache",
  "cross_tenant_fanout",
] as const;

export type CacheInvalidationChannel =
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  (typeof ALLOWED_CHANNELS)[number];

/** NOTIFY channel name (mirrors `NOTIFY_CHANNEL_NAME` in Python). */
export const NOTIFY_CHANNEL_NAME = "cache_invalidation_log";

/** Payload keys (5 keys for 4 channels, alphabetical order — V8 determinism contract). */
export const PAYLOAD_KEYS = [
  "channel",
  "correction_group_id",
  "period_key",
  "tenant_id",
  "trace_id",
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type CacheInvalidationPayloadKey = (typeof PAYLOAD_KEYS)[number];

/**
 * Payload keys (7 keys for cross_tenant_fanout, alphabetical order — V8 determinism contract).
 *
 * Story 14.1 EXTENSION. The 7 keys are typed as required — V8 determinism
 * enforces exact shape. Mirrors `EXPECTED_PAYLOAD_KEYS_CROSS_TENANT` in Python.
 */
export const PAYLOAD_KEYS_CROSS_TENANT = [
  "channel",
  "correction_group_id",
  "invalidation_id",
  "period_key",
  "source_tenant_id",
  "target_tenant_ids",
  "trace_id",
] as const;

export type CacheInvalidationPayloadKeyCrossTenant =
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  (typeof PAYLOAD_KEYS_CROSS_TENANT)[number];

/**
 * Discriminated union payload (mirrors `CacheInvalidationPayload` in Python).
 *
 * The 5/7 keys are typed as required (V8 determinism enforces exact shape).
 * `channel` is the discriminator — TypeScript narrows the type based on
 * the channel value:
 * - 5 keys for the 4 standard channels
 * - 7 keys for `cross_tenant_fanout` (Story 14.1 EXTENSION)
 */
export type CacheInvalidationPayload = {
  channel: CacheInvalidationChannel;
  correction_group_id: string;
  period_key: string;
  trace_id: string;
} & (
  | {
      // 5-key shape (4 standard channels).
      channel: Exclude<
        CacheInvalidationChannel,
        "cross_tenant_fanout"
      >;
      tenant_id: string;
    }
  | {
      // 7-key shape (cross_tenant_fanout, Story 14.1 EXTENSION).
      channel: "cross_tenant_fanout";
      invalidation_id: string;
      source_tenant_id: string;
      target_tenant_ids: string[];
    }
);

/** Serde error thrown when payload validation fails. */
export class ListenerPayloadInvalidError extends Error {
  constructor(
    public readonly reason: string,
    public readonly payload: unknown,
  ) {
    super(`listener payload invalid: ${reason} (payload=${JSON.stringify(payload)})`);
    this.name = "ListenerPayloadInvalidError";
  }
}

/**
 * Serialize payload for V8 byte-identical determinism.
 *
 * Mirrors `serialize_payload_for_v8` in Python. Uses `JSON.stringify`
 * with sorted keys (alphabetical order) and no whitespace.
 *
 * Story 14.1 EXTENSION: 7-key payload for `cross_tenant_fanout` channel.
 */
export function serializePayloadForV8(
  payload: CacheInvalidationPayload,
): string {
  if (payload.channel === "cross_tenant_fanout") {
    // 7-key shape, alphabetical order.
    const ordered: Record<
      CacheInvalidationPayloadKeyCrossTenant,
      string | string[]
    > = {
      channel: payload.channel,
      correction_group_id: payload.correction_group_id,
      invalidation_id: payload.invalidation_id,
      period_key: payload.period_key,
      source_tenant_id: payload.source_tenant_id,
      target_tenant_ids: payload.target_tenant_ids,
      trace_id: payload.trace_id,
    };
    return JSON.stringify(ordered);
  }
  // 5-key shape, alphabetical order.
  const ordered: Record<CacheInvalidationPayloadKey, string> = {
    channel: payload.channel,
    correction_group_id: payload.correction_group_id,
    period_key: payload.period_key,
    tenant_id: (payload as Extract<
      CacheInvalidationPayload,
      { tenant_id: string }
    >).tenant_id,
    trace_id: payload.trace_id,
  };
  return JSON.stringify(ordered);
}

/**
 * Parse a NOTIFY payload string into a typed CacheInvalidationPayload.
 *
 * Mirrors `parse_payload` in Python. Validates:
 * - 5 keys for 4 standard channels OR 7 keys for cross_tenant_fanout
 * - channel is in ALLOWED_CHANNELS
 * - tenant_id + correction_group_id (5-key) OR source_tenant_id +
 *   correction_group_id + invalidation_id (7-key) are valid UUIDs
 * - target_tenant_ids (7-key) is an array of valid UUID strings
 * - trace_id + period_key are non-empty strings
 *
 * Throws `ListenerPayloadInvalidError` on any validation failure.
 *
 * Story 14.1 EXTENSION: 7-key cross_tenant_fanout payload handling.
 */
export function parseCacheInvalidationPayload(
  raw: string,
): CacheInvalidationPayload {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    throw new ListenerPayloadInvalidError(
      `JSON parse failed: ${(e as Error).message}`,
      raw,
    );
  }

  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new ListenerPayloadInvalidError(
      "payload is not a JSON object",
      parsed,
    );
  }

  const obj = parsed as Record<string, unknown>;

  // Validate channel FIRST (decides which key set to validate).
  const channel = obj.channel;
  if (typeof channel !== "string") {
    throw new ListenerPayloadInvalidError(
      `channel must be str, got ${typeof channel}`,
      parsed,
    );
  }
  if (!ALLOWED_CHANNELS.includes(channel as CacheInvalidationChannel)) {
    throw new ListenerPayloadInvalidError(
      `channel ${JSON.stringify(channel)} not in ALLOWED_CHANNELS`,
      parsed,
    );
  }

  // Validate key set based on channel.
  const actualKeys = Object.keys(obj).sort();
  let expectedKeys: string[];
  if (channel === "cross_tenant_fanout") {
    expectedKeys = [...PAYLOAD_KEYS_CROSS_TENANT].sort();
  } else {
    expectedKeys = [...PAYLOAD_KEYS].sort();
  }
  if (
    actualKeys.length !== expectedKeys.length ||
    !actualKeys.every((k, i) => k === expectedKeys[i])
  ) {
    throw new ListenerPayloadInvalidError(
      `payload keys mismatch for channel ${JSON.stringify(channel)}: expected ${JSON.stringify(expectedKeys)}, got ${JSON.stringify(actualKeys)}`,
      parsed,
    );
  }

  // Validate UUID fields.
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  // Validate common fields.
  if (typeof obj.correction_group_id !== "string") {
    throw new ListenerPayloadInvalidError(
      `correction_group_id must be str, got ${typeof obj.correction_group_id}`,
      parsed,
    );
  }
  if (
    obj.correction_group_id !== "" &&
    !uuidRegex.test(obj.correction_group_id)
  ) {
    throw new ListenerPayloadInvalidError(
      `correction_group_id is not a valid UUID: ${obj.correction_group_id}`,
      parsed,
    );
  }
  if (typeof obj.trace_id !== "string" || obj.trace_id === "") {
    throw new ListenerPayloadInvalidError(
      "trace_id must be non-empty str",
      parsed,
    );
  }
  if (typeof obj.period_key !== "string" || obj.period_key === "") {
    throw new ListenerPayloadInvalidError(
      "period_key must be non-empty str",
      parsed,
    );
  }

  if (channel === "cross_tenant_fanout") {
    // 7-key shape: validate source_tenant_id + invalidation_id + target_tenant_ids.
    if (
      typeof obj.source_tenant_id !== "string" ||
      !uuidRegex.test(obj.source_tenant_id)
    ) {
      throw new ListenerPayloadInvalidError(
        `source_tenant_id is not a valid UUID: ${obj.source_tenant_id}`,
        parsed,
      );
    }
    if (
      typeof obj.invalidation_id !== "string" ||
      obj.invalidation_id === ""
    ) {
      throw new ListenerPayloadInvalidError(
        `invalidation_id must be non-empty str, got ${typeof obj.invalidation_id}`,
        parsed,
      );
    }
    if (!Array.isArray(obj.target_tenant_ids)) {
      throw new ListenerPayloadInvalidError(
        `target_tenant_ids must be array, got ${typeof obj.target_tenant_ids}`,
        parsed,
      );
    }
    const targetTenantIds = obj.target_tenant_ids as unknown[];
    for (let i = 0; i < targetTenantIds.length; i++) {
      const tid = targetTenantIds[i];
      if (typeof tid !== "string" || !uuidRegex.test(tid)) {
        throw new ListenerPayloadInvalidError(
          `target_tenant_ids[${i}] is not a valid UUID: ${tid}`,
          parsed,
        );
      }
    }
    return {
      channel: "cross_tenant_fanout",
      correction_group_id: obj.correction_group_id as string,
      invalidation_id: obj.invalidation_id as string,
      period_key: obj.period_key as string,
      source_tenant_id: obj.source_tenant_id as string,
      target_tenant_ids: targetTenantIds as string[],
      trace_id: obj.trace_id as string,
    };
  }

  // 5-key shape: validate tenant_id.
  if (typeof obj.tenant_id !== "string" || !uuidRegex.test(obj.tenant_id)) {
    throw new ListenerPayloadInvalidError(
      `tenant_id is not a valid UUID: ${obj.tenant_id}`,
      parsed,
    );
  }

  return {
    channel: channel as Exclude<
      CacheInvalidationChannel,
      "cross_tenant_fanout"
    >,
    correction_group_id: obj.correction_group_id as string,
    period_key: obj.period_key as string,
    tenant_id: obj.tenant_id as string,
    trace_id: obj.trace_id as string,
  };
}

/**
 * Adapter protocol (mirrors `CacheInvalidationAdapter` in Python).
 *
 * Each channel adapter implements `onInvalidate(payload)` to evict
 * channel-specific cache entries. The TS mirror exists for parity
 * testing; the actual eviction happens on the backend (apps/api) side.
 */
export interface CacheInvalidationAdapter {
  readonly channel: CacheInvalidationChannel;
  onInvalidate(payload: CacheInvalidationPayload): Promise<void>;
}

/**
 * 5+ channel dispatch table (mirrors `build_default_adapter_factories` in Python).
 *
 * Story 14.1 EXTENSION: cross_tenant_fanout channel 추가.
 */
export const DEFAULT_CHANNEL_ADAPTERS: Record<CacheInvalidationChannel, string> = {
  ai_cache: "M10AIInvalidationAdapter",
  cost_engine_cache: "M3CostEngineInvalidationAdapter",
  fiscal_period_cache: "M11FiscalPeriodInvalidationAdapter",
  closing_snapshot_cache: "M11ClosingSnapshotInvalidationAdapter",
  cross_tenant_fanout: "CrossTenantFanoutAdapter",
};

/**
 * Multi-tenant isolation state (Story 14.1 TS interface NEW).
 *
 * Mirrors the multi-tenant isolation state shape from the Python
 * CrossTenantFanoutAdapter. TS interface exists for parity testing.
 */
export interface MultiTenantIsolationState {
  source_tenant_id: string;
  target_tenant_ids: string[];
  /** Whether the source tenant has LISTEN_NOTIFY_TENANT_FANOUT capability grant. */
  source_has_capability: boolean;
}

/**
 * Leader election state (Story 14.1 TS interface NEW).
 *
 * Mirrors `LeaderElectionState` in Python. TS interface exists for
 * parity testing.
 */
export interface LeaderElectionState {
  is_leader: boolean;
  leader_pod_id: string;
  follower_pod_ids: string[];
}

/**
 * ko-KR reject message (CR 12-5 D-PARITY-01 inversion).
 * Drift 발생 시 displayed to user via the drift detector.
 */
export const DRIFT_DETECTED_REJECT_KO = "LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다";

/**
 * ko-KR reject message for cross-tenant drift (Story 14.1 EXTENSION).
 *
 * Mirrors `CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` in Python.
 */
export const CROSS_TENANT_DRIFT_DETECTED_REJECT_KO =
  "크로스 테넌트 LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다";
