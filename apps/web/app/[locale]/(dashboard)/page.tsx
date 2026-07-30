/**
 * apps/web/app/[locale]/(dashboard)/page.tsx — dashboard home (placeholder).
 *
 * Story 1.1 — Task 4.4 placeholder. The real dashboard widgets land
 * in their respective stories (m1_baseline, m2_input, …). This page
 * exists so the route is reachable after industry selection.
 */

"use client";

import { CalculatorBanner } from "@/components/calc/CalculatorBanner";
import { useMenuContext } from "@/components/sidebar/MenuContext";

export default function DashboardHomePage() {
  const { industry, menu, settingsVersion, accessToken } = useMenuContext();
  return (
    <section>
      <CalculatorBanner accessToken={accessToken} />
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
        대시보드
      </h1>
      <p style={{ color: "#475569", marginBottom: "1rem" }}>
        현재 업종: <strong>{industry ?? "(미설정)"}</strong> · 설정 버전:{" "}
        <code>{settingsVersion}</code>
      </p>
      <p style={{ color: "#475569", marginBottom: "1rem" }}>
        노출 메뉴: {menu.length}개
      </p>
    </section>
  );
}
