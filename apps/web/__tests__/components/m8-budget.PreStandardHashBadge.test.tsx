// apps/web/__tests__/components/m8-budget.PreStandardHashBadge.test.tsx — Story 8.3
//
// Component tests for PreStandardHashBadge.

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PreStandardHashBadge } from "../../components/m8-budget/PreStandardHashBadge";
import koKR from "../../messages/ko-KR.json";

vi.mock("next-intl", () => ({
  useTranslations: (namespace: string) => {
    return (key: string) => {
      const messages = (koKR as unknown as Record<string, Record<string, string>>)[namespace];
      return messages?.[key] ?? `[${namespace}.${key}]`;
    };
  },
}));

describe("PreStandardHashBadge component (Story 8.3)", () => {
  const hash = "a".repeat(64);

  it("renders hash badge label", () => {
    render(<PreStandardHashBadge resultHash={hash} />);
    expect(screen.getByText(/결정론 해시:/)).toBeInTheDocument();
  });

  it("renders first 12 chars + ellipsis", () => {
    render(<PreStandardHashBadge resultHash={hash} />);
    expect(screen.getByText(/aaaaaaaaaaaa…/)).toBeInTheDocument();
  });

  it("stores full hash in title (hover tooltip)", () => {
    render(<PreStandardHashBadge resultHash={hash} />);
    const span = screen.getByText(/aaaaaaaaaaaa…/);
    expect(span.getAttribute("title")).toBe(hash);
  });

  it("renders copy button", () => {
    render(<PreStandardHashBadge resultHash={hash} />);
    expect(screen.getByTestId("hash-copy-button")).toBeInTheDocument();
    expect(screen.getByText(/전체 복사/)).toBeInTheDocument();
  });
});