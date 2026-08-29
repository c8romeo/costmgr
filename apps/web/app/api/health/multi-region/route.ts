/**
 * apps/web/app/api/health/multi-region/route.ts — Phase 5 multi-region health proxy.
 *
 * Phase 5 (cj-style 75번째 wire) — AD-31 (e) verbatim + PRD §F20.5 + AC #5.1~#5.4.
 * Proxies the Python FastAPI `/api/v1/health/multi-region` endpoint to the
 * Next.js frontend. CR 12-5 D-PARITY-01 inversion: Python backend envelope
 * mirrors this TypeScript Next.js envelope verbatim.
 *
 * Architecture:
 * - Edge Runtime: low-latency health check (no cold start).
 * - force-dynamic: bypass Next.js route cache (health must be fresh).
 * - Public route: no authentication required (health checks must work
 *   even when auth subsystem is degraded).
 * - CR 12-5 D-PARITY-01: envelope shape matches Python backend exactly.
 */

import { NextResponse } from "next/server";

export const runtime = "edge";
export const dynamic = "force-dynamic";

interface RegionHealth {
  region: "primary_seoul" | "secondary_tokyo";
  replication_status:
    | "healthy"
    | "lagging"
    | "stalled"
    | "disconnected";
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  lag_seconds: number;
  last_wal_received_at: string | null;
}

interface MultiRegionHealth {
  status: "healthy" | "degraded" | "unhealthy";
  primary: RegionHealth;
  secondary: RegionHealth;
  timestamp: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const SUPABASE_URL = process.env.SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY ?? "";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export async function GET(): Promise<NextResponse<MultiRegionHealth>> {
  // Fetch from Python backend /api/v1/health/multi-region.
  // Fallback to disconnected envelope if backend unreachable.
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/health/multi-region`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          apikey: SUPABASE_ANON_KEY,
        },
        signal: AbortSignal.timeout(5_000),
        cache: "no-store",
      },
    );

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = (await response.json()) as MultiRegionHealth;
    return NextResponse.json<MultiRegionHealth>(data, {
      status: response.status,
    });
  } catch {
    // Fallback envelope — both regions disconnected.
    const now = new Date().toISOString();
    return NextResponse.json<MultiRegionHealth>(
      {
        status: "unhealthy",
        primary: {
          region: "primary_seoul",
          replication_status: "disconnected",
          lag_seconds: 0,
          last_wal_received_at: null,
        },
        secondary: {
          region: "secondary_tokyo",
          replication_status: "disconnected",
          lag_seconds: 0,
          last_wal_received_at: null,
        },
        timestamp: now,
      },
      { status: 503 },
    );
  }
}