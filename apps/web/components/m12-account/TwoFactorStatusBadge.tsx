/**
 * apps/web/components/m12-account/TwoFactorStatusBadge.tsx — Story 12.5
 *
 * M12 2FA status badge (AC #3). Tiny read-only badge with 3 visual states:
 *  - enabled    → green "2FA 활성" + 마지막 로그인 timestamp
 *  - disabled   → red   "2FA 미설정" + [설정하기] link
 *  - locked     → yellow "잠김 — {retry_after}" + Retry-After countdown
 *
 * Server-side fetch via RSC `getTotpStatus()` (12-4 T3.1 service method).
 * The badge itself does NOT re-fetch on the client — purely a presentational
 * component fed by parent (typically /account/security page.tsx).
 *
 * Korean SSOT: apps/web/messages/ko-KR.json::two_factor_status_badge.
 */

import Link from "next/link";
import { useTranslations } from "next-intl";
import * as React from "react";

export type TotpStatus = "enabled" | "disabled" | "locked";

export interface TwoFactorStatusBadgeProps {
  /** TOTP enrollment state. */
  status: TotpStatus;
  /** Last successful login timestamp (ISO-8601), null when disabled. */
  last_login_at?: string | null;
  /** Lockout expiry (ISO-8601), only when status='locked'. */
  lockout_until?: string | null;
  /** Recovery codes remaining count, only when status='enabled'. */
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  recovery_codes_remaining?: number | null;
  /** Locale prefix for the link href (e.g. 'ko' or 'en'). */
  locale?: string;
  /** Optional className override. */
  className?: string;
}

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

/**
 * TwoFactorStatusBadge — header-level read-only status indicator.
 *
 * Always renders as a single pill with state-specific color + label.
 * The "disabled" state includes a CTA link to /account/security/setup.
 */
export function TwoFactorStatusBadge({
  status,
  // eslint-disable-next-line camelcase
  last_login_at,
  // eslint-disable-next-line camelcase
  lockout_until,
  // eslint-disable-next-line camelcase
  recovery_codes_remaining,
  locale,
  className,
}: TwoFactorStatusBadgeProps): React.ReactElement {
  const t = useTranslations("two_factor_status_badge");
  const prefix = locale ? `/${locale}` : "";

  if (status === "enabled") {
    return (
      <div
        data-testid="two-factor-status-badge"
        data-status="enabled"
        className={
          "inline-flex items-center gap-2 rounded-full border border-green-300 bg-green-50 px-3 py-1.5 text-sm " +
          (className ?? "")
        }
      >
        <span className="h-2 w-2 rounded-full bg-green-600" aria-hidden="true" />
        <span className="font-medium text-green-800">
          {t("label_enabled")}
        </span>
        // eslint-disable-next-line camelcase
        {last_login_at ? (
          <span className="text-xs text-green-700">
            · 최근: {formatDateTime(last_login_at)}
          </span>
        ) : null}
        // eslint-disable-next-line camelcase
        {recovery_codes_remaining != null ? (
          <span className="text-xs text-green-700">
            · {t("recovery_codes_remaining_label").replace(
              "{N}",
              String(recovery_codes_remaining),
            )}
          </span>
        ) : null}
      </div>
    );
  }

  if (status === "locked") {
    return (
      <div
        data-testid="two-factor-status-badge"
        data-status="locked"
        className={
          "inline-flex items-center gap-2 rounded-full border border-yellow-300 bg-yellow-50 px-3 py-1.5 text-sm " +
          (className ?? "")
        }
      >
        <span className="h-2 w-2 rounded-full bg-yellow-600" aria-hidden="true" />
        <span className="font-medium text-yellow-800">{t("label_locked")}</span>
        // eslint-disable-next-line camelcase
        {lockout_until ? (
          <span className="text-xs text-yellow-700">
            · {formatDateTime(lockout_until)} 까지
          </span>
        ) : null}
      </div>
    );
  }

  // disabled
  return (
    <div
      data-testid="two-factor-status-badge"
      data-status="disabled"
      className={
        "inline-flex items-center gap-2 rounded-full border border-red-300 bg-red-50 px-3 py-1.5 text-sm " +
        (className ?? "")
      }
    >
      <span className="h-2 w-2 rounded-full bg-red-600" aria-hidden="true" />
      <span className="font-medium text-red-800">{t("label_disabled")}</span>
      <Link
        href={`${prefix}/account/security`}
        className="text-xs font-medium text-red-700 underline hover:text-red-800"
        data-testid="status-badge-setup-link"
      >
        [설정하기]
      </Link>
    </div>
  );
}
