"use client";

/**
 * apps/web/components/activity/ActivityStreamTimeline.tsx — Epic 17 T3 (AC #3.2)
 *
 * Timeline of activity stream groups, ordered by `timestamp_bucket`
 * (newest first).
 *
 * Each bucket shows:
 *   - timestamp bucket label (e.g. "2026-08-22 14:00" for 1d hourly,
 *     "2026-08-22" for 7d/30d daily, "2026-08-W34" for 90d weekly)
 *   - entry count
 *   - top_actions (chip list)
 *   - top_actors (chip list)
 *
 * Drill-in to per-entry detail is NOT implemented in this component —
 * the deep-link to /audit-log is exposed via `ActivityStreamEntry`
 * for individual entries (PRD §F21.3 verbatim: "click 시 해당
 * audit-log entry 로 이동 결정").
 *
 * The grouped representation is enough at this level — the
 * `entry_count` is the count for the bucket.
 */

import { useTranslations } from "next-intl";

import type { ActivityStreamGroup } from "@/lib/audit/audit-log-client";

interface ActivityStreamTimelineProps {
  groups: ActivityStreamGroup[];
}

function formatBucket(bucket: string): string {
  // Backend emits ISO-8601 strings; surface a compact representation.
  // Examples:
  //   2026-08-22T14:00:00Z → 2026-08-22 14:00
  //   2026-08-22T00:00:00Z → 2026-08-22
  //   2026-08-22W34       → 2026-W34 (90d weekly)
  // We attempt a tolerant parse; if unsure, return the raw string.
  const dateTimeMatch = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/.exec(bucket);
  if (dateTimeMatch) {
    return `${dateTimeMatch[1]} ${dateTimeMatch[2]}:${dateTimeMatch[3]}`;
  }
  const dateMatch = /^(\d{4}-\d{2}-\d{2})$/.exec(bucket);
  if (dateMatch) return dateMatch[1];
  const weekMatch = /^(\d{4}-\d{2})W(\d{2})$/.exec(bucket);
  if (weekMatch) return `${weekMatch[1]} W${weekMatch[2]}`;
  return bucket;
}

export function ActivityStreamTimeline({
  groups,
}: ActivityStreamTimelineProps): React.ReactElement {
  const t = useTranslations("activity");
  return (
    <ol
      data-testid="activity-stream-timeline"
      style={{
        listStyle: "none",
        padding: 0,
        margin: 0,
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      {groups.map((group, idx) => (
        <li
          key={`${group.timestamp_bucket}-${idx}`}
          data-testid="activity-stream-bucket"
          style={{
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "1rem",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              marginBottom: "0.5rem",
            }}
          >
            <strong>{formatBucket(group.timestamp_bucket)}</strong>
            <span data-testid="activity-stream-bucket-count">
              {t("bucket_entry_count", { count: group.entry_count })}
            </span>
          </div>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <div>
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "var(--muted)",
                  marginBottom: "0.25rem",
                }}
              >
                {t("bucket_top_actions_label")}
              </div>
              <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
                {group.top_actions.length === 0 ? (
                  <span style={{ color: "var(--muted)" }}>-</span>
                ) : (
                  group.top_actions.map((action) => (
                    <span
                      key={action}
                      data-testid="activity-stream-top-action"
                      style={{
                        background: "var(--surface-muted)",
                        padding: "0.1rem 0.5rem",
                        borderRadius: 4,
                        fontSize: "0.85rem",
                      }}
                    >
                      {action}
                    </span>
                  ))
                )}
              </div>
            </div>
            <div>
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "var(--muted)",
                  marginBottom: "0.25rem",
                }}
              >
                {t("bucket_top_actors_label")}
              </div>
              <div style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}>
                {group.top_actors.length === 0 ? (
                  <span style={{ color: "var(--muted)" }}>-</span>
                ) : (
                  group.top_actors.map((actor) => (
                    <span
                      key={actor}
                      data-testid="activity-stream-top-actor"
                      style={{
                        background: "var(--surface-muted)",
                        padding: "0.1rem 0.5rem",
                        borderRadius: 4,
                        fontSize: "0.85rem",
                      }}
                    >
                      {actor}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
