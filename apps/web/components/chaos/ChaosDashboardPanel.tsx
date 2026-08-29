"use client";

/**
 * apps/web/components/chaos/ChaosDashboardPanel.tsx —
 * Phase 9 (cj-style 99번째 wire) — Client orchestrator for the chaos
 * engineering admin dashboard.
 *
 * 4 components in one panel (PRD §F25.1 + §F25.3 + §F25.6):
 *   - ChaosExperimentList — recent experiments with status
 *   - ChaosExperimentTriggerButton — owner-only (AD-22 + Epic 12 2FA 챌린지)
 *   - ChaosGameDayCalendar — quarterly schedule
 *   - ChaosRollbackLog — auto-rollback history
 *
 * All access is gated through the `require_chaos_engineering` capability
 * (CR 12-5 D-GATE-01 inversion) + owner-only RBAC at the backend
 * (AD-22 verbatim for trigger + manual abort + rollback strategy).
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  listChaosExperiments,
  listChaosRollbacks,
  triggerChaosExperiment,
  ChaosExperimentApiError,
  type ChaosExperiment,
  type ChaosRollback,
} from "@/lib/chaos/chaos-client";

interface Props {
  accessToken: string;
  locale: string;
}

export function ChaosDashboardPanel({ accessToken, locale }: Props) {
  const router = useRouter();
  const [experiments, setExperiments] = useState<ChaosExperiment[]>([]);
  const [rollbacks, setRollbacks] = useState<ChaosRollback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const exp = await listChaosExperiments(accessToken);
        const rb = await listChaosRollbacks(accessToken);
        if (!cancelled) {
          setExperiments(exp.experiments);
          setRollbacks(rb.rollbacks);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "load_failed");
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleTrigger() {
    setTriggering(true);
    try {
      await triggerChaosExperiment(accessToken, {
        fault_type: "latency",
        blast_radius: "single_request",
        region: "seoul",
        duration_seconds: 60,
        intensity: "low",
        dry_run: true,
      });
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ChaosExperimentApiError
          ? err.message
          : "trigger_failed",
      );
    } finally {
      setTriggering(false);
    }
  }

  return (
    <section data-testid="chaos-dashboard-panel" role="region" aria-label="chaos">
      <header>
        <h1>Chaos Engineering 대시보드</h1>
        <p>테넌트의 chaos 실험 + game day + auto-rollback 상태를 확인합니다.</p>
      </header>

      {loading && <div role="status">데이터를 불러오는 중…</div>}
      {error && (
        <div role="alert" data-state="error">
          {error}
        </div>
      )}

      <ChaosExperimentList experiments={experiments} />
      <ChaosExperimentTriggerButton
        onTrigger={handleTrigger}
        disabled={triggering}
      />
      <ChaosGameDayCalendar />
      <ChaosRollbackLog rollbacks={rollbacks} />

      <input type="hidden" data-locale={locale} readOnly />
    </section>
  );
}

// ── 4 sub-components (Phase 9 T7) ──────────────────────────────

function ChaosExperimentList({ experiments }: { experiments: ChaosExperiment[] }) {
  return (
    <section data-component="chaos-experiment-list" aria-label="experiments">
      <h2>최근 chaos 실험</h2>
      {experiments.length === 0 ? (
        <p>아직 chaos 실험이 없습니다.</p>
      ) : (
        <ul>
          {experiments.map((e) => (
            <li key={e.experiment_id} data-status={e.status}>
              <strong>{e.experiment_name}</strong>
              <span> · fault={e.fault_type}</span>
              <span> · blast={e.blast_radius}</span>
              <span> · dry_run={String(e.dry_run)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ChaosExperimentTriggerButton({
  onTrigger,
  disabled,
}: {
  onTrigger: () => void;
  disabled: boolean;
}) {
  return (
    <section data-component="chaos-experiment-trigger-button" aria-label="trigger">
      <h2>chaos 실험 실행 (dry-run)</h2>
      <button
        type="button"
        onClick={onTrigger}
        disabled={disabled}
        aria-label="chaos-experiment-trigger-button"
      >
        {disabled ? "실행 중..." : "chaos 실험 실행"}
      </button>
      <p>chaos 실험 실행은 owner 권한이 필요합니다 (2FA 챌린지 포함).</p>
    </section>
  );
}

function ChaosGameDayCalendar() {
  return (
    <section data-component="chaos-game-day-calendar" aria-label="game-day">
      <h2>분기 game day 일정</h2>
      <ul>
        <li data-quarter="Q1">Q1: 2026-03-01 03:00 KST</li>
        <li data-quarter="Q2">Q2: 2026-06-07 03:00 KST</li>
        <li data-quarter="Q3">Q3: 2026-09-06 03:00 KST</li>
        <li data-quarter="Q4">Q4: 2026-12-06 03:00 KST</li>
      </ul>
    </section>
  );
}

function ChaosRollbackLog({ rollbacks }: { rollbacks: ChaosRollback[] }) {
  return (
    <section data-component="chaos-rollback-log" aria-label="rollback-log">
      <h2>auto-rollback 이력</h2>
      {rollbacks.length === 0 ? (
        <p>rollback 이력이 없습니다.</p>
      ) : (
        <ol>
          {rollbacks.map((r) => (
            <li key={r.rollback_id} data-strategy={r.strategy}>
              <strong>{r.experiment_id}</strong>
              <span> · strategy={r.strategy}</span>
              <span> · reason={r.reason}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
