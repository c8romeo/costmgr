// apps/web/lib/m11-reversal.ts — Story 11.1 TS mirror.
//
// M11 reversal sequence TS projection (AD-15 §11 SSOT parity with
// `packages/services/m11_close/reversal_negating.py` +
// `reversal_corrected.py` + `reversal_authorization.py`).
//
// Drift caught by `tests/integration/test_m11_reversal_label_consistency.py`.
//
// Korean message SSOT (single source of truth for ko-KR.json parity):
// - M11_AUTHORIZE_KO mirrors Python `M11_AUTHORIZE_KO`.
// - M11_REJECT_LOCKED_KO mirrors Python `M11_REJECT_LOCKED_KO`.
// - M11_REJECT_NO_CAPABILITY_KO mirrors Python `M11_REJECT_NO_CAPABILITY_KO`.
//
// AD-22 reversal sequence event_type whitelist (Alembic 0015 11-value CHECK):
// - REVERSAL_NEGATING_EVENT_TYPE: sign-negating row
// - REVERSAL_CORRECTED_EVENT_TYPE: corrected row (optional)
//
// AD-22 (tenant_id, reverses_event_id) UNIQUE constraint (Alembic 0015
// `uq_inventory_ledger_reverses_event_id` PARTIAL UNIQUE INDEX) blocks
// re-correction of the same target event. M11 service layer raises
// `ReversalDuplicateError` → 422 REVERSAL_DUPLICATE envelope on violation.
//
// Story 5-2 P11 (`m4_inventory/handlers.py:356-390` 501 forward-fill route)
// is deprecated by Story 11.1 — M11 actual write endpoint
// `POST /api/v1/close/reversal-requests` is SSOT.

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const M11_AUTHORIZE_KO = "M11 모듈 권한 OK" as const;
export const M11_REJECT_LOCKED_KO = "잠긴 기간 — 역분개 불가" as const;
export const M11_REJECT_NO_CAPABILITY_KO =
  "역분개 권한 미보유 (REVERSAL_REQUEST capability)" as const;

// ── Event type whitelist (AD-22 sign-negating + corrected row) ───
export const REVERSAL_NEGATING_EVENT_TYPE = "reversal_negating" as const;
export const REVERSAL_CORRECTED_EVENT_TYPE = "reversal_corrected" as const;

export const REVERSAL_EVENT_TYPES = [
  REVERSAL_NEGATING_EVENT_TYPE,
  REVERSAL_CORRECTED_EVENT_TYPE,
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type ReversalEventType = (typeof REVERSAL_EVENT_TYPES)[number];

// ── Period status (AD-6 close lock — monthly_input_periods.status) ──
// "open" / "closed" → reversal allowed. "locked" → reject (422
// LOCKED_PERIOD_REVERSAL_REJECTED).
export const PERIOD_STATUS_OPEN = "open" as const;
export const PERIOD_STATUS_CLOSED = "closed" as const;
export const PERIOD_STATUS_LOCKED = "locked" as const;

export const PERIOD_STATUSES = [
  PERIOD_STATUS_OPEN,
  PERIOD_STATUS_CLOSED,
  PERIOD_STATUS_LOCKED,
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type PeriodStatus = (typeof PERIOD_STATUSES)[number];

// ── ReversalRequestState (frontend mirror of authorize_reversal result) ──
export interface ReversalRequestState {
  target_event_id: string;
  period_status: PeriodStatus;
  capability_granted: boolean;
  period_locked: boolean;
  allow_submission: boolean;
  reject_reason_ko: string | null;
}

// ── ReversalRequestPayload (POST /api/v1/close/reversal-requests body) ──
// Mirrors Pydantic `ReversalCreateRequest` (handlers.py).
export interface ReversalRequestPayload {
  target_event_id: string;
  reason: string;
  corrected_qty: string | null;       // Decimal string (AD-8)
  corrected_period_key: string | null; // AD-24 typed "YYYY-MM"
}

// ── InventoryLedgerEvent (reversal target — 5-2 wire extension) ──
// Mirrors Python `InventoryLedgerEvent` NamedTuple (9 reversal fields).
export interface InventoryLedgerEvent {
  event_id: string;
  tenant_id: string;
  product_id: string;
  period_key: string;
  event_type: string;
  qty: string;                        // Decimal string (AD-8)
  trace_id: string;
  reverses_event_id: string | null;
  correction_group_id: string | null;
  reversal_of_period_key: string | null;
  actor_id: string;
  payload: Record<string, unknown>;
}

// ── ReversalHistoryEntry (GET /reversal-requests/{cid} row) ──
export interface ReversalHistoryEntry {
  event_id: string;
  tenant_id: string;
  product_id: string;
  period_key: string;
  event_type: string;
  qty: string | null;
  reverses_event_id: string | null;
  correction_group_id: string | null;
  reversal_of_period_key: string | null;
  trace_id: string;
}

// ── ReversalCreateResponse (POST /reversal-requests response envelope) ──
// Mirrors Pydantic `ReversalCreateResponse`.
export interface ReversalCreateResponse {
  correction_group_id: string;
  negating_event_id: string;
  corrected_event_id: string | null;
  target_event_id: string;
  reversal_history: ReversalHistoryEntry[];
  trace_id: string;
  cache_invalidation_receipt: Record<string, string>;
}

// ── ReversalHistoryResponse (GET /reversal-requests/{cid} envelope) ──
export interface ReversalHistoryResponse {
  correction_group_id: string;
  reversal_history: ReversalHistoryEntry[];
  trace_id: string;
}

// ── CacheInvalidationPublishRequest (POST /cache-invalidation body) ──
export interface CacheInvalidationPublishRequest {
  channel: string;                    // FROZENSET = {'ai_cache'} for 11-1 wire
  event_id: string;
  correction_group_id: string;
}

// ── CacheInvalidationPublishResponse (POST /cache-invalidation envelope) ──
export interface CacheInvalidationPublishResponse {
  channel: string;
  tenant_id: string;
  event_id: string;
  correction_group_id: string;
  published_at: string;
  trace_id: string;
}

// ── Error code constants (AD-15 §4 typed envelope) ──────────────
export const REVERSAL_ERROR_CODE_TARGET_NOT_FOUND =
  "REVERSAL_TARGET_NOT_FOUND" as const;
export const REVERSAL_ERROR_CODE_REJECTED = "REVERSAL_REJECTED" as const;
export const REVERSAL_ERROR_CODE_UNAUTHORIZED =
  "REVERSAL_UNAUTHORIZED" as const;
export const REVERSAL_ERROR_CODE_DUPLICATE = "REVERSAL_DUPLICATE" as const;
export const REVERSAL_ERROR_CODE_LOCKED =
  "LOCKED_PERIOD_REVERSAL_REJECTED" as const;
export const REVERSAL_ERROR_CODE_INDUSTRY_NOT_SUPPORTED =
  "INDUSTRY_NOT_SUPPORTED" as const;

// ── buildReversalRequestState (frontend authorization gate) ─────
// Mirrors Python `authorize_reversal` pure-kernel decision.
export function buildReversalRequestState(input: {
  target_event_id: string;
  period_status: PeriodStatus;
  capability_granted: boolean;
}): ReversalRequestState {
  // eslint-disable-next-line @typescript-eslint/naming-convention, camelcase
  const period_locked = input.period_status === PERIOD_STATUS_LOCKED;
  // eslint-disable-next-line @typescript-eslint/naming-convention, camelcase
  const allow_submission =
    // eslint-disable-next-line camelcase
    !period_locked &&
    input.capability_granted &&
    input.target_event_id.length > 0;

  // eslint-disable-next-line @typescript-eslint/naming-convention, camelcase
  let reject_reason_ko: string | null = null;
  if (!input.capability_granted) {
    // eslint-disable-next-line camelcase
    reject_reason_ko = M11_REJECT_NO_CAPABILITY_KO;
  // eslint-disable-next-line camelcase
  } else if (period_locked) {
    // eslint-disable-next-line camelcase
    reject_reason_ko = M11_REJECT_LOCKED_KO;
  }

  return {
    target_event_id: input.target_event_id,
    period_status: input.period_status,
    capability_granted: input.capability_granted,
    // eslint-disable-next-line camelcase
    period_locked,
    // eslint-disable-next-line camelcase
    allow_submission,
    // eslint-disable-next-line camelcase
    reject_reason_ko,
  };
}

// ── isReversalRequestAllowed (defense-in-depth gate) ────────────
export function isReversalRequestAllowed(state: ReversalRequestState): boolean {
  return state.allow_submission;
}

// ── formatReversalReasonKo (Korean SSOT — reason field) ─────────
export function formatReversalReasonKo(reason: string): string {
  const trimmed = reason.trim();
  if (trimmed.length === 0) {
    return "";
  }
  return trimmed;
}

// ── validateReversalNegatingConstraints (defense-in-depth) ─────
// Mirrors Python `validate_reversal_negating_constraints`.
// Reversal target event_type must be in the reversal-eligible whitelist
// (8 values from the 11-value inventory_ledger event_type CHECK).
const REVERSAL_ELIGIBLE_EVENT_TYPES: ReadonlySet<string> = new Set([
  "opening_carried",
  "opening_carried_stale_overwrite",
  "purchase_inbound",
  "sales_outbound",
  "production_output_inbound",
  "production_material_consumption",
  "adjustment_positive",
  "adjustment_negative",
  "closing_snapshot",
]);

const NON_REVERSIBLE_EVENT_TYPES: ReadonlySet<string> = new Set([
  REVERSAL_NEGATING_EVENT_TYPE,
  REVERSAL_CORRECTED_EVENT_TYPE,
]);

export function validateReversalNegatingConstraints(
  target: InventoryLedgerEvent,
): void {
  if (!target.event_id) {
    throw new Error("target_event_id is required");
  }
  if (NON_REVERSIBLE_EVENT_TYPES.has(target.event_type)) {
    throw new Error(
      `self-reversal forbidden — cannot reverse event_type=${target.event_type}`,
    );
  }
  if (!REVERSAL_ELIGIBLE_EVENT_TYPES.has(target.event_type)) {
    throw new Error(
      `event_type=${target.event_type} is not reversal-eligible`,
    );
  }
}

// ── validateReversalCorrectedConstraints (defense-in-depth) ────
// Mirrors Python `validate_reversal_corrected_constraints`. Pure-KO.
const PERIOD_KEY_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

export function validateReversalCorrectedConstraints(input: {
  target_event: InventoryLedgerEvent;
  corrected_period_key: string;
  correction_group_id: string;
}): void {
  if (!PERIOD_KEY_PATTERN.test(input.corrected_period_key)) {
    throw new Error(
      `corrected_period_key=${input.corrected_period_key} must match AD-24 typed 'YYYY-MM' pattern`,
    );
  }
  if (!input.correction_group_id) {
    throw new Error("correction_group_id is required");
  }
  if (!input.target_event.event_id) {
    throw new Error("target_event.event_id is required");
  }
}
