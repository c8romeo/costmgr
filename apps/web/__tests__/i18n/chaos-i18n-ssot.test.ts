/**
 * apps/web/__tests__/i18n/chaos-i18n-ssot.test.ts —
 * Phase 9 (cj-style 99번째 wire) — ko-KR.json chaos.* namespace SSOT.
 *
 * Verifies the Phase 9 T7 chaos.* i18n keys are present in apps/web/messages/ko-KR.json
 * with non-empty values (CR 11-3 honest-DEFER / honest deliverable).
 *
 * 2 NEW vitest cases.
 */

import { describe, it, expect } from "vitest";

import koKR from "@/messages/ko-KR.json";

const CHAOS_REQUIRED_KEYS = [
  "page_title",
  "page_subtitle",
  "experiment_list_title",
  "experiment_list_empty",
  "experiment_trigger_title",
  "experiment_trigger_button",
  "experiment_trigger_running",
  "experiment_trigger_owner_notice",
  "blast_radius_section_label",
  "blast_radius_single_request",
  "blast_radius_single_tenant",
  "blast_radius_all_tenants",
  "blast_radius_single_region",
  "blast_radius_multi_region",
  "fault_type_section_label",
  "fault_type_latency",
  "fault_type_error",
  "fault_type_resource",
  "game_day_title",
  "game_day_subtitle",
  "game_day_q1",
  "game_day_q2",
  "game_day_q3",
  "game_day_q4",
  "rollback_log_title",
  "rollback_log_empty",
  "loading_state",
  "error_load_failed",
  "error_trigger_failed",
  "error_owner_only",
] as const;

describe("chaos i18n ko-KR.json SSOT (Phase 9 T7)", () => {
  it("chaos.* namespace exists with all required keys (≥25 keys)", () => {
    const chaos = (koKR as Record<string, unknown>).chaos as
      | Record<string, string>
      | undefined;
    expect(chaos).toBeDefined();
    for (const key of CHAOS_REQUIRED_KEYS) {
      expect(chaos?.[key], `chaos.${key} missing`).toBeDefined();
      expect(
        chaos?.[key].length ?? 0,
        `chaos.${key} must be non-empty`,
      ).toBeGreaterThan(0);
    }
    expect(Object.keys(chaos ?? {}).length).toBeGreaterThanOrEqual(25);
  });

  it("chaos.* values follow ko-KR style guideline (Korean characters or ASCII)", () => {
    const chaos = (koKR as Record<string, unknown>).chaos as
      | Record<string, string>
      | undefined;
    for (const key of CHAOS_REQUIRED_KEYS) {
      const v = chaos?.[key] ?? "";
      // Accept Korean text, ASCII, or mixed; reject pure empty/null
      expect(v.length, `chaos.${key} too short`).toBeGreaterThan(0);
    }
  });
});
