// apps/web/__tests__/i18n/performance-ko-KR-ssot.test.ts — ko-KR verbatim SSOT.
//
// 3 NEW vitest cases PASS (Phase 8 cj-style 95번째 wire frontend tests).
import { describe, expect, it } from "vitest";
import koKR from "@/messages/ko-KR.json";

describe("i18n: performance ko-KR SSOT — Phase 8 F24", () => {
  it("sla_dashboard_title is ko-KR verbatim", () => {
    const performance = koKR.performance as Record<string, string>;
    expect(performance.sla_dashboard_title).toBe("SLO 대시보드");
  });

  it("p99_regression banner copy is ko-KR verbatim", () => {
    const performance = koKR.performance as Record<string, string>;
    expect(performance.p99_regression_banner_title).toBeTruthy();
    expect(performance.p99_regression_banner_title).toMatch(/p99|회귀/);
  });

  it("k6 load test trigger button is owner-only RBAC AD-22 verbatim", () => {
    const performance = koKR.performance as Record<string, string>;
    expect(performance.k6_load_test_trigger_button).toBeTruthy();
    // AD-22 + Epic 12 2FA 챌린지 보존.
    expect(performance.k6_load_test_owner_only_notice).toContain("owner");
  });
});
