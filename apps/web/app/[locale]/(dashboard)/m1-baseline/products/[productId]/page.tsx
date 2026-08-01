/**
 * apps/web/app/[locale]/(dashboard)/m1-baseline/products/[productId]/page.tsx
 *
 * Story 2.2 — Task 5.1. Product detail page with BOM editor.
 *
 * Server Component — reads the access token, awaits the BOM GET
 * server-side (F-20 race-free), and delegates the matrix UI to
 * BOMEditorClient.
 *
 * UX-locked: ko-KR labels, WCAG AA contrast, Professional 톤.
 */

import { cookies } from "next/headers";

import { BOMEditorClient } from "@/components/m1-baseline/products/BOMEditorClient";
import { fetchBomServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ productId: string }>;
}) {
  const { productId } = await params;
  const accessToken = cookies().get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  const initialBom = await fetchBomServerSide(productId, accessToken, traceId);

  return (
    <section style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          품목 상세 / BOM 편집
        </h1>
        <p style={{ color: "#475569" }}>
          PRD §8.M1(b) — BOM 비중 합이 100%여야 [계산] 버튼이 활성화됩니다.
        </p>
      </header>
      <BOMEditorClient
        productId={productId}
        accessToken={accessToken}
        initialBom={initialBom}
      />
    </section>
  );
}