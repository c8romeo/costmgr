/**
 * apps/web/components/m12-account/TwoFactorSetupForm.tsx — Story 12.5
 *
 * M12 2FA setup wizard (AC #3, 3-step wizard with manual entry only).
 *
 * Step 1: 안내 + base32 secret (4-자리 그룹 포맷) + otpauth URI
 *         + "복사" 버튼 (sonner toast)
 * Step 2: 6-digit TOTP code input + [확인] → POST /verify
 * Step 3: 8 recovery codes 1회 표시 + 각 코드별 복사 + 모두 복사 +
 *         "저장했습니다" 체크박스 + [완료]
 *
 * QR 미사용 (user decision 2026-08-12): `otpauth://` URI 텍스트 노출 +
 * secret base32 4-자리 그룹 포맷 (`JBSW Y3DP EHPK 3PXP`) + 복사 버튼.
 *   - 의존성 0개 (qrcode / qrcode.react 라이브러리 없음)
 *   - STACK_PIN BUMP 없음
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::two_factor_setup_panel.
 * AD-15 §11 envelope + AD-10 owner/member role gate (handled server-side).
 */

"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

export interface TwoFactorSetupFormProps {
  /** Base32 secret returned from POST /api/v1/account/2fa/setup (4-자리 그룹으로 표시). */
  secret: string;
  /** otpauth URI returned from POST /setup. */
  uri: string;
  /** Account email — embedded into the URI for client UX only. */
  email?: string;
  /** 8 recovery codes returned from POST /setup (1회만 표시). */
  recovery_codes: string[];
  /** Submit handler — receives the 6-digit code as input. */
  onVerify?: (code: string) => Promise<{ ok: boolean; error_ko?: string }>;
  /** Click handler for final step [완료] (typically router.push('/m2-input')). */
  onComplete?: () => void;
  /** Optional className override. */
  className?: string;
}

type Step = "intro" | "verify" | "recovery";

/**
 * formatSecretWithGroups — split base32 secret into 4-자리 groups (e.g. "JBSW Y3DP EHPK 3PXP").
 *
 * Pure helper (no React state) — extracted so it can be unit-tested in isolation.
 * Strips existing whitespace, re-emits in uppercase, pads with empty groups as needed.
 */
export function formatSecretWithGroups(secret: string): string {
  const clean = secret.replace(/\s+/g, "").toUpperCase();
  const groups: string[] = [];
  for (let i = 0; i < clean.length; i += 4) {
    groups.push(clean.slice(i, i + 4));
  }
  return groups.join(" ");
}

/**
 * TwoFactorSetupForm — client component for the 3-step 2FA enrollment wizard.
 *
 * Step machine driven by `step` state. After step 3 (recovery codes acknowledged),
 * the parent route typically calls `onComplete` to redirect the user into
 * /m2-input (where TwoFactorGuard now passes).
 */
export function TwoFactorSetupForm({
  secret,
  uri,
  email,
  // eslint-disable-next-line camelcase
  recovery_codes,
  onVerify,
  onComplete,
  className,
}: TwoFactorSetupFormProps): React.ReactElement {
  const t = useTranslations("two_factor_setup_panel");
  const router = useRouter();

  const [step, setStep] = React.useState<Step>("intro");
  const [code, setCode] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [savedChecked, setSavedChecked] = React.useState(false);

  const secretFormatted = React.useMemo(
    () => formatSecretWithGroups(secret),
    [secret],
  );

  // ── clipboard helpers ────────────────────────────────────────
  const copyToClipboard = async (text: string, label: string) => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(text);
        toast.success(`${label} 복사 완료`);
      } else {
        toast.error("클립보드 접근 불가");
      }
    } catch {
      toast.error("복사 실패");
    }
  };

  const handleCopyAllRecovery = async () => {
    // eslint-disable-next-line camelcase
    const joined = recovery_codes.join("\n");
    await copyToClipboard(joined, "복구 코드 8개");
  };

  // ── verify step submit ───────────────────────────────────────
  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    if (!/^\d{6}$/.test(code)) {
      toast.error(t("step2_description"));
      return;
    }
    setSubmitting(true);
    try {
      if (onVerify) {
        const result = await onVerify(code);
        if (result.ok) {
          toast.success(t("setup_success_toast"));
          setStep("recovery");
          setCode("");
        } else {
          toast.error(result.error_ko ?? "인증 실패");
        }
      } else {
        // Default: assume parent wires submit externally; advance on local success.
        toast.success(t("setup_success_toast"));
        setStep("recovery");
        setCode("");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = () => {
    if (onComplete) onComplete();
    else router.refresh();
  };

  return (
    <div
      data-testid="two-factor-setup-form"
      data-step={step}
      className={
        "space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm " +
        (className ?? "")
      }
    >
      <h2 className="text-lg font-semibold text-slate-900">
        {t("panel_title")}
      </h2>

      {step === "intro" && (
        <div className="space-y-4" data-testid="setup-step-intro">
          <div>
            <h3 className="text-sm font-medium text-slate-700">
              {t("step1_title")}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              {t("step1_description")}
            </p>
          </div>

          {/* Base32 secret 4-자리 그룹 + 복사 버튼 */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-500">
              {t("secret_label")}
            </label>
            <div
              data-testid="setup-secret"
              className="flex items-center gap-2 rounded-md border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-base tracking-wider text-slate-900"
            >
              <span className="flex-1 select-all break-all">
                {secretFormatted}
              </span>
              <button
                type="button"
                onClick={() => copyToClipboard(secretFormatted, "비밀키")}
                className="rounded-md bg-blue-700 px-3 py-1 text-xs font-medium text-white hover:bg-blue-600"
                data-testid="setup-secret-copy-button"
              >
                복사
              </button>
            </div>
          </div>

          {/* otpauth URI 텍스트 + 복사 */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-500">
              {t("uri_label")}
            </label>
            <div className="flex items-start gap-2 rounded-md border border-slate-300 bg-slate-50 px-3 py-2">
              <code
                data-testid="setup-uri"
                className="flex-1 select-all break-all text-xs text-slate-700"
              >
                {uri}
              </code>
              <button
                type="button"
                onClick={() => copyToClipboard(uri, "URI")}
                className="rounded-md bg-slate-200 px-3 py-1 text-xs font-medium text-slate-800 hover:bg-slate-300"
                data-testid="setup-uri-copy-button"
              >
                복사
              </button>
            </div>
            {email ? (
              <p className="text-xs text-slate-500">계정: {email}</p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={() => setStep("verify")}
            className="w-full rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
            data-testid="setup-intro-next-button"
          >
            다음
          </button>
        </div>
      )}

      {step === "verify" && (
        <form
          onSubmit={handleVerifySubmit}
          className="space-y-4"
          data-testid="setup-step-verify"
        >
          <div>
            <h3 className="text-sm font-medium text-slate-700">
              {t("step2_title")}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              {t("step2_description")}
            </p>
          </div>

          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
            placeholder="000000"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-center font-mono text-lg tracking-widest text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
            aria-label={t("step2_title")}
            data-testid="setup-verify-code-input"
            required
            autoComplete="one-time-code"
          />

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setStep("intro")}
              className="flex-1 rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-300"
              data-testid="setup-verify-back-button"
            >
              이전
            </button>
            <button
              type="submit"
              disabled={submitting || !/^\d{6}$/.test(code)}
              className="flex-1 rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
              data-testid="setup-verify-submit-button"
            >
              {submitting ? "확인 중..." : t("verify_button")}
            </button>
          </div>
        </form>
      )}

      {step === "recovery" && (
        <div className="space-y-4" data-testid="setup-step-recovery">
          <div>
            <h3 className="text-sm font-medium text-slate-700">
              {t("recovery_codes_title")}
            </h3>
          </div>

          <div
            className="grid grid-cols-2 gap-2"
            data-testid="setup-recovery-codes"
          >
            {/* eslint-disable-next-line camelcase */}
            {recovery_codes.map((rc, idx) => (
              <div
                key={`${rc}-${idx}`}
                className="flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-2 py-1"
              >
                <code
                  data-testid="setup-recovery-code"
                  className="flex-1 select-all break-all font-mono text-xs text-slate-800"
                >
                  {rc}
                </code>
                <button
                  type="button"
                  onClick={() => copyToClipboard(rc, `복구 코드 ${idx + 1}`)}
                  className="rounded bg-slate-200 px-2 py-0.5 text-xs text-slate-700 hover:bg-slate-300"
                  data-testid="setup-recovery-code-copy-button"
                  aria-label={`복구 코드 ${idx + 1} 복사`}
                >
                  복사
                </button>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={handleCopyAllRecovery}
            className="w-full rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-300"
            data-testid="setup-recovery-copy-all-button"
          >
            모두 복사
          </button>

          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={savedChecked}
              onChange={(e) => setSavedChecked(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300"
              data-testid="setup-recovery-saved-checkbox"
            />
            저장했습니다
          </label>

          <button
            type="button"
            onClick={handleComplete}
            disabled={!savedChecked}
            className="w-full rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
            data-testid="setup-complete-button"
          >
            완료
          </button>
        </div>
      )}
    </div>
  );
}
