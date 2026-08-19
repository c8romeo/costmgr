/**
 * apps/web/components/m10-ai/AiDraftCard.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Story 10.1 (AI Document Extraction to Input Drafts) frontend mount.
 * Displays a single monthly extraction draft row with field metadata +
 * confidence badge + evidence reference.
 *
 * AD-7 verbatim: this component is DISPLAY ONLY. M10 NEVER writes
 * confirmed_inputs/monthly_input_rows. All confirmation flows go
 * through the backend POST /api/v1/ai/promote endpoint (Sprint 10.4
 * AD-17 verbatim promotion port).
 *
 * AD-11 layer rule: components/m10-ai/ ONLY mounts + display; no
 * business logic in this file (form state, validation logic lives
 * in form packages — here AiExtractModal.tsx owns react-hook-form).
 *
 * AD-15 parity SSOT: MonthlyDraftEntry shape mirrors `apps/api/modules
 * /m10_ai/schemas.py` `MonthlyDraftResponse` Pydantic v2 model.
 */

"use client";

import type { MonthlyDraftEntry } from "@/lib/ai-extract";

import { ConfidenceBadge } from "./ConfidenceBadge";

interface AiDraftCardProps {
  draft: MonthlyDraftEntry;
  locale?: "ko-KR" | "en-US";
  onSelect?: (draft: MonthlyDraftEntry) => void;
  isSelected?: boolean;
}

const FIELD_NAME_LABEL_KO: Readonly<Record<string, string>> = {
  직접재료비: "직접재료비",
  직접노무비: "직접노무비",
  제조간접비: "제조간접비",
  판매관리비: "판매관리비",
  매출: "매출",
  기말재고: "기말재고",
} as const;

export function AiDraftCard({
  draft,
  locale = "ko-KR",
  onSelect,
  isSelected = false,
}: AiDraftCardProps): React.ReactElement {
  const fieldLabel =
    FIELD_NAME_LABEL_KO[draft.field_name] ?? draft.field_name;

  const handleClick = onSelect
    ? (): void => {
        onSelect(draft);
      }
    : undefined;

  const cardClass = [
    "rounded-md border p-3 transition-colors",
    isSelected
      ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
      : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-900 dark:hover:border-gray-500",
    onSelect ? "cursor-pointer" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={cardClass}
      data-testid="ai-draft-card"
      data-field-name={draft.field_name}
      data-confidence={draft.confidence}
      data-target-table={draft.target_table}
      onClick={handleClick}
      role={onSelect ? "button" : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onKeyDown={
        onSelect
          ? (e): void => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(draft);
              }
            }
          : undefined
      }
    >
      <div className="flex items-start justify-between gap-2">
        <div className="font-medium text-sm text-gray-900 dark:text-gray-100">
          {fieldLabel}
        </div>
        <ConfidenceBadge
          confidence={Number(draft.confidence)}
          locale={locale}
        />
      </div>

      <div className="mt-2 flex items-baseline gap-1 text-sm text-gray-700 dark:text-gray-300">
        <span className="font-mono text-base">{draft.value}</span>
        <span className="text-xs text-gray-500">KRW</span>
      </div>

      {draft.evidence_page !== null && (
        <div className="mt-1 text-xs text-gray-500">
          출처: p.{draft.evidence_page}
        </div>
      )}

      {draft.requires_user_confirmation && (
        <div
          className="mt-2 rounded-sm bg-yellow-50 px-2 py-1 text-xs text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200"
          data-testid="ai-draft-confirmation-required"
        >
          ⚠ {locale === "ko-KR"
            ? "확인이 필요합니다 (confidence 낮음)"
            : "Confirmation required (low confidence)"}
        </div>
      )}
    </div>
  );
}
