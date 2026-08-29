/**
 * apps/web/components/m12-account/TwoFactorDisableForm.tsx — Story 12.5
 *
 * M12 2FA disable form (AC #3 + AC #2 owner-only).
 *
 * Server-side gate: handler enforces `require_role("owner")` (12-4 P-14
 * keep). The form receives `is_owner` from the parent route — when false,
 * the form is replaced with a static informational banner.
 *
 * Workflow:
 *  1. User enters current 6-digit TOTP code (proof of possession).
 *  2. Optional reason textarea (admin override requires ≥20 chars).
 *  3. POST /api/v1/account/2fa/disable → sonner toast feedback.
 *  4. Parent route should `router.refresh()` to re-fetch TOTP status.
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::two_factor_disable_panel.
 */

"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

export interface TwoFactorDisableFormProps {
  /** Whether the current user is owner (server-enforced role gate). */
  is_owner: boolean;
  /** Submit handler — receives the code + optional reason. */
  onDisable?: (
    code: string,
    reason: string,
  ) => Promise<{ ok: boolean; error_ko?: string }>;
  /** Optional className override. */
  className?: string;
}

/**
 * TwoFactorDisableForm — owner-only 2FA disable form.
 *
 * When `is_owner=false`, renders an info banner explaining the role gate
 * instead of the form (defense-in-depth: role gate is also enforced
 * server-side at the handler dependency).
 */
export function TwoFactorDisableForm({
  // eslint-disable-next-line camelcase
  is_owner,
  onDisable,
  className,
}: TwoFactorDisableFormProps): React.ReactElement {
  const t = useTranslations("two_factor_disable_panel");
  const router = useRouter();

  const [code, setCode] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [showConfirm, setShowConfirm] = React.useState(false);

  // eslint-disable-next-line camelcase
  if (!is_owner) {
    return (
      <div
        data-testid="two-factor-disable-form-non-owner"
        className={
          "rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 " +
          (className ?? "")
        }
      >
        owner만 2FA를 비활성화할 수 있습니다.
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    if (!/^\d{6}$/.test(code)) {
      toast.error("6자리 코드를 입력하세요");
      return;
    }
    if (!showConfirm) {
      setShowConfirm(true);
      return;
    }

    setSubmitting(true);
    try {
      if (onDisable) {
        const result = await onDisable(code, reason.trim());
        if (result.ok) {
          toast.success(t("disable_success_toast"));
          router.refresh();
        } else {
          toast.error(result.error_ko ?? "비활성화 실패");
        }
      } else {
        toast.success(t("disable_success_toast"));
        router.refresh();
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      data-testid="two-factor-disable-form"
      className={
        "space-y-4 rounded-lg border border-red-200 bg-white p-6 shadow-sm " +
        (className ?? "")
      }
    >
      <h2 className="text-lg font-semibold text-slate-900">
        {t("panel_title")}
      </h2>
      <p className="text-sm text-slate-600">{t("description")}</p>

      <div className="space-y-1">
        <label className="text-xs font-medium text-slate-500">
          {t("code_label")}
        </label>
        <input
          type="text"
          inputMode="numeric"
          pattern="[0-9]{6}"
          maxLength={6}
          placeholder={t("code_placeholder")}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-center font-mono text-base tracking-widest text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          aria-label={t("code_label")}
          data-testid="disable-code-input"
          required
          autoComplete="one-time-code"
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-slate-500">
          {t("reason_label")}
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          aria-label={t("reason_label")}
          data-testid="disable-reason-textarea"
        />
      </div>

      {showConfirm ? (
        <div
          data-testid="disable-confirm-dialog"
          className="rounded-md border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-800"
          role="alert"
        >
          2FA를 비활성화하시겠습니까? 비활성화 후 재설정이 필요합니다.
        </div>
      ) : null}

      <button
        type="submit"
        disabled={submitting || !/^\d{6}$/.test(code)}
        className="w-full rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-50"
        data-testid="disable-submit-button"
      >
        {submitting
          ? "처리 중..."
          : showConfirm
            ? "확인"
            : t("submit_button")}
      </button>
    </form>
  );
}
