"use client";

/**
 * apps/web/components/activity/ActivityStreamEntry.tsx — Epic 17 T3 (AC #3.3)
 *
 * Single activity entry row (NOT the bucket — single row, click to
 * deep link to the corresponding audit-log entry detail page).
 *
 * Backend `query_activity_stream` returns grouped aggregates only —
 * per-entry drill-in requires a follow-up call to
 * `/api/v1/audit-log/{entry_id}`. For Epic 17 T3 the deep link goes
 * to `/audit-log?trace_id={trace_id}` (the audit log viewer filters
 * by trace_id), which the panel emits when this component is wired
 * into a drill-down surface.
 *
 * This component is presentational + click-to-deep-link. The parent
 * (typically a future "expand bucket" view) owns the entry data.
 */

import { useTranslations } from "next-intl";

interface ActivityStreamEntryProps {
  entryId: number;
  traceId: string;
  actorId: string;
  action: string;
  resourceType: string | null;
  resourceId: string | null;
  createdAt: string;
}

export function ActivityStreamEntry({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  entryId,
  traceId,
  actorId,
  action,
  resourceType,
  resourceId,
  createdAt,
}: ActivityStreamEntryProps): React.ReactElement {
  const t = useTranslations("activity");
  return (
    <div
      data-testid="activity-stream-entry"
      style={{
        display: "grid",
        gridTemplateColumns: "180px 1fr",
        gap: "0.5rem",
        padding: "0.5rem",
        borderTop: "1px solid var(--border)",
      }}
    >
      <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
        {createdAt}
      </span>
      <a
        href={`/ko-KR/audit-log?trace_id=${encodeURIComponent(traceId)}`}
        data-testid="activity-stream-entry-link"
        style={{ textDecoration: "none", color: "var(--accent)" }}
      >
        <strong>{actorId}</strong> · {action}
        {resourceType ? ` · ${resourceType}` : ""}
        {resourceId ? ` · ${resourceId}` : ""} —{" "}
        <span style={{ textDecoration: "underline" }}>
          {t("entry_view_detail")}
        </span>
      </a>
    </div>
  );
}
