"use client";

/**
 * apps/web/components/m8-budget/BudgetScenarioPanel.tsx — Story 8.1
 *
 * Client Component for the M8 budget scenario management UI.
 *
 * Per AC #4 (Story 8.1):
 *  - Lists tenant's scenarios (default empty, max 1 in 1차 MVP) via
 *    `GET /api/v1/budget/scenarios`.
 *  - Owner/member can [시나리오 만들기] → calls `POST /api/v1/budget/scenarios`
 *    with real_period_key (YYYY-MM).
 *  - 409 SCENARIO_LIMIT_EXCEEDED envelope surfaces in toast + disabled button.
 *  - 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY envelope surfaces inline error.
 *
 * The page itself is rendered via
 * `(dashboard)/budget/scenarios/page.tsx` which calls
 * `fetchBudgetScenariosServerSide` for the initial list.
 */

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";

import {
  type BudgetScenarioListResponse,
  type BudgetScenarioSerialized,
  isValidRealPeriodKeyTS,
  MVP_MAX_SCENARIOS_PER_TENANT,
  SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO,
} from "@/lib/m8-budget-scenario";

interface BudgetScenarioPanelProps {
  initialList: BudgetScenarioListResponse | null;
  accessToken: string | undefined;
  initialError: string | null;
}

export function BudgetScenarioPanel({
  initialList,
  accessToken,
  initialError,
}: BudgetScenarioPanelProps): React.ReactElement {
  const t = useTranslations("budget_scenario");
  const [list, setList] = useState<BudgetScenarioListResponse | null>(initialList);
  const [error, setError] = useState<string | null>(initialError);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [periodInput, setPeriodInput] = useState<string>("");
  const [createError, setCreateError] = useState<string | null>(null);

  const scenarios: BudgetScenarioSerialized[] = list?.scenarios ?? [];
  const limitReached = scenarios.length >= MVP_MAX_SCENARIOS_PER_TENANT;

  // ── Refresh list ─────────────────────────────────────────────
  const refreshList = useCallback(async (): Promise<void> => {
    try {
      const res = await fetch(`/api/v1/budget/scenarios`, {
        method: "GET",
        headers: {
          Authorization: accessToken ? `Bearer ${accessToken}` : "",
          "X-Trace-Id": crypto.randomUUID(),
        },
        cache: "no-store",
      });
      if (!res.ok) {
        setError(`HTTP ${res.status}`);
        return;
      }
      const data: BudgetScenarioListResponse = await res.json();
      setList(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [accessToken]);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  // ── Create scenario ──────────────────────────────────────────
  const handleCreate = useCallback(async (): Promise<void> => {
    setCreateError(null);

    if (!isValidRealPeriodKeyTS(periodInput)) {
      setCreateError(t("invalid_period_key_message"));
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`/api/v1/budget/scenarios`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: accessToken ? `Bearer ${accessToken}` : "",
          "X-Trace-Id": crypto.randomUUID(),
        },
        body: JSON.stringify({ real_period_key: periodInput }),
        cache: "no-store",
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as {
          code?: string;
          message_ko?: string;
        };
        if (body.code === "SCENARIO_LIMIT_EXCEEDED") {
          setCreateError(SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO);
        } else if (body.code === "INVALID_VIRTUAL_BUDGET_PERIOD_KEY") {
          setCreateError(t("invalid_period_key_message"));
        } else {
          setCreateError(body.message_ko ?? `HTTP ${res.status}`);
        }
        return;
      }
      // Success — close modal + refresh.
      setModalOpen(false);
      setPeriodInput("");
      await refreshList();
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }, [periodInput, accessToken, refreshList, t]);

  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">{t("page_title")}</h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      <section className="mt-6 rounded border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">{t("panel_title")}</h2>
          <button
            type="button"
            className="rounded bg-blue-600 px-3 py-1 text-white disabled:bg-gray-400"
            disabled={limitReached}
            onClick={() => setModalOpen(true)}
          >
            {t("create_button")}
          </button>
        </div>
        <p className="mt-2 text-sm text-gray-600">{t("panel_description")}</p>

        {error ? (
          <p className="mt-3 text-sm text-red-600">
            {t("load_failed")} ({error})
          </p>
        ) : null}

        {scenarios.length === 0 ? (
          <p className="mt-3 text-sm text-gray-500">{t("empty_message")}</p>
        ) : (
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2 text-left">{t("col_period_key")}</th>
                <th className="py-2 text-left">{t("col_real_period_key")}</th>
                <th className="py-2 text-left">{t("col_scenario_hash")}</th>
                <th className="py-2 text-left">{t("col_created_at")}</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => (
                <tr key={s.id} className="border-b">
                  <td className="py-2 font-mono">{s.period_key}</td>
                  <td className="py-2 font-mono">{s.real_period_key}</td>
                  <td className="py-2 font-mono text-xs">
                    {s.scenario_hash.slice(0, 16)}…
                  </td>
                  <td className="py-2">{s.created_at_kst}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-96 rounded bg-white p-6 shadow-lg">
            <h3 className="text-lg font-medium">{t("modal_title")}</h3>
            <p className="mt-1 text-sm text-gray-600">
              {t("modal_description")}
            </p>
            <label className="mt-4 block text-sm font-medium">
              {t("real_period_key_label")}
              <input
                type="text"
                value={periodInput}
                placeholder={t("real_period_key_placeholder")}
                onChange={(e) => setPeriodInput(e.target.value)}
                className="mt-1 block w-full rounded border px-2 py-1"
              />
            </label>
            <p className="mt-1 text-xs text-gray-500">
              {t("real_period_key_hint")}
            </p>
            {createError ? (
              <p className="mt-2 text-sm text-red-600">{createError}</p>
            ) : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded border px-3 py-1"
                onClick={() => {
                  setModalOpen(false);
                  setCreateError(null);
                  setPeriodInput("");
                }}
              >
                {t("cancel")}
              </button>
              <button
                type="button"
                className="rounded bg-blue-600 px-3 py-1 text-white disabled:bg-gray-400"
                disabled={submitting || periodInput.length === 0}
                onClick={() => void handleCreate()}
              >
                {submitting ? t("create_submitting") : t("create_submit")}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}