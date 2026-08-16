"use client";

/**
 * apps/web/components/m8-budget/PreStandardCostTable.tsx — Story 8.3
 *
 * Pre-standard cost table (PRD §F8.3 — 직접재료·직접노무·제조경비).
 *
 * 4-column display: label / amount (KRW integer) / share (%) / note.
 * Total row at bottom (bolded).
 */

import { useTranslations } from "next-intl";

import type { BudgetPreStandardSnapshotSerialized } from "@/lib/m8-budget-pre-standard";

interface PreStandardCostTableProps {
  snapshot: BudgetPreStandardSnapshotSerialized;
}

export function PreStandardCostTable({
  snapshot,
}: PreStandardCostTableProps): React.ReactElement {
  const t = useTranslations("budget_pre_standard");

  const materialCost = BigInt(snapshot.material_cost);
  const laborCost = BigInt(snapshot.labor_cost);
  const overheadCost = BigInt(snapshot.overhead_cost);
  const manufacturingCost = BigInt(snapshot.manufacturing_cost);

  const calcShare = (part: bigint, total: bigint): string => {
    if (total === 0n) return "0.00";
    return ((Number(part) / Number(total)) * 100).toFixed(2);
  };

  return (
    <div className="mt-4" data-testid="pre-standard-cost-table">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-2 py-1 text-left">
              {t("preview_table_label_item")}
            </th>
            <th className="border border-gray-300 px-2 py-1 text-right">
              {t("preview_table_label_amount")}
            </th>
            <th className="border border-gray-300 px-2 py-1 text-right">
              {t("preview_table_label_share")}
            </th>
            <th className="border border-gray-300 px-2 py-1 text-left">
              {t("preview_table_label_note")}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="border border-gray-300 px-2 py-1">
              {t("preview_table_label_material")}
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {materialCost.toLocaleString()}원
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {calcShare(materialCost, manufacturingCost)}%
            </td>
            <td className="border border-gray-300 px-2 py-1 text-xs text-gray-500">
              {t("preview_table_note_material")}
            </td>
          </tr>
          <tr>
            <td className="border border-gray-300 px-2 py-1">
              {t("preview_table_label_labor")}
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {laborCost.toLocaleString()}원
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {calcShare(laborCost, manufacturingCost)}%
            </td>
            <td className="border border-gray-300 px-2 py-1 text-xs text-gray-500">
              {t("preview_table_note_labor")}
            </td>
          </tr>
          <tr>
            <td className="border border-gray-300 px-2 py-1">
              {t("preview_table_label_overhead")}
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {overheadCost.toLocaleString()}원
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {calcShare(overheadCost, manufacturingCost)}%
            </td>
            <td className="border border-gray-300 px-2 py-1 text-xs text-gray-500">
              {t("preview_table_note_overhead")}
            </td>
          </tr>
          <tr className="bg-gray-100 font-bold">
            <td className="border border-gray-300 px-2 py-1">
              {t("preview_table_total_label")}
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">
              {manufacturingCost.toLocaleString()}원
            </td>
            <td className="border border-gray-300 px-2 py-1 text-right">100.00%</td>
            <td className="border border-gray-300 px-2 py-1 text-xs text-gray-500">
              {t("preview_table_note_total")}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
