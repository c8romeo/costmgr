/**
 * apps/web/components/m11-close/ReopenOperatorDialog.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 재오픈 다이얼로그 — W2 reopen flow (operator_action 4-value enum + reason 20-500).
 *
 * Opens a form for owner-only reopen. On submit triggers
 * `ReopenService.authorize_reopen` (POST /api/v1/close/reopen).
 *
 * Capability gate: `Capability.REOPEN_OPERATOR` (owner-only).
 * When `capability_granted=false` OR `is_owner=false`, the dialog is hidden.
 *
 * Korean SSOT: `lib/ko-KR.json::m11_close` + `messages/ko-KR.json::reopen_operator_dialog`.
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
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
  REOPEN_OPERATOR_ACTIONS,
  REOPEN_REJECT_INVALID_OPERATOR_KO,
  REOPEN_REJECT_NO_CAPABILITY_KO,
  REOPEN_REJECT_NOT_OWNER_KO,
  REOPEN_REJECT_REASON_TOO_LONG_KO,
  REOPEN_REJECT_REASON_TOO_SHORT_KO,
  buildReopenAuthorizationState,
  formatReopenResultKo,
  isReasonLengthValid,
  isReopenAllowed,
  type ReopenAuthorizationState,
} from "@/lib/m11-reopen";

export interface ReopenOperatorDialogProps {
  /** Controlled open state. */
  open: boolean;
  /** Open state setter. */
  onOpenChange: (open: boolean) => void;
  /** Tenant id. */
  tenant_id: string;
  /** Actor id. */
  actor_id: string;
  /** Whether actor is owner. */
  is_owner: boolean;
  /** Capability.REOPEN_OPERATOR capability_granted mirror. */
  capability_granted: boolean;
  /** Click handler. Returns ReopenAuthorizationResult. */
  onSubmit?: (payload: {
    tenant_id: string;
    actor_id: string;
    operator_action: string;
    reason: string;
  }) => Promise<{
    fiscal_period_id: string;
    period_key: string;
    status: string;
    reopen_audit_id: string;
    trace_id: string;
  }>;
  /** Optional className override. */
  className?: string;
}

/**
 * ReopenOperatorDialog — W2 reopen authorization confirmation flow.
 *
 * Renders shadcn Dialog + operator_action select + reason input. On
 * [재오픈 실행] calls onSubmit and reflects outcome via sonner toast.
 */
export function ReopenOperatorDialog({
  open,
  onOpenChange,
  tenant_id,
  actor_id,
  is_owner,
  capability_granted,
  onSubmit,
  className,
}: ReopenOperatorDialogProps): React.ReactElement | null {
  const t = useTranslations("reopen_operator_dialog");
  const [submitting, setSubmitting] = React.useState(false);
  const [operator_action, setOperatorAction] = React.useState<string>(
    REOPEN_OPERATOR_ACTIONS[0],
  );
  const [reason, setReason] = React.useState("");

  // Capability gate: owner + capability both required.
  if (!capability_granted || !is_owner) {
    return null;
  }

  // Compute authorization state via TS mirror.
  const state: ReopenAuthorizationState = buildReopenAuthorizationState({
    tenant_id,
    actor_id,
    operator_action,
    reason,
    capability_granted,
    is_owner,
  });

  const handleSubmit = async () => {
    if (submitting) return;
    if (!isReopenAllowed(state)) {
      const code = state.reject_reason_ko ?? REOPEN_REJECT_INVALID_OPERATOR_KO;
      if (code === REOPEN_REJECT_NOT_OWNER_KO) {
        toast.error(t("reject_not_owner_toast"));
      } else if (code === REOPEN_REJECT_NO_CAPABILITY_KO) {
        // P-007 — explicit REOPEN_REJECT_NO_CAPABILITY_KO case.
        toast.error(t("reject_no_capability_toast"));
      } else if (code === REOPEN_REJECT_REASON_TOO_SHORT_KO) {
        toast.error(t("reject_reason_too_short_toast"));
      } else if (code === REOPEN_REJECT_REASON_TOO_LONG_KO) {
        toast.error(t("reject_reason_too_long_toast"));
      } else {
        toast.error(t("reject_invalid_operator_toast"));
      }
      return;
    }
    setSubmitting(true);
    try {
      const response = await onSubmit?.({
        tenant_id,
        actor_id,
        operator_action,
        reason,
      });
      if (response) {
        // P-002 — backend envelope uses `reopen_audit_id` (audit-first
        // emit receipt per CR 1.1) as the SSOT success signal. The
        // `reopen_audit_id` is non-null on successful authorization.
        if (response.reopen_audit_id) {
          toast.success(t("reopen_success_toast") ?? t("completed_toast"));
        } else {
          toast.error(t("reject_invalid_operator_toast"));
        }
        onOpenChange(false);
      }
    } catch (err) {
      // P-001 — distinguish network errors vs auth errors vs validation.
      // Network error (fetch failed): connection issue.
      // Auth error: 401/403 (owner/capability mismatch).
      // Validation error: 422 (reason length, operator_action enum).
      const msg = err instanceof Error ? err.message : "";
      if (err instanceof TypeError || msg.includes("fetch")) {
        toast.error(t("network_error_toast") ?? "네트워크 오류");
      } else if (msg.includes("401") || msg.includes("403")) {
        toast.error(t("reject_no_capability_toast"));
      } else if (msg.includes("422")) {
        toast.error(t("reject_reason_too_short_toast"));
      } else {
        toast.error(t("commit_failed_toast") ?? "재오픈 실패");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const reasonValid = isReasonLengthValid(reason);
  const allowed = isReopenAllowed(state);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={className ?? "sm:max-w-md"}
        data-testid="reopen-operator-dialog"
        data-operator-action={operator_action}
      >
        <DialogHeader>
          <DialogTitle>{t("dialog_title")}</DialogTitle>
          <DialogDescription>{t("dialog_description")}</DialogDescription>
        </DialogHeader>
        <div className="text-sm text-slate-700">
          <div className="mb-2">
            <span className="font-mono">
              result: {formatReopenResultKo(state)}
            </span>
          </div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            {t("dialog_action_label")}
          </label>
          <select
            className="mb-3 w-full rounded-md border border-slate-300 p-2 text-sm"
            value={operator_action}
            onChange={(e) => setOperatorAction(e.target.value)}
            data-testid="reopen-operator-action-select"
          >
            {REOPEN_OPERATOR_ACTIONS.map((action) => (
              <option key={action} value={action}>
                {action}
              </option>
            ))}
          </select>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            {t("dialog_reason_label")}
          </label>
          <textarea
            className="w-full rounded-md border border-slate-300 p-2 text-sm"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            data-testid="reopen-operator-reason-input"
            rows={3}
          />
        </div>
        <DialogFooter>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !allowed || !reasonValid}
            data-testid="reopen-operator-submit-button"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("dialog_submit")}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}