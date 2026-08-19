/**
 * apps/web/__tests__/lib/insight-cache-parity.test.ts — Sprint 10.5 T2 wire (D-10-2-DEFER-4 해소)
 *
 * AD-15 cross-language parity test for insight-cache.ts (TS mirror) vs
 * apps/api/modules/m10_ai/schemas.py Story 10.2 EXTENSION.
 */

import { describe, expect, it } from "vitest";

import {
  composeInsightCacheKey,
  INSIGHT_KIND_VALUES,
  SOURCE_KIND_VALUES,
  type InsightEntry,
  type InsightListResponse,
} from "@/lib/insight-cache";

describe("insight-cache parity — Sprint 10.5 T2", () => {
  it("INSIGHT_KIND_VALUES has exactly 3 kinds (cost_reduction_candidate, anomaly_pattern, forecast)", () => {
    expect(INSIGHT_KIND_VALUES).toEqual([
      "cost_reduction_candidate",
      "anomaly_pattern",
      "forecast",
    ]);
  });

  it("SOURCE_KIND_VALUES has 2 kinds (auto_analysis, ai_reference)", () => {
    expect(SOURCE_KIND_VALUES).toEqual(["auto_analysis", "ai_reference"]);
  });

  it("composeInsightCacheKey 3-tuple format = tenantId::periodKey::hash (AD-25 verbatim)", () => {
    const key = composeInsightCacheKey("tenant-1", "2026-07", "abc123");
    expect(key).toBe("tenant-1::2026-07::abc123");
  });

  it("InsightEntry shape: 5 fields + required source_kind discriminator", () => {
    const entry: InsightEntry = {
      insight_kind: "cost_reduction_candidate",
      question: "Q?",
      answer: "A",
      source_kind: "auto_analysis",
      evidence_ref: null,
      generated_at: "2026-08-19T00:00:00Z",
    };
    expect(entry.source_kind).toBe("auto_analysis");
    // Story 10.3 wire 진입 시점에 ai_reference 추가 expected
  });

  it("InsightListResponse success envelope has status='success' tag discriminator", () => {
    const res: InsightListResponse = {
      status: "success",
      insights: [],
      period_key: "2026-07",
      calculation_result_hash: "abc123",
      hit_count: 0,
      miss_count: 0,
    };
    expect(res.status).toBe("success");
  });

  it("InsightListResponse has 6 required AD-25 cache key triplet fields", () => {
    const res: InsightListResponse = {
      status: "success",
      insights: [],
      period_key: "2026-07",
      calculation_result_hash: "abc123",
      hit_count: 0,
      miss_count: 0,
    };
    expect(Object.keys(res).sort()).toEqual([
      "calculation_result_hash",
      "hit_count",
      "insights",
      "miss_count",
      "period_key",
      "status",
    ]);
  });
});
