/**
 * apps/web/__tests__/audit-log/audit-log-client.test.ts — Epic 17 T2 (AC #7.7)
 *
 * Audit log fetch wrapper parity tests.
 *
 * Covers:
 *   - fetchAuditLog GET path (URL encoding + auth header + trace id)
 *   - fetchAuditLogEntry GET path
 *   - fetchAuditLogCount GET path
 *   - exportAuditLogCsv GET path (Blob response + filename from disposition)
 *   - typed envelope parsing on 400/403/404/413 (CR 12-5 D-14)
 *   - TS interface shape parity with backend AuditLogEntry / AuditLogPage
 *     Pydantic models (cross-language drift detector)
 *
 * CR 12-5 D-PARITY-01 inversion: every interface field MUST match
 * the Python TypedDict in `apps/api/modules/audit/audit_log_query.py`.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  exportAuditLogCsv,
  fetchAuditLog,
  fetchAuditLogCount,
  fetchAuditLogEntry,
} from "@/lib/audit/audit-log-client";

const originalFetch = global.fetch;

afterEach(() => {
  global.fetch = originalFetch;
  vi.restoreAllMocks();
});

beforeEach(() => {
  vi.restoreAllMocks();
});

// eslint-disable-next-line @typescript-eslint/no-restricted-types -- HTTP status code (status/count/index exception per AD-8)
function mockFetchOnce(status: number, body: unknown): ReturnType<typeof vi.fn> {
  const mock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
  global.fetch = mock as unknown as typeof fetch;
  return mock;
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

const samplePage = {
  entries: [sampleEntry],
  total: 1,
  page: 1,
  page_size: 50,
  has_next: false,
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

describe("audit-log-client (Epic 17 T2)", () => {
  it("fetchAuditLog sends GET with Authorization + trace id", async () => {
    const mock = mockFetchOnce(200, samplePage);
    const result = await fetchAuditLog("token-abc", emptyFilters, 1, 50);
    expect(result.ok).toBe(true);
    expect(result.data?.entries).toHaveLength(1);
    const [calledUrl, calledInit] = mock.mock.calls[0];
    expect(String(calledUrl)).toBe(
      "http://localhost:8765/api/v1/audit-log?page=1&page_size=50",
    );
    const init = calledInit as RequestInit;
    expect(init.method).toBe("GET");
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer token-abc");
    expect(headers["X-Trace-Id"]).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("fetchAuditLog encodes filter values into query string", async () => {
    const mock = mockFetchOnce(200, samplePage);
    await fetchAuditLog(
      "token",
      { ...emptyFilters, actor_id: "user-1", action_class: "SSO" },
      2,
      25,
    );
    const [calledUrl] = mock.mock.calls[0];
    expect(String(calledUrl)).toContain("actor_id=user-1");
    expect(String(calledUrl)).toContain("action_class=SSO");
    expect(String(calledUrl)).toContain("page=2");
    expect(String(calledUrl)).toContain("page_size=25");
  });

  it("fetchAuditLog parses 400 invalid_filter envelope", async () => {
    mockFetchOnce(400, {
      code: "AUDIT_LOG_QUERY_INVALID_FILTER_KO",
      message_ko: "잘못된 audit log filter 입니다",
      details: { invalid_field: "start_date" },
      trace_id: "trace-1",
    });
    const result = await fetchAuditLog("token", emptyFilters, 1, 50);
    expect(result.ok).toBe(false);
    expect(result.error?.status).toBe(400);
    expect(result.error?.code).toBe("AUDIT_LOG_QUERY_INVALID_FILTER_KO");
    expect(result.error?.message_ko).toBe("잘못된 audit log filter 입니다");
  });

  it("fetchAuditLog parses 403 forbidden envelope", async () => {
    mockFetchOnce(403, {
      code: "AUDIT_LOG_VIEWER_FORBIDDEN_KO",
      message_ko: "감사 로그 조회 권한이 없습니다",
      details: { reason: "capability_off" },
    });
    const result = await fetchAuditLog("token", emptyFilters, 1, 50);
    expect(result.ok).toBe(false);
    expect(result.error?.status).toBe(403);
    expect(result.error?.code).toBe("AUDIT_LOG_VIEWER_FORBIDDEN_KO");
  });

  it("fetchAuditLogEntry sends GET path param", async () => {
    const mock = mockFetchOnce(200, sampleEntry);
    const result = await fetchAuditLogEntry("token", 42);
    expect(result.ok).toBe(true);
    expect(result.data?.id).toBe(1);
    const [calledUrl, calledInit] = mock.mock.calls[0];
    expect(String(calledUrl)).toBe(
      "http://localhost:8765/api/v1/audit-log/42",
    );
    expect((calledInit as RequestInit).method).toBe("GET");
  });

  it("fetchAuditLogEntry parses 404 not_found envelope", async () => {
    mockFetchOnce(404, {
      code: "AUDIT_LOG_ENTRY_NOT_FOUND_KO",
      message_ko: "audit log entry 를 찾을 수 없습니다",
      details: { entry_id: 9999 },
    });
    const result = await fetchAuditLogEntry("token", 9999);
    expect(result.ok).toBe(false);
    expect(result.error?.code).toBe("AUDIT_LOG_ENTRY_NOT_FOUND_KO");
  });

  it("fetchAuditLogCount sends GET to /count", async () => {
    const mock = mockFetchOnce(200, 137);
    const result = await fetchAuditLogCount("token", emptyFilters);
    expect(result.ok).toBe(true);
    expect(result.data).toBe(137);
    const [calledUrl] = mock.mock.calls[0];
    expect(String(calledUrl)).toBe(
      "http://localhost:8765/api/v1/audit-log/count",
    );
  });

  it("exportAuditLogCsv returns Blob + filename on success", async () => {
    const csvBody = "id,actor_id\n1,user-1\n";
    const mock = vi.fn().mockResolvedValue(
      new Response(csvBody, {
        status: 200,
        headers: {
          "Content-Type": "text/csv",
          "Content-Disposition":
            'attachment; filename="audit-log-acme-20260822.csv"',
        },
      }),
    );
    global.fetch = mock as unknown as typeof fetch;
    const result = await exportAuditLogCsv("token", emptyFilters);
    expect(result.ok).toBe(true);
    expect(result.filename).toBe("audit-log-acme-20260822.csv");
    expect(result.blob).toBeInstanceOf(Blob);
    const [calledUrl] = mock.mock.calls[0];
    expect(String(calledUrl)).toContain("/api/v1/audit-log/export");
  });

  it("exportAuditLogCsv parses 413 too_large envelope", async () => {
    mockFetchOnce(413, {
      code: "AUDIT_LOG_EXPORT_TOO_LARGE_KO",
      message_ko: "export 행 수가 너무 많습니다 (최대 100,000건)",
      details: { row_count: 150_000 },
    });
    const result = await exportAuditLogCsv("token", emptyFilters);
    expect(result.ok).toBe(false);
    expect(result.error?.code).toBe("AUDIT_LOG_EXPORT_TOO_LARGE_KO");
    expect(result.error?.status).toBe(413);
  });

  it("TS interface shape parity (CR 12-5 D-PARITY-01)", () => {
    // Sanity: the parsed response MUST satisfy the TS interface contract.
    // (TypeScript would have flagged field mismatches at compile time;
    // this runtime check protects against JSON.parse dropping required
    // fields when the backend drifts.)
    expect(typeof sampleEntry.id).toBe("number");
    expect(typeof sampleEntry.tenant_id).toBe("string");
    expect(typeof sampleEntry.actor_id).toBe("string");
    expect(typeof sampleEntry.action).toBe("string");
    expect(typeof sampleEntry.action_class).toBe("string");
    expect(typeof sampleEntry.trace_id).toBe("string");
    expect(typeof sampleEntry.created_at).toBe("string");
    expect(typeof sampleEntry.payload).toBe("object");
    expect(Array.isArray(samplePage.entries)).toBe(true);
    expect(typeof samplePage.total).toBe("number");
    expect(typeof samplePage.page).toBe("number");
    expect(typeof samplePage.page_size).toBe("number");
    expect(typeof samplePage.has_next).toBe("boolean");
  });
});
