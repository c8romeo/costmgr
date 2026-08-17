"use client";

/**
 * apps/web/components/m9-abc/AbcDispatchDecisionBadge.tsx — Story 9.3
 *
 * Dispatch decision badge — surfaces M3 orchestrator's engine_type tag
 * decision (PRD §F9.3 + A29 forward-lock dual-route + AD-19).
 *
 * Per AC #1 (Story 9.3) — POST /api/v1/calc returns discriminated union
 * `CalcOutcome | CalcOutcomeABC`. The orchestrator's
 * `_resolve_engine_type(industry)` returns:
 *   - "abc" if tenant.industry == "service"
 *   - "trad" otherwise
 *
 * Badge shows:
 *   - engine_type: "trad" → TRAD path (gray badge, no ABC computation)
 *   - engine_type: "abc"  → ABC path (blue badge, full dual-route wire)
 *
 * Rendered by AbcDispatchResultCard.
 */

import { useTranslations } from "next-intl";

import type { EngineTypeTag } from "@/lib/m9-abc-dispatch";

interface AbcDispatchDecisionBadgeProps {
  engineType: EngineTypeTag;
  tenantIndustry: string;
  reason: string;
}

export function AbcDispatchDecisionBadge({
  engineType,
  tenantIndustry,
  reason,
}: AbcDispatchDecisionBadgeProps): React.ReactElement {
  const t = useTranslations("abc_calculation");

  const isAbc = engineType === "abc";
  const label = isAbc ? t("dispatch_decision_abc") : t("dispatch_decision_trad");
  const ariaLabel = isAbc
    ? t("dispatch_decision_abc_aria")
    : t("dispatch_decision_trad_aria");

  return (
    <div
      className={[
        "inline-flex items-center gap-2 rounded px-3 py-1 text-xs font-medium",
        isAbc
          ? "bg-blue-100 text-blue-800 border border-blue-300"
          : "bg-gray-100 text-gray-700 border border-gray-300",
      ].join(" ")}
      data-testid="abc-dispatch-decision-badge"
      data-engine-type={engineType}
      data-tenant-industry={tenantIndustry}
      role="status"
      aria-label={ariaLabel}
    >
      <span
        className={[
          "h-2 w-2 rounded-full",
          isAbc ? "bg-blue-600" : "bg-gray-500",
        ].join(" ")}
        aria-hidden="true"
      />
      <span className="font-mono uppercase tracking-wide">{label}</span>
      <span className="text-xs opacity-70">· {reason}</span>
    </div>
  );
}
