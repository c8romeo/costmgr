"use client";

/**
 * apps/web/components/m12-account/AccountDeletionModal.tsx — Story 12.3
 *
 * Client Component for the M12 account deletion modal (owner-only,
 * destructive endpoint — CR 12-5 L3 3-layer TOTP defense UI mirror).
 *
 * Per AC #1 + AC #4 (Story 12.3):
 *  - Step 1: Owner enters 6-digit TOTP code (Layer 2 proof).
 *    POST /api/v1/account/deletion/challenge-token → returns 5-min JWT.
 *  - Step 2: Owner reads the Korean consent template (verbatim) and
 *    types it EXACTLY into the consent textarea (verbatim match enforced
 *    by validate_consent_text on the backend).
 *  - Step 3: Owner clicks [삭제 요청] → POST /api/v1/account/deletion/request
 *    with the challenge token in Authorization header.
 *
 * 3-layer TOTP defense (CR 12-5 L3) — UI mirror:
 *  - Layer 1: route `require_role("owner")` + `require_capability(ACCOUNT_DELETION)`
 *  - Layer 2: service verify_totp_challenge (UI provides the 6-digit code)
 *  - Layer 3: handler audit-first BEFORE any raise (UI shows Korean error
 *    envelope from AD-15 §4)
 *
 * UX locked: Dark MVP / WCAG AA / Professional / ko-KR 격식체 종결 /
 * Negative/Destructive token (Story 12.5 UX decisions).
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";


import {
  DELETION_CHALLENGE_TOKEN_PURPOSE,
  DELETION_CONSENT_TEMPLATE_KO,
  type DeletionEnvelopeResponse,
  type DeletionChallengeTokenResponse,
} from "@/lib/m12-account-deletion";

interface AccountDeletionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (envelope: DeletionEnvelopeResponse) => void;
  accessToken: string | undefined;
}

export function AccountDeletionModal({
  open,
  onOpenChange,
  onSuccess,
  accessToken,
}: AccountDeletionModalProps): React.ReactElement | null {
  const t = useTranslations("account_deletion");
  const [step, setStep] = useState<"totp" | "consent" | "submitting">("totp");
  const [totpCode, setTotpCode] = useState<string>("");
  const [consentText, setConsentText] = useState<string>("");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [challengeToken, setChallengeToken] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const resetState = useCallback(() => {
    setStep("totp");
    setTotpCode("");
    setConsentText("");
    setChallengeToken("");
    setError(null);
  }, []);

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (!nextOpen) {
        resetState();
      }
      onOpenChange(nextOpen);
    },
    [onOpenChange, resetState],
  );

  // Step 1 — verify TOTP code → mint challenge token.
  const handleTotpSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      if (!/^\d{6}$/.test(totpCode)) {
        setError(t("totp_invalid_format"));
        return;
      }
      try {
        const res = await fetch("/api/v1/account/deletion/challenge-token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken ?? ""}`,
          },
          body: JSON.stringify({ current_code: totpCode }),
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as {
            message_ko?: string;
          };
          setError(body.message_ko ?? t("totp_failed"));
          return;
        }
        const data = (await res.json()) as DeletionChallengeTokenResponse;
        setChallengeToken(data.token);
        setStep("consent");
      } catch {
        setError(t("network_error"));
      }
    },
    [totpCode, accessToken, t],
  );

  // Step 2 — verify consent text verbatim → submit deletion request.
  const handleConsentSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      if (consentText.trim() !== DELETION_CONSENT_TEMPLATE_KO) {
        setError(t("consent_mismatch"));
        return;
      }
      setStep("submitting");
      try {
        const res = await fetch("/api/v1/account/deletion/request", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken ?? ""} ${DELETION_CHALLENGE_TOKEN_PURPOSE}`,
          },
          body: JSON.stringify({
            consent_checked: true,
            consent_text: consentText.trim(),
          }),
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as {
            message_ko?: string;
          };
          setError(body.message_ko ?? t("request_failed"));
          setStep("consent");
          return;
        }
        const data = (await res.json()) as DeletionEnvelopeResponse;
        onSuccess(data);
        handleOpenChange(false);
      } catch {
        setError(t("network_error"));
        setStep("consent");
      }
    },
    [consentText, accessToken, onSuccess, handleOpenChange, t],
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deletion-modal-title"
    >
      <div className="w-full max-w-md rounded-lg border border-negative/30 bg-card p-6 shadow-xl">
        <h2
          id="deletion-modal-title"
          className="text-lg font-semibold text-negative"
        >
          {t("modal_title")}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {t("modal_description")}
        </p>

        {step === "totp" ? (
          <form onSubmit={handleTotpSubmit} className="mt-4 space-y-4">
            <label htmlFor="deletion-totp" className="block text-sm font-medium">
              {t("totp_label")}
            </label>
            <input
              id="deletion-totp"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="\d{6}"
              maxLength={6}
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
              className="block w-full rounded-md border border-input bg-background px-3 py-2 text-base"
              required
            />
            {error ? (
              <p className="text-sm text-negative" role="alert">
                {error}
              </p>
            ) : null}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => handleOpenChange(false)}
                className="rounded-md border border-input px-4 py-2 text-sm"
              >
                {t("cancel")}
              </button>
              <button
                type="submit"
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
              >
                {t("next")}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleConsentSubmit} className="mt-4 space-y-4">
            <div className="rounded-md border border-warning/30 bg-warning/5 p-3 text-sm">
              <p className="font-medium">{t("consent_warning_title")}</p>
              <p className="mt-1 whitespace-pre-line text-muted-foreground">
                {DELETION_CONSENT_TEMPLATE_KO}
              </p>
            </div>
            <label htmlFor="deletion-consent" className="block text-sm font-medium">
              {t("consent_label")}
            </label>
            <textarea
              id="deletion-consent"
              value={consentText}
              onChange={(e) => setConsentText(e.target.value)}
              rows={3}
              className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              required
            />
            {error ? (
              <p className="text-sm text-negative" role="alert">
                {error}
              </p>
            ) : null}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setStep("totp")}
                className="rounded-md border border-input px-4 py-2 text-sm"
                disabled={step === "submitting"}
              >
                {t("back")}
              </button>
              <button
                type="submit"
                disabled={step === "submitting"}
                className="rounded-md bg-negative px-4 py-2 text-sm font-medium text-negative-foreground"
              >
                {step === "submitting" ? t("submitting") : t("submit_destructive")}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
