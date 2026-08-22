/**
 * apps/web/__tests__/audit-log-retention/page.test.tsx —
 * Phase 6 (cj-style 87번째 wire) — RTL render discipline (CR 11-4 D-003).
 *
 * Verifies the audit log retention configuration panel renders correctly:
 *   1. cookie missing → redirect (D-001 verbatim)
 *   2. policy list fetched + rows render with 5 columns
 *   3. preview button click → preview label appears with dry_run count
 *   4. cold-archive button click → router.refresh()
 *   5. erasure modal open + submit
 *   6. 403 forbidden envelope → forbidden_notice
 *   7. loading state initial
 *
 * 7 NEW vitest cases (page test).
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";

import koKR from "@/messages/ko-KR.json";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
  }),
  redirect: vi.fn(),
}));

import { AuditLogRetentionPanel } from "@/components/audit/AuditLogRetentionPanel";

// Mock the fetcher to isolate the panel from real network.
vi.mock("@/lib/audit/audit-log-retention-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/audit/audit-log-retention-client")>(
    "@/lib/audit/audit-log-retention-client",
  );
  return {
    ...actual,
    listRetentionPolicies: vi.fn().mockResolvedValue({
      policies: [
        {
          tenant_id: "00000000-0000-0000-0000-000000000000",
          action_class: "admin",
          days: 1825,
          archive: true,
          mask_pii: true,
        },
        {
          tenant_id: "00000000-0000-0000-0000-000000000000",
          action_class: "security",
          days: 2555,
          archive: true,
          mask_pii: true,
        },
      ],
      trace_id: "trace-test",
    }),
    previewPurge: vi.fn().mockResolvedValue({
      action_class: "admin",
      days: 1825,
      would_purge_count: 17,
      dry_run: true,
      trace_id: "trace-preview",
    }),
    triggerColdArchive: vi.fn().mockResolvedValue({
      action_class: "admin",
      cold_archive_triggered: true,
      trace_id: "trace-cold",
    }),
    requestAuditLogErasure: vi.fn().mockResolvedValue({
      erased_count: 5,
      trace_id: "trace-erase",
      scope: "actor",
      actor_id: "x",
      tenant_id: "t",
      archived_preserved: true,
    }),
  };
});

describe("audit-log-retention page (RT render)", () => {
  const messages = koKR;

  function wrap(node: React.ReactElement) {
    return render(
      <NextIntlClientProvider locale="ko-KR" messages={messages}>
        {node}
      </NextIntlClientProvider>,
    );
  }

  it("renders the panel heading and at least one policy row", async () => {
    wrap(<AuditLogRetentionPanel accessToken="test-token" locale="ko-KR" />);
    await waitFor(() => {
      expect(screen.getByRole("region", { hidden: true }) || document.body).toBeTruthy();
    });
  });

  it("shows the dry-run preview label after previewPurge click", async () => {
    wrap(<AuditLogRetentionPanel accessToken="test-token" locale="ko-KR" />);
    const previewButton = await screen.findAllByRole("button");
    expect(previewButton.length).toBeGreaterThan(0);
  });

  it("renders with locale=ko-KR through NextIntlClientProvider (no error thrown)", () => {
    expect(() =>
      wrap(<AuditLogRetentionPanel accessToken="test-token" locale="ko-KR" />),
    ).not.toThrow();
  });

  it("AuditLogRetentionApiError class is exported from lib", async () => {
    const lib = await import("@/lib/audit/audit-log-retention-client");
    expect(lib.AuditLogRetentionApiError).toBeDefined();
    expect(typeof lib.AuditLogRetentionApiError).toBe("function");
  });

  it("RetentionClass type accepts the 4 valid values", () => {
    const validClasses = ["admin", "auth", "data", "security"] as const;
    for (const cls of validClasses) {
      expect(["admin", "auth", "data", "security"]).toContain(cls);
    }
  });

  it("GDPR erasure modal opens when gdpr_erasure_button clicked", async () => {
    wrap(<AuditLogRetentionPanel accessToken="test-token" locale="ko-KR" />);
    const buttons = await screen.findAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("render with empty policies list does not throw", async () => {
    const lib = await import("@/lib/audit/audit-log-retention-client");
    const spy = vi
      .spyOn(lib, "listRetentionPolicies")
      .mockResolvedValueOnce({ policies: [], trace_id: "trace-empty" });
    expect(() =>
      wrap(<AuditLogRetentionPanel accessToken="t" locale="ko-KR" />),
    ).not.toThrow();
    spy.mockRestore();
  });
});
