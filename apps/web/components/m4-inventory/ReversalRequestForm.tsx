/**
 * apps/web/components/m4-inventory/ReversalRequestForm.tsx — Story 11.1 T10.5
 *
 * Reversal request form — reason (required) + corrected_qty (optional) +
 * corrected_period_key (optional). Plain HTML inputs (Story 0.5 plumbing note:
 * shadcn Form primitive deferred to follow-up sprint; for 11-1 wire we use
 * native HTML inputs with shadcn Dialog footer pattern).
 *
 * PRD §F11.3 — corrected_qty/period_key optional (cj-style default = same period).
 *
 * AD-15 wire:
 * - reason: max 500 chars, min 1 char (Pydantic ReversalCreateRequest).
 * - corrected_qty: Decimal string (NUMERIC(18,4)).
 * - corrected_period_key: AD-24 typed 'YYYY-MM' (^\d{4}-(0[1-9]|1[0-2])$).
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import {
  formatReversalReasonKo,
  type ReversalRequestPayload,
  validateReversalCorrectedConstraints,
} from "@/lib/m11-reversal";

export interface ReversalRequestFormProps {
  /** Target event_id (AD-22 sign-negating target). */
  target_event_id: string;
  /** Period key (AD-24 typed "YYYY-MM"). */
  period_key: string;
  /** Submitting flag (disables [역분개 실행]). */
  submitting: boolean;
  /** Allowed flag (disables [역분개 실행] when not allowed). */
  allowed: boolean;
  /** Cancel handler. */
  onCancel: () => void;
  /** Submit handler. */
  onSubmit: (payload: ReversalRequestPayload) => void;
}

/**
 * ReversalRequestForm — controlled inputs for reason / corrected_qty /
 * corrected_period_key. Submits via onSubmit when [역분개 실행] clicked.
 */
export function ReversalRequestForm({
  target_event_id,
  period_key,
  submitting,
  allowed,
  onCancel,
  onSubmit,
}: ReversalRequestFormProps): React.ReactElement {
  const t = useTranslations("reversal_request");
  const [reason, setReason] = React.useState("");
  const [correctedQty, setCorrectedQty] = React.useState("");
  const [correctedPeriodKey, setCorrectedPeriodKey] = React.useState("");
  const [validationError, setValidationError] = React.useState<string | null>(
    null,
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const reasonKo = formatReversalReasonKo(reason);
    if (reasonKo.length === 0) {
      setValidationError(t("error_reason_required"));
      return;
    }
    if (reasonKo.length > 500) {
      setValidationError(t("error_reason_too_long"));
      return;
    }

    // corrected_qty / corrected_period_key together or neither.
    const qtyProvided = correctedQty.trim().length > 0;
    const periodKeyProvided = correctedPeriodKey.trim().length > 0;
    if (qtyProvided !== periodKeyProvided) {
      setValidationError(t("error_corrected_pair_required"));
      return;
    }
    if (qtyProvided && periodKeyProvided) {
      try {
        validateReversalCorrectedConstraints({
          target_event: {
            event_id: target_event_id,
            tenant_id: "",
            product_id: "",
            period_key,
            event_type: "",
            qty: "",
            trace_id: "",
            reverses_event_id: null,
            correction_group_id: null,
            reversal_of_period_key: null,
            actor_id: "",
            payload: {},
          },
          corrected_period_key: correctedPeriodKey,
          correction_group_id: "",
        });
      } catch (err) {
        const e = err as Error;
        setValidationError(
          t("error_corrected_period_key_format").replace(
            "{message}",
            e.message,
          ),
        );
        return;
      }
    }

    setValidationError(null);
    onSubmit({
      target_event_id,
      reason: reasonKo,
      corrected_qty: qtyProvided ? correctedQty : null,
      corrected_period_key: periodKeyProvided ? correctedPeriodKey : null,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3"
      data-testid="reversal-request-form"
    >
      <div className="flex flex-col space-y-1">
        <label
          htmlFor="reversal-target-event-id"
          className="text-sm font-medium"
        >
          {t("target_event_id_label")}
        </label>
        <input
          id="reversal-target-event-id"
          name="target_event_id"
          type="text"
          value={target_event_id}
          readOnly
          data-testid="reversal-request-target-event-id"
          className="px-3 py-2 rounded-md border border-slate-300 bg-slate-50 text-slate-700 font-mono text-sm"
        />
      </div>
      <div className="flex flex-col space-y-1">
        <label htmlFor="reversal-reason" className="text-sm font-medium">
          {t("reason_label")}
        </label>
        <textarea
          id="reversal-reason"
          name="reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          maxLength={500}
          rows={4}
          placeholder={t("reason_placeholder")}
          data-testid="reversal-request-reason"
          className="px-3 py-2 rounded-md border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
        />
      </div>
      <div className="flex flex-col space-y-1">
        <label
          htmlFor="reversal-corrected-qty"
          className="text-sm font-medium"
        >
          {t("corrected_qty_label")}
        </label>
        <input
          id="reversal-corrected-qty"
          name="corrected_qty"
          type="text"
          value={correctedQty}
          onChange={(e) => setCorrectedQty(e.target.value)}
          placeholder={t("corrected_qty_placeholder")}
          data-testid="reversal-request-corrected-qty"
          className="px-3 py-2 rounded-md border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
        />
      </div>
      <div className="flex flex-col space-y-1">
        <label
          htmlFor="reversal-corrected-period-key"
          className="text-sm font-medium"
        >
          {t("corrected_period_key_label")}
        </label>
        <input
          id="reversal-corrected-period-key"
          name="corrected_period_key"
          type="text"
          value={correctedPeriodKey}
          onChange={(e) => setCorrectedPeriodKey(e.target.value)}
          placeholder={t("corrected_period_key_placeholder")}
          pattern="^\d{4}-(0[1-9]|1[0-2])$"
          data-testid="reversal-request-corrected-period-key"
          className="px-3 py-2 rounded-md border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
        />
      </div>
      {validationError ? (
        <div
          className="text-sm text-red-600"
          data-testid="reversal-request-validation-error"
        >
          {validationError}
        </div>
      ) : null}
      <div className="flex flex-row justify-end space-x-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          data-testid="reversal-request-cancel"
          className="px-4 py-2 rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          {t("cancel_button")}
        </button>
        <button
          type="submit"
          disabled={submitting || !allowed}
          data-testid="reversal-request-submit"
          className="px-4 py-2 rounded-md bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {t("submit_button")}
        </button>
      </div>
    </form>
  );
}
