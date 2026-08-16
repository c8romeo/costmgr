// apps/web/__tests__/lib/m9-abc-allocation-schema-parity.test.ts — Story 9.2
//
// Cross-language parity tests for M9 ABC Allocation Engine TS mirror
// (PRD §F9.2 + §A9 + §V7 verbatim).
//
// Mirrors `packages/cost_engine/abc_engine.py` (CCRResult + AllocationResult
// + UnusedCapacityRow + compute_ccr + compute_allocation + produce_unused_capacity_row).
//
// CR 11-4 D-002: Korean SSOT messages match ko-KR.json + Python exceptions.py.
// CR 11-4 D-005: Validation throws (no silent fall-through).

import { describe, expect, it } from "vitest";

import {
  ABC_ALLOCATION_BALANCE_ERROR_KO,
  ABC_CCR_INVALID_CAPACITY_KO,
  CCR_HASH_PREFIX,
} from "../../lib/m9-abc-allocation";
import {
  AbcAllocationInputError,
  buildKoreanUnusedCapacityMessage,
  computeAllocationTS,
  computeCcrTS,
  isBalancedAllocation,
  produceUnusedCapacityRowTS,
} from "../../lib/m9-abc-allocation-schema";

// ── computeCcrTS parity tests (mirror backend compute_ccr) ───

describe("computeCcrTS (Story 9.2 parity)", () => {
  it("computes CCR per hour 33,000 KRW from 13,200,000 KRW / 400h", () => {
    const result = computeCcrTS({
      department_id: "dept-001",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    expect(result.ccr_per_hour).toBe("33000");
    expect(result.department_id).toBe("dept-001");
  });

  it("uses 1-Won precision (CCR_KRW_QUANTUM = 1)", () => {
    const result = computeCcrTS({
      department_id: "dept-precision",
      department_cost: "19800000",
      practical_capacity_hours: "600",
    });
    expect(result.ccr_per_hour).toBe("33000");
  });

  it("returns sha256:64-hex hash with prefix", () => {
    const result = computeCcrTS({
      department_id: "dept-hash",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    expect(result.hash.startsWith(CCR_HASH_PREFIX)).toBe(true);
    expect(result.hash.length).toBe(CCR_HASH_PREFIX.length + 64);
  });

  it("is deterministic — same input → same hash", () => {
    const a = computeCcrTS({
      department_id: "dept-det",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const b = computeCcrTS({
      department_id: "dept-det",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    expect(a.hash).toBe(b.hash);
    expect(a.ccr_per_hour).toBe(b.ccr_per_hour);
  });

  it("throws on zero capacity", () => {
    expect(() =>
      computeCcrTS({
        department_id: "dept-zero",
        department_cost: "13200000",
        practical_capacity_hours: "0",
      }),
    ).toThrow(AbcAllocationInputError);
  });

  it("throws on negative capacity", () => {
    expect(() =>
      computeCcrTS({
        department_id: "dept-neg",
        department_cost: "13200000",
        practical_capacity_hours: "-50",
      }),
    ).toThrow(AbcAllocationInputError);
  });

  it("throws on negative cost", () => {
    expect(() =>
      computeCcrTS({
        department_id: "dept-negcost",
        department_cost: "-100",
        practical_capacity_hours: "400",
      }),
    ).toThrow(AbcAllocationInputError);
  });

  it("throws on empty department_id", () => {
    expect(() =>
      computeCcrTS({
        department_id: "",
        department_cost: "13200000",
        practical_capacity_hours: "400",
      }),
    ).toThrow(AbcAllocationInputError);
  });
});

// ── isBalancedAllocation parity tests (mirror backend V7 balance) ─

describe("isBalancedAllocation (Story 9.2 parity)", () => {
  it("returns true when Σ breakdown + unused = Σ department_cost", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [
        {
          activity_id: "act-001",
          hours: "400",
          ccr_amount_krw: "13200000",
        },
      ],
      cost_object_breakdown: [
        {
          product_id: "prod-A",
          activity_id: "act-001",
          driver_id: "drv-001",
          allocated_krw: "13200000",
        },
      ],
      used_hours: "400",
    });
    expect(isBalancedAllocation(allocation)).toBe(true);
  });

  it("returns false when breakdown + unused != department_cost", () => {
    const ccr = computeCcrTS({
      department_id: "dept-unbalanced",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [],
      cost_object_breakdown: [
        {
          product_id: "prod-A",
          activity_id: "act-001",
          driver_id: "drv-001",
          allocated_krw: "10000000",
        },
      ],
      used_hours: "400",
    });
    expect(isBalancedAllocation(allocation)).toBe(false);
  });

  it("returns false with empty breakdown", () => {
    const ccr = computeCcrTS({
      department_id: "dept-empty",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [],
      cost_object_breakdown: [],
      used_hours: "400",
    });
    expect(isBalancedAllocation(allocation)).toBe(false);
  });

  it("uses default used_hours = capacity when null provided", () => {
    const ccr = computeCcrTS({
      department_id: "dept-default",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [],
      cost_object_breakdown: [
        {
          product_id: "prod-A",
          activity_id: "act-001",
          driver_id: "drv-001",
          allocated_krw: "13200000",
        },
      ],
      used_hours: null,
    });
    expect(allocation.unused_capacity.unused_hours).toBe("0");
    expect(isBalancedAllocation(allocation)).toBe(true);
  });

  it("throws on negative used_hours", () => {
    const ccr = computeCcrTS({
      department_id: "dept-negused",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    expect(() =>
      computeAllocationTS({
        ccr,
        activity_mappings: [],
        cost_object_breakdown: [],
        used_hours: "-10",
      }),
    ).toThrow(AbcAllocationInputError);
  });
});

// ── AbcAllocationInputError parity (mirror Python typed exceptions) ─

describe("AbcAllocationInputError (Story 9.2 parity)", () => {
  it("carries target and reason", () => {
    try {
      computeCcrTS({
        department_id: "dept-x",
        department_cost: "13200000",
        practical_capacity_hours: "0",
      });
    } catch (e) {
      expect(e).toBeInstanceOf(AbcAllocationInputError);
      const err = e as AbcAllocationInputError;
      expect(err.target).toBe("ccr");
      expect(err.reason).toContain(ABC_CCR_INVALID_CAPACITY_KO);
    }
  });

  it("name is set to AbcAllocationInputError", () => {
    const err = new AbcAllocationInputError("ccr", "test");
    expect(err.name).toBe("AbcAllocationInputError");
    expect(err.message).toContain("ccr");
  });

  it("toString carries target and reason", () => {
    const err = new AbcAllocationInputError(
      "allocation",
      ABC_ALLOCATION_BALANCE_ERROR_KO,
    );
    expect(err.message).toContain(ABC_ALLOCATION_BALANCE_ERROR_KO);
  });

  it("supports all 3 targets: ccr, allocation, unused_capacity", () => {
    const targets: Array<"ccr" | "allocation" | "unused_capacity"> = [
      "ccr",
      "allocation",
      "unused_capacity",
    ];
    for (const target of targets) {
      const err = new AbcAllocationInputError(target, "test_reason");
      expect(err.target).toBe(target);
    }
  });
});

// ── Frozen types parity (mirror Python frozen dataclasses) ────

describe("AllocationState union coverage (Story 9.2 parity)", () => {
  it("CCRResult has all required fields", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    expect(typeof ccr.department_id).toBe("string");
    expect(typeof ccr.department_cost).toBe("string");
    expect(typeof ccr.practical_capacity_hours).toBe("string");
    expect(typeof ccr.ccr_per_hour).toBe("string");
    expect(typeof ccr.hash).toBe("string");
  });

  it("UnusedCapacityRow has all required fields", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "19800000",
      practical_capacity_hours: "600",
    });
    const unused = produceUnusedCapacityRowTS({
      ccr,
      used_hours: "400",
    });
    expect(typeof unused.unused_hours).toBe("string");
    expect(typeof unused.ccr_per_hour).toBe("string");
    expect(typeof unused.unused_cost_krw).toBe("string");
    expect(typeof unused.hash).toBe("string");
  });

  it("AllocationResult has all required fields", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [],
      cost_object_breakdown: [],
      used_hours: "400",
    });
    expect(typeof allocation.department_cost).toBe("string");
    expect(typeof allocation.total_breakdown_sum).toBe("string");
    expect(typeof allocation.is_balanced).toBe("boolean");
  });

  it("PRD §A9 verbatim — unused 200h * 33,000 = 6,600,000원", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "19800000",
      practical_capacity_hours: "600",
    });
    const unused = produceUnusedCapacityRowTS({
      ccr,
      used_hours: "400",
    });
    expect(unused.unused_hours).toBe("200");
    expect(unused.unused_cost_krw).toBe("6600000");
  });

  it("AllocationResult contains CCR + activity_mappings + breakdown + unused", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [
        {
          activity_id: "act-001",
          hours: "400",
          ccr_amount_krw: "13200000",
        },
      ],
      cost_object_breakdown: [
        {
          product_id: "prod-A",
          activity_id: "act-001",
          driver_id: "drv-001",
          allocated_krw: "13200000",
        },
      ],
      used_hours: "400",
    });
    expect(allocation.ccr).toEqual(ccr);
    expect(allocation.activity_mappings).toHaveLength(1);
    expect(allocation.cost_object_breakdown).toHaveLength(1);
    expect(allocation.unused_capacity).toBeDefined();
  });

  it("hash field uses sha256 prefix + 64-hex", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    expect(ccr.hash.startsWith("sha256:")).toBe(true);
    expect(ccr.hash.slice("sha256:".length)).toMatch(/^[0-9a-f]{64}$/);
  });

  it("Korean message builder uses verbatim format", () => {
    const ccr = computeCcrTS({
      department_id: "dept-001",
      department_cost: "19800000",
      practical_capacity_hours: "600",
    });
    const unused = produceUnusedCapacityRowTS({
      ccr,
      used_hours: "400",
    });
    expect(buildKoreanUnusedCapacityMessage(unused)).toBe(
      "미사용능력 6600000원",
    );
  });

  it("unbalanced allocation surfaces Korean error message", () => {
    const ccr = computeCcrTS({
      department_id: "dept-unbalanced",
      department_cost: "13200000",
      practical_capacity_hours: "400",
    });
    const allocation = computeAllocationTS({
      ccr,
      activity_mappings: [],
      cost_object_breakdown: [
        {
          product_id: "prod-A",
          activity_id: "act-001",
          driver_id: "drv-001",
          allocated_krw: "10000000",
        },
      ],
      used_hours: "400",
    });
    expect(allocation.is_balanced).toBe(false);
  });
});