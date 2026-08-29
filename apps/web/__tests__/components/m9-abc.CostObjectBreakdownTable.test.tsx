// apps/web/__tests__/components/m9-abc.CostObjectBreakdownTable.test.tsx — Story 9.2
//
// Component test for CostObjectBreakdownTable — 4컬럼 (상품·활동·동인·배부액)
// + Σ balance row + V7 balance badge.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CostObjectBreakdownTable } from "../../components/m9-abc/CostObjectBreakdownTable";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

const baseProps = {
  activityMappings: [
    {
      activity_id: "act-001",
      hours: "400",
      ccr_amount_krw: "13200000",
    },
  ],
  rows: [
    {
      product_id: "prod-A",
      activity_id: "act-001",
      driver_id: "drv-001",
      allocated_krw: "13200000",
    },
  ],
  totalBreakdownSum: "13200000",
  isBalanced: true,
};

describe("CostObjectBreakdownTable component (Story 9.2)", () => {
  it("renders 4-column table with single row and balance badge", () => {
    render(<CostObjectBreakdownTable {...baseProps} />);
    expect(
      screen.getByTestId("cost-object-breakdown-table"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("cost-object-breakdown-row")).toBeInTheDocument();
    expect(
      screen.getByTestId("cost-object-breakdown-balance-badge"),
    ).toHaveTextContent("V7 균형");
  });

  it("formats allocated_krw with Korean thousands separator", () => {
    render(<CostObjectBreakdownTable {...baseProps} />);
    const allocated = screen.getByTestId("cost-object-breakdown-allocated");
    expect(allocated.textContent).toContain("13,200,000");
  });

  it("renders empty placeholder when no rows", () => {
    render(
      <CostObjectBreakdownTable
        {...baseProps}
        rows={[]}
        totalBreakdownSum="0"
        isBalanced={false}
      />,
    );
    expect(
      screen.getByTestId("cost-object-breakdown-empty"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("cost-object-breakdown-balance-badge"),
    ).toHaveTextContent("V7 불균형");
  });

  it("displays Σ total in footer row", () => {
    render(<CostObjectBreakdownTable {...baseProps} />);
    expect(
      screen.getByTestId("cost-object-breakdown-total"),
    ).toHaveTextContent("13,200,000");
  });
});