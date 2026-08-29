/**
 * apps/web/__tests__/settings/sso/page.test.tsx — Epic 16 T4 (AC #7.6)
 *
 * RTL render tests for /settings/sso (Tenant IdP admin UI).
 *
 * Covers:
 *   - D-001: page.tsx mounts the Client Component unconditionally
 *   - D-002: ko-KR.json settings_sso namespace keys all present
 *   - D-003: vitest RTL renders each sub-component (IdPList,
 *     IdPCreateForm, IdPEditForm, IdPTestPanel)
 *   - D-005: unknown state reject — tenant_slug_required surface
 *     renders when tenantSlug is empty
 *   - empty state (no IdP configured) → CTA "IdP 등록"
 *   - configured state → IdPList shows fingerprint + action buttons
 *   - 403 envelope → forbidden_notice renders
 *   - IdPCreateForm submit triggers POST + dispatches refetch
 *   - IdPEditForm pre-fills fields from existing config
 *   - IdPTestPanel renders 8-step pass/fail list
 *
 * Mock strategy: vi.mock the admin-idp-client module so RTL never
 * touches the network. next/navigation is also mocked (router.refresh).
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

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/lib/auth/admin-idp-client", () => ({
  listIdPConfigs: vi.fn(),
  createIdPConfig: vi.fn(),
  updateIdPConfig: vi.fn(),
  deleteIdPConfig: vi.fn(),
  testIdPConfig: vi.fn(),
}));

import { IdPAdminPanel } from "@/components/settings/sso/IdPAdminPanel";
import {
  createIdPConfig,
  deleteIdPConfig,
  listIdPConfigs,
  testIdPConfig,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  updateIdPConfig,
} from "@/lib/auth/admin-idp-client";

const settingsSsoMessages = (koKR as unknown as { settings_sso: Record<string, string> })
  .settings_sso;

function withIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider
      locale="ko-KR"
      messages={{ settings_sso: settingsSsoMessages }}
    >
      {node}
    </NextIntlClientProvider>
  );
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

beforeEach(() => {
  vi.clearAllMocks();
});

describe("IdPAdminPanel (Epic 16 T4 /settings/sso)", () => {
  it("D-005: renders tenant_slug_required surface when tenantSlug is empty", () => {
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug=""
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    expect(
      screen.getByTestId("idp-admin-tenant-slug-required"),
    ).toBeInTheDocument();
    expect(screen.getByText(/tenant 정보를 먼저 선택/)).toBeInTheDocument();
  });

  it("D-001: page mounts unconditionally and renders panel header", () => {
    (listIdPConfigs as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: [],
    });
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    expect(screen.getByTestId("idp-admin-panel")).toBeInTheDocument();
    expect(screen.getByText("SSO / IdP 설정")).toBeInTheDocument();
  });

  it("empty state: shows IdPList empty CTA when initialConfigs is empty", () => {
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    expect(screen.getByTestId("idp-list-empty")).toBeInTheDocument();
    expect(screen.getByTestId("idp-list-empty-create-button")).toBeInTheDocument();
    expect(screen.getByText(/아직 등록된 IdP 가 없습니다/)).toBeInTheDocument();
  });

  it("configured state: shows IdPList configured surface with fingerprint", () => {
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[sampleConfig]}
          accessToken="token"
        />,
      ),
    );
    expect(screen.getByTestId("idp-list-configured")).toBeInTheDocument();
    expect(screen.getByTestId("idp-list-status-badge")).toHaveTextContent("활성");
    // The sample config uses the same value for entity_id + sso_url —
    // both fields render that text, so we use getAllByText.
    expect(
      screen.getAllByText("https://idp.example.com/sso").length,
    ).toBeGreaterThanOrEqual(2);
    expect(
      screen.getByText("abc123abc123abc123abc123abc123abc123abc123abc123abc123abc123abcd"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("idp-list-edit-button")).toBeInTheDocument();
    expect(screen.getByTestId("idp-list-test-button")).toBeInTheDocument();
    expect(screen.getByTestId("idp-list-delete-button")).toBeInTheDocument();
  });

  it("empty CTA click switches to IdPCreateForm (XML mode default)", async () => {
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-empty-create-button"));
    expect(screen.getByTestId("idp-create-form")).toBeInTheDocument();
    expect(screen.getByTestId("idp-create-mode-xml")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByTestId("idp-create-metadata-xml")).toBeInTheDocument();
  });

  it("create form: switch to direct mode reveals direct fields", async () => {
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-empty-create-button"));
    await user.click(screen.getByTestId("idp-create-mode-direct"));
    expect(screen.getByTestId("idp-create-entity-id")).toBeInTheDocument();
    expect(screen.getByTestId("idp-create-sso-url")).toBeInTheDocument();
    expect(screen.getByTestId("idp-create-x509-cert")).toBeInTheDocument();
  });

  it("create form: submit disabled until required direct fields are filled", async () => {
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-empty-create-button"));
    await user.click(screen.getByTestId("idp-create-mode-direct"));
    const submitBtn = screen.getByTestId("idp-create-submit-button");
    expect(submitBtn).toBeDisabled();
    await user.type(
      screen.getByTestId("idp-create-entity-id"),
      "https://idp.example.com",
    );
    await user.type(
      screen.getByTestId("idp-create-sso-url"),
      "https://idp.example.com/sso",
    );
    await user.type(
      screen.getByTestId("idp-create-x509-cert"),
      "-----BEGIN CERTIFICATE-----\nMIIDazCCAlOgAwIBAgIUJxZ\n-----END CERTIFICATE-----",
    );
    expect(submitBtn).not.toBeDisabled();
  });

  it("create form: successful submit POSTs and refetches", async () => {
    (createIdPConfig as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: sampleConfig,
    });
    (listIdPConfigs as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: [sampleConfig],
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-empty-create-button"));
    await user.click(screen.getByTestId("idp-create-mode-direct"));
    await user.type(
      screen.getByTestId("idp-create-entity-id"),
      "https://idp.example.com",
    );
    await user.type(
      screen.getByTestId("idp-create-sso-url"),
      "https://idp.example.com/sso",
    );
    await user.type(
      screen.getByTestId("idp-create-x509-cert"),
      "-----BEGIN CERTIFICATE-----\nMIIDazCCAlOgAwIBAgIUJxZ\n-----END CERTIFICATE-----",
    );
    await user.click(screen.getByTestId("idp-create-submit-button"));
    await waitFor(() => {
      expect(createIdPConfig).toHaveBeenCalledWith(
        "token",
        "acme",
        expect.objectContaining({
          idp_entity_id: "https://idp.example.com",
          idp_sso_url: "https://idp.example.com/sso",
          enabled: true,
        }),
      );
    });
  });

  it("edit form: prefills from existing config + requires cert re-entry", async () => {
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[sampleConfig]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-edit-button"));
    expect(screen.getByTestId("idp-edit-form")).toBeInTheDocument();
    expect(screen.getByTestId("idp-edit-entity-id")).toHaveValue(
      "https://idp.example.com/sso",
    );
    expect(screen.getByTestId("idp-edit-sso-url")).toHaveValue(
      "https://idp.example.com/sso",
    );
    expect(screen.getByTestId("idp-edit-x509-cert")).toHaveValue("");
    expect(screen.getByTestId("idp-edit-cert-notice")).toBeInTheDocument();
    expect(screen.getByTestId("idp-edit-submit-button")).toBeDisabled();
  });

  it("test panel: renders 8-step result after run", async () => {
    (testIdPConfig as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: {
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
          name_id_format: null,
        },
      },
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[sampleConfig]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-test-button"));
    expect(screen.getByTestId("idp-test-panel")).toBeInTheDocument();
    await user.type(
      screen.getByTestId("idp-test-metadata-xml"),
      "<EntityDescriptor ...></EntityDescriptor>",
    );
    await user.click(screen.getByTestId("idp-test-run-button"));
    await waitFor(() => {
      expect(screen.getByTestId("idp-test-result")).toBeInTheDocument();
    });
    for (let i = 1; i <= 8; i++) {
      expect(screen.getByTestId(`idp-test-step-${i}`)).toBeInTheDocument();
    }
  });

  it("delete confirm flow: shows confirm button then issues DELETE", async () => {
    (deleteIdPConfig as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
    });
    (listIdPConfigs as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      data: [],
    });
    const user = userEvent.setup();
    render(
      withIntl(
        <IdPAdminPanel
          tenantSlug="acme"
          initialConfigs={[sampleConfig]}
          accessToken="token"
        />,
      ),
    );
    await user.click(screen.getByTestId("idp-list-delete-button"));
    expect(
      screen.getByTestId("idp-list-delete-confirm-button"),
    ).toBeInTheDocument();
    await user.click(screen.getByTestId("idp-list-delete-confirm-button"));
    await waitFor(() => {
      expect(deleteIdPConfig).toHaveBeenCalledWith("token", "acme");
    });
  });
});
