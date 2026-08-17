/**
 * apps/web/__tests__/components/m9-abc.AbcDispatchDecisionBadge.test.tsx — Story 9.7
 *
 * Vitest tests for AbcDispatchDecisionBadge (M9 ABC dispatch dual-route wire).
 *
 * Coverage (T2 A35):
 *   - data-engine-type attribute rendering (abc vs trad) (3 cases)
 *   - data-tenant-industry attribute rendering (3 cases)
 *   - role/aria-label accessibility (3 cases)
 *   - styling differences (blue for abc / gray for trad) (3 cases)
 *
 * Total: ~12 NEW vitest cases (T2 A35 wire).
 */

import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import koKR from "@/messages/ko-KR.json";

import { AbcDispatchDecisionBadge } from "@/components/m9-abc/AbcDispatchDecisionBadge";

const messages = koKR;

function renderWithIntl(node: React.ReactElement): React.ReactElement {
  return (
    <NextIntlClientProvider locale="ko-KR" messages={messages}>
      {node}
    </NextIntlClientProvider>
  );
}

// ── data-engine-type attribute (3 cases) ─────────────────────

describe("AbcDispatchDecisionBadge data-engine-type", () => {
  it("renders abc engine_type data attribute when engineType='abc'", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="service industry → ABC path"
        />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-decision-badge");
    expect(badge.getAttribute("data-engine-type")).toBe("abc");
  });

  it("renders trad engine_type data attribute when engineType='trad'", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="trad"
          tenantIndustry="manufacturing"
          reason="manufacturing industry → TRAD path"
        />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-decision-badge");
    expect(badge.getAttribute("data-engine-type")).toBe("trad");
  });

  it("renders reason text in the badge", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="service industry dispatch reason"
        />,
      ),
    );
    expect(screen.getByText(/service industry dispatch reason/)).toBeTruthy();
  });
});

// ── data-tenant-industry attribute (3 cases) ────────────────

describe("AbcDispatchDecisionBadge data-tenant-industry", () => {
  it("renders service tenant industry data attribute", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="abc path"
        />,
      ),
    );
    expect(
      screen
        .getByTestId("abc-dispatch-decision-badge")
        .getAttribute("data-tenant-industry"),
    ).toBe("service");
  });

  it("renders manufacturing tenant industry data attribute", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="trad"
          tenantIndustry="manufacturing"
          reason="trad path"
        />,
      ),
    );
    expect(
      screen
        .getByTestId("abc-dispatch-decision-badge")
        .getAttribute("data-tenant-industry"),
    ).toBe("manufacturing");
  });

  it("passes through unknown industry strings as data attribute verbatim", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="retail"
          reason="retail industry"
        />,
      ),
    );
    expect(
      screen
        .getByTestId("abc-dispatch-decision-badge")
        .getAttribute("data-tenant-industry"),
    ).toBe("retail");
  });
});

// ── accessibility (3 cases) ──────────────────────────────────

describe("AbcDispatchDecisionBadge accessibility", () => {
  it("renders role='status' for live region announcement", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="abc path"
        />,
      ),
    );
    expect(
      screen.getByTestId("abc-dispatch-decision-badge").getAttribute("role"),
    ).toBe("status");
  });

  it("renders Korean aria-label for abc engine_type", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="abc path"
        />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-decision-badge");
    const ariaLabel = badge.getAttribute("aria-label");
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).toContain("ABC");
  });

  it("renders Korean aria-label for trad engine_type", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="trad"
          tenantIndustry="manufacturing"
          reason="trad path"
        />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-decision-badge");
    const ariaLabel = badge.getAttribute("aria-label");
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).toContain("전통 원가 계산 경로");
  });
});

// ── styling (3 cases) ────────────────────────────────────────

describe("AbcDispatchDecisionBadge styling", () => {
  it("uses blue background for abc engine_type", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="abc"
        />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-decision-badge");
    expect(badge.className).toContain("bg-blue-100");
  });

  it("uses gray background for trad engine_type", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="trad"
          tenantIndustry="manufacturing"
          reason="trad"
        />,
      ),
    );
    const badge = screen.getByTestId("abc-dispatch-decision-badge");
    expect(badge.className).toContain("bg-gray-100");
  });

  it("uppercases engine_type label text", () => {
    render(
      renderWithIntl(
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason="abc"
        />,
      ),
    );
    // ABC Korean label is rendered in an uppercase tracking-wide span
    const labelSpan = screen.getByText(/ABC/);
    expect(labelSpan.className).toContain("uppercase");
  });
});