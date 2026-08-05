/**
 * apps/web/app/[locale]/(dashboard)/m1-baseline/products/page.tsx
 *
 * Story 2.1 — Task 5.1. 품목 마스터 (Product / Item Master) 랜딩 페이지.
 *
 * Server Component — reads the access token (F-1: pass the STRING, not a
 * function reference) and delegates the product list UI to a Client
 * Component.
 *
 * F-20: Server-side initial fetch (race-free). The RSC awaits the
 * list endpoint server-side and passes the result as `initialProducts`
 * prop. The Client Component seeds its hook from this prop so even fast
 * clicks before the first poll cannot clobber existing tenant products.
 *
 * UX-locked: ko-KR labels, WCAG AA contrast, Professional 톤.
 */

import { cookies } from "next/headers";

import { ProductListClient } from "@/components/m1-baseline/products/ProductListClient";
import { fetchProductsServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function ProductsPage() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  // F-20: server-side initial product list fetch. On any failure
  // (network, 401, 5xx, JSON decode), return `null` so the Client
  // Component falls back to its polling loop.
  const initialProducts = await fetchProductsServerSide(accessToken, traceId);

  return (
    <section style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          품목 마스터
        </h1>
        <p style={{ color: "#475569" }}>
          우리 회사 카탈로그(제품·반제품·원자재·상품·서비스)를 등록하고 유형별 배지로 구분합니다.
          (PRD §8.M1)
        </p>
      </header>
      <ProductListClient
        accessToken={accessToken}
        initialProducts={initialProducts}
        industry={null}
      />
    </section>
  );
}
