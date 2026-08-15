"use client";

/**
 * apps/web/components/m12-account/DeletionStatusPanel.tsx — Story 12.3
 *
 * Client Component for the M12 account deletion status panel (owner-only,
 * read-only snapshot).
 *
 * Per AC #5 (Story 12.3):
 *  - Fetches `GET /api/v1/account/deletion/status` on mount (initial
 *    server-side fetch via `(dashboard)/account/settings/page.tsx`).
 *  - Shows the FSM status badge (활성 / 삭제 대기 / 삭제 완료).
 *  - If `pending_deletion`, shows days-remaining-until-hard-delete +
 *    [취소하기] button → POST /api/v1/account/deletion/cancel.
 *  - If `active`, shows [계정 삭제하기] button → opens AccountDeletionModal.
 *  - If `deleted`, shows terminal state (HTTP 410 from API).
 */

import { useCallback, useState } from "react";

import { useTranslations } from "next-intl";

import {
  TenantDeletionStatus,
  daysUntilHardDelete,
  getStatusLabel,
  type DeletionEnvelopeResponse,
  type DeletionStatusResponse,
} from "@/lib/m12-account-deletion";

import { AccountDeletionModal } from "./AccountDeletionModal";

interface DeletionStatusPanelProps {
  initialStatus: DeletionStatusResponse | null;
  accessToken: string | undefined;
}

export function DeletionStatusPanel({
  initialStatus,
  accessToken,
}: DeletionStatusPanelProps): React.ReactElement {
  const t = useTranslations("account_deletion");
  const [status, setStatus] = useState<DeletionStatusResponse | null>(initialStatus);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/account/deletion/status", {
        headers: { Authorization: `Bearer ${accessToken ?? ""}` },
      });
      if (res.status === 410) {
        setStatus(null);
        return;
      }
      if (!res.ok) {
        return;
      }
      const data = (await res.json()) as DeletionStatusResponse;
      setStatus(data);
    } catch {
      // Silent — UI shows last known state.
    }
  }, [accessToken]);

  const handleCancel = useCallback(async () => {
    setError(null);
    setIsCancelling(true);
    try {
      const res = await fetch("/api/v1/account/deletion/cancel", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken ?? ""}`,
        },
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as {
          message_ko?: string;
        };
        setError(body.message_ko ?? t("cancel_failed"));
        return;
      }
      await refreshStatus();
    } catch {
      setError(t("network_error"));
    } finally {
      setIsCancelling(false);
    }
  }, [accessToken, refreshStatus, t]);

  const handleDeletionSuccess = useCallback(
    (_envelope: DeletionEnvelopeResponse) => {
      void refreshStatus();
    },
    [refreshStatus],
  );

  const isPending =
    status?.status === TenantDeletionStatus.PENDING_DELETION;
  const isActive = status?.status === TenantDeletionStatus.ACTIVE;
  const daysLeft = daysUntilHardDelete(status?.deletion_scheduled_for ?? null);

  return (
    <section
      aria-labelledby="deletion-status-title"
      className="rounded-lg border border-border bg-card p-6"
    >
      <h2 id="deletion-status-title" className="text-base font-semibold">
        {t("panel_title")}
      </h2>

      {status === null ? (
        <p className="mt-3 text-sm text-muted-foreground">{t("status_deleted")}</p>
      ) : (
        <>
          <div className="mt-3 flex items-center gap-3">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                isPending
                  ? "bg-warning/10 text-warning"
                  : "bg-success/10 text-success"
              }`}
            >
              {getStatusLabel(status.status)}
            </span>
            {isPending && daysLeft !== null ? (
              <span className="text-sm text-muted-foreground">
                {t("days_remaining", { days: daysLeft })}
              </span>
            ) : null}
          </div>

          {error ? (
            <p className="mt-3 text-sm text-negative" role="alert">
              {error}
            </p>
          ) : null}

          <div className="mt-4 flex gap-2">
            {isActive ? (
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                className="rounded-md bg-negative px-4 py-2 text-sm font-medium text-negative-foreground"
              >
                {t("start_deletion")}
              </button>
            ) : null}
            {isPending ? (
              <button
                type="button"
                onClick={handleCancel}
                disabled={isCancelling}
                className="rounded-md border border-input px-4 py-2 text-sm font-medium"
              >
                {isCancelling ? t("cancelling") : t("cancel_deletion")}
              </button>
            ) : null}
          </div>
        </>
      )}

      <AccountDeletionModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSuccess={handleDeletionSuccess}
        accessToken={accessToken}
      />
    </section>
  );
}
