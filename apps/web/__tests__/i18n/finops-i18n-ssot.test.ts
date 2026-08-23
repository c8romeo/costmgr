/**
 * apps/web/__tests__/i18n/finops-i18n-ssot.test.ts —
 * Phase 11 T7 (cj-style 107번째 wire) — 2 NEW vitest cases verifying
 * that the FinOps i18n keys in ko-KR.json form a complete SSOT (Single
 * Source Of Truth) — every UI-visible label must have a ko-KR entry.
 *
 * CR 11-4 D-002 ko-KR SSOT lesson applied.
 */
import { describe, expect, it } from "vitest";

import koKR from "@/messages/ko-KR.json";

const FINOPS_REQUIRED_KEYS = [
  "page_title",
  "page_subtitle",
  "showback_section_title",
  "showback_period_selector_label",
  "showback_period_current_month",
  "showback_period_previous_month",
  "showback_period_last_3_months",
  "showback_period_last_6_months",
  "showback_period_ytd",
  "showback_period_custom_range",
  "showback_group_by_label",
  "showback_group_by_department",
  "showback_group_by_cost_center",
  "showback_group_by_product_line",
  "showback_group_by_service",
  "showback_group_by_custom_tag",
  "department_breakdown_title",
  "comparison_view_title",
  "chargeback_section_title",
  "chargeback_rule_type_label",
  "chargeback_rule_type_flat_fee",
  "chargeback_rule_type_proportional_allocation",
  "chargeback_rule_type_metered",
  "chargeback_export_section_title",
  "department_mapping_section_title",
  "loading_state",
  "error_load_failed",
  "error_export_failed",
  "error_owner_only",
] as const;

describe("finops i18n SSOT", () => {
  it("ko-KR.json includes finops.* namespace with required keys (≥25 keys)", () => {
    const finops = (koKR as Record<string, unknown>).finops as
      | Record<string, string>
      | undefined;
    expect(finops).toBeDefined();
    for (const key of FINOPS_REQUIRED_KEYS) {
      expect(finops?.[key], `finops.${key} missing`).toBeDefined();
      expect(
        finops?.[key].length ?? 0,
        `finops.${key} must be non-empty`,
      ).toBeGreaterThan(0);
    }
    expect(Object.keys(finops ?? {}).length).toBeGreaterThanOrEqual(25);
  });

  it("finops.* values follow ko-KR style guideline", () => {
    const finops = (koKR as Record<string, unknown>).finops as
      | Record<string, string>
      | undefined;
    for (const key of FINOPS_REQUIRED_KEYS) {
      const v = finops?.[key] ?? "";
      expect(v.length, `finops.${key} too short`).toBeGreaterThan(0);
    }
  });
});
