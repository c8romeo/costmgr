// apps/web/__tests__/lib/m9-abc-validation-schema-parity.test.ts — Story 9.1
//
// Cross-language parity test: TS validation schema must mirror backend
// Pydantic rules (`apps/api/modules/m9_abc/schemas.py` +
// `validate_abc_pct_list` 3-layer defense).
//
// CR 11-4 D-002 ko-KR.json SSOT pin: Korean error message constants in
// `m9-abc-validation.ts` must match backend typed exception constants
// (`apps/api/modules/m9_abc/exceptions.py`).

import { describe, expect, it } from "vitest";

import {
  ABC_ACTIVITY_INVALID_SUM_KO,
  ABC_COST_POOL_INVALID_SUM_KO,
  ABC_DRIVER_INVALID_SUM_KO,
  ABC_VALIDATION_NOT_FOUND_KO,
  VALIDATION_100_PCT_TARGET,
  isValidAbcPct,
  isValidAbcPctList,
  sumPct,
} from "@/lib/m9-abc-validation";
import {
  buildKoreanMismatchHint,
  computeSumPct,
  is100Percent,
  validateAbcPctList,
} from "@/lib/m9-abc-validation-schema";

// ── Korean SSOT pin (CR 11-4 D-002) ─────────────────────────────

describe("korean SSOT pin (CR 11-4 D-002)", () => {
  it("ABC_COST_POOL_INVALID_SUM_KO matches backend verbatim", () => {
    expect(ABC_COST_POOL_INVALID_SUM_KO).toBe("원가풀 행 합이 100%가 아닙니다");
  });
  it("ABC_ACTIVITY_INVALID_SUM_KO matches backend verbatim", () => {
    expect(ABC_ACTIVITY_INVALID_SUM_KO).toBe("활동 열 합이 100%가 아닙니다");
  });
  it("ABC_DRIVER_INVALID_SUM_KO matches backend verbatim", () => {
    expect(ABC_DRIVER_INVALID_SUM_KO).toBe("동인 합이 100%가 아닙니다");
  });
  it("ABC_VALIDATION_NOT_FOUND_KO matches backend verbatim", () => {
    expect(ABC_VALIDATION_NOT_FOUND_KO).toBe(
      "ABC 검증 대상을 찾을 수 없습니다",
    );
  });
});

// ── 100% target pin ─────────────────────────────────────────────

describe("VALIDATION_100_PCT_TARGET", () => {
  it("is 100", () => {
    expect(VALIDATION_100_PCT_TARGET).toBe(100);
  });
});

// ── isValidAbcPct / isValidAbcPctList (mirror Pydantic Field bounds) ──

describe("isValidAbcPct", () => {
  it("accepts '0'", () => {
    expect(isValidAbcPct("0")).toBe(true);
  });
  it("accepts '100'", () => {
    expect(isValidAbcPct("100")).toBe(true);
  });
  it("accepts '33.33'", () => {
    expect(isValidAbcPct("33.33")).toBe(true);
  });
  it("rejects '-1'", () => {
    expect(isValidAbcPct("-1")).toBe(false);
  });
  it("rejects '101'", () => {
    expect(isValidAbcPct("101")).toBe(false);
  });
  it("rejects 'abc'", () => {
    expect(isValidAbcPct("abc")).toBe(false);
  });
  it("rejects ''", () => {
    expect(isValidAbcPct("")).toBe(false);
  });
});

describe("isValidAbcPctList", () => {
  it("accepts non-empty list of valid pcts", () => {
    expect(isValidAbcPctList(["25", "75"])).toBe(true);
  });
  it("rejects empty list (CR 11-4 D-005)", () => {
    expect(isValidAbcPctList([])).toBe(false);
  });
  it("rejects list with invalid value", () => {
    expect(isValidAbcPctList(["50", "200"])).toBe(false);
  });
});

// ── sumPct (mirror backend Decimal sum) ─────────────────────────

describe("sumPct", () => {
  it("sums valid list to 100", () => {
    expect(sumPct(["25", "25", "25", "25"])).toBe(100);
  });
  it("returns 0 for empty list", () => {
    expect(sumPct([])).toBe(0);
  });
  it("sums decimal values", () => {
    expect(sumPct(["33.33", "33.33", "33.34"])).toBeCloseTo(100, 2);
  });
});

// ── validateAbcPctList — CR 11-4 D-005 (throw on invalid) ───────

describe("validateAbcPctList", () => {
  it("cost_pool: accepts valid list (CR 11-4 D-005)", () => {
    expect(() => validateAbcPctList(["50", "50"], "cost_pool")).not.toThrow();
  });
  it("cost_pool: throws on empty list", () => {
    expect(() => validateAbcPctList([], "cost_pool")).toThrow();
  });
  it("cost_pool: throws on out-of-range", () => {
    expect(() => validateAbcPctList(["150"], "cost_pool")).toThrow();
  });
  it("activity: accepts valid list", () => {
    expect(() => validateAbcPctList(["50", "50"], "activity")).not.toThrow();
  });
  it("activity: throws on empty list", () => {
    expect(() => validateAbcPctList([], "activity")).toThrow();
  });
  it("driver: accepts valid list", () => {
    expect(() => validateAbcPctList(["100"], "driver")).not.toThrow();
  });
  it("driver: throws on empty list", () => {
    expect(() => validateAbcPctList([], "driver")).toThrow();
  });
  it("driver: throws on out-of-range", () => {
    expect(() => validateAbcPctList(["-5"], "driver")).toThrow();
  });
});

// ── computeSumPct (re-export sanity) ────────────────────────────

describe("computeSumPct", () => {
  it("matches sumPct", () => {
    expect(computeSumPct(["25", "75"])).toBe(100);
  });
});

// ── is100Percent (with tolerance) ───────────────────────────────

describe("is100Percent", () => {
  it("returns true when sum equals 100", () => {
    expect(is100Percent(["50", "50"])).toBe(true);
  });
  it("returns false when sum is 105", () => {
    expect(is100Percent(["55", "50"])).toBe(false);
  });
  it("accepts 1% tolerance", () => {
    expect(is100Percent(["99", "2"], 1)).toBe(true);
  });
});

// ── buildKoreanMismatchHint ─────────────────────────────────────

describe("buildKoreanMismatchHint", () => {
  it("cost_pool hint includes sum_pct", () => {
    const hint = buildKoreanMismatchHint("cost_pool", 105);
    expect(hint).toContain("원가풀");
    expect(hint).toContain("105");
  });
  it("activity hint includes sum_pct", () => {
    const hint = buildKoreanMismatchHint("activity", 92);
    expect(hint).toContain("활동");
    expect(hint).toContain("92");
  });
  it("driver hint includes sum_pct", () => {
    const hint = buildKoreanMismatchHint("driver", 80);
    expect(hint).toContain("동인");
    expect(hint).toContain("80");
  });
});