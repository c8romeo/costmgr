"use client";

/**
 * apps/web/components/audit/AuditLogDetailModal.tsx — Epic 17 T2 (AC #2.6)
 *
 * Single audit log entry detail modal.
 *
 * Shows: payload (pretty-printed JSON), actor_id, ip_address,
 * user_agent, trace_id. "copy trace_id" copies to clipboard.
 *
 * Implementation note: a minimal `dialog`-element-based modal is
 * used (no @radix-ui dependency to avoid scope creep — the table
 * row's "view" button opens the modal with `entry != null`).
 */

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import type { AuditLogEntry } from "@/lib/audit/audit-log-client";

interface AuditLogDetailModalProps {
  entry: AuditLogEntry | null;
  onClose: () => void;
}

export function AuditLogDetailModal({
  entry,
  onClose,
}: AuditLogDetailModalProps): React.ReactElement | null {
  const t = useTranslations("audit_log");
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    const dlg = dialogRef.current;
    if (!dlg) return;
    if (entry && !dlg.open) {
      dlg.showModal();
    } else if (!entry && dlg.open) {
      dlg.close();
    }
  }, [entry]);

  if (!entry) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(entry.trace_id);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <dialog
      ref={dialogRef}
      data-testid="audit-log-detail-modal"
      onClose={onClose}
      style={{
        padding: "1.5rem",
        minWidth: "min(640px, 90vw)",
        maxWidth: "90vw",
        borderRadius: 8,
      }}
    >
      <h2 style={{ marginTop: 0 }}>{t("detail_modal_title")}</h2>
      <dl
        style={{
          display: "grid",
          gridTemplateColumns: "160px 1fr",
          rowGap: "0.4rem",
          columnGap: "0.75rem",
        }}
      >
        <dt>{t("column_actor_id")}</dt>
        <dd data-testid="audit-log-detail-actor">{entry.actor_id}</dd>
        <dt>{t("detail_ip_address_label")}</dt>
        <dd>{entry.ip_address ?? "-"}</dd>
        <dt>{t("detail_user_agent_label")}</dt>
        <dd style={{ wordBreak: "break-all" }}>{entry.user_agent ?? "-"}</dd>
        <dt>{t("detail_trace_id_label")}</dt>
        <dd style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <code data-testid="audit-log-detail-trace-id">{entry.trace_id}</code>
          <button
            data-testid="audit-log-detail-copy-trace"
            type="button"
            onClick={handleCopy}
          >
            {copied ? "✓" : t("detail_copy_trace_id")}
          </button>
        </dd>
        <dt>{t("detail_payload_label")}</dt>
        <dd>
          <pre
            data-testid="audit-log-detail-payload"
            style={{
              background: "var(--surface-muted)",
              padding: "0.5rem",
              borderRadius: 4,
              overflow: "auto",
              maxHeight: "40vh",
            }}
          >
            {JSON.stringify(entry.payload, null, 2)}
          </pre>
        </dd>
      </dl>
      <form method="dialog" style={{ textAlign: "right" }}>
        <button data-testid="audit-log-detail-close" type="submit">
          {t("detail_close")}
        </button>
      </form>
    </dialog>
  );
}
