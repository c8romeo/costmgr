/**
 * apps/web/components/m11-close/ReversalExecuteDialog.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 스냅샷 역분개 다이얼로그 — AD-22 영구화 (committed → reversed) UI.
 *
 * Opens a form for the user to confirm reversal execute. On submit
 * triggers `ReversalExecuteService.execute_reversal`
 * (POST /api/v1/close/reversal-execute).
 *
 * Capability gate: `Capability.REVERSAL_EXECUTE` (manufacturing 3종 ✅ / service-only ❌).
 * When `capability_granted=false`, the dialog is hidden.
 *
 * Korean SSOT: `lib/ko-KR.json::m11_close` + `messages/ko-KR.json::reversal_execute_dialog`.
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
  REOPEN_REASON_MAX_LENGTH,
  REOPEN_REASON_MIN_LENGTH,
} from "@/lib/m11-reopen";
import {
  REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  REVERSAL_EXECUTE_OK_KO,
  buildReversalExecuteState,
  formatReversalExecuteResultKo,
  isReversalExecuteAllowed,
  type ReversalExecuteState,
} from "@/lib/m11-reversal-execute";

export interface ReversalExecuteDialogProps {
  /** Controlled open state. */
  open: boolean;
  /** Open state setter. */
  onOpenChange: (open: boolean) => void;
  /** Tenant id. */
  tenant_id: string;
  /** Target event_id (AD-22 sign-negating target). */
  target_event_id: string;
  /** Snapshot id. */
  snapshot_id: string;
  /** Current snapshot state. */
  snapshot_state: "draft" | "verified" | "committed" | "reversed";
  /** Target qty (Decimal string). */
  target_qty: string;
  /** Optional corrected qty override (Decimal string). */
  corrected_qty?: string | null;
  /** Correction group id (UUID v4). */
  correction_group_id: string;
  /** Actor id. */
  actor_id: string;
  /** Capability.REVERSAL_EXECUTE capability_granted mirror. */
  capability_granted: boolean;
  /** Click handler. Returns ReversalExecuteResult. */
  onSubmit?: (payload: {
    tenant_id: string;
    target_event_id: string;
    snapshot_id: string;
    correction_group_id: string;
    target_qty: string;
    corrected_qty: string | null;
  }) => Promise<{
    snapshot_id: string;
    period_key: string;
    state: "draft" | "verified" | "committed" | "reversed";
    correction_group_id: string;
    cache_invalidation_receipts?: Array<Record<string, string>>;
    trace_id: string;
  }>;
  /** Optional className override. */
  className?: string;
}

/**
 * ReversalExecuteDialog — AD-22 reversal 영구화 confirmation flow.
 *
 * Renders shadcn Dialog + reason input. On [역분개 실행] calls onSubmit
 * and reflects outcome via sonner toast. Reason length 20-500 (AD-15 §4 envelope).
 */
export function ReversalExecuteDialog({
  open,
  onOpenChange,
  tenant_id,
  target_event_id,
  snapshot_id,
  snapshot_state,
  target_qty,
  corrected_qty,
  correction_group_id,
  actor_id,
  capability_granted,
  onSubmit,
  className,
}: ReversalExecuteDialogProps): React.ReactElement | null {
  const t = useTranslations("reversal_execute_dialog");
  const [submitting, setSubmitting] = React.useState(false);
  const [reason, setReason] = React.useState("");

  // Capability gate.
  if (!capability_granted) {
    return null;
  }

  // Compute authorization state via TS mirror.
  const state: ReversalExecuteState = buildReversalExecuteState({
    tenant_id,
    target_event_id,
    snapshot_id,
    snapshot_state,
    target_qty,
    corrected_qty: corrected_qty ?? null,
    correction_group_id,
    actor_id,
  });

  const handleSubmit = async () => {
    if (submitting) return;
    if (!isReversalExecuteAllowed(state)) {
      toast.error(state.reject_reason_ko ?? REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO);
      return;
    }
    setSubmitting(true);
    try {
      const response = await onSubmit?.({
        tenant_id,
        target_event_id,
        snapshot_id,
        correction_group_id,
        target_qty,
        corrected_qty: corrected_qty ?? null,
      });
      if (response) {
        // P-002 — backend envelope uses `correction_group_id` as the SSOT
        // success signal (links sign-negating + corrected rows). The
        // `cache_invalidation_receipts` map is the AD-25 multi-channel
        // publish receipt. Success path closes the dialog.
        if (response.correction_group_id) {
          toast.success(t("reversal_success_toast") ?? t("completed_toast"));
        } else {
          toast.error(t("invalid_snapshot_toast"));
        }
        onOpenChange(false);
      }
    } catch (err) {
      // P-001 — distinguish network errors vs state errors vs 404.
      // Network error (fetch failed): connection issue.
      // 404: snapshot/target_event not found.
      // State error: backend returned non-OK (snapshot state mismatch).
      const msg = err instanceof Error ? err.message : "";
      if (err instanceof TypeError || msg.includes("fetch")) {
        toast.error(t("network_error_toast") ?? "네트워크 오류");
      } else if (msg.includes("404")) {
        toast.error(t("snapshot_not_found_toast") ?? "스냅샷을 찾을 수 없습니다");
      } else {
        toast.error(t("invalid_snapshot_toast"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={className ?? "sm:max-w-md"}
        data-testid="reversal-execute-dialog"
        data-snapshot-state={snapshot_state}
      >
        <DialogHeader>
          <DialogTitle>{t("dialog_title")}</DialogTitle>
          <DialogDescription>{t("dialog_description")}</DialogDescription>
        </DialogHeader>
        <div className="text-sm text-slate-700">
          <div className="mb-2">
            <span className="font-mono">
              result: {formatReversalExecuteResultKo(state)}
            </span>
          </div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            {t("reversal_form_reason_label")}
          </label>
          <textarea
            className="w-full rounded-md border border-slate-300 p-2 text-sm"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            data-testid="reversal-execute-reason-input"
            rows={3}
          />
        </div>
        <DialogFooter>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={
              submitting ||
              !isReversalExecuteAllowed(state) ||
              reason.length < REOPEN_REASON_MIN_LENGTH ||
              reason.length > REOPEN_REASON_MAX_LENGTH
            }
            data-testid="reversal-execute-submit-button"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("reversal_form_submit")}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}