"use client";

/**
 * apps/web/components/m7-simulation/ProjectionPdfButton.tsx — Story 7.2
 *
 * PDF download trigger for the "원가 예측 보고서" envelope (Epic 6 §9 #20+).
 * 4 states: idle / loading / success / error.
 *
 * Per AC #4: button label is "원가 예측 보고서 PDF 다운로드" with a
 * loading spinner when generating.
 */

import { useState } from "react";
import { useTranslations } from "next-intl";

import { ERROR_CODE_PROJECTION_BASELINE_NOT_FOUND } from "@/lib/m7-simulation-projection";
import type { ProjectionInputsSerialized } from "@/lib/m7-simulation-projection";

interface ProjectionPdfButtonProps {
  periodKey: string;
  projectionMonth: string;
  inputs: ProjectionInputsSerialized;
  accessToken: string | undefined;
}

type PdfState = "idle" | "loading" | "success" | "error";

export function ProjectionPdfButton({
  periodKey,
  projectionMonth,
  inputs,
  accessToken,
}: ProjectionPdfButtonProps): React.ReactElement {
  const t = useTranslations("projection_simulation");
  const [state, setState] = useState<PdfState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDownload = async (): Promise<void> => {
    setState("loading");
    setErrorMessage(null);
    try {
      const res = await fetch(
        "/api/v1/simulation/projection/report/pdf",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          body: JSON.stringify({
            period_key: periodKey,
            projection_month: projectionMonth,
            projection_inputs: inputs,
            format: "A4",
          }),
          cache: "no-store",
        },
      );
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as {
          code?: string;
          message_ko?: string;
        };
        if (body.code === ERROR_CODE_PROJECTION_BASELINE_NOT_FOUND) {
          setErrorMessage(t("pdf_button_error_baseline_not_found"));
        } else {
          setErrorMessage(body.message_ko ?? `HTTP ${res.status}`);
        }
        setState("error");
        return;
      }
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `cost-prediction-report-${periodKey}-${projectionMonth}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
      setState("success");
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  };

  const buttonText =
    state === "loading"
      ? t("pdf_button_loading")
      : state === "success"
        ? t("pdf_button_success")
        : t("pdf_button_label");

  const colorClass =
    state === "error"
      ? "bg-red-600 hover:bg-red-700"
      : state === "success"
        ? "bg-green-600 hover:bg-green-700"
        : "bg-indigo-600 hover:bg-indigo-700";

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => void handleDownload()}
        disabled={state === "loading"}
        data-testid="projection-pdf-button"
        className={`rounded px-4 py-2 text-white ${colorClass} ${
          state === "loading" ? "cursor-not-allowed opacity-70" : ""
        }`}
      >
        {state === "loading" ? (
          <span className="inline-flex items-center gap-2">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            {buttonText}
          </span>
        ) : (
          buttonText
        )}
      </button>
      {state === "error" && errorMessage ? (
        <p
          className="text-sm text-red-600"
          role="alert"
          data-testid="projection-pdf-error"
        >
          {t("pdf_button_error")}: {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
