/**
 * apps/web/__tests__/lib/ko-kr-json-ssot-drift.test.ts — Sprint 10.5 T5 wire (A38 AC #5)
 *                                  Epic 16 T4 (A117 sweep)
 *
 * P-015 EXTENSION (A38 spec + Epic 16 T4 sweep): ko-KR.json SSOT drift detector.
 *
 * Verifies that all m10-ai (Epic 10) namespace keys are PRESENT + NON-EMPTY
 * in apps/web/messages/ko-KR.json. If a downstream component imports a
 * namespace key that this test doesn't cover, it'll fail to render the
 * expected Korean label — this drift detector catches that class of
 * regression automatically.
 *
 * 5 namespaces covered:
 *   - ai_extract (10-1)
 *   - insight_cache (10-2)
 *   - ai_badge (10-3) — note: NOT ai_comments (overlapping with badge separation)
 *   - ai_promote (10-4)
 *   - settings_sso (Epic 16 T4) — NEW for cj-style 71번째 wire
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

const REQUIRED_NAMESPACES = {
  ai_extract: 25,    // 10-1 minimum SSOT strings
  insight_cache: 15, // 10-2 minimum SSOT strings
  ai_badge: 8,       // 10-3 badge labels + tooltip
  ai_promote: 12,    // 10-4 promote error messages + status labels
  settings_sso: 45,  // Epic 16 T4 (cj-style 71번째) — SSOT strings for /settings/sso page
} as const;

describe("ko-KR.json SSOT drift detector — Sprint 10.5 T5 (P-015) + Epic 16 T4 sweep", () => {
  it("ai_extract namespace has minimum SSOT string coverage", () => {
    const entries = flatten(koKR.ai_extract);
    expect(entries.length).toBeGreaterThanOrEqual(REQUIRED_NAMESPACES.ai_extract);
    for (const { value } of entries) {
      expect(typeof value).toBe("string");
      expect((value as string).length).toBeGreaterThan(0);
    }
  });

  it("insight_cache namespace has minimum SSOT string coverage", () => {
    const entries = flatten(koKR.insight_cache);
    expect(entries.length).toBeGreaterThanOrEqual(REQUIRED_NAMESPACES.insight_cache);
    for (const { value } of entries) {
      expect(typeof value).toBe("string");
      expect((value as string).length).toBeGreaterThan(0);
    }
  });

  it("ai_badge namespace has minimum SSOT string coverage", () => {
    const entries = flatten(koKR.ai_badge);
    expect(entries.length).toBeGreaterThanOrEqual(REQUIRED_NAMESPACES.ai_badge);
    // tooltip MUST have specific verbatim value (PRD §13.1 ko-KR SSOT)
    expect(koKR.ai_badge.tooltip_ai_not_authoritative).toBe(
      "AI는 비권위적입니다 — 확정 책임은 사용자에게",
    );
    // emoji markers MUST be present in labels
    expect(koKR.ai_badge.ai_reference_label).toContain("🤖");
    expect(koKR.ai_badge.auto_analysis_label).toContain("📊");
  });

  it("ai_promote namespace has minimum SSOT string coverage", () => {
    const entries = flatten(koKR.ai_promote);
    expect(entries.length).toBeGreaterThanOrEqual(REQUIRED_NAMESPACES.ai_promote);
    for (const { value } of entries) {
      expect(typeof value).toBe("string");
      expect((value as string).length).toBeGreaterThan(0);
    }
  });

  it("settings_sso namespace (Epic 16 T4) has minimum SSOT string coverage", () => {
    const entries = flatten(koKR.settings_sso);
    expect(entries.length).toBeGreaterThanOrEqual(
      REQUIRED_NAMESPACES.settings_sso,
    );
    for (const { value } of entries) {
      expect(typeof value).toBe("string");
      expect((value as string).length).toBeGreaterThan(0);
    }
    // Required verbatim labels (Epic 16 T4 SSOT invariants)
    expect(koKR.settings_sso.page_title).toBe("SSO / IdP 설정");
    expect(koKR.settings_sso.tenant_slug_required).toContain("tenant");
    expect(koKR.settings_sso.forbidden_notice).toContain("owner");
    expect(koKR.settings_sso.field_metadata_xml).toBe("Metadata XML");
    expect(koKR.settings_sso.field_x509_cert_pem).toContain("X.509");
  });

  it("ko-KR.json MUST NOT contain TODO / FIXME placeholder strings", () => {
    const all = flatten(koKR);
    for (const { key, value } of all) {
      if (typeof value !== "string") continue;
      expect(value, `Found TODO/FIXME placeholder at ${key}`).not.toMatch(
        /TODO|FIXME|\bTBD\b/,
      );
    }
  });
});
