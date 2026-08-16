// apps/web/__tests__/lib/m8-budget-variance-parity.test.ts — Story 8.2 (Epic 8)
//
// Cross-language parity test (TS ↔ Python pure kernel mirror drift detector).
// Drift caught between:
// - `packages/cost_engine/budget_variance.py` (Python pure kernel)
// - `apps/web/lib/m8-budget-variance.ts` (TS mirror)
//
// SSOT: the Python pure kernel. The TS mirror must match the Python
// verdict for the same input — drift here means the variance table
// would render a different color/severity than the backend computes.
//
// Run via: `pnpm exec vitest run m8-budget-variance-parity`

import { describe, expect, it } from "vitest";

import {
  ABCD_DISABLED_NOTE,
  computeVarianceTSToString,
  formatKRWTS,
  formatVariancePctTS,
  getVarianceColorClassTS,
  getVarianceTextClassTS,
  SEVERITY_THRESHOLD_CRITICAL_PCT,
  SEVERITY_THRESHOLD_WARNING_PCT,
  TOTAL_ROW_LABEL_KO,
  VARIANCE_PCT_DECIMAL_PLACES,
} from "../../lib/m8-budget-variance";

describe("m8-budget-variance parity — severity thresholds", () => {
  it("parity 1: warning threshold == 5 (PRD §F8.2 verbatim)", () => {
    expect(SEVERITY_THRESHOLD_WARNING_PCT).toBe(5);
  });

  it("parity 2: critical threshold == 10 (PRD §F8.2 verbatim)", () => {
    expect(SEVERITY_THRESHOLD_CRITICAL_PCT).toBe(10);
  });

  it("parity 3: variance_pct quantum == 4 decimal places", () => {
    expect(VARIANCE_PCT_DECIMAL_PLACES).toBe(4);
  });
});

describe("m8-budget-variance parity — computeVarianceTSToString", () => {
  it("parity 1: zero budget → 0% normal gray", () => {
    const result = computeVarianceTSToString("0", "100");
    expect(result.variance_pct).toBe("0");
    expect(result.severity).toBe("normal");
    expect(result.color).toBe("gray");
  });

  it("parity 2: +5% exact boundary → warning yellow", () => {
    const result = computeVarianceTSToString("1000000", "1050000");
    expect(result.variance_pct).toBe("5");
    expect(result.severity).toBe("warning");
    expect(result.color).toBe("yellow");
  });

  it("parity 3: +10% exact boundary → critical red", () => {
    const result = computeVarianceTSToString("1000000", "1100000");
    expect(result.variance_pct).toBe("10");
    expect(result.severity).toBe("critical");
    expect(result.color).toBe("red");
  });

  it("parity 4: -5% boundary → warning yellow (sign preserved)", () => {
    const result = computeVarianceTSToString("1000000", "950000");
    expect(result.variance_pct).toBe("-5");
    expect(result.severity).toBe("warning");
    expect(result.color).toBe("yellow");
  });

  it("parity 5: small diff (1.5%) → normal gray", () => {
    const result = computeVarianceTSToString("1000000", "1015000");
    expect(result.color).toBe("gray");
    expect(result.severity).toBe("normal");
  });

  it("parity 6: invalid input → fallback normal gray", () => {
    const result = computeVarianceTSToString("not-a-number", "100");
    expect(result.severity).toBe("normal");
    expect(result.color).toBe("gray");
  });
});

describe("m8-budget-variance parity — formatters", () => {
  it("parity 1: formatKRWTS adds 천단위 콤마", () => {
    expect(formatKRWTS("1234567")).toBe("1,234,567");
  });

  it("parity 2: formatKRWTS invalid → passthrough", () => {
    expect(formatKRWTS("invalid")).toBe("invalid");
  });

  it("parity 3: formatVariancePctTS preserves positive sign", () => {
    expect(formatVariancePctTS("5.1234")).toBe("+5.1234%");
  });

  it("parity 4: formatVariancePctTS handles negative", () => {
    expect(formatVariancePctTS("-3.5")).toBe("-3.5000%");
  });

  it("parity 5: formatVariancePctTS handles zero (no sign)", () => {
    expect(formatVariancePctTS("0")).toBe("0.0000%");
  });
});

describe("m8-budget-variance parity — color class helpers", () => {
  it("parity 1: gray → bg-gray-50 + text-gray-700", () => {
    expect(getVarianceColorClassTS("gray")).toBe("bg-gray-50");
    expect(getVarianceTextClassTS("gray")).toBe("text-gray-700");
  });

  it("parity 2: yellow → bg-yellow-50 + text-yellow-700", () => {
    expect(getVarianceColorClassTS("yellow")).toBe("bg-yellow-50");
    expect(getVarianceTextClassTS("yellow")).toBe("text-yellow-700");
  });

  it("parity 3: red → bg-red-50 + text-red-700", () => {
    expect(getVarianceColorClassTS("red")).toBe("bg-red-50");
    expect(getVarianceTextClassTS("red")).toBe("text-red-700");
  });
});

describe("m8-budget-variance parity — SSOT constants", () => {
  it("parity 1: ABCD disabled note (PRD §15 NON-GOAL #1)", () => {
    expect(ABCD_DISABLED_NOTE).toBe(
      "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]",
    );
  });

  it("parity 2: total row label (PRD §F8.2)", () => {
    expect(TOTAL_ROW_LABEL_KO).toBe("합계");
  });
});
