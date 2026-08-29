/**
 * apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 close sequence step-complete button (11-2 carry-over).
 *
 * Renders a per-step [단계 완료] button that calls `onStepComplete`
 * with the stage name. Disabled when not the current next_step
 * (chronological-order guard).
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

export interface CloseSequenceStepCompleteButtonProps {
  /** The stage this button represents. */
  stage: "divisions" | "manufacturing" | "abc" | "common";
  /** Disabled state (chronological-order guard). */
  disabled: boolean;
  /** Per-step click handler. */
  onClick?: (
    stage: "divisions" | "manufacturing" | "abc" | "common",
  ) => Promise<void>;
  /** Optional className override. */
  className?: string;
}

/**
 * CloseSequenceStepCompleteButton — [단계 완료] button per stage.
 */
export function CloseSequenceStepCompleteButton({
  stage,
  disabled,
  onClick,
  className,
}: CloseSequenceStepCompleteButtonProps): React.ReactElement {
  const t = useTranslations("close_sequence_panel");
  const [submitting, setSubmitting] = React.useState(false);

  const handleClick = async () => {
    if (submitting || disabled || !onClick) return;
    setSubmitting(true);
    try {
      await onClick(stage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={submitting || disabled}
      data-testid={`close-sequence-step-complete-${stage}`}
      data-stage={stage}
      className={
        "rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50 " +
        (className ?? "")
      }
    >
      {t("step_complete_button")}
    </button>
  );
}