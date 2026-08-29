// apps/web/components/performance/LatencyRegressionBanner.tsx —
// Phase 8 F24.4 latency regression PR banner (cj-style 95번째 wire).
//
// Renders an alert banner when actual p99 exceeds the baseline p99 by
// more than the configured threshold percentage. Returns null when the
// delta is at or below the threshold so the banner is not visible.

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  actual_p99_ms: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  baseline_p99_ms: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  threshold_pct: number;
  trace_id: string;
}

export default function LatencyRegressionBanner({
  actual_p99_ms,
  baseline_p99_ms,
  threshold_pct,
  trace_id,
}: Props) {
  if (baseline_p99_ms <= 0) {
    return null;
  }
  const delta_pct = ((actual_p99_ms - baseline_p99_ms) / baseline_p99_ms) * 100;
  if (delta_pct <= threshold_pct) {
    return null;
  }
  return (
    <div
      data-testid="regression-banner"
      role="alert"
      className="rounded-lg border border-amber-500 bg-amber-950/40 p-3 text-amber-100"
    >
      <p className="text-sm font-medium">
        p99 latency regression detected: actual={actual_p99_ms}ms,
        baseline={baseline_p99_ms}ms (+{delta_pct.toFixed(1)}% &gt; {threshold_pct}%).
      </p>
      <p className="mt-1 text-xs text-amber-200">trace_id: {trace_id}</p>
    </div>
  );
}