/**
 * apps/web/__tests__/lib/admin-idp-client.test.ts — Epic 16 T4 (AC #7.3, #7.5)
 *
 * Tenant IdP admin fetch wrapper parity tests.
 *
 * Covers:
 *   - listIdPConfigs GET path (URL encoding + auth header + trace id)
 *   - createIdPConfig POST path (JSON body + content-type)
 *   - updateIdPConfig PUT path
 *   - deleteIdPConfig DELETE path
 *   - testIdPConfig POST /test path
 *   - typed envelope parsing on 403/404/400 (CR 12-5 D-14)
 *   - 2xx responses parse correctly
 *   - network error handling
 *   - TS interface shape parity with backend IdPConfigResponse Pydantic model
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createIdPConfig,
  deleteIdPConfig,
  listIdPConfigs,
  testIdPConfig,
  updateIdPConfig,
} from "@/lib/auth/admin-idp-client";

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

const sampleConfig = {
  id: "00000000-0000-0000-0000-000000000001",
  tenant_id: "00000000-0000-0000-0000-0000000000aa",
  idp_entity_id: "https://idp.example.com/sso",
  idp_sso_url: "https://idp.example.com/sso",
  idp_slo_url: null,
  idp_x509_cert_sha256:
    "abc123abc123abc123abc123abc123abc123abc123abc123abc123abc123abcd",
  acs_url: "https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme",
  name_id_format:
    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
  enabled: true,
  created_at: "2026-08-22T00:00:00Z",
  updated_at: "2026-08-22T00:00:00Z",
};

describe("admin-idp-client (Epic 16 T4)", () => {
  it("listIdPConfigs sends GET with Authorization + trace id", async () => {
    const mock = mockFetchOnce(200, [sampleConfig]);
    const result = await listIdPConfigs("token-abc", "acme");
    expect(result.ok).toBe(true);
    expect(result.data).toHaveLength(1);
    expect(result.data[0].idp_entity_id).toBe("https://idp.example.com/sso");
    const [calledUrl, calledInit] = mock.mock.calls[0];
    expect(String(calledUrl)).toBe(
      "http://localhost:8765/api/v1/admin/tenant/acme/idp",
    );
    const init = calledInit as RequestInit;
    expect(init.method).toBe("GET");
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer token-abc");
    expect(headers["X-Trace-Id"]).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("listIdPConfigs URL-encodes tenant slug with special chars", async () => {
    const mock = mockFetchOnce(200, []);
    await listIdPConfigs("token", "acme & friends");
    const [calledUrl] = mock.mock.calls[0];
    expect(String(calledUrl)).toContain("acme%20%26%20friends");
  });

  it("listIdPConfigs parses 403 envelope (CR 12-5 D-14)", async () => {
    mockFetchOnce(403, {
      code: "TENANT_IDP_FORBIDDEN_KO",
      message_ko: "IdP 관리 권한이 없습니다",
      details: { reason: "role_check_failed" },
      trace_id: "trace-1",
    });
    const result = await listIdPConfigs("token", "acme");
    expect(result.ok).toBe(false);
    expect(result.error?.status).toBe(403);
    expect(result.error?.code).toBe("TENANT_IDP_FORBIDDEN_KO");
    expect(result.error?.message_ko).toBe("IdP 관리 권한이 없습니다");
    expect(result.error?.trace_id).toBe("trace-1");
  });

  it("createIdPConfig POST sends metadata_xml + content-type", async () => {
    const mock = mockFetchOnce(201, sampleConfig);
    const result = await createIdPConfig("token", "acme", {
      metadata_xml: "<EntityDescriptor ...></EntityDescriptor>",
      enabled: true,
    });
    expect(result.ok).toBe(true);
    const [calledUrl, calledInit] = mock.mock.calls[0];
    expect(String(calledUrl)).toBe(
      "http://localhost:8765/api/v1/admin/tenant/acme/idp",
    );
    const init = calledInit as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.body).toBe(
      JSON.stringify({
        metadata_xml: "<EntityDescriptor ...></EntityDescriptor>",
        enabled: true,
      }),
    );
    const headers = init.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("createIdPConfig parses 409 already_exists envelope", async () => {
    mockFetchOnce(409, {
      code: "TENANT_IDP_ALREADY_EXISTS_KO",
      message_ko: "이 tenant 에 이미 IdP 가 등록되어 있습니다",
      details: { tenant_slug: "acme" },
    });
    const result = await createIdPConfig("token", "acme", {
      metadata_xml: "<x/>",
    });
    expect(result.ok).toBe(false);
    expect(result.error?.code).toBe("TENANT_IDP_ALREADY_EXISTS_KO");
  });

  it("createIdPConfig parses 400 metadata_invalid envelope", async () => {
    mockFetchOnce(400, {
      code: "TENANT_IDP_METADATA_INVALID_KO",
      message_ko: "IdP 메타데이터가 유효하지 않습니다 (XML 파싱 실패)",
      details: { validator_code: "IDPMetadataMalformedError" },
    });
    const result = await createIdPConfig("token", "acme", {
      metadata_xml: "not-valid-xml",
    });
    expect(result.ok).toBe(false);
    expect(result.error?.status).toBe(400);
    expect(result.error?.details?.validator_code).toBe(
      "IDPMetadataMalformedError",
    );
  });

  it("updateIdPConfig PUT path", async () => {
    const mock = mockFetchOnce(200, sampleConfig);
    const result = await updateIdPConfig("token", "acme", {
      idp_entity_id: "https://new-idp.example.com",
      idp_sso_url: "https://new-idp.example.com/sso",
      idp_x509_cert_pem: "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
      enabled: false,
    });
    expect(result.ok).toBe(true);
    const [, calledInit] = mock.mock.calls[0];
    expect((calledInit as RequestInit).method).toBe("PUT");
  });

  it("updateIdPConfig parses 404 not_found envelope", async () => {
    mockFetchOnce(404, {
      code: "TENANT_IDP_NOT_FOUND_KO",
      message_ko: "IdP 설정을 찾을 수 없습니다",
      details: { tenant_slug: "acme" },
    });
    const result = await updateIdPConfig("token", "acme", {
      metadata_xml: "<x/>",
    });
    expect(result.ok).toBe(false);
    expect(result.error?.code).toBe("TENANT_IDP_NOT_FOUND_KO");
  });

  it("deleteIdPConfig DELETE path returns ok on 200", async () => {
    const mock = mockFetchOnce(200, {
      code: "TENANT_IDP_DISABLED_OK",
      id: sampleConfig.id,
    });
    const result = await deleteIdPConfig("token", "acme");
    expect(result.ok).toBe(true);
    const [, calledInit] = mock.mock.calls[0];
    expect((calledInit as RequestInit).method).toBe("DELETE");
  });

  it("deleteIdPConfig returns error on 403 (non-owner)", async () => {
    mockFetchOnce(403, {
      code: "TENANT_IDP_FORBIDDEN_KO",
      message_ko: "IdP 관리 권한이 없습니다",
      details: { reason: "role_check_failed" },
    });
    const result = await deleteIdPConfig("token", "acme");
    expect(result.ok).toBe(false);
    expect(result.error?.status).toBe(403);
  });

  it("testIdPConfig POST /test returns 8-step result on success", async () => {
    const mock = mockFetchOnce(200, {
      passed: true,
      steps: [
        { step: 1, name: "xml_well_formedness", passed: true, detail: null },
        { step: 2, name: "root_entity_descriptor", passed: true, detail: null },
        { step: 3, name: "entity_id_present", passed: true, detail: null },
        { step: 4, name: "idpsso_descriptor_present", passed: true, detail: null },
        { step: 5, name: "x509_cert_present", passed: true, detail: null },
        { step: 6, name: "sso_url_https", passed: true, detail: null },
        { step: 7, name: "slo_url_optional_https", passed: true, detail: null },
        { step: 8, name: "tenant_slug_host_match", passed: true, detail: null },
      ],
      metadata: {
        entity_id: "https://idp.example.com/sso",
        sso_url: "https://idp.example.com/sso",
        slo_url: null,
        name_id_format:
          "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
      },
    });
    const result = await testIdPConfig(
      "token",
      "acme",
      "<EntityDescriptor ...></EntityDescriptor>",
    );
    expect(result.ok).toBe(true);
    expect(result.data?.passed).toBe(true);
    expect(result.data?.steps).toHaveLength(8);
    const [calledUrl] = mock.mock.calls[0];
    expect(String(calledUrl)).toBe(
      "http://localhost:8765/api/v1/admin/tenant/acme/idp/test",
    );
  });

  it("testIdPConfig handles network errors gracefully", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("ECONNREFUSED")) as unknown as typeof fetch;
    const result = await testIdPConfig("token", "acme", "<x/>");
    expect(result.ok).toBe(false);
  });
});
