// apps/web/__tests__/components/m9-abc.CcrResultCard.test.tsx — Story 9.2
//
// Component test for CcrResultCard — CCR per hour display + V8 hash badge.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CcrResultCard } from "../../components/m9-abc/CcrResultCard";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

const baseCCR = {
  department_id: "dept-001",
  department_cost: "13200000",
  practical_capacity_hours: "400",
  ccr_per_hour: "33000",
  hash: "a".repeat(71), // sha256: + 64 hex
};

describe("CcrResultCard component (Story 9.2)", () => {
  it("renders valid CCR with success badge and hash", () => {
    render(<CcrResultCard ccr={baseCCR} messageKo={null} />);
    expect(screen.getByTestId("ccr-result-card")).toBeInTheDocument();
    expect(screen.getByTestId("ccr-result-success-badge")).toHaveTextContent(
      "CCR OK",
    );
    expect(screen.getByTestId("ccr-result-hash").textContent).toContain(
      "a".repeat(64),
    );
  });

  it("formats CCR per hour with Korean thousands separator", () => {
    render(<CcrResultCard ccr={baseCCR} messageKo={null} />);
    const perHour = screen.getByTestId("ccr-result-per-hour");
    expect(perHour.textContent).toContain("33,000");
    expect(perHour.textContent).toContain("원/시간");
  });

  it("renders failure badge + error message when messageKo is set", () => {
    render(
      <CcrResultCard
        ccr={baseCCR}
        messageKo="CCR 계산: 실제 조업능력은 0보다 커야 합니다"
      />,
    );
    expect(screen.getByTestId("ccr-result-failure-badge")).toHaveTextContent(
      "CCR 실패",
    );
    expect(screen.getByTestId("ccr-result-error-message")).toHaveTextContent(
      "CCR 계산: 실제 조업능력은 0보다 커야 합니다",
    );
  });

  it("shows department_id and capacity metadata", () => {
    render(<CcrResultCard ccr={baseCCR} messageKo={null} />);
    expect(screen.getByText(/dept-001/)).toBeInTheDocument();
    expect(screen.getByText("400h")).toBeInTheDocument();
  });
});