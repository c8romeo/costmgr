/**
 * apps/web/__tests__/components/m9-abc.AbcDispatchPanel.test.tsx — Story 9.7
 *
 * Vitest tests for AbcDispatchPanel (M9 ABC dispatch dual-route main client).
 *
 * Coverage (T2 A35):
 *   - Panel mount + form state (3 cases)
 *   - Service vs manufacturing tenant industry dispatch decision (2 cases)
 *   - Submit handler → discriminated union outcome (abc vs trad) (3 cases)
 *   - Error toast integration when initialError provided (2 cases)
 *   - Empty result placeholder when initialOutcome is null (1 case)
 *   - accessToken undefined shows no_token_notice (1 case)
 *
 * Total: ~12 NEW vitest cases (T2 A35 wire).
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import { AbcDispatchPanel } from "@/components/m9-abc/AbcDispatchPanel";
import koKR from "@/messages/ko-KR.json";


const messages = koKR;

function renderWithIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider locale="ko-KR" messages={messages}>
      {node}
    </NextIntlClientProvider>
  );
}

const defaultProps = {
  accessToken: "sb-test-token" as string | undefined,
  tenantIndustry: "service",
  initialOutcome: null,
  initialError: null,
};

// ── Panel mount + form state (3 cases) ─────────────────────

describe("AbcDispatchPanel mount", () => {
  it("renders panel root with data-testid='abc-dispatch-panel'", () => {
    render(renderWithIntl(<AbcDispatchPanel {...defaultProps} />));
    expect(screen.getByTestId("abc-dispatch-panel")).toBeTruthy();
  });

  it("renders tenant_industry display with data-tenant-industry attribute", () => {
    render(renderWithIntl(<AbcDispatchPanel {...defaultProps} />));
    const indicator = screen.getByTestId("abc-dispatch-tenant-industry");
    expect(indicator.getAttribute("data-tenant-industry")).toBe("service");
  });

  it("renders form with tenant_id and period_key inputs and submit button", () => {
    render(renderWithIntl(<AbcDispatchPanel {...defaultProps} />));
    expect(screen.getByTestId("abc-dispatch-form")).toBeTruthy();
    expect(screen.getByTestId("abc-dispatch-submit")).toBeTruthy();
  });
});

// ── Service vs manufacturing dispatch decision (2 cases) ───

describe("AbcDispatchPanel dispatch decision", () => {
  it("shows expected_engine_type='abc' for service industry", () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel {...defaultProps} tenantIndustry="service" />,
      ),
    );
    const indicator = screen.getByTestId("abc-dispatch-tenant-industry");
    expect(indicator.textContent).toMatch(/abc/i);
  });

  it("shows expected_engine_type='trad' for manufacturing industry", () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel {...defaultProps} tenantIndustry="manufacturing" />,
      ),
    );
    const indicator = screen.getByTestId("abc-dispatch-tenant-industry");
    expect(indicator.textContent).toMatch(/trad/i);
  });
});

// ── Submit handler (3 cases) ──────────────────────────────

describe("AbcDispatchPanel submit handler", () => {
  it("renders empty result placeholder before submit", () => {
    render(renderWithIntl(<AbcDispatchPanel {...defaultProps} />));
    expect(screen.getByTestId("abc-dispatch-empty-result")).toBeTruthy();
  });

  it("renders abc result card after submit when tenant_industry=service", async () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel {...defaultProps} tenantIndustry="service" />,
      ),
    );
    fireEvent.click(screen.getByTestId("abc-dispatch-submit"));
    await waitFor(() =>
      expect(screen.queryByTestId("abc-dispatch-result-abc")).toBeTruthy(),
    );
  });

  it("renders trad result card after submit when tenant_industry=manufacturing", async () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel {...defaultProps} tenantIndustry="manufacturing" />,
      ),
    );
    fireEvent.click(screen.getByTestId("abc-dispatch-submit"));
    await waitFor(() =>
      expect(screen.queryByTestId("abc-dispatch-result-trad")).toBeTruthy(),
    );
  });
});

// ── Error toast integration (2 cases) ──────────────────────

describe("AbcDispatchPanel error integration", () => {
  it("surfaces error toast when initialError='ABC_EMPTY_DEPARTMENTS'", () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel
          {...defaultProps}
          initialError="ABC_EMPTY_DEPARTMENTS"
        />,
      ),
    );
    expect(screen.getByTestId("abc-dispatch-error-toast")).toBeTruthy();
    expect(
      screen
        .getByTestId("abc-dispatch-error-toast")
        .getAttribute("data-error-code"),
    ).toBe("ABC_EMPTY_DEPARTMENTS");
  });

  it("dismiss button clears error toast", async () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel
          {...defaultProps}
          initialError="ABC_EMPTY_DEPARTMENTS"
        />,
      ),
    );
    fireEvent.click(screen.getByTestId("abc-dispatch-error-dismiss"));
    await waitFor(() =>
      expect(screen.queryByTestId("abc-dispatch-error-toast")).toBeNull(),
    );
  });
});

// ── accessToken undefined (1 case) ────────────────────────

describe("AbcDispatchPanel accessToken undefined", () => {
  it("shows no_token_notice when accessToken is undefined", () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel {...defaultProps} accessToken={undefined} />,
      ),
    );
    expect(screen.getByTestId("abc-dispatch-no-token")).toBeTruthy();
  });

  it("does NOT show no_token_notice when accessToken is provided", () => {
    render(
      renderWithIntl(
        <AbcDispatchPanel {...defaultProps} accessToken="sb-token-abc" />,
      ),
    );
    expect(screen.queryByTestId("abc-dispatch-no-token")).toBeNull();
  });
});