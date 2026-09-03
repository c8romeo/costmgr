/**
 * apps/web/components/m2-input/MonthlyInputTabsInteractive.tsx — cj-252
 *
 * Client wrapper that owns the `onSubmit` + `onClosingPeriodConfirm`
 * handlers previously inlined in the RSC server page. The server page
 * cannot pass function props across the RSC boundary — Next.js 15
 * hard-rejects with `Event handlers cannot be passed to Client Component
 * props` at SSR time. Wrapping in a `'use client'` boundary lets the
 * server pass data props (serializable) and the client own the handlers.
 *
 * Replaces the previous pattern where
 * `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx`
 * defined arrow functions inline and passed them to `<MonthlyInputTabs>`.
 * That pattern yielded 16+ e2e test failures spanning
 * closing-guard / m11-reversal / m12-* / onboarding / monthly-closing-report
 * specs at run 33507513957 (cj-251 live CI verification).
 *
 * Replaces server `revalidatePath()` (RSC-only) with client
 * `router.refresh()` (RSC-aware) — `revalidatePath` cannot cross the RSC
 * boundary either, so the prior inline handler was doubly broken: it
 * would have crashed at the boundary even if functions were serializable.
 */

"use client";

import { useRouter } from "next/navigation";

import { MonthlyInputTabs, type MonthlyInputTabsProps } from "./MonthlyInputTabs";

/**
 * cj-252 — RSC-safe props subset. We forward the same data props the
 * page.tsx used to thread through `<MonthlyInputTabs>` directly. The
 * `onSubmit` / `onClosingPeriodConfirm` handlers are owned internally
 * by this wrapper (cannot cross the RSC boundary as function props), so
 * they are omitted from the public props surface.
 */
export interface MonthlyInputTabsInteractiveProps
  extends Pick<
    MonthlyInputTabsProps,
    | "period_key"
    | "invariant"
    | "audit_trail"
    | "production_consumption_events"
    | "opening_inventory_locked"
    | "trace_id"
    | "productNameLookup"
    | "closing_period_state"
    | "closing_period_capability_granted"
    | "closing_period_finalized_at"
  > {
  /**
   * Supabase sb-access-token cookie value, read server-side from
   * `cookies()`. Passed through so the client can attach the
   * `Authorization: Bearer <token>` header to the closing-period
   * confirm POST. NOTE: This token is serialized into the client bundle
   * — pre-existing security characteristic (the prior inline handler
   * captured the same variable in its closure), not introduced by this
   * wrapper.
   */
  accessToken: string | undefined;
}

/**
 * MonthlyInputTabsInteractive — RSC-safe wrapper that owns
 * `onSubmit` (no-op for CLOSING_OK [수불부] save path) +
 * `onClosingPeriodConfirm` (POST /api/v1/inventory/closing-period/confirm
 * + router.refresh() to re-fetch the RSC tree).
 */
export function MonthlyInputTabsInteractive(
  props: MonthlyInputTabsInteractiveProps,
): React.ReactElement {
  const router = useRouter();

  const onSubmit = async (key: string): Promise<void> => {
    // P3-3rd-sweep P27 — no-op save handler for [수불부] tab in CLOSING_OK
    // path. Real save flow wires through useSaveRow hook in follow-up
    // Story (currently saves via api-client directly).
    await Promise.resolve(key);
  };

  const onClosingPeriodConfirm = async (
    // eslint-disable-next-line camelcase
    period_key: string,
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
  ): Promise<number> => {
    // Story 6.1 T8.6 — POST /api/v1/inventory/closing-period/confirm.
    // Best-effort: throw on 409/403 so the Dialog surfaces toast.error.
    const res = await fetch("/api/v1/inventory/closing-period/confirm", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(props.accessToken
          ? { Authorization: `Bearer ${props.accessToken}` }
          : {}),
      },
      body: JSON.stringify({
        // eslint-disable-next-line camelcase
        period_key,
      }),
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as {
        error?: { code?: string };
      };
      const err = new Error("ClosingPeriodConfirmError") as Error & {
        response?: { data?: { error?: { code?: string } } };
      };
      err.response = { data: body };
      throw err;
    }
    const data = (await res.json()) as {
      // eslint-disable-next-line @typescript-eslint/no-restricted-types
      closing_snapshot_count?: number;
    };
    // CR 6-1 R4 patch D12 (cj-252 RSC-safe variant): client uses
    // `router.refresh()` instead of server `revalidatePath()`. The
    // latter is RSC-only and cannot be invoked from a client runtime
    // after a successful POST. `router.refresh()` re-fetches the RSC
    // tree from the server, picking up the updated monthly_input_periods
    // row + closing_period_state + audit trail on next render.
    router.refresh();
    return data.closing_snapshot_count ?? 0;
  };

  return (
    <MonthlyInputTabs
      period_key={props.period_key}
      invariant={props.invariant}
      audit_trail={props.audit_trail}
      production_consumption_events={props.production_consumption_events}
      opening_inventory_locked={props.opening_inventory_locked}
      trace_id={props.trace_id}
      productNameLookup={props.productNameLookup}
      closing_period_state={props.closing_period_state}
      closing_period_capability_granted={
        props.closing_period_capability_granted
      }
      closing_period_finalized_at={props.closing_period_finalized_at}
      onSubmit={onSubmit}
      onClosingPeriodConfirm={onClosingPeriodConfirm}
    />
  );
}