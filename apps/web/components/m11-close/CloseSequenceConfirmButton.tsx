/**
 * apps/web/components/m11-close/CloseSequenceConfirmButton.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 close sequence [마감 확정] button (11-2 carry-over).
 *
 * Final [마감 확정] button — fires `onConfirm` when clicked.
 * Disabled until all 4 stages have valid chronological timestamps.
 * Triggers AD-6 INSERT refusal activation on success.
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

export interface CloseSequenceConfirmButtonProps {
  /** Disabled state — true when 4 stages not all complete OR not in chronological order. */
  disabled: boolean;
  /** Click handler. */
  onClick?: () => Promise<void>;
  /** Optional className override. */
  className?: string;
}

/**
 * CloseSequenceConfirmButton — final close sequence confirm.
 */
export function CloseSequenceConfirmButton({
  disabled,
  onClick,
  className,
}: CloseSequenceConfirmButtonProps): React.ReactElement {
  const t = useTranslations("close_sequence_panel");
  const [submitting, setSubmitting] = React.useState(false);

  const handleClick = async () => {
    if (submitting || disabled || !onClick) return;
    setSubmitting(true);
    try {
      await onClick();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={submitting || disabled}
      data-testid="close-sequence-confirm-button"
      className={
        "rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50 " +
        (className ?? "")
      }
    >
      {t("confirm_button")}
    </button>
  );
}