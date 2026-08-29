/**
 * apps/web/components/m4-inventory/ReversalRequestButton.tsx — Story 11.1 T10.6
 *
 * Reversal request trigger button. Mounted in `MonthlyInputTabs` (closing period
 * section). Opens `ReversalRequestDialog` on click.
 *
 * Capability gate: `Capability.REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌).
 * When `capability_granted=false`, the button is hidden (service-only tenant UX).
 *
 * PRD §F11.3 — 마감 후 입력 수정은 역분개로만 가능합니다.
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import {
  PERIOD_STATUS_LOCKED,
  type PeriodStatus,
} from "@/lib/m11-reversal";
import { cn } from "@/lib/utils";

import { ReversalRequestDialog } from "./ReversalRequestDialog";

export interface ReversalRequestButtonProps {
  /** Target event_id for the reversal. */
  target_event_id: string;
  /** Period key (AD-24 typed "YYYY-MM"). */
  period_key: string;
  /** monthly_input_periods.status. */
  period_status: PeriodStatus;
  /** Capability.REVERSAL_REQUEST capability_granted mirror. */
  capability_granted: boolean;
  /** Submit handler. */
  onSubmit?: (payload: {
    target_event_id: string;
    reason: string;
    corrected_qty: string | null;
    corrected_period_key: string | null;
  }) => Promise<{
    correction_group_id: string;
  }>;
  /** Optional className override. */
  className?: string;
}

/**
 * ReversalRequestButton — trigger button + Dialog wrapper.
 * Hidden when capability_granted=false (service-only tenant).
 */
export function ReversalRequestButton({
  // eslint-disable-next-line camelcase
  target_event_id,
  // eslint-disable-next-line camelcase
  period_key,
  // eslint-disable-next-line camelcase
  period_status,
  // eslint-disable-next-line camelcase
  capability_granted,
  onSubmit,
  className,
}: ReversalRequestButtonProps): React.ReactElement | null {
  const t = useTranslations("reversal_request");
  const [open, setOpen] = React.useState(false);

  // Capability gate: service-only tenant → button hidden entirely.
  // eslint-disable-next-line camelcase
  if (!capability_granted) {
    return null;
  }

  // Period lock gate: button disabled when period_status='locked'.
  // eslint-disable-next-line camelcase
  const disabled = period_status === PERIOD_STATUS_LOCKED;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={disabled}
        data-testid="reversal-request-button"
        // eslint-disable-next-line camelcase
        data-period-key={period_key}
        // eslint-disable-next-line camelcase
        data-period-status={period_status}
        className={cn(
          "px-4 py-2 rounded-md bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed",
          className,
        )}
      >
        {t("trigger_label")}
      </button>
      <ReversalRequestDialog
        open={open}
        onOpenChange={setOpen}
        // eslint-disable-next-line camelcase
        target_event_id={target_event_id}
        // eslint-disable-next-line camelcase
        period_key={period_key}
        // eslint-disable-next-line camelcase
        period_status={period_status}
        // eslint-disable-next-line camelcase
        capability_granted={capability_granted}
        onSubmit={async (payload) => {
          if (!onSubmit) {
            return {
              correction_group_id: "",
              negating_event_id: "",
              corrected_event_id: null,
              target_event_id: payload.target_event_id,
              reversal_history: [],
              trace_id: "",
              cache_invalidation_receipt: {},
            };
          }
          const partial = await onSubmit(payload);
          return {
            correction_group_id: partial.correction_group_id,
            negating_event_id: "",
            corrected_event_id: null,
            target_event_id: payload.target_event_id,
            reversal_history: [],
            trace_id: "",
            cache_invalidation_receipt: {},
          };
        }}
      />
    </>
  );
}
