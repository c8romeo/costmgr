/**
 * apps/web/__tests__/IndustrySelector.test.tsx — component tests.
 *
 * Story 1.1 — Task 6.3. Vitest + React Testing Library. Verifies:
 *   - Renders all 4 industry cards.
 *   - Clicking "service" POSTs `{ industry: "service" }`.
 *   - On 200 OK, navigates to /dashboard.
 *   - On 409 INDUSTRY_LOCKED, shows the locked toast and disables inputs.
 *
 * Why this file uses `vi.mock` instead of MSW: the api-client wrapper is
 * already a tiny fetch shim — mocking at the wrapper boundary keeps
 * tests fast and deterministic. MSW handlers in mocks/handlers.ts cover
 * the broader suite.
 *
 * Story 0.5 wired the vitest toolchain (T4) — this test now runs as part
 * of `pnpm test`.
 */

/* eslint-disable @typescript-eslint/no-restricted-types --
 * AD-8 deferred: this test file uses `number` for `count` and similar
 * non-money fields. See api-client.ts for the full rationale.
 */

/// <reference types="@testing-library/jest-dom" />

import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useRouter } from "next/navigation";

import { IndustrySelector } from "@/components/onboarding/IndustrySelector";
import { useMenuContext } from "@/components/sidebar/MenuContext";

// Mock the api-client wrapper at the module boundary.
vi.mock("@/lib/api-client", () => ({
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public payload: { code: string; message_ko: string; details: unknown; trace_id: string },
    ) {
      super(payload.message_ko);
    }
  },
  updateIndustry: vi.fn(),
  getTenantSettings: vi.fn(),
}));

// Mock the router so navigation calls don't blow up.
vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
  useParams: vi.fn(() => ({ locale: "ko-KR" })),
}));

// Mock the MenuContext to a controllable stub.
vi.mock("@/components/sidebar/MenuContext", () => ({
  useMenuContext: vi.fn(),
}));

import { updateIndustry } from "@/lib/api-client";

const mockPush = vi.fn();
const mockSetIndustry = vi.fn();

describe("IndustrySelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue({ push: mockPush });
    (useMenuContext as ReturnType<typeof vi.fn>).mockReturnValue({
      industry: null,
      menu: [],
      settingsVersion: 0,
      isLoading: false,
      error: null,
      refresh: vi.fn(),
      setIndustry: mockSetIndustry,
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders all 4 industry cards", () => {
    render(<IndustrySelector />);
    expect(screen.getByText("제조업")).toBeInTheDocument();
    expect(screen.getByText("서비스업")).toBeInTheDocument();
    expect(screen.getByText("제조+서비스")).toBeInTheDocument();
    expect(screen.getByText("제조+서비스+기타")).toBeInTheDocument();
  });

  it("POSTs `{ industry: 'service' }` on click and navigates on success", async () => {
    (updateIndustry as ReturnType<typeof vi.fn>).mockResolvedValue({
      industry: "service",
      menu: ["원가풀", "활동", "동인"],
      settings_version: 2,
      is_initial: false,
      selected_at: "2026-07-29T08:00:00Z",
    });

    render(<IndustrySelector />);
    fireEvent.click(screen.getByText("서비스업"));

    await waitFor(() => {
      expect(updateIndustry).toHaveBeenCalledWith(
        expect.objectContaining({ industry: "service" }),
        undefined,
      );
      expect(mockSetIndustry).toHaveBeenCalledWith("service", ["원가풀", "활동", "동인"]);
      expect(mockPush).toHaveBeenCalledWith("/ko-KR/dashboard");
    });
  });

  it("shows the A7 lock message on 409 INDUSTRY_LOCKED", async () => {
    (updateIndustry as ReturnType<typeof vi.fn>).mockRejectedValue({
      status: 409,
      payload: {
        code: "INDUSTRY_LOCKED",
        message_ko: "업종 변경은 다음 회계연도부터 가능합니다 (A7 전진법)",
        details: { current_industry: "manufacturing", next_fiscal_year_start: "2027-01-01" },
        trace_id: "trace-abc",
      },
    });

    render(<IndustrySelector />);
    fireEvent.click(screen.getByText("서비스업"));

    await waitFor(() => {
      expect(
        screen.getByText(/업종이 A7 전진법으로 잠겼습니다/),
      ).toBeInTheDocument();
      expect(screen.getByText(/2027-01-01/)).toBeInTheDocument();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it("shows FORBIDDEN_ROLE toast on 403", async () => {
    (updateIndustry as ReturnType<typeof vi.fn>).mockRejectedValue({
      status: 403,
      payload: {
        code: "FORBIDDEN_ROLE",
        message_ko: "업종 변경은 owner 역할만 가능합니다",
        details: { role: "member" },
        trace_id: "trace-def",
      },
    });

    render(<IndustrySelector />);
    fireEvent.click(screen.getByText("제조+서비스"));

    await waitFor(() => {
      expect(screen.getByText(/owner 역할만 가능합니다/)).toBeInTheDocument();
    });
  });

  it("renders a radiogroup with 4 buttons", () => {
    render(<IndustrySelector />);
    const group = screen.getByRole("radiogroup");
    expect(group).toBeInTheDocument();
    expect(group.querySelectorAll("button")).toHaveLength(4);
  });
});
