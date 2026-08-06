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
 */

import { cookies } from "next/headers";

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

  const initialState = await fetchMonthlyInputStateServerSide(
    periodKey,
    accessToken,
    traceId,
  );

  // Default invariant when state fetch fails (F-20 fallback). CLOSING_OK
  // is the safe default — the Client Component will re-fetch via polling
  // and surface the actual invariant once available.
  const invariant: ClosingInvariant = initialState?.closing_guard_invariant ?? {
    code: "CLOSING_OK",
    negative_products: {},
    closing_per_product: {},
    guard_enabled: true,
  };

  const isBlocked = initialState?.closing_guard_blocked ?? false;

  return (
    <section style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          월 입력 — {periodKey}
        </h1>
        <p style={{ color: "#475569" }}>
          PRD §8.M2(b) — 6 stream 입력 + 기말재고 검증 (§F4.2) + V3 연결성 검증 (§V3).
        </p>
        {isBlocked && (
          <p
            data-testid="closing-guard-blocked-banner"
            style={{
              marginTop: "0.5rem",
              padding: "0.5rem 0.75rem",
              borderRadius: 6,
              background: "#fef2f2",
              color: "#991b1b",
              fontWeight: 600,
            }}
            role="alert"
          >
            기말재고 음수 — [마감] 버튼이 비활성화됩니다.
          </p>
        )}
      </header>
      <MonthlyInputTabs
        period_key={periodKey}
        invariant={invariant}
      />
    </section>
  );
}
