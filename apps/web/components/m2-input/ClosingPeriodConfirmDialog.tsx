/**
 * apps/web/components/m2-input/ClosingPeriodConfirmDialog.tsx — Story 6.1 T8.4
 *
 * Closing period confirmation dialog — shadcn `<Dialog>` + sonner toast pattern.
 * Opens a preview of the closing_period snapshot, then on [확정] click POSTs
 * `/api/v1/inventory/closing-period/confirm` and reflects the result via sonner
 * `toast.success` / `toast.error`.
 *
 * AD-15 envelope wire:
 * - 200 OK → sonner `toast.success('월 마감 확정 완료: closing_snapshot {N}건 저장')`
 * - 409 CLOSING_PERIOD_BLOCKED → `toast.error('마감 차단: 음수 기말재고')` + Dialog closes
 * - 409 ALREADY_CLOSED → `toast.error('이미 마감됨')` + Dialog closes
 * - 403 INDUSTRY_NOT_SUPPORTED → `toast.error(...)` + Dialog closes
 *
 * Idempotent re-confirm: monthly_input_periods.status='closed' already → backend
 * 409 ALREADY_CLOSED → no-op (no INSERT, no UPDATE, no audit).
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CLOSING_PERIOD_STATUSES,
  type ClosingPeriodState,
  isClosingPeriodAllowed,
} from "@/lib/closing-period";
import { cn } from "@/lib/utils";

export interface ClosingPeriodConfirmDialogProps {
  /** Controlled open state. */
  open: boolean;
  /** Open state setter. */
  onOpenChange: (open: boolean) => void;
  /** Closing period state to preview + confirm. */
  state: ClosingPeriodState;
  /** Period key (e.g. "2026-07"). */
  period_key: string;
  /** Click handler that triggers the POST. Returns the confirmed snapshot count. */
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  onConfirm?: (period_key: string) => Promise<number>;
  /** Optional className override. */
  className?: string;
}

/**
 * ClosingPeriodConfirmDialog — confirmation flow with snapshot preview.
 *
 * Renders preview of closing_per_product (top 5 products), then on [확정]
 * triggers POST and reflects outcome via sonner toast + Dialog close.
 */
export function ClosingPeriodConfirmDialog({
  open,
  onOpenChange,
  state,
  period_key,
  onConfirm,
  className,
}: ClosingPeriodConfirmDialogProps): React.ReactElement {
  const t = useTranslations("closing_period");
  const [submitting, setSubmitting] = React.useState(false);

  // Defensive default — block submit for unknown status codes.
  const statusKnown = CLOSING_PERIOD_STATUSES.includes(state.status);
  const preview = Object.entries(state.closing_per_product)
    .slice(0, 5)
    .map(([product_id, qty]) => ({ product_id, qty }));

  const handleConfirm = async () => {
    if (submitting || !statusKnown) return;
    // CR 6-1 R4 patch D17: gate [확정] click on CLOSING_READY status only.
    // Defense-in-depth — the panel disables the trigger button, but the
    // dialog could be opened via deep-link / programmatic state. Without
    // this gate, the user can fire POST with non-READY status (e.g.,
    // CLOSING_BLOCKED, EMPTY_PERIOD, ALREADY_CLOSED) and receive 409.
    if (!isClosingPeriodAllowed(state.status)) {
      onOpenChange(false);
      return;
    }
    setSubmitting(true);
    try {
      const count = await onConfirm?.(period_key);
      const safeCount = typeof count === "number" ? count : 0;
      toast.success(t("toast_success").replace("{N}", String(safeCount)));
      onOpenChange(false);
    } catch (err) {
      // Best-effort typed-envelope decode. AD-15 §4 envelope contract:
      // { error: { code, message_ko, ... } }
      const e = err as { response?: { data?: { error?: { code?: string } } } };
      const code = e?.response?.data?.error?.code;
      if (code === "CLOSING_PERIOD_BLOCKED") {
        toast.error(t("toast_error_blocked"));
      } else if (code === "ALREADY_CLOSED") {
        toast.error(t("toast_error_already_closed"));
      } else if (code === "INDUSTRY_NOT_SUPPORTED") {
        toast.error(t("toast_error_industry_not_supported"));
      } else {
        toast.error(t("toast_error_generic"));
      }
      onOpenChange(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn("sm:max-w-md", className)}
        data-testid="closing-period-confirm-dialog"
        data-period-key={period_key}
        data-status={state.status}
      >
        <DialogHeader>
          <DialogTitle>{t("dialog_title")}</DialogTitle>
          <DialogDescription>{t("dialog_description")}</DialogDescription>
        </DialogHeader>
        <div
          className="text-sm text-muted-foreground"
          data-testid="closing-period-snapshot-preview"
        >
          <div className="mb-2">
            period_key: <span className="font-mono">{period_key}</span>
          </div>
          <div className="mb-2">
            status: <span className="font-mono">{state.status}</span>
          </div>
          <div className="mb-2">
            ledger_event_count:{" "}
            <span className="font-mono">{state.ledger_event_count}</span>
          </div>
          {preview.length > 0 ? (
            <ul className="list-disc pl-5">
              {preview.map((p) => (
                <li key={p.product_id}>
                  {p.product_id.slice(0, 8)}: {p.qty}
                </li>
              ))}
            </ul>
          ) : (
            <div>closing_per_product 없음</div>
          )}
        </div>
        <DialogFooter>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
            data-testid="closing-period-dialog-cancel"
            className="px-4 py-2 rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={submitting || !statusKnown || !isClosingPeriodAllowed(state.status)}
            data-testid="closing-period-dialog-confirm"
            className="px-4 py-2 rounded-md bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {t("dialog_confirm")}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
