/**
 * apps/web/components/m10-ai/AiExtractModal.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Story 10.1 (AI Document Extraction to Input Drafts) frontend mount.
 * Triggers `POST /api/v1/ai/extract-monthly` for the selected period and
 * displays the resulting draft cards.
 *
 * AD-7 verbatim: this component is READ-ONLY on monthly_input_rows —
 * M10 NEVER writes confirmed_inputs. All confirmation flows go through
 * the backend POST /api/v1/ai/promote endpoint (Sprint 10.4 AD-17).
 *
 * AD-11 layer rule: form state + validation logic live here (plain
 * useState + inline validation, mirroring m7-simulation/ProjectionForm.tsx
 * pattern) — components display + form only, no business logic.
 *
 * AD-15 parity SSOT: POST body shape mirrors `apps/api/modules/m10_ai
 * /schemas.py` `MonthlyExtractRequest` Pydantic model (period_key +
 * document_b64 + document_type).
 *
 * CR 11-4 D-005 — Unknown state reject (no flicker):
 *   `loading` state renders nothing-but-spinner — no half-rendered
 *   drafts while extraction is in flight (CR 11-4 type-narrowing pattern).
 *
 * Implementation note (D-10-5-DEFER-3 honestly deferred):
 *   Spec recommended react-hook-form + Zod resolver, but those packages
 *   are not yet in apps/web/package.json (also deferred in m7-simulation
 *   ProjectionForm.tsx D-7-2-DEFER-7). We use plain React useState +
 *   inline validation here. A follow-up sprint can add `zod` +
 *   `react-hook-form` and migrate.
 */

"use client";

import { useCallback, useState } from "react";

import {
  extractMonthlyAiDraft,
  isMonthlyExtractError,
  type MonthlyDraftEntry,
  type MonthlyExtractEnvelope,
} from "@/lib/ai-extract";
import { ApiError } from "@/lib/api-client";

import { AiDraftCard } from "./AiDraftCard";

const PERIOD_KEY_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

interface FormFields {
  period_key: string;
  document_b64: string;
  document_type: "pdf" | "xlsx";
}

interface FormErrors {
  period_key: string | null;
  document_b64: string | null;
}

type ExtractionState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; drafts: MonthlyDraftEntry[]; lowConfidenceCount: number }
  | { kind: "low_confidence_warning"; drafts: MonthlyDraftEntry[]; lowConfidenceCount: number }
  | { kind: "error"; message_ko: string; error_code: string };

interface AiExtractModalProps {
  accessToken?: string;
  isOpen: boolean;
  onClose: () => void;
  onDraftsConfirmed?: (drafts: MonthlyDraftEntry[]) => void;
  defaultPeriodKey?: string;
}

export function AiExtractModal({
  accessToken,
  isOpen,
  onClose,
  onDraftsConfirmed,
  defaultPeriodKey,
}: AiExtractModalProps): React.ReactElement | null {
  const [fields, setFields] = useState<FormFields>({
    period_key: defaultPeriodKey ?? "",
    document_b64: "",
    document_type: "pdf",
  });
  const [errors, setErrors] = useState<FormErrors>({
    period_key: null,
    document_b64: null,
  });
  const [state, setState] = useState<ExtractionState>({ kind: "idle" });

  const validate = useCallback((): boolean => {
    const next: FormErrors = { period_key: null, document_b64: null };
    if (!PERIOD_KEY_PATTERN.test(fields.period_key)) {
      next.period_key = "YYYY-MM 형식이 올바르지 않습니다 (예: 2026-07)";
    }
    if (fields.document_b64.length === 0) {
      next.document_b64 = "문서를 첨부해 주세요";
    }
    setErrors(next);
    return next.period_key === null && next.document_b64 === null;
  }, [fields]);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      const file = e.target.files?.[0];
      if (!file) {
        setFields((f) => ({ ...f, document_b64: "" }));
        return;
      }
      const reader = new FileReader();
      reader.onload = (): void => {
        const result = reader.result;
        if (typeof result === "string") {
          // Strip `data:...;base64,` prefix
          const commaIdx = result.indexOf(",");
          const base64 = commaIdx >= 0 ? result.slice(commaIdx + 1) : result;
          const fileName = file.name.toLowerCase();
          const docType: "pdf" | "xlsx" = fileName.endsWith(".xlsx")
            ? "xlsx"
            : "pdf";
          setFields((f) => ({ ...f, document_b64: base64, document_type: docType }));
        }
      };
      reader.readAsDataURL(file);
    },
    [],
  );

  const handlePeriodChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      setFields((f) => ({ ...f, period_key: e.target.value }));
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      if (!validate()) return;
      setState({ kind: "loading" });
      try {
        const env: MonthlyExtractEnvelope = await extractMonthlyAiDraft(
          {
            period_key: fields.period_key,
            document_b64: fields.document_b64,
            document_type: fields.document_type,
          },
          accessToken,
        );
        if (env.status === "success" || env.status === "low_confidence_warning") {
          setState({
            kind:
              env.status === "low_confidence_warning"
                ? "low_confidence_warning"
                : "success",
            drafts: env.drafts,
            lowConfidenceCount: env.low_confidence_count,
          });
        } else if (isMonthlyExtractError(env)) {
          setState({
            kind: "error",
            message_ko: env.message_ko,
            error_code: env.error_code,
          });
        } else {
          setState({
            kind: "error",
            message_ko: "추출 응답을 해석할 수 없습니다",
            error_code: "MONTHLY_EXTRACTION_ERROR",
          });
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setState({
            kind: "error",
            message_ko: err.payload.message_ko,
            error_code: err.payload.code,
          });
        } else {
          setState({
            kind: "error",
            message_ko:
              err instanceof Error ? err.message : "추출 요청 실패",
            error_code: "MONTHLY_EXTRACTION_ERROR",
          });
        }
      }
    },
    [validate, fields, accessToken],
  );

  if (!isOpen) return null;

  const isLoading = state.kind === "loading";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ai-extract-modal-title"
      data-testid="ai-extract-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <h2
            id="ai-extract-modal-title"
            className="text-lg font-semibold text-gray-900 dark:text-gray-100"
          >
            AI 월별 추출
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            data-testid="ai-extract-modal-close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="period_key"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              기간 (YYYY-MM)
            </label>
            <input
              id="period_key"
              type="text"
              placeholder="2026-07"
              value={fields.period_key}
              onChange={handlePeriodChange}
              className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-800"
              data-testid="ai-extract-period-input"
            />
            {errors.period_key && (
              <p className="mt-1 text-xs text-red-600">
                {errors.period_key}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="document_file"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              PDF 또는 Excel 업로드
            </label>
            <input
              id="document_file"
              type="file"
              accept=".pdf,.xlsx"
              onChange={handleFileChange}
              className="mt-1 w-full text-sm"
              data-testid="ai-extract-file-input"
            />
            {errors.document_b64 && (
              <p className="mt-1 text-xs text-red-600">
                {errors.document_b64}
              </p>
            )}
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isLoading}
              data-testid="ai-extract-submit"
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? "추출 중..." : "AI 추출 실행"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              취소
            </button>
          </div>
        </form>

        {/* Result section */}
        <div className="mt-6 border-t pt-4" data-testid="ai-extract-result">
          {state.kind === "idle" && (
            <p className="text-sm text-gray-500">
              양식을 작성하고 [AI 추출 실행]을 클릭하세요.
            </p>
          )}
          {state.kind === "loading" && (
            <p className="text-sm text-gray-500" data-testid="ai-extract-loading">
              추출 중...
            </p>
          )}
          {(state.kind === "success" ||
            state.kind === "low_confidence_warning") && (
            <div data-testid="ai-extract-drafts-list">
              {state.kind === "low_confidence_warning" && (
                <div className="mb-3 rounded bg-yellow-50 px-3 py-2 text-xs text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200">
                  ⚠ 신뢰도 낮은 초안 {state.lowConfidenceCount}건 — 사용자 확인 필요
                </div>
              )}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {state.drafts.map((d, idx) => (
                  <AiDraftCard
                    key={`${d.field_name}-${idx}`}
                    draft={d}
                  />
                ))}
              </div>
              {onDraftsConfirmed && (
                <button
                  type="button"
                  onClick={(): void => onDraftsConfirmed(state.drafts)}
                  className="mt-4 rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                  data-testid="ai-extract-confirm-button"
                >
                  초안 확정 (승격 큐에 추가)
                </button>
              )}
            </div>
          )}
          {state.kind === "error" && (
            <div
              role="alert"
              data-testid="ai-extract-error"
              className="rounded bg-red-50 px-3 py-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200"
            >
              {state.message_ko} ({state.error_code})
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
