/**
 * apps/web/__tests__/components/auth.LogoutButton.test.tsx — Logout button parity.
 *
 * Phase 3-1 — T8.4 (AC #4.1, #4.2) — 8 vitest cases.
 * Covers: fetch POST /api/auth/logout, redirect to /login on success,
 * network error display, button disable while submitting.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

import { LogoutButton } from "@/components/auth/LogoutButton";

const mockRouter = {
  push: vi.fn(),
  refresh: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
  globalThis.fetch = vi.fn();
});

describe("LogoutButton (Phase 3-1 T5.2)", () => {
  it("renders logout button", () => {
    render(<LogoutButton locale="ko-KR" />);
    expect(screen.getByRole("button", { name: "로그아웃" })).toBeInTheDocument();
  });

  it("calls POST /<locale>/api/auth/logout on click", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ redirect: "/ko-KR/login" }),
    });
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/ko-KR/api/auth/logout",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("redirects to /<locale>/login on success", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ redirect: "/ko-KR/login" }),
    });
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/login");
    });
  });

  it("calls router.refresh after logout", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ redirect: "/ko-KR/login" }),
    });
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    await waitFor(() => {
      expect(mockRouter.refresh).toHaveBeenCalled();
    });
  });

  it("uses server-redirect target if provided", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ redirect: "/ko-KR/login?loggedOut=true" }),
    });
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/login?loggedOut=true");
    });
  });

  it("shows error message on fetch failure", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      json: async () => ({ code: "INTERNAL_ERROR" }),
    });
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    await waitFor(() => {
      expect(
        screen.getByText("로그아웃에 실패했습니다. 잠시 후 다시 시도해 주세요."),
      ).toBeInTheDocument();
    });
  });

  it("shows NETWORK_ERROR message on network error", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("network failure"),
    );
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    await waitFor(() => {
      expect(
        screen.getByText("네트워크 오류로 로그아웃하지 못했습니다."),
      ).toBeInTheDocument();
    });
  });

  it("disables button while submitting", async () => {
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 100)),
    );
    const user = userEvent.setup();
    render(<LogoutButton locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그아웃" }));
    expect(screen.getByRole("button", { name: "로그아웃 중..." })).toBeDisabled();
  });
});
