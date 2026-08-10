// apps/web/lib/m11-reversal-execute.ts — Story 11.4 (A13 sprint-up) TS mirror.
//
// M11 reversal execute TS projection (AD-15 §11 SSOT parity with
// `packages/services/m11_close/reversal_execute_snapshot.py`).
//
// Drift caught by `apps/web/lib/m11-reversal-execute-parity.ts`
// (vitest cross-language parity test).
//
// AD-22 reversal 영구화: committed → reversed. 3-tier guard:
// 1. monthly_input_periods.status (11-1 SSOT)
// 2. fiscal_periods.status (11-2 PRIMARY)
// 3. fiscal_period_snapshots.state (11-3 NEW — committed only)
//
// Korean message SSOT:
// - REVERSAL_EXECUTE_OK_KO mirrors Python `REVERSAL_EXECUTE_OK_KO`.
// - REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO mirrors Python `REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO`.

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const REVERSAL_EXECUTE_OK_KO = "스냅샷 역분개 완료" as const;
export const REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO =
  "스냅샷 상태가 커밋 상태가 아닙니다 — 역분개 불가" as const;

// ── Snapshot state whitelist for reversal 영구화 ─────────────────
// Only `committed` snapshot state allows reversal 영구화.
export const SNAPSHOT_STATE_REQUIRED = ["committed"] as const;
export const SNAPSHOT_STATE_REJECTED_DRAFT = ["draft"] as const;
export const SNAPSHOT_STATE_REJECTED_VERIFIED = ["verified"] as const;
export const SNAPSHOT_STATE_REJECTED_REVERSED = ["reversed"] as const;

// QTY_QUANTUM = NUMERIC(18, 4) — banker's rounding parity (CR 0-4).
export const QTY_QUANTUM = "0.0001" as const;

// ── Decimal string regex (P-003) ────────────────────────────────
// Mirrors Python `Decimal` strict typing. Accepts signed decimal
// strings ("0", "10.0", "-1.5"). Rejects NaN, Infinity, malformed.
export const DECIMAL_REGEX = /^-?\d+(\.\d+)?$/;

// ── Error codes (mirror Python ERROR_CODE_*) ────────────────────
export const ERROR_CODE_INVALID_INPUT = "INVALID_REVERSAL_INPUT" as const;
export const ERROR_CODE_INVALID_SNAPSHOT_STATE = "INVALID_SNAPSHOT_STATE" as const;
export const ERROR_CODE_INSUFFICIENT_QTY = "INSUFFICIENT_QTY_FOR_NEGATING" as const;

// ── NegatingRowSpec (mirror of Python NamedTuple) ───────────────
export interface NegatingRowSpec {
  tenant_id: string;
  product_id: string;
  period_key: string;
  event_type: "reversal_negating";
  negating_qty: string; // Decimal string (absolute value)
  reverses_event_id: string;
  correction_group_id: string;
  actor_id: string;
  trace_id: string;
}

// ── CorrectedRowSpec (mirror of Python NamedTuple) ──────────────
export interface CorrectedRowSpec {
  tenant_id: string;
  product_id: string;
  period_key: string;
  event_type: "reversal_corrected";
  corrected_qty: string; // Decimal string
  correction_group_id: string;
  actor_id: string;
  trace_id: string;
}

// ── ReversalExecuteState (TS view model) ────────────────────────
export interface ReversalExecuteState {
  authorized: boolean;
  snapshot_state: string;
  correction_group_id: string;
  target_event_id: string;
  negating_qty: string; // absolute value
  corrected_qty: string | null;
  tenant_id: string;
  actor_id: string;
  reject_reason_ko: string | null;
}

// ── validate_reversal_execute_snapshot (TS mirror) ──────────────
// Mirrors Python `validate_reversal_execute_snapshot` pure kernel.
export function buildReversalExecuteState(input: {
  tenant_id: string;
  target_event_id: string;
  snapshot_id: string;
  snapshot_state: string;
  target_qty: string;
  corrected_qty: string | null;
  correction_group_id: string;
  actor_id: string;
}): ReversalExecuteState {
  if (
    !input.tenant_id ||
    !input.target_event_id ||
    !input.snapshot_id ||
    !input.correction_group_id ||
    !input.actor_id
  ) {
    return {
      authorized: false,
      snapshot_state: input.snapshot_state,
      correction_group_id: input.correction_group_id,
      target_event_id: input.target_event_id,
      negating_qty: "0",
      corrected_qty: input.corrected_qty,
      tenant_id: input.tenant_id,
      actor_id: input.actor_id,
      reject_reason_ko: ERROR_CODE_INVALID_INPUT,
    };
  }

  // P-003 — Decimal string validation (parity with Python `Decimal`).
  // P-016 — reject zero qty (meaningless reversal: -0 == 0).
  const qtyNum = parseFloat(input.target_qty);
  if (
    !DECIMAL_REGEX.test(input.target_qty) ||
    isNaN(qtyNum) ||
    qtyNum < 0 ||
    qtyNum === 0
  ) {
    return {
      authorized: false,
      snapshot_state: input.snapshot_state,
      correction_group_id: input.correction_group_id,
      target_event_id: input.target_event_id,
      negating_qty: "0",
      corrected_qty: input.corrected_qty,
      tenant_id: input.tenant_id,
      actor_id: input.actor_id,
      reject_reason_ko: ERROR_CODE_INVALID_INPUT,
    };
  }

  // D-005 — explicit per-state branches (parity with Python kernel).
  // Authoritative: snapshot_state='committed' → authorized.
  const REQUIRED_LIST = SNAPSHOT_STATE_REQUIRED as readonly string[];
  const REJECTED_DRAFT_LIST = SNAPSHOT_STATE_REJECTED_DRAFT as readonly string[];
  const REJECTED_VERIFIED_LIST = SNAPSHOT_STATE_REJECTED_VERIFIED as readonly string[];
  const REJECTED_REVERSED_LIST = SNAPSHOT_STATE_REJECTED_REVERSED as readonly string[];

  if (REQUIRED_LIST.includes(input.snapshot_state)) {
    // Authorized: state='committed' → reversed transition.
    return {
      authorized: true,
      snapshot_state: input.snapshot_state,
      correction_group_id: input.correction_group_id,
      target_event_id: input.target_event_id,
      negating_qty: input.target_qty, // absolute value (sign applied at INSERT)
      corrected_qty: input.corrected_qty,
      tenant_id: input.tenant_id,
      actor_id: input.actor_id,
      reject_reason_ko: null,
    };
  }

  // Known non-committed states: 'draft' / 'verified' / 'reversed'.
  if (
    REJECTED_DRAFT_LIST.includes(input.snapshot_state) ||
    REJECTED_VERIFIED_LIST.includes(input.snapshot_state) ||
    REJECTED_REVERSED_LIST.includes(input.snapshot_state)
  ) {
    return {
      authorized: false,
      snapshot_state: input.snapshot_state,
      correction_group_id: input.correction_group_id,
      target_event_id: input.target_event_id,
      negating_qty: "0",
      corrected_qty: input.corrected_qty,
      tenant_id: input.tenant_id,
      actor_id: input.actor_id,
      reject_reason_ko: REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO,
    };
  }

  // D-005 — explicit unknown state rejection (parity with Python).
  // Mirrors Python `validate_reversal_execute_snapshot` which raises
  // ERROR_CODE_INVALID_SNAPSHOT_STATE for any state not in REQUIRED /
  // REJECTED_DRAFT / REJECTED_VERIFIED / REJECTED_REVERSED.
  // Defense-in-depth — caller bug, should not surface at runtime.
  return {
    authorized: false,
    snapshot_state: input.snapshot_state,
    correction_group_id: input.correction_group_id,
    target_event_id: input.target_event_id,
    negating_qty: "0",
    corrected_qty: input.corrected_qty,
    tenant_id: input.tenant_id,
    actor_id: input.actor_id,
    reject_reason_ko: ERROR_CODE_INVALID_INPUT,
  };
}

// ── build_negating_row_spec (TS mirror) ─────────────────────────
export function buildNegatingRowSpec(input: {
  tenant_id: string;
  product_id: string;
  period_key: string;
  target_qty: string;
  target_event_id: string;
  correction_group_id: string;
  actor_id: string;
  trace_id: string;
}): NegatingRowSpec {
  // P-003 — Decimal string validation. P-016 — zero qty rejection.
  const qtyNum = parseFloat(input.target_qty);
  if (
    !input.tenant_id ||
    !DECIMAL_REGEX.test(input.target_qty) ||
    isNaN(qtyNum) ||
    qtyNum < 0 ||
    qtyNum === 0
  ) {
    throw new Error(ERROR_CODE_INVALID_INPUT);
  }
  return {
    tenant_id: input.tenant_id,
    product_id: input.product_id,
    period_key: input.period_key,
    event_type: "reversal_negating",
    negating_qty: input.target_qty, // absolute value (sign applied at INSERT)
    reverses_event_id: input.target_event_id,
    correction_group_id: input.correction_group_id,
    actor_id: input.actor_id,
    trace_id: input.trace_id,
  };
}

// ── build_corrected_row_spec (TS mirror) ────────────────────────
export function buildCorrectedRowSpec(input: {
  tenant_id: string;
  product_id: string;
  period_key: string;
  corrected_qty: string;
  correction_group_id: string;
  actor_id: string;
  trace_id: string;
}): CorrectedRowSpec {
  // P-003 — Decimal string validation. P-016 — zero qty rejection.
  const qtyNum = parseFloat(input.corrected_qty);
  if (
    !DECIMAL_REGEX.test(input.corrected_qty) ||
    isNaN(qtyNum) ||
    qtyNum < 0 ||
    qtyNum === 0
  ) {
    throw new Error(ERROR_CODE_INVALID_INPUT);
  }
  return {
    tenant_id: input.tenant_id,
    product_id: input.product_id,
    period_key: input.period_key,
    event_type: "reversal_corrected",
    corrected_qty: input.corrected_qty,
    correction_group_id: input.correction_group_id,
    actor_id: input.actor_id,
    trace_id: input.trace_id,
  };
}

// ── isReversalExecuteAllowed (defense-in-depth gate) ────────────
export function isReversalExecuteAllowed(
  state: ReversalExecuteState,
): boolean {
  return state.authorized;
}

// ── formatReversalExecuteResultKo (Korean SSOT) ─────────────────
export function formatReversalExecuteResultKo(
  state: ReversalExecuteState,
): string {
  if (!state.authorized) return state.reject_reason_ko ?? "";
  return REVERSAL_EXECUTE_OK_KO;
}