"use client";

/**
 * apps/web/components/m9-abc/CcrResultCard.tsx — Story 9.2
 *
 * CCR 계산 결과 카드 — CCR per hour (e.g., "33,000원/시간") + V8 hash badge.
 *
 * Per AC #2 (Story 9.2):
 *  - Shows CCR per hour with Korean thousands separator.
 *  - Shows V8 hash badge (sha256:64-hex).
 *  - Renders Korean SSOT error message when CCR compute fails.
 *
 * Parent: <AbcAllocationPanel>.
 */

import { useTranslations } from "next-intl";

import {
  ABC_CCR_INVALID_CAPACITY_KO,
  type CCRResult,
} from "@/lib/m9-abc-allocation";

interface CcrResultCardProps {
  ccr: CCRResult;
  messageKo: string | null;
}

function formatKRW(value: string): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return value;
  return new Intl.NumberFormat("ko-KR").format(num);
}

export function CcrResultCard({
  ccr,
  messageKo,
}: CcrResultCardProps): React.ReactElement {
  const t = useTranslations("abc_allocation");

  const isFailure = messageKo !== null && messageKo.length > 0;
  const errorMessage =
    messageKo === ABC_CCR_INVALID_CAPACITY_KO
      ? ABC_CCR_INVALID_CAPACITY_KO
      : messageKo;

  return (
    <div
      className={`rounded border p-4 ${
        isFailure ? "border-red-300 bg-red-50" : "border-gray-300 bg-white"
      }`}
      data-testid="ccr-result-card"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium">{t("card_ccr_title")}</h3>
        {isFailure ? (
          <span
            className="rounded bg-red-600 px-2 py-0.5 text-xs text-white"
            data-testid="ccr-result-failure-badge"
          >
            {t("card_ccr_failed")}
          </span>
        ) : (
          <span
            className="rounded bg-green-600 px-2 py-0.5 text-xs text-white"
            data-testid="ccr-result-success-badge"
          >
            {t("card_ccr_valid")}
          </span>
        )}
      </div>

      <p className="mt-2 text-sm text-gray-600">
        {t("card_ccr_department_id")}: {ccr.department_id}
      </p>

      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-500">{t("card_ccr_per_hour_label")}</p>
          <p
            className="text-2xl font-semibold"
            data-testid="ccr-result-per-hour"
          >
            {formatKRW(ccr.ccr_per_hour)}
            <span className="ml-1 text-sm font-normal text-gray-600">
              {t("card_ccr_per_hour_unit")}
            </span>
          </p>
        </div>
        <div>
          <p className="text-gray-500">{t("card_ccr_capacity_label")}</p>
          <p className="font-mono text-base">{ccr.practical_capacity_hours}h</p>
        </div>
      </div>

      <div className="mt-3 border-t pt-3">
        <p className="text-xs text-gray-500">{t("card_ccr_hash_label")}</p>
        <p
          className="mt-1 break-all font-mono text-xs text-gray-700"
          data-testid="ccr-result-hash"
        >
          {ccr.hash}
        </p>
      </div>

      {isFailure ? (
        <div
          className="mt-3 rounded bg-red-100 p-2 text-sm text-red-700"
          data-testid="ccr-result-error-message"
        >
          {errorMessage}
        </div>
      ) : null}
    </div>
  );
}