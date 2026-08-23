/**
 * apps/web/__tests__/i18n/slo-i18n-ssot.test.ts —
 * Phase 10 T7 (cj-style 103번째 wire) — 2 NEW vitest cases verifying
 * that the SLO i18n keys in ko-KR.json form a complete SSOT (Single
 * Source Of Truth) — every UI-visible label must have a ko-KR entry.
 *
 * CR 11-4 D-002 ko-KR SSOT lesson applied.
 */
import { describe, expect, it } from "vitest";

import koKR from "@/messages/ko-KR.json";

describe("slo i18n SSOT", () => {
  it("ko-KR.json includes slo.* namespace with required keys", () => {
    expect(koKR.slo).toBeDefined();
    expect(koKR.slo.page_title).toBeTruthy();
    expect(koKR.slo.page_subtitle).toBeTruthy();
    expect(koKR.slo.definition_list_title).toBeTruthy();
    expect(koKR.slo.error_budget_section_title).toBeTruthy();
    expect(koKR.slo.burn_rate_section_title).toBeTruthy();
    expect(koKR.slo.governance_section_title).toBeTruthy();
    expect(koKR.slo.freeze_section_title).toBeTruthy();
  });

  it("sli_type labels cover all 5 SliType enum values", () => {
    const labels = [
      koKR.slo.sli_type_latency,
      koKR.slo.sli_type_availability,
      koKR.slo.sli_type_throughput,
      koKR.slo.sli_type_error_rate,
      koKR.slo.sli_type_freshness,
    ];
    for (const label of labels) {
      expect(typeof label).toBe("string");
      expect(label.length).toBeGreaterThan(0);
    }
  });
});
