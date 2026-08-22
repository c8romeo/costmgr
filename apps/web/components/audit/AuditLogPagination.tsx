"use client";

/**
 * apps/web/components/audit/AuditLogPagination.tsx — Epic 17 T2 (AC #2.4)
 *
 * Prev/next + page indicator for the audit log viewer.
 *
 * The parent owns the page state and refetch logic; this component
 * is a controlled navigator. URL query param sync is the parent's
 * responsibility (the page.tsx reads `?page=...`).
 */

import { useTranslations } from "next-intl";

interface AuditLogPaginationProps {
  page: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  onPageChange: (nextPage: number) => void;
}

export function AuditLogPagination({
  page,
  pageSize,
  total,
  hasNext,
  onPageChange,
}: AuditLogPaginationProps): React.ReactElement {
  const t = useTranslations("audit_log");
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const canPrev = page > 1;
  return (
    <nav
      data-testid="audit-log-pagination"
      aria-label="pagination"
      style={{
        display: "flex",
        gap: "0.5rem",
        alignItems: "center",
        justifyContent: "flex-end",
        marginTop: "1rem",
      }}
    >
      <span style={{ color: "var(--muted)" }}>
        {t("pagination_page_indicator", {
          total,
          page,
          totalPages,
        })}
      </span>
      <button
        data-testid="audit-log-pagination-prev"
        type="button"
        onClick={() => canPrev && onPageChange(page - 1)}
        disabled={!canPrev}
      >
        {t("pagination_prev")}
      </button>
      <button
        data-testid="audit-log-pagination-next"
        type="button"
        onClick={() => hasNext && onPageChange(page + 1)}
        disabled={!hasNext}
      >
        {t("pagination_next")}
      </button>
    </nav>
  );
}
