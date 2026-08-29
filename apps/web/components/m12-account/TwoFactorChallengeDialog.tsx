/**
 * apps/web/components/m12-account/TwoFactorChallengeDialog.tsx — Story 12.5
 *
 * M12 2FA challenge dialog (AC #3 + AC #6). Modal dialog shown when
 * /m2-entry-gate returns `requires_challenge=true` (user is 2FA-enrolled
 * but hasn't passed a fresh TOTP challenge in this session).
 *
 * Features:
 *  - 6-digit TOTP input OR recovery code input (toggle via "복구 코드 사용" link)
 *  - 5회 실패 → 429 → lockout message + Retry-After countdown
 *    (based on server-supplied `lockout_until` ISO-8601)
 *  - sonner toast feedback on success/failure
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::two_factor_guard.
 *
 * Server endpoints (per Story 12.4 + 12.5 wire):
 *  - POST /api/v1/account/2fa/challenge  (TOTP mode)
 *  - POST /api/v1/account/2fa/recovery   (recovery code mode)
 *
 * The dialog mounts at the M2 entry guard boundary; the parent decides
 * success state via `onSuccess` (typically router.refresh → re-fetch gate).
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

export interface TwoFactorChallengeDialogProps {
  /** Whether the dialog is open. */
  open: boolean;
  /** Lockout expiry ISO-8601 if user is locked out. */
  lockout_until?: string | null;
  /** Submit handlers — receive the code and return ok/error envelope. */
  onChallenge?: (
    code: string,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  ) => Promise<{ ok: boolean; retry_after_seconds?: number; error_ko?: string }>;
  onRecovery?: (
    code: string,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  ) => Promise<{ ok: boolean; retry_after_seconds?: number; error_ko?: string }>;
  /** Callback after successful challenge/recovery. */
  onSuccess?: () => void;
  /** Cancel handler — close dialog without submitting. */
  onCancel?: () => void;
  /** Optional className override. */
  className?: string;
}

type Mode = "totp" | "recovery";

/**
 * useCountdown — derives seconds remaining from an ISO-8601 expiry.
 * Returns 0 when expired.
 */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
// eslint-disable-next-line camelcase
function useCountdown(until_iso: string | null | undefined): number {
  const [now, setNow] = React.useState(() => Date.now());
  React.useEffect(() => {
    // eslint-disable-next-line camelcase
    if (!until_iso) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  // eslint-disable-next-line camelcase
  }, [until_iso]);

  // eslint-disable-next-line camelcase
  if (!until_iso) return 0;
  const target = Date.parse(until_iso);
  if (Number.isNaN(target)) return 0;
  const diff = Math.max(0, Math.floor((target - now) / 1000));
  return diff;
}

// eslint-disable-next-line @typescript-eslint/no-restricted-types
// eslint-disable-next-line camelcase
function formatMmSs(total_seconds: number): string {
  // eslint-disable-next-line camelcase
  const mm = Math.floor(total_seconds / 60)
    .toString()
    .padStart(2, "0");
  // eslint-disable-next-line camelcase
  const ss = (total_seconds % 60).toString().padStart(2, "0");
  return `${mm}:${ss}`;
}

/**
 * TwoFactorChallengeDialog — modal dialog for 2FA challenge / recovery.
 *
 * Implements Korean-locked labels (ko-KR.json SSOT), WCAG AA contrast,
 * and a server-driven Retry-After countdown when locked out.
 */
export function TwoFactorChallengeDialog({
  open,
  // eslint-disable-next-line camelcase
  lockout_until,
  onChallenge,
  onRecovery,
  onSuccess,
  onCancel,
  className,
}: TwoFactorChallengeDialogProps): React.ReactElement | null {
  const t = useTranslations("two_factor_guard");
  const [mode, setMode] = React.useState<Mode>("totp");
  const [code, setCode] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [retryAfterSeconds, setRetryAfterSeconds] = React.useState<
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    number | null
  >(null);

  const lockoutCountdown = useCountdown(lockout_until);
  const lockedOut = lockoutCountdown > 0;

  // Reset code when dialog re-opens or mode toggles.
  React.useEffect(() => {
    if (open) setCode("");
  }, [open, mode]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting || lockedOut) return;
    const handler = mode === "totp" ? onChallenge : onRecovery;
    if (!handler) {
      toast.error(t("network_error_toast"));
      return;
    }

    // TOTP = 6 digits, Recovery code = Crockford base32 10 chars.
    const expected = mode === "totp" ? /^\d{6}$/ : /^[0-9A-Z]{10}$/i;
    if (!expected.test(code.trim())) {
      toast.error(t("invalid_code_toast"));
      return;
    }

    setSubmitting(true);
    try {
      const result = await handler(code.trim());
      if (result.ok) {
        toast.success(
          mode === "totp" ? t("challenge_passed_toast") : t("recovery_passed_toast"),
        );
        if (onSuccess) onSuccess();
      } else {
        if (result.retry_after_seconds) {
          setRetryAfterSeconds(result.retry_after_seconds);
        }
        toast.error(result.error_ko ?? t("invalid_code_toast"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const effectiveLockoutSeconds =
    retryAfterSeconds ?? (lockedOut ? lockoutCountdown : null);

  return (
    <div
      data-testid="two-factor-challenge-dialog"
      data-mode={mode}
      role="dialog"
      aria-modal="true"
      aria-labelledby="tfc-dialog-title"
      className={
        "fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 " +
        (className ?? "")
      }
    >
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-xl">
        <h2
          id="tfc-dialog-title"
          className="text-lg font-semibold text-slate-900"
        >
          {mode === "totp"
            ? t("challenge_required_label")
            : t("challenge_recovery_label")}
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          {mode === "totp"
            ? t("challenge_required_description")
            : t("challenge_recovery_placeholder")}
        </p>

        {effectiveLockoutSeconds ? (
          <div
            data-testid="tfc-lockout-message"
            className="mt-3 rounded-md border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-800"
            role="alert"
          >
            {t("locked_out_label")} — {formatMmSs(effectiveLockoutSeconds)}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <input
            type="text"
            inputMode={mode === "totp" ? "numeric" : "text"}
            pattern={mode === "totp" ? "[0-9]{6}" : "[0-9A-Z]{10}"}
            maxLength={mode === "totp" ? 6 : 10}
            placeholder={
              mode === "totp"
                ? t("challenge_input_placeholder")
                : t("challenge_recovery_placeholder")
            }
            value={code}
            onChange={(e) =>
              setCode(
                mode === "totp"
                  ? e.target.value.replace(/\D/g, "")
                  : e.target.value.replace(/\s+/g, ""),
              )
            }
            disabled={effectiveLockoutSeconds !== null}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-center font-mono text-base tracking-widest text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:bg-slate-100 disabled:text-slate-400"
            data-testid="tfc-code-input"
            autoFocus
            required
            autoComplete="one-time-code"
          />

          <div className="flex gap-2">
            {onCancel ? (
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-300"
                data-testid="tfc-cancel-button"
              >
                취소
              </button>
            ) : null}
            <button
              type="submit"
              disabled={
                submitting ||
                !code.trim() ||
                effectiveLockoutSeconds !== null
              }
              className="flex-1 rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
              data-testid="tfc-submit-button"
            >
              {submitting
                ? "확인 중..."
                : mode === "totp"
                  ? t("challenge_submit_button")
                  : t("recovery_submit_button")}
            </button>
          </div>

          <button
            type="button"
            onClick={() => setMode((m) => (m === "totp" ? "recovery" : "totp"))}
            className="w-full text-xs text-blue-700 underline hover:text-blue-800"
            data-testid="tfc-mode-toggle"
          >
            {mode === "totp"
              ? t("challenge_recovery_label")
              : t("challenge_required_label")}
          </button>
        </form>
      </div>
    </div>
  );
}
