/**
 * apps/web/__tests__/i18n/activity-i18n-ssot.test.ts — Epic 17 T3 (AC #7.10)
 *
 * P-015 EXTENSION + CR 11-4 D-002 ko-KR.json SSOT drift detector for
 * the activity namespace.
 *
 * Verifies that all activity.* keys (PRD §F21.3 verbatim, 8 keys
 * specified in spec) are PRESENT + NON-EMPTY in
 * apps/web/messages/ko-KR.json.
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
  "activity.page_title",
  "activity.page_subtitle",
  "activity.window_selector_label",
  "activity.window_day_1",
  "activity.window_day_7",
  "activity.window_day_30",
  "activity.window_day_90",
  "activity.bucket_entry_count",
  "activity.bucket_top_actions_label",
  "activity.bucket_top_actors_label",
  "activity.entry_view_detail",
  "activity.empty_state",
  "activity.loading_state",
  "activity.error_load_failed",
] as const;

describe("activity ko-KR.json SSOT drift detector (Epic 17 T3)", () => {
  it("activity namespace has at least 13 SSOT keys (PRD §F21.3)", () => {
    const entries = flatten(
      (koKR as unknown as { activity: Record<string, unknown> }).activity,
    );
    expect(entries.length).toBeGreaterThanOrEqual(13);
  });

  it("every activity.* string is present and non-empty", () => {
    const activity = (koKR as unknown as { activity: Record<string, unknown> })
      .activity;
    for (const key of REQUIRED_VERBATIM_KEYS) {
      const [, leaf] = key.split(".");
      const value = activity[leaf];
      expect(typeof value, `key ${key} must exist`).toBe("string");
      expect(
        (value as string).length,
        `key ${key} must be non-empty`,
      ).toBeGreaterThan(0);
    }
  });

  it("verbatim label invariants hold", () => {
    const activity = (koKR as unknown as { activity: Record<string, string> })
      .activity;
    expect(activity.page_title).toBe("활동 스트림");
    expect(activity.window_day_1).toBe("최근 1일");
    expect(activity.window_day_7).toBe("최근 7일");
    expect(activity.window_day_30).toBe("최근 30일");
    expect(activity.window_day_90).toBe("최근 90일");
    expect(activity.bucket_entry_count).toContain("건");
  });
});
