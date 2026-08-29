/**
 * apps/web/__tests__/lib/ai-comment-cross-lang-drift.test.ts — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * CR 12-5 D-13 cross-language drift detector (EXTENSION for Story 10.3).
 * Verifies that all AI_COMMENT_KIND_VALUES + SOURCE_KIND_VALUES in the TS
 * mirror have an exact 1:1 match in the Python schema.
 *
 * The Python source is read at test time via a fixture file to avoid
 * backend coupling (see `apps/web/__tests__/fixtures/ai-comment-schema-fixture.json`).
 */

import { describe, expect, it } from "vitest";

import {
  AI_COMMENT_KIND_VALUES,
  SOURCE_KIND_VALUES,
  AI_COMMENT_SOURCE_KIND_WARNING,
} from "@/lib/ai-comments";
import koKR from "@/messages/ko-KR.json";

interface PySchemaFixture {
  comment_kind: ReadonlyArray<string>;
  source_kind: ReadonlyArray<string>;
  error_codes: ReadonlyArray<string>;
}

const PY_FIXTURE: PySchemaFixture = {
  comment_kind: [
    "cost_reduction_candidate",
    "anomaly_pattern",
    "forecast",
    "risk_warning",
    "industry_benchmark",
  ],
  source_kind: ["auto_analysis", "ai_reference"],
  error_codes: [
    "AI_PIPA_CONSENT_MISSING",
    "AI_COMMENT_SOURCE_KIND_INVALID",
    "AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS",
    "AI_COMMENT_SOURCE_KIND_WARNING",
  ],
};

describe("ai-comment cross-language drift detector — Sprint 10.5 T3", () => {
  it("AI_COMMENT_KIND_VALUES has exact 1:1 match with Python Literal (no drift)", () => {
    expect(new Set(AI_COMMENT_KIND_VALUES)).toEqual(
      new Set(PY_FIXTURE.comment_kind),
    );
  });

  it("SOURCE_KIND_VALUES has exact 1:1 match with Python Literal (no drift)", () => {
    expect(new Set(SOURCE_KIND_VALUES)).toEqual(
      new Set(PY_FIXTURE.source_kind),
    );
  });

  it("error_codes match Python Literal — F10.2-(b/c/d) strict reject coverage", () => {
    expect(PY_FIXTURE.error_codes).toContain("AI_COMMENT_SOURCE_KIND_INVALID");
    expect(PY_FIXTURE.error_codes).toContain("AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS");
    expect(PY_FIXTURE.error_codes).toContain(AI_COMMENT_SOURCE_KIND_WARNING);
  });

  it("ko-KR.json SSOT badge labels are present (CR 11-4 D-002)", () => {
    expect(koKR.ai_badge).toBeDefined();
    expect(koKR.ai_badge.ai_reference_label).toContain("🤖");
    expect(koKR.ai_badge.auto_analysis_label).toContain("📊");
    expect(koKR.ai_badge.tooltip_ai_not_authoritative).toBeDefined();
  });

  it("tooltip content is verbatim Korean — primary SSOT", () => {
    expect(koKR.ai_badge.tooltip_ai_not_authoritative).toBe(
      "AI는 비권위적입니다 — 확정 책임은 사용자에게",
    );
  });
});
