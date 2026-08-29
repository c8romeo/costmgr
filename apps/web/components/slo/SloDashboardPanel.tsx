"use client";

/**
 * apps/web/components/slo/SloDashboardPanel.tsx —
 * Phase 10 T7 (cj-style 103번째 wire) — Client orchestrator for the
 * SLO Engineering / Error Budget Management admin dashboard.
 *
 * 4 panels in one dashboard (PRD §F26.1 + §F26.3 + §F26.4 + §F26.5):
 *   - SloDefinitionList — SLO definitions with state
 *   - ErrorBudgetTracker — burn-rate + remaining minutes
 *   - SloGovernanceReviewList — pending reviews
 *   - SloFreezeButton — owner-only (AD-22 + Epic 12 2FA 챌린지)
 *
 * All access is gated through the `require_slo_engineering` capability
 * (CR 12-5 D-GATE-01 inversion) + owner-only RBAC at the backend
 * (AD-22 verbatim for create/update/delete + freeze + unfreeze +
 * override + auto-rollback trigger).
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  approveGovernanceReview,
  freezeErrorBudget,
  listErrorBudgets,
  listGovernanceReviews,
  listSloDefinitions,
  type ErrorBudget,
  type GovernanceReview,
  type SloDefinition,
} from "@/lib/slo/slo-client";

interface Props {
  accessToken: string;
  locale: string;
}

export function SloDashboardPanel({ accessToken, locale }: Props) {
  const router = useRouter();
  const [definitions, setDefinitions] = useState<SloDefinition[]>([]);
  const [budgets, setBudgets] = useState<ErrorBudget[]>([]);
  const [reviews, setReviews] = useState<GovernanceReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [freezeReason, setFreezeReason] = useState("");
  const [selectedSloId, setSelectedSloId] = useState<string | null>(null);
  const [freezing, setFreezing] = useState(false);
  const [approving, setApproving] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const defs = await listSloDefinitions(accessToken);
        const buds = await listErrorBudgets(accessToken);
        const revs = await listGovernanceReviews(accessToken);
        if (!cancelled) {
          setDefinitions(defs.items);
          setBudgets(buds.budgets);
          setReviews(revs.reviews);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load SLO data");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleFreeze() {
    if (!selectedSloId) return;
    setFreezing(true);
    try {
      await freezeErrorBudget(accessToken, selectedSloId, freezeReason);
      setFreezeReason("");
      // Refresh
      const buds = await listErrorBudgets(accessToken);
      setBudgets(buds.budgets);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to freeze");
    } finally {
      setFreezing(false);
    }
  }

  async function handleApprove(reviewId: string, notes: string) {
    setApproving(reviewId);
    try {
      await approveGovernanceReview(accessToken, reviewId, notes);
      const revs = await listGovernanceReviews(accessToken);
      setReviews(revs.reviews);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve");
    } finally {
      setApproving(null);
    }
  }

  if (loading) {
    return <div data-testid="slo-dashboard-loading">Loading SLO dashboard…</div>;
  }
  if (error) {
    return (
      <div data-testid="slo-dashboard-error" role="alert">
        {error}
      </div>
    );
  }

  return (
    <div data-testid="slo-dashboard">
      <h1>SLO Engineering / Error Budget Management</h1>

      {/* Panel 1: SloDefinitionList */}
      <section data-testid="slo-definition-list">
        <h2>SLO Definitions ({definitions.length})</h2>
        <ul>
          {definitions.map((def) => (
            <li
              key={def.slo_id}
              data-testid="slo-definition-item"
              data-slo-id={def.slo_id}
            >
              {def.slo_id} — service={def.service} objective={def.objective}% window={def.window} state={def.state}
            </li>
          ))}
        </ul>
      </section>

      {/* Panel 2: ErrorBudgetTracker */}
      <section data-testid="error-budget-tracker">
        <h2>Error Budgets ({budgets.length})</h2>
        <ul>
          {budgets.map((bud) => (
            <li
              key={bud.slo_id}
              data-testid="error-budget-item"
              data-slo-id={bud.slo_id}
              data-freeze={bud.freeze_triggered}
            >
              {bud.slo_id} — remaining={bud.budget_remaining_minutes.toFixed(1)}min freeze={String(bud.freeze_triggered)}
            </li>
          ))}
        </ul>
      </section>

      {/* Panel 3: SloGovernanceReviewList */}
      <section data-testid="slo-governance-review-list">
        <h2>Governance Reviews ({reviews.length})</h2>
        <ul>
          {reviews.map((rev) => (
            <li
              key={rev.review_id}
              data-testid="slo-governance-review-item"
              data-review-id={rev.review_id}
              data-status={rev.review_status}
            >
              {rev.review_id} — slo={rev.slo_id} status={rev.review_status}
              {rev.review_status === "pending" && (
                <button
                  type="button"
                  onClick={() => handleApprove(rev.review_id, "Approved via dashboard")}
                  disabled={approving === rev.review_id}
                  data-testid="slo-governance-approve-button"
                >
                  Approve
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* Panel 4: SloFreezeButton (owner-only AD-22 + Epic 12 2FA 챌린지) */}
      <section data-testid="slo-freeze-section">
        <h2>Freeze Error Budget</h2>
        <select
          value={selectedSloId ?? ""}
          onChange={(e) => setSelectedSloId(e.target.value || null)}
          data-testid="slo-freeze-select"
        >
          <option value="">Select SLO…</option>
          {budgets.map((bud) => (
            <option key={bud.slo_id} value={bud.slo_id}>
              {bud.slo_id}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Reason"
          value={freezeReason}
          onChange={(e) => setFreezeReason(e.target.value)}
          data-testid="slo-freeze-reason"
        />
        <button
          type="button"
          onClick={handleFreeze}
          disabled={!selectedSloId || freezing}
          data-testid="slo-freeze-button"
        >
          {freezing ? "Freezing…" : "Freeze"}
        </button>
      </section>
    </div>
  );
}
