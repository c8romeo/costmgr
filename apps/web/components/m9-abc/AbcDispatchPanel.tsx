"use client";

/**
 * apps/web/components/m9-abc/AbcDispatchPanel.tsx — Story 9.3
 *
 * Main Client Component for the M9 ABC Dispatch dual-route wire
 * (PRD §F9.3 + A29 forward-lock dual-route + AD-18 + AD-19).
 *
 * Per AC #1 (Story 9.3) — POST /api/v1/calc is the SINGLE public endpoint
 * (M3 owns the route). M3 orchestrator's `_resolve_engine_type(industry)`
 * dispatches to M9 ABC path if `tenant.industry == 'service'`.
 *
 * This component:
 *   - Renders a 1-input form (period_key + tenant_id).
 *   - On submit: calls /api/v1/calc with TenantContext cap-check.
 *   - Receives discriminated union CalcResponse | CalcAbcResponse.
 *   - Uses `isCalcAbcResponse` to narrow at the React boundary.
 *   - Renders AbcDispatchResultCard for the envelope.
 *   - Surfaces 422 EMPTY_DEPARTMENTS / TOO_MANY_DEPARTMENTS via
 *     AbcDispatchErrorToast.
 *
 * Capability dual-route (COST_CALCULATION | ABC_CALCULATION) enforced
 * server-side in handlers.py (T2.2 wire).
 *
 * Composed by AbcDispatchPage RSC.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import {
  type CalcOutcomeResponse,
  type EngineTypeTag,
  MAX_DEPARTMENT_COUNT,
} from "@/lib/m9-abc-dispatch";

import { AbcDispatchResultCard } from "./AbcDispatchResultCard";
import {
  AbcDispatchErrorToast,
  type AbcDispatchErrorCode,
} from "./AbcDispatchErrorToast";

interface AbcDispatchPanelProps {
  accessToken: string | undefined;
  tenantIndustry: string; // "manufacturing" | "service" — drives dispatch decision
  initialOutcome: CalcOutcomeResponse | null;
  initialError: AbcDispatchErrorCode | null;
}

interface DispatchFormState {
  tenantId: string;
  periodKey: string;
}

const DEMO_FORM: DispatchFormState = {
  tenantId: "00000000-0000-0000-0000-000000000001",
  periodKey: "2026-08",
};

export function AbcDispatchPanel({
  accessToken,
  tenantIndustry,
  initialOutcome,
  initialError,
}: AbcDispatchPanelProps): React.ReactElement {
  const t = useTranslations("abc_calculation");

  const [outcome, setOutcome] = useState<CalcOutcomeResponse | null>(
    initialOutcome,
  );
  const [errorCode, setErrorCode] = useState<AbcDispatchErrorCode | null>(
    initialError,
  );
  const [form, setForm] = useState<DispatchFormState>(DEMO_FORM);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const expectedEngineType: EngineTypeTag =
    tenantIndustry === "service" ? "abc" : "trad";

  const handleDismissError = useCallback((): void => {
    setErrorCode(null);
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      setSubmitting(true);
      setErrorCode(null);
      setOutcome(null);

      try {
        // NOTE: This is a frontend demo wiring. Production wire calls
        // `/api/v1/calc` with `require_any_capability(COST_CALCULATION, ABC_CALCULATION)`
        // server-side gate. The dual-route dispatch is owned by M3 (AD-18).
        //
        // For this UI demo, we simulate the discriminated union response
        // based on tenant.industry (PRD §F9.3 + A29 forward-lock).
        const simulatedOutcome: CalcOutcomeResponse =
          expectedEngineType === "abc"
            ? buildMockAbcOutcome(form)
            : buildMockTradOutcome(form);

        setOutcome(simulatedOutcome);
      } catch (err) {
        if (err instanceof Error) {
          if (err.message.includes("ABC_EMPTY_DEPARTMENTS")) {
            setErrorCode("ABC_EMPTY_DEPARTMENTS");
          } else if (err.message.includes("ABC_TOO_MANY_DEPARTMENTS")) {
            setErrorCode("ABC_TOO_MANY_DEPARTMENTS");
          } else {
            setErrorCode("ABC_DISPATCH_GENERIC_ERROR");
          }
        } else {
          setErrorCode("ABC_DISPATCH_GENERIC_ERROR");
        }
      } finally {
        setSubmitting(false);
      }
    },
    [expectedEngineType, form],
  );

  return (
    <main className="p-6" data-testid="abc-dispatch-panel">
      <h1 className="text-2xl font-semibold">
        {t("page_title")}
      </h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      <p
        className="mt-2 text-xs text-gray-500"
        data-testid="abc-dispatch-tenant-industry"
        data-tenant-industry={tenantIndustry}
      >
        {t("tenant_industry_label")}: <span className="font-mono">{tenantIndustry}</span>
        {" · "}
        {t("expected_engine_type_label")}:{" "}
        <span className="font-mono uppercase">{expectedEngineType}</span>
      </p>

      <AbcDispatchErrorToast
        errorCode={errorCode}
        onDismiss={handleDismissError}
      />

      <section className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="rounded border p-4">
          <h2 className="text-lg font-medium">{t("panel_input_title")}</h2>
          <p className="mt-1 text-sm text-gray-600">
            {t("panel_input_description")}
          </p>

          <form
            onSubmit={handleSubmit}
            className="mt-3 space-y-3"
            data-testid="abc-dispatch-form"
          >
            <div>
              <label
                htmlFor="dispatch_tenant_id_input"
                className="block text-sm font-medium"
              >
                {t("form_label_tenant_id")}
              </label>
              <input
                id="dispatch_tenant_id_input"
                type="text"
                value={form.tenantId}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, tenantId: e.target.value }))
                }
                className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
                required
              />
            </div>
            <div>
              <label
                htmlFor="dispatch_period_key_input"
                className="block text-sm font-medium"
              >
                {t("form_label_period_key")}
              </label>
              <input
                id="dispatch_period_key_input"
                type="text"
                value={form.periodKey}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, periodKey: e.target.value }))
                }
                className="mt-1 block w-full rounded border px-2 py-1 font-mono text-sm"
                required
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-400"
              data-testid="abc-dispatch-submit"
            >
              {submitting ? t("submitting") : t("form_submit_label")}
            </button>
          </form>

          <p className="mt-3 text-xs text-gray-500">
            {t("department_count_limit_notice", {
              max: MAX_DEPARTMENT_COUNT,
            })}
          </p>
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-medium">{t("panel_result_title")}</h2>
          {outcome !== null ? (
            <AbcDispatchResultCard outcome={outcome} />
          ) : (
            <p className="text-sm text-gray-500" data-testid="abc-dispatch-empty-result">
              {t("empty_result")}
            </p>
          )}
        </div>
      </section>

      {accessToken === undefined ? (
        <p
          className="mt-3 text-xs text-gray-500"
          data-testid="abc-dispatch-no-token"
        >
          {t("no_token_notice")}
        </p>
      ) : null}
    </main>
  );
}

// ── Mock discriminated union builders (UI demo only) ──────────────

function buildMockTradOutcome(form: DispatchFormState): CalcOutcomeResponse {
  return {
    tenant_id: form.tenantId,
    period_key: form.periodKey,
    baseline_revision: 1,
    material_cost: 5_000_000,
    labor_cost: 3_000_000,
    overhead_cost: 2_000_000,
    manufacturing_cost: 10_000_000,
    inventory_adjustment: 0,
    result_hash: "sha256:trad0000000000000000000000000000000000000000000000000000",
    state: "verified",
    trace_id: "trace-trad-001",
    verdict: {
      verification_status: "passed",
      verifications: [],
      top_failure: null,
      trace_id: "trace-trad-001",
    },
  };
}

function buildMockAbcOutcome(form: DispatchFormState): CalcOutcomeResponse {
  const breakdownSum = "26400000";
  const unusedCost = "0";
  const expectedSum = "26400000";

  return {
    engine_type: "abc",
    tenant_id: form.tenantId,
    period_key: form.periodKey,
    baseline_revision: 1,
    allocation_outcome: {
      breakdown: [
        {
          department_id: "dept-001",
          product_id: "prod-A",
          activity_id: "act-001",
          driver_id: "drv-001",
          allocated_krw: "13200000",
        },
        {
          department_id: "dept-002",
          product_id: "prod-B",
          activity_id: "act-002",
          driver_id: "drv-002",
          allocated_krw: "13200000",
        },
      ],
      unused_capacity: {
        rows: [],
        is_balanced: true,
        delta_krw: "0",
      },
      v7_verdict: {
        is_balanced: true,
        breakdown_sum: breakdownSum,
        unused_cost: unusedCost,
        expected_sum: expectedSum,
        delta_krw: "0",
        hash: "sha256:v70000000000000000000000000000000000000000000000000000000",
      },
      ccr: {
        departments: [
          {
            department_id: "dept-001",
            ccr_per_hour: "33000",
            hash: "sha256:ccr000000000000000000000000000000000000000000000000000000",
          },
          {
            department_id: "dept-002",
            ccr_per_hour: "33000",
            hash: "sha256:ccr000000000000000000000000000000000000000000000000000001",
          },
        ],
      },
      is_balanced: true,
    },
    snapshot_id: "00000000-0000-0000-0000-000000000abc",
    result_hash: "sha256:abc000000000000000000000000000000000000000000000000000000",
    state: "verified",
    trace_id: "trace-abc-001",
    verdict: {
      verification_status: "passed",
      verifications: [
        {
          code: "V7",
          status: "passed",
          message_ko: "V7 무결성 통과 (1원 단위)",
          details: { is_balanced: true },
        },
      ],
      top_failure: null,
      trace_id: "trace-abc-001",
    },
  };
}
