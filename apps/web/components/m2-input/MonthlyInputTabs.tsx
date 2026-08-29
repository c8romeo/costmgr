/**
 * apps/web/components/m2-input/MonthlyInputTabs.tsx — Story 5.3 T9 + P19
 *
 * shadcn/ui Tabs container for the [기초재고] / [수불부] / [마감] tab
 * navigation. Composes the closing-guard banner + form + gate so the
 * [마감] tab shows the red banner and locks while invariant is violated.
 *
 * Re-uses existing `apps/web/components/ui/tabs.tsx` shadcn primitive.
 */

"use client";

import * as React from "react";

import { ReversalRequestButton } from "@/components/m4-inventory/ReversalRequestButton";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import type { ClosingGuardAuditEntry, ProductionConsumptionEventWire } from "@/lib/api-client";
import {
  isCloseBlocked,
  type ClosingInvariant,
} from "@/lib/l2-input-inventory-ledger";
import { cn } from "@/lib/utils";

import { M2ClosingGuardBanner } from "./ClosingGuardBanner";
import { ClosingPeriodConfirmDialog } from "./ClosingPeriodConfirmDialog";
import { ClosingPeriodConfirmationPanel } from "./ClosingPeriodConfirmationPanel";
import { MonthlyClosingReportPanel } from "./MonthlyClosingReportPanel";
import { MonthlyInputRowForm } from "./MonthlyInputRowForm";

export type MonthlyInputTabId = "opening" | "subub" | "close";

export interface MonthlyInputTabsProps {
  /** Period key (e.g. "2026-07"). */
  period_key: string;
  /** Closing invariant — drives banner visibility + gate. */
  invariant: ClosingInvariant;
  /** Optional product id → human-readable name lookup. */
  productNameLookup?: Record<string, string>;
  /** Form submit handler passed to the [마감] tab form. */
  onSubmit?: (period_key: string) => Promise<void> | void;
  /** Initial active tab (defaults to "subub"). */
  defaultTab?: MonthlyInputTabId;
  /** Optional controlled active tab. */
  activeTab?: MonthlyInputTabId;
  /** Optional className override. */
  className?: string;
  /**
   * P3-3rd-sweep P6: closing-guard audit trail (last 10 entries,
   * closing_guard_violated / closing_guard_passed / v3_closing_invariant_verified).
   * Rendered in [마감] tab below the form.
   */
  audit_trail?: ClosingGuardAuditEntry[];
  /**
   * P3-3rd-sweep P6: production consumption events (BOM-aware reconciliation
   * ledger events for this period). Rendered in [수불부] tab.
   */
  production_consumption_events?: ProductionConsumptionEventWire[];
  /**
   * P3-3rd-sweep P3: opening inventory locked flag (Story 5.1 hook 2 +
   * 5-3 manual edit reject UI). When true, [기초재고] tab renders disabled
   * fieldset + helper text "기초재고 잠김 — 자동 이월 체인 활성. 수동 수정 불가".
   */
  opening_inventory_locked?: boolean;
  /** P3-3rd-sweep P25: trace ID for audit correlation. */
  trace_id?: string;
  /**
   * Story 6.1 T8.5 — closing period state for the [마감] tab panel.
   * Additive on top of ClosingGuardBanner (5-3 wire).
   */
  closing_period_state?: import("@/lib/closing-period").ClosingPeriodState;
  /**
   * Story 6.1 T8.5 — MONTHLY_CLOSING_REPORT capability gate (A10).
   * When false, ClosingPeriodConfirmationPanel is hidden entirely.
   */
  closing_period_capability_granted?: boolean;
  /**
   * Story 6.1 T8.5 — monthly_input_periods.finalized_at (ISO-8601 UTC)
   * surfaced for ALREADY_CLOSED display.
   */
  closing_period_finalized_at?: string | null;
  /**
   * Story 6.1 T8.5 — handler fired when [마감 확정] is clicked.
   * Wired up by the parent page to open ClosingPeriodConfirmDialog.
   */
  onClosingPeriodConfirmClick?: (
    state: import("@/lib/closing-period").ClosingPeriodState,
  ) => void;
  /**
   * Story 6.1 T8.5 — POST handler for closing-period confirmation.
   * Returns the closing_snapshot_count written; throws on 409/403.
   */
  onClosingPeriodConfirm?: (
    period_key: string,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  ) => Promise<number>;
  /**
   * Story 6.2 T7.6 — Monthly closing report aggregate (read-only join).
   * When provided, MonthlyClosingReportPanel is rendered below the
   * ClosingPeriodConfirmationPanel in the [마감] tab.
   */
  monthly_closing_report?: import("@/lib/monthly-closing-report").MonthlyClosingReportAggregate;
  /**
   * Story 6.2 T7.6 — V4 verdict for monthly closing report (6-1 carry-over + 6-2 extension).
   */
  monthly_closing_report_v4_verdict?: import("@/lib/monthly-closing-report").MonthlyClosingReportV4Verdict | null;
  /**
   * Story 6.2 T7.6 — Audit trail entries (last 10 — CR 1.1 observability).
   */
  monthly_closing_report_audit_trail?: Array<{
    id: string;
    action: string;
    actor_id: string | null;
    created_at: string;
  }>;
  /**
   * Story 11.1 T10.7 — ReversalRequestTrigger composite state from
   * `MonthlyInputStateResponse`. When provided, ReversalRequestButton is
   * rendered as the 3rd component in the [마감] tab vertical stack
   * (ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel +
   * ReversalRequestButton). Capability gate handled internally by the
   * button (returns null when capability_granted=false).
   */
  reversal_request_trigger?: import("@/lib/closing-period").ReversalRequestTrigger;
  /**
   * Story 11.1 T10.7 — monthly_input_periods.status mirror. Used by
   * ReversalRequestButton to gate the disabled state (locked → reject).
   */
  reversal_request_period_status?: import("@/lib/m11-reversal").PeriodStatus;
  /**
   * Story 11.1 T10.7 — POST handler for reversal-request confirmation.
   * Returns correction_group_id; throws on 422/403/404.
   */
  onReversalRequestSubmit?: (
    payload: import("@/lib/m11-reversal").ReversalRequestPayload,
  ) => Promise<import("@/lib/m11-reversal").ReversalCreateResponse>;
}

/**
 * MonthlyInputTabs — Tabbed container for [기초재고] / [수불부] / [마감].
 *
 * The [마감] tab wires the closing-guard banner + form + fieldset gate.
 * The banner is visible iff invariant.code = NEGATIVE_CLOSING, and the
 * form is blocked via <fieldset disabled> so keyboard + programmatic
 * submission bypass correctly (P22 patch).
 */
export function MonthlyInputTabs({
  // eslint-disable-next-line camelcase
  period_key,
  invariant,
  productNameLookup,
  onSubmit,
  defaultTab = "subub",
  activeTab,
  className,
  // eslint-disable-next-line camelcase
  audit_trail,
  // eslint-disable-next-line camelcase
  production_consumption_events,
  // eslint-disable-next-line camelcase
  opening_inventory_locked = false,
  // eslint-disable-next-line camelcase
  trace_id,
  // eslint-disable-next-line camelcase
  closing_period_state,
  // eslint-disable-next-line camelcase
  closing_period_capability_granted = false,
  // eslint-disable-next-line camelcase
  closing_period_finalized_at,
  onClosingPeriodConfirmClick,
  onClosingPeriodConfirm,
  // eslint-disable-next-line camelcase
  monthly_closing_report,
  // eslint-disable-next-line camelcase
  monthly_closing_report_v4_verdict,
  // eslint-disable-next-line camelcase
  monthly_closing_report_audit_trail,
  // eslint-disable-next-line camelcase
  reversal_request_trigger,
  // eslint-disable-next-line camelcase
  reversal_request_period_status = "open",
  onReversalRequestSubmit,
}: MonthlyInputTabsProps): React.ReactElement {
  // eslint-disable-next-line camelcase
  const is_blocked = isCloseBlocked(invariant);

  // Story 6.1 T8.5 — internal dialog state. Opened when panel's
  // onConfirmClick fires; rendered below.
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const handleConfirmClick = React.useCallback(
    (s: import("@/lib/closing-period").ClosingPeriodState) => {
      onClosingPeriodConfirmClick?.(s);
      setDialogOpen(true);
    },
    [onClosingPeriodConfirmClick],
  );

  return (
    <Tabs
      defaultValue={defaultTab}
      value={activeTab}
      className={cn("w-full", className)}
      data-testid="monthly-input-tabs"
      // eslint-disable-next-line camelcase
      data-period-key={period_key}
    >
      <TabsList>
        <TabsTrigger value="opening" data-testid="tab-opening">
          기초재고
        </TabsTrigger>
        <TabsTrigger value="subub" data-testid="tab-subub">
          수불부
        </TabsTrigger>
        <TabsTrigger value="close" data-testid="tab-close">
          마감
        </TabsTrigger>
      </TabsList>
      <TabsContent value="opening">
        {/* P3-3rd-sweep P3: manual edit reject UI when opening locked */}
        // eslint-disable-next-line camelcase
        {opening_inventory_locked ? (
          <fieldset
            disabled
            data-testid="opening-inventory-locked-fieldset"
            // eslint-disable-next-line camelcase
            data-trace-id={trace_id}
            className="flex flex-col gap-2 border-0 p-0 m-0"
          >
            <div className="text-sm text-muted-foreground">
              // eslint-disable-next-line camelcase
              {period_key} 기초재고 입력 (Story 5.1 M14)
            </div>
            <p
              data-testid="opening-inventory-locked-helper"
              className="text-sm text-amber-700"
            >
              기초재고 잠김 — 자동 이월 체인 활성. 수동 수정 불가
            </p>
          </fieldset>
        ) : (
          <div className="text-sm text-muted-foreground">
            // eslint-disable-next-line camelcase
            {period_key} 기초재고 입력 (Story 5.1 M14)
          </div>
        )}
      </TabsContent>
      <TabsContent value="subub">
        <div className="flex flex-col gap-3">
          <div className="text-sm text-muted-foreground">
            // eslint-disable-next-line camelcase
            {period_key} 수불부 입력
          </div>
          {/* P3-3rd-sweep P6: production consumption events list */}
          // eslint-disable-next-line camelcase
          {production_consumption_events && production_consumption_events.length > 0 && (
            <ul
              data-testid="production-consumption-list"
              className="text-sm space-y-1"
            >
              // eslint-disable-next-line camelcase
              {production_consumption_events.map((event) => (
                <li
                  key={`${event.product_id}-${event.event_type}`}
                  data-testid={`event-${event.product_id}`}
                >
                  {event.event_type}: {event.product_id.slice(0, 8)} ({event.qty ?? "-"})
                </li>
              ))}
            </ul>
          )}
        </div>
      </TabsContent>
      <TabsContent value="close" data-testid="tab-close-content">
        <div className="flex flex-col gap-3">
          <M2ClosingGuardBanner
            invariant={invariant}
            productNameLookup={productNameLookup}
          />
          {/* Story 6.1 T8.5 — ClosingPeriodConfirmationPanel additive on top
              of ClosingGuardBanner (5-3 wire). Same vertical stack; only
              visible when MONTHLY_CLOSING_REPORT capability is granted (A10). */}
          // eslint-disable-next-line camelcase
          {closing_period_state && (
            <ClosingPeriodConfirmationPanel
              // eslint-disable-next-line camelcase
              state={closing_period_state}
              // eslint-disable-next-line camelcase
              finalized_at={closing_period_finalized_at}
              // eslint-disable-next-line camelcase
              capability_granted={closing_period_capability_granted}
              onConfirmClick={handleConfirmClick}
            />
          )}
          {/* Story 6.1 T8.5 — Dialog open when panel button fires. */}
          // eslint-disable-next-line camelcase
          {closing_period_state && onClosingPeriodConfirm && (
            <ClosingPeriodConfirmDialog
              open={dialogOpen}
              onOpenChange={setDialogOpen}
              // eslint-disable-next-line camelcase
              state={closing_period_state}
              // eslint-disable-next-line camelcase
              period_key={period_key}
              onConfirm={onClosingPeriodConfirm}
            />
          )}
          {/* Story 6.2 T7.6 — MonthlyClosingReportPanel wire below
              ClosingPeriodConfirmationPanel. Renders 4 KPI cards + table +
              V4 verdict envelope + audit-trail. Hidden when
              monthly_closing_report_capability_granted=false. */}
          // eslint-disable-next-line camelcase
          {monthly_closing_report && (
            <MonthlyClosingReportPanel
              // eslint-disable-next-line camelcase
              aggregate={monthly_closing_report}
              // eslint-disable-next-line camelcase
              v4_verdict={monthly_closing_report_v4_verdict ?? null}
              // eslint-disable-next-line camelcase
              audit_trail={monthly_closing_report_audit_trail ?? []}
              // eslint-disable-next-line camelcase
              capability_granted={closing_period_capability_granted}
            />
          )}
          {/* Story 11.1 T10.7 — ReversalRequestButton wire as the 3rd
              component in the [마감] tab vertical stack. Capability gate
              handled internally (returns null when capability_granted=false).
              Hidden when reversal_request_trigger is not provided (page-level
              MonthlyInputStateResponse determines trigger shape). */}
          // eslint-disable-next-line camelcase
          {reversal_request_trigger && (
            <ReversalRequestButton
              // eslint-disable-next-line camelcase
              target_event_id={reversal_request_trigger.target_event_id}
              // eslint-disable-next-line camelcase
              period_key={period_key}
              // eslint-disable-next-line camelcase
              period_status={reversal_request_period_status}
              // eslint-disable-next-line camelcase
              capability_granted={reversal_request_trigger.capability_granted}
              onSubmit={async (payload) => {
                if (!onReversalRequestSubmit) {
                  return {
                    correction_group_id: "",
                    negating_event_id: "",
                    corrected_event_id: null,
                    target_event_id: payload.target_event_id,
                    reversal_history: [],
                    trace_id: "",
                    cache_invalidation_receipt: {},
                  };
                }
                const response = await onReversalRequestSubmit(payload);
                return response;
              }}
            />
          )}
          <MonthlyInputRowForm
            // eslint-disable-next-line camelcase
            is_blocked={is_blocked}
            // eslint-disable-next-line camelcase
            period_key={period_key}
            onSubmit={onSubmit}
          />
          {/* P3-3rd-sweep P6: closing-guard audit trail list */}
          // eslint-disable-next-line camelcase
          {audit_trail && audit_trail.length > 0 && (
            <div data-testid="audit-trail-list" className="text-sm space-y-1">
              <h3 className="font-medium">마감 검증 이력</h3>
              <ul className="space-y-1">
                // eslint-disable-next-line camelcase
                {audit_trail.map((entry) => (
                  <li
                    key={entry.id}
                    data-testid={`audit-entry-${entry.id}`}
                    className="flex gap-2"
                  >
                    <span>{entry.action}</span>
                    <span className="text-muted-foreground">{entry.created_at}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </TabsContent>
    </Tabs>
  );
}