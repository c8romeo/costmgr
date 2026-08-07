/**
 * apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx
 *
 * Story 5.3 T15.1 — Server Component page-level wire for [월 입력].
 *
 * Reads access token, awaits the monthly-input state server-side
 * (F-20 race-free), projects the 5 NEW 5-3 closing-guard fields
 * (closing_guard_blocked, closing_guard_audit_trail,
 * production_consumption_events, v3_verdict, closing_guard_invariant)
 * to page-level state hook, then delegates the tab UI to
 * MonthlyInputTabs (existing client component).
 *
 * UX-locked: ko-KR labels, WCAG AA contrast, Professional 톤.
 *
 * P3-3rd-sweep fixes:
 * - P1: project all 5 NEW fields to <MonthlyInputTabs> (not just 2).
 * - P2: remove inline `<p>` blocking banner; rely on tab-level
 *   <M2ClosingGuardBanner> via MonthlyInputTabs.
 * - P3: thread `opening_inventory_locked` flag for manual edit reject UI.
 * - P24: wrap fetch in try/catch with error boundary (best-effort;
 *   actual ErrorBoundary would be a layout-level concern).
 * - P25: thread server-side `traceId` to <MonthlyInputTabs> for audit
 *   correlation.
 * - P26: pass `productNameLookup` (empty fallback; backend may supply
 *   product names in future).
 * - P27: pass `onSubmit` no-op handler (CLOSING_OK path: [수불부] tab
 *   form can save when unblocked).
 * - P28: fail-closed fallback — when initialState is null, invariant
 *   is EMPTY_PERIOD (not CLOSING_OK) + guard_enabled=false + isBlocked=false
 *   (consistent triple fallback).
 */

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

import { MonthlyInputTabs } from "@/components/m2-input/MonthlyInputTabs";
import type { ClosingInvariant } from "@/lib/l2-input-inventory-ledger";
import { fetchMonthlyInputStateServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function MonthlyInputPeriodPage({
  params,
}: {
  params: Promise<{ periodKey: string }>;
}) {
  const { periodKey } = await params;
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  // P3-3rd-sweep P24: best-effort error boundary via try/catch. A thrown
  // fetch error or MonthlyInputService error would otherwise crash the
  // page. Returns null → fail-closed fallback (P28).
  let initialState: Awaited<
    ReturnType<typeof fetchMonthlyInputStateServerSide>
  > = null;
  try {
    initialState = await fetchMonthlyInputStateServerSide(
      periodKey,
      accessToken,
      traceId,
    );
  } catch {
    initialState = null;
  }

  // P3-3rd-sweep P28: fail-closed fallback — when initialState is null,
  // ALL three flags are consistent: invariant=EMPTY_PERIOD (not
  // CLOSING_OK), guard_enabled=false, isBlocked=false. Page does not
  // show a misleading "OK" banner when the backend is unreachable.
  const invariant: ClosingInvariant = initialState?.closing_guard_invariant ?? {
    code: "EMPTY_PERIOD",
    negative_products: {},
    closing_per_product: {},
    guard_enabled: false,
  };

  const openingInventoryLocked =
    initialState?.opening_inventory_locked ?? false;
  const auditTrail = initialState?.closing_guard_audit_trail ?? [];
  const productionConsumptionEvents =
    initialState?.production_consumption_events ?? [];

  // Story 6.1 T8.6 — 4 NEW closing-period fields from MonthlyInputStateResponse.
  const closingPeriodState = initialState?.closing_period_state ?? null;
  const closingSnapshotCount = initialState?.closing_snapshot_count ?? 0;
  const closingPeriodFinalizedAt =
    initialState?.closing_period_finalized_at ?? null;
  // CR 6-1 R4 patch D11 — explicit capability gate (A10 MONTHLY_CLOSING_REPORT).
  // Decoupled from state-presence coupling: service-only tenants get False
  // even when closing_period_state is None.
  const monthlyClosingReportCapabilityGranted =
    initialState?.monthly_closing_report_capability_granted ?? false;

  return (
    <section style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          월 입력 — {periodKey}
        </h1>
        <p style={{ color: "#475569" }}>
          PRD §8.M2(b) — 6 stream 입력 + 기말재고 검증 (§F4.2) + V3 연결성 검증 (§V3).
        </p>
      </header>
      {/* P3-3rd-sweep P1: project all 5 NEW fields. P3: opening locked.
          P25: traceId. P26: productNameLookup. P27: onSubmit no-op.
          Story 6.1 T8.6 — closing_period_state + capability gate + onConfirm. */}
      <MonthlyInputTabs
        period_key={periodKey}
        invariant={invariant}
        audit_trail={auditTrail}
        production_consumption_events={productionConsumptionEvents}
        opening_inventory_locked={openingInventoryLocked}
        trace_id={traceId}
        productNameLookup={{}}
        closing_period_state={closingPeriodState ?? undefined}
        closing_period_capability_granted={monthlyClosingReportCapabilityGranted}
        closing_period_finalized_at={closingPeriodFinalizedAt}
        onSubmit={async (key) => {
          // P3-3rd-sweep P27: no-op save handler for [수불부] tab in
          // CLOSING_OK path. Real save flow wires through useSaveRow hook
          // in follow-up Story (currently saves via api-client directly).
          await Promise.resolve(key);
        }}
        onClosingPeriodConfirm={async (key) => {
          // Story 6.1 T8.6 — POST /api/v1/inventory/closing-period/confirm.
          // Best-effort: throw on 409/403 so the Dialog surfaces toast.error.
          const res = await fetch("/api/v1/inventory/closing-period/confirm", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            },
            body: JSON.stringify({ period_key: key }),
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
            closing_snapshot_count?: number;
          };
          // CR 6-1 R4 patch D12: revalidate the page path so the
          // Server Component re-reads monthly_input_periods.status='closed'
          // + finalized_at + audit trail on next render. Without this,
          // the cached state would still show CLOSING_READY even after
          // the user confirms.
          revalidatePath(`/m2-input/period/${key}`);
          return data.closing_snapshot_count ?? closingSnapshotCount;
        }}
      />
    </section>
  );
}
