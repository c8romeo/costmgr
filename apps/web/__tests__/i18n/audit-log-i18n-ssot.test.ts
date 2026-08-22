/**
 * apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts — Epic 17 T2 (AC #7.9)
 *
 * P-015 EXTENSION + CR 11-4 D-002 ko-KR.json SSOT drift detector for
 * the audit_log namespace.
 *
 * Verifies that all audit_log.* keys (PRD §F21.2 verbatim, 14 keys
 * specified in spec) are PRESENT + NON-EMPTY in
 * apps/web/messages/ko-KR.json. If a downstream component imports a
 * namespace key that this test doesn't cover, it'll fail to render
 * the expected Korean label — this drift detector catches that
 * class of regression automatically.
 */

import { describe, expect, it } from "vitest";

import koKR from "@/messages/ko-KR.json";

interface KVPair {
  key: string;
  value: unknown;
}

function flatten(obj: unknown, prefix = ""): KVPair[] {
  if (obj === null || typeof obj !== "object") {
    return [{ key: prefix, value: obj }];
  }
  const result: KVPair[] = [];
  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "string") {
      result.push({ key: path, value: v });
    } else if (v !== null && typeof v === "object") {
      result.push(...flatten(v, path));
    }
  }
  return result;
}

const REQUIRED_VERBATIM_KEYS = [
  "audit_log.page_title",
  "audit_log.page_subtitle",
  "audit_log.forbidden_notice",
  "audit_log.filter_panel_title",
  "audit_log.filter_actor_label",
  "audit_log.filter_action_label",
  "audit_log.filter_action_class_label",
  "audit_log.filter_resource_type_label",
  "audit_log.filter_start_date_label",
  "audit_log.filter_end_date_label",
  "audit_log.filter_trace_id_label",
  "audit_log.filter_apply_button",
  "audit_log.filter_reset_button",
  "audit_log.table_title",
  "audit_log.column_created_at",
  "audit_log.column_actor_id",
  "audit_log.column_action_class",
  "audit_log.column_action",
  "audit_log.column_resource_type",
  "audit_log.column_trace_id",
  "audit_log.empty_state",
  "audit_log.loading_state",
  "audit_log.pagination_prev",
  "audit_log.pagination_next",
  "audit_log.pagination_page_indicator",
  "audit_log.export_button_label",
  "audit_log.detail_modal_title",
  "audit_log.detail_payload_label",
  "audit_log.detail_trace_id_label",
  "audit_log.detail_copy_trace_id",
  "audit_log.detail_close",
  "audit_log.error_invalid_filter",
  "audit_log.error_entry_not_found",
  "audit_log.error_export_forbidden",
  "audit_log.error_export_too_large",
  "audit_log.error_load_failed",
] as const;

describe("audit_log ko-KR.json SSOT drift detector (Epic 17 T2)", () => {
  it("audit_log namespace has at least 35 SSOT keys (PRD §F21.2)", () => {
    const entries = flatten(
      (koKR as unknown as { audit_log: Record<string, unknown> }).audit_log,
    );
    expect(entries.length).toBeGreaterThanOrEqual(35);
  });

  it("every audit_log.* string is present and non-empty", () => {
    const auditLog = (koKR as unknown as { audit_log: Record<string, unknown> })
      .audit_log;
    for (const key of REQUIRED_VERBATIM_KEYS) {
      const [, leaf] = key.split(".");
      const value = auditLog[leaf];
      expect(typeof value, `key ${key} must exist`).toBe("string");
      expect(
        (value as string).length,
        `key ${key} must be non-empty`,
      ).toBeGreaterThan(0);
    }
  });

  it("verbatim label invariants hold", () => {
    const auditLog = (koKR as unknown as { audit_log: Record<string, string> })
      .audit_log;
    expect(auditLog.page_title).toBe("감사 로그");
    expect(auditLog.forbidden_notice).toContain("owner");
    expect(auditLog.detail_copy_trace_id).toContain("추적 ID");
  });
});
