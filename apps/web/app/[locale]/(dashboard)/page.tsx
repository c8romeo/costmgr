/**
 * apps/web/app/[locale]/(dashboard)/page.tsx — dashboard home (KPI + Quick Access).
 *
 * Story 1.1 — Task 4.4 placeholder가 cj-style N+19 (2026-09-15 KST, D-Day+1,
 * Dashboard 보강 A=KPI+빠른진입) 으로 확장됨.
 *
 * 결정 wire 보존:
 * - Option A only (B/C 결정 보류 post-MVP, see
 *   memory/project-dday-dashboard-reinforcement.md).
 * - 데이터 활용 = 시드 monthly_input_rows 그대로 (현재 seed 는 purchases
 *   2행 200,000 KRW; sales/production/expenses/labor 미시드 → 해당 KPI
 *   0원 표시. 사용자가 seed 확장 옵션 B 안에서 따로 결정 가능).
 * - periodKey-bound: 시드는 2026-08 만 보유 → 하드코드 (cj-style N+14 의
 *   ROUTE_BY_LABEL 동일 결정 verbatim mirror).
 * - RSC server-side fetch (race-free, F-20 패턴). try/catch best-effort:
 *   backend 미가용 시 KPI "—" placeholder (fail-closed UI).
 *
 * UX-locked: WCAG AA contrast, ko-KR 라벨, 슬레이트 톤.
 */

/* eslint-disable @typescript-eslint/no-restricted-types --
 * AD-8 deferred (Story 0.5+): display-only KPI 합계라 실수 위험 없음.
 * server-API 실제로 amount_krw 를 number 로 직렬화 (BIGINT <2^53 가정).
 * 차후 decimal-string strict mode 전환 시 본 블록 제거. */

import { cookies } from "next/headers";

import { CalculatorBanner } from "@/components/calc/CalculatorBanner";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { QuickAccessCard } from "@/components/dashboard/QuickAccessCard";
import type { MonthlyInputStateResponse } from "@/lib/api-client";
import { INDUSTRY_MENU_MAP, type Industry } from "@/lib/menu-config";
import {
  fetchMonthlyInputStateServerSide,
  fetchTenantSettingsServerSide,
} from "@/lib/server-api";

export const dynamic = "force-dynamic";

// cj-style N+19 — periodKey-bound (시드는 2026-08 단일 period). 주석 — see
// `apps/web/components/sidebar/Sidebar.tsx::ROUTE_BY_LABEL` 의 동일 결정.
const PERIOD_KEY = "2026-08";

interface DashboardKpi {
  revenue: number;
  cost: number;
  margin: number;
  margin_rate: number | null; // revenue==0 → null (0% 표시 시 손실과 구분 불가)
}

// cost stream 분류: PRD §8.M2(b) 의 6-stream 중 orders/production/purchases/
// expenses/labor 가 비용성 (sales 만 수익성).
const COST_STREAMS = new Set([
  "orders",
  "production",
  "purchases",
  "expenses",
  "labor",
]);

function computeKpi(rows: MonthlyInputStateResponse["rows"] | undefined): DashboardKpi | null {
  if (!rows || rows.length === 0) return null;
  let revenue = 0;
  let cost = 0;
  for (const row of rows) {
    const stream = (row as { stream?: string }).stream;
    const amount = Number((row as { amount_krw?: number | null }).amount_krw ?? 0);
    if (!stream || !Number.isFinite(amount)) continue;
    if (stream === "sales") revenue += amount;
    else if (COST_STREAMS.has(stream)) cost += amount;
  }
  const margin = revenue - cost;
  const margin_rate = revenue > 0 ? Math.round((margin / revenue) * 1000) / 10 : null;
  return { revenue, cost, margin, margin_rate };
}

const fmtKrw = (n: number) => `${n.toLocaleString("ko-KR")}원`;

export default async function DashboardHomePage() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  // F-20 race-free server-side fetch — try/catch best-effort. 시드/네트워크
  // 부재 시 state=null → KPI "—" placeholder (페이지가 깨지지 않음).
  let state: Awaited<ReturnType<typeof fetchMonthlyInputStateServerSide>> = null;
  try {
    state = await fetchMonthlyInputStateServerSide(PERIOD_KEY, accessToken, traceId);
  } catch {
    state = null;
  }
  const kpi = computeKpi(state?.rows);

  // tenant-settings (industry, settings_version, menu count). INDUSTRY_MENU_MAP
  // mirror = `apps/web/lib/menu-config.ts` 결정 wire 보존.
  let settings: Awaited<ReturnType<typeof fetchTenantSettingsServerSide>> = null;
  try {
    settings = await fetchTenantSettingsServerSide(accessToken, traceId);
  } catch {
    settings = null;
  }
  const industry = settings?.industry ?? null;
  const settingsVersion = settings?.settings_version ?? 0;
  const menuCount = industry ? (INDUSTRY_MENU_MAP[industry as Industry]?.length ?? 0) : 0;

  return (
    <section>
      <CalculatorBanner accessToken={accessToken} />
      <h1
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem", color: "#0f172a" }}
      >
        대시보드
      </h1>
      <p style={{ color: "#475569", marginBottom: "1rem" }}>
        현재 업종: <strong>{industry ?? "(미설정)"}</strong> · 설정 버전:{" "}
        <code>{settingsVersion}</code>
        {settings ? <> · 노출 메뉴: {menuCount}개</> : null}
      </p>

      {/* cj-style N+19 — KPI 카드 4개 grid (매출/원가/마진/마진율).
          데이터 부재 시 "—" placeholder (useReducer 미사용; RSC 단순 표현). */}
      <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "1.5rem 0 0.75rem", color: "#0f172a" }}>
        {PERIOD_KEY} 실적
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
          marginBottom: "1.5rem",
        }}
      >
        <KpiCard
          label="매출 (sales)"
          value={kpi ? fmtKrw(kpi.revenue) : "—"}
          color="#0f766e"
        />
        <KpiCard
          label="원가 (orders+production+purchases+expenses+labor)"
          value={kpi ? fmtKrw(kpi.cost) : "—"}
          color="#b91c1c"
        />
        <KpiCard
          label="마진"
          value={kpi ? fmtKrw(kpi.margin) : "—"}
          color={kpi && kpi.margin >= 0 ? "#1d4ed8" : "#b91c1c"}
        />
        <KpiCard
          label="마진율"
          value={
            kpi
              ? kpi.margin_rate === null
                ? "— (매출 0)"
                : `${kpi.margin_rate}%`
              : "—"
          }
          color="#6b21a8"
        />
      </div>

      {/* cj-style N+19 — 빠른 진입 3개 (M1/M2/M3). 라우트는
          `apps/web/components/sidebar/Sidebar.tsx::ROUTE_BY_LABEL` 과 동일
          결정 wire 보존 (periodKey-bound 2026-08). */}
      <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "1rem 0 0.75rem", color: "#0f172a" }}>
        빠른 진입
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 12,
        }}
      >
        <QuickAccessCard
          href="/m1-baseline/products"
          title="M1 품목 / BOM"
          description="제품·반제품·원자재 카탈로그 + BOM 등록 + 조회"
        />
        <QuickAccessCard
          href={`/m2-input/period/${PERIOD_KEY}`}
          title="M2 수불부 (월 입력)"
          description="6-stream 월 입력 행 입력/수정/삭제 + 마감"
        />
        <QuickAccessCard
          href="/budget/abc-allocation"
          title="M3 원가풀 (ABC)"
          description="원가풀·활동·동인 배부 + Activity-Based Costing"
        />
      </div>

      {/* 결정 wire 보존 — Option B/C 는 post-MVP 결정 보류. memo:
          memory/project-dday-dashboard-reinforcement.md (다음 세션 시작
          시 또는 본 sprint 후속 결정 wire 보류). */}
    </section>
  );
}
