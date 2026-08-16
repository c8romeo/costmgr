// apps/web/__tests__/components/m9-abc.AbcAllocationPanel.test.tsx — Story 9.2
//
// Component test for AbcAllocationPanel — main Client Component for
// M9 ABC Allocation Engine UI (PRD §F9.2 + §A9 + §V7 verbatim).

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AbcAllocationPanel } from "../../components/m9-abc/AbcAllocationPanel";

import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("AbcAllocationPanel component (Story 9.2)", () => {
  const baseProps = {
    accessToken: "test-token" as string | undefined,
    initialAllocation: null as Parameters<typeof AbcAllocationPanel>[0]["initialAllocation"],
    initialError: null as string | null,
  };

  it("renders panel with title + form (CR 11-4 D-001 mount check)", () => {
    render(<AbcAllocationPanel {...baseProps} />);
    expect(screen.getByTestId("abc-allocation-panel")).toBeInTheDocument();
    expect(screen.getByText("ABC 배부 엔진 (CCR · 1원 단위)")).toBeInTheDocument();
    expect(screen.getByTestId("abc-allocation-form")).toBeInTheDocument();
  });

  it("renders empty-result placeholder when initialAllocation=null", () => {
    render(<AbcAllocationPanel {...baseProps} />);
    expect(
      screen.getByText(/CCR 계산 실행 후 결과가 여기에 표시됩니다/),
    ).toBeInTheDocument();
  });

  it("renders error banner when initialError is set", () => {
    render(
      <AbcAllocationPanel
        accessToken="test-token"
        initialAllocation={null}
        initialError="load_failed"
      />,
    );
    const banner = screen.getByTestId("abc-allocation-error-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toContain("load_failed");
  });

  it("renders CCR + Unused + Breakdown + Balance badge sections", () => {
    render(
      <AbcAllocationPanel
        accessToken="test-token"
        initialAllocation={{
          ccr: {
            department_id: "dept-001",
            department_cost: "13200000",
            practical_capacity_hours: "400",
            ccr_per_hour: "33000",
            hash: "a".repeat(71), // sha256: + 64 hex
          },
          activity_mappings: [
            {
              activity_id: "act-001",
              hours: "400",
              ccr_amount_krw: "13200000",
            },
          ],
          cost_object_breakdown: [
            {
              product_id: "prod-A",
              activity_id: "act-001",
              driver_id: "drv-001",
              allocated_krw: "13200000",
            },
          ],
          unused_capacity: {
            unused_hours: "0",
            ccr_per_hour: "33000",
            unused_cost_krw: "0",
            hash: "b".repeat(71),
          },
          department_cost: "13200000",
          total_breakdown_sum: "13200000",
          is_balanced: true,
        }}
        initialError={null}
      />,
    );
    expect(screen.getByTestId("ccr-result-card")).toBeInTheDocument();
    expect(screen.getByTestId("unused-capacity-row")).toBeInTheDocument();
    expect(
      screen.getByTestId("cost-object-breakdown-table"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("cost-object-breakdown-balance-badge"),
    ).toHaveTextContent("V7 균형");
  });

  it("renders unbalanced badge when is_balanced=false", () => {
    render(
      <AbcAllocationPanel
        accessToken="test-token"
        initialAllocation={{
          ccr: {
            department_id: "dept-unbalanced",
            department_cost: "13200000",
            practical_capacity_hours: "400",
            ccr_per_hour: "33000",
            hash: "a".repeat(71),
          },
          activity_mappings: [],
          cost_object_breakdown: [],
          unused_capacity: {
            unused_hours: "0",
            ccr_per_hour: "33000",
            unused_cost_krw: "0",
            hash: "b".repeat(71),
          },
          department_cost: "13200000",
          total_breakdown_sum: "10000000",
          is_balanced: false,
        }}
        initialError={null}
      />,
    );
    expect(
      screen.getByTestId("cost-object-breakdown-balance-badge"),
    ).toHaveTextContent("V7 불균형");
  });

  it("computes CCR + allocation on submit and renders 4 sections", () => {
    render(<AbcAllocationPanel {...baseProps} />);
    const submitButton = screen.getByTestId("abc-allocation-submit");
    fireEvent.click(submitButton);
    expect(screen.getByTestId("ccr-result-card")).toBeInTheDocument();
    expect(screen.getByTestId("unused-capacity-row")).toBeInTheDocument();
    expect(
      screen.getByTestId("cost-object-breakdown-table"),
    ).toBeInTheDocument();
  });
});