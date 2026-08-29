"use client";

/**
 * apps/web/components/m9-abc/AbcAllocationPanel.tsx — Story 9.2
 *
 * Main Client Component for the M9 ABC Allocation Engine UI
 * (PRD §F9.2 + §A9 + §V7 verbatim).
 *
 * Per AC #2 + AC #3 + AC #4 (Story 9.2):
 *  - 3-input form: department_id + department_cost + practical_capacity_hours.
 *  - On submit: in-memory computeCcrTS → CCRResult + UnusedCapacityRow +
 *    CostObjectBreakdownTable + V7 balance check.
 *  - Renders <CcrResultCard> + <UnusedCapacityRow> + <CostObjectBreakdownTable>.
 *  - Capability gate ABC_CALCULATION enforced server-side (CR 12-5 L3).
 *  - 422 CCR_INVALID_CAPACITY + 422 ALLOCATION_BALANCE_ERROR envelopes
 *    surface as inline errors.
 *
 * Composes the form + 4-section result panel (CCR + Unused + Breakdown +
 * Balance Badge).
 *
 * The page itself is rendered via
 * `(dashboard)/budget/abc-allocation/page.tsx`.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import {
  ABC_ALLOCATION_BALANCE_ERROR_KO,
  ABC_CCR_INVALID_CAPACITY_KO,
  type AllocationResult,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  type CCRResult,
  type CostObjectRow,
  type ActivityMapping,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  type UnusedCapacityRow as UnusedCapacityRowType,
  isAllocationResult,
} from "@/lib/m9-abc-allocation";
import {
  AbcAllocationInputError,
  buildKoreanUnusedCapacityMessage,
  computeAllocationTS,
  computeCcrTS,
  isBalancedAllocation,
} from "@/lib/m9-abc-allocation-schema";

import { CcrResultCard } from "./CcrResultCard";
import { CostObjectBreakdownTable } from "./CostObjectBreakdownTable";
import { UnusedCapacityRow } from "./UnusedCapacityRow";

interface AbcAllocationPanelProps {
  accessToken: string | undefined;
  initialAllocation: AllocationResult | null;
  initialError: string | null;
}

interface DemoPreset {
  cost: string;
  hours: string;
  used: string;
  activityMappings: ActivityMapping[];
  breakdown: CostObjectRow[];
}

const DEMO_PRESET: DemoPreset = {
  cost: "13200000",
  hours: "400",
  used: "400",
  activityMappings: [
    {
      activity_id: "act-001",
      hours: "400",
      ccr_amount_krw: "13200000",
    },
  ],
  breakdown: [
    {
      product_id: "prod-A",
      activity_id: "act-001",
      driver_id: "drv-001",
      allocated_krw: "13200000",
    },
  ],
};

export function AbcAllocationPanel({
  accessToken,
  initialAllocation,
  initialError,
}: AbcAllocationPanelProps): React.ReactElement {
  const t = useTranslations("abc_allocation");

  const [allocation, setAllocation] = useState<AllocationResult | null>(
    initialAllocation,
  );
  const [error, setError] = useState<string | null>(initialError);
  const [ccrError, setCcrError] = useState<string | null>(null);
  const [departmentId, setDepartmentId] = useState<string>("dept-001");
  const [departmentCost, setDepartmentCost] = useState<string>("13200000");
  const [practicalCapacity, setPracticalCapacity] = useState<string>("400");
  const [usedHours, setUsedHours] = useState<string>("400");
  const [submitting, setSubmitting] = useState<boolean>(false);

  const handleCompute = useCallback((): void => {
    setError(null);
    setCcrError(null);

    try {
      const ccr = computeCcrTS({
        department_id: departmentId,
        department_cost: departmentCost,
        practical_capacity_hours: practicalCapacity,
      });

      const result = computeAllocationTS({
        ccr,
        activity_mappings: DEMO_PRESET.activityMappings,
        cost_object_breakdown: DEMO_PRESET.breakdown,
        used_hours: usedHours,
      });

      if (!isAllocationResult(result)) {
        setError("invalid_result_shape");
        return;
      }

      setAllocation(result);
      if (!isBalancedAllocation(result)) {
        setError(ABC_ALLOCATION_BALANCE_ERROR_KO);
      }
    } catch (e) {
      if (e instanceof AbcAllocationInputError) {
        if (e.target === "ccr") {
          setCcrError(e.message);
          setError(ABC_CCR_INVALID_CAPACITY_KO);
        } else {
          setError(e.message);
        }
        return;
      }
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [departmentId, departmentCost, practicalCapacity, usedHours]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      setSubmitting(true);
      try {
        handleCompute();
      } finally {
        setSubmitting(false);
      }
    },
    [handleCompute],
  );

  return (
    <main className="p-6" data-testid="abc-allocation-panel">
      <h1 className="text-2xl font-semibold">
        {t("page_title")}
      </h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      {error !== null ? (
        <div
          className="mt-3 rounded bg-red-100 p-3 text-sm text-red-700"
          data-testid="abc-allocation-error-banner"
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

          <form
            onSubmit={handleSubmit}
            className="mt-3 space-y-3"
            data-testid="abc-allocation-form"
          >
            <div>
              <label
                htmlFor="department_id_input"
                className="block text-sm font-medium"
              >
                {t("form_label_department_id")}
              </label>
              <input
                id="department_id_input"
                type="text"
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
                required
              />
            </div>
            <div>
              <label
                htmlFor="department_cost_input"
                className="block text-sm font-medium"
              >
                {t("form_label_department_cost")}
              </label>
              <input
                id="department_cost_input"
                type="text"
                value={departmentCost}
                onChange={(e) => setDepartmentCost(e.target.value)}
                className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                {t("form_hint_department_cost")}
              </p>
            </div>
            <div>
              <label
                htmlFor="practical_capacity_input"
                className="block text-sm font-medium"
              >
                {t("form_label_practical_capacity")}
              </label>
              <input
                id="practical_capacity_input"
                type="text"
                value={practicalCapacity}
                onChange={(e) => setPracticalCapacity(e.target.value)}
                className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                {t("form_hint_practical_capacity")}
              </p>
            </div>
            <div>
              <label
                htmlFor="used_hours_input"
                className="block text-sm font-medium"
              >
                {t("form_label_used_hours")}
              </label>
              <input
                id="used_hours_input"
                type="text"
                value={usedHours}
                onChange={(e) => setUsedHours(e.target.value)}
                className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                {t("form_hint_used_hours")}
              </p>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
              data-testid="abc-allocation-submit"
            >
              {submitting ? t("submitting") : t("form_submit_label")}
            </button>
          </form>
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-medium">{t("panel_result_title")}</h2>
          {allocation !== null ? (
            <>
              <CcrResultCard ccr={allocation.ccr} messageKo={ccrError} />
              <UnusedCapacityRow unused={allocation.unused_capacity} />
              <div
                className="text-sm text-gray-600"
                data-testid="abc-allocation-unused-message"
              >
                {buildKoreanUnusedCapacityMessage(allocation.unused_capacity)}
              </div>
              <CostObjectBreakdownTable
                activityMappings={allocation.activity_mappings}
                rows={allocation.cost_object_breakdown}
                totalBreakdownSum={allocation.total_breakdown_sum}
                isBalanced={allocation.is_balanced}
              />
            </>
          ) : (
            <p className="text-sm text-gray-500">{t("empty_result")}</p>
          )}
        </div>
      </section>

      {accessToken === undefined ? (
        <p
          className="mt-3 text-xs text-gray-500"
          data-testid="abc-allocation-no-token"
        >
          {t("no_token_notice")}
        </p>
      ) : null}
    </main>
  );
}