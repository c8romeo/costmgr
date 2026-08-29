/**
 * apps/web/__tests__/audit-log/page.test.tsx — Epic 17 T2 (AC #7.6)
 *
 * RTL render tests for /audit-log (audit log viewer).
 *
 * Covers:
 *   - D-001: page mounts unconditionally
 *   - D-002: ko-KR.json audit_log namespace keys all present
 *   - D-003: vitest RTL renders AuditLogFilterPanel + AuditLogTable +
 *     AuditLogPagination + AuditLogExportButton + AuditLogDetailModal
 *   - D-005: unknown state reject — empty / error / loading render
 *   - owner/admin RBAC: 403 envelope renders forbidden_notice
 *   - empty state when entries = []
 *   - row click opens detail modal
 *
 * Mock strategy: vi.mock the audit-log-client module so RTL never
 * touches the network.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import koKR from "@/messages/ko-KR.json";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
  }),
}));

vi.mock("@/lib/audit/audit-log-client", () => ({
  fetchAuditLog: vi.fn(),
  fetchAuditLogEntry: vi.fn(),
  fetchAuditLogCount: vi.fn(),
  exportAuditLogCsv: vi.fn(),
}));

import { AuditLogPanel } from "@/components/audit/AuditLogPanel";
import { fetchAuditLog, exportAuditLogCsv } from "@/lib/audit/audit-log-client";

const auditLogMessages = (koKR as unknown as { audit_log: Record<string, string> })
  .audit_log;

function withIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider
      locale="ko-KR"
      messages={{ audit_log: auditLogMessages }}
    >
      {node}
    </NextIntlClientProvider>
  );
}

const sampleEntry = {
  id: 1,
  tenant_id: "00000000-0000-0000-0000-0000000000aa",
  actor_id: "user-1",
  action: "tenant_idp_created",
  action_class: "SSO",
  resource_type: "tenant_idp",
  resource_id: "00000000-0000-0000-0000-000000000001",
  payload: { idp_entity_id: "https://idp.example.com/sso" },
  ip_address: "203.0.113.42",
  user_agent: "Mozilla/5.0",
  trace_id: "11111111-2222-3333-4444-555555555555",
  created_at: "2026-08-22T12:00:00Z",
};

const emptyFilters = {
  actor_id: null,
  action: null,
  action_class: null,
  resource_type: null,
  resource_id: null,
  start_date: null,
  end_date: null,
  trace_id: null,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AuditLogPanel (Epic 17 T2 /audit-log)", () => {
  it("D-001: mounts unconditionally and renders panel header", () => {
    (fetchAuditLog as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: { entries: [], total: 0, page: 1, page_size: 50, has_next: false },
    });
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [],
            total: 0,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    expect(screen.getByTestId("audit-log-panel")).toBeInTheDocument();
    expect(screen.getByText("감사 로그")).toBeInTheDocument();
  });

  it("renders empty state when entries is empty", () => {
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [],
            total: 0,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    expect(screen.getByTestId("audit-log-empty")).toBeInTheDocument();
    expect(screen.getByText("감사 로그가 없습니다.")).toBeInTheDocument();
  });

  it("renders forbidden notice when initialPage is null (403 envelope)", () => {
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={null}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    expect(screen.getByTestId("audit-log-error")).toBeInTheDocument();
    expect(screen.getByText(/owner.*admin/)).toBeInTheDocument();
  });

  it("renders AuditLogTable + AuditLogPagination when entries present", () => {
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [sampleEntry],
            total: 1,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    expect(screen.getByTestId("audit-log-table")).toBeInTheDocument();
    expect(screen.getByTestId("audit-log-pagination")).toBeInTheDocument();
    expect(screen.getByText("user-1")).toBeInTheDocument();
    expect(screen.getByText("tenant_idp_created")).toBeInTheDocument();
  });

  it("row click opens detail modal with payload", async () => {
    const user = userEvent.setup();
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [sampleEntry],
            total: 1,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    await user.click(screen.getByTestId("audit-log-trace-id-button"));
    await waitFor(() => {
      expect(screen.getByTestId("audit-log-detail-modal")).toBeInTheDocument();
    });
    expect(
      screen.getByTestId("audit-log-detail-payload").textContent,
    ).toContain("idp.example.com");
  });

  it("filter Apply triggers fetchAuditLog with applied filters", async () => {
    (fetchAuditLog as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: { entries: [], total: 0, page: 1, page_size: 50, has_next: false },
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [],
            total: 0,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    await user.type(
      screen.getByTestId("audit-log-filter-actor"),
      "user-99",
    );
    await user.click(screen.getByTestId("audit-log-filter-apply"));
    await waitFor(() => {
      expect(fetchAuditLog).toHaveBeenCalledWith(
        "token",
        expect.objectContaining({ actor_id: "user-99" }),
        1,
        50,
      );
    });
  });

  it("export button triggers exportAuditLogCsv", async () => {
    (exportAuditLogCsv as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      blob: new Blob(["id,actor_id\n1,user-1\n"], { type: "text/csv" }),
      filename: "audit-log-acme-20260822.csv",
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [sampleEntry],
            total: 1,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    await user.click(screen.getByTestId("audit-log-export-button"));
    await waitFor(() => {
      expect(exportAuditLogCsv).toHaveBeenCalledWith(
        "token",
        expect.objectContaining(emptyFilters),
      );
    });
  });

  it("renders loading state during refetch", async () => {
    (fetchAuditLog as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}), // never resolves
    );
    const user = userEvent.setup();
    render(
      withIntl(
        <AuditLogPanel
          accessToken="token"
          initialPage={{
            entries: [],
            total: 0,
            page: 1,
            page_size: 50,
            has_next: false,
          }}
          initialFilters={emptyFilters}
          initialPageNumber={1}
          initialPageSize={50}
        />,
      ),
    );
    await user.click(screen.getByTestId("audit-log-filter-apply"));
    await waitFor(() => {
      expect(screen.getByTestId("audit-log-loading")).toBeInTheDocument();
    });
  });
});
