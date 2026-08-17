"use client";

/**
 * apps/web/components/m9-abc/AbcDispatchResultCard.tsx — Story 9.3
 *
 * Discriminated union result renderer for POST /api/v1/calc dual-route
 * (PRD §F9.3 + A29 forward-lock dual-route + AD-19).
 *
 * Per AC #2 (Story 9.3) — CalcOutcomeResponse = CalcResponse | CalcAbcResponse:
 *   - CalcResponse (trad path): material_cost + labor_cost + overhead_cost
 *   - CalcAbcResponse (abc path): allocation_outcome (breakdown + unused + CCR + V7 verdict)
 *
 * Uses `isCalcAbcResponse` type guard to narrow to ABC path and renders
 * 4 sections: dispatch decision badge + V7 verdict + CCR table +
 * cost object breakdown table.
 *
 * Composed by AbcDispatchPanel.
 */

import { useTranslations } from "next-intl";

import {
  type CalcOutcomeResponse,
  type CalcAbcResponse,
  isCalcAbcResponse,
} from "@/lib/m9-abc-dispatch";

import {
  formatV7DeltaKrw,
  formatV7VerdictLabel,
  V7_BALANCED_KO,
  V7_UNBALANCED_KO,
} from "@/lib/m9-abc-v7-verdict-schema";

import { AbcDispatchDecisionBadge } from "./AbcDispatchDecisionBadge";

/** Format a Decimal-as-string KRW integer for display (ko-KR thousands separator). */
function formatDecimalAsKr(value: string): string {
  const num = Number.parseFloat(value);
  if (!Number.isFinite(num)) {
    return value;
  }
  return Math.round(num).toLocaleString("ko-KR");
}

interface AbcDispatchResultCardProps {
  outcome: CalcOutcomeResponse;
}

export function AbcDispatchResultCard({
  outcome,
}: AbcDispatchResultCardProps): React.ReactElement {
  const t = useTranslations("abc_calculation");

  // Trad path — CalcResponse without engine_type tag (PRD §F9.3).
  if (!isCalcAbcResponse(outcome)) {
    return (
      <section
        className="mt-4 rounded border border-gray-300 bg-gray-50 p-4"
        data-testid="abc-dispatch-result-trad"
        data-engine-type="trad"
        role="region"
        aria-label={t("result_card_trad_aria")}
      >
        <header className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">
            {t("result_card_trad_title")}
          </h2>
          <AbcDispatchDecisionBadge
            engineType="trad"
            tenantIndustry="manufacturing"
            reason={t("dispatch_reason_trad_default")}
          />
        </header>

        <dl className="grid gap-2 text-sm md:grid-cols-2">
          <div>
            <dt className="text-xs text-gray-500">
              {t("field_material_cost")}
            </dt>
            <dd
              className="font-mono"
              data-testid="abc-dispatch-trad-material-cost"
            >
              {outcome.material_cost.toLocaleString("ko-KR")}원
            </dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">{t("field_labor_cost")}</dt>
            <dd
              className="font-mono"
              data-testid="abc-dispatch-trad-labor-cost"
            >
              {outcome.labor_cost.toLocaleString("ko-KR")}원
            </dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">
              {t("field_overhead_cost")}
            </dt>
            <dd
              className="font-mono"
              data-testid="abc-dispatch-trad-overhead-cost"
            >
              {outcome.overhead_cost.toLocaleString("ko-KR")}원
            </dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">
              {t("field_manufacturing_cost")}
            </dt>
            <dd
              className="font-mono"
              data-testid="abc-dispatch-trad-manufacturing-cost"
            >
              {outcome.manufacturing_cost.toLocaleString("ko-KR")}원
            </dd>
          </div>
        </dl>

        <footer className="mt-3 border-t pt-2 text-xs text-gray-500">
          <span>
            {t("field_result_hash")}:{" "}
            <span
              className="font-mono"
              data-testid="abc-dispatch-trad-result-hash"
            >
              {outcome.result_hash}
            </span>
          </span>
        </footer>
      </section>
    );
  }

  // ABC path — CalcAbcResponse with engine_type='abc' tag.
  return <AbcDispatchResultAbc outcome={outcome} />;
}

interface AbcDispatchResultAbcProps {
  outcome: CalcAbcResponse;
}

function AbcDispatchResultAbc({
  outcome,
}: AbcDispatchResultAbcProps): React.ReactElement {
  const t = useTranslations("abc_calculation");
  const allocation = outcome.allocation_outcome;
  const v7 = allocation.v7_verdict;
  const v7Label = v7.is_balanced ? V7_BALANCED_KO : V7_UNBALANCED_KO;

  return (
    <section
      className="mt-4 rounded border border-blue-300 bg-blue-50 p-4"
      data-testid="abc-dispatch-result-abc"
      data-engine-type="abc"
      data-snapshot-id={outcome.snapshot_id}
      role="region"
      aria-label={t("result_card_abc_aria")}
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-blue-800">
          {t("result_card_abc_title")}
        </h2>
        <AbcDispatchDecisionBadge
          engineType="abc"
          tenantIndustry="service"
          reason={t("dispatch_reason_abc_default")}
        />
      </header>

      {/* V7 verdict badge — Σ breakdown + unused = Σ department (1-Won precision). */}
      <div
        className={[
          "mb-3 inline-flex items-center gap-2 rounded px-3 py-1 text-xs font-medium",
          v7.is_balanced
            ? "bg-green-100 text-green-800 border border-green-300"
            : "bg-red-100 text-red-800 border border-red-300",
        ].join(" ")}
        data-testid="abc-dispatch-v7-badge"
        data-is-balanced={v7.is_balanced}
        role="status"
        aria-label={v7.is_balanced ? t("v7_passed_aria") : t("v7_failed_aria")}
      >
        <span>{v7Label}</span>
        {!v7.is_balanced ? (
          <span className="font-mono">
            Δ={formatV7DeltaKrw(v7.delta_krw)}
          </span>
        ) : null}
      </div>

      {/* CCR per department table (PRD §F9.3). */}
      <div className="mb-3">
        <h3 className="mb-1 text-sm font-semibold text-gray-700">
          {t("section_ccr_title")}
        </h3>
        <table
          className="w-full border-collapse text-sm"
          data-testid="abc-dispatch-ccr-table"
        >
          <thead>
            <tr className="border-b text-left text-xs text-gray-500">
              <th className="py-1">{t("field_department_id")}</th>
              <th className="py-1">{t("field_ccr_per_hour")}</th>
              <th className="py-1">{t("field_hash")}</th>
            </tr>
          </thead>
          <tbody>
            {allocation.ccr.departments.map((dept) => (
              <tr key={dept.department_id} className="border-b">
                <td className="py-1 font-mono">{dept.department_id}</td>
                <td className="py-1 font-mono">
                  {formatDecimalAsKr(dept.ccr_per_hour)}원/h
                </td>
                <td className="py-1 font-mono text-xs text-gray-500">
                  {dept.hash.slice(0, 12)}…
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cost object breakdown table (PRD §A6 + §V7). */}
      <div className="mb-3">
        <h3 className="mb-1 text-sm font-semibold text-gray-700">
          {t("section_breakdown_title")}{" "}
          <span className="text-xs text-gray-500">
            ({allocation.breakdown.length} {t("unit_rows")})
          </span>
        </h3>
        <table
          className="w-full border-collapse text-sm"
          data-testid="abc-dispatch-breakdown-table"
        >
          <thead>
            <tr className="border-b text-left text-xs text-gray-500">
              <th className="py-1">{t("field_department_id")}</th>
              <th className="py-1">{t("field_product_id")}</th>
              <th className="py-1">{t("field_activity_id")}</th>
              <th className="py-1">{t("field_driver_id")}</th>
              <th className="py-1 text-right">
                {t("field_allocated_krw")}
              </th>
            </tr>
          </thead>
          <tbody>
            {allocation.breakdown.map((row, idx) => (
              <tr key={`${row.department_id}-${idx}`} className="border-b">
                <td className="py-1 font-mono">{row.department_id}</td>
                <td className="py-1 font-mono">{row.product_id}</td>
                <td className="py-1 font-mono">{row.activity_id}</td>
                <td className="py-1 font-mono">{row.driver_id}</td>
                <td className="py-1 text-right font-mono">
                  {formatDecimalAsKr(row.allocated_krw)}원
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Unused capacity sub-rows (PRD §A9). */}
      <div className="mb-3">
        <h3 className="mb-1 text-sm font-semibold text-gray-700">
          {t("section_unused_title")}{" "}
          <span className="text-xs text-gray-500">
            ({allocation.unused_capacity.rows.length} {t("unit_rows")})
          </span>
        </h3>
        {allocation.unused_capacity.rows.length === 0 ? (
          <p className="text-xs text-gray-500">{t("empty_unused")}</p>
        ) : (
          <table
            className="w-full border-collapse text-sm"
            data-testid="abc-dispatch-unused-table"
          >
            <thead>
              <tr className="border-b text-left text-xs text-gray-500">
                <th className="py-1">{t("field_department_id")}</th>
                <th className="py-1 text-right">{t("field_unused_hours")}</th>
                <th className="py-1 text-right">
                  {t("field_unused_cost_krw")}
                </th>
              </tr>
            </thead>
            <tbody>
              {allocation.unused_capacity.rows.map((row) => (
                <tr key={row.department_id} className="border-b">
                  <td className="py-1 font-mono">{row.department_id}</td>
                  <td className="py-1 text-right font-mono">
                    {row.unused_hours}h
                  </td>
                  <td className="py-1 text-right font-mono">
                    {formatDecimalAsKr(row.unused_cost_krw)}원
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <footer className="mt-3 border-t pt-2 text-xs text-gray-500">
        <div>
          <span>{t("field_snapshot_id")}: </span>
          <span
            className="font-mono"
            data-testid="abc-dispatch-abc-snapshot-id"
          >
            {outcome.snapshot_id}
          </span>
        </div>
        <div>
          <span>{t("field_result_hash")}: </span>
          <span
            className="font-mono"
            data-testid="abc-dispatch-abc-result-hash"
          >
            {outcome.result_hash}
          </span>
        </div>
        <div className="mt-1">
          <span className="text-gray-400">
            {t("field_v7_verdict_label")}: {formatV7VerdictLabel(v7)} (
            {v7.is_balanced ? "✓" : "✗"})
          </span>
        </div>
      </footer>
    </section>
  );
}
