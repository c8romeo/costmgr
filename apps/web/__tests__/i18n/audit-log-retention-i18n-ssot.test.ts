/**
 * apps/web/__tests__/i18n/audit-log-retention-i18n-ssot.test.ts —
 * Phase 6 (cj-style 87번째 wire) — SSOT drift detector (CR 11-4 D-002 + P-015).
 *
 * Verifies the i18n keys required by AuditLogRetentionPanel +
 * AuditLogRetentionPage are present in ko-KR.json with non-empty values.
 * Drift catches missing keys during development.
 *
 * 3 NEW SSOT drift cases (minimum keys + presence + non-empty + verbatim
 * label invariants).
 */

import { describe, it, expect } from "vitest";

import koKR from "@/messages/ko-KR.json";

const retention = (koKR as Record<string, unknown>)["audit_log_retention"] as
  | Record<string, string>
  | undefined;

describe("audit_log_retention i18n SSOT", () => {
  it("audit_log_retention namespace exists and has at least 24 keys", () => {
    expect(retention).toBeDefined();
    expect(Object.keys(retention ?? {}).length).toBeGreaterThanOrEqual(24);
  });

  it("every required key is present and non-empty", () => {
    const required = [
      "page_title",
      "page_subtitle",
      "forbidden_notice",
      "panel_heading",
      "column_action_class",
      "column_days",
      "column_archive",
      "column_mask_pii",
      "column_actions",
      "preview_button",
      "cold_archive_button",
      "gdpr_erasure_button",
      "loading_state",
      "preview_label",
      "erasure_modal_title",
      "erasure_actor_id_label",
      "erasure_scope_label",
      "erasure_scope_actor",
      "erasure_scope_tenant",
      "erasure_scope_all",
      "erasure_reason_label",
      "erasure_submit_button",
      "erasure_close_button",
      "error_invalid_policy",
      "error_load_failed",
      "error_erasure_forbidden",
      "error_erasure_not_found",
      "empty_state",
    ];
    for (const key of required) {
      expect(retention?.[key], `key ${key} missing`).toBeDefined();
      expect(retention?.[key]?.length ?? 0, `key ${key} empty`).toBeGreaterThan(0);
    }
  });

  it("label invariants match Phase 6 spec verbatim", () => {
    expect(retention?.["page_title"]).toBe("감사 로그 보존 정책");
    expect(retention?.["gdpr_erasure_button"]).toContain("GDPR");
    expect(retention?.["cold_archive_button"]).toContain("콜드");
    expect(retention?.["preview_button"]).toContain("미리보기");
  });
});
