// apps/web/__tests__/components/m8-budget-variance.VariancePdfButton.test.tsx — Story 8.3
//
// Component tests for VariancePdfButton (8-3 wire activation).
// 8-2: button was disabled with "8-3 follow-up" tooltip.
// 8-3: button is enabled with "§9 #20 예산-실적 차이 명세서 PDF" tooltip.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { VariancePdfButton } from "../../components/m8-budget-variance/VariancePdfButton";

import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("VariancePdfButton component (Story 8.3 — 8-2 wire activation)", () => {
  const baseProps = {
    accessToken: undefined as string | undefined,
    periodKey: "2026-07#B1",
  };

  it("renders the PDF button (8-3: enabled, not disabled-by-default)", () => {
    render(<VariancePdfButton {...baseProps} />);
    const button = screen.getByTestId("variance-pdf-button");
    expect(button).toBeInTheDocument();
    expect(button).toBeEnabled();
  });

  it("uses 'ready' tooltip (8-3: not '8-3 follow-up')", () => {
    render(<VariancePdfButton {...baseProps} />);
    const button = screen.getByTestId("variance-pdf-button");
    expect(button.getAttribute("title")).toContain("예산-실적 차이 명세서 PDF");
  });

  it("renders 8-3 activation note (replaces 8-2 envelope-only note)", () => {
    render(<VariancePdfButton {...baseProps} />);
    expect(screen.getByText(/8-3 활성화/)).toBeInTheDocument();
  });

  it("renders the Korean PDF button label", () => {
    render(<VariancePdfButton {...baseProps} />);
    expect(screen.getByText(/PDF 내보내기/)).toBeInTheDocument();
  });
});