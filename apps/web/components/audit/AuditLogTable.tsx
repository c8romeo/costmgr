"use client";

/**
 * apps/web/components/audit/AuditLogTable.tsx — Epic 17 T2 (AC #2.3)
 *
 * Paginated audit log rows.
 *
 * Columns: created_at | actor_id | action_class | action |
 * resource_type | resource_id | trace_id.
 *
 * trace_id cell is a button that opens the AuditLogDetailModal via
 * the `onSelectEntry` callback. Other cells are presentational.
 */

import { useTranslations } from "next-intl";

import type { AuditLogEntry } from "@/lib/audit/audit-log-client";

interface AuditLogTableProps {
  entries: AuditLogEntry[];
  onSelectEntry: (entry: AuditLogEntry) => void;
}

export function AuditLogTable({
  entries,
  onSelectEntry,
}: AuditLogTableProps): React.ReactElement {
  const t = useTranslations("audit_log");
  return (
    <table
      data-testid="audit-log-table"
      style={{
        width: "100%",
        borderCollapse: "collapse",
        marginTop: "0.5rem",
      }}
    >
      <thead>
        <tr>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_created_at")}
          </th>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_actor_id")}
          </th>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_action_class")}
          </th>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_action")}
          </th>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_resource_type")}
          </th>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_resource_id")}
          </th>
          <th style={{ textAlign: "left", padding: "0.5rem" }}>
            {t("column_trace_id")}
          </th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr
            key={entry.id}
            data-testid="audit-log-table-row"
            style={{ borderTop: "1px solid var(--border)" }}
          >
            <td style={{ padding: "0.5rem" }}>{entry.created_at}</td>
            <td style={{ padding: "0.5rem" }}>{entry.actor_id}</td>
            <td style={{ padding: "0.5rem" }}>{entry.action_class}</td>
            <td style={{ padding: "0.5rem" }}>{entry.action}</td>
            <td style={{ padding: "0.5rem" }}>{entry.resource_type ?? "-"}</td>
            <td style={{ padding: "0.5rem" }}>{entry.resource_id ?? "-"}</td>
            <td style={{ padding: "0.5rem" }}>
              <button
                data-testid="audit-log-trace-id-button"
                type="button"
                onClick={() => onSelectEntry(entry)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent)",
                  cursor: "pointer",
                  padding: 0,
                  textDecoration: "underline",
                }}
              >
                {entry.trace_id.slice(0, 8)}…
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
