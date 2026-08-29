"use client";

/**
 * apps/web/components/m12-account/BackupDownloadPanel.tsx — Story 12.2
 *
 * Client Component for the M12 backup management UI (owner-only).
 *
 * Per AC #4 (Story 12.2):
 *  - Lists recent backups (default 7 days, max 30) via
 *    `GET /api/v1/account/backups/recent`.
 *  - Each row has a [다운로드] button → calls `GET /backups/{id}/download`
 *    (browser receives JSON bytes + Content-Disposition attachment).
 *  - [수동 백업 실행] button at the top calls
 *    `POST /api/v1/account/backups/trigger` → new backup appears in list.
 *
 * Inherits the owner-only gate from the server (`require_role("owner")`).
 * The page itself is rendered via `(dashboard)/account/backups/page.tsx`
 * which calls `fetchBackupsRecentServerSide` for the initial list.
 */

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";


import {
  BACKUP_DEFAULT_LIST_DAYS,
  BACKUP_MAX_LIST_DAYS,
  buildBackupFilename,
  formatBytes,
  type BackupListItem,
  type BackupListResponse,
  type BackupTriggerResponse,
} from "@/lib/m12-account-backup";

interface BackupDownloadPanelProps {
  initialList: BackupListResponse | null;
  accessToken: string | undefined;
  initialError: string | null;
}

export function BackupDownloadPanel({
  initialList,
  accessToken,
  initialError,
}: BackupDownloadPanelProps): React.ReactElement {
  const t = useTranslations("account_backup");
  const [list, setList] = useState<BackupListResponse | null>(initialList);
  const [error, setError] = useState<string | null>(initialError);
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  const [days, setDays] = useState<number>(BACKUP_DEFAULT_LIST_DAYS);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);

  // ── Refresh list ──────────────────────────────────────────
  const refreshList = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    async (daysArg: number): Promise<void> => {
      try {
        const res = await fetch(
          `/api/v1/account/backups/recent?days=${daysArg}`,
          {
            method: "GET",
            headers: {
              Authorization: accessToken ? `Bearer ${accessToken}` : "",
              "X-Trace-Id": crypto.randomUUID(),
            },
            cache: "no-store",
          },
        );
        if (!res.ok) {
          const msg = `HTTP ${res.status}`;
          setError(msg);
          return;
        }
        const data: BackupListResponse = await res.json();
        setList(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [accessToken],
  );

  // Auto-refresh when `days` changes (debounced)
  useEffect(() => {
    void refreshList(days);
  }, [days, refreshList]);

  // ── Manual trigger ────────────────────────────────────────
  const handleTrigger = useCallback(async (): Promise<void> => {
    if (isTriggering) return;
    setIsTriggering(true);
    try {
      const res = await fetch("/api/v1/account/backups/trigger", {
        method: "POST",
        headers: {
          Authorization: accessToken ? `Bearer ${accessToken}` : "",
          "X-Trace-Id": crypto.randomUUID(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        setError(`HTTP ${res.status}`);
        return;
      }
      const _trigger: BackupTriggerResponse = await res.json();
      // Refresh list to show the new backup
      await refreshList(days);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsTriggering(false);
    }
  }, [accessToken, days, isTriggering, refreshList]);

  // ── Download handler ──────────────────────────────────────
  const handleDownload = useCallback(
    (item: BackupListItem): void => {
      const url = `/api/v1/account/backups/${item.backup_id}/download`;
      window.location.href = url;
    },
    [],
  );

  return (
    <section className="backup-download-panel">
      <header>
        <h2>{t("panel_title")}</h2>
        <p className="muted">{t("panel_description")}</p>
      </header>

      <div className="controls">
        <label htmlFor="days-select">
          {t("days_label")}
          <select
            id="days-select"
            value={days}
            onChange={(e): void => {
              const v = Number(e.target.value);
              const clamped = Math.max(
                1,
                Math.min(v, BACKUP_MAX_LIST_DAYS),
              );
              setDays(clamped);
            }}
          >
            {[7, 14, 30].map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={(): void => {
            void handleTrigger();
          }}
          disabled={isTriggering}
        >
          {isTriggering ? t("trigger_running") : t("trigger_button")}
        </button>
      </div>

      {error !== null && (
        <div role="alert" className="error">
          {t("error_prefix")} {error}
        </div>
      )}

      {list !== null && list.items.length === 0 && (
        <p className="empty">{t("empty_message")}</p>
      )}

      {list !== null && list.items.length > 0 && (
        <table className="backup-list">
          <thead>
            <tr>
              <th>{t("col_date")}</th>
              <th>{t("col_size")}</th>
              <th>{t("col_rows")}</th>
              <th>{t("col_audit_rows")}</th>
              <th>{t("col_sha256")}</th>
              <th>{t("col_actions")}</th>
            </tr>
          </thead>
          <tbody>
            {list.items.map((item) => (
              <tr key={item.backup_id}>
                <td>{item.backup_date}</td>
                <td>{formatBytes(item.payload_size_bytes)}</td>
                <td>{item.row_count_total.toLocaleString("ko-KR")}</td>
                <td>{item.audit_log_exported_rows.toLocaleString("ko-KR")}</td>
                <td className="mono">
                  {item.payload_sha256.slice(0, 12)}…
                </td>
                <td>
                  <button
                    type="button"
                    onClick={(): void => {
                      handleDownload(item);
                    }}
                  >
                    {t("download_button")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <footer className="muted">
        <small>
          {t("filename_hint", {
            filename: buildBackupFilename("YYYY-MM-DD"),
          })}
        </small>
      </footer>
    </section>
  );
}
