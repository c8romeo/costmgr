"use client";

/**
 * apps/web/components/m5-reports/UnusedCapacityAccordion.tsx — Story 9.4
 *
 * Unused Capacity breakdown accordion (PRD §A9 + §F9.3 verbatim).
 * D-9-3-DEFER-3 해소 (부서별 breakdown, 9-3에서 honestly DEFER).
 *
 * Collapsible panel — single open at a time. Each panel shows
 * 3-column row (department_id, unused_hours, unused_cost_krw).
 */

import { useTranslations } from "next-intl";
import { useState } from "react";

import type { Report21UnusedCapacityRow } from "@/lib/report21";

interface UnusedCapacityAccordionProps {
  rows: ReadonlyArray<Report21UnusedCapacityRow>;
}

function formatKrw(value: string): string {
  // Decimal-as-string → KRW display (e.g., "6600000" → "6,600,000원")
  return Number(value).toLocaleString("ko-KR");
}

export function UnusedCapacityAccordion({
  rows,
}: UnusedCapacityAccordionProps): React.ReactElement {
  const t = useTranslations("report21");
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  if (rows.length === 0) {
    return <p data-testid="report21-unused-empty">{t("unused_capacity_empty")}</p>;
  }

  const totalUnused = rows.reduce(
    (acc, r) => acc + Number(r.unused_cost_krw),
    0,
  );
  const totalHours = rows.reduce(
    (acc, r) => acc + Number(r.unused_hours),
    0,
  );

  return (
    <div data-testid="report21-unused-accordion">
      {rows.map((row, i) => {
        const isOpen = openIndex === i;
        return (
          <div
            key={`${row.department_id}-${i}`}
            data-testid={`report21-unused-row-${row.department_id}`}
            data-open={isOpen}
          >
            <button
              onClick={() => setOpenIndex(isOpen ? null : i)}
              aria-expanded={isOpen}
              aria-controls={`report21-unused-panel-${i}`}
            >
              {row.department_id}: {formatKrw(row.unused_cost_krw)}
              {t("unused_capacity_krw_unit")}
            </button>
            {isOpen && (
              <div id={`report21-unused-panel-${i}`}>
                <table>
                  <tbody>
                    <tr>
                      <th>{t("unused_capacity_column_department")}</th>
                      <td>{row.department_id}</td>
                    </tr>
                    <tr>
                      <th>{t("unused_capacity_column_hours")}</th>
                      <td>
                        {row.unused_hours}
                        {t("unused_capacity_krw_unit")}
                      </td>
                    </tr>
                    <tr>
                      <th>{t("unused_capacity_column_cost")}</th>
                      <td>
                        {formatKrw(row.unused_cost_krw)}
                        {t("unused_capacity_krw_unit")}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
      <div data-testid="report21-unused-totals">
        <span>
          {t("unused_capacity_total_label")}: {totalHours}h
        </span>
        <span>
          {totalUnused.toLocaleString("ko-KR")}
          {t("unused_capacity_krw_unit")}
        </span>
      </div>
    </div>
  );
}
