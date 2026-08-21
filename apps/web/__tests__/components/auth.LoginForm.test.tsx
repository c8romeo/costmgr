/**
 * apps/web/__tests__/components/auth.LoginForm.test.tsx — Login form parity.
 *
 * Phase 3-1 — T8.1 (AC #1.1, #1.2, #1.3) — 15 vitest cases.
 * Covers: render, validation, 5-failure cool-down rate-limit handling,
 * AAL 2FA redirect (aal1 → /auth/2fa, aal2 → /dashboard), ?redirect= preservation,
 * password show/hide toggle, router.refresh on success.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
  useParams: () => ({ locale: "ko-KR" }),
}));

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: vi.fn(),
}));

vi.mock("@/lib/auth/login", () => ({
  signInWithPassword: vi.fn(),
}));

import { LoginForm } from "@/components/auth/LoginForm";
import { signInWithPassword } from "@/lib/auth/login";

const mockRouter = {
  push: vi.fn(),
  refresh: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
});

describe("LoginForm (Phase 3-1 T2.2)", () => {
  it("renders email + password fields and submit button", () => {
    render(<LoginForm locale="ko-KR" />);
    expect(screen.getByLabelText("이메일")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
  });

  it("renders signup link + forgot-password link", () => {
    render(<LoginForm locale="ko-KR" />);
    expect(screen.getByText("회원가입")).toBeInTheDocument();
    expect(screen.getByText("비밀번호 찾기")).toBeInTheDocument();
  });

  it("shows ?reset=success message on resetSuccess=true", () => {
    render(<LoginForm locale="ko-KR" resetSuccess />);
    expect(
      screen.getByText(
        "비밀번호가 성공적으로 변경되었습니다. 다시 로그인해 주세요.",
      ),
    ).toBeInTheDocument();
  });

  it("calls signInWithPassword on submit", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      aal: "aal2",
      message: "OK",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(signInWithPassword).toHaveBeenCalledWith({
        email: "kim@example.com",
        password: "Sup3rSecret!",
      });
    });
  });

  it("redirects to /<locale>/dashboard on aal2 success", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      aal: "aal2",
      message: "OK",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/dashboard");
    });
  });

  it("redirects to /auth/2fa on aal1 success", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      aal: "aal1",
      message: "OK",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/auth/2fa");
    });
  });

  it("preserves ?redirect= query on aal1 redirect", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      aal: "aal1",
      message: "OK",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" redirectTo="/ko-KR/budget" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining("/ko-KR/auth/2fa"),
      );
    });
    const callArg = (mockRouter.push as ReturnType<typeof vi.fn>).mock.calls[0][0];
    expect(callArg).toMatch(/redirect=/);
  });

  it("shows error message on invalid credentials", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "INVALID_CREDENTIALS",
      message: "이메일 또는 비밀번호가 올바르지 않습니다.",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "wrong");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(
        screen.getByText("이메일 또는 비밀번호가 올바르지 않습니다."),
      ).toBeInTheDocument();
    });
  });

  it("shows rate-limited message on RATE_LIMITED", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "RATE_LIMITED",
      message: "로그인 5회 실패로 30초간 제한됩니다.",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "wrong");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(
        screen.getByText(/로그인 5회 실패로 30초간 제한됩니다/),
      ).toBeInTheDocument();
    });
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    const passwordInput = screen.getByLabelText("비밀번호") as HTMLInputElement;
    expect(passwordInput.type).toBe("password");
    // Button has aria-label "비밀번호 보기" — match by full accessible name.
    await user.click(screen.getByRole("button", { name: "비밀번호 보기" }));
    expect(passwordInput.type).toBe("text");
  });

  it("preserves ?redirect= on dashboard redirect", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      aal: "aal2",
      message: "OK",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" redirectTo="/ko-KR/budget" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/budget");
    });
  });

  it("disables submit button while submitting", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, aal: "aal2", message: "OK" }), 100)),
    );
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    expect(screen.getByRole("button", { name: "로그인 중..." })).toBeDisabled();
  });

  it("calls router.refresh after successful redirect", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      aal: "aal2",
      message: "OK",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(mockRouter.refresh).toHaveBeenCalled();
    });
  });

  it("does not redirect on invalid credentials", async () => {
    (signInWithPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "INVALID_CREDENTIALS",
      message: "이메일 또는 비밀번호가 올바르지 않습니다.",
    });
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), "wrong");
    await user.click(screen.getByRole("button", { name: "로그인" }));
    await waitFor(() => {
      expect(mockRouter.push).not.toHaveBeenCalled();
    });
  });

  it("requires email + password before submit", async () => {
    const user = userEvent.setup();
    render(<LoginForm locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "로그인" }));
    // HTML5 required prevents submission → signInWithPassword not called.
    expect(signInWithPassword).not.toHaveBeenCalled();
  });
});
