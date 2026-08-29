/**
 * apps/web/components/m4-inventory/ReversalRequestDialog.tsx — Story 11.1 T10.4
 *
 * Reversal request dialog — shadcn `<Dialog>` + sonner toast pattern.
 * Opens a form for the user to fill in `reason` (required) + `corrected_qty` +
 * `corrected_period_key` (both optional), then on [역분개 실행] click triggers
 * `ReversalService.execute_reversal` (POST /api/v1/close/reversal-requests).
 *
 * PRD §F11.3 — 마감 후 입력 수정은 역분개로만 가능합니다.
 *
 * AD-15 envelope wire (handlers.py):
 * - 201 REVERSAL_COMPLETED → sonner `toast.success('역분개 완료 — correction_group_id: ...')` + Dialog close + MonthlyInputStateResponse revalidate
 * - 422 LOCKED_PERIOD_REVERSAL_REJECTED → `toast.error('잠긴 기간 — 역분개 불가')` + Dialog stays open
 * - 422 REVERSAL_DUPLICATE → `toast.error('이미 처리된 역분개 요청입니다')` + Dialog stays open
 * - 403 INDUSTRY_NOT_SUPPORTED → `toast.error('업종 미지원: ...')` + Dialog close
 * - 404 REVERSAL_TARGET_NOT_FOUND → `toast.error('대상 event를 찾을 수 없습니다')` + Dialog stays open
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
  M11_AUTHORIZE_KO,
  REVERSAL_ERROR_CODE_DUPLICATE,
  REVERSAL_ERROR_CODE_INDUSTRY_NOT_SUPPORTED,
  REVERSAL_ERROR_CODE_LOCKED,
  REVERSAL_ERROR_CODE_TARGET_NOT_FOUND,
  buildReversalRequestState,
  isReversalRequestAllowed,
  type ReversalCreateResponse,
  type ReversalRequestPayload,
  type ReversalRequestState,
} from "@/lib/m11-reversal";
import { cn } from "@/lib/utils";

import { ReversalRequestForm } from "./ReversalRequestForm";

export interface ReversalRequestDialogProps {
  /** Controlled open state. */
  open: boolean;
  /** Open state setter. */
  onOpenChange: (open: boolean) => void;
  /** Target event_id for the reversal (AD-22 sign-negating target). */
  target_event_id: string;
  /** Period key (AD-24 typed "YYYY-MM"). */
  period_key: string;
  /** monthly_input_periods.status (open | closed | locked). */
  period_status: "open" | "closed" | "locked";
  /** Capability.REVERSAL_REQUEST capability_granted mirror. */
  capability_granted: boolean;
  /** Click handler that triggers the POST. Returns ReversalCreateResponse. */
  onSubmit?: (payload: ReversalRequestPayload) => Promise<ReversalCreateResponse>;
  /** Optional className override. */
  className?: string;
}

/**
 * ReversalRequestDialog — confirmation flow with optional corrected row inputs.
 *
 * Renders shadcn Dialog + ReversalRequestForm. On [역분개 실행] calls
 * onSubmit and reflects outcome via sonner toast.
 */
export function ReversalRequestDialog({
  open,
  onOpenChange,
  target_event_id,
  period_key,
  period_status,
  capability_granted,
  onSubmit,
  className,
}: ReversalRequestDialogProps): React.ReactElement {
  const t = useTranslations("reversal_request");
  const [submitting, setSubmitting] = React.useState(false);

  // Defense-in-depth: compute authorization state.
  const state: ReversalRequestState = buildReversalRequestState({
    target_event_id,
    period_status,
    capability_granted,
  });

  const handleSubmit = async (payload: ReversalRequestPayload) => {
    if (submitting) return;
    if (!isReversalRequestAllowed(state)) {
      // Should never happen — the Form disables [역분개 실행] when not allowed.
      toast.error(state.reject_reason_ko ?? t("error_generic"));
      return;
    }
    setSubmitting(true);
    try {
      const response = await onSubmit?.(payload);
      if (response) {
        toast.success(
          t("toast_success").replace(
            "{correction_group_id}",
            response.correction_group_id,
          ),
        );
        onOpenChange(false);
      }
    } catch (err) {
      // Best-effort typed-envelope decode. AD-15 §4 envelope contract:
      // { error: { code, message_ko, ... } }
      const e = err as {
        response?: { data?: { error?: { code?: string } } };
      };
      const code = e?.response?.data?.error?.code;
      if (code === REVERSAL_ERROR_CODE_LOCKED) {
        toast.error(t("toast_error_locked"));
      } else if (code === REVERSAL_ERROR_CODE_DUPLICATE) {
        toast.error(t("toast_error_duplicate"));
      } else if (code === REVERSAL_ERROR_CODE_TARGET_NOT_FOUND) {
        toast.error(t("toast_error_target_not_found"));
      } else if (code === REVERSAL_ERROR_CODE_INDUSTRY_NOT_SUPPORTED) {
        toast.error(t("toast_error_industry_not_supported"));
        onOpenChange(false);
      } else {
        toast.error(t("toast_error_generic"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn("sm:max-w-md", className)}
        data-testid="reversal-request-dialog"
        data-target-event-id={target_event_id}
        data-period-key={period_key}
        data-period-status={period_status}
      >
        <DialogHeader>
          <DialogTitle>{t("dialog_title")}</DialogTitle>
          <DialogDescription>{t("dialog_description")}</DialogDescription>
        </DialogHeader>
        <div
          className="text-sm text-muted-foreground"
          data-testid="reversal-request-authorization"
        >
          <div className="mb-2">
            {t("authorization_label")}:{" "}
            <span className="font-mono">
              {state.capability_granted ? M11_AUTHORIZE_KO : state.reject_reason_ko}
            </span>
          </div>
          <div className="mb-2">
            {t("period_status_label")}:{" "}
            <span className="font-mono">{state.period_status}</span>
          </div>
        </div>
        <ReversalRequestForm
          target_event_id={target_event_id}
          period_key={period_key}
          submitting={submitting}
          allowed={isReversalRequestAllowed(state)}
          onCancel={() => onOpenChange(false)}
          onSubmit={handleSubmit}
        />
        <DialogFooter>
          <span className="text-xs text-muted-foreground">
            {t("dialog_footer_hint")}
          </span>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
