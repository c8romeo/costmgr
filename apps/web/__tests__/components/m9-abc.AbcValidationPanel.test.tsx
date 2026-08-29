// apps/web/__tests__/components/m9-abc.AbcValidationPanel.test.tsx — Story 9.1
//
// Component test for AbcValidationPanel — main Client Component for
// M9 ABC 100% validation UI (PRD §F9.1 verbatim).

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AbcValidationPanel } from "../../components/m9-abc/AbcValidationPanel";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("AbcValidationPanel component (Story 9.1)", () => {
  const baseProps = {
    accessToken: "test-token" as string | undefined,
    initialResponse: null as Parameters<typeof AbcValidationPanel>[0]["initialResponse"],
    initialError: null as string | null,
  };

  it("renders panel with title + form (CR 11-4 D-001 mount check)", () => {
    render(<AbcValidationPanel {...baseProps} />);
    expect(screen.getByTestId("abc-validation-panel")).toBeInTheDocument();
    expect(screen.getByText("ABC 100% 가드 검증")).toBeInTheDocument();
    expect(screen.getByTestId("abc-validation-form")).toBeInTheDocument();
  });

  it("renders empty-result placeholder when initialResponse=null", () => {
    render(<AbcValidationPanel {...baseProps} />);
    expect(
      screen.getByText(/검증 실행 후 결과가 여기에 표시됩니다/),
    ).toBeInTheDocument();
  });

  it("renders error banner when initialError is set", () => {
    render(
      <AbcValidationPanel
        accessToken="test-token"
        initialResponse={null}
        initialError="load_failed"
      />,
    );
    const banner = screen.getByTestId("abc-validation-error-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toContain("load_failed");
  });

  it("renders guard badge + 3 layer statuses when initialResponse provided", () => {
    render(
      <AbcValidationPanel
        accessToken="test-token"
        initialResponse={{
          cost_pool_id: "cp-001",
          activity_id: "act-001",
          all_valid: true,
          layers: [
            {
              target: "cost_pool",
              sum_pct: "100",
              count: 4,
              is_valid: true,
              hash: "a".repeat(64),
              message_ko: null,
            },
            {
              target: "activity",
              sum_pct: "100",
              count: 3,
              is_valid: true,
              hash: "b".repeat(64),
              message_ko: null,
            },
            {
              target: "driver",
              sum_pct: "100",
              count: 2,
              is_valid: true,
              hash: "c".repeat(64),
              message_ko: null,
            },
          ],
        }}
        initialError={null}
      />,
    );
    expect(
      screen.getByTestId("abc-validation-guard-badge"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("abc-validation-status-cost_pool"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("abc-validation-status-activity"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("abc-validation-status-driver"),
    ).toBeInTheDocument();
  });

  it("renders form submit button (3-layer guard trigger)", () => {
    render(<AbcValidationPanel {...baseProps} />);
    expect(screen.getByTestId("abc-validation-submit")).toBeInTheDocument();
    expect(screen.getByText("3-layer 가드 검증 실행")).toBeInTheDocument();
  });
});