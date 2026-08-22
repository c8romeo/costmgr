// apps/web/__tests__/components/m8-budget.PreStandardCostTable.test.tsx — Story 8.3
//
// Component tests for PreStandardCostTable.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PreStandardCostTable } from "../../components/m8-budget/PreStandardCostTable";

import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("PreStandardCostTable component (Story 8.3)", () => {
  const snapshot = {
    period_key: "2026-07#B1",
    scenario_index: 1,
    material_cost: "10000",
    labor_cost: "400000",
    overhead_cost: "51250",
    manufacturing_cost: "461250",
    result_hash: "a".repeat(64),
    trace_id: null,
  };

  it("renders 4-column table headers", () => {
    render(<PreStandardCostTable snapshot={snapshot} />);
    expect(screen.getByText(/항목/)).toBeInTheDocument();
    expect(screen.getByText(/금액 \(KRW\)/)).toBeInTheDocument();
    expect(screen.getByText(/구성비/)).toBeInTheDocument();
    expect(screen.getByText(/설명/)).toBeInTheDocument();
  });

  it("renders 3 cost rows + 1 total row", () => {
    const { container } = render(<PreStandardCostTable snapshot={snapshot} />);
    const rows = container.querySelectorAll("tbody tr");
    expect(rows).toHaveLength(4);
  });

  it("renders Korean labels for material/labor/overhead/total", () => {
    render(<PreStandardCostTable snapshot={snapshot} />);
    expect(screen.getByText("직접재료")).toBeInTheDocument();
    expect(screen.getByText("직접노무")).toBeInTheDocument();
    expect(screen.getByText("제조경비")).toBeInTheDocument();
    expect(screen.getByText("제조원가 합계")).toBeInTheDocument();
  });

  it("renders formatted KRW amounts with 천단위 콤마", () => {
    render(<PreStandardCostTable snapshot={snapshot} />);
    expect(screen.getByText(/10,000원/)).toBeInTheDocument();
    expect(screen.getByText(/400,000원/)).toBeInTheDocument();
    expect(screen.getByText(/51,250원/)).toBeInTheDocument();
    expect(screen.getByText(/461,250원/)).toBeInTheDocument();
  });

  it("renders total row share = 100.00%", () => {
    render(<PreStandardCostTable snapshot={snapshot} />);
    expect(screen.getByText("100.00%")).toBeInTheDocument();
  });

  it("renders notes column descriptions", () => {
    render(<PreStandardCostTable snapshot={snapshot} />);
    expect(screen.getByText("직접재료 단가 × 수량")).toBeInTheDocument();
    expect(screen.getByText("직접노무 단가 × 시간")).toBeInTheDocument();
    expect(screen.getByText(/제조경비율/)).toBeInTheDocument();
  });

  it("handles zero snapshot gracefully", () => {
    const zero = {
      ...snapshot,
      material_cost: "0",
      labor_cost: "0",
      overhead_cost: "0",
      manufacturing_cost: "0",
    };
    render(<PreStandardCostTable snapshot={zero} />);
    expect(screen.getByText("100.00%")).toBeInTheDocument();
  });
});