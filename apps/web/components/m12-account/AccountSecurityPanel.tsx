/**
 * apps/web/components/m12-account/AccountSecurityPanel.tsx — Story 12.5
 *
 * Orchestration client component for /account/security page.
 *
 * Reads init state from RSC parent (status, role, recovery_codes_remaining).
 * On mount, if user is disabled, fetches setup data (secret + URI + recovery
 * codes) from POST /api/v1/account/2fa/setup, then drives 2FA setup flow:
 *   - TwoFactorSetupForm renders with the fetched payload.
 *   - On verify success → transition to recovery codes display.
 *   - On TOTP code error → sonner toast.
 *
 * Layout per AC #4:
 *   - <TwoFactorStatusBadge> (header)
 *   - <TwoFactorSetupForm> if status.enabled=false
 *   - <TwoFactorDisableForm> if status.enabled=true AND is_owner
 *   - Recovery codes panel (display only) when status.enabled=true
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::account_security.
 */

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { TwoFactorStatusBadge } from "./TwoFactorStatusBadge";
import { TwoFactorSetupForm, formatSecretWithGroups } from "./TwoFactorSetupForm";
import { TwoFactorDisableForm } from "./TwoFactorDisableForm";

export interface AccountSecurityPanelProps {
  /** Whether 2FA is currently enrolled for this user. */
  totp_enabled: boolean;
  /** TOTP enabled_at (ISO-8601), null when disabled. */
  totp_enabled_at: string | null;
  /** Recovery codes remaining, null when disabled. */
  recovery_codes_remaining: number | null;
  /** Whether the user is currently locked out. */
  locked_out: boolean;
  /** Lockout expiry ISO-8601, null when not locked. */
  lockout_until: string | null;
  /** Current user's role (for owner-only disable form). */
  role: string;
  /** Access token forwarded from RSC layout (F-1, F-38). */
  accessToken?: string;
}

interface SetupData {
  secret: string;
  uri: string;
  recovery_codes: string[];
}

export function AccountSecurityPanel(props: AccountSecurityPanelProps): React.ReactElement {
  const t = useTranslations("account_security");
  const router = useRouter();
  const accessToken = props.accessToken;

  const [loading, setLoading] = React.useState(false);
  const [setupData, setSetupData] = React.useState<SetupData | null>(null);
  const [verifying, setVerifying] = React.useState(false);

  const isOwner = props.role === "owner";

  const status = props.locked_out
    ? "locked"
    : props.totp_enabled
      ? "enabled"
      : "disabled";

  // Eagerly request setup data when status='disabled'.
  React.useEffect(() => {
    if (status !== "disabled") return;
    if (setupData) return;
    if (!accessToken) return;
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const res = await fetch("/api/v1/account/2fa/setup", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({}),
        });
        if (cancelled) return;
        if (!res.ok) {
          toast.error("2FA 설정 데이터를 가져오지 못했습니다");
          return;
        }
        const data = (await res.json()) as {
          secret?: string;
          uri?: string;
          recovery_codes?: string[];
        };
        if (data.secret && data.uri && data.recovery_codes) {
          setSetupData({
            secret: data.secret,
            uri: data.uri,
            recovery_codes: data.recovery_codes,
          });
        }
      } catch {
        if (!cancelled) toast.error("네트워크 오류");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [status, setupData, accessToken]);

  const handleVerify = async (code: string) => {
    if (!accessToken) {
      return { ok: false, error_ko: "인증 토큰 없음" };
    }
    setVerifying(true);
    try {
      const res = await fetch("/api/v1/account/2fa/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ code }),
      });
      if (res.ok) {
        router.refresh();
        return { ok: true };
      }
      const data = (await res.json().catch(() => ({}))) as {
        message_ko?: string;
        retry_after_seconds?: number;
      };
      return {
        ok: false,
        error_ko: data.message_ko ?? "인증 실패",
        retry_after_seconds: data.retry_after_seconds,
      } as { ok: boolean; retry_after_seconds?: number; error_ko?: string };
    } catch {
      return { ok: false, error_ko: "네트워크 오류" };
    } finally {
      setVerifying(false);
    }
  };

  const handleDisable = async (
    code: string,
    reason: string,
  ): Promise<{ ok: boolean; error_ko?: string }> => {
    if (!accessToken) return { ok: false, error_ko: "인증 토큰 없음" };
    try {
      const res = await fetch("/api/v1/account/2fa/disable", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ code, reason }),
      });
      if (res.ok || res.status === 204) {
        router.refresh();
        return { ok: true };
      }
      const data = (await res.json().catch(() => ({}))) as {
        message_ko?: string;
      };
      return { ok: false, error_ko: data.message_ko ?? "비활성화 실패" };
    } catch {
      return { ok: false, error_ko: "네트워크 오류" };
    }
  };

  return (
    <div
      data-testid="account-security-panel"
      className="mx-auto max-w-2xl space-y-6"
    >
      <header className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900">{t("page_title")}</h1>
        <p className="text-sm text-slate-600">{t("page_subtitle")}</p>
        <TwoFactorStatusBadge
          status={status}
          last_login_at={props.totp_enabled_at}
          lockout_until={props.lockout_until}
          recovery_codes_remaining={props.recovery_codes_remaining}
        />
      </header>

      {status === "disabled" ? (
        <section data-testid="account-security-setup-section">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            {t("setup_section_title")}
          </h2>
          {loading ? (
            <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
              준비 중...
            </div>
          ) : setupData ? (
            <TwoFactorSetupForm
              secret={setupData.secret}
              uri={setupData.uri}
              recovery_codes={setupData.recovery_codes}
              onVerify={handleVerify}
              onComplete={() => {
                router.refresh();
                router.push("/m2-input");
              }}
            />
          ) : (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-800">
              2FA 설정을 시작할 수 없습니다. 잠시 후 다시 시도해 주세요.
            </div>
          )}
        </section>
      ) : null}

      {status === "enabled" ? (
        <>
          <section data-testid="account-security-recovery-section">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">
              {t("recovery_codes_section_title")}
            </h2>
            <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600">
              {t("recovery_codes_section_title")}.
              {props.recovery_codes_remaining != null ? (
                <span className="ml-2 font-medium text-slate-900">
                  {props.recovery_codes_remaining}개 남음
                </span>
              ) : null}
            </div>
          </section>

          {isOwner ? (
            <section data-testid="account-security-disable-section">
              <h2 className="mb-3 text-sm font-semibold text-slate-700">
                {t("disable_section_title")}
              </h2>
              <TwoFactorDisableForm is_owner={isOwner} onDisable={handleDisable} />
            </section>
          ) : (
            <div
              data-testid="account-security-owner-only-notice"
              className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600"
            >
              {t("owner_only_notice")}
            </div>
          )}
        </>
      ) : null}

      {status === "locked" ? (
        <div
          data-testid="account-security-locked-notice"
          className="rounded-lg border border-yellow-300 bg-yellow-50 p-6 text-sm text-yellow-800"
        >
          5회 연속 실패로 {props.lockout_until ?? "잠시"} 까지 잠금 상태입니다.
        </div>
      ) : null}
      {/* suppress unused import warning */}
      {verifying ? null : null}
      {void(formatSecretWithGroups("").length)}
    </div>
  );
}
