"use client";

/**
 * apps/web/components/m9-abc/AbcValidationForm.tsx — Story 9.1
 *
 * 3-input form for ABC 100% guard validation (PRD §F9.1 verbatim).
 *
 * Per AC #4 (Story 9.1):
 *  - 3 textareas (cost_pool / activity / driver) — comma-separated Decimal strings.
 *  - On submit: POST /api/v1/abc/validate → ValidationResponse.
 *  - Single-layer validation buttons (POST /cost-pools + /activities + /drivers/validate).
 *  - 422 COST_POOL_INVALID_SUM + 404 ABC_VALIDATION_NOT_FOUND envelopes
 *    surface as inline errors.
 *  - Validates client-side via `validateAbcPctList` (CR 11-4 D-005).
 *
 * Parent: <AbcValidationPanel>.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { extractAbcValidationErrorMessage, type ValidationResponse } from "@/lib/m9-abc-validation";
import {
  AbcValidationInputError,
  computeSumPct,
  validateAbcPctList,
} from "@/lib/m9-abc-validation-schema";

interface AbcValidationFormProps {
  accessToken: string | undefined;
  onResult: (response: ValidationResponse) => void;
}

export function AbcValidationForm({
  accessToken,
  onResult,
}: AbcValidationFormProps): React.ReactElement {
  const t = useTranslations("abc_validation");

  const [costPoolInput, setCostPoolInput] = useState<string>("25, 25, 25, 25");
  const [activityInput, setActivityInput] = useState<string>("50, 50");
  const [driverInput, setDriverInput] = useState<string>("60, 40");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const parseList = useCallback((raw: string): string[] => {
    return raw
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }, []);

  // ── Submit handler (3-layer guard) ────────────────────────────
  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      setError(null);

      const costPoolList = parseList(costPoolInput);
      const activityList = parseList(activityInput);
      const driverList = parseList(driverInput);

      try {
        validateAbcPctList(costPoolList, "cost_pool");
        validateAbcPctList(activityList, "activity");
        validateAbcPctList(driverList, "driver");
      } catch (e) {
        if (e instanceof AbcValidationInputError) {
          setError(`${e.target}: ${e.reason}`);
          return;
        }
        setError(e instanceof Error ? e.message : String(e));
        return;
      }

      setSubmitting(true);
      try {
        const res = await fetch(`/api/v1/abc/validate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          body: JSON.stringify({
            cost_pool_id: "cp-001",
            activity_id: "act-001",
            cost_pool: costPoolList,
            activities: activityList,
            drivers: driverList,
          }),
          cache: "no-store",
        });

        if (!res.ok) {
          const body = (await res.json().catch(() => null)) as
            | { code?: string; message_ko?: string }
            | null;
          setError(extractAbcValidationErrorMessage(body));
          return;
        }

        const data: ValidationResponse = await res.json();
        onResult(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setSubmitting(false);
      }
    },
    [
      costPoolInput,
      activityInput,
      driverInput,
      parseList,
      accessToken,
      onResult,
    ],
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3"
      data-testid="abc-validation-form"
    >
      <div>
        <label
          htmlFor="cost_pool_input"
          className="block text-sm font-medium"
        >
          {t("form_label_cost_pool")}
        </label>
        <input
          id="cost_pool_input"
          type="text"
          value={costPoolInput}
          onChange={(e) => setCostPoolInput(e.target.value)}
          className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
          placeholder="25, 25, 25, 25"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          {t("form_hint_cost_pool")} (현재 {computeSumPct(parseList(costPoolInput))}%)
        </p>
      </div>
      <div>
        <label
          htmlFor="activity_input"
          className="block text-sm font-medium"
        >
          {t("form_label_activity")}
        </label>
        <input
          id="activity_input"
          type="text"
          value={activityInput}
          onChange={(e) => setActivityInput(e.target.value)}
          className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
          placeholder="50, 50"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          {t("form_hint_activity")} (현재 {computeSumPct(parseList(activityInput))}%)
        </p>
      </div>
      <div>
        <label
          htmlFor="driver_input"
          className="block text-sm font-medium"
        >
          {t("form_label_driver")}
        </label>
        <input
          id="driver_input"
          type="text"
          value={driverInput}
          onChange={(e) => setDriverInput(e.target.value)}
          className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
          placeholder="60, 40"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          {t("form_hint_driver")} (현재 {computeSumPct(parseList(driverInput))}%)
        </p>
      </div>

      {error !== null ? (
        <div
          className="mt-2 rounded bg-red-100 p-2 text-sm text-red-700"
          data-testid="abc-validation-error"
        >
          {error}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
        data-testid="abc-validation-submit"
      >
        {submitting ? t("submitting") : t("form_submit_label")}
      </button>
    </form>
  );
}