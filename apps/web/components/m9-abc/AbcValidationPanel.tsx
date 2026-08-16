"use client";

/**
 * apps/web/components/m9-abc/AbcValidationPanel.tsx — Story 9.1
 *
 * Main Client Component for the M9 ABC 100% validation UI.
 *
 * Per AC #4 (Story 9.1):
 *  - Mounts 3-input form (cost_pool / activity / driver).
 *  - On submit: POST /api/v1/abc/validate → ValidationResponse.
 *  - Renders AbcValidationGuardBadge + AbcValidationStatus for each layer.
 *  - Capability gate ABC_CALCULATION enforced server-side (CR 12-5 L3).
 *  - 422 COST_POOL_INVALID_SUM + 404 ABC_VALIDATION_NOT_FOUND envelopes
 *    surface as inline errors.
 *
 * Composes <AbcValidationForm> + <AbcValidationGuardBadge> +
 * <AbcValidationStatus>.
 *
 * The page itself is rendered via
 * `(dashboard)/budget/abc-validation/page.tsx`.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import {
  type ValidationResponse,
  isValidationResponse,
} from "@/lib/m9-abc-validation";

import { AbcValidationForm } from "./AbcValidationForm";
import { AbcValidationGuardBadge } from "./AbcValidationGuardBadge";
import { AbcValidationStatus } from "./AbcValidationStatus";

interface AbcValidationPanelProps {
  accessToken: string | undefined;
  initialResponse: ValidationResponse | null;
  initialError: string | null;
}

export function AbcValidationPanel({
  accessToken,
  initialResponse,
  initialError,
}: AbcValidationPanelProps): React.ReactElement {
  const t = useTranslations("abc_validation");

  const [response, setResponse] = useState<ValidationResponse | null>(
    initialResponse,
  );
  const [error, setError] = useState<string | null>(initialError);

  const handleResult = useCallback((res: ValidationResponse): void => {
    if (!isValidationResponse(res)) {
      setError("invalid_response_shape");
      return;
    }
    setResponse(res);
    setError(null);
  }, []);

  return (
    <main className="p-6" data-testid="abc-validation-panel">
      <h1 className="text-2xl font-semibold">{t("page_title")}</h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      {error !== null ? (
        <div
          className="mt-3 rounded bg-red-100 p-3 text-sm text-red-700"
          data-testid="abc-validation-error-banner"
        >
          {error}
        </div>
      ) : null}

      <section className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="rounded border p-4">
          <h2 className="text-lg font-medium">{t("panel_input_title")}</h2>
          <p className="mt-1 text-sm text-gray-600">
            {t("panel_input_description")}
          </p>
          <div className="mt-3">
            <AbcValidationForm
              accessToken={accessToken}
              onResult={handleResult}
            />
          </div>
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-medium">{t("panel_result_title")}</h2>
          {response !== null ? (
            <>
              <AbcValidationGuardBadge response={response} />
              <div className="space-y-2">
                {response.layers.map((layer) => (
                  <AbcValidationStatus key={layer.target} layer={layer} />
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-500">{t("empty_result")}</p>
          )}
        </div>
      </section>
    </main>
  );
}