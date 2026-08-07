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

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import {
  isCloseBlocked,
  type ClosingInvariant,
} from "@/lib/l2-input-inventory-ledger";
import type { ClosingGuardAuditEntry, ProductionConsumptionEventWire } from "@/lib/api-client";
import { cn } from "@/lib/utils";

import { M2ClosingGuardBanner } from "./ClosingGuardBanner";
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
  period_key,
  invariant,
  productNameLookup,
  onSubmit,
  defaultTab = "subub",
  activeTab,
  className,
  audit_trail,
  production_consumption_events,
  opening_inventory_locked = false,
  trace_id,
}: MonthlyInputTabsProps): React.ReactElement {
  const is_blocked = isCloseBlocked(invariant);

  return (
    <Tabs
      defaultValue={defaultTab}
      value={activeTab}
      className={cn("w-full", className)}
      data-testid="monthly-input-tabs"
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
        {opening_inventory_locked ? (
          <fieldset
            disabled
            data-testid="opening-inventory-locked-fieldset"
            data-trace-id={trace_id}
            className="flex flex-col gap-2 border-0 p-0 m-0"
          >
            <div className="text-sm text-muted-foreground">
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
            {period_key} 기초재고 입력 (Story 5.1 M14)
          </div>
        )}
      </TabsContent>
      <TabsContent value="subub">
        <div className="flex flex-col gap-3">
          <div className="text-sm text-muted-foreground">
            {period_key} 수불부 입력
          </div>
          {/* P3-3rd-sweep P6: production consumption events list */}
          {production_consumption_events && production_consumption_events.length > 0 && (
            <ul
              data-testid="production-consumption-list"
              className="text-sm space-y-1"
            >
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
          <MonthlyInputRowForm
            is_blocked={is_blocked}
            period_key={period_key}
            onSubmit={onSubmit}
          />
          {/* P3-3rd-sweep P6: closing-guard audit trail list */}
          {audit_trail && audit_trail.length > 0 && (
            <div data-testid="audit-trail-list" className="text-sm space-y-1">
              <h3 className="font-medium">마감 검증 이력</h3>
              <ul className="space-y-1">
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