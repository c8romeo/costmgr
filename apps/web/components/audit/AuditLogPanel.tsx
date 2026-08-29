"use client";

/**
 * apps/web/components/audit/AuditLogPanel.tsx — Epic 17 T2 (AC #2.1)
 *
 * Orchestrator for /audit-log (audit log viewer).
 *
 * Composes:
 *   - AuditLogFilterPanel (7 filter fields + URL query param sync)
 *   - AuditLogTable (paginated rows with click-to-detail)
 *   - AuditLogPagination (prev/next + page indicator)
 *   - AuditLogExportButton (CSV export with filter snapshot)
 *   - AuditLogDetailModal (single entry payload inspector)
 *
 * State management: local React state (useState) for filters, current
 * page, selected entry. Refetches on filter or page change via
 * `fetchAuditLog` (apps/web/lib/audit/audit-log-client.ts).
 *
 * CR 11-4 D-001 (page.tsx mount MUST) is honored — the panel renders
 * unconditionally and shows the empty/error envelope via the typed
 * CR 12-5 D-14 envelope from the client.
 *
 * Owner/admin RBAC enforcement is at the backend route layer
 * (AD-22 verbatim + CR 12-5 D-GATE-01 inversion). The frontend does
 * NOT re-check role here; 403 surfaces via the typed envelope.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import {
  fetchAuditLog,
  type AuditLogEntry,
  type AuditLogPage,
  type AuditLogQueryFilters,
} from "@/lib/audit/audit-log-client";

import { AuditLogDetailModal } from "./AuditLogDetailModal";
import { AuditLogExportButton } from "./AuditLogExportButton";
import { AuditLogFilterPanel } from "./AuditLogFilterPanel";
import { AuditLogPagination } from "./AuditLogPagination";
import { AuditLogTable } from "./AuditLogTable";

interface AuditLogPanelProps {
  accessToken: string;
  initialPage: AuditLogPage | null;
  initialFilters: AuditLogQueryFilters;
  initialPageNumber: number;
  initialPageSize: number;
}

const EMPTY_FILTERS: AuditLogQueryFilters = {
  actor_id: null,
  action: null,
  action_class: null,
  resource_type: null,
  resource_id: null,
  start_date: null,
  end_date: null,
  trace_id: null,
};

export function AuditLogPanel({
  accessToken,
  initialPage,
  initialFilters,
  initialPageNumber,
  initialPageSize,
}: AuditLogPanelProps): React.ReactElement {
  const t = useTranslations("audit_log");
  const [filters, setFilters] = useState<AuditLogQueryFilters>(initialFilters);
  const [pageNumber, setPageNumber] = useState<number>(initialPageNumber);
  const [pageSize] = useState<number>(initialPageSize);
  const [data, setData] = useState<AuditLogPage | null>(initialPage);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(
    initialPage == null ? t("forbidden_notice") : null,
  );
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(
    null,
  );

  const refetch = useCallback(
    async (nextFilters: AuditLogQueryFilters, nextPage: number) => {
      setLoading(true);
      setErrorMessage(null);
      const result = await fetchAuditLog(
        accessToken,
        nextFilters,
        nextPage,
        pageSize,
      );
      if (result.ok && result.data) {
        setData(result.data);
      } else if (result.error) {
        if (result.error.status === 403) {
          setErrorMessage(t("forbidden_notice"));
        } else if (result.error.status === 400) {
          setErrorMessage(t("error_invalid_filter"));
        } else {
          setErrorMessage(result.error.message_ko || t("error_load_failed"));
        }
        setData(null);
      } else {
        setErrorMessage(t("error_load_failed"));
        setData(null);
      }
      setLoading(false);
    },
    [accessToken, pageSize, t],
  );

  const handleApplyFilters = useCallback(
    (nextFilters: AuditLogQueryFilters) => {
      setFilters(nextFilters);
      setPageNumber(1);
      void refetch(nextFilters, 1);
    },
    [refetch],
  );

  const handleResetFilters = useCallback(() => {
    setFilters(EMPTY_FILTERS);
    setPageNumber(1);
    void refetch(EMPTY_FILTERS, 1);
  }, [refetch]);

  const handlePageChange = useCallback(
    (nextPage: number) => {
      setPageNumber(nextPage);
      void refetch(filters, nextPage);
    },
    [filters, refetch],
  );

  return (
    <section data-testid="audit-log-panel">
      <header style={{ marginBottom: "1rem" }}>
        <h1>{t("page_title")}</h1>
        <p style={{ color: "var(--muted)" }}>{t("page_subtitle")}</p>
      </header>

      <AuditLogFilterPanel
        filters={filters}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          margin: "1rem 0 0.5rem",
        }}
      >
        <h2 style={{ fontSize: "1.1rem", fontWeight: 600 }}>
          {t("table_title")}
        </h2>
        <AuditLogExportButton
          accessToken={accessToken}
          filters={filters}
        />
      </div>

      {loading ? (
        <p data-testid="audit-log-loading">{t("loading_state")}</p>
      ) : errorMessage ? (
        <p
          data-testid="audit-log-error"
          style={{ color: "var(--destructive)" }}
        >
          {errorMessage}
        </p>
      ) : data == null || data.entries.length === 0 ? (
        <p data-testid="audit-log-empty">{t("empty_state")}</p>
      ) : (
        <>
          <AuditLogTable
            entries={data.entries}
            onSelectEntry={setSelectedEntry}
          />
          <AuditLogPagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            hasNext={data.has_next}
            onPageChange={handlePageChange}
          />
        </>
      )}

      <AuditLogDetailModal
        entry={selectedEntry}
        onClose={() => setSelectedEntry(null)}
      />
    </section>
  );
}
