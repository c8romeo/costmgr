/**
 * apps/web/__tests__/lib/ai-comment-parity.test.ts — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * AD-15 cross-language parity test for ai-comments.ts (TS mirror) vs
 * apps/api/modules/m10_ai/schemas.py Story 10.3 EXTENSION.
 */

import { describe, expect, it } from "vitest";

import {
  AI_COMMENT_KIND_VALUES,
  AI_COMMENT_SOURCE_KIND_WARNING,
  isAICommentError,
  isAICommentListSuccess,
  isSourceKind,
  type AICommentEntry,
  type AICommentListResponse,
} from "@/lib/ai-comments";

describe("ai-comments parity — Sprint 10.5 T3", () => {
  it("AI_COMMENT_KIND_VALUES has 5 kinds (10-3 forward-fill 2 NEW: risk_warning, industry_benchmark)", () => {
    expect(AI_COMMENT_KIND_VALUES).toEqual([
      "cost_reduction_candidate",
      "anomaly_pattern",
      "forecast",
      "risk_warning",
      "industry_benchmark",
    ]);
  });

  it("isSourceKind accepts ONLY 'auto_analysis' or 'ai_reference'", () => {
    expect(isSourceKind("auto_analysis")).toBe(true);
    expect(isSourceKind("ai_reference")).toBe(true);
    expect(isSourceKind("unknown_source")).toBe(false);
    expect(isSourceKind("")).toBe(false);
    expect(isSourceKind(null)).toBe(false);
    expect(isSourceKind(42)).toBe(false);
  });

  it("AI_COMMENT_SOURCE_KIND_WARNING envelope name is verbatim", () => {
    expect(AI_COMMENT_SOURCE_KIND_WARNING).toBe("AI_COMMENT_SOURCE_KIND_WARNING");
  });

  it("AICommentEntry carries source_kind + comment_kind as discriminator tags", () => {
    const entry: AICommentEntry = {
      comment_id: "c-1",
      comment_kind: "cost_reduction_candidate",
      body_text: "test",
      source_kind: "auto_analysis",
      evidence_ref: null,
      generated_at: "2026-08-19T00:00:00Z",
    };
    expect(isSourceKind(entry.source_kind)).toBe(true);
    expect(AI_COMMENT_KIND_VALUES).toContain(entry.comment_kind);
  });

  it("AICommentListResponse success envelope has status='success' tag discriminator", () => {
    const res: AICommentListResponse = {
      status: "success",
      comments: [],
      period_key: "2026-07",
      calculation_result_hash: "abc123",
      hit_count: 0,
      miss_count: 0,
      counter_total: 0,
    };
    expect(res.status).toBe("success");
    expect(isAICommentListSuccess(res)).toBe(true);
  });

  it("error envelope detection via isAICommentError", () => {
    const err = {
      status: "error" as const,
      error_code: "AI_COMMENT_SOURCE_KIND_INVALID" as const,
      message_ko: "test",
      details: {},
      trace_id: "tr-1",
    };
    expect(isAICommentError(err)).toBe(true);
    expect(isAICommentListSuccess(err)).toBe(false);
  });

  it("auto_analysis read-only guard invariant — frontend MUST NOT provide modify path", async () => {
    // F10.2-(c) verbatim: ai-comments.ts does NOT export any modify/edit
    // function — only fetch (read-only). This guards against future drift
    // where someone adds a `modifyAIComment(...)` function.
    const mod = await import("@/lib/ai-comments");
    const moduleKeys = Object.keys(mod);
    expect(moduleKeys).not.toContain("modifyAIComment");
    expect(moduleKeys).not.toContain("updateAIComment");
    expect(moduleKeys).not.toContain("deleteAIComment");
  });
});
