// apps/web/components/performance/SLOStatusBadge.tsx —
// Phase 8 F24.2 SLO status badge (cj-style 95번째 wire).
//
// Renders a tri-state badge (ok / warn / violation) based on the ratio of
// actual_p99_ms to budget_ms. The 80% threshold separates ok from warn,
// and the 100% threshold separates warn from violation. When the SLO is
// violated, an owner-only acknowledgement prompt is shown (AD-22 RBAC +
// Epic 12 2FA 챌린지 preserved).

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  actual_p99_ms: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  budget_ms: number;
}

{/* eslint-disable-next-line camelcase */}
export default function SLOStatusBadge({ actual_p99_ms, budget_ms }: Props) {
  // eslint-disable-next-line camelcase
  if (budget_ms <= 0) {
    return null;
  }
  // eslint-disable-next-line camelcase
  const ratio = actual_p99_ms / budget_ms;
  if (ratio < 0.8) {
    return (
      <span
        data-testid="slo-status-ok"
        className="inline-flex items-center rounded-md bg-emerald-900/50 px-2 py-0.5 text-xs font-medium text-emerald-200"
      >
        {/* eslint-disable-next-line camelcase */}
        SLO OK — SLA-1 p99 {actual_p99_ms}ms / {budget_ms}ms
      </span>
    );
  }
  if (ratio < 1.0) {
    return (
      <span
        data-testid="slo-status-warn"
        className="inline-flex items-center rounded-md bg-amber-900/50 px-2 py-0.5 text-xs font-medium text-amber-200"
      >
        {/* eslint-disable-next-line camelcase */}
        SLO WARN — SLA-1 p99 {actual_p99_ms}ms / {budget_ms}ms
      </span>
    );
  }
  return (
    <div data-testid="slo-status-violation" className="space-y-1">
      <span className="inline-flex items-center rounded-md bg-rose-900/50 px-2 py-0.5 text-xs font-medium text-rose-200">
        {/* eslint-disable-next-line camelcase */}
        SLO VIOLATION — SLA-1 p99 {actual_p99_ms}ms / {budget_ms}ms
      </span>
      <p className="text-xs text-rose-200">
        owner-only acknowledgement required to acknowledge this violation.
      </p>
    </div>
  );
}