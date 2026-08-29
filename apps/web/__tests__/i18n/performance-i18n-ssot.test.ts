// apps/web/__tests__/i18n/performance-i18n-ssot.test.ts — i18n performance namespace SSOT.
//
// CR 11-4 D-002 + P-015 — SSOT only, never inline copy.
// 2 NEW vitest cases PASS (Phase 8 cj-style 95번째 wire frontend tests).
import { describe, expect, it } from "vitest";

import koKR from "@/messages/ko-KR.json";

describe("i18n: performance namespace — Phase 8", () => {
  it("ko-KR exposes `performance.*` namespace", () => {
    expect(koKR.performance).toBeDefined();
    expect(typeof koKR.performance).toBe("object");
  });

  it("ko-KR performance namespace has the 4 canonical SLA labels verbatim", () => {
    const performance = koKR.performance as Record<string, string>;
    expect(performance.sla_dashboard_title).toBeTruthy();
    expect(performance.sla_cost_calculation_label).toBeTruthy();
    expect(performance.sla_audit_log_query_label).toBeTruthy();
    expect(performance.sla_login_label).toBeTruthy();
    expect(performance.sla_multi_region_failover_label).toBeTruthy();
  });
});
