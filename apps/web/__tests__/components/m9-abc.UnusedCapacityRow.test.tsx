// apps/web/__tests__/components/m9-abc.UnusedCapacityRow.test.tsx — Story 9.2
//
// Component test for UnusedCapacityRow — PRD §A9 verbatim
// "미사용능력 X,XXX원 별도 행" 회색 배지.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { UnusedCapacityRow } from "../../components/m9-abc/UnusedCapacityRow";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

const baseUnused = {
  unused_hours: "200",
  ccr_per_hour: "33000",
  unused_cost_krw: "6600000",
  hash: "b".repeat(71), // sha256: + 64 hex
};

describe("UnusedCapacityRow component (Story 9.2)", () => {
  it("renders unused row with separate-row badge and hash", () => {
    render(<UnusedCapacityRow unused={baseUnused} />);
    expect(screen.getByTestId("unused-capacity-row")).toBeInTheDocument();
    expect(screen.getByTestId("unused-capacity-badge")).toHaveTextContent(
      "별도 행",
    );
    expect(screen.getByTestId("unused-capacity-hash").textContent).toContain(
      "b".repeat(64),
    );
  });

  it("formats KRW with thousands separator", () => {
    render(<UnusedCapacityRow unused={baseUnused} />);
    const cost = screen.getByTestId("unused-capacity-cost");
    expect(cost.textContent).toContain("6,600,000");
    expect(cost.textContent).toContain("원");
  });

  it("displays unused hours with 'h' unit", () => {
    render(<UnusedCapacityRow unused={baseUnused} />);
    expect(screen.getByTestId("unused-capacity-hours").textContent).toContain(
      "200h",
    );
  });
});