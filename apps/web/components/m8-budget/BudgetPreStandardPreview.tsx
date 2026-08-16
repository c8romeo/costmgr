"use client";

/**
 * apps/web/components/m8-budget/BudgetPreStandardPreview.tsx — Story 8.3
 *
 * Client Component for the M8 budget pre-standard cost preview UI.
 *
 * Per AC #4 (Story 8.3):
 *  - Mounts 5-field form (material_unit_cost, labor_unit_cost, overhead_rate,
 *    material_qty, labor_hours) + period_key.
 *  - On submit: POST /api/v1/budget/pre-standard → PreStandardCost snapshot.
 *  - On mount: GET /api/v1/budget/pre-standard?period_key=2026-07#B1 → display
 *    existing snapshot if present.
 *  - 4-role read (owner+member+viewer+consultant_proxy); owner+member write.
 *  - 409 PRE_STANDARD_ALREADY_EXISTS + 422 INVALID_PRE_STANDARD_INPUT envelopes
 *    surface as toast errors.
 *  - 8-3 wire: composes <PreStandardCostTable> + <PreStandardPdfButton> +
 *    <PreStandardHashBadge>.
 *
 * The page itself is rendered via
 * `(dashboard)/budget/pre-standard/page.tsx` which calls
 * `fetchBudgetPreStandardServerSide` for the initial snapshot.
 */

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useState } from "react";

import {
  type BudgetPreStandardResponse,
  DEFAULT_PRE_STANDARD_PERIOD_KEY,
  isValidVirtualBudgetPeriodKeyTS,
} from "@/lib/m8-budget-pre-standard";

import { PreStandardCostTable } from "./PreStandardCostTable";
import { PreStandardHashBadge } from "./PreStandardHashBadge";
import { PreStandardPdfButton } from "./PreStandardPdfButton";

interface BudgetPreStandardPreviewProps {
  initialSnapshot: BudgetPreStandardResponse | null;
  accessToken: string | undefined;
  initialError: string | null;
}

export function BudgetPreStandardPreview({
  initialSnapshot,
  accessToken,
  initialError,
}: BudgetPreStandardPreviewProps): React.ReactElement {
  const t = useTranslations("budget_pre_standard");

  const [snapshot, setSnapshot] = useState<BudgetPreStandardResponse | null>(
    initialSnapshot,
  );
  const [error, setError] = useState<string | null>(initialError);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [periodKey, setPeriodKey] = useState<string>(DEFAULT_PRE_STANDARD_PERIOD_KEY);

  // 5 form fields (PRD §F8.3).
  const [materialUnitCost, setMaterialUnitCost] = useState<string>("0");
  const [laborUnitCost, setLaborUnitCost] = useState<string>("0");
  const [overheadRate, setOverheadRate] = useState<string>("0");
  const [materialQty, setMaterialQty] = useState<string>("0");
  const [laborHours, setLaborHours] = useState<string>("0");

  // ── Refresh snapshot ─────────────────────────────────────────
  const refreshSnapshot = useCallback(async (): Promise<void> => {
    if (!isValidVirtualBudgetPeriodKeyTS(periodKey)) {
      return;
    }
    try {
      const res = await fetch(
        `/api/v1/budget/pre-standard?period_key=${encodeURIComponent(periodKey)}`,
        {
          method: "GET",
          headers: {
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          cache: "no-store",
        },
      );
      if (res.status === 404) {
        setSnapshot(null);
        setError(null);
        return;
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`);
        return;
      }
      const data: BudgetPreStandardResponse = await res.json();
      setSnapshot(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [accessToken, periodKey]);

  useEffect(() => {
    void refreshSnapshot();
  }, [refreshSnapshot]);

  // ── Submit handler ───────────────────────────────────────────
  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      setSubmitting(true);
      setError(null);

      try {
        const res = await fetch(`/api/v1/budget/pre-standard`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          body: JSON.stringify({
            period_key: periodKey,
            scenario_index: 1,
            material_unit_cost: materialUnitCost,
            labor_unit_cost: laborUnitCost,
            overhead_rate: overheadRate,
            material_qty: materialQty,
            labor_hours: laborHours,
          }),
        });
        if (!res.ok) {
          const data = (await res.json().catch(() => null)) as
            | { code?: string; message_ko?: string }
            | null;
          if (data?.code === "PRE_STANDARD_ALREADY_EXISTS") {
            setError(t("already_exists"));
          } else if (data?.code === "INVALID_PRE_STANDARD_INPUT") {
            setError(t("invalid_input"));
          } else if (data?.code === "CAPABILITY_NOT_GRANTED") {
            setError(t("capability_denied"));
          } else {
            setError(`HTTP ${res.status}`);
          }
          return;
        }
        const data: BudgetPreStandardResponse = await res.json();
        setSnapshot(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setSubmitting(false);
      }
    },
    [
      accessToken,
      periodKey,
      materialUnitCost,
      laborUnitCost,
      overheadRate,
      materialQty,
      laborHours,
      t,
    ],
  );

  return (
    <div className="budget-pre-standard-preview" data-testid="budget-pre-standard-preview">
      <h1 className="text-2xl font-bold">{t("page_title")}</h1>
      <p className="text-sm text-gray-600">{t("page_subtitle")}</p>

      {error ? (
        <div className="mt-3 rounded bg-red-100 p-3 text-sm text-red-700" data-testid="error-banner">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3" data-testid="pre-standard-form">
        <div>
          <label htmlFor="period_key" className="block text-sm font-medium">
            {t("form_label_period_key")}
          </label>
          <input
            id="period_key"
            type="text"
            value={periodKey}
            onChange={(e) => setPeriodKey(e.target.value)}
            className="mt-1 block w-full rounded border px-2 py-1"
            required
          />
        </div>
        <div>
          <label htmlFor="material_unit_cost" className="block text-sm font-medium">
            {t("form_label_material_unit_cost")}
          </label>
          <input
            id="material_unit_cost"
            type="number"
            value={materialUnitCost}
            onChange={(e) => setMaterialUnitCost(e.target.value)}
            min="0"
            className="mt-1 block w-full rounded border px-2 py-1"
            required
          />
        </div>
        <div>
          <label htmlFor="labor_unit_cost" className="block text-sm font-medium">
            {t("form_label_labor_unit_cost")}
          </label>
          <input
            id="labor_unit_cost"
            type="number"
            value={laborUnitCost}
            onChange={(e) => setLaborUnitCost(e.target.value)}
            min="0"
            className="mt-1 block w-full rounded border px-2 py-1"
            required
          />
        </div>
        <div>
          <label htmlFor="overhead_rate" className="block text-sm font-medium">
            {t("form_label_overhead_rate")}
          </label>
          <input
            id="overhead_rate"
            type="number"
            value={overheadRate}
            onChange={(e) => setOverheadRate(e.target.value)}
            min="0"
            max="100"
            step="0.01"
            className="mt-1 block w-full rounded border px-2 py-1"
            required
          />
        </div>
        <div>
          <label htmlFor="material_qty" className="block text-sm font-medium">
            {t("form_label_material_qty")}
          </label>
          <input
            id="material_qty"
            type="number"
            value={materialQty}
            onChange={(e) => setMaterialQty(e.target.value)}
            min="0"
            className="mt-1 block w-full rounded border px-2 py-1"
            required
          />
        </div>
        <div>
          <label htmlFor="labor_hours" className="block text-sm font-medium">
            {t("form_label_labor_hours")}
          </label>
          <input
            id="labor_hours"
            type="number"
            value={laborHours}
            onChange={(e) => setLaborHours(e.target.value)}
            min="0"
            className="mt-1 block w-full rounded border px-2 py-1"
            required
          />
        </div>
        <div className="flex space-x-2">
          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
            data-testid="submit-button"
          >
            {submitting ? t("submitting") : t("form_submit_label")}
          </button>
          <button
            type="button"
            onClick={() => {
              setMaterialUnitCost("0");
              setLaborUnitCost("0");
              setOverheadRate("0");
              setMaterialQty("0");
              setLaborHours("0");
            }}
            className="rounded bg-gray-300 px-4 py-2 text-gray-700"
            data-testid="clear-button"
          >
            {t("form_clear_label")}
          </button>
        </div>
      </form>

      {snapshot !== null ? (
        <div className="mt-6">
          <PreStandardCostTable snapshot={snapshot.snapshot} />
          <PreStandardHashBadge resultHash={snapshot.snapshot.result_hash} />
          <PreStandardPdfButton
            accessToken={accessToken}
            periodKey={snapshot.snapshot.period_key}
            snapshotReady={true}
          />
        </div>
      ) : null}
    </div>
  );
}
