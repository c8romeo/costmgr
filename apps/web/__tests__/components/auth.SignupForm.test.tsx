/**
 * apps/web/__tests__/components/auth.SignupForm.test.tsx — Signup form parity.
 *
 * Phase 3-1 — T8.2 (AC #2.1, #2.2, #2.3, #2.4, #2.5) — 15 vitest cases.
 * Covers 4-field form (email, password, password_confirm, company_name),
 * pre-onboarding flow (`signUpAndCreateTenant`), email-verification-pending
 * redirect.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
  useParams: () => ({ locale: "ko-KR" }),
}));

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: vi.fn(),
}));

vi.mock("@/lib/auth/signup", () => ({
  signUpAndCreateTenant: vi.fn(),
}));

import { SignupForm } from "@/components/auth/SignupForm";
import { signUpAndCreateTenant } from "@/lib/auth/signup";

const mockRouter = {
  push: vi.fn(),
  refresh: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
});

const TYPED_COMPANY = "Acme Inc.";
const TYPED_PASSWORD = "Sup3rSecret!";

describe("SignupForm (Phase 3-1 T3.2)", () => {
  it("renders 4 fields + submit button", () => {
    render(<SignupForm locale="ko-KR" />);
    expect(screen.getByLabelText("이메일")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호")).toBeInTheDocument();
    expect(screen.getByLabelText("비밀번호 확인")).toBeInTheDocument();
    expect(screen.getByLabelText("회사명")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "가입하기" })).toBeInTheDocument();
  });

  it("renders login link back", () => {
    render(<SignupForm locale="ko-KR" />);
    expect(screen.getByText("로그인으로 돌아가기")).toBeInTheDocument();
  });

  it("calls signUpAndCreateTenant on submit", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      requiresEmailVerification: true,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(signUpAndCreateTenant).toHaveBeenCalledWith({
        email: "kim@example.com",
        password: TYPED_PASSWORD,
        passwordConfirm: TYPED_PASSWORD,
        companyName: TYPED_COMPANY,
      });
    });
  });

  it("redirects to email-verification-pending when requiresEmailVerification", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      requiresEmailVerification: true,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith(
        "/ko-KR/signup/email-verification-pending",
      );
    });
  });

  it("redirects to /onboarding/industry when NOT requiresEmailVerification", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      requiresEmailVerification: false,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith("/ko-KR/onboarding/industry");
    });
  });

  it("shows error message on failure", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "SIGNUP_FAILED",
      message: "가입에 실패했습니다.",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(screen.getByText("가입에 실패했습니다.")).toBeInTheDocument();
    });
  });

  it("does not redirect on failure", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "SIGNUP_FAILED",
      message: "가입에 실패했습니다.",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(mockRouter.push).not.toHaveBeenCalled();
    });
  });

  it("disables submit while submitting", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, requiresEmailVerification: true, message: "OK" }), 100)),
    );
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    expect(screen.getByRole("button", { name: "가입 중..." })).toBeDisabled();
  });

  it("preserves email value on failure", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      code: "SIGNUP_FAILED",
      message: "가입에 실패했습니다.",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(
        (screen.getByLabelText("이메일") as HTMLInputElement).value,
      ).toBe("kim@example.com");
    });
  });

  it("requires email format (HTML5 type=email)", () => {
    render(<SignupForm locale="ko-KR" />);
    const emailInput = screen.getByLabelText("이메일") as HTMLInputElement;
    expect(emailInput.type).toBe("email");
  });

  it("requires all fields before submit", async () => {
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    expect(signUpAndCreateTenant).not.toHaveBeenCalled();
  });

  it("calls router.refresh after redirect", async () => {
    (signUpAndCreateTenant as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      requiresEmailVerification: true,
      message: "OK",
    });
    const user = userEvent.setup();
    render(<SignupForm locale="ko-KR" />);
    await user.type(screen.getByLabelText("이메일"), "kim@example.com");
    await user.type(screen.getByLabelText("비밀번호"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("비밀번호 확인"), TYPED_PASSWORD);
    await user.type(screen.getByLabelText("회사명"), TYPED_COMPANY);
    await user.click(screen.getByRole("button", { name: "가입하기" }));
    await waitFor(() => {
      expect(mockRouter.refresh).toHaveBeenCalled();
    });
  });

  it("company name has maxLength=100", () => {
    render(<SignupForm locale="ko-KR" />);
    const companyInput = screen.getByLabelText("회사명") as HTMLInputElement;
    expect(companyInput.maxLength).toBe(100);
  });

  it("password field type is password (hidden)", () => {
    render(<SignupForm locale="ko-KR" />);
    const passwordInput = screen.getByLabelText("비밀번호") as HTMLInputElement;
    expect(passwordInput.type).toBe("password");
  });

  it("password confirm field type is password", () => {
    render(<SignupForm locale="ko-KR" />);
    const confirmInput = screen.getByLabelText("비밀번호 확인") as HTMLInputElement;
    expect(confirmInput.type).toBe("password");
  });

  it("renders heading h1", () => {
    render(<SignupForm locale="ko-KR" />);
    expect(screen.getByRole("heading", { level: 1, name: "회원가입" })).toBeInTheDocument();
  });
});
