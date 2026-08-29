/**
 * apps/web/components/m2-input/MonthlyInputRowForm.tsx — Story 5.3 T9 + P19
 *
 * Monthly input row form for [기초재고] / [수불부] tab. Composes the
 * `M2ClosingGuardGate` so manual edit + the 마감 button are disabled
 * while the closing-guard invariant is violated.
 *
 * Manual edit gate (P22):
 * - <fieldset disabled={is_blocked}> wraps the close button + form fields
 * - Disabled while invariant.code = NEGATIVE_CLOSING
 * - Tab + Enter + programmatic submit all bypass correctly
 */

"use client";

import * as React from "react";

import {
  NEGATIVE_CLOSING_INVENTORY_KO,
} from "@/lib/l2-input-inventory-ledger";
import { cn } from "@/lib/utils";

import { M2ClosingGuardGate } from "./ClosingGuardBanner";

export interface MonthlyInputRowFormProps {
  /** Whether the closing guard is currently blocked. */
  is_blocked: boolean;
  /** Period key (e.g. "2026-07") for the form context. */
  period_key: string;
  /** Optional product id → human-readable name lookup (gate context). */
  productNameLookup?: Record<string, string>;
  /** Form submit handler. Disabled while `is_blocked=true`. */
  onSubmit?: (period_key: string) => Promise<void> | void;
  /** Optional className override. */
  className?: string;
}

/**
 * MonthlyInputRowForm — Wraps the manual-edit form + 마감 button in a
 * <fieldset disabled> gate while the closing invariant is violated.
 *
 * Defense-in-depth: Even if a downstream component bypasses the React
 * `disabled` prop, the HTML `disabled` attribute on the fieldset blocks
 * keyboard navigation + form submission at the DOM level.
 */
export function MonthlyInputRowForm({
  // eslint-disable-next-line camelcase
  is_blocked,
  // eslint-disable-next-line camelcase
  period_key,
  onSubmit,
  className,
}: MonthlyInputRowFormProps): React.ReactElement {
  const handleSubmit = React.useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      // eslint-disable-next-line camelcase
      if (is_blocked) return;
      if (!onSubmit) return;
      await onSubmit(period_key);
    },
    // eslint-disable-next-line camelcase
    [is_blocked, onSubmit, period_key],
  );

  return (
    // eslint-disable-next-line camelcase
    <M2ClosingGuardGate is_blocked={is_blocked}>
      <form
        onSubmit={handleSubmit}
        className={cn("flex flex-col gap-3", className)}
        data-testid="monthly-input-row-form"
        // eslint-disable-next-line camelcase
        data-period-key={period_key}
      >
        <div className="text-sm text-muted-foreground">
          // eslint-disable-next-line camelcase
          {period_key} 수불 입력
        </div>
        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          data-testid="monthly-input-row-submit"
          // eslint-disable-next-line camelcase
          title={is_blocked ? NEGATIVE_CLOSING_INVENTORY_KO : undefined}
        >
          // eslint-disable-next-line camelcase
          {is_blocked ? "마감 불가" : "저장"}
        </button>
      </form>
    </M2ClosingGuardGate>
  );
}