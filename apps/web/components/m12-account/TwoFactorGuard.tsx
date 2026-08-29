/**
 * apps/web/components/m12-account/TwoFactorGuard.tsx — Story 12.4 (A13 sprint-up + Epic 12)
 *
 * M2 ([월 입력]) entry gate UI — AD-15 §11 SSOT parity with
 * `apps/web/lib/m12-two-factor-gate.ts::buildM2EntryGateState`.
 *
 * Mounted in `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx`
 * (CR 11-4 D-001 — must actually mount components, not just declare them).
 *
 * Render decision:
 *  - allowed=true → render children as-is (M2 entry granted)
 *  - allowed=false → render a gate panel with the appropriate message
 *    + action button (2FA setup link or challenge prompt)
 *
 * Capability/role gate: 2FA is industry-agnostic (security baseline,
 * CR 12-1 L4) — there is NO capability matrix gate. Role allowlist
 * (owner/member only) is enforced via the `role` prop.
 *
 * UX-locked (ko-KR labels, WCAG AA contrast, Professional tone).
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import {
  buildM2EntryGateState,
  type M2EntryGateState,
} from "@/lib/m12-two-factor-gate";

export interface TwoFactorGuardProps {
  /** Current user's role (from session context). */
  role: string;
  /** Whether 2FA is enrolled for this user. */
  totp_enabled: boolean;
  /** Whether the user is currently in 5-fail lockout. */
  locked_out: boolean;
  /** Lockout expiry (ISO-8601), null when not locked. */
  lockout_until: string | null;
  /** Children to render when gate is allowed. */
  children: React.ReactNode;
  /** Optional className override for the gate wrapper. */
  className?: string;
}

/**
 * TwoFactorGuard — wraps M2 entry with a 2FA gate panel.
 *
 * Hidden when state.allowed=true (transparent wrapper). When gate is
 * denied, renders a yellow-bordered panel with the appropriate Korean
 * message and an action button linking to /account/security (TODO:
 * account/security page is honestly DEFERred — see deferred-work.md).
 */
export function TwoFactorGuard({
  role,
  // eslint-disable-next-line camelcase
  totp_enabled,
  // eslint-disable-next-line camelcase
  locked_out,
  // eslint-disable-next-line camelcase
  lockout_until,
  children,
  className,
}: TwoFactorGuardProps): React.ReactElement {
  const t = useTranslations("two_factor_guard");
  const tGate = useTranslations("m2_entry_gate");

  const state: M2EntryGateState = buildM2EntryGateState({
    role,
    // eslint-disable-next-line camelcase
    totp_enabled,
    // eslint-disable-next-line camelcase
    locked_out,
    // eslint-disable-next-line camelcase
    lockout_until,
  });

  if (state.allowed) {
    return <>{children}</>;
  }

  // Compose visible message. Prefer ko-KR.json entries; fall back to
  // server-supplied message_ko.
  let visibleMessage = state.message_ko;
  if (state.locked_out) {
    visibleMessage = tGate(
      "blocked_lockout_label",
    // eslint-disable-next-line camelcase
    )?.replace("{until}", lockout_until ?? "") ?? visibleMessage;
  } else if (!state.role_allowed) {
    visibleMessage = tGate("blocked_role_label") ?? visibleMessage;
  } else if (state.requires_two_factor) {
    visibleMessage = tGate("blocked_2fa_required_label") ?? visibleMessage;
  }

  return (
    <section
      role="alert"
      aria-live="polite"
      data-testid="two-factor-guard"
      data-allowed="false"
      data-requires-two-factor={state.requires_two_factor}
      data-locked-out={state.locked_out}
      className={
        "rounded-md border border-amber-300 bg-amber-50 p-6 shadow-sm " +
        (className ?? "")
      }
    >
      <h2 className="mb-2 text-lg font-semibold text-amber-900">
        {t("panel_title")}
      </h2>
      <p className="mb-4 text-sm text-amber-800">{t("panel_description")}</p>
      <div className="mb-4 rounded border border-amber-200 bg-white p-3 text-sm text-slate-700">
        <span className="font-mono">{visibleMessage}</span>
      </div>
      <div className="flex gap-2">
        {state.requires_two_factor && !state.locked_out && (
          <a
            href="/api/v1/account/2fa/challenge"
            data-testid="two-factor-guard-challenge-link"
            className="inline-flex items-center rounded-md bg-amber-700 px-4 py-2 text-sm font-medium text-white hover:bg-amber-800"
          >
            {t("setup_button")}
          </a>
        )}
        {state.locked_out && (
          <span
            className="inline-flex items-center rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-700"
            data-testid="two-factor-guard-lockout-label"
          >
            {t("locked_out_label")}
          </span>
        )}
      </div>
    </section>
  );
}
