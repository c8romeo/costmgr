/**
 * apps/web/app/api/health/route.ts — Next.js health check route handler
 * (Phase 4 T5 wire).
 *
 * Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AD-27 verbatim +
 * PRD §F16.5 + AC #5.5.
 *
 * Vercel-side health check at `/api/health`. Returns a minimal envelope
 * with build SHA + region so operators can verify which deployment is
 * live without exposing secrets.
 *
 * Architecture patterns (CR 11-3 honest-DEFER discipline):
 * - Edge Runtime compatible (no Node-specific APIs).
 * - No PII leakage (only build metadata + region).
 * - No database calls — purely static.
 */

import { NextResponse } from "next/server";

// Force dynamic so the response reflects the current deployment.
export const dynamic = "force-dynamic";
// Edge Runtime for low-latency response (matches apps/web/middleware.ts pattern).
export const runtime = "edge";

interface HealthResponse {
  status: "healthy";
  build: string | null;
  region: string | null;
  timestamp: string;
}

export async function GET(): Promise<NextResponse<HealthResponse>> {
  const build =
    process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA ?? process.env.VERCEL_GIT_COMMIT_SHA ?? null;
  const region =
    process.env.NEXT_PUBLIC_VERCEL_REGION ?? process.env.VERCEL_REGION ?? null;
  const timestamp = new Date().toISOString();

  return NextResponse.json(
    {
      status: "healthy" as const,
      build,
      region,
      timestamp,
    },
    {
      status: 200,
      headers: {
        "Cache-Control": "no-store, max-age=0",
      },
    },
  );
}