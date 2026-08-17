"use client";

/**
 * apps/web/components/m9-abc/AbcDispatchErrorToast.tsx — Story 9.3
 *
 * 422 envelope error surface for M9 ABC dispatch path
 * (PRD §F9.3 + AD-19 + CR 12-5 D-14 envelope handler pattern).
 *
 * Per AC #4 (Story 9.3) — 422 EMPTY_DEPARTMENTS + 422 TOO_MANY_DEPARTMENTS
 * envelopes surface as inline error toast (NOT as page crash).
 *
 * The 422 envelopes are wired by `_m9_abc_empty_departments_error_handler`
 * and `_m9_abc_too_many_departments_error_handler` in `apps/api/main.py`
 * (T3 wire).
 *
 * Composed by AbcDispatchPanel.
 */

import { useTranslations } from "next-intl";

import {
  ABC_EMPTY_DEPARTMENTS_KO,
  ABC_TOO_MANY_DEPARTMENTS_KO,
} from "@/lib/m9-abc-dispatch";

export type AbcDispatchErrorCode =
  | "ABC_EMPTY_DEPARTMENTS"
  | "ABC_TOO_MANY_DEPARTMENTS"
  | "ABC_DISPATCH_GENERIC_ERROR";

interface AbcDispatchErrorToastProps {
  errorCode: AbcDispatchErrorCode | null;
  errorMessage?: string | null;
  onDismiss?: () => void;
}

export function AbcDispatchErrorToast({
  errorCode,
  errorMessage,
  onDismiss,
}: AbcDispatchErrorToastProps): React.ReactElement | null {
  const t = useTranslations("abc_calculation");

  if (errorCode === null) {
    return null;
  }

  // Map 422 envelope code → Korean SSOT label.
  const codeLabel =
    errorCode === "ABC_EMPTY_DEPARTMENTS"
      ? t("error_empty_departments")
      : errorCode === "ABC_TOO_MANY_DEPARTMENTS"
        ? t("error_too_many_departments")
        : t("error_generic");

  const description =
    errorCode === "ABC_EMPTY_DEPARTMENTS"
      ? ABC_EMPTY_DEPARTMENTS_KO
      : errorCode === "ABC_TOO_MANY_DEPARTMENTS"
        ? ABC_TOO_MANY_DEPARTMENTS_KO
        : (errorMessage ?? t("error_generic_description"));

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="mt-3 rounded border border-red-400 bg-red-50 p-3 text-sm text-red-800"
      data-testid="abc-dispatch-error-toast"
      data-error-code={errorCode}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold" data-testid="abc-dispatch-error-code">
            {codeLabel}
          </p>
          <p
            className="mt-1 text-xs text-red-700"
            data-testid="abc-dispatch-error-description"
          >
            {description}
          </p>
        </div>
        {onDismiss !== undefined ? (
          <button
            type="button"
            onClick={onDismiss}
            className="rounded px-2 py-1 text-xs text-red-700 hover:bg-red-100"
            data-testid="abc-dispatch-error-dismiss"
            aria-label={t("error_dismiss_aria")}
          >
            ✕
          </button>
        ) : null}
      </div>
    </div>
  );
}
