"use client";

/**
 * apps/web/components/activity/ActivityStreamPanel.tsx — Epic 17 T3 (AC #3.1)
 *
 * Orchestrator for /activity (activity stream timeline).
 *
 * Composes:
 *   - ActivityStreamWindowSelector (1d / 7d / 30d / 90d)
 *   - ActivityStreamTimeline (grouped by timestamp bucket)
 *   - ActivityStreamEntry (single bucket row with deep link to audit-log)
 *
 * State management: local React state for the active window. URL
 * query param sync is the parent's responsibility (page.tsx reads
 * `?window_days=...`).
 *
 * CR 11-4 D-001 honored — panel renders unconditionally and shows
 * the empty/error envelope via typed CR 12-5 D-14 envelopes.
 */

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";

import {
  fetchActivityStream,
  type ActivityStreamGroup,
} from "@/lib/audit/audit-log-client";

import { ActivityStreamWindowSelector } from "./ActivityStreamWindowSelector";
import { ActivityStreamTimeline } from "./ActivityStreamTimeline";

interface ActivityStreamPanelProps {
  accessToken: string;
  initialGroups: ActivityStreamGroup[];
  initialWindowDays: 1 | 7 | 30 | 90;
}

export function ActivityStreamPanel({
  accessToken,
  initialGroups,
  initialWindowDays,
}: ActivityStreamPanelProps): React.ReactElement {
  const t = useTranslations("activity");
  const router = useRouter();
  const [windowDays, setWindowDays] =
    useState<1 | 7 | 30 | 90>(initialWindowDays);
  const [groups, setGroups] = useState<ActivityStreamGroup[]>(initialGroups);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    initialGroups.length === 0 ? null : null,
  );

  const handleWindowChange = useCallback(
    async (next: 1 | 7 | 30 | 90) => {
      setWindowDays(next);
      setLoading(true);
      setErrorMessage(null);
      const result = await fetchActivityStream(accessToken, next);
      if (result.ok && result.data) {
        setGroups(result.data);
      } else if (result.error) {
        setErrorMessage(result.error.message_ko || t("error_load_failed"));
        setGroups([]);
      } else {
        setErrorMessage(t("error_load_failed"));
        setGroups([]);
      }
      setLoading(false);
      // URL sync (refresh-friendly — Epic 17 T3 PRD §F21.3 verbatim)
      router.replace(`/ko-KR/activity?window_days=${next}`);
    },
    [accessToken, router, t],
  );

  return (
    <section data-testid="activity-stream-panel">
      <header style={{ marginBottom: "1rem" }}>
        <h1>{t("page_title")}</h1>
        <p style={{ color: "var(--muted)" }}>{t("page_subtitle")}</p>
      </header>

      <ActivityStreamWindowSelector
        value={windowDays}
        onChange={handleWindowChange}
      />

      {loading ? (
        <p data-testid="activity-stream-loading">{t("loading_state")}</p>
      ) : errorMessage ? (
        <p
          data-testid="activity-stream-error"
          style={{ color: "var(--destructive)" }}
        >
          {errorMessage}
        </p>
      ) : groups.length === 0 ? (
        <p data-testid="activity-stream-empty">{t("empty_state")}</p>
      ) : (
        <ActivityStreamTimeline groups={groups} />
      )}
    </section>
  );
}
