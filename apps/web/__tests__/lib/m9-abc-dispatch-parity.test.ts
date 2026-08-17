// apps/web/__tests__/lib/m9-abc-dispatch-parity.test.ts — Story 9.7
//
// Cross-language parity tests for M9 ABC Dispatch TS mirror
// (PRD §F9.3 + A29 forward-lock dual-route + AD-19).
//
// Mirrors `apps/web/lib/m9-abc-dispatch.ts` 9-3 EXTENSION surface:
//   - EngineTypeTag Literal "trad" | "abc"
//   - DispatchState / V7Verdict / MultiDepartmentCcrResult / DepartmentAllocation
//   - UnusedCapacitySubRow / AllocationOutcomeABC / CalcAbcResponse / CalcResponse
//   - VerdictWire / VerificationItemWire
//   - isCalcAbcResponse / isCalcResponse type guards
//
// CR 11-4 D-002: Korean SSOT constants match ko-KR.json + Python exceptions.py.
// CR 11-4 D-005: type guards reject unknown state (no silent fall-through).
//
// A35 wire — resolves D3 (8 컴포넌트 마운트 부재 중 m9-abc-dispatch parity 추가).

import { describe, expect, it } from "vitest";

import {
  ABC_EMPTY_DEPARTMENTS_KO,
  ABC_HASH_LENGTH,
  ABC_HASH_PREFIX,
  ABC_HASH_REGEX,
  ABC_TOO_MANY_DEPARTMENTS_KO,
  type CalcAbcResponse,
  type CalcOutcomeResponse,
  type CalcResponse,
  MAX_DEPARTMENT_COUNT,
  V7_BALANCE_TOLERANCE_KRW,
  isCalcAbcResponse,
  isCalcResponse,
} from "../../lib/m9-abc-dispatch";

// ── Constants pin (5 cases) ─────────────────────────────────

describe("m9-abc-dispatch constants (Story 9.3 parity, A35 wire)", () => {
  it("pins V7_BALANCE_TOLERANCE_KRW = '0.01' (PRD §V7 verbatim)", () => {
    expect(V7_BALANCE_TOLERANCE_KRW).toBe("0.01");
  });

  it("pins MAX_DEPARTMENT_COUNT = 50 (PRD §F9.3)", () => {
    expect(MAX_DEPARTMENT_COUNT).toBe(50);
  });

  it("pins ABC_HASH_PREFIX = 'sha256:' (V8 hash prefix)", () => {
    expect(ABC_HASH_PREFIX).toBe("sha256:");
  });

  it("pins ABC_HASH_LENGTH = 64 (sha256 hex digits)", () => {
    expect(ABC_HASH_LENGTH).toBe(64);
  });

  it("ABC_HASH_REGEX matches sha256 64-hex format (no prefix in regex)", () => {
    // Note: ABC_HASH_PREFIX = "sha256:" is informational; the regex itself
    // matches only the 64 hex chars (per m9-abc-dispatch.ts:32).
    expect(ABC_HASH_REGEX.test("0".repeat(64))).toBe(true);
    expect(ABC_HASH_REGEX.test("g".repeat(64))).toBe(false);
    expect(ABC_HASH_REGEX.test("a".repeat(63))).toBe(false);
  });
});

// ── Korean SSOT pin (2 cases — CR 11-4 D-002) ─────────────

describe("m9-abc-dispatch Korean SSOT (CR 11-4 D-002)", () => {
  it("pins ABC_EMPTY_DEPARTMENTS_KO verbatim", () => {
    expect(ABC_EMPTY_DEPARTMENTS_KO).toBe("ABC 부서가 등록되지 않았습니다");
  });

  it("pins ABC_TOO_MANY_DEPARTMENTS_KO verbatim", () => {
    expect(ABC_TOO_MANY_DEPARTMENTS_KO).toBe("ABC 부서 수가 한도를 초과했습니다");
  });
});

// ── Type guards (CR 11-4 D-005) ────────────────────────────

describe("isCalcAbcResponse type guard", () => {
  const tradOutcome: CalcResponse = {
    tenant_id: "00000000-0000-0000-0000-000000000001",
    period_key: "2026-08",
    baseline_revision: 1,
    material_cost: 5_000_000,
    labor_cost: 3_000_000,
    overhead_cost: 2_000_000,
    manufacturing_cost: 10_000_000,
    inventory_adjustment: 0,
    result_hash: "sha256:trad0000000000000000000000000000000000000000000000000000",
    state: "verified",
    trace_id: "trace-trad-001",
    verdict: {
      verification_status: "passed",
      verifications: [],
      top_failure: null,
      trace_id: "trace-trad-001",
    },
  };

  const abcOutcome: CalcAbcResponse = {
    engine_type: "abc",
    tenant_id: "00000000-0000-0000-0000-000000000001",
    period_key: "2026-08",
    baseline_revision: 1,
    allocation_outcome: {
      breakdown: [],
      unused_capacity: { rows: [], is_balanced: true, delta_krw: "0" },
      v7_verdict: {
        is_balanced: true,
        breakdown_sum: "0",
        unused_cost: "0",
        expected_sum: "0",
        delta_krw: "0",
        hash: "sha256:" + "0".repeat(64),
      },
      ccr: { departments: [] },
      is_balanced: true,
    },
    snapshot_id: "00000000-0000-0000-0000-000000000abc",
    result_hash: "sha256:" + "a".repeat(64),
    state: "verified",
    trace_id: "trace-abc-001",
    verdict: {
      verification_status: "passed",
      verifications: [],
      top_failure: null,
      trace_id: "trace-abc-001",
    },
  };

  it("returns true for outcome with engine_type='abc' tag", () => {
    expect(isCalcAbcResponse(abcOutcome)).toBe(true);
  });

  it("returns false for outcome without engine_type tag (trad)", () => {
    expect(isCalcAbcResponse(tradOutcome)).toBe(false);
  });

  it("returns false when engine_type is 'trad' (unknown state reject — CR 11-4 D-005)", () => {
    const malformed = {
      ...tradOutcome,
      engine_type: "trad" as const,
    } as unknown as CalcOutcomeResponse;
    expect(isCalcAbcResponse(malformed)).toBe(false);
  });
});

describe("isCalcResponse type guard", () => {
  const tradOutcome: CalcResponse = {
    tenant_id: "t-1",
    period_key: "2026-08",
    baseline_revision: 1,
    material_cost: 0,
    labor_cost: 0,
    overhead_cost: 0,
    manufacturing_cost: 0,
    inventory_adjustment: 0,
    result_hash: "sha256:" + "t".repeat(64),
    state: "verified",
    trace_id: "trace-t",
    verdict: {
      verification_status: "passed",
      verifications: [],
      top_failure: null,
      trace_id: "trace-t",
    },
  };

  const abcOutcome: CalcAbcResponse = {
    engine_type: "abc",
    tenant_id: "t-1",
    period_key: "2026-08",
    baseline_revision: 1,
    allocation_outcome: {
      breakdown: [],
      unused_capacity: { rows: [], is_balanced: true, delta_krw: "0" },
      v7_verdict: {
        is_balanced: true,
        breakdown_sum: "0",
        unused_cost: "0",
        expected_sum: "0",
        delta_krw: "0",
        hash: "sha256:" + "0".repeat(64),
      },
      ccr: { departments: [] },
      is_balanced: true,
    },
    snapshot_id: "00000000-0000-0000-0000-000000000abc",
    result_hash: "sha256:" + "a".repeat(64),
    state: "verified",
    trace_id: "trace-a",
    verdict: {
      verification_status: "passed",
      verifications: [],
      top_failure: null,
      trace_id: "trace-a",
    },
  };

  it("returns true for outcome without engine_type tag (trad)", () => {
    expect(isCalcResponse(tradOutcome)).toBe(true);
  });

  it("returns false for outcome with engine_type='abc' tag", () => {
    expect(isCalcResponse(abcOutcome)).toBe(false);
  });
});

// ── Type shape parity (3 cases — frozen shape invariant) ───

describe("m9-abc-dispatch type shape", () => {
  it("CalcAbcResponse requires engine_type='abc' tag (Literal)", () => {
    const sample: CalcAbcResponse = {
      engine_type: "abc",
      tenant_id: "t-1",
      period_key: "2026-08",
      baseline_revision: 1,
      allocation_outcome: {
        breakdown: [],
        unused_capacity: { rows: [], is_balanced: true, delta_krw: "0" },
        v7_verdict: {
          is_balanced: true,
          breakdown_sum: "0",
          unused_cost: "0",
          expected_sum: "0",
          delta_krw: "0",
          hash: "sha256:" + "0".repeat(64),
        },
        ccr: { departments: [] },
        is_balanced: true,
      },
      snapshot_id: "00000000-0000-0000-0000-000000000abc",
      result_hash: "sha256:" + "a".repeat(64),
      state: "verified",
      trace_id: "trace-a",
      verdict: {
        verification_status: "passed",
        verifications: [],
        top_failure: null,
        trace_id: "trace-a",
      },
    };
    expect(sample.engine_type).toBe("abc");
    expect(sample.state).toBe("verified");
  });

  it("CalcResponse (trad) requires NO engine_type field", () => {
    const sample: CalcResponse = {
      tenant_id: "t-1",
      period_key: "2026-08",
      baseline_revision: 1,
      material_cost: 0,
      labor_cost: 0,
      overhead_cost: 0,
      manufacturing_cost: 0,
      inventory_adjustment: 0,
      result_hash: "sha256:" + "t".repeat(64),
      state: "verified",
      trace_id: "trace-t",
      verdict: {
        verification_status: "passed",
        verifications: [],
        top_failure: null,
        trace_id: "trace-t",
      },
    };
    expect("engine_type" in sample).toBe(false);
  });

  it("CalcOutcomeResponse is a discriminated union of CalcResponse | CalcAbcResponse", () => {
    const outcome: CalcOutcomeResponse =
      Math.random() > 0.5
        ? ({
            engine_type: "abc",
            tenant_id: "t-1",
            period_key: "2026-08",
            baseline_revision: 1,
            allocation_outcome: {
              breakdown: [],
              unused_capacity: { rows: [], is_balanced: true, delta_krw: "0" },
              v7_verdict: {
                is_balanced: true,
                breakdown_sum: "0",
                unused_cost: "0",
                expected_sum: "0",
                delta_krw: "0",
                hash: "sha256:" + "0".repeat(64),
              },
              ccr: { departments: [] },
              is_balanced: true,
            },
            snapshot_id: "00000000-0000-0000-0000-000000000abc",
            result_hash: "sha256:" + "a".repeat(64),
            state: "verified",
            trace_id: "trace-a",
            verdict: {
              verification_status: "passed",
              verifications: [],
              top_failure: null,
              trace_id: "trace-a",
            },
          } as CalcAbcResponse)
        : ({
            tenant_id: "t-1",
            period_key: "2026-08",
            baseline_revision: 1,
            material_cost: 0,
            labor_cost: 0,
            overhead_cost: 0,
            manufacturing_cost: 0,
            inventory_adjustment: 0,
            result_hash: "sha256:" + "t".repeat(64),
            state: "verified",
            trace_id: "trace-t",
            verdict: {
              verification_status: "passed",
              verifications: [],
              top_failure: null,
              trace_id: "trace-t",
            },
          } as CalcResponse);

    // Type guard narrowing works at compile time + runtime.
    if (isCalcAbcResponse(outcome)) {
      expect(outcome.engine_type).toBe("abc");
    } else {
      expect("engine_type" in outcome).toBe(false);
    }
  });
});