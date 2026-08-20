/**
 * apps/web/lib/cache-invalidation-listener.ts — Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION) TS mirror.
 *
 * Sprint 13-1 (cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속
 * 정직 회복) — T7 wire (cross-language drift detector EXTENSION).
 *
 * AD-15 cross-language parity SSOT: this file mirrors the Python schema
 * (`apps/api/core/cache_invalidation_listener.py`) verbatim. Per CR 12-5
 * D-PARITY-01 inversion, the payload shape MUST match between Python and
 * TS — drift detector verifies this byte-for-byte.
 *
 * Payload shape (5 keys, alphabetical order — V8 determinism):
 *   {
 *     "channel":              "ai_cache",
 *     "correction_group_id":  "uuid-string",
 *     "period_key":           "YYYY-MM",
 *     "tenant_id":            "uuid-string",
 *     "trace_id":             "uuid-string"
 *   }
 *
 * 4 channels (AD-25 verbatim):
 *   - "ai_cache"               — M10 AI cache invalidation
 *   - "cost_engine_cache"      — M3 cost engine calculation result cache
 *   - "fiscal_period_cache"    — M11 fiscal_periods + fiscal_period_snapshots
 *   - "closing_snapshot_cache" — M11 closing_snapshot + ledger closing event
 *
 * Drift detection: if the Python ↔ TS payload shape diverges, the
 * `tests/web/test_cache_invalidation_listener_parity.py` test fails
 * with a 1-line ko-KR reject message.
 */

// ── SSOT mirror — Python `apps.api.core.cache_invalidation_listener` ──

/** 4-channel whitelist (AD-25 verbatim, mirrors `ALLOWED_CHANNELS` in Python). */
export const ALLOWED_CHANNELS = [
  "ai_cache",
  "cost_engine_cache",
  "fiscal_period_cache",
  "closing_snapshot_cache",
] as const;

export type CacheInvalidationChannel =
  (typeof ALLOWED_CHANNELS)[number];

/** NOTIFY channel name (mirrors `NOTIFY_CHANNEL_NAME` in Python). */
export const NOTIFY_CHANNEL_NAME = "cache_invalidation_log";

/** Payload keys (5 keys, alphabetical order — V8 determinism contract). */
export const PAYLOAD_KEYS = [
  "channel",
  "correction_group_id",
  "period_key",
  "tenant_id",
  "trace_id",
] as const;

export type CacheInvalidationPayloadKey = (typeof PAYLOAD_KEYS)[number];

/**
 * Discriminated union payload (mirrors `CacheInvalidationPayload` in Python).
 *
 * The 5 keys are typed as required strings (V8 determinism enforces exact
 * shape). `channel` is the discriminator — TypeScript narrows the type
 * based on the channel value.
 */
export type CacheInvalidationPayload = {
  channel: CacheInvalidationChannel;
  correction_group_id: string;
  period_key: string;
  tenant_id: string;
  trace_id: string;
};

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
 */
export function serializePayloadForV8(
  payload: CacheInvalidationPayload,
): string {
  // Build the object with keys in alphabetical order. This is the
  // canonical serialization order — JSON.stringify preserves insertion
  // order for string keys (per ECMA-262).
  const ordered: Record<CacheInvalidationPayloadKey, string> = {
    channel: payload.channel,
    correction_group_id: payload.correction_group_id,
    period_key: payload.period_key,
    tenant_id: payload.tenant_id,
    trace_id: payload.trace_id,
  };
  return JSON.stringify(ordered);
}

/**
 * Parse a NOTIFY payload string into a typed CacheInvalidationPayload.
 *
 * Mirrors `parse_payload` in Python. Validates:
 * - 5 keys, alphabetical order
 * - channel is in ALLOWED_CHANNELS
 * - tenant_id + correction_group_id are valid UUIDs
 * - trace_id + period_key are non-empty strings
 *
 * Throws `ListenerPayloadInvalidError` on any validation failure.
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

  // Validate exactly 5 keys.
  const actualKeys = Object.keys(obj).sort();
  const expectedKeys = [...PAYLOAD_KEYS].sort();
  if (
    actualKeys.length !== expectedKeys.length ||
    !actualKeys.every((k, i) => k === expectedKeys[i])
  ) {
    throw new ListenerPayloadInvalidError(
      `payload keys mismatch: expected ${JSON.stringify(expectedKeys)}, got ${JSON.stringify(actualKeys)}`,
      parsed,
    );
  }

  // Validate channel.
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

  // Validate UUID fields.
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  for (const key of ["tenant_id", "correction_group_id"] as const) {
    if (typeof obj[key] !== "string" || !uuidRegex.test(obj[key] as string)) {
      throw new ListenerPayloadInvalidError(
        `${key} is not a valid UUID: ${obj[key]}`,
        parsed,
      );
    }
  }

  // Validate trace_id + period_key.
  if (typeof obj.trace_id !== "string" || obj.trace_id === "") {
    throw new ListenerPayloadInvalidError("trace_id must be non-empty str", parsed);
  }
  if (typeof obj.period_key !== "string" || obj.period_key === "") {
    throw new ListenerPayloadInvalidError("period_key must be non-empty str", parsed);
  }

  return {
    channel: channel as CacheInvalidationChannel,
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
 * 4-channel dispatch table (mirrors `build_default_adapter_factories` in Python).
 */
export const DEFAULT_CHANNEL_ADAPTERS: Record<CacheInvalidationChannel, string> = {
  ai_cache: "M10AIInvalidationAdapter",
  cost_engine_cache: "M3CostEngineInvalidationAdapter",
  fiscal_period_cache: "M11FiscalPeriodInvalidationAdapter",
  closing_snapshot_cache: "M11ClosingSnapshotInvalidationAdapter",
};

/**
 * ko-KR reject message (CR 12-5 D-PARITY-01 inversion).
 * Drift 발생 시 displayed to user via the drift detector.
 */
export const DRIFT_DETECTED_REJECT_KO = "LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다";
