// apps/web/lib/m11-close-sequence-parity.ts — Story 11.4 (A13 sprint-up) vitest parity.
//
// Cross-language parity test (Python pure kernel ↔ TS mirror).
// Drift caught between:
// - `packages/services/m11_close/close_sequence_order.py` (Python)
// - `packages/services/m11_close/close_sequence_state.py` (Python)
// - `apps/web/lib/m11-close-sequence.ts` (TS mirror)
//
// SSOT (single source of truth): the Python pure kernels. The TS mirror
// must match the Python verdict for the same input — drift here means
// the panel would render a different close sequence state than the
// backend computes.
//
// Run via: `pnpm exec vitest run m11-close-sequence-parity`

import { describe, expect, it } from "vitest";

import {
  ALL_STAGES_REQUIRED_KO,
  CLOSE_SEQUENCE_STAGES,
  CHRONOLOGICAL_VIOLATION_KO,
  checkAd6InsertAllowed,
  computeCloseSequenceState,
  formatCloseSequenceStateKo,
  validateCloseSequenceOrder,
} from "../../lib/m11-close-sequence";

// ── 5 parity cases mirroring Python pure kernel verdicts ────────

describe("m11-close-sequence parity — validateCloseSequenceOrder", () => {
  it("parity 1: all 4 stages complete → valid + next_step=confirmed", () => {
    const ts = "2026-08-01T00:00:00Z";
    const result = validateCloseSequenceOrder({
      divisions_completed_at: ts,
      manufacturing_completed_at: "2026-08-02T00:00:00Z",
      abc_completed_at: "2026-08-03T00:00:00Z",
      common_completed_at: "2026-08-04T00:00:00Z",
    });
    expect(result.valid).toBe(true);
    expect(result.violations).toEqual([]);
    expect(result.next_step).toBe("confirmed");
    expect(result.reject_reason_ko).toBeNull();
  });

  it("parity 2: divisions missing → invalid + reject_reason_ko=ALL_STAGES_REQUIRED_KO", () => {
    const result = validateCloseSequenceOrder({
      divisions_completed_at: null,
      manufacturing_completed_at: "2026-08-02T00:00:00Z",
      abc_completed_at: null,
      common_completed_at: null,
    });
    expect(result.valid).toBe(false);
    expect(result.next_step).toBe("divisions");
    expect(result.reject_reason_ko).toBe(ALL_STAGES_REQUIRED_KO);
  });

  it("parity 3: chronological violation (manufacturing before divisions) → invalid", () => {
    const result = validateCloseSequenceOrder({
      divisions_completed_at: "2026-08-05T00:00:00Z", // later
      manufacturing_completed_at: "2026-08-01T00:00:00Z", // earlier
      abc_completed_at: null,
      common_completed_at: null,
    });
    expect(result.valid).toBe(false);
    expect(result.violations).toContain(CHRONOLOGICAL_VIOLATION_KO);
  });

  it("parity 4: compute_close_sequence_state — 0 steps → 'divisions'", () => {
    const state = computeCloseSequenceState({
      divisions_completed_at: null,
      manufacturing_completed_at: null,
      abc_completed_at: null,
      common_completed_at: null,
      closed_at: null,
    });
    expect(state).toBe("divisions");
  });

  it("parity 5: check_ad6_insert_allowed — confirmed + reversal_negating → ALLOWED", () => {
    const result = checkAd6InsertAllowed({
      close_sequence_state: "confirmed",
      target_table: "inventory_ledger",
      target_event_type: "reversal_negating",
    });
    expect(result.allowed).toBe(true);
    expect(result.guard_type).toBe("REVERSAL_EXCEPTION");
  });
});

describe("m11-close-sequence parity — CLOSE_SEQUENCE_STAGES + formatCloseSequenceStateKo", () => {
  it("stage ordering parity: 5 stages divisions→manufacturing→abc→common→confirmed", () => {
    expect(CLOSE_SEQUENCE_STAGES).toEqual([
      "divisions",
      "manufacturing",
      "abc",
      "common",
      "confirmed",
    ]);
  });

  it("formatCloseSequenceStateKo returns Korean SSOT for each stage", () => {
    expect(formatCloseSequenceStateKo("divisions")).toBe("divisions 단계 미완료");
    expect(formatCloseSequenceStateKo("confirmed")).toBe("마감 확정");
  });
});

describe("m11-close-sequence parity — AD-6 INSERT guard", () => {
  it("non-confirmed state → ALLOWED", () => {
    const result = checkAd6InsertAllowed({
      close_sequence_state: "manufacturing",
      target_table: "monthly_input_rows",
      target_event_type: "production_material_consumption",
    });
    expect(result.allowed).toBe(true);
    expect(result.guard_type).toBe("ALLOWED");
  });

  it("confirmed + business-data table → CLOSED_LOCK + reject", () => {
    const result = checkAd6InsertAllowed({
      close_sequence_state: "confirmed",
      target_table: "monthly_input_rows",
      target_event_type: "production_material_consumption",
    });
    expect(result.allowed).toBe(false);
    expect(result.guard_type).toBe("CLOSED_LOCK");
    expect(result.reject_reason_ko).toContain("AD-6");
  });
});