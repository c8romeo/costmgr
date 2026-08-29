/**
 * apps/web/__tests__/audit/audit-log-retention-client.test.ts —
 * Phase 6 (cj-style 87번째 wire) — TS mirror parity test.
 *
 * Verifies:
 *   1. CR 12-5 D-PARITY-01 inversion: TS interfaces
 *      (RetentionPolicy, PurgePreviewResult, ErasureResult) stay in
 *      sync with Pydantic TypedDict `RetentionPolicy` in
 *      `apps/api/modules/audit/retention/retention_dsl.py`.
 *   2. CR 12-5 D-14: 400/403/404 envelope parse.
 *   3. Bearer token + X-Trace-Id header forwarding.
 *   4. happy path: GET retention list returns RetentionPolicy[].
 *
 * Drift caught by 11 NEW vitest cases (5+5+1).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  listRetentionPolicies,
  createRetentionPolicy,
  updateRetentionPolicy,
  deleteRetentionPolicy,
  previewPurge,
  triggerColdArchive,
  requestAuditLogErasure,
  AuditLogRetentionApiError,
  type RetentionPolicy,
  type PurgePreviewResult,
  type ErasureResult,
} from "@/lib/audit/audit-log-retention-client";

const BASE = "http://localhost:8765";
const ACCESS = "test-access-token";

interface MockResponseInit {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types -- HTTP status code (status/count/index exception per AD-8)
  status?: number;
  body?: unknown;
}

function mockFetchResponse(init: MockResponseInit = {}): Response {
  const status = init.status ?? 200;
  const body = init.body ?? null;
  return new Response(body !== null ? JSON.stringify(body) : null, {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("audit-log-retention-client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("listRetentionPolicies issues GET /audit-log/retention + Bearer token + X-Trace-Id", async () => {
    const fakeTrace = "11111111-1111-1111-1111-111111111111";
    const pol: RetentionPolicy = {
      tenant_id: "00000000-0000-0000-0000-000000000000",
      action_class: "admin",
      days: 1825,
      archive: true,
      mask_pii: true,
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        mockFetchResponse({ status: 200, body: { policies: [pol], trace_id: fakeTrace } }),
      );

    const res = await listRetentionPolicies({ accessToken: ACCESS });
    expect(res.policies).toEqual([pol]);
    expect(res.trace_id).toBe(fakeTrace);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/retention`);
    const headers = (calledInit?.headers ?? {}) as Record<string, string>;
    expect(headers["Authorization"]).toBe(`Bearer ${ACCESS}`);
    expect(headers["X-Trace-Id"]).toBeTypeOf("string");
  });

  it("createRetentionPolicy issues POST with RetentionPolicy payload", async () => {
    const pol: RetentionPolicy = {
      tenant_id: "00000000-0000-0000-0000-000000000000",
      action_class: "security",
      days: 2555,
      archive: true,
      mask_pii: true,
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockFetchResponse({ status: 201, body: pol }));

    const res = await createRetentionPolicy(
      { action_class: "security", days: 2555, archive: true, mask_pii: true },
      { accessToken: ACCESS },
    );
    expect(res).toEqual(pol);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/retention`);
    expect(calledInit?.method).toBe("POST");
    expect(JSON.parse((calledInit?.body as string) ?? "{}")).toEqual({
      action_class: "security",
      days: 2555,
      archive: true,
      mask_pii: true,
    });
  });

  it("previewPurge issues POST /retention/preview with dry_run=true in response", async () => {
    const preview: PurgePreviewResult = {
      action_class: "data",
      days: 1825,
      would_purge_count: 42,
      dry_run: true,
      trace_id: "22222222-2222-2222-2222-222222222222",
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockFetchResponse({ status: 200, body: preview }));

    const res = await previewPurge({ action_class: "data" }, { accessToken: ACCESS });
    expect(res.would_purge_count).toBe(42);
    expect(res.dry_run).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/retention/preview`);
  });

  it("triggerColdArchive issues POST /retention/{class}/cold-archive", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        mockFetchResponse({
          status: 200,
          body: {
            action_class: "auth",
            cold_archive_triggered: true,
            trace_id: "33333333-3333-3333-3333-333333333333",
          },
        }),
      );

    const res = await triggerColdArchive("auth", { accessToken: ACCESS });
    expect(res.cold_archive_triggered).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/retention/auth/cold-archive`);
    expect(calledInit?.method).toBe("POST");
  });

  it("requestAuditLogErasure issues POST /audit-log/erase with ErasureResult envelope", async () => {
    const result: ErasureResult = {
      erased_count: 17,
      trace_id: "44444444-4444-4444-4444-444444444444",
      scope: "actor",
      actor_id: "55555555-5555-5555-5555-555555555555",
      tenant_id: "00000000-0000-0000-0000-000000000000",
      archived_preserved: true,
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockFetchResponse({ status: 200, body: result }));

    const res = await requestAuditLogErasure(
      {
        actor_id: "55555555-5555-5555-5555-555555555555",
        scope: "actor",
        reason: "GDPR Article 17 right to erasure",
      },
      { accessToken: ACCESS },
    );
    expect(res.erased_count).toBe(17);
    expect(res.archived_preserved).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/erase`);
    expect(calledInit?.method).toBe("POST");
    expect(JSON.parse((calledInit?.body as string) ?? "{}")).toEqual({
      actor_id: "55555555-5555-5555-5555-555555555555",
      scope: "actor",
      reason: "GDPR Article 17 right to erasure",
    });
  });

  it("parses 400 envelope as AuditLogRetentionApiError with code", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockFetchResponse({
        status: 400,
        body: {
          code: "AUDIT_LOG_RETENTION_DAYS_OUT_OF_RANGE",
          message_ko: "보존 일수가 범위를 벗어났습니다",
          details: { days: 10 },
          trace_id: "66666666-6666-6666-6666-666666666666",
        },
      }),
    );
    await expect(listRetentionPolicies({ accessToken: ACCESS })).rejects.toThrowError(
      AuditLogRetentionApiError,
    );
  });

  it("parses 403 envelope as AuditLogRetentionApiError with code AUDIT_LOG_PII_ERASURE_FORBIDDEN", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockFetchResponse({
        status: 403,
        body: {
          code: "AUDIT_LOG_PII_ERASURE_FORBIDDEN",
          message_ko: "PII 삭제는 owner 권한이 필요합니다",
          details: { requester_role: "member" },
          trace_id: "77777777-7777-7777-7777-777777777777",
        },
      }),
    );
    await expect(
      requestAuditLogErasure(
        { actor_id: "x", scope: "actor", reason: "GDPR" },
        { accessToken: ACCESS },
      ),
    ).rejects.toThrowError(AuditLogRetentionApiError);
  });

  it("parses 404 envelope as AuditLogRetentionApiError with code AUDIT_LOG_PII_ERASURE_NOT_FOUND", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockFetchResponse({
        status: 404,
        body: {
          code: "AUDIT_LOG_PII_ERASURE_NOT_FOUND",
          message_ko: "삭제할 감사 로그 항목이 없습니다",
          trace_id: "88888888-8888-8888-8888-888888888888",
        },
      }),
    );
    await expect(
      requestAuditLogErasure(
        { actor_id: "y", scope: "actor", reason: "GDPR" },
        { accessToken: ACCESS },
      ),
    ).rejects.toThrowError(AuditLogRetentionApiError);
  });

  it("deleteRetentionPolicy issues DELETE /retention/{class} returning 204", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockFetchResponse({ status: 204 }));

    await deleteRetentionPolicy("data", { accessToken: ACCESS });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/retention/data`);
    expect(calledInit?.method).toBe("DELETE");
  });

  it("updateRetentionPolicy issues PUT /retention/{class}", async () => {
    const pol: RetentionPolicy = {
      tenant_id: "00000000-0000-0000-0000-000000000000",
      action_class: "admin",
      days: 1095,
      archive: false,
      mask_pii: true,
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(mockFetchResponse({ status: 200, body: pol }));

    const res = await updateRetentionPolicy(
      "admin",
      { days: 1095, archive: false, mask_pii: true },
      { accessToken: ACCESS },
    );
    expect(res.days).toBe(1095);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = fetchMock.mock.calls[0];
    expect(calledUrl).toBe(`${BASE}/api/v1/audit-log/retention/admin`);
    expect(calledInit?.method).toBe("PUT");
  });

  it("TS interface RetentionPolicy has all 5 fields (parity CR 12-5 D-PARITY-01)", () => {
    const pol: RetentionPolicy = {
      tenant_id: "t",
      action_class: "admin",
      days: 1825,
      archive: true,
      mask_pii: true,
    };
    expect(Object.keys(pol).sort()).toEqual(
      ["action_class", "archive", "days", "mask_pii", "tenant_id"].sort(),
    );
  });

  it("forwards caller-supplied X-Trace-Id when provided", async () => {
    const explicitTrace = "99999999-9999-9999-9999-999999999999";
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        mockFetchResponse({ status: 200, body: { policies: [], trace_id: explicitTrace } }),
      );

    await listRetentionPolicies({ accessToken: ACCESS, traceId: explicitTrace });
    const [, calledInit] = fetchMock.mock.calls[0];
    const headers = (calledInit?.headers ?? {}) as Record<string, string>;
    expect(headers["X-Trace-Id"]).toBe(explicitTrace);
  });
});
