// apps/web/lib/m11-reopen-parity.ts — Story 11.4 (A13 sprint-up) vitest parity.
//
// Cross-language parity test (Python pure kernel ↔ TS mirror) for W2
// reopen authorization (operator_action 4-value enum + reason length 20-500).
//
// Drift caught between:
// - `packages/services/m11_close/reopen_authorization.py` (Python)
// - `apps/web/lib/m11-reopen.ts` (TS mirror)
//
// Run via: `pnpm exec vitest run m11-reopen-parity`

import { describe, expect, it } from "vitest";

import {
  REOPEN_AUTHORIZE_OK_KO,
  REOPEN_REJECT_INVALID_OPERATOR_KO,
  REOPEN_REJECT_NO_CAPABILITY_KO,
  REOPEN_REJECT_NOT_OWNER_KO,
  REOPEN_REJECT_REASON_TOO_LONG_KO,
  REOPEN_REJECT_REASON_TOO_SHORT_KO,
  REOPEN_REASON_MAX_LENGTH,
  REOPEN_REASON_MIN_LENGTH,
  buildReopenAuthorizationState,
  formatReopenResultKo,
  isReopenAllowed,
  isReasonLengthValid,
} from "../../lib/m11-reopen";

const TENANT_ID = "22222222-2222-4222-8222-222222222222";
const ACTOR_ID = "33333333-3333-4333-8333-333333333333";
const VALID_REASON =
  "재오픈 사유 — 20자 이상의 정당화 사유 작성 필요 (audit-justification minimum)";

describe("m11-reopen parity — buildReopenAuthorizationState", () => {
  it("parity 1: owner + capability + valid operator + valid reason → authorized", () => {
    const state = buildReopenAuthorizationState({
      tenant_id: TENANT_ID,
      actor_id: ACTOR_ID,
      operator_action: "audit_finding",
      reason: VALID_REASON,
      capability_granted: true,
      is_owner: true,
    });
    expect(state.authorized).toBe(true);
    expect(state.reject_reason_ko).toBeNull();
    expect(formatReopenResultKo(state)).toBe(REOPEN_AUTHORIZE_OK_KO);
    expect(isReopenAllowed(state)).toBe(true);
  });

  it("parity 2: is_owner=false → REOPEN_REJECT_NOT_OWNER_KO", () => {
    const state = buildReopenAuthorizationState({
      tenant_id: TENANT_ID,
      actor_id: ACTOR_ID,
      operator_action: "operator_reopen",
      reason: VALID_REASON,
      capability_granted: true,
      is_owner: false,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REOPEN_REJECT_NOT_OWNER_KO);
  });

  it("parity 3: capability_granted=false → REOPEN_REJECT_NO_CAPABILITY_KO", () => {
    const state = buildReopenAuthorizationState({
      tenant_id: TENANT_ID,
      actor_id: ACTOR_ID,
      operator_action: "operator_reopen",
      reason: VALID_REASON,
      capability_granted: false,
      is_owner: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REOPEN_REJECT_NO_CAPABILITY_KO);
  });

  it("parity 4: invalid operator_action → REOPEN_REJECT_INVALID_OPERATOR_KO", () => {
    const state = buildReopenAuthorizationState({
      tenant_id: TENANT_ID,
      actor_id: ACTOR_ID,
      operator_action: "INVALID_OPERATOR",
      reason: VALID_REASON,
      capability_granted: true,
      is_owner: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REOPEN_REJECT_INVALID_OPERATOR_KO);
  });

  it("parity 5: reason too short (< 20 chars) → REOPEN_REJECT_REASON_TOO_SHORT_KO", () => {
    const state = buildReopenAuthorizationState({
      tenant_id: TENANT_ID,
      actor_id: ACTOR_ID,
      operator_action: "operator_reopen",
      reason: "too short",
      capability_granted: true,
      is_owner: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REOPEN_REJECT_REASON_TOO_SHORT_KO);
  });

  it("parity 6: reason too long (> 500 chars) → REOPEN_REJECT_REASON_TOO_LONG_KO", () => {
    const state = buildReopenAuthorizationState({
      tenant_id: TENANT_ID,
      actor_id: ACTOR_ID,
      operator_action: "operator_reopen",
      reason: "x".repeat(REOPEN_REASON_MAX_LENGTH + 1),
      capability_granted: true,
      is_owner: true,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REOPEN_REJECT_REASON_TOO_LONG_KO);
  });
});

describe("m11-reopen parity — isReasonLengthValid + operator_action whitelist", () => {
  it("parity 7: REOPEN_REASON_MIN_LENGTH=20 + REOPEN_REASON_MAX_LENGTH=500", () => {
    expect(REOPEN_REASON_MIN_LENGTH).toBe(20);
    expect(REOPEN_REASON_MAX_LENGTH).toBe(500);
  });

  it("parity 8: reason within bounds → isReasonLengthValid=true", () => {
    expect(isReasonLengthValid(VALID_REASON)).toBe(true);
  });

  it("parity 9: reason below min → isReasonLengthValid=false", () => {
    expect(isReasonLengthValid("short")).toBe(false);
  });

  it("parity 10: 4-value operator_action enum accepted", () => {
    for (const action of [
      "operator_reopen",
      "audit_finding",
      "legal_compliance",
      "data_correction",
    ]) {
      const state = buildReopenAuthorizationState({
        tenant_id: TENANT_ID,
        actor_id: ACTOR_ID,
        operator_action: action,
        reason: VALID_REASON,
        capability_granted: true,
        is_owner: true,
      });
      expect(state.authorized).toBe(true);
    }
  });
});