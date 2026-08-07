/**
 * apps/web/components/m2-input/ClosingPeriodConfirmationPanel.tsx — Story 6.1 T8.3
 *
 * Closing period confirmation panel — additive on top of M2ClosingGuardBanner (5-3 wire).
 * Renders a status-conditional Alert with a [마감 확정] trigger button. The button is
 * wired through ClosingPeriodConfirmDialog (T8.4) for the actual POST flow.
 *
 * Status 4 codes (AD-15 §11 parity):
 * - CLOSING_READY         → green Alert + button enabled
 * - CLOSING_BLOCKED       → red Alert + button disabled (closes mirror ClosingGuardBanner gate)
 * - ALREADY_CLOSED        → muted Alert + button hidden (AD-6 close lock)
 * - EMPTY_PERIOD          → amber Alert + button disabled
 *
 * Capability gate (A10) — when `capability_granted=false`, panel is hidden entirely
 * (service-only tenant → INDUSTRY_NOT_SUPPORTED).
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { CheckCircle2, Lock, AlertCircle, FileText } from "lucide-react";

import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  CLOSING_PERIOD_STATUSES,
  type ClosingPeriodState,
  isClosingPeriodAllowed,
} from "@/lib/closing-period";
import { cn } from "@/lib/utils";

export interface ClosingPeriodConfirmationPanelProps {
  /** Closing period state (closing_period_status + closing_per_product + counts). */
  state: ClosingPeriodState;
  /**
   * Optional finalized_at (ISO-8601 UTC) for ALREADY_CLOSED display.
   * Mirrors `monthly_input_periods.finalized_at`.
   */
  finalized_at?: string | null;
  /**
   * Capability gate (A10 MONTHLY_CLOSING_REPORT). When false, panel is hidden entirely
   * (service-only tenant → INDUSTRY_NOT_SUPPORTED).
   */
  capability_granted?: boolean;
  /** Click handler — opens ClosingPeriodConfirmDialog. */
  onConfirmClick?: (state: ClosingPeriodState) => void;
  /** Optional className override. */
  className?: string;
}

/**
 * ClosingPeriodConfirmationPanel — additive on top of M2ClosingGuardBanner (5-3 wire).
 *
 * Renders status-conditional Alert + [마감 확정] trigger button. Panel is hidden when
 * `capability_granted=false` (A10) or `state.status` is not one of the 4 SSOT codes
 * (defensive default).
 */
export function ClosingPeriodConfirmationPanel({
  state,
  finalized_at,
  capability_granted = false,
  onConfirmClick,
  className,
}: ClosingPeriodConfirmationPanelProps): React.ReactElement | null {
  const t = useTranslations("closing_period");

  // A10 capability gate — service-only tenant → hidden entirely.
  if (!capability_granted) {
    return null;
  }

  // Defensive default — unknown status codes (drift detector backstop).
  if (!CLOSING_PERIOD_STATUSES.includes(state.status)) {
    return null;
  }

  const allowed = isClosingPeriodAllowed(state.status);
  const is_blocked = state.status === "CLOSING_BLOCKED";
  const is_already_closed = state.status === "ALREADY_CLOSED";
  const is_empty = state.status === "EMPTY_PERIOD";

  // Variant + icon + title per status code (AD-15 §11 SSOT).
  let variant: "default" | "destructive" = "default";
  let icon: React.ReactElement = <CheckCircle2 className="h-4 w-4" aria-hidden="true" />;
  let title = "";
  let description: React.ReactNode = null;
  let buttonDisabled = false;
  let buttonHidden = false;

  if (state.status === "CLOSING_READY") {
    variant = "default";
    icon = <CheckCircle2 className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_ready");
    description = (
      <>
        {state.closing_snapshot_count > 0 ? (
          <span>
            {t("panel_ready_description_with_count").replace(
              "{N}",
              String(state.closing_snapshot_count),
            )}
          </span>
        ) : (
          <span>
            {t("panel_ready_description_default").replace(
              "{N}",
              String(state.ledger_event_count ?? 0),
            )}
          </span>
        )}
      </>
    );
    buttonDisabled = false;
  } else if (state.status === "CLOSING_BLOCKED") {
    variant = "destructive";
    icon = <AlertCircle className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_blocked");
    description = <span>{t("panel_blocked_description")}</span>;
    buttonDisabled = true;
  } else if (state.status === "ALREADY_CLOSED") {
    variant = "default";
    icon = <Lock className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_already_closed");
    description = finalized_at ? (
      <span>
        {t("finalized_at_label")}: {finalized_at}
      </span>
    ) : (
      <span>{t("panel_already_closed_description_locked")}</span>
    );
    buttonDisabled = true;
    buttonHidden = true; // AD-6 — 이미 마감된 경우 button 비노출
  } else if (state.status === "EMPTY_PERIOD") {
    variant = "default";
    icon = <FileText className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_empty_period");
    description = <span>{t("panel_empty_period_description")}</span>;
    buttonDisabled = true;
  }

  return (
    <div
      data-testid="closing-period-confirmation-panel"
      data-status={state.status}
      data-allowed={allowed}
      data-capability-granted={capability_granted}
      className={cn("flex flex-col gap-2", className)}
    >
      <Alert
        variant={variant}
        role={is_blocked ? "alert" : "status"}
        aria-live={is_blocked ? "assertive" : "polite"}
      >
        {icon}
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{description}</AlertDescription>
      </Alert>
      {!buttonHidden && (
        <button
          type="button"
          disabled={buttonDisabled}
          onClick={() => onConfirmClick?.(state)}
          data-testid="closing-period-confirm-button"
          data-status={state.status}
          className={cn(
            "self-start px-4 py-2 rounded-md font-medium transition",
            allowed
              ? "bg-slate-900 text-white hover:bg-slate-700"
              : "bg-white border border-slate-300 text-slate-700",
            buttonDisabled && "opacity-50 cursor-not-allowed",
          )}
        >
          {t("confirm_button")}
        </button>
      )}
    </div>
  );
}
