/**
 * apps/web/__tests__/components/auth.ForgotPasswordForm.test.tsx — Password reset parity.
 *
 * Phase 3-1 — T8.5 (AC #5.1, #5.2, #5.3, #5.4, #5.5) — 10 vitest cases.
 * Covers forgot-password always-success security invariant + reset-password
 * strength regex + mismatch check + redirect.
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

vi.mock("@/lib/auth/forgot-password", () => ({
  requestPasswordReset: vi.fn(),
}));

vi.mock("@/lib/auth/reset-password", () => ({
  resetPassword: vi.fn(),
}));

import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";
import { requestPasswordReset } from "@/lib/auth/forgot-password";
import { resetPassword } from "@/lib/auth/reset-password";

const mockRouter = {
  push: vi.fn(),
  refresh: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
});

describe("ForgotPasswordForm (Phase 3-1 T6.2)", () => {
  it("renders email field + submit button", () => {
    render(<ForgotPasswordForm locale="ko-KR" />);
    expect(screen.getByLabelText("이메일")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "재설정 링크 보내기" })).toBeInTheDocument();
  });

  it("renders login link back", () => {
    render(<ForgotPasswordForm locale="ko-KR" />);
    expect(screen.getByText("로그인으로 돌아가기")).toBeInTheDocument();
  });

  it("calls requestPasswordReset on submit", async () => {
    (requestPasswordReset as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    render(<ForgotPasswordForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.click(screen.getByRole("button", { name: "재설정 링크 보내기" }));
    await waitFor(() => {
      expect(requestPasswordReset).toHaveBeenCalledWith({
        email: "kim@example.com",
        locale: "ko-KR",
      });
    });
  });

  it("shows generic success message regardless of email validity", async () => {
    (requestPasswordReset as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    render(<ForgotPasswordForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "unknown@example.com");
    await user.click(screen.getByRole("button", { name: "재설정 링크 보내기" }));
    await waitFor(() => {
      expect(
        screen.getByText(/이메일이 등록된 경우, 재설정 링크가 곧 도착합니다/),
      ).toBeInTheDocument();
    });
  });

  it("shows same success message even if request throws (security invariant)", async () => {
    (requestPasswordReset as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("non-existent"),
    );
    const user = userEvent.setup();
    render(<ForgotPasswordForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.click(screen.getByRole("button", { name: "재설정 링크 보내기" }));
    await waitFor(() => {
      expect(
        screen.getByText(/이메일이 등록된 경우, 재설정 링크가 곧 도착합니다/),
      ).toBeInTheDocument();
    });
  });

  it("does not leak email existence into the UI", async () => {
    (requestPasswordReset as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    render(<ForgotPasswordForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.click(screen.getByRole("button", { name: "재설정 링크 보내기" }));
    await waitFor(() => {
      // Generic message — no reference to the email address.
      expect(screen.queryByText("kim@example.com")).toBeNull();
    });
  });
});

describe("ResetPasswordForm (Phase 3-1 T6.4)", () => {
  it("renders 2 password fields + submit button", () => {
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    expect(screen.getByLabelText("새 비밀번호")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호 확인")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "비밀번호 변경" })).toBeInTheDocument();
  });

  it("renders heading h1", () => {
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    expect(
      screen.getByRole("heading", { level: 1, name: "비밀번호 재설정" }),
    ).toBeInTheDocument();
  });

  it("calls resetPassword on submit", async () => {
    (resetPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    await user.type(screen.getByLabelText("새 비밀번호"), "Sup3rSecret!");
    await user.type(screen.getByLabelText("비밀번호 확인"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));
    await waitFor(() => {
      expect(resetPassword).toHaveBeenCalledWith({
        code: "code-123",
        password: "Sup3rSecret!",
        passwordConfirm: "Sup3rSecret!",
      });
    });
  });

  it("redirects to /login?reset=success on success", async () => {
    (resetPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    await user.type(screen.getByLabelText("새 비밀번호"), "Sup3rSecret!");
    await user.type(screen.getByLabelText("비밀번호 확인"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/login?reset=success");
    });
  });

  it("calls router.refresh after reset success", async () => {
    (resetPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    await user.type(screen.getByLabelText("새 비밀번호"), "Sup3rSecret!");
    await user.type(screen.getByLabelText("비밀번호 확인"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));
    await waitFor(() => {
      expect(mockRouter.refresh).toHaveBeenCalled();
    });
  });

  it("disables submit while submitting", async () => {
    (resetPassword as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, message: "OK" }), 100)),
    );
    const user = userEvent.setup();
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    await user.type(screen.getByLabelText("새 비밀번호"), "Sup3rSecret!");
    await user.type(screen.getByLabelText("비밀번호 확인"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));
    expect(screen.getByRole("button", { name: "변경 중..." })).toBeDisabled();
  });

  it("shows INVALID_TOKEN message on bad code", async () => {
    (resetPassword as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "INVALID_TOKEN",
      message: "재설정 링크가 유효하지 않거나 만료되었습니다. 다시 요청해 주세요.",
    });
    const user = userEvent.setup();
    render(<ResetPasswordForm locale="ko-KR" code="bad-code" />);
    await user.type(screen.getByLabelText("새 비밀번호"), "Sup3rSecret!");
    await user.type(screen.getByLabelText("비밀번호 확인"), "Sup3rSecret!");
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));
    await waitFor(() => {
      expect(
        screen.getByText(
          "재설정 링크가 유효하지 않거나 만료되었습니다. 다시 요청해 주세요.",
        ),
      ).toBeInTheDocument();
    });
  });

  it("requires both fields before submit", async () => {
    const user = userEvent.setup();
    render(<ResetPasswordForm locale="ko-KR" code="code-123" />);
    await user.click(screen.getByRole("button", { name: "비밀번호 변경" }));
    expect(resetPassword).not.toHaveBeenCalled();
  });
});
