/**
 * apps/web/__tests__/m11-reversal-route.test.tsx — Story 11.1 T10.10
 *
 * Vitest scenarios for the reversal request route + parity helpers:
 *
 * 1. test_buildReversalRequestState_open_allowed — period_status='open' +
 *    capability_granted=true → allow_submission=true.
 * 2. test_buildReversalRequestState_locked_rejected — period_status='locked' →
 *    allow_submission=false + reject_reason_ko=M11_REJECT_LOCKED_KO.
 * 3. test_buildReversalRequestState_no_capability_rejected —
 *    capability_granted=false → allow_submission=false + reject_reason_ko=
 *    M11_REJECT_NO_CAPABILITY_KO.
 * 4. test_negateQty_bankers_rounding — banker's rounding parity (sign flip +
 *    ROUND_HALF_EVEN at QTY_QUANTUM = 0.0001).
 * 5. test_quantizeDecimal_even_rounding — ROUND_HALF_EVEN behavior at 0.00005.
 * 6. test_validateReversalNegatingConstraints_self_reversal_forbidden —
 *    target.event_type='reversal_negating' → throws "self-reversal forbidden".
 */

import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it } from "vitest";
import { cleanup } from "@testing-library/react";

import {
  buildReversalRequestState,
  isReversalRequestAllowed,
  M11_REJECT_LOCKED_KO,
  M11_REJECT_NO_CAPABILITY_KO,
  PERIOD_STATUS_OPEN,
  PERIOD_STATUS_LOCKED,
  validateReversalNegatingConstraints,
} from "@/lib/m11-reversal";
import {
  correctedQty,
  isReversalQtyParity,
  negateQty,
  quantizeDecimal,
} from "@/lib/m11-reversal-parity";

describe("m11-reversal route helpers", () => {
  afterEach(() => {
    cleanup();
  });

  // ── Case 1: open + capability → allowed ────────────────────────
  it("test_buildReversalRequestState_open_allowed", () => {
    const state = buildReversalRequestState({
      target_event_id: "11111111-1111-1111-1111-111111111111",
      period_status: PERIOD_STATUS_OPEN,
      capability_granted: true,
    });
    expect(state.allow_submission).toBe(true);
    expect(isReversalRequestAllowed(state)).toBe(true);
    expect(state.period_locked).toBe(false);
  });

  // ── Case 2: locked → rejected with Korean message ─────────────
  it("test_buildReversalRequestState_locked_rejected", () => {
    const state = buildReversalRequestState({
      target_event_id: "11111111-1111-1111-1111-111111111111",
      period_status: PERIOD_STATUS_LOCKED,
      capability_granted: true,
    });
    expect(state.allow_submission).toBe(false);
    expect(state.reject_reason_ko).toBe(M11_REJECT_LOCKED_KO);
  });

  // ── Case 3: no capability → rejected ──────────────────────────
  it("test_buildReversalRequestState_no_capability_rejected", () => {
    const state = buildReversalRequestState({
      target_event_id: "11111111-1111-1111-1111-111111111111",
      period_status: PERIOD_STATUS_OPEN,
      capability_granted: false,
    });
    expect(state.allow_submission).toBe(false);
    expect(state.reject_reason_ko).toBe(M11_REJECT_NO_CAPABILITY_KO);
  });

  // ── Case 4: negateQty + banker's rounding ─────────────────────
  it("test_negateQty_bankers_rounding", () => {
    expect(negateQty("10.5")).toBe("-10.5000");
    expect(negateQty("0.0001")).toBe("-0.0001");
    // ROUND_HALF_EVEN at midpoint: 0.00005 → 0.0000 (even) NOT 0.0001.
    expect(quantizeDecimal("0.00005")).toBe("0.0000");
  });

  // ── Case 5: ROUND_HALF_EVEN parity with Python ────────────────
  it("test_quantizeDecimal_even_rounding", () => {
    // Python Decimal("0.00015").quantize(Decimal("0.0001"), ROUND_HALF_EVEN)
    // → "0.0002" (banker's rounding to even).
    // TS Decimal.js ROUND_HALF_EVEN should match.
    expect(correctedQty("0.00015")).toBe("0.0002");
    expect(isReversalQtyParity("0.00015", "0.0002")).toBe(true);
  });

  // ── Case 6: self-reversal forbidden (validate target event_type) ──
  it("test_validateReversalNegatingConstraints_self_reversal_forbidden", () => {
    const target = {
      event_id: "11111111-1111-1111-1111-111111111111",
      tenant_id: "22222222-2222-2222-2222-222222222222",
      product_id: "33333333-3333-3333-3333-333333333333",
      period_key: PERIOD_KEY_OPEN_OK,
      event_type: "reversal_negating",
      qty: "-10.5",
      trace_id: "44444444-4444-4444-4444-444444444444",
      reverses_event_id: null,
      correction_group_id: null,
      reversal_of_period_key: null,
      actor_id: "55555555-5555-5555-5555-555555555555",
      payload: {},
    };
    expect(() => validateReversalNegatingConstraints(target)).toThrow(
      /self-reversal forbidden/,
    );
  });
});

const PERIOD_KEY_OPEN_OK = "2026-08";
