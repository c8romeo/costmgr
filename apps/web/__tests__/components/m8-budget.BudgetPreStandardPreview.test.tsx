// apps/web/__tests__/components/m8-budget.BudgetPreStandardPreview.test.tsx — Story 8.3
//
// Component tests for BudgetPreStandardPreview (CR 11-4 D-001 page mounts + renders).
// Uses next-intl mock + 8-3 default state.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BudgetPreStandardPreview } from "../../components/m8-budget/BudgetPreStandardPreview";

import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("BudgetPreStandardPreview component (Story 8.3)", () => {
  const baseProps = {
    initialSnapshot: null,
    accessToken: undefined as string | undefined,
    initialError: null as string | null,
  };

  it("renders page title (ko-KR.json SSOT)", () => {
    render(<BudgetPreStandardPreview {...baseProps} />);
    expect(screen.getByText(/예산 사전 표준원가 미리보기/)).toBeInTheDocument();
  });

  it("renders 5-field form labels", () => {
    render(<BudgetPreStandardPreview {...baseProps} />);
    expect(screen.getByLabelText(/예산 기간/)).toBeInTheDocument();
    expect(screen.getByLabelText(/직접재료 단가/)).toBeInTheDocument();
    expect(screen.getByLabelText(/직접노무 단가/)).toBeInTheDocument();
    expect(screen.getByLabelText(/제조경비 배부율/)).toBeInTheDocument();
    expect(screen.getByLabelText(/직접재료 수량/)).toBeInTheDocument();
    expect(screen.getByLabelText(/직접노무 시간/)).toBeInTheDocument();
  });

  it("renders submit + clear buttons", () => {
    render(<BudgetPreStandardPreview {...baseProps} />);
    expect(screen.getByTestId("submit-button")).toBeInTheDocument();
    expect(screen.getByTestId("clear-button")).toBeInTheDocument();
  });

  it("renders pre-standard form", () => {
    render(<BudgetPreStandardPreview {...baseProps} />);
    expect(screen.getByTestId("pre-standard-form")).toBeInTheDocument();
  });

  it("does NOT render snapshot block when initialSnapshot=null", () => {
    render(<BudgetPreStandardPreview {...baseProps} />);
    expect(screen.queryByTestId("pre-standard-cost-table")).toBeNull();
    expect(screen.queryByTestId("pre-standard-hash-badge")).toBeNull();
    expect(screen.queryByTestId("pre-standard-pdf-button")).toBeNull();
  });

  it("renders error banner when initialError set", () => {
    render(<BudgetPreStandardPreview {...baseProps} initialError="fetch_failed" />);
    expect(screen.getByTestId("error-banner")).toBeInTheDocument();
    expect(screen.getByText("fetch_failed")).toBeInTheDocument();
  });

  it("renders snapshot block when initialSnapshot provided", () => {
    const snapshot = {
      snapshot: {
        period_key: "2026-07#B1",
        scenario_index: 1,
        material_cost: "10000",
        labor_cost: "400000",
        overhead_cost: "51250",
        manufacturing_cost: "461250",
        result_hash: "a".repeat(64),
        trace_id: null,
      },
      trace_id: null,
    };
    render(
      <BudgetPreStandardPreview
        {...baseProps}
        initialSnapshot={snapshot}
      />,
    );
    expect(screen.getByTestId("pre-standard-cost-table")).toBeInTheDocument();
    expect(screen.getByTestId("pre-standard-hash-badge")).toBeInTheDocument();
    expect(screen.getByTestId("pre-standard-pdf-button")).toBeInTheDocument();
  });
});