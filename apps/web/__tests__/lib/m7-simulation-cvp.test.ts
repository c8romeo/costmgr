// apps/web/__tests__/lib/m7-simulation-cvp.test.ts — Story 7.1
//
// TS mirror parity tests for `apps/web/lib/m7-simulation-cvp.ts`.
// Cross-language drift detector (CR 12-5 D-13) — TS implementation
// MUST match Python `packages/cost_engine.cvp` semantics.

import { describe, expect, it } from "vitest";

import {
  type CVPBaselineSerialized,
  type CVPDeltaSerialized,
  applyDeltaTS,
  computeBepTS,
  isValidDeltaPctTS,
  isValidRealPeriodKeyTS,
  simulateCvpTS,
} from "@/lib/m7-simulation-cvp";

const baseline: CVPBaselineSerialized = {
  fixed_cost: "10000000",
  unit_variable_cost: "6000",
  unit_price: "10000",
  operating_rate: "1.0",
  target_profit: "0",
};

const zeroDelta: CVPDeltaSerialized = {
  unit_price_delta_pct: "0",
  unit_variable_cost_delta_pct: "0",
  fixed_cost_delta_pct: "0",
  operating_rate_delta_pct: "0",
};

describe("computeBepTS", () => {
  it("basic case — fixed_cost=10000000, unit_variable_cost=6000, unit_price=10000", () => {
    const result = computeBepTS(10000000, 6000, 10000);
    expect(result.bep_quantity).toBe("2500");
    expect(result.bep_revenue).toBe("25000000");
    expect(result.contribution_margin_per_unit).toBe("4000");
    expect(result.contribution_margin_ratio).toBe("0.4");
  });

  it("zero fixed_cost → bep_quantity=0", () => {
    const result = computeBepTS(0, 6000, 10000);
    expect(result.bep_quantity).toBe("0");
    expect(result.bep_revenue).toBe("0");
  });

  it("unit_price == unit_variable_cost → throw", () => {
    expect(() => computeBepTS(10000000, 10000, 10000)).toThrow();
  });

  it("unit_price < unit_variable_cost → throw", () => {
    expect(() => computeBepTS(10000000, 11000, 10000)).toThrow();
  });

  it("negative fixed_cost → throw", () => {
    expect(() => computeBepTS(-1000, 6000, 10000)).toThrow();
  });
});

describe("applyDeltaTS", () => {
  it("zero delta returns equivalent baseline (assertion bounds)", () => {
    const simulated = applyDeltaTS(baseline, zeroDelta);
    expect(simulated.fixed_cost).toBe(baseline.fixed_cost);
    expect(simulated.unit_price).toBe(baseline.unit_price);
  });

  it("unit_price +10% → 11000", () => {
    const simulated = applyDeltaTS(baseline, {
      ...zeroDelta,
      unit_price_delta_pct: "0.1",
    });
    expect(simulated.unit_price).toBe("11000");
  });

  it("operating_rate out of bounds → throw", () => {
    expect(() =>
      applyDeltaTS(baseline, {
        ...zeroDelta,
        operating_rate_delta_pct: "0.9", // 1.0 + 0.9 = 1.9 > 1.5
      }),
    ).toThrow();
  });

  it("baseline NOT mutated (frozen semantics)", () => {
    const before = baseline.unit_price;
    applyDeltaTS(baseline, {
      ...zeroDelta,
      unit_price_delta_pct: "0.1",
    });
    expect(baseline.unit_price).toBe(before);
  });
});

describe("simulateCvpTS", () => {
  it("zero delta → simulated == baseline", () => {
    const result = simulateCvpTS(baseline, zeroDelta);
    expect(result.simulated_bep.bep_quantity).toBe(result.baseline_bep.bep_quantity);
  });

  it("unit_price +10% → simulated BEP quantity < baseline", () => {
    const result = simulateCvpTS(baseline, {
      ...zeroDelta,
      unit_price_delta_pct: "0.1",
    });
    const baselineQty = parseFloat(result.baseline_bep.bep_quantity);
    const simulatedQty = parseFloat(result.simulated_bep.bep_quantity);
    expect(simulatedQty).toBeLessThan(baselineQty);
  });

  it("delta_summary contains all 4 keys", () => {
    const result = simulateCvpTS(baseline, zeroDelta);
    expect(result.delta_summary).toHaveProperty("unit_price_delta_pct");
    expect(result.delta_summary).toHaveProperty("unit_variable_cost_delta_pct");
    expect(result.delta_summary).toHaveProperty("fixed_cost_delta_pct");
    expect(result.delta_summary).toHaveProperty("operating_rate_delta_pct");
  });

  it("target_profit zero → simulated_target_profit.target_quantity == baseline target_quantity", () => {
    const result = simulateCvpTS(baseline, zeroDelta);
    expect(result.simulated_target_profit.target_quantity).toBe(
      result.baseline_target_profit.target_quantity,
    );
  });
});

describe("validators", () => {
  it("isValidRealPeriodKeyTS — YYYY-MM valid", () => {
    expect(isValidRealPeriodKeyTS("2026-07")).toBe(true);
    expect(isValidRealPeriodKeyTS("2026-13")).toBe(false);
    expect(isValidRealPeriodKeyTS("2026-7")).toBe(false);
  });

  it("isValidDeltaPctTS — respects bounds", () => {
    expect(isValidDeltaPctTS(0.3, [-0.5, 0.5])).toBe(true);
    expect(isValidDeltaPctTS(0.7, [-0.5, 0.5])).toBe(false);
    expect(isValidDeltaPctTS(-0.5, [-0.5, 0.5])).toBe(true);
  });
});
