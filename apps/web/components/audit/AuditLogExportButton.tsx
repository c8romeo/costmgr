"use client";

/**
 * apps/web/components/audit/AuditLogExportButton.tsx — Epic 17 T2 (AC #2.5)
 *
 * "Export CSV" button for the audit log viewer.
 *
 * Owner/admin only — the backend enforces the role check via the
 * route dep (`Depends(require_role("owner", "admin"))` +
 * `Depends(require_capability(Capability.AUDIT_LOG_VIEW))`). The
 * frontend surfaces a typed envelope on 403.
 *
 * Audit-first INSERT `audit_log_exported` happens server-side before
 * the CSV byte stream flush (CR 1-1 verbatim, Epic 17 T5).
 */

import { useState } from "react";
import { useTranslations } from "next-intl";

import {
  exportAuditLogCsv,
  type AuditLogQueryFilters,
} from "@/lib/audit/audit-log-client";

interface AuditLogExportButtonProps {
  accessToken: string;
  filters: AuditLogQueryFilters;
}

export function AuditLogExportButton({
  accessToken,
  filters,
}: AuditLogExportButtonProps): React.ReactElement {
  const t = useTranslations("audit_log");
  const [busy, setBusy] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleClick = async () => {
    setBusy(true);
    setErrorMessage(null);
    const result = await exportAuditLogCsv(accessToken, filters);
    if (result.ok && result.blob && result.filename) {
      const url = URL.createObjectURL(result.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } else if (result.error) {
      if (result.error.status === 403) {
        setErrorMessage(t("error_export_forbidden"));
      } else if (result.error.status === 413) {
        setErrorMessage(t("error_export_too_large"));
      } else {
        setErrorMessage(result.error.message_ko || t("error_network"));
      }
    } else {
      setErrorMessage(t("error_network"));
    }
    setBusy(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
      <button
        data-testid="audit-log-export-button"
        type="button"
        onClick={handleClick}
        disabled={busy}
      >
        {t("export_button_label")}
      </button>
      {errorMessage ? (
        <span
          data-testid="audit-log-export-error"
          style={{ color: "var(--destructive)", fontSize: "0.85rem" }}
        >
          {errorMessage}
        </span>
      ) : null}
    </div>
  );
}
