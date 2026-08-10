// apps/web/lib/m11-reopen.ts — Story 11.4 (A13 sprint-up) TS mirror.
//
// M11 reopen authorization TS projection (AD-15 §11 SSOT parity with
// `packages/services/m11_close/reopen_authorization.py`).
//
// Drift caught by `apps/web/lib/m11-reopen-parity.ts`
// (vitest cross-language parity test).
//
// W2 reopen flow (PRD §F11.4):
// 1. fiscal_periods.status='closed' AND close_sequence_state='confirmed'
// 2. AD-10 owner-only role
// 3. AD-15 reason length 20-500 chars (audit-justification minimum)
// 4. operator_action 4-value enum
// 5. AD-25 multi-channel publish (fiscal_period_cache + closing_snapshot_cache)
//
// Korean message SSOT:
// - REOPEN_AUTHORIZE_OK_KO mirrors Python `REOPEN_AUTHORIZE_OK_KO`.
// - REOPEN_REJECT_NOT_OWNER_KO mirrors Python `REOPEN_REJECT_NOT_OWNER_KO`.
// - REOPEN_REJECT_NO_CAPABILITY_KO mirrors Python `REOPEN_REJECT_NO_CAPABILITY_KO`.
// - REOPEN_REJECT_INVALID_OPERATOR_KO mirrors Python `REOPEN_REJECT_INVALID_OPERATOR_KO`.
// - REOPEN_REJECT_REASON_TOO_SHORT_KO mirrors Python `REOPEN_REJECT_REASON_TOO_SHORT_KO`.
// - REOPEN_REJECT_REASON_TOO_LONG_KO mirrors Python `REOPEN_REJECT_REASON_TOO_LONG_KO`.

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const REOPEN_AUTHORIZE_OK_KO = "재오픈 승인 완료" as const;
export const REOPEN_REJECT_NOT_OWNER_KO =
  "소유자 역할이 아닙니다 — 재오픈 불가" as const;
export const REOPEN_REJECT_NO_CAPABILITY_KO = "재오픈 권한 미보유" as const;
export const REOPEN_REJECT_INVALID_OPERATOR_KO =
  "재오픈 사유 분류가 올바르지 않습니다" as const;
export const REOPEN_REJECT_REASON_TOO_SHORT_KO =
  "재오픈 사유는 20자 이상이어야 합니다" as const;
export const REOPEN_REJECT_REASON_TOO_LONG_KO =
  "재오픈 사유는 500자 이하여야 합니다" as const;

// ── Reason length bounds (AD-15 §11 audit-justification minimum) ─
export const REOPEN_REASON_MIN_LENGTH = 20 as const;
export const REOPEN_REASON_MAX_LENGTH = 500 as const;

// ── operator_action 4-value enum (W2 reopen flow) ───────────────
export const OPERATOR_ACTION_OPERATOR_REOPEN = "operator_reopen" as const;
export const OPERATOR_ACTION_AUDIT_FINDING = "audit_finding" as const;
export const OPERATOR_ACTION_LEGAL_COMPLIANCE = "legal_compliance" as const;
export const OPERATOR_ACTION_DATA_CORRECTION = "data_correction" as const;

export const REOPEN_OPERATOR_ACTIONS = [
  OPERATOR_ACTION_OPERATOR_REOPEN,
  OPERATOR_ACTION_AUDIT_FINDING,
  OPERATOR_ACTION_LEGAL_COMPLIANCE,
  OPERATOR_ACTION_DATA_CORRECTION,
] as const;

export type ReopenOperatorAction = (typeof REOPEN_OPERATOR_ACTIONS)[number];

// ── Error codes (mirror Python ERROR_CODE_*) ────────────────────
export const ERROR_CODE_INVALID_OPERATOR_ACTION =
  "INVALID_OPERATOR_ACTION" as const;
export const ERROR_CODE_INVALID_REASON_LENGTH = "INVALID_REASON_LENGTH" as const;
export const ERROR_CODE_NO_CAPABILITY = "NO_CAPABILITY" as const;
export const ERROR_CODE_NOT_OWNER = "NOT_OWNER_ROLE" as const;
export const ERROR_CODE_NON_UUID_TENANT = "NON_UUID_TENANT_ID" as const;
export const ERROR_CODE_NON_UUID_ACTOR = "NON_UUID_ACTOR_ID" as const;

// ── UUID format validation (P-004) ─────────────────────────────
// Matches Python uuid.UUID validation. Empty string fails (returns false).
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function isUuid(value: string): boolean {
  if (!value) return false;
  return UUID_REGEX.test(value);
}

// ── ReopenAuthorizationState (TS view model) ─────────────────────
export interface ReopenAuthorizationState {
  authorized: boolean;
  reject_reason_ko: string | null;
  operator_action: string;
  reason_length: number;
  capability_granted: boolean;
  is_owner: boolean;
  actor_id: string;
  tenant_id: string;
}

// ── authorize_reopen (TS mirror) ────────────────────────────────
// Mirrors Python `authorize_reopen` pure kernel from reopen_authorization.py.
export function buildReopenAuthorizationState(input: {
  tenant_id: string;
  actor_id: string;
  operator_action: string;
  reason: string;
  capability_granted: boolean;
  is_owner: boolean;
}): ReopenAuthorizationState {
  if (!input.tenant_id || !input.actor_id) {
    // P-005 — distinguish empty/missing input vs invalid UUID format.
    // Empty string is non-UUID by definition; the Python kernel raises
    // ERROR_CODE_NON_UUID_TENANT / NON_UUID_ACTOR for non-UUID inputs.
    const tenantError =
      !input.tenant_id || !isUuid(input.tenant_id)
        ? ERROR_CODE_NON_UUID_TENANT
        : null;
    const actorError =
      !input.actor_id || !isUuid(input.actor_id)
        ? ERROR_CODE_NON_UUID_ACTOR
        : null;
    return {
      authorized: false,
      reject_reason_ko: tenantError ?? actorError ?? ERROR_CODE_NO_CAPABILITY,
      operator_action: input.operator_action,
      reason_length: (input.reason ?? "").length,
      capability_granted: input.capability_granted,
      is_owner: input.is_owner,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
    };
  }

  const reasonLength = (input.reason ?? "").length;

  // Role gate (AD-10 owner-only).
  if (!input.is_owner) {
    return {
      authorized: false,
      reject_reason_ko: REOPEN_REJECT_NOT_OWNER_KO,
      operator_action: input.operator_action,
      reason_length: reasonLength,
      capability_granted: input.capability_granted,
      is_owner: false,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
    };
  }

  // Capability gate.
  if (!input.capability_granted) {
    return {
      authorized: false,
      reject_reason_ko: REOPEN_REJECT_NO_CAPABILITY_KO,
      operator_action: input.operator_action,
      reason_length: reasonLength,
      capability_granted: false,
      is_owner: true,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
    };
  }

  // operator_action enum gate.
  if (
    !(REOPEN_OPERATOR_ACTIONS as readonly string[]).includes(
      input.operator_action,
    )
  ) {
    return {
      authorized: false,
      reject_reason_ko: REOPEN_REJECT_INVALID_OPERATOR_KO,
      operator_action: input.operator_action,
      reason_length: reasonLength,
      capability_granted: true,
      is_owner: true,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
    };
  }

  // Reason length gate.
  if (reasonLength < REOPEN_REASON_MIN_LENGTH) {
    return {
      authorized: false,
      reject_reason_ko: REOPEN_REJECT_REASON_TOO_SHORT_KO,
      operator_action: input.operator_action,
      reason_length: reasonLength,
      capability_granted: true,
      is_owner: true,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
    };
  }

  if (reasonLength > REOPEN_REASON_MAX_LENGTH) {
    return {
      authorized: false,
      reject_reason_ko: REOPEN_REJECT_REASON_TOO_LONG_KO,
      operator_action: input.operator_action,
      reason_length: reasonLength,
      capability_granted: true,
      is_owner: true,
      actor_id: input.actor_id,
      tenant_id: input.tenant_id,
    };
  }

  // Authorized.
  return {
    authorized: true,
    reject_reason_ko: null,
    operator_action: input.operator_action,
    reason_length: reasonLength,
    capability_granted: true,
    is_owner: true,
    actor_id: input.actor_id,
    tenant_id: input.tenant_id,
  };
}

// ── isReopenAllowed (defense-in-depth gate) ─────────────────────
export function isReopenAllowed(state: ReopenAuthorizationState): boolean {
  return state.authorized;
}

// ── formatReopenResultKo (Korean SSOT for reopen outcome) ───────
export function formatReopenResultKo(
  state: ReopenAuthorizationState,
): string {
  if (!state.authorized) return state.reject_reason_ko ?? "";
  return REOPEN_AUTHORIZE_OK_KO;
}

// ── validateReopenReasonLength (defense-in-depth) ───────────────
// Mirrors Python REOPEN_REASON_MIN_LENGTH / REOPEN_REASON_MAX_LENGTH.
// Returns true if reason length is within bounds.
export function isReasonLengthValid(reason: string): boolean {
  return (
    reason.length >= REOPEN_REASON_MIN_LENGTH &&
    reason.length <= REOPEN_REASON_MAX_LENGTH
  );
}