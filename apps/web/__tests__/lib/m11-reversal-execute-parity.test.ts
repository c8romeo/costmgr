// apps/web/lib/m11-reversal-execute-parity.ts — Story 11.4 (A13 sprint-up) vitest parity.
//
// Cross-language parity test (Python pure kernel ↔ TS mirror) for AD-22
// reversal execute 영구화 (committed → reversed).
//
// Drift caught between:
// - `packages/services/m11_close/reversal_execute_snapshot.py` (Python)
// - `apps/web/lib/m11-reversal-execute.ts` (TS mirror)
//
// Run via: `pnpm exec vitest run m11-reversal-execute-parity`

import { describe, expect, it } from "vitest";

import {
  REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO,
  REVERSAL_EXECUTE_OK_KO,
  buildCorrectedRowSpec,
  buildNegatingRowSpec,
  buildReversalExecuteState,
  formatReversalExecuteResultKo,
  isReversalExecuteAllowed,
} from "../../lib/m11-reversal-execute";

const TENANT_ID = "22222222-2222-4222-8222-222222222222";
const TARGET_EVENT_ID = "44444444-4444-4444-8444-444444444444";
const SNAPSHOT_ID = "11111111-1111-4111-8111-111111111111";
const CORRECTION_GROUP_ID = "55555555-5555-4555-8555-555555555555";
const PRODUCT_ID = "66666666-6666-4666-8666-666666666666";
const ACTOR_ID = "33333333-3333-4333-8333-333333333333";
const TRACE_ID = "trace-test-1";

describe("m11-reversal-execute parity — buildReversalExecuteState", () => {
  it("parity 1: state='committed' + target_qty='10.0' → authorized + OK_KO", () => {
    const state = buildReversalExecuteState({
      tenant_id: TENANT_ID,
      target_event_id: TARGET_EVENT_ID,
      snapshot_id: SNAPSHOT_ID,
      snapshot_state: "committed",
      target_qty: "10.0",
      corrected_qty: null,
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
    });
    expect(state.authorized).toBe(true);
    expect(state.negating_qty).toBe("10.0");
    expect(state.reject_reason_ko).toBeNull();
    expect(formatReversalExecuteResultKo(state)).toBe(REVERSAL_EXECUTE_OK_KO);
    expect(isReversalExecuteAllowed(state)).toBe(true);
  });

  it("parity 2: state='verified' → not authorized + INVALID_SNAPSHOT_KO", () => {
    const state = buildReversalExecuteState({
      tenant_id: TENANT_ID,
      target_event_id: TARGET_EVENT_ID,
      snapshot_id: SNAPSHOT_ID,
      snapshot_state: "verified",
      target_qty: "10.0",
      corrected_qty: null,
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO);
  });

  it("parity 3: state='reversed' → not authorized + INVALID_SNAPSHOT_KO", () => {
    const state = buildReversalExecuteState({
      tenant_id: TENANT_ID,
      target_event_id: TARGET_EVENT_ID,
      snapshot_id: SNAPSHOT_ID,
      snapshot_state: "reversed",
      target_qty: "10.0",
      corrected_qty: null,
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe(REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO);
  });

  it("parity 4: corrected_qty='8.5' → preserved in result", () => {
    const state = buildReversalExecuteState({
      tenant_id: TENANT_ID,
      target_event_id: TARGET_EVENT_ID,
      snapshot_id: SNAPSHOT_ID,
      snapshot_state: "committed",
      target_qty: "10.0",
      corrected_qty: "8.5",
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
    });
    expect(state.authorized).toBe(true);
    expect(state.corrected_qty).toBe("8.5");
  });

  it("parity 5: negative target_qty → INVALID_REVERSAL_INPUT error", () => {
    const state = buildReversalExecuteState({
      tenant_id: TENANT_ID,
      target_event_id: TARGET_EVENT_ID,
      snapshot_id: SNAPSHOT_ID,
      snapshot_state: "committed",
      target_qty: "-1.0",
      corrected_qty: null,
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
    });
    expect(state.authorized).toBe(false);
    expect(state.reject_reason_ko).toBe("INVALID_REVERSAL_INPUT");
  });
});

describe("m11-reversal-execute parity — buildNegatingRowSpec", () => {
  it("parity 6: target_qty='10.0' → NegatingRowSpec with event_type='reversal_negating'", () => {
    const spec = buildNegatingRowSpec({
      tenant_id: TENANT_ID,
      product_id: PRODUCT_ID,
      period_key: "2026-08",
      target_qty: "10.0",
      target_event_id: TARGET_EVENT_ID,
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
      trace_id: TRACE_ID,
    });
    expect(spec.event_type).toBe("reversal_negating");
    expect(spec.negating_qty).toBe("10.0");
    expect(spec.reverses_event_id).toBe(TARGET_EVENT_ID);
  });

  it("parity 7: negative target_qty → throws INVALID_REVERSAL_INPUT", () => {
    expect(() =>
      buildNegatingRowSpec({
        tenant_id: TENANT_ID,
        product_id: PRODUCT_ID,
        period_key: "2026-08",
        target_qty: "-1.0",
        target_event_id: TARGET_EVENT_ID,
        correction_group_id: CORRECTION_GROUP_ID,
        actor_id: ACTOR_ID,
        trace_id: TRACE_ID,
      }),
    ).toThrow("INVALID_REVERSAL_INPUT");
  });
});

describe("m11-reversal-execute parity — buildCorrectedRowSpec", () => {
  it("parity 8: corrected_qty='8.5' → CorrectedRowSpec with event_type='reversal_corrected'", () => {
    const spec = buildCorrectedRowSpec({
      tenant_id: TENANT_ID,
      product_id: PRODUCT_ID,
      period_key: "2026-08",
      corrected_qty: "8.5",
      correction_group_id: CORRECTION_GROUP_ID,
      actor_id: ACTOR_ID,
      trace_id: TRACE_ID,
    });
    expect(spec.event_type).toBe("reversal_corrected");
    expect(spec.corrected_qty).toBe("8.5");
  });
});